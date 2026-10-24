"""One contemporary baseline on ALL16 frozen backbone-development cases.

This is a stronger control, not a proposed reputation method or model sweep.
"""
import argparse
import hashlib
import json
import time
import zipfile
from pathlib import Path
from .cli import ROOT,read
from .pipeline import atomic
from .core import digest,correct
from .pot_tools import messages
from .composition_tools import canonical

APP='repguard-thesis-modern-backbone-20261019';MODEL='qwen3.5:27b'
DEST=ROOT/'results/thesis_modern_backbone_control_v1'
FILES=['modern_probe.py','modern_probe_app.py','pot_tools.py','composition_tools.py','core.py','modal_app.py']

def download():
    import modal
    f=DEST/'model_manifest.json'
    if f.exists():return read(f)
    atomic(DEST/'download_initiated.json',{'epoch':time.time(),'app':APP,'model':MODEL,'model_inference_calls':0})
    m=modal.Function.from_name(APP,'download_modern_model').remote();atomic(f,m)
    print(json.dumps(m,indent=2),flush=True);return m

def prepare():
    source=read(ROOT/'results/thesis_backbone_diversity_probe_v1/plan.json');cases=source['public_cases']
    manifest=read(DEST/'model_manifest.json')
    plan={'scope':'ONE contemporary stronger single-agent control on the same16 NEW development reports; not independent confirmation or reputation method',
          'case_ids':[c['id'] for c in cases],'public_cases':cases,'model':MODEL,'model_digest':manifest['models'][MODEL]['digest'],
          'app':APP,'model_manifest_sha256':hashlib.sha256((DEST/'model_manifest.json').read_bytes()).hexdigest(),
          'max_new_calls':16,'max_collection_wall_seconds':5400,'gpu':'L40S','num_predict':4096,'num_ctx':16384,'seed':19102026,'temperature':0,'thinking':True,
          'prompt':'Unchanged pot_tools.messages, same canonical executor as8B/14B probe','quality_retry':False,'gold_at_inference':False,
          'scoring':'FinQA target exact round5, no oracle scale search, all16 cases; no cherry-picking previous failures',
          'preexisting_probe_plan_sha256':hashlib.sha256((ROOT/'results/thesis_backbone_diversity_probe_v1/plan.json').read_bytes()).hexdigest(),
          'known_limits':['One16case development probe, cannot select model then call the same cases a final test','Different GPU: compare runtime/tokens transparently; not equal compute or billing','Same family across different Qwen generations, not architecture-diverse generality','Contamination of publicTRAIN unknown; no confirmation reports used'],
          'source_sha256':{f:hashlib.sha256(Path(__file__).with_name(f).read_bytes()).hexdigest() for f in FILES}}
    plan['run_id']=digest(plan)[:24];f=DEST/'plan.json'
    if f.exists():assert read(f)==plan
    else:
        atomic(f,plan)
        with zipfile.ZipFile(DEST/'frozen_source.zip','w') as z:
            for name in FILES:z.write(Path(__file__).with_name(name),name)
        atomic(DEST/'registration.json',{'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'run_id':plan['run_id'],
                   'plan_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'new_responses_at_registration':len(list((DEST/'responses').glob('*.json')))})
    print(json.dumps({'run_id':plan['run_id'],'calls_cap':16,'model_digest':plan['model_digest']}),flush=True);return plan,cases

def collect():
    import modal
    plan,cases=prepare();server=modal.Cls.from_name(APP,'ModernBackboneOllama')();start=time.monotonic()
    for n,c in enumerate(cases,1):
        f=DEST/'responses'/f'{digest(c["id"])[:16]}.json'
        if f.exists():
            r=read(f)
            if r['state']!='completed':raise RuntimeError('Unresolved initiated call; no retry')
        else:
            if time.monotonic()-start>plan['max_collection_wall_seconds']:raise RuntimeError('Wall cap')
            atomic(f,{'state':'initiated','case_id':c['id'],'epoch':time.time()})
            o=server.solve.remote(c,MODEL);r={'state':'completed','case_id':c['id'],'output':o};atomic(f,r)
        o=r['output'];assert o['prompt_sha256']==digest(messages(c)) and o['model_digest']==plan['model_digest']
        assert o['live_inference'] and not o['evaluation_volume_mounted'] and o['verification']==canonical(o['response']['message']['content'])
        print(json.dumps({'completed':n,'case':c['id'],'valid':o['verification']['hard_pass'],'value':o['verification']['value']}),flush=True)
    atomic(DEST/'collection_complete.json',{'actual_new_calls':16,'mock_calls':0,'epoch':time.time()})

def analyze():
    plan,cases=prepare();assert read(DEST/'collection_complete.json')['actual_new_calls']==16
    source=read(ROOT/'results/thesis_backbone_diversity_probe_v1/summary.json')
    previous=read(ROOT/'results/thesis_backbone_diversity_probe_v1/traces_private.json')['rows']
    raw={r['id']:r for r in read(ROOT/'results/thesis_real_pilot_v2/finqa_train_private.json')};data=[];rows={}
    with zipfile.ZipFile(DEST/'frozen_source.zip') as z:
        for f,h in plan['source_sha256'].items():assert hashlib.sha256(Path(__file__).with_name(f).read_bytes()).hexdigest()==h==hashlib.sha256(z.read(f)).hexdigest()
    for c in cases:
        f=DEST/'responses'/f'{digest(c["id"])[:16]}.json';r=read(f);o=r['output'];v=canonical(o['response']['message']['content']);assert v==o['verification']
        assert o['model_digest']==plan['model_digest'] and o['prompt_sha256']==digest(messages(c))
        assert o['app']==APP and o['gpu']=='NVIDIA L40S' and o['response']['done'] and o['model']==MODEL
        ok=bool(v['hard_pass'] and correct(v['value'],raw[c['id']]['qa']['exe_ans']))
        rows[c['id']]={**previous[c['id']],MODEL:{'correct':ok,'value':v['value']}};data.append(o)
    methods={**source['methods'],MODEL:{'correct':sum(r[MODEL]['correct'] for r in rows.values()),'n':16,'valid':sum(o['verification']['hard_pass'] for o in data),
            'input_tokens':sum(o['response'].get('prompt_eval_count',0) for o in data),'output_tokens':sum(o['response'].get('eval_count',0) for o in data),
            'length_stops':sum(o['response'].get('done_reason')=='length' for o in data),'mean_ollama_eval_seconds':sum((o['response'].get('prompt_eval_duration',0)+o['response'].get('eval_duration',0))/1e9 for o in data)/16}}
    pair={}
    for other in source['methods']:
        pair[other]={'modern_only_correct':sum(r[MODEL]['correct'] and not r[other]['correct'] for r in rows.values()),
                     'other_only_correct':sum(r[other]['correct'] and not r[MODEL]['correct'] for r in rows.values())}
    union=sum(any(v['correct'] for v in r.values()) for r in rows.values())
    result={'run_id':plan['run_id'],'scope':plan['scope'],'actual_new_calls':16,'n':16,'mock_calls':0,'methods':methods,'paired':pair,
            'oracle_union_all_three':union,'best_fixed':max(m['correct'] for m in methods.values()),'reputation_superiority_claim':False,
            'same16cases_same_prompt_and_cap':True,'gpu_mismatch_not_cost_matched':True,'confirmation_reports_used':0}
    atomic(DEST/'summary.json',result);atomic(DEST/'traces_private.json',{'rows':rows});print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['download','prepare','collect','analyze']);a=p.parse_args();{'download':download,'prepare':prepare,'collect':collect,'analyze':analyze}[a.command]()
