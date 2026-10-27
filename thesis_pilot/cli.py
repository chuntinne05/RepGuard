"""Prepare, submit, inspect, fetch and independently verify the REAL pilot."""
import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
import io
from pathlib import Path
from .core import AGENTS,digest,normalized,visible_record
from .pipeline import atomic,validate,verify_visible,load_responses

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'results/thesis_real_pilot_v2'
APP='repguard-thesis-real-pilot-20261018'
SOURCE_REVISION='0f16e2867befa6840783e58be38c9efb9229d742'
DATA_SHA='49f237eb9779b569473b26b08048867d04635a7cc39ad6a7a5664c55bb428db6'


def read(p):return json.loads(p.read_text())


def prepare():
    target=OUT/'packet_private.json'
    if target.exists():
        packet=read(target);verify_visible(packet['visible']);print(json.dumps({'run_id':packet['run_id'],'existing':True}));return
    path=OUT/'finqa_train_private.json'
    if hashlib.sha256(path.read_bytes()).hexdigest()!=DATA_SHA:raise ValueError('Pinned FinQA file changed')
    source=read(path);excluded=set()
    parent=ROOT/'results/routerbench_headroom_v1/cloud/input_private.json'
    if parent.exists():excluded=set(read(parent)['datasets']['finqa/test']['query_ids'])
    groups={}
    for row in source:
        public=visible_record(row)
        qhash=hashlib.sha256(normalized(public['question']).encode()).hexdigest()
        if qhash in excluded:continue
        groups.setdefault(public['report'],[]).append((public,qhash))
    byid={r['id']:r for r in source};cases=[];used=set()
    for group in sorted(groups,key=lambda x:digest('repguard-thesis-v1-report:'+x)):
        for public,qhash in sorted(groups[group],key=lambda x:digest('repguard-thesis-v1-id:'+x[0]['id'])):
            if qhash in used:continue
            cases.append(public);used.add(qhash);break
        if len(cases)==100:break
    if len(cases)!=100:raise ValueError('Insufficient distinct questions/reports')
    # Targets are extracted only after the metadata-only ID list above is final.
    evaluation={'gold':{c['id']:byid[c['id']]['qa']['exe_ans'] for c in cases},
                'scope':'Full supervised history gold + held-out development screen; evaluator only'}
    manifest=read(OUT/'model_manifest.json')
    source_files=['__init__.py','core.py','analysis.py','pipeline.py','modal_app.py','cli.py','protocol.md']
    hashes={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in source_files}
    partition={c['id']:('history' if i<60 else 'calibration' if i<70 else 'validation' if i<80 else 'screen')
               for i,c in enumerate(cases)}
    public={'cases':cases,'partition':partition,'agents':AGENTS,'total_requests':200,
            'source_revision':SOURCE_REVISION,'dataset_sha256':DATA_SHA,'source_sha256':hashes,
            'evaluation_sha256':digest(evaluation),'ollama_version':manifest['ollama'],
            'model_digests':{name:row['digest'] for name,row in manifest['models'].items()},
            'max_collection_wall_seconds':6600,'excluded_prior_development_hashes':len(excluded),
            'selection':'SHA256 report then ID; unique normalized question; no target-based selection'}
    public['run_id']=digest(public)[:24]
    packet={'run_id':public['run_id'],'visible':public,'evaluation':evaluation}
    verify_visible(public);atomic(target,packet)
    with zipfile.ZipFile(OUT/'frozen_source.zip','w') as z:
        for name in source_files:z.write(Path(__file__).with_name(name),name)
    print(json.dumps({'run_id':public['run_id'],'questions':100,'reports':100,'requests':200,
                      'source_sha256':hashes,'model_digests':public['model_digests']},indent=2))


def near(a,b):
    import numpy as np
    if isinstance(a,dict):
        assert a.keys()==b.keys()
        for k in a:near(a[k],b[k])
    elif isinstance(a,list):
        assert len(a)==len(b)
        for x,y in zip(a,b):near(x,y)
    elif isinstance(a,float):assert np.isclose(a,b,atol=1e-9,rtol=1e-9), (a,b)
    else:assert a==b,(a,b)


def report():
    from .analysis import analyze
    packet=read(OUT/'packet_private.json');verify_visible(packet['visible'])
    response_root=OUT/'cloud/responses';evaluation_root=OUT/'cloud/evaluation'
    assert read(evaluation_root/'packet_private.json')==packet
    responses=load_responses(packet['visible'],response_root)
    cloud=read(evaluation_root/'analysis_private.json');validate(cloud)
    actual=analyze(packet,responses);near(actual,{k:v for k,v in cloud.items() if k!='artifact_sha256'})
    summary={k:v for k,v in actual.items() if k not in ['examples_private','action_traces','learner_artifacts']}
    attempts=sum(len(r['attempts']) for r in responses.values())
    summary['verification']={'real_responses_verified':len(responses),'attempts_started':attempts,
                             'cloud_local_recomputation_match':True,
                             'environment':read(response_root/'environment.json')}
    out=ROOT/'docs/analysis';atomic(out/'repguard_thesis_pilot_results_2026-10-18.json',summary)
    lines=['# RepGuard: pilot đồ án chạy model thật','',
        '100 câu FinQA TRAIN,100 báo cáo;60history/10calibration/10validation/20development screen.',
        '**Đây là pilot development, chưa phải xác nhận cuối hoặc so sánh SOTA.**','',
        f"Run `{packet['run_id']}`; app `{APP}`;200 phản hồi thật đã kiểm checksum và tính lại local.",
        '', '| Phương pháp | Đúng/20 | Accuracy | Approved coverage | Sai được approved | Mean tokens | Calls/20 |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for name,r in summary['methods'].items():
        lines.append(f"| {name} | {r['correct']} | {r['accuracy']:.1%} | {r['coverage']:.1%} | {r['wrong_approved']} | {r['mean_tokens']:.1f} | {r['model_calls']} |")
    lines+=['',f"**Pilot signal gate: {'PASS' if summary['pilot_signal_pass'] else 'FAIL'}.**",'',
            'Cả hai learner được huấn luyện supervised từ outcome thực; nhãn history được cấp công bằng cho controls. Không gọi kết quả này là10%audit.',
            'Source/operation checks không chứng minh đúng ngữ nghĩa. Token/request seconds không phải tổng billing Modal.',
            'Các policy được replay trên phản hồi thật đã thu;200calls thu counterfactual không phải cost serving của mỗi policy.','',
            '| RepGuard so với | Accuracy difference | CI95 | Rescue | Harm |','|---|---:|---|---:|---:|']
    for name,r in summary['primary_contrasts'].items():
        lines.append(f"| {name} | {r['difference']:+.1%} | [{r['ci95'][0]:+.1%},{r['ci95'][1]:+.1%}] | {r['rescues']} | {r['harms']} |")
    lines+=['','Giới hạn: chỉ20câu screen; bootstrap exploratory, chưa adjustment; model cùng họ; latency chịu thứ tự block/cold load. Giữ nguyên kết quả âm và không tune trên screen.','']
    (out/'repguard_thesis_pilot_assessment_2026-10-18.md').write_text('\n'.join(lines))
    print(json.dumps(summary,ensure_ascii=False,indent=2))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','submit','status','fetch','report'])
    args=parser.parse_args()
    if args.command=='prepare':return prepare()
    if args.command=='report':return report()
    import modal
    packet=read(OUT/'packet_private.json');verify_visible(packet['visible'])
    receipt=OUT/'receipt.json'
    if args.command=='submit':
        if receipt.exists():raise RuntimeError('Receipt exists; inspect existing job, never submit duplicate')
        call=modal.Function.from_name(APP,'worker').spawn(packet)
        atomic(receipt,{'app':APP,'run_id':packet['run_id'],'call_id':call.object_id})
        print(json.dumps(read(receipt)));return
    function=modal.Function.from_name(APP,'inspect_run')
    if args.command=='status':print(json.dumps(function.remote(packet['run_id']),indent=2));return
    archive=function.remote(packet['run_id'],True)
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        for name in z.namelist():
            if '..' in Path(name).parts or Path(name).is_absolute():raise ValueError('Unsafe artifact path')
        z.extractall(OUT/'cloud')
    print(json.dumps({'fetched_files':len(z.namelist()),'run_id':packet['run_id']}))


if __name__=='__main__':main()
