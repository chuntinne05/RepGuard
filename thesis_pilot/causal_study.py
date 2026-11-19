"""Preregister, collect real causal probes, then a bounded fresh repair study."""
import argparse
import hashlib
import json
import time
import zipfile
from pathlib import Path
from .cli import ROOT,OUT,DATA_SHA,read
from .core import digest,visible_record,normalized,correct,skill
from .pipeline import atomic
from .causal_tools import messages,verify

DEST=ROOT/'results/thesis_causal_repair_v1'
ACTIONS=['initial','self_repair','evidence_repair','plan_repair']
FILES=['causal_tools.py','causal_study.py','live_app.py','typed_tools.py','source_checks.py','core.py']

def prepare():
    if (DEST/'plan.json').exists():return read(DEST/'plan.json')
    packet=read(OUT/'packet_private.json');rawpath=OUT/'finqa_train_private.json'
    assert hashlib.sha256(rawpath.read_bytes()).hexdigest()==DATA_SHA
    raw=read(rawpath);byid={r['id']:r for r in raw}
    history=[c for c in packet['visible']['cases'] if packet['visible']['partition'][c['id']]=='history'][:8]
    # Metadata-only selection. Exclude all 100 previous pilot reports, plus old archive hashes.
    excluded_reports={c['report'] for c in packet['visible']['cases']}
    excluded_q={digest(normalized(c['question'])) for c in packet['visible']['cases']}
    archive=ROOT/'results/routerbench_headroom_v1/cloud/input_private.json'
    prior_hash=set(read(archive)['datasets']['finqa/test']['query_ids']) if archive.exists() else set()
    groups={}
    for row in raw:
        c=visible_record(row)
        if c['report'] in excluded_reports or digest(normalized(c['question'])) in excluded_q:continue
        if hashlib.sha256(normalized(c['question']).encode()).hexdigest() in prior_hash:continue
        groups.setdefault(c['report'],[]).append(c)
    cases=[]
    for group in sorted(groups,key=lambda g:digest('causal-repair-v1-report:'+g)):
        cases.append(min(groups[group],key=lambda c:digest('causal-repair-v1-id:'+c['id'])))
        if len(cases)==24:break
    assert len(cases)==24 and len({c['report'] for c in cases})==24
    # Only now extract development targets and oracle sources. No final test opened.
    oracle={}
    for c in history:
        ids=set()
        for key in byid[c['id']]['qa']['gold_inds']:
            kind,index=key.split('_');index=int(index)
            if kind=='table':ids.update(f'T{index}C{i}' for i in range(len(c['table'][index])))
            else:
                prefix='P' if index<len(c['pre_text']) else 'Q'
                j=index if prefix=='P' else index-len(c['pre_text'])
                text=c['pre_text'] if prefix=='P' else c['post_text']
                ids.update(f'{prefix}{k}' for k in range(max(0,j-1),min(len(text),j+2)))
        oracle[c['id']]=sorted(ids)
    private={'gold':{c['id']:byid[c['id']]['qa']['exe_ans'] for c in history+cases},
             'qa':{c['id']:{k:byid[c['id']]['qa'][k] for k in ['program','answer','exe_ans','gold_inds']} for c in history+cases},
             'oracle_sources':oracle}
    plan={'scope':'Development mechanism experiment; NOT final confirmation or novelty proof',
      'history_diagnostic':history,'fresh_cases':cases,'selection':'SHA256 report+id; excludes all previous100 reports and prior200 question hashes',
      'model':'qwen3:14b','thinking':False,'num_predict':1536,'num_ctx':16384,'temperature':0,'seed':18102026,
      'diagnostic_arms':['initial','oracle_evidence'],'diagnostic_new_calls':16,
      'fresh_actions':ACTIONS,'max_total_new_calls':112,'max_collection_wall_seconds':3600,
      'quality_retries':False,'gold_at_deployable_inference':False,
      'diagnostic_oracle':'Only gold source spans for known8; no program/target; NEVER counted as deployable method',
      'scoring':'Unchanged FinQA exe_ans exact round5; no oracle unit/factor100 matching; semantic ambiguity flagged separately',
      'acceptance':'Repair accepted iff source program executes and satisfies edit constraint; otherwise retain initial. No semantic correctness oracle.',
      'first_gate':'Collect fresh24 initial; stop repairs if initial checked-correct <4/24',
      'headroom_gate':'Continue policy investigation only if repair union rescues >=3 and oracle union beats best fixed action by >=2/24',
      'policy':'Exploratory 3fold report-separated OOF; empirical repair-minus-harm gain, global prior4/local prior6; choose repair only predicted gain>0.05; local key=(question skill,initial source family,initial one/multi step); tie order self,evidence,plan; no tuning',
      'controls':['initial','always self_repair','each fixed repair','OOF global best action including stop','OOF contextual gain history'],
      'cost':'Report collection all112 calls separately from replay initial plus chosen repair; token cost and request seconds, not billing',
      'semantic_audit':'Preserve official score; review all initial/final discordances and known8 labels, without deleting inconvenient outcomes',
      'private_sha256':digest(private),'source_sha256':{f:hashlib.sha256(Path(__file__).with_name(f).read_bytes()).hexdigest() for f in FILES}}
    plan['run_id']=digest(plan)[:24]
    atomic(DEST/'private.json',private);atomic(DEST/'plan.json',plan)
    with zipfile.ZipFile(DEST/'frozen_source.zip','w') as z:
        for f in FILES:z.write(Path(__file__).with_name(f),f)
    return plan

def collect():
    import modal
    plan=prepare();private=read(DEST/'private.json')
    for f,h in plan['source_sha256'].items():assert hashlib.sha256(Path(__file__).with_name(f).read_bytes()).hexdigest()==h
    server=modal.Cls.from_name('repguard-thesis-real-pilot-20261018','LiveOllama')()
    begin=time.monotonic();count=0
    def request(case,action,phase,initial=None):
        nonlocal count
        target=DEST/phase/f'{digest(case["id"])[:16]}_{action}.json'
        oracle=private['oracle_sources'][case['id']] if action=='oracle_evidence' else None
        prompt=messages(case,action,initial,oracle)
        if target.exists():
            row=read(target)
            if row['state']!='completed':raise RuntimeError('Unresolved initiated call; no silent retry')
        else:
            if time.monotonic()-begin>plan['max_collection_wall_seconds']:raise RuntimeError('Collection wall cap')
            atomic(target,{'state':'initiated','case_id':case['id'],'action':action,'epoch':time.time(),'prompt_sha256':digest(prompt)})
            output=server.causal_solve.remote(case,action,initial,oracle)
            assert output['prompt_sha256']==digest(prompt)
            row={'state':'completed','case_id':case['id'],'action':action,'output':output}
            atomic(target,row)
        count+=1
        print(phase,count,case['id'],action,'value',row['output']['verification']['value'],'errors',row['output']['verification']['errors'],flush=True)
        return row['output']
    for case in plan['history_diagnostic']:
        for action in plan['diagnostic_arms']:request(case,action,'diagnostic')
    baseline={c['id']:request(c,'initial','fresh') for c in plan['fresh_cases']}
    initial_score=sum(o['verification']['hard_pass'] and correct(o['verification']['value'],private['gold'][i]) for i,o in baseline.items())
    atomic(DEST/'initial_gate.json',{'initial_correct':initial_score,'n':24,'gate_pass':initial_score>=4})
    if initial_score>=4:
        for case in plan['fresh_cases']:
            initial=baseline[case['id']]['verification']['answer']
            if initial is None:
                # Keep malformed raw response as public data; constrained arms will fail safely.
                initial={'reasoning':'Initial output malformed','status':'insufficient_evidence','steps':[],'display_unit':'number'}
            for action in ACTIONS[1:]:request(case,action,'fresh',initial)
    report()

def report():
    plan=read(DEST/'plan.json');private=read(DEST/'private.json');rows=[]
    with zipfile.ZipFile(DEST/'frozen_source.zip') as z:
        for f,h in plan['source_sha256'].items():assert hashlib.sha256(z.read(f)).hexdigest()==h
    for phase in ['diagnostic','fresh']:
        cases={c['id']:c for c in plan['history_diagnostic' if phase=='diagnostic' else 'fresh_cases']}
        for path in sorted((DEST/phase).glob('*.json')):
            row=read(path);assert row['state']=='completed';case=cases[row['case_id']];o=row['output']
            initial=None
            if row['action'] in ACTIONS[1:]:
                b=read(DEST/phase/f'{digest(case["id"])[:16]}_initial.json')['output']['verification']['answer']
                initial=b or {'reasoning':'Initial output malformed','status':'insufficient_evidence','steps':[],'display_unit':'number'}
            oracle=private['oracle_sources'][case['id']] if row['action']=='oracle_evidence' else None
            assert digest(messages(case,row['action'],initial,oracle))==o['prompt_sha256']
            assert verify(case,o['response']['message']['content'],row['action'],initial)==o['verification']
            assert o['live_inference'] and not o['evaluation_volume_mounted'] and o['model_digest']=='bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8'
            rows.append({**row,'phase':phase})
    result={'run_id':plan['run_id'],'scope':plan['scope'],'actual_new_calls':len(rows),'mock_calls':0,
      'independently_recomputed_responses':len(rows),'input_tokens':sum(r['output']['response'].get('prompt_eval_count',0) for r in rows),
      'output_tokens':sum(r['output']['response'].get('eval_count',0) for r in rows),
      'request_wall_seconds':sum(r['output']['wall_seconds'] for r in rows),
      'diagnostic':{},'fresh':{},'initial_gate':read(DEST/'initial_gate.json')}
    for action in plan['diagnostic_arms']:
        rr=[r for r in rows if r['phase']=='diagnostic' and r['action']==action]
        result['diagnostic'][action]={'n':len(rr),'hard_pass':sum(r['output']['verification']['hard_pass'] for r in rr),
         'correct':sum(r['output']['verification']['hard_pass'] and correct(r['output']['verification']['value'],private['gold'][r['case_id']]) for r in rr)}
    fresh={c['id']:{r['action']:r['output'] for r in rows if r['phase']=='fresh' and r['case_id']==c['id']} for c in plan['fresh_cases']}
    if all(set(x)==set(ACTIONS) for x in fresh.values()):
        outcomes={};costs={}
        for i,rr in fresh.items():
            outcomes[i]={};costs[i]={}
            b=rr['initial']['verification']
            for action,o in rr.items():
                v=o['verification'] if o['verification']['hard_pass'] else b
                outcomes[i][action]=int(v['hard_pass'] and correct(v['value'],private['gold'][i]))
                costs[i][action]=sum(o['response'].get(k,0) for k in ['prompt_eval_count','eval_count'])
        for action in ACTIONS:
            result['fresh'][action]={'correct':sum(x[action] for x in outcomes.values()),'n':24,
             'rescue':sum(x[action]>x['initial'] for x in outcomes.values()),'harm':sum(x[action]<x['initial'] for x in outcomes.values()),
             'accepted_edits':sum(rr[action]['verification']['hard_pass'] for rr in fresh.values()),
             'mean_serving_tokens':sum(costs[i]['initial']+(0 if action=='initial' else costs[i][action]) for i in fresh)/24}
        union=sum(max(x.values()) for x in outcomes.values());best=max(sum(x[a] for x in outcomes.values()) for a in ACTIONS)
        result['headroom_gate']={'oracle_union_correct':union,'best_fixed_correct':best,'union_rescues':union-result['fresh']['initial']['correct'],'gate_pass':union-result['fresh']['initial']['correct']>=3 and union-best>=2,'oracle_is_not_a_method':True}
        if result['headroom_gate']['gate_pass']:
            cases={c['id']:c for c in plan['fresh_cases']}
            def key(i):
                v=fresh[i]['initial']['verification'];ss=v['sources'];family='mixed' if any(s['source'].startswith('T') for s in ss) and any(not s['source'].startswith('T') for s in ss) else 'table' if any(s['source'].startswith('T') for s in ss) else 'text'
                return (skill(cases[i]['question']),family,'multi' if len((v['answer'] or {}).get('steps',[]))>1 else 'one')
            ids=sorted(fresh,key=lambda i:digest('causal-repair-fold:'+cases[i]['report']))
            folds={i:j%3 for j,i in enumerate(ids)};traces=[]
            for i in ids:
                train=[j for j in ids if folds[j]!=folds[i]];local=[j for j in train if key(j)==key(i)]
                global_gain={a:sum(outcomes[j][a]-outcomes[j]['initial'] for j in train)/(len(train)+4) for a in ACTIONS[1:]}
                local_gain={a:(sum(outcomes[j][a]-outcomes[j]['initial'] for j in local)+6*global_gain[a])/(len(local)+6) for a in ACTIONS[1:]}
                def choose(g):
                    a=max(ACTIONS[1:],key=lambda a:g[a]);return a if g[a]>.05 else 'initial'
                traces.append({'case_id':i,'fold':folds[i],'train_n':len(train),'local_n':len(local),'key':key(i),'global_gains':global_gain,'local_gains':local_gain,'global_action':choose(global_gain),'local_action':choose(local_gain)})
            for name,field in [('oof_global_history','global_action'),('oof_contextual_history','local_action')]:
                picks={t['case_id']:t[field] for t in traces}
                result['fresh'][name]={'correct':sum(outcomes[i][a] for i,a in picks.items()),'n':24,
                 'repair_calls':sum(a!='initial' for a in picks.values()),'mean_serving_tokens':sum(costs[i]['initial']+(0 if a=='initial' else costs[i][a]) for i,a in picks.items())/24}
            atomic(DEST/'oof_traces_private.json',traces)
        atomic(DEST/'outcomes_private.json',{'outcomes':outcomes,'costs':costs})
    atomic(DEST/'summary.json',result);atomic(ROOT/'docs/analysis/repguard_causal_repair_results_2026-10-18.json',result)
    print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','collect','report']);a=p.parse_args()
    if a.command=='prepare':print(json.dumps(prepare(),indent=2))
    elif a.command=='collect':collect()
    else:report()
