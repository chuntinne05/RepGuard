"""Single locked paired-audit ablation; real archived outcomes, no model calls."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from analyze_dart_leaderboard import cluster_ci
from run_dart_audit_pilot import digest, summarize, write_status
from repguard.audit.paired import paired_sample, select_paired
from repguard.audit.routing import TextFeatures, calibrated_proxy, global_means, knn_routes, policy_bank

METHODS = ('PairedAuditOnly', 'PairedHistory', 'PairedGlobal', 'PairedKNN')


def run(args: argparse.Namespace) -> None:
    old_status = json.loads((args.reference / 'status.json').read_text())
    if old_status['state'] != 'completed':
        raise ValueError('Reference replay must complete before paired ablation')
    if args.output.exists():
        raise ValueError('Refusing to overwrite an existing ablation')
    matrix = json.loads(Path('results/dart_leaderboard_v1/outcomes_private.json').read_text())
    feedback = json.loads((args.reference / 'feedback_private.json').read_text())
    old = json.loads((args.reference / 'predictions_private.json').read_text())
    ids, agents = matrix['task_ids'], matrix['agents']
    if feedback['task_ids'] != ids or feedback['agents'] != agents or old['task_ids'] != ids:
        raise ValueError('Source matrix alignment mismatch')
    f, y = np.array(feedback['feedback']), np.array(matrix['success'])
    traces = [json.loads(x) for x in (args.reference / 'audit_trace_private.jsonl').read_text().splitlines()]
    rows = [r for r in traces if r['method'] == 'RandomHistory']
    if len(rows) != 300 or len({(r['fold'],r['seed'],r['budget_fraction']) for r in rows}) != 300:
        raise ValueError('Need all frozen reference fold/budget/seed cases')
    lookup = {t: i for i,t in enumerate(ids)}
    texts = []
    for t in ids:
        spec = json.loads((args.data_root / 'tasks' / t / 'specs.json').read_text())
        if spec['db_version'] != '0.1.0':
            raise ValueError('Instruction version mismatch')
        texts.append(spec['instruction'])
    sources = ['run_dart_paired_ablation.py','src/repguard/audit/paired.py',
               'src/repguard/audit/routing.py','src/repguard/audit/design.py',
               'run_dart_audit_pilot.py','analyze_dart_leaderboard.py']
    manifest = {'protocol': 'docs/analysis/dart_paired_audit_ablation_protocol_2026-10-04.md',
                'source_sha256': {s: hashlib.sha256(Path(s).read_bytes()).hexdigest() for s in sources},
                'reference_manifest_sha256': hashlib.sha256((args.reference/'manifest.json').read_bytes()).hexdigest(),
                'matrix_sha256':digest(matrix),'feedback_sha256':digest(feedback),'instructions_sha256':digest(texts),
                'methods':METHODS,'seeds':list(range(20)),'budgets':[.05,.1,.2],
                'new_inference_calls':0,'independent_confirmation':False}
    args.output.mkdir(parents=True)
    (args.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    predictions = {str(b):{m:np.full((20,168),np.nan) for m in METHODS} for b in [.05,.1,.2]}
    cache = {}
    write_status(args.output,state='running',completed=0,total=300)
    for step,row in enumerate(rows,1):
        fold,seed,budget = row['fold'],row['seed'],str(row['budget_fraction'])
        if fold not in cache:
            c,s,t = [np.array([lookup[z] for z in row[key]]) for key in
                     ('construction_ids','selection_ids','test_ids')]
            train=np.array(sorted(set(c.tolist()+s.tolist())))
            if set(train)&set(t):
                raise ValueError('Training/test overlap')
            enc=TextFeatures([texts[i] for i in c]); xc=enc.transform([texts[i] for i in c])
            ss=enc.transform([texts[i] for i in s])@xc.T
            st=enc.transform([texts[i] for i in t])@xc.T
            allenc=TextFeatures([texts[i] for i in train])
            allsim=allenc.transform([texts[i] for i in t])@allenc.transform([texts[i] for i in train]).T
            cache[fold]=(c,s,t,train,ss,st,allsim)
        c,s,t,train,ss,st,allsim=cache[fold]
        anchors=np.full((len(c),len(agents)),np.nan)
        anchor_ix=row['anchor_indices']; anchors.ravel()[anchor_ix]=y[c].ravel()[anchor_ix]
        names,rs=policy_bank(ss,anchors); _,rt=policy_bank(st,anchors)
        if rt[row['selected_policy']].tolist()!=row['test_agent_choices']:
            raise ValueError('Reference bank reconstruction mismatch')
        proxy=calibrated_proxy(f[c],anchors,f[s]); baseline=int(global_means(anchors).argmax())
        choices={}; logs=[]
        for method in ('PairedAuditOnly','PairedHistory'):
            selected=select_paired(rs,proxy,baseline,row['selection_budget'],
                                   np.random.default_rng(22004+100*seed+fold),
                                   lambda indices:y[s].ravel()[indices].copy(),
                                   use_proxy=method=='PairedHistory')
            choices[method]=rt[selected['selected_policy']]
            logs.append({'method':method,'anchor_indices':anchor_ix,
                         'construction_ids':row['construction_ids'],'selection_ids':row['selection_ids'],
                         **selected})
        total=row['total_audits']
        full_ix=paired_sample((len(train),len(agents)),total,np.random.default_rng(44004+100*seed+fold))
        full_labels=np.full((len(train),len(agents)),np.nan)
        full_labels.ravel()[full_ix]=y[train].ravel()[full_ix]
        choices['PairedGlobal']=np.full(len(t),int(global_means(full_labels).argmax()))
        choices['PairedKNN']=knn_routes(allsim,full_labels,10)
        for method in ('PairedGlobal','PairedKNN'):
            logs.append({'method':method,'training_ids':[ids[i] for i in train],
                         'audit_indices':full_ix.tolist()})
        # Look up held-out labels only after all routing actions above are fixed.
        for method,actions in choices.items():
            predictions[budget][method][seed,t]=y[t,actions]
        with (args.output/'audit_trace_private.jsonl').open('a') as handle:
            for record in logs:
                handle.write(json.dumps({**record,'fold':fold,'seed':seed,'budget_fraction':float(budget),
                   'total_audits':total,'test_ids':row['test_ids'],
                   'test_agent_choices':choices[record['method']].tolist()})+'\n')
        write_status(args.output,state='running',completed=step,total=300)
    merged={b:{**old['predictions'][b],**{m:v.tolist() for m,v in methods.items()}}
            for b,methods in predictions.items()}
    result=summarize(merged,ids,20,primary_method='PairedHistory')
    result['feedback']=feedback['provenance']
    result['scope']='exploratory paired-audit design ablation; not a new DART superiority claim'
    groups=[t.rsplit('_',1)[0] for t in ids]
    for budget,data in result['budgets'].items():
        contrasts=data.pop('DART_contrasts')
        for comparator in ('DARTContrast','PairedGlobal','PairedAuditOnly'):
            delta=(np.array(merged[budget]['PairedHistory'])-np.array(merged[budget][comparator])).mean(axis=0)
            contrasts[comparator]={'difference':float(delta.mean()),'generator_cluster_ci95':cluster_ci(delta,groups)}
        data['paired_history_contrasts']=contrasts
        data['matched_design_contrasts']={}
        for new,prior in [('PairedAuditOnly','AuditOnly'),('PairedHistory','RandomHistory'),
                          ('PairedGlobal','UniformAuditGlobal'),('PairedKNN','UniformAuditKNN')]:
            delta=(np.array(merged[budget][new])-np.array(merged[budget][prior])).mean(axis=0)
            data['matched_design_contrasts'][new]={'comparator':prior,'difference':float(delta.mean()),
                                                  'generator_cluster_ci95':cluster_ci(delta,groups)}
    primary=result['budgets']['0.1']['paired_history_contrasts']
    result['exploratory_method_gate_pass']=all(primary[m]['generator_cluster_ci95'][0]>0
        for m in ('RandomHistory','DARTContrast','UniformAuditGlobal','PairedGlobal'))
    (args.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    (args.output/'predictions_private.json').write_text(json.dumps({'task_ids':ids,'predictions':merged})+'\n')
    write_status(args.output,state='completed',completed=300,total=300,audit_policy_runs=1200,
                 inference_calls=0,exploratory_method_gate_pass=result['exploratory_method_gate_pass'])
    print(json.dumps({b:{m:d['methods'][m]['mean_correct'] for m in METHODS}
                      for b,d in result['budgets'].items()},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--data-root',type=Path,default=Path('/private/tmp/repguard_appworld_data010/data'))
    run(p.parse_args())
