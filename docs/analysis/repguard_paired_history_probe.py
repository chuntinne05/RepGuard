"""Exploratory OOF action-history test on REAL counterfactual outputs.

Not an independent test, a novel method claim, or live-policy validation.
Register analysis before inspecting the newly collected PoT outputs.
"""
import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))
from thesis_pilot.core import digest,correct,skill
from thesis_pilot.causal_tools import verify
from thesis_pilot.program_integrity_v2 import inspect_program
from repguard_unit_failure_diagnostic import surgery

PLAN=HERE/'repguard_paired_history_analysis_plan_2026-10-18.json'

def read(p):return json.loads(p.read_text())

def register():
    p={'scope':'Exploratory pre-analysis after inspecting cheap development outputs, before opening newly collected PoT outputs. NOT preregistration before all model generation and NOT independent confirmation.',
      'new_inference_calls':0,'max_repairs':1,'dataset':'Same24development reports as causal v1',
      'cheap':'Real initial DSL plus the fixed post-hoc source-only unit surgery, mechanically executed',
      'regenerate':'Real independent native-PoT output; if invalid, retain cheap; no gold-based acceptance',
      'guard':'Regenerate if cheap hard_pass false or final program has no valid evidence dependency; available equally to rule/history controls',
      'controls':['cheap','direct_pot','always_regenerate_with_fallback','rule_guard_only','oof_global_history','oof_local_history'],
      'gate':'Fit history only if regenerate rescues at least3cheap errors; otherwise record lack of signal',
      'folds':'3, report-separated SHA256 causal-repair-fold, unchanged from earlier proposed learner',
      'learner':'Exclude guard-forced cases from discretionary training; global net-gain sum/(n+4); local tuple(question skill,source family,one/multi-step) shrinks to global with prior6; regenerate iff gain>0.05; no hyperparameter tuning',
      'gold':'Full supervised paired labels shared with all history controls, not a10%audit result; case label excluded from its fold training',
      'cost':'All responses collected for research; policy serving replay counts cheap+selected calls, plus measured Ollama prompt_eval_duration+eval_duration. Compute-time proxy, not USD billing or live latency.',
      'uncertainty':'20,000 paired report bootstraps, seed18102026; one-sided exact95%harm upper bound; 2ppNI margin cannot be established merely by bootstrapzero difference on24cases',
      'known_limits':'Cheap unit surgery and feature design used prior development outcomes; this OOF remains exploratory; source/semantic correctness and final prototype not established',
      'registered_epoch':time.time(),'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      'helper_sha256':{f:hashlib.sha256((HERE/f).read_bytes()).hexdigest() for f in ['repguard_unit_failure_diagnostic.py']}}
    if PLAN.exists():raise RuntimeError('Analysis plan already registered; do not overwrite')
    PLAN.write_text(json.dumps(p,indent=2));print(json.dumps({'registered':True,'source_sha256':p['source_sha256'],'new_inference_calls':0}))

def harm_upper(h,n):
    if h==n:return 1.
    lo,hi=0.,1.
    for _ in range(70):
        p=(lo+hi)/2;cdf=sum(math.comb(n,j)*p**j*(1-p)**(n-j) for j in range(h+1))
        if cdf>.05:lo=p
        else:hi=p
    return (lo+hi)/2

def main():
    import numpy as np
    p=read(PLAN);assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==p['source_sha256']
    for f,h in p['helper_sha256'].items():assert hashlib.sha256((HERE/f).read_bytes()).hexdigest()==h
    dest=ROOT/'results/thesis_causal_repair_v1';study=read(dest/'plan.json');private=read(dest/'private.json')
    read(ROOT/'results/thesis_pot_control_v1/summary.json')  # Require complete collection.
    cases={c['id']:c for c in study['fresh_cases']};ids=sorted(cases,key=lambda i:digest('causal-repair-fold:'+cases[i]['report']))
    data={}
    def cost(o):
        r=o['response']
        if not all(k in r for k in ['prompt_eval_duration','eval_duration']):raise ValueError('Missing measured compute times')
        return (r['prompt_eval_duration']+r['eval_duration'])/1e9
    for i in ids:
        c=cases[i];initial=read(dest/'fresh'/f'{digest(i)[:16]}_initial.json')['output']
        regen=read(ROOT/'results/thesis_pot_control_v1'/f'{digest(i)[:16]}.json')['output']
        b=initial['verification'];a,changed=surgery(b['answer']);cheap=verify(c,json.dumps(a)) if changed else b
        rv=regen['verification'];after=rv if rv['hard_pass'] else cheap
        def score(v):return int(v['hard_pass'] and correct(v['value'],private['gold'][i]))
        integrity=inspect_program(cheap['answer']);guard=not cheap['hard_pass'] or bool(integrity['errors'])
        ss=cheap.get('sources',[]);table=any(s['source'].startswith('T') for s in ss);text=any(not s['source'].startswith('T') for s in ss)
        family='mixed' if table and text else 'table' if table else 'text'
        key=(skill(c['question']),family,'multi' if len((cheap['answer'] or {}).get('steps',[]))>1 else 'one')
        data[i]={'cheap':score(cheap),'direct_pot':score(rv),'regen':score(after),
          'cheap_cost':cost(initial),'regen_cost':cost(regen),'guard':guard,'key':key}
    rescues=sum(d['regen']>d['cheap'] for d in data.values());harms=sum(d['regen']<d['cheap'] for d in data.values())
    gate=rescues>=3;fold={i:j%3 for j,i in enumerate(ids)};traces=[]
    for i in ids:
        d=data[i];train=[j for j in ids if fold[j]!=fold[i] and not data[j]['guard']]
        assert i not in train and all(cases[j]['report']!=cases[i]['report'] for j in train)
        local=[j for j in train if data[j]['key']==d['key']]
        g=sum(data[j]['regen']-data[j]['cheap'] for j in train)/(len(train)+4)
        l=(sum(data[j]['regen']-data[j]['cheap'] for j in local)+6*g)/(len(local)+6)
        traces.append({'id':i,'fold':fold[i],'train_ids':train,'local_ids':local,'key':d['key'],'forced_guard':d['guard'],
          'global_gain':g,'local_gain':l,'global_regenerate':bool(d['guard'] or g>.05) if gate else None,
          'local_regenerate':bool(d['guard'] or l>.05) if gate else None})
    policies=['cheap','direct_pot','always_regenerate_with_fallback','rule_guard_only']+(['oof_global_history','oof_local_history'] if gate else [])
    scores={};costs={};calls={}
    byid={t['id']:t for t in traces}
    for name in policies:
        scores[name]=[];costs[name]=[];calls[name]=[]
        for i in ids:
            d=data[i]
            if name=='direct_pot':y,c,n=d['direct_pot'],d['regen_cost'],1
            else:
                invoke=(name=='always_regenerate_with_fallback' or (name=='rule_guard_only' and d['guard']) or
                   (name=='oof_global_history' and byid[i]['global_regenerate']) or (name=='oof_local_history' and byid[i]['local_regenerate']))
                y=d['regen'] if invoke else d['cheap'];c=d['cheap_cost']+(d['regen_cost'] if invoke else 0);n=1+int(invoke)
            scores[name].append(y);costs[name].append(c);calls[name].append(n)
    rng=np.random.default_rng(18102026);samples=rng.integers(0,len(ids),size=(20000,len(ids)));out={}
    base=np.asarray(scores['direct_pot']);base_cost=np.asarray(costs['direct_pot'])
    for name in policies:
        s=np.asarray(scores[name]);co=np.asarray(costs[name]);delta=s-base;h=int(sum((base==1)&(s==0)))
        ratio=(co[samples].mean(axis=1)/base_cost[samples].mean(axis=1))
        out[name]={'correct':int(s.sum()),'n':len(ids),'mean_model_calls':float(np.mean(calls[name])),
          'mean_ollama_eval_seconds':float(co.mean()),'accuracy_diff_vs_direct_pot':float(delta.mean()),
          'paired_bootstrap_diff_ci95':[float(x) for x in np.quantile(delta[samples].mean(axis=1),[.025,.975])],
          'rescue_vs_direct_pot':int(sum((base==0)&(s==1))),'harm_vs_direct_pot':h,
          'harm_probability_exact_upper95':harm_upper(h,len(ids)),
          'compute_ratio_vs_direct_pot':float(co.mean()/base_cost.mean()),'paired_compute_ratio_ci95':[float(x) for x in np.quantile(ratio,[.025,.975])]}
    result={'scope':p['scope'],'history_fit_gate':{'pass':gate,'regen_rescues':rescues,'regen_harms':harms},
      'real_responses_used':48,'new_model_calls':0,'current_case_gold_excluded_from_OOF_training':True,
      'methods':out,'independent_confirmation':False,'live_policy_tested':False,
      'ni_margin':.02,'zero_harm_upper95_at_n24':harm_upper(0,24),
      'source_sha256':p['source_sha256'],'helper_sha256':p['helper_sha256']}
    outdir=ROOT/'results/thesis_paired_history_probe_v1';outdir.mkdir(exist_ok=True)
    (outdir/'traces_private.json').write_text(json.dumps({'data':data,'traces':traces},indent=2))
    (outdir/'plan.json').write_text(json.dumps(p,indent=2));(outdir/'summary.json').write_text(json.dumps(result,indent=2))
    (HERE/'repguard_paired_history_probe_2026-10-18.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('command',choices=['register','analyze']);q=a.parse_args()
    if q.command=='register':register()
    else:main()
