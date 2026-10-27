"""Post-run error evidence; never used by the collector or any learner."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from run_dart_modal_judge import read_case, read_ledger


def run() -> None:
    source = Path('results/dart_modal_judge_v1')
    manifest = json.loads((source/'manifest.json').read_text())
    rows = read_ledger(source/'judgments_private.jsonl',manifest)
    repo = Path('/private/tmp/repguard_appworld_leaderboard')
    data = Path('/private/tmp/repguard_appworld_data010/data')
    matrix = json.loads(Path('results/dart_leaderboard_v1/outcomes_private.json').read_text())
    truth = {(t,a):matrix['success'][i][j] for i,t in enumerate(matrix['task_ids']) for j,a in enumerate(matrix['agents'])}
    cached, counts, labels = {}, Counter(), Counter()
    bins = {b:{'n':0,'successes':0,'sum_probability':0.} for b in ('[0,.5)','[.5,.9)','[.9,1]')}
    examples = []
    for r in rows.values():
        case = r['case']; a,t = case['agent'],case['task_id']
        prompt,metadata = read_case(case,repo,data)
        if any(case[k] != v for k,v in metadata.items()):
            raise ValueError('Archived instruction/trajectory does not match real judge request')
        if a not in cached:
            path = repo/'experiments/outputs'/(a+'_test_normal')/'evaluations/test_normal.json'
            cached[a] = json.loads(path.read_text())['individual']
        ev = cached[a][t]; success = ev['success']; p = r['success_probability']
        if not r['valid'] or bool(truth[t,a]) != success or success != (len(ev['failures']) == 0):
            raise ValueError('Outcome/ledger mismatch')
        key = '[0,.5)' if p < .5 else '[.5,.9)' if p < .9 else '[.9,1]'
        bins[key]['n'] += 1; bins[key]['successes'] += int(success); bins[key]['sum_probability'] += p
        counts['verified_cases'] += 1
        if p < .5 or success:
            continue
        counts['false_positives'] += 1
        counts['false_positives_clipped' if case['clipped'] else 'false_positives_unclipped'] += 1
        requirements = [f['requirement'].strip() for f in ev['failures']]
        answer = sum(x == 'assert answers match.' for x in requirements)
        counts['fp_with_answer_mismatch'] += int(answer > 0)
        counts['fp_only_answer_mismatch'] += int(answer == len(requirements))
        counts['fp_with_other_failed_checks'] += int(answer < len(requirements))
        labels.update(f['label'] for f in ev['failures'])
        if p >= .9:
            counts['high_confidence_fp'] += 1
            if not case['clipped']:
                counts['high_confidence_unclipped_fp'] += 1
                examples.append((hashlib.sha256((a+':'+t).encode()).hexdigest(),r,ev))
    if counts['verified_cases'] != 2352 or counts['false_positives'] != 1072:
        raise ValueError('Full-run confusion count mismatch')
    for b in bins.values():
        b['mean_probability'] = b.pop('sum_probability')/b['n']
        b['actual_success_rate'] = b['successes']/b['n']
    private = Path('results/dart_judge_errors_v1'); private.mkdir(exist_ok=True)
    (private/'examples_private.json').write_text(json.dumps([{'sha256_order':h,'judgment':r,'evaluation':ev}
          for h,r,ev in sorted(examples)[:3]],indent=2)+'\n')
    summary = {'scope':'posthoc full-data diagnostics; not causal estimates of model reasoning',
               'think':manifest['think'],'num_predict':manifest['num_predict'],
               'counts':dict(counts),'confidence_bins':bins,'failed_check_labels_counts':dict(labels),
               'examples_selection':'First three SHA256(agent:task) among p>=.9, false-positive, unclipped cases; raw cases private',
               'all_prompt_hashes_verified':True,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    Path('docs/analysis/dart_judge_error_evidence_2026-10-05.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__ == '__main__':
    run()
