"""Full-data, post-run diagnostics; never imported by collection or routing."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
from repguard.audit.feedback import judge_feedback
from repguard.audit.routing import TextFeatures, policy_bank
from analyze_dart_leaderboard import cluster_ci
from run_dart_modal_judge import read_ledger


def confusion(y: np.ndarray, pred: np.ndarray) -> np.ndarray:
    return np.array([((y == 1) & (pred == 1)).sum(), ((y == 1) & (pred == 0)).sum(),
                     ((y == 0) & (pred == 0)).sum(), ((y == 0) & (pred == 1)).sum()])


def rates(counts: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    tp, fn, tn, fp = np.moveaxis(np.asarray(counts, dtype=float), -1, 0)
    with np.errstate(divide='ignore', invalid='ignore'):
        return (tp+tn)/(tp+fn+tn+fp), .5*(tp/(tp+fn)+tn/(tn+fp))


def metrics(y: np.ndarray, p: np.ndarray) -> dict:
    counts = confusion(y, p >= .5)
    acc, ba = rates(counts)
    positive, negative = p[y == 1], p[y == 0]
    auc = (float(((positive[:, None] > negative).sum() +
                 .5*(positive[:, None] == negative).sum()) / (len(positive)*len(negative)))
           if len(positive) and len(negative) else None)
    return {'n': len(y), **dict(zip(['tp', 'fn', 'tn', 'fp'], counts.tolist())),
            'accuracy': float(acc) if np.isfinite(acc) else None,
            'balanced_accuracy': float(ba) if np.isfinite(ba) else None,
            'brier': float(((y-p)**2).mean()) if len(y) else None, 'auc': auc}


def paired_feedback(y: np.ndarray, p: np.ndarray, self_report: np.ndarray,
                    groups: list[str]) -> dict:
    j, s = p >= .5, self_report >= .5
    ga = np.array(groups)
    unique = sorted(set(groups))
    cj = np.array([confusion(y[ga == g], j[ga == g]) for g in unique])
    cs = np.array([confusion(y[ga == g], s[ga == g]) for g in unique])
    draw = np.random.default_rng(410026).integers(0, len(unique), (5000, len(unique)))
    aj, bj = rates(cj[draw].sum(axis=1))
    ass, bs = rates(cs[draw].sum(axis=1))
    return {'judge': metrics(y, p), 'self_report_binary': metrics(y, self_report),
            'agreement': float((j == s).mean()),
            'judge_corrects_self_report': int(((j == y) & (s != y)).sum()),
            'judge_introduces_error': int(((j != y) & (s == y)).sum()),
            'accuracy_delta_ci95': np.quantile(aj-ass, [.025, .975]).tolist(),
            'balanced_accuracy_delta_ci95': np.nanquantile(bj-bs, [.025, .975]).tolist(),
            'bootstrap_draws_with_both_classes': int(np.isfinite(bj-bs).sum()),
            'all_failure_accuracy_diagnostic': float((y == 0).mean()),
            'prevalence_constant_brier_diagnostic': float(((y-y.mean())**2).mean())}


def routing_comparison(judge_dir: Path, self_dir: Path) -> dict:
    a = json.loads((judge_dir / 'predictions_private.json').read_text())
    b = json.loads((self_dir / 'predictions_private.json').read_text())
    if a['task_ids'] != b['task_ids']:
        raise ValueError('Routing task order differs')
    groups = [t.rsplit('_', 1)[0] for t in a['task_ids']]
    independent = ('AuditOnly', 'UniformAuditGlobal', 'UniformAuditKNN', 'AnchorOnly',
                   'GoldTrainSingle', 'GoldTrainKNN')
    result = {}
    for budget, methods in a['predictions'].items():
        summary = {}
        for method, values in methods.items():
            ja = np.array(values)
            sa = np.array(b['predictions'][budget][method])
            if ja.shape != (20, 168) or sa.shape != ja.shape:
                raise ValueError('Wrong routing shape')
            if method in independent and not np.array_equal(ja, sa):
                raise ValueError(f'Gold-only control changed with feedback: {budget}/{method}')
            delta = (ja-sa).mean(axis=0)
            summary[method] = {'judge_mean_correct': float(ja.sum(axis=1).mean()),
                               'self_report_mean_correct': float(sa.sum(axis=1).mean()),
                               'accuracy_delta': float(delta.mean()),
                               'generator_ci95': cluster_ci(delta, groups),
                               'identical_predictions': bool(np.array_equal(ja, sa))}
        result[budget] = summary
    return {'gold_only_controls_invariant': True, 'budgets': result}


def selection_diagnostics(directory: Path, matrix: dict, data_root: Path) -> dict:
    ids, agents = matrix['task_ids'], matrix['agents']
    lookup = {t: i for i, t in enumerate(ids)}
    y = np.array(matrix['success'])
    traces = [json.loads(line) for line in (directory / 'audit_trace_private.jsonl').read_text().splitlines()]
    texts = {t: json.loads((data_root / 'tasks' / t / 'specs.json').read_text())['instruction'] for t in ids}
    grouped, cache = {}, {}
    for row in traces:
        if 'estimated_values' not in row:
            continue
        cids, sids, tids = row['construction_ids'], row['selection_ids'], row['test_ids']
        key = (row['fold'], row['budget_fraction'], row['seed'])
        if key not in cache:
            c, s, t = [np.array([lookup[z] for z in zz]) for zz in (cids, sids, tids)]
            anchors = np.full((len(c), len(agents)), np.nan)
            ix = row['anchor_indices']
            anchors.ravel()[ix] = y[c].ravel()[ix]
            enc = TextFeatures([texts[z] for z in cids])
            xc = enc.transform([texts[z] for z in cids])
            names, rs = policy_bank(enc.transform([texts[z] for z in sids]) @ xc.T, anchors)
            _, rt = policy_bank(enc.transform([texts[z] for z in tids]) @ xc.T, anchors)
            values_s = y[s][np.arange(len(s))[None, :], rs].mean(axis=1)
            counts_t = y[t][np.arange(len(t))[None, :], rt].sum(axis=1)
            cache[key] = (names, rt, values_s, counts_t, len(t))
        names, rt, values_s, counts_t, nt = cache[key]
        selected = row['selected_policy']
        if names[selected] != row['chosen_policy_name'] or rt[selected].tolist() != row['test_agent_choices']:
            raise ValueError('Reconstructed candidate bank differs from actual saved actions')
        estimated = np.array(row['estimated_values'])
        result = {'selected_policy': names[selected], 'test_n': nt,
                  'chosen_test_correct': float(counts_t[selected]),
                  'full_selection_gold_chosen_test_correct_diagnostic': float(counts_t[int(values_s.argmax())]),
                  'best_test_candidate_correct_diagnostic': float(counts_t.max()),
                  'selection_value_regret_diagnostic': float(values_s.max()-values_s[selected]),
                  'chosen_value_optimism': float(estimated[selected]-values_s[selected]),
                  'candidate_value_rmse': float(np.sqrt(((estimated-values_s)**2).mean())),
                  'selected_estimate_outside_0_1': int(not 0 <= estimated[selected] <= 1),
                  'effective_sample_size': row['effective_sample_size']}
        grouped.setdefault(str(row['budget_fraction']), {}).setdefault(row['method'], []).append(result)
    summary = {}
    for budget, methods in grouped.items():
        summary[budget] = {}
        for method, rows in methods.items():
            if len(rows) != 100 or sum(r['test_n'] for r in rows) != 20*168:
                raise ValueError('Incomplete selection diagnostics')
            stats = {k: float(np.mean([r[k] for r in rows])) for k in rows[0]
                     if k not in ('selected_policy', 'test_n')}
            for k in ('chosen_test_correct', 'full_selection_gold_chosen_test_correct_diagnostic',
                      'best_test_candidate_correct_diagnostic'):
                stats[k + '_per_168'] = sum(r[k] for r in rows)/20
                del stats[k]
            stats['selected_policy_counts'] = dict(Counter(r['selected_policy'] for r in rows))
            stats['evaluated_fold_seed_runs'] = len(rows)
            summary[budget][method] = stats
    return summary


def analyze(args: argparse.Namespace) -> dict:
    status = json.loads((args.replay / 'status.json').read_text())
    if status['state'] != 'completed':
        raise ValueError('Wait for the complete frozen replay')
    matrix = json.loads((args.capability / 'outcomes_private.json').read_text())
    ids, agents = matrix['task_ids'], matrix['agents']
    _, metadata = judge_feedback(args.judge, ids, agents)
    manifest = json.loads((args.judge / 'manifest.json').read_text())
    ledger = read_ledger(args.judge / 'judgments_private.jsonl', manifest)
    if len(ledger) != 2352:
        raise ValueError('Full 2352-case ledger required')
    self_data = json.loads((args.self_report / 'feedback_private.json').read_text())
    if self_data['task_ids'] != ids or self_data['agents'] != agents:
        raise ValueError('Self-report matrix alignment mismatch')
    self_feedback = np.array(self_data['feedback'])
    y = np.array(matrix['success'])
    ti, ai = {t: i for i, t in enumerate(ids)}, {a: i for i, a in enumerate(agents)}
    valid = [ledger[k] for k in sorted(ledger) if ledger[k]['valid']]
    yy = np.array([y[ti[r['case']['task_id']], ai[r['case']['agent']]] for r in valid])
    pp = np.array([r['success_probability'] for r in valid])
    ss = np.array([self_feedback[ti[r['case']['task_id']], ai[r['case']['agent']]] for r in valid])
    groups = [r['case']['task_id'].rsplit('_', 1)[0] for r in valid]
    result = {'scope': 'exploratory full-data post-run diagnostics, no new method or confirmation',
              'feedback_provenance': metadata, 'valid_feedback_records': len(valid),
              'feedback': paired_feedback(yy, pp, ss, groups),
              'per_agent': {}, 'by_clipping': {},
              'routing_feedback_comparison': routing_comparison(args.replay, args.self_report),
              'selection_diagnostics': selection_diagnostics(args.replay, matrix, args.data_root)}
    for a in agents:
        mask = np.array([r['case']['agent'] == a for r in valid])
        result['per_agent'][a] = {'judge': metrics(yy[mask], pp[mask]),
                                  'self_report': metrics(yy[mask], ss[mask])}
    for clipped in (False, True):
        mask = np.array([r['case']['clipped'] == clipped for r in valid])
        result['by_clipping'][str(clipped)] = {'judge': metrics(yy[mask], pp[mask]),
                                              'self_report': metrics(yy[mask], ss[mask])}
    chronological = [ledger[k] for k in sorted(ledger)]
    gaps = [(datetime.fromisoformat(b['finished_at'])-datetime.fromisoformat(a['finished_at'])).total_seconds()
            for a, b in zip(chronological, chronological[1:])]
    requests = [json.loads(x) for x in (args.judge / 'requests.jsonl').read_text().splitlines()]
    result['operations'] = {'completed_records': len(ledger), 'logical_request_starts': len(requests),
                            'repeated_request_starts': len(requests)-len({r['index'] for r in requests}),
                            'largest_record_gap_s': max(gaps),
                            'first_record_at': chronological[0]['finished_at'],
                            'last_record_at': chronological[-1]['finished_at'],
                            'sum_completed_latency_s': sum(r['latency_s'] for r in chronological),
                            'prompt_tokens': sum(r['usage']['prompt_eval_count'] or 0 for r in chronological),
                            'output_tokens': sum(r['usage']['eval_count'] or 0 for r in chronological)}
    result['source_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--judge', type=Path, default=Path('results/dart_modal_judge_v1'))
    parser.add_argument('--replay', type=Path, default=Path('results/dart_audit_judge_v1'))
    parser.add_argument('--self-report', type=Path, default=Path('results/dart_audit_selfreport_v3'))
    parser.add_argument('--capability', type=Path, default=Path('results/dart_leaderboard_v1'))
    parser.add_argument('--data-root', type=Path, default=Path('/private/tmp/repguard_appworld_data010/data'))
    parser.add_argument('--output', type=Path, default=Path('docs/analysis/dart_postrun_diagnostics_2026-10-04.json'))
    args = parser.parse_args()
    result = analyze(args)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('feedback', 'operations')}, indent=2))


if __name__ == '__main__':
    main()
