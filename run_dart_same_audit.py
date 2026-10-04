"""Frozen controlled forensics on real archived audits, not new inference."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np

from analyze_dart_leaderboard import cluster_ci
from run_dart_audit_pilot import digest, write_status
from repguard.audit.feedback import judge_feedback
from repguard.audit.forensics import choose, ridge_proxy, sampled_values
from repguard.audit.routing import TextFeatures, calibrated_proxy, global_means, policy_bank, select_policy

METHODS = ('Original','ZeroHT','AgentPriorHT','BinaryRidgeHT','ContinuousRidgeHT',
           'RawHT','Binary14HT','BinarySN','ZeroSN','SGlobal','CSGlobal','CSStratifiedHT')
DESIGNS = ('RandomHistory','DARTContrast')
PAIRS = [('ContinuousRidgeHT','BinaryRidgeHT'),('Binary14HT','Original'),
         ('BinarySN','Original'),('ZeroSN','ZeroHT'),('CSGlobal','SGlobal')]


def run(output: Path, data_root: Path) -> None:
    if output.exists():
        raise ValueError('Refusing to overwrite existing experiment')
    matrix = json.loads(Path('results/dart_leaderboard_v1/outcomes_private.json').read_text())
    ids, agents = matrix['task_ids'], matrix['agents']; k = len(agents)
    y = np.array(matrix['success'], dtype=float); lookup = {t:i for i,t in enumerate(ids)}
    texts = [json.loads((data_root/'tasks'/t/'specs.json').read_text())['instruction'] for t in ids]
    judge_dir = Path('results/dart_modal_judge_v1')
    judge_bits, provenance = judge_feedback(judge_dir, ids, agents)
    scores = np.full_like(y, np.nan)
    for line in (judge_dir/'judgments_private.jsonl').read_text().splitlines():
        r = json.loads(line)
        if not r['valid']:
            raise ValueError('This ablation requires every score valid')
        scores[lookup[r['case']['task_id']], agents.index(r['case']['agent'])] = r['success_probability']
    if not np.isfinite(scores).all() or not np.array_equal(scores >= .5, judge_bits):
        raise ValueError('Continuous score alignment differs from validated ledger')
    sources = ['run_dart_same_audit.py','src/repguard/audit/forensics.py',
               'src/repguard/audit/routing.py','src/repguard/audit/design.py',
               'docs/analysis/dart_same_audit_protocol_2026-10-05.md']
    references = {'self_report':Path('results/dart_audit_selfreport_v3'),
                  'judge':Path('results/dart_audit_judge_v1')}
    manifest = {'protocol':sources[-1], 'source_sha256':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sources},
                'matrix_sha256':digest(matrix),'instructions_sha256':digest(texts),
                'judge_provenance':provenance,'variants':METHODS,'designs':DESIGNS,
                'reference_files_sha256':{ch:{name:hashlib.sha256((root/name).read_bytes()).hexdigest()
                  for name in ('manifest.json','audit_trace_private.jsonl','predictions_private.json','feedback_private.json')}
                  for ch,root in references.items()},
                'independent_confirmation':False,'new_inference_calls':0}
    output.mkdir(parents=True)
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    groups = [t.rsplit('_',1)[0] for t in ids]
    all_summary, all_predictions, complete = {}, {}, 0
    write_status(output,state='running',completed=0,total=1200)
    for channel, reference in references.items():
        if json.loads((reference/'status.json').read_text())['state'] != 'completed':
            raise ValueError('Reference incomplete')
        feedback = json.loads((reference/'feedback_private.json').read_text())
        if feedback['task_ids'] != ids or feedback['agents'] != agents:
            raise ValueError('Feedback alignment differs')
        f = np.array(feedback['feedback']); p = scores if channel == 'judge' else f.astype(float)
        if channel == 'judge' and not np.array_equal(f, judge_bits):
            raise ValueError('Reference categorical feedback mismatch')
        original = json.loads((reference/'predictions_private.json').read_text())
        if original['task_ids'] != ids:
            raise ValueError('Prediction alignment differs')
        traces = [json.loads(x) for x in (reference/'audit_trace_private.jsonl').read_text().splitlines()]
        rows = [r for r in traces if r['method'] in DESIGNS]
        if len(rows) != 600 or len({(r['method'],r['fold'],r['seed'],r['budget_fraction']) for r in rows}) != 600:
            raise ValueError('Need every reference case exactly once')
        pred = {d:{str(b):{m:np.full((20,len(ids)),np.nan) for m in METHODS} for b in (.05,.1,.2)} for d in DESIGNS}
        stats, fold_cache, case_cache = {}, {}, {}
        for row in rows:
            fold, seed, budget, design = row['fold'],row['seed'],str(row['budget_fraction']),row['method']
            if fold not in fold_cache:
                c,s,t = [np.array([lookup[z] for z in row[key]]) for key in ('construction_ids','selection_ids','test_ids')]
                if set(c)&set(s) or (set(c)|set(s))&set(t):
                    raise ValueError('Partition overlap')
                enc = TextFeatures([texts[i] for i in c]); xc = enc.transform([texts[i] for i in c])
                fold_cache[fold] = (c,s,t,enc.transform([texts[i] for i in s])@xc.T,enc.transform([texts[i] for i in t])@xc.T)
            c,s,t,ss,st = fold_cache[fold]
            key = (fold,seed,budget)
            if key not in case_cache:
                anchors = np.full((len(c),k),np.nan)
                aix = np.array(row['anchor_indices']); anchors.ravel()[aix] = y[c].ravel()[aix]
                names,rs = policy_bank(ss,anchors); _,rt = policy_bank(st,anchors)
                proxy = calibrated_proxy(f[c],anchors,f[s])
                ridge_binary = ridge_proxy(f[c],anchors,f[s]); ridge_cont = ridge_proxy(p[c],anchors,p[s])
                if channel == 'self_report':
                    np.testing.assert_array_equal(ridge_binary,ridge_cont)
                case_cache[key] = (anchors,rs,rt,proxy,ridge_binary,ridge_cont,aix)
            anchors,rs,rt,proxy,ridge_binary,ridge_cont,aix = case_cache[key]
            if row['anchor_indices'] != aix.tolist():
                raise ValueError('Anchors differ between designs')
            baseline = int(global_means(anchors).argmax()); ix = np.array(row['audit_indices'])
            labels = y[s].ravel()[ix].copy(); q = np.array(row['sampled_probabilities'])
            def audit(requested):
                np.testing.assert_array_equal(requested,ix)
                return labels.copy()
            replay = select_policy(design,rs,proxy,baseline,row['selection_budget'],
                                   np.random.default_rng(22004+seed*100+fold),audit)
            fullq = np.array(replay['audit_probabilities'])
            if digest(fullq.tolist()) != row['all_probability_sha256'] or replay['selected_policy'] != row['selected_policy']:
                raise ValueError('Reference reconstruction failed')
            np.testing.assert_array_equal(fullq[ix],q)
            np.testing.assert_array_equal(rt[row['selected_policy']],row['test_agent_choices'])
            np.testing.assert_allclose(replay['estimated_values'],row['estimated_values'],atol=1e-14,rtol=0)
            values = {'Original':sampled_values(rs,proxy,ix,labels,q),
                      'ZeroHT':sampled_values(rs,np.zeros_like(proxy),ix,labels,q),
                      'AgentPriorHT':sampled_values(rs,np.broadcast_to(global_means(anchors),proxy.shape),ix,labels,q),
                      'BinaryRidgeHT':sampled_values(rs,ridge_binary,ix,labels,q),
                      'ContinuousRidgeHT':sampled_values(rs,ridge_cont,ix,labels,q),
                      'RawHT':sampled_values(rs,p[s],ix,labels,q),
                      'BinarySN':sampled_values(rs,proxy,ix,labels,q,normalized=True),
                      'ZeroSN':sampled_values(rs,np.zeros_like(proxy),ix,labels,q,normalized=True)}
            values['Binary14HT'] = values['Original'][:k]
            observed = np.full_like(proxy,np.nan); observed.ravel()[ix] = labels
            values['SGlobal'] = global_means(observed)
            values['CSGlobal'] = global_means(np.concatenate([anchors,observed]))
            rc = np.repeat(np.arange(k)[:,None],len(c),axis=1)
            vc = sampled_values(rc,np.zeros_like(anchors),aix,anchors.ravel()[aix],np.full(len(aix),len(aix)/anchors.size))
            values['CSStratifiedHT'] = (len(c)*vc+len(s)*values['ZeroHT'][:k])/(len(c)+len(s))
            choices = {m:choose(v,baseline) for m,v in values.items()}
            np.testing.assert_allclose(values['Original'],row['estimated_values'],atol=1e-14,rtol=0)
            if choices['Original'] != row['selected_policy']:
                raise ValueError('Counterfactual Original differs')
            # All actions above fixed before the following offline gold diagnostics.
            truth_s = y[s][np.arange(len(s))[None,:],rs].mean(axis=1)
            with (output/'trace_private.jsonl').open('a') as handle:
                for method,selected in choices.items():
                    actions = rt[selected]
                    pred[design][budget][method][seed,t] = y[t,actions]
                    diagnostic = {'chosen_policy':int(selected),'matching_audits':int((rs[selected,ix//k] == ix%k).sum())}
                    if method not in ('CSGlobal','CSStratifiedHT'):
                        truth = truth_s[:len(values[method])]
                        diagnostic.update(rmse=float(np.sqrt(np.mean((values[method]-truth)**2))),
                                          optimism=float(values[method][selected]-truth[selected]),
                                          selection_regret=float(truth.max()-truth[selected]))
                    stats.setdefault((design,budget,method),[]).append(diagnostic)
                    handle.write(json.dumps({'channel':channel,'design':design,'budget':budget,'fold':fold,'seed':seed,
                         'method':method,'test_agent_choices':actions.tolist(),'values':values[method].tolist(),**diagnostic})+'\n')
            for name,pr in [('categorical',proxy),('ridge_binary',ridge_binary),('ridge_continuous',ridge_cont)]:
                stats.setdefault((design,budget,'proxy_'+name),[]).append({'brier':float(((pr-y[s])**2).mean())})
            complete += 1
            write_status(output,state='running',completed=complete,total=1200,channel=channel,design=design)
        all_summary[channel] = {}
        for design,budgets in pred.items():
            all_summary[channel][design] = {}
            for budget,methods in budgets.items():
                original_values = np.array(original['predictions'][budget][design])
                np.testing.assert_array_equal(methods['Original'],original_values)
                summary = {'methods':{},'mechanism_contrasts':{}}
                uniform = np.array(original['predictions'][budget]['UniformAuditGlobal'])
                for method,a in methods.items():
                    if a.shape != (20,168) or not np.isfinite(a).all():
                        raise ValueError('Incomplete predictions')
                    ds = stats[(design,budget,method)]
                    if len(ds) != 100:
                        raise ValueError('Incomplete diagnostics')
                    summary['methods'][method] = {'mean_correct':float(a.sum(axis=1).mean()),
                         'vs_original':contrast(a,original_values,groups),'vs_uniform_global':contrast(a,uniform,groups),
                         'diagnostics':{name:float(np.mean([d[name] for d in ds])) for name in ds[0] if name != 'chosen_policy'},
                         'chosen_policy_counts':dict(Counter(d['chosen_policy'] for d in ds))}
                for a,b in PAIRS:
                    summary['mechanism_contrasts'][a+'-'+b] = contrast(methods[a],methods[b],groups)
                summary['proxy_brier_on_S_diagnostic'] = {name:float(np.mean([d['brier'] for d in stats[(design,budget,'proxy_'+name)]]))
                    for name in ('categorical','ridge_binary','ridge_continuous')}
                all_summary[channel][design][budget] = summary
        all_predictions[channel] = {d:{b:{m:a.tolist() for m,a in methods.items()} for b,methods in budgets.items()} for d,budgets in pred.items()}
    result = {'scope':'exploratory controlled same-audit replay; no independent confirmation',
              'completed_cases':complete,'policy_selections':complete*len(METHODS),'new_inference_calls':0,
              'all_original_predictions_reproduced':True,'results':all_summary}
    (output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    (output/'predictions_private.json').write_text(json.dumps({'task_ids':ids,'predictions':all_predictions})+'\n')
    write_status(output,state='completed',completed=complete,total=1200,policy_selections=complete*len(METHODS),new_inference_calls=0)
    print(json.dumps({c:{d:{m:v['mean_correct'] for m,v in b['0.1']['methods'].items()} for d,b in ds.items()}
                      for c,ds in all_summary.items()},indent=2))


def contrast(a: np.ndarray, b: np.ndarray, groups: list[str]) -> dict:
    delta = (a-b).mean(axis=0)
    return {'difference':float(delta.mean()),'generator_ci95':cluster_ci(delta,groups)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=Path('results/dart_same_audit_v1'))
    parser.add_argument('--data-root',type=Path,default=Path('/private/tmp/repguard_appworld_data010/data'))
    args = parser.parse_args()
    run(args.output,args.data_root)
