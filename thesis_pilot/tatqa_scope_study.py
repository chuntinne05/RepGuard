"""Frozen 24-context real-inference mechanism pilot; not a reputation result."""
import argparse
import hashlib
import json
import sys
import time
import zipfile
from pathlib import Path
from .core import digest
from .pipeline import atomic
from .tatqa_scope_tools import messages,verify,incumbent,accept,scope_ok,combined

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'results/thesis_tatqa_source_v1'
DEST=ROOT/'results/thesis_tatqa_scoped_repair_v1'
APP='repguard-thesis-modern-backbone-20261019'
MODEL_DIGEST='64ae5b1d651fb2709d5928ccb8dcfb4bb2cc9c2c8001ac34497e36a6cf905b59'
ACTIONS=['plain','initial','evidence','operation','self1','self2']
ARMS=['plain','initial','evidence','operation','combined','self1','self2']
FILES=['tatqa_scope_study.py','tatqa_scope_tools.py','tatqa_scope_app.py','modern_direct_app.py','modern_probe_app.py','pot_tools.py','core.py','pipeline.py','modal_app.py']
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def prepare():
    cases=read(SOURCE/'public_development_inventory.json')[:24]
    assert len(cases)==24 and len({c['context_id'] for c in cases})==24
    p={'scope':'Exploratory TRAIN development mechanism pilot. No independent confirmation or learned reputation policy.',
       'public_cases':cases,'case_ids':[c['id'] for c in cases],'selection':'First24 of the previously hash-selected public64 inventory; no outcome-based selection.',
       'public_inventory_sha256':sha(SOURCE/'public_development_inventory.json'),
       'app':APP,'model':'qwen3.5:27b','model_digest':MODEL_DIGEST,'gpu':'L40S','thinking':False,
       'num_predict':4096,'num_ctx':16384,'seed':20102026,'temperature':0,'max_new_calls':144,
       'max_collection_wall_seconds':10800,'actions':ACTIONS,'quality_retry':False,'gold_at_inference':False,
       'comparison':'Plain executable PoT; source-bound initial; independently scoped evidence and operation repairs; their mechanical combination; unrestricted self-review1/2.',
       'same_tools':'Same numeric catalogue, full raw source, AST interpreter, model/mode and per-call cap. Self may edit every field. Plain lacks the binding constraint intentionally as capability control.',
       'scope_enforcement':'Evidence changes only source IDs for fixed names; operation changes code/status/scale with all bindings frozen. Joint merges compatible RAW patches even if one alone fails execution, then validates. No semantic/gold selector.',
       'acceptance':'Mechanically valid permitted patch accepted; otherwise retain incumbent. Invalid initial remains invalid until repaired. No voting or correctness-based choice.',
       'arms_calls':{'plain':1,'initial':1,'evidence':2,'operation':2,'combined':3,'self1':2,'self2':3},
       'compute':'Report actual input/output tokens and eval durations. Same call caps do not ensure same realized FLOPs. GPU eval proxy excludes startup, idle, CPU, memory/storage and is not billing.',
       'scoring':'Pinned original TAT-QA TaTQAEmAndF1. Nonempty list[str(value)] and MODEL-predicted scale. Invalid/abstain => empty list/EM0. Primary official arithmetic EM; scale accuracy and executable validity separate.',
       'metric_sha256':sha(SOURCE/'tatqa_metric.py'),'utils_sha256':sha(SOURCE/'tatqa_utils.py'),
       'gate':'Collect all24. For subsequent history learner, scoped oracle over KEEP/E/O/EO must exceed strongest unrestricted fixed control among plain/initial/self1/self2 by at least2 cases AND rescue at least2 cases missed by ALL such controls. No fit if fail. Oracle is diagnostic only, not deployed policy.',
       'interaction':'For each case compute EM(EO)-EM(E)-EM(O)+EM(KEEP). Report all four outcomes and counts; positive interaction alone is not a policy win or novelty.',
       'technical_gate':'After2 complete contexts, stop if neither source-bound initial is executable; stop if any prompt_eval_count>12288 (context budget). No target inspection/quality stopping before completion.',
       'statistics':'Paired20k bootstrap(seed20102026) and exact sign/McNemar for combined vs self2; exploratory uncertainty only. No significance claim from oracle selection.',
       'limits':['24 TRAIN contexts, not test','context UID is not report identity','no guaranteed pretraining or report disjointness','source-token check is not semantic verification','not independent human annotation audit','same backbone with different scopes, not demonstrated agent skill heterogeneity'],
       'source_sha256':{f:sha(Path(__file__).with_name(f)) for f in FILES}}
    p['run_id']=digest(p)[:24];f=DEST/'plan.json'
    if f.exists():assert read(f)==p,'Frozen plan/source changed'
    else:
        atomic(f,p)
        with zipfile.ZipFile(DEST/'frozen_source.zip','w') as z:
            for name in FILES:z.write(Path(__file__).with_name(name),name)
        atomic(DEST/'registration.json',{'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
          'epoch':time.time(),'run_id':p['run_id'],'plan_sha256':sha(f),'new_responses_at_registration':len(list((DEST/'responses').glob('*.json')))})
    return p,cases

def path(case_id,action):return DEST/'responses'/f'{digest(case_id)[:16]}_{action}.json'
def collect():
    import modal
    p,cases=prepare();server=modal.Cls.from_name(APP,'TatqaScopeOllama')()
    startfile=DEST/'collection_started.json'
    if not startfile.exists():atomic(startfile,{'epoch':time.time(),'run_id':p['run_id']})
    start=read(startfile)['epoch'];completed=0;initial_valid=[]
    for n,c in enumerate(cases):
        outputs={};effective={}
        for action in ACTIONS:
            prompt_action='self' if action in ['self1','self2'] else action
            base=effective['self1'] if action=='self2' else effective.get('initial')
            current=incumbent(base) if action in ['evidence','operation','self1','self2'] else None
            f=path(c['id'],action)
            if f.exists():
                r=read(f)
                if r['state']!='completed':raise RuntimeError('Unresolved initiated call; no automatic retry')
            else:
                if time.time()-start>p['max_collection_wall_seconds']:raise RuntimeError('Collection wall budget exceeded')
                atomic(f,{'state':'initiated','run_id':p['run_id'],'case_id':c['id'],'action':action,'epoch':time.time()})
                o=server.solve.remote(c,prompt_action,current)
                r={'state':'completed','run_id':p['run_id'],'case_id':c['id'],'action':action,'output':o,'completed_epoch':time.time()};atomic(f,r)
            o=r['output'];assert o['prompt_sha256']==digest(messages(c,prompt_action,current))
            assert o['model_digest']==MODEL_DIGEST and o['live_inference'] and not o['evaluation_volume_mounted']
            assert o['actual_thinking_chars']==0 and 'L40S' in o['gpu']
            v=verify(c,o['response']['message']['content'],plain=action=='plain');assert v==o['verification']
            outputs[action]=v
            if action in ['plain','initial']:effective[action]=v
            elif action in ['self1','self2']:effective[action]=accept(base,v)
            else:effective[action]=accept(base,v,scope_ok(base['proposal'],v['proposal'],action))
            completed+=1
            print(json.dumps({'completed':completed,'cap':144,'context':n+1,'action':action,'valid':v['hard_pass'],'tokens':o['response'].get('eval_count',0)}),flush=True)
            if o['response'].get('prompt_eval_count',0)>12288:raise RuntimeError('Input context budget technical gate')
        initial_valid.append(effective['initial']['hard_pass'])
        if n==1:
            gate={'contexts':2,'initial_executable':sum(initial_valid),'passed':any(initial_valid),'uses_gold':False}
            atomic(DEST/'technical_gate.json',gate)
            if not gate['passed']:raise RuntimeError('Technical validity gate failed; do not tune on targets')
    atomic(DEST/'collection_complete.json',{'run_id':p['run_id'],'actual_new_calls':completed,'mock_calls':0,'epoch':time.time()})

def replay(c):
    raw={a:read(path(c['id'],a))['output'] for a in ACTIONS}
    v={a:verify(c,o['response']['message']['content'],plain=a=='plain') for a,o in raw.items()}
    for a in ACTIONS:assert v[a]==raw[a]['verification']
    b=v['initial'];e=accept(b,v['evidence'],scope_ok(b['proposal'],v['evidence']['proposal'],'evidence'))
    o=accept(b,v['operation'],scope_ok(b['proposal'],v['operation']['proposal'],'operation'))
    s1=accept(b,v['self1']);s2=accept(s1,v['self2']);eo,info=combined(c,b,v['evidence'],v['operation'])
    return dict(plain=v['plain'],initial=b,evidence=e,operation=o,combined=eo,self1=s1,self2=s2),raw,info

def analyze():
    import numpy as np
    p,cases=prepare();assert read(DEST/'collection_complete.json')['actual_new_calls']==144
    sys.path.insert(0,'/tmp/repguard_tatqa_eval_deps');sys.path.insert(0,str(SOURCE))
    from tatqa_metric import TaTQAEmAndF1
    labels=read(SOURCE/'annotations_private.json');rows={};costs={a:[] for a in ARMS};rawstats=[]
    for c in cases:
        effective,raw,info=replay(c);scores={}
        for a,v in effective.items():
            m=TaTQAEmAndF1();m(ground_truth=labels[c['id']],prediction=[str(v['value'])] if v['hard_pass'] else [],pred_scale=v['scale'])
            em,f1,_,_=m.get_overall_metric();scores[a]={'correct':bool(em),'em':em,'f1':f1,'value':v['value'],'scale':v['scale'],'valid':v['hard_pass']}
        deps={'plain':['plain'],'initial':['initial'],'evidence':['initial','evidence'],'operation':['initial','operation'],
              'combined':['initial','evidence','operation'],'self1':['initial','self1'],'self2':['initial','self1','self2']}
        for a,parts in deps.items():
            costs[a].append({k:sum((raw[t]['response'].get('prompt_eval_duration',0)+raw[t]['response'].get('eval_duration',0))/1e9 for t in parts) if k=='eval_seconds' else sum(raw[t]['response'].get(k,0) for t in parts) for k in ['eval_seconds','prompt_eval_count','eval_count']})
        for a,o in raw.items():
            rawstats.append({'case':c['id'],'action':a,'length_stop':o['response'].get('done_reason')=='length',
                             'input':o['response'].get('prompt_eval_count',0),'output':o['response'].get('eval_count',0)})
        interaction=int(scores['combined']['correct'])-int(scores['evidence']['correct'])-int(scores['operation']['correct'])+int(scores['initial']['correct'])
        rows[c['id']]={'arms':scores,'interaction':interaction,'joint_acceptance':info,
          'scope_ok':{a:scope_ok(effective['initial']['proposal'],raw[a]['verification']['proposal'],a) for a in ['evidence','operation']},
          'raw_errors':{a:raw[a]['verification']['errors'] for a in ACTIONS}}
    summary={}
    for a in ARMS:
        ys=[r['arms'][a] for r in rows.values()]
        summary[a]={'correct':sum(y['correct'] for y in ys),'n':24,'valid':sum(y['valid'] for y in ys),'calls_per_case':p['arms_calls'][a],
                    'mean_eval_seconds':sum(x['eval_seconds'] for x in costs[a])/24,
                    'input_tokens':sum(x['prompt_eval_count'] for x in costs[a]),'output_tokens':sum(x['eval_count'] for x in costs[a]),
                    'scale_correct':sum(y['scale']==labels[c['id']]['scale'] for y,c in zip(ys,cases))}
    control=['plain','initial','self1','self2'];scoped=['initial','evidence','operation','combined']
    best=max(summary[a]['correct'] for a in control);oracle=sum(any(r['arms'][a]['correct'] for a in scoped) for r in rows.values())
    unique=sum(any(r['arms'][a]['correct'] for a in scoped) and not any(r['arms'][a]['correct'] for a in control) for r in rows.values())
    diff=np.array([int(r['arms']['combined']['correct'])-int(r['arms']['self2']['correct']) for r in rows.values()]);rng=np.random.default_rng(20102026)
    samples=diff[rng.integers(0,24,(20000,24))].mean(axis=1)
    rescue=int((diff==1).sum());harm=int((diff==-1).sum());discord=rescue+harm
    import math
    exact=min(1.0,2*sum(math.comb(discord,k) for k in range(min(rescue,harm)+1))/2**discord) if discord else 1.0
    result={'run_id':p['run_id'],'actual_new_calls':144,'mock_calls':0,'questions':24,'methods':summary,
            'scoped_oracle_diagnostic':oracle,'best_fixed_unrestricted_control':best,'scoped_unique_vs_all_unrestricted':unique,
            'headroom_gate_pass':oracle>=best+2 and unique>=2,'history_learner_fitted':False,'reputation_win_claim':False,
            'interaction_counts':{str(i):sum(r['interaction']==i for r in rows.values()) for i in [-2,-1,0,1,2]},
            'combined_vs_self2':{'rescues':rescue,'harms':harm,'delta_pp':100*float(diff.mean()),'paired_bootstrap95_pp':[100*float(x) for x in np.quantile(samples,[.025,.975])],'exact_mcnemar_p':exact},
            'real_new_input_tokens':sum(r['input'] for r in rawstats),'real_new_output_tokens':sum(r['output'] for r in rawstats),
            'length_stops':sum(r['length_stop'] for r in rawstats),'limits':p['limits']}
    atomic(DEST/'traces_private.json',{'rows':rows,'costs':costs,'raw_stats':rawstats});atomic(DEST/'summary.json',result)
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','collect','analyze'])
    cmd=parser.parse_args().command
    if cmd=='prepare':print(json.dumps({'run_id':prepare()[0]['run_id'],'cap':144}))
    else:{'collect':collect,'analyze':analyze}[cmd]()
