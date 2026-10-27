"""Two natural backbones on16 reserved DEVELOPMENT reports, no final holdout."""
import argparse
import hashlib
import json
import time
import zipfile
from pathlib import Path
from .cli import ROOT,read,DATA_SHA
from .core import digest,visible_record,correct
from .pipeline import atomic
from .pot_tools import messages
from .composition_tools import canonical

DEST=ROOT/'results/thesis_backbone_diversity_probe_v1'
MODELS=['qwen3:8b','qwen3:14b']
FILES=['backbone_probe.py','backbone_probe_app.py','pot_tools.py','composition_tools.py','core.py','modal_app.py']

def prepare():
    reserved=read(ROOT/'docs/analysis/repguard_reserved_report_splits_2026-10-19.json')
    ids=[c['id'] for c in reserved['splits']['development'][:16]]
    rawpath=ROOT/'results/thesis_real_pilot_v2/finqa_train_private.json'
    assert hashlib.sha256(rawpath.read_bytes()).hexdigest()==DATA_SHA
    # No target/answer/program fields extracted by prepare/collect.
    byid={r['id']:visible_record(r) for r in read(rawpath)};cases=[byid[i] for i in ids]
    assert len({c['report'] for c in cases})==16
    confirmation_reports={c['report'] for c in reserved['splits']['confirmation']}
    seen={c['report'] for c in read(ROOT/'results/thesis_real_pilot_v2/packet_private.json')['visible']['cases']}
    seen|={c['report'] for c in read(ROOT/'results/thesis_causal_repair_v1/plan.json')['fresh_cases']}
    assert not ({c['report'] for c in cases} & (confirmation_reports|seen))
    manifest=read(ROOT/'results/thesis_real_pilot_v2/model_manifest.json')
    plan={'scope':'Mechanistic pool-diversity development probe16 NEW reports relative to LIVE cohorts; not confirmation of a method',
          'motivation':'Test genuine parameter-size/backbone diversity rather than several names/prompts of the same14b solver. Same complete sources, native thinking and standard executable PoT for both.',
          'trigger':'Independent32call pool-diversity probe on a second isolated research app, in parallel with cycle2. Registered before any probe responses/targets; no gate-based early stopping.',
          'case_ids':ids,'public_cases':cases,'models':MODELS,'max_new_calls':32,'max_collection_wall_seconds':5400,
          'model_digests':{m:manifest['models'][m]['digest'] for m in MODELS},
          'seed':19102026,'temperature':0,'num_predict':4096,'num_ctx':16384,'thinking':True,
          'quality_retry':False,'gold_at_inference':False,'scoring':'Same exact round5 FinQA target; common canonical format/readout; invalid counts incorrect; no oracle selection',
          'gate_for_larger_history_collection':'oracle union >= best fixed+2 and each backbone has >=1 uniquely correct question; exploratory only, not superiority',
          'known_limits':['16reports small; no reputation learner in probe','Both models sameQwen3family, not diverse architectures','Archive report identity unresolved; report-disjointness from124 LIVE reports and reserved confirmation established','General pretraining exposure to publicTRAIN unknown','Same4096cap is token-cap matching, not equal compute; report actual runtime separately'],
          'reservation_sha256':hashlib.sha256((ROOT/'docs/analysis/repguard_reserved_report_splits_2026-10-19.json').read_bytes()).hexdigest(),
          'source_sha256':{f:hashlib.sha256(Path(__file__).with_name(f).read_bytes()).hexdigest() for f in FILES}}
    plan['run_id']=digest(plan)[:24];f=DEST/'plan.json'
    if f.exists():assert read(f)==plan
    else:
        atomic(f,plan)
        with zipfile.ZipFile(DEST/'frozen_source.zip','w') as z:
            for name in FILES:z.write(Path(__file__).with_name(name),name)
        atomic(DEST/'registration.json',{'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'run_id':plan['run_id'],
                    'plan_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'new_responses_at_registration':len(list((DEST/'responses').glob('*.json')))})
    print(json.dumps({'run_id':plan['run_id'],'new_reports':16,'new_calls_cap':32,'state':'prepared, not started'}),flush=True)
    return plan,cases

def collect():
    import modal
    plan,cases=prepare()
    atomic(DEST/'activation.json',{'app':'repguard-thesis-backbone-probe-20261019','epoch':time.time(),'mode':'independent natural-diversity probe'})
    server=modal.Cls.from_name('repguard-thesis-backbone-probe-20261019','BackboneProbeOllama')();start=time.monotonic();n=0
    for model in MODELS:
        for c in cases:
            f=DEST/'responses'/f'{digest(c["id"])[:16]}_{model.replace(":","_")}.json'
            if f.exists():
                row=read(f)
                if row['state']!='completed':raise RuntimeError('Unresolved initiated call; do not retry')
            else:
                if time.monotonic()-start>plan['max_collection_wall_seconds']:raise RuntimeError('Wall cap')
                atomic(f,{'state':'initiated','case_id':c['id'],'model':model,'epoch':time.time()})
                o=server.solve.remote(c,model);row={'state':'completed','case_id':c['id'],'model':model,'output':o};atomic(f,row)
            o=row['output'];assert o['prompt_sha256']==digest(messages(c)) and o['model_digest']==plan['model_digests'][model]
            assert canonical(o['response']['message']['content'])==o['verification'] and o['live_inference'] and not o['evaluation_volume_mounted']
            n+=1;print(json.dumps({'completed':n,'case':c['id'],'model':model,'value':o['verification']['value'],'valid':o['verification']['hard_pass']}),flush=True)
    atomic(DEST/'collection_complete.json',{'actual_new_calls':n,'mock_calls':0,'epoch':time.time()})

def analyze():
    plan,cases=prepare();assert read(DEST/'collection_complete.json')['actual_new_calls']==32
    byid={r['id']:r for r in read(ROOT/'results/thesis_real_pilot_v2/finqa_train_private.json')}
    methods={};rows={c['id']:{} for c in cases}
    for model in MODELS:
        data=[]
        for c in cases:
            r=read(DEST/'responses'/f'{digest(c["id"])[:16]}_{model.replace(":","_")}.json');o=r['output'];v=canonical(o['response']['message']['content'])
            ok=bool(v['hard_pass'] and correct(v['value'],byid[c['id']]['qa']['exe_ans']));rows[c['id']][model]={'value':v['value'],'correct':ok};data.append(o)
        methods[model]={'correct':sum(r[model]['correct'] for r in rows.values()),'n':16,
            'valid':sum(o['verification']['hard_pass'] for o in data),'input_tokens':sum(o['response'].get('prompt_eval_count',0) for o in data),
            'output_tokens':sum(o['response'].get('eval_count',0) for o in data),'length_stops':sum(o['response'].get('done_reason')=='length' for o in data),
            'mean_ollama_eval_seconds':sum((o['response'].get('eval_duration',0)+o['response'].get('prompt_eval_duration',0))/1e9 for o in data)/16}
    # All rows now contain both models; compute each model's unique successes.
    for model in MODELS:methods[model]['uniquely_correct']=sum(r[model]['correct'] and not r[MODELS[1-MODELS.index(model)]]['correct'] for r in rows.values())
    union=sum(any(x['correct'] for x in r.values()) for r in rows.values());best=max(m['correct'] for m in methods.values())
    result={'run_id':plan['run_id'],'scope':plan['scope'],'n':16,'actual_new_calls':32,'mock_calls':0,'methods':methods,
            'oracle_union':union,'best_fixed':best,'gate_for_larger_history_collection':union>=best+2 and all(m['uniquely_correct']>=1 for m in methods.values()),
            'reputation_superiority_claim':False,'confirmation_reports_used':0,'archive_report_disjointness_established':False}
    atomic(DEST/'summary.json',result);atomic(DEST/'traces_private.json',{'rows':rows})
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','collect','analyze']);a=p.parse_args();{'prepare':prepare,'collect':collect,'analyze':analyze}[a.command]()
