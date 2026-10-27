"""Post-hoc capability and cross-family control; scopes' primary results preserved."""
import argparse
import hashlib
import json
import sys
import time
import zipfile
from pathlib import Path
from .core import digest
from .pipeline import atomic
from .tatqa_scope_tools import verify,incumbent,accept
from .tatqa_plain_tools import messages

ROOT=Path(__file__).resolve().parents[1];DEST=ROOT/'results/thesis_tatqa_crossfamily_v1'
PARENT=ROOT/'results/thesis_tatqa_scoped_repair_v1';SOURCE=ROOT/'results/thesis_tatqa_source_v1'
QMODEL='qwen3.5:27b';GMODEL='gemma4:26b-a4b-it-q4_K_M'
QAPP='repguard-thesis-modern-backbone-20261019';GAPP='repguard-thesis-crossfamily-20261020'
FILES=['tatqa_crossfamily_study.py','tatqa_crossfamily_app.py','tatqa_plain_review_app.py','tatqa_plain_tools.py',
       'tatqa_scope_app.py','tatqa_scope_tools.py','modern_direct_app.py','modern_probe_app.py','pot_tools.py','core.py','pipeline.py','modal_app.py']
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def prepare():
    source=read(PARENT/'plan.json');cases=source['public_cases'];manifest=read(DEST/'model_manifest.json');g=manifest['models'][GMODEL]
    assert g['digest'].startswith('5571076f3d70') and g['details']['quantization_level']=='Q4_K_M'
    p={'scope':'Post-hoc whole24context capability control and cross-family headroom probe, not independent confirmation or reputation method.',
       'trigger':'Source-bound contract rejects legitimate averaging divisor3; prior pools used closely related Qwen models. Test unrestricted same-model review and a different model family. Do not change original scoped protocol.',
       'selected_before':'No TAT-QA target scores inspected at design; model chosen from official tag metadata, not comparative outcomes.',
       'public_cases':cases,'case_ids':source['case_ids'],'parent_plan_sha256':sha(PARENT/'plan.json'),
       'models':{'qwen':{'name':QMODEL,'digest':source['model_digest'],'app':QAPP,'class':'TatqaPlainReviewOllama'},
                 'gemma':{'name':GMODEL,'digest':g['digest'],'app':GAPP,'class':'TatqaGemmaOllama'}},
       'gemma_manifest_sha256':sha(DEST/'model_manifest.json'),'thinking':False,'temperature':0,'seed':20102026,
       'num_ctx':16384,'num_predict':4096,'gpu':'L40S','max_new_calls':120,'max_wall_seconds':10800,
       'jobs':'Qwen self1/self2 for all24 from cached REAL parent plain outputs (48 new), then Gemma plain/self1/self2 for all24 (72 new). Sequential calls, no quality retry.',
       'comparability':'Identical public raw source/catalogue, plain Python/schema/executor and review prompt across families. Qwen direct reused EXACT existing prompt. No binding/count-literal restriction for either family.',
       'sampling_limit':'One greedy sample per case/arm. Temperature0 standardized; not Gemma recommended temperature1.0. This tests declared configurations, not maximized model capacity.',
       'acceptance':'Execute candidate; if invalid retain previous. No target/gold selector. Count both rescues and harms.',
       'scoring':'Pinned official TAT-QA evaluator, model-predicted scale, nonempty list[str(value)] including zero, invalid/abstain EM0. No original scores rewritten.',
       'metric_sha256':sha(SOURCE/'tatqa_metric.py'),'utils_sha256':sha(SOURCE/'tatqa_utils.py'),
       'gate':'For future cross-family history collection, union of all6 workflows >= best fixed workflow+2 cases AND at least one case uniquely correct in each family (relative to union of other family). Oracle diagnostic only. No learner fitted on this control.',
       'technical_gate':'After first2 Gemma contexts, stop if neither direct response executable, or if any prompt_eval_count>12288. Stop unresolved initiated call; no silent retry.',
       'paired_inference':'Qwen plain-self2 vs scoped-self2 on ALL24, exact McNemar and paired20kbootstrap(seed20102026). Post-hoc configuration comparison, not independent method gain.',
       'compute':'Each workflow1/2/3 calls, including reused direct parent generation cost. Report actual eval seconds and tokens, not billed cost or isolated backbone causality.',
       'limits':source['limits']+['Post-hoc capability control','Different-family labels do not establish useful predictable specialization','No human semantic adjudication'],
       'source_sha256':{f:sha(Path(__file__).with_name(f)) for f in FILES}}
    p['run_id']=digest(p)[:24];f=DEST/'plan.json'
    if f.exists():assert read(f)==p,'Frozen source or metadata changed'
    else:
        atomic(f,p)
        with zipfile.ZipFile(DEST/'frozen_source.zip','w') as z:
            for name in FILES:z.write(Path(__file__).with_name(name),name)
        atomic(DEST/'registration.json',{'epoch':time.time(),'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
               'run_id':p['run_id'],'plan_sha256':sha(f),'new_responses_at_registration':len(list((DEST/'responses').glob('*.json')))})
    return p,cases

def path(case_id,family,action):return DEST/'responses'/f'{digest(case_id)[:16]}_{family}_{action}.json'
def parent(case):return read(PARENT/'responses'/f'{digest(case["id"])[:16]}_plain.json')['output']
def collect():
    import modal
    p,cases=prepare();assert read(PARENT/'collection_complete.json')['actual_new_calls']==144
    startfile=DEST/'collection_started.json'
    if not startfile.exists():atomic(startfile,{'epoch':time.time(),'run_id':p['run_id']})
    start=read(startfile)['epoch'];completed=0
    for family in ['qwen','gemma']:
        cfg=p['models'][family];server=modal.Cls.from_name(cfg['app'],cfg['class'])();directs=[]
        for n,c in enumerate(cases):
            current=None
            if family=='qwen':
                cached=parent(c);assert cached['prompt_sha256']==digest(messages(c)) and cached['model_digest']==cfg['digest']
                assert verify(c,cached['response']['message']['content'],plain=True)==cached['verification'];current=cached['verification']
            for action in (['self1','self2'] if family=='qwen' else ['plain','self1','self2']):
                context=incumbent(current) if current is not None else None;f=path(c['id'],family,action)
                if f.exists():
                    r=read(f)
                    if r['state']!='completed':raise RuntimeError('Unresolved initiated call; no automatic retry')
                else:
                    if time.time()-start>p['max_wall_seconds']:raise RuntimeError('Wall budget')
                    atomic(f,{'state':'initiated','run_id':p['run_id'],'case_id':c['id'],'family':family,'action':action,'epoch':time.time()})
                    o=server.solve.remote(c,context);r={'state':'completed','run_id':p['run_id'],'case_id':c['id'],'family':family,'action':action,'output':o,'completed_epoch':time.time()};atomic(f,r)
                o=r['output'];assert o['prompt_sha256']==digest(messages(c,context)) and o['model_digest']==cfg['digest']
                assert o['live_inference'] and not o['evaluation_volume_mounted'] and o['actual_thinking_chars']==0
                assert 'L40S' in o['gpu'];v=verify(c,o['response']['message']['content'],plain=True);assert v==o['verification']
                current=accept(current,v) if current is not None else v;completed+=1
                if action=='plain':directs.append(v['hard_pass'])
                print(json.dumps({'completed':completed,'cap':120,'family':family,'context':n+1,'action':action,'valid':v['hard_pass'],'tokens':o['response'].get('eval_count',0)}),flush=True)
                if o['response'].get('prompt_eval_count',0)>12288:raise RuntimeError('Context budget technical gate')
            if family=='gemma' and n==1:
                gate={'contexts':2,'direct_executable':sum(directs),'passed':any(directs),'uses_gold':False};atomic(DEST/'technical_gate.json',gate)
                if not gate['passed']:raise RuntimeError('Gemma interface adequacy gate failed')
    atomic(DEST/'collection_complete.json',{'actual_new_calls':completed,'mock_calls':0,'epoch':time.time(),'run_id':p['run_id']})

def replay(case,p):
    effective={};outputs={}
    for family in ['qwen','gemma']:
        previous=None
        for action in ['plain','self1','self2']:
            o=parent(case) if family=='qwen' and action=='plain' else read(path(case['id'],family,action))['output']
            assert o['prompt_sha256']==digest(messages(case,incumbent(previous) if previous is not None else None))
            assert o['model_digest']==p['models'][family]['digest'] and o['live_inference'] and not o['evaluation_volume_mounted'] and o['actual_thinking_chars']==0
            v=verify(case,o['response']['message']['content'],plain=True);assert v==o['verification']
            previous=accept(previous,v) if previous is not None else v
            effective[f'{family}_{action}']=previous;outputs[f'{family}_{action}']=o
    return effective,outputs

def analyze():
    import numpy as np,math
    p,cases=prepare();assert read(DEST/'collection_complete.json')['actual_new_calls']==120
    sys.path.insert(0,'/tmp/repguard_tatqa_eval_deps');sys.path.insert(0,str(SOURCE));from tatqa_metric import TaTQAEmAndF1
    labels=read(SOURCE/'annotations_private.json');rows={};metrics={f'{f}_{a}':{'correct':0,'valid':0,'scale_correct':0,'n':24,'eval_seconds':0,'input_tokens':0,'output_tokens':0,'calls_per_case':n+1} for f in ['qwen','gemma'] for n,a in enumerate(['plain','self1','self2'])}
    newraw=[]
    for c in cases:
        effective,outputs=replay(c,p);rr={}
        for name,v in effective.items():
            m=TaTQAEmAndF1();m(ground_truth=labels[c['id']],prediction=[str(v['value'])] if v['hard_pass'] else [],pred_scale=v['scale']);em=m.get_overall_metric()[0]
            rr[name]={'correct':bool(em),'value':v['value'],'scale':v['scale'],'valid':v['hard_pass']}
            metric=metrics[name];metric['correct']+=bool(em);metric['valid']+=v['hard_pass'];metric['scale_correct']+=v['scale']==labels[c['id']]['scale']
            family,action=name.split('_');parts=['plain','self1','self2'][:['plain','self1','self2'].index(action)+1]
            for part in parts:
                resp=outputs[f'{family}_{part}']['response'];metric['eval_seconds']+=(resp.get('prompt_eval_duration',0)+resp.get('eval_duration',0))/1e9;metric['input_tokens']+=resp.get('prompt_eval_count',0);metric['output_tokens']+=resp.get('eval_count',0)
        for name,o in outputs.items():
            if name!='qwen_plain':newraw.append({'case':c['id'],'arm':name,'input':o['response'].get('prompt_eval_count',0),'output':o['response'].get('eval_count',0),'length_stop':o['response'].get('done_reason')=='length'})
        rows[c['id']]=rr
    for m in metrics.values():m['mean_eval_seconds']=m.pop('eval_seconds')/24
    q=['qwen_plain','qwen_self1','qwen_self2'];g=['gemma_plain','gemma_self1','gemma_self2'];best=max(m['correct'] for m in metrics.values())
    union=sum(any(v['correct'] for v in r.values()) for r in rows.values());unique={f:sum(any(r[a]['correct'] for a in own) and not any(r[a]['correct'] for a in other) for r in rows.values()) for f,own,other in [('qwen',q,g),('gemma',g,q)]}
    old=read(PARENT/'traces_private.json')['rows'];diff=np.array([int(rows[c['id']]['qwen_self2']['correct'])-int(old[c['id']]['arms']['self2']['correct']) for c in cases]);rng=np.random.default_rng(20102026)
    ci=np.quantile(diff[rng.integers(0,24,(20000,24))].mean(axis=1),[.025,.975]);rescue=int((diff==1).sum());harm=int((diff==-1).sum());disc=rescue+harm
    exact=min(1.,2*sum(math.comb(disc,i) for i in range(min(rescue,harm)+1))/2**disc) if disc else 1.
    summary={'run_id':p['run_id'],'scope':p['scope'],'actual_new_calls':120,'reused_real_calls':24,'mock_calls':0,'methods':metrics,
             'oracle_union_diagnostic':union,'best_fixed':best,'unique_family_cases':unique,'headroom_gate_pass':union>=best+2 and min(unique.values())>=1,
             'history_learner_fitted':False,'reputation_superiority_claim':False,
             'qwen_plain_self2_vs_scoped_self2':{'rescues':rescue,'harms':harm,'delta_pp':100*float(diff.mean()),'paired_bootstrap95_pp':[100*float(x) for x in ci],'exact_mcnemar_p':exact},
             'new_input_tokens':sum(r['input'] for r in newraw),'new_output_tokens':sum(r['output'] for r in newraw),'length_stops':sum(r['length_stop'] for r in newraw),'limits':p['limits']}
    atomic(DEST/'summary.json',summary);atomic(DEST/'traces_private.json',{'rows':rows,'new_raw_stats':newraw});print(json.dumps(summary,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','collect','analyze']);cmd=parser.parse_args().command
    if cmd=='prepare':print(json.dumps({'run_id':prepare()[0]['run_id'],'cap':120}))
    else:{'collect':collect,'analyze':analyze}[cmd]()
