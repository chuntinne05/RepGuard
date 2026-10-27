"""ALL16case no-native-thinking control, triggered by native4096truncations.

Separate post-hoc development experiment, not a quality retry or new model.
"""
import argparse
import hashlib
import json
import time
import zipfile
from pathlib import Path
from .cli import ROOT,read
from .core import digest,correct
from .pipeline import atomic
from .pot_tools import messages
from .composition_tools import canonical

APP='repguard-thesis-modern-backbone-20261019';MODEL='qwen3.5:27b'
DEST=ROOT/'results/thesis_modern_direct_control_v1'
FILES=['modern_direct_control.py','modern_direct_app.py','modern_probe_app.py','pot_tools.py','composition_tools.py','core.py','modal_app.py']

def prepare():
    parent=ROOT/'results/thesis_modern_backbone_control_v1/plan.json';source=read(parent);cases=source['public_cases']
    plan={'scope':'Post-hoc whole16case interface/compute adequacy control, NOT independent method test. Same model, no native thinking.',
          'motivation':'At least4native responses exhausted4096tokens with empty final content. Keep original results; test thinkFalse on ALL16 including successes.',
          'public_cases':cases,'case_ids':source['case_ids'],'model':MODEL,'model_digest':source['model_digest'],'app':APP,'gpu':'L40S',
          'parent_plan_sha256':hashlib.sha256(parent.read_bytes()).hexdigest(),'thinking':False,'num_predict':4096,'num_ctx':16384,'seed':19102026,'temperature':0,
          'max_new_calls':16,'max_collection_wall_seconds':3600,'quality_retry':False,'gold_at_inference':False,
          'prompt':'Unchanged pot_tools.messages and canonical executor','scoring':'Same exact FinQA round5; no oracle sign/scale matching',
          'original_native_results_preserved':True,'no_confirmation_reports':True,
          'source_sha256':{f:hashlib.sha256(Path(__file__).with_name(f).read_bytes()).hexdigest() for f in FILES}}
    plan['run_id']=digest(plan)[:24];f=DEST/'plan.json'
    if f.exists():assert read(f)==plan
    else:
        atomic(f,plan)
        with zipfile.ZipFile(DEST/'frozen_source.zip','w') as z:
            for name in FILES:z.write(Path(__file__).with_name(name),name)
        atomic(DEST/'registration.json',{'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'run_id':plan['run_id'],
                 'plan_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'new_responses_at_registration':len(list((DEST/'responses').glob('*.json')))})
    print(json.dumps({'run_id':plan['run_id'],'calls_cap':16,'mode':'thinkFalse'}),flush=True);return plan,cases

def collect():
    import modal
    plan,cases=prepare();assert read(ROOT/'results/thesis_modern_backbone_control_v1/collection_complete.json')['actual_new_calls']==16
    server=modal.Cls.from_name(APP,'ModernDirectOllama')();start=time.monotonic()
    for n,c in enumerate(cases,1):
        f=DEST/'responses'/f'{digest(c["id"])[:16]}.json'
        if f.exists():
            r=read(f)
            if r['state']!='completed':raise RuntimeError('Unresolved initiated call, no retry')
        else:
            if time.monotonic()-start>plan['max_collection_wall_seconds']:raise RuntimeError('Wall cap')
            atomic(f,{'state':'initiated','case_id':c['id'],'epoch':time.time()})
            o=server.solve.remote(c,MODEL);r={'state':'completed','case_id':c['id'],'output':o};atomic(f,r)
        o=r['output'];assert digest(messages(c))==o['prompt_sha256'] and o['model_digest']==plan['model_digest']
        assert o['live_inference'] and not o['evaluation_volume_mounted'] and canonical(o['response']['message']['content'])==o['verification']
        print(json.dumps({'completed':n,'case':c['id'],'valid':o['verification']['hard_pass'],'value':o['verification']['value'],'native_thinking_chars':o['actual_thinking_chars']}),flush=True)
    atomic(DEST/'collection_complete.json',{'actual_new_calls':16,'mock_calls':0,'epoch':time.time()})

def analyze():
    plan,cases=prepare();assert read(DEST/'collection_complete.json')['actual_new_calls']==16
    raw={r['id']:r for r in read(ROOT/'results/thesis_real_pilot_v2/finqa_train_private.json')};rr=[];ys={}
    for c in cases:
        r=read(DEST/'responses'/f'{digest(c["id"])[:16]}.json');o=r['output'];v=canonical(o['response']['message']['content']);assert v==o['verification']
        ys[c['id']]={'correct':bool(v['hard_pass'] and correct(v['value'],raw[c['id']]['qa']['exe_ans'])),'value':v['value']};rr.append(o)
    m={'correct':sum(y['correct'] for y in ys.values()),'n':16,'valid':sum(o['verification']['hard_pass'] for o in rr),
       'input_tokens':sum(o['response'].get('prompt_eval_count',0) for o in rr),'output_tokens':sum(o['response'].get('eval_count',0) for o in rr),
       'length_stops':sum(o['response'].get('done_reason')=='length' for o in rr),'native_thinking_nonempty':sum(bool(o['actual_thinking_chars']) for o in rr),
       'mean_ollama_eval_seconds':sum((o['response'].get('prompt_eval_duration',0)+o['response'].get('eval_duration',0))/1e9 for o in rr)/16}
    parent=read(ROOT/'results/thesis_modern_backbone_control_v1/traces_private.json')['rows'];pair={}
    for other in ['qwen3:14b','qwen3.5:27b']:
        pair[other]={'direct_only_correct':sum(ys[i]['correct'] and not parent[i][other]['correct'] for i in ys),
                     'other_only_correct':sum(parent[i][other]['correct'] and not ys[i]['correct'] for i in ys)}
    result={'run_id':plan['run_id'],'scope':plan['scope'],'actual_new_calls':16,'mock_calls':0,'method':m,'paired':pair,
            'reputation_superiority_claim':False,'posthoc_model_configuration_control':True,'confirmation_reports_used':0}
    atomic(DEST/'summary.json',result);atomic(DEST/'traces_private.json',{'rows':ys});print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','collect','analyze']);a=p.parse_args();{'prepare':prepare,'collect':collect,'analyze':analyze}[a.command]()
