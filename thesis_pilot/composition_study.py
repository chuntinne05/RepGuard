"""Frozen exploratory comparison: all24 existing reports,72 new real responses.

Labels loaded only by analyze(), after collection. Each call durably initiated;
an unresolved request is never silently retried. No target-dependent stopping.
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
from .composition_tools import candidate,messages,canonical
from .causal_tools import verify as dsl_verify

DEST=ROOT/'results/thesis_composition_cycle_02'
FILES=['composition_tools.py','composition_app.py','composition_study.py','pot_tools.py','core.py','causal_tools.py','live_app.py','modal_app.py']
DIGEST='bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8'

def parents():
    import sys
    sys.path.insert(0,str(ROOT/'docs/analysis'))
    from repguard_unit_failure_diagnostic import surgery
    cases=read(ROOT/'results/thesis_causal_repair_v1/plan.json')['fresh_cases'];out={}
    for c in cases:
        i=c['id'];h=digest(i)[:16]
        p=ROOT/'results/thesis_pot_control_v1'/f'{h}.json'
        d=ROOT/'results/thesis_causal_repair_v1/fresh'/f'{h}_initial.json'
        po=read(p)['output'];do=read(d)['output'];v=do['verification']
        a,changed=surgery(v['answer']);dv=dsl_verify(c,json.dumps(a)) if changed else v
        out[i]={'pot':candidate(canonical(po['response']['message']['content'])),
                'dsl':candidate(dv),'pot_output':po,'dsl_output':do,
                'parent_files':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [p,d]}}
    return cases,out

def prepare():
    cases,pp=parents()
    plan={'created_utc':None,'scope':'Exploratory mechanistic development on ALL24 previously seen reports; not an independent test or novelty evidence',
          'hypothesis':'Source-grounded reconciliation of complementary facts creates useful new answers beyond competent iterative self-review',
          'case_ids':[c['id'] for c in cases],'max_new_calls':72,'max_collection_wall_seconds':7200,
          'actions':['self_review_1','self_review_2','compose'],
          'design':'self1 reviews PoT; self2 reviews accepted self1; compose reviews original PoT plus original DSL with common unit pass. Same system, source, executor, cap and seed for all NEW calls. No gold feedback.',
          'fallback':'Mechanical invalid => keep the current candidate, never choose by correctness',
          'model':'qwen3:14b','model_digest':DIGEST,'thinking':True,'num_predict':4096,'num_ctx':16384,'temperature':0,'seed':19102026,
          'scoring':'Official FinQA exe_ans exact round5, no percent oracle; all common robust format/readout controls frozen before new responses',
          'budget':'Composition uses 1xDSL1536 +1xPoT4096 +1xcomposition4096; practical self2 uses 3xPoT4096. Compare actual measured runtime/tokens; self1 practical 2calls. Existing parents cached for collection only and charged to conceptual deployment costs.',
          'gate_for_history_learning':'Exploratory action union among directPoT,self1,self2,compose >= best fixed+2 and compose has >=2 rescues over self2. Otherwise do not fit another history controller on this pool.',
          'next_confirmation':'Any selected approach must be frozen and tested on NEW report groups before superiority claims; sparse-history and compute-controlled ablations required.',
          'known_limitations':['Repeated development, not final holdout','Same backbone/scaffold variants; not evidence for cross-model reputation','No learned reputation in these arms','DSL auxiliary may anchor wrong scope/unit; source existence does not verify semantic relevance','Native parents seed18102026 and newcalls19102026; no isolated seed-effect claim'],
          'quality_retry':False,'gold_at_inference':False,'parent_files':{k:v for p in pp.values() for k,v in p['parent_files'].items()},
          'source_sha256':{f:hashlib.sha256(Path(__file__).with_name(f).read_bytes()).hexdigest() for f in FILES},
          'helper_sha256':hashlib.sha256((ROOT/'docs/analysis/repguard_unit_failure_diagnostic.py').read_bytes()).hexdigest()}
    plan['run_id']=digest(plan)[:24]
    f=DEST/'plan.json'
    if f.exists():assert read(f)==plan
    else:
        atomic(f,plan)
        with zipfile.ZipFile(DEST/'frozen_source.zip','w') as z:
            for name in FILES:z.write(Path(__file__).with_name(name),name)
            z.write(ROOT/'docs/analysis/repguard_unit_failure_diagnostic.py','repguard_unit_failure_diagnostic.py')
        atomic(DEST/'registration.json',{'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'run_id':plan['run_id'],'plan_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'new_responses_at_registration':len(list((DEST/'responses').glob('*.json')))})
    print(json.dumps({'run_id':plan['run_id'],'cases':len(cases),'cap':72}),flush=True)
    return plan,cases,pp

def collect():
    import modal
    plan,cases,pp=prepare();begin=time.monotonic()
    server=modal.Cls.from_name('repguard-thesis-real-pilot-20261018','CompositionOllama')()
    count=0
    for c in cases:
        p=pp[c['id']];current=p['pot']
        for action in ['self_review_1','self_review_2','compose']:
            inp=p['pot'] if action=='compose' else current
            alt=p['dsl'] if action=='compose' else None
            path=DEST/'responses'/f'{digest(c["id"])[:16]}_{action}.json'
            ph=digest(messages(c,inp,alt))
            if path.exists():
                row=read(path)
                if row['state']!='completed':raise RuntimeError('Unresolved initiated call; manual audit required, no retry')
            else:
                if time.monotonic()-begin>plan['max_collection_wall_seconds']:raise RuntimeError('Wall cap reached')
                atomic(path,{'state':'initiated','case_id':c['id'],'action':action,'prompt_sha256':ph,'epoch':time.time()})
                o=server.refine.remote(c,inp,alt)
                row={'state':'completed','case_id':c['id'],'action':action,'input_current':inp,'input_alternative':alt,'output':o}
                atomic(path,row)
            o=row['output']
            assert o['prompt_sha256']==ph and o['model_digest']==DIGEST and o['live_inference'] and not o['evaluation_volume_mounted']
            assert o['verification']==canonical(o['response']['message']['content'])
            accepted=o['verification']['hard_pass']
            if action!='compose' and accepted:current=candidate(o['verification'])
            count+=1
            print(json.dumps({'completed':count,'case':c['id'],'action':action,'executable':accepted,'value':o['verification']['value'],'tokens':o['response'].get('eval_count')}),flush=True)
    atomic(DEST/'collection_complete.json',{'run_id':plan['run_id'],'completed':count,'new_calls':72,'mock_calls':0,'epoch':time.time()})

def analyze():
    plan,cases,pp=prepare();assert read(DEST/'collection_complete.json')['completed']==72
    gold=read(ROOT/'results/thesis_causal_repair_v1/private.json')['gold']
    methods={a:{'correct':0,'model_calls_per_question':n,'output_tokens':0,'input_tokens':0,'ollama_eval_seconds':0,'rows':{}} for a,n in [('direct_pot',1),('self_review_1',2),('self_review_2',3),('compose',3)]}
    def cost(o):
        r=o['response'];return (r.get('eval_count',0),r.get('prompt_eval_count',0),(r.get('eval_duration',0)+r.get('prompt_eval_duration',0))/1e9)
    rows=[];actual=[]
    for c in cases:
        i=c['id'];p=pp[i];current=p['pot'];potcost=cost(p['pot_output']);selfcost=list(potcost)
        states={'direct_pot':current};costs={'direct_pot':potcost};raw={}
        for a in ['self_review_1','self_review_2','compose']:
            row=read(DEST/'responses'/f'{digest(i)[:16]}_{a}.json');o=row['output'];actual.append(o)
            inp=p['pot'] if a=='compose' else current;alt=p['dsl'] if a=='compose' else None
            assert row['input_current']==inp and row['input_alternative']==alt
            assert digest(messages(c,inp,alt))==o['prompt_sha256']
            assert canonical(o['response']['message']['content'])==o['verification']
            v=o['verification'];new=candidate(v) if v['hard_pass'] else inp
            raw[a]={'executable':v['hard_pass'],'value':v['value'],'accepted':v['hard_pass']}
            if a!='compose':
                current=new;selfcost=[x+y for x,y in zip(selfcost,cost(o))];costs[a]=list(selfcost)
            else:costs[a]=[sum(x) for x in zip(potcost,cost(p['dsl_output']),cost(o))]
            states[a]=new
        outcome={}
        for a,s in states.items():
            ok=bool(s['execution']['hard_pass'] and correct(s['execution']['value'],gold[i]));outcome[a]=ok
            m=methods[a];m['correct']+=ok;m['rows'][i]=int(ok)
            for k,v in zip(['output_tokens','input_tokens','ollama_eval_seconds'],costs[a]):m[k]+=v
        rows.append({'id':i,'official_target':gold[i],'outcomes':outcome,'raw':raw,'values':{a:s['execution']['value'] for a,s in states.items()}})
    base=methods['direct_pot']['rows'];self2=methods['self_review_2']['rows']
    for a,m in methods.items():
        ys=m['rows'];m['rescue_vs_direct']=sum(ys[i] and not base[i] for i in base);m['harm_vs_direct']=sum(base[i] and not ys[i] for i in base)
        m['rescue_vs_self2']=sum(ys[i] and not self2[i] for i in base);m['harm_vs_self2']=sum(self2[i] and not ys[i] for i in base)
        m['mean_ollama_eval_seconds']=m['ollama_eval_seconds']/len(cases)
    union=sum(any(m['rows'][c['id']] for m in methods.values()) for c in cases);best=max(m['correct'] for m in methods.values())
    gate=union>=best+2 and methods['compose']['rescue_vs_self2']>=2
    result={'run_id':plan['run_id'],'scope':plan['scope'],'n':len(cases),'actual_new_calls':len(actual),'mock_calls':0,
            'methods':methods,'action_oracle_union':union,'best_fixed':best,'gate_for_history_learning':gate,
            'new_input_tokens':sum(o['response'].get('prompt_eval_count',0) for o in actual),
            'new_output_tokens':sum(o['response'].get('eval_count',0) for o in actual),
            'new_request_wall_seconds':sum(o['wall_seconds'] for o in actual),
            'new_length_stops':sum(o['response'].get('done_reason')=='length' for o in actual),
            'new_native_thinking_nonempty':sum(bool(o['actual_thinking_chars']) for o in actual),
            'gold_only_evaluator':True,'reputation_superiority_claim':False}
    atomic(DEST/'traces_private.json',{'rows':rows});atomic(DEST/'summary.json',result)
    print(json.dumps({k:v if k!='methods' else {a:{x:y for x,y in m.items() if x!='rows'} for a,m in v.items()} for k,v in result.items()},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','collect','analyze']);args=parser.parse_args()
    {'prepare':prepare,'collect':collect,'analyze':analyze}[args.command]()
