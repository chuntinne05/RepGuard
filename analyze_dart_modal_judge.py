"""Separate post-collection quality gate; never imported by the collector."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from run_dart_modal_judge import PILOT_SIZE, atomic_json, canonical, read_ledger


def balanced_accuracy(truth: np.ndarray, prediction: np.ndarray) -> float:
    if len(set(truth.tolist())) != 2:
        return float('nan')
    return float(np.mean([(truth[truth == label] == prediction[truth == label]).mean()
                          for label in (0, 1)]))


def analyze(output: Path, capability: Path) -> dict:
    manifest = json.loads((output / 'manifest.json').read_text())
    ledger = read_ledger(output / 'judgments_private.jsonl', manifest)
    rows = [ledger[i] for i in range(PILOT_SIZE)]
    matrix = json.loads((capability / 'outcomes_private.json').read_text())
    outcomes = {(t, a): matrix['success'][i][j] for i, t in enumerate(matrix['task_ids'])
                for j, a in enumerate(matrix['agents'])}
    usable = [r for r in rows if r['valid']]
    truth = np.array([outcomes[r['case']['task_id'], r['case']['agent']] for r in usable])
    p = np.array([r['success_probability'] for r in usable])
    predicted = (p >= .5).astype(int)
    groups = np.array([r['case']['task_id'].rsplit('_', 1)[0] for r in usable])
    unique = sorted(set(groups))
    rng = np.random.default_rng(141004)
    samples = []
    for _ in range(5000 if len(unique) else 0):
        draw = rng.choice(unique, size=len(unique), replace=True)
        indices = np.concatenate([np.flatnonzero(groups == g) for g in draw])
        samples.append(balanced_accuracy(truth[indices], predicted[indices]))
    finite = np.array(samples)[np.isfinite(samples)]
    ci = np.quantile(finite, [.025, .975]).tolist() if len(finite) >= 4750 else [None, None]
    ba = balanced_accuracy(truth, predicted)
    gate = len(usable) >= .95 * PILOT_SIZE and np.isfinite(ba) and ba >= .60 and ci[0] is not None and ci[0] > .50
    report = {'scope': 'judge quality pilot, not routing or method superiority',
              'protocol_hash': manifest['hash'], 'pilot_rows_sha256': canonical(rows),
              'rows': len(rows), 'valid': len(usable), 'generators': len(unique),
              'positive_labels': int(truth.sum()), 'negative_labels': int(len(truth) - truth.sum()),
              'balanced_accuracy': float(ba) if np.isfinite(ba) else None,
              'balanced_accuracy_generator_ci95': ci,
              'accuracy': float((truth == predicted).mean()) if len(truth) else None,
              'brier_score': float(((truth-p)**2).mean()) if len(truth) else None,
              'clipped_records': sum(r['case']['clipped'] for r in rows),
              'prompt_tokens': sum(r['usage']['prompt_eval_count'] or 0 for r in rows),
              'output_tokens': sum(r['usage']['eval_count'] or 0 for r in rows),
              'sum_call_latency_s': sum(r['latency_s'] for r in rows),
              'gate_pass': bool(gate), 'next_stage': 'collect_full_frozen_matrix' if gate else 'stop_and_diagnose_feedback',
              'no_routing_superiority_claim': True}
    atomic_json(output / 'pilot_quality.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path('results/dart_modal_judge_v1'))
    parser.add_argument('--capability', type=Path, default=Path('results/dart_leaderboard_v1'))
    args = parser.parse_args()
    print(json.dumps(analyze(args.output, args.capability), indent=2))
