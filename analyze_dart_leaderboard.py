"""Validate and analyze the preregistered AppWorld pool; never rerun agents.

Decrypted task outcomes stay in ignored results/. This is an offline analysis of
real official trajectories, not a fresh inference or an independent holdout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

import numpy as np


def exact_mcnemar(a_only: int, b_only: int) -> float:
    n = a_only + b_only
    return min(1.0, 2 * sum(math.comb(n, k) for k in range(min(a_only, b_only) + 1)) / 2**n)


def cluster_ci(delta: np.ndarray, groups: list[str], seed: int = 1404) -> list[float]:
    unique = sorted(set(groups))
    totals = np.array([delta[np.array(groups) == g].sum() for g in unique])
    counts = np.array([groups.count(g) for g in unique])
    draws = np.random.default_rng(seed).integers(0, len(unique), (5000, len(unique)))
    values = totals[draws].sum(axis=1) / counts[draws].sum(axis=1)
    return np.quantile(values, [0.025, 0.975]).tolist()


def load_pool(repo: Path, manifest: dict) -> tuple[list[str], list[str], np.ndarray, list[dict]]:
    commit = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
    if commit != manifest['leaderboard_commit']:
        raise ValueError('Leaderboard commit differs from frozen manifest')
    expected = set(manifest['dataset_id_lists']['test_normal']['task_ids'])
    provenance, records = [], {}
    all_versions = set()
    for agent in manifest['agents']:
        name = agent['name']
        rel = agent['bundle_paths']['test_normal']
        pointer = subprocess.check_output(['git', '-C', str(repo), 'show', 'HEAD:' + rel], text=True)
        pointer = dict(line.split(' ', 1) for line in pointer.splitlines())
        bundle = (repo / rel).read_bytes()
        digest = hashlib.sha256(bundle).hexdigest()
        if digest != pointer['oid'].split(':')[1] or len(bundle) != int(pointer['size']):
            raise ValueError(f'Corrupt encrypted bundle: {name}')
        root = (repo / rel).parent
        evaluation = root / 'evaluations/test_normal.json'
        data = json.loads(evaluation.read_text())['individual']
        ids = sorted(expected & data.keys())
        meta = json.loads((root / 'metadata.json').read_text())
        if meta['dataset'] != 'test_normal':
            raise ValueError(f'Wrong dataset: {name}')
        versions = {}
        for key, path in [('data', 'version/data.txt'), ('code', 'version/code.txt'),
                          ('evaluator', 'evaluation/version.txt')]:
            versions[key] = sorted({(root / 'tasks' / t / path).read_text().strip() for t in ids})
        if len(versions['data']) != 1 or versions['data'] != versions['evaluator']:
            raise ValueError(f'Inconsistent data/evaluator versions: {name}')
        all_versions.update(versions['data'])
        for task_id in ids:
            row = data[task_id]
            if type(row['success']) is not bool:
                raise ValueError('Exact success must be a boolean')
            if row['success'] != (len(row['failures']) == 0):
                raise ValueError('Success contradicts official failed checks')
            if len(row['passes']) + len(row['failures']) != row['num_tests']:
                raise ValueError('Official check counts inconsistent')
        eligible = len(ids) >= math.ceil(0.95 * len(expected))
        provenance.append({'agent': name, 'eligible': eligible, 'coverage': len(ids),
                           'missing_ids': sorted(expected - data.keys()), 'versions': versions,
                           'bundle_sha256': digest, 'bundle_bytes': len(bundle),
                           'evaluation_sha256': hashlib.sha256(evaluation.read_bytes()).hexdigest(),
                           'metadata': meta,
                           'usage_file_count': len(list(root.rglob('usage.json')))})
        if eligible:
            records[name] = data
    if len(all_versions) != 1:
        raise ValueError('Mixed data versions across agents; no pooled analysis allowed')
    if len(records) < 2:
        raise ValueError('Fewer than two eligible agents')
    ids = sorted(set.intersection(expected, *(set(d) for d in records.values())))
    if len(ids) < 150:
        raise ValueError('Complete-case task count below preregistered 150 gate')
    names = list(records)
    outcomes = np.array([[int(records[a][t]['success']) for a in names] for t in ids])
    return names, ids, outcomes, provenance


def analyze(names: list[str], ids: list[str], outcomes: np.ndarray) -> dict:
    groups = [t.rsplit('_', 1)[0] for t in ids]
    per_agent = [{'agent': a, 'correct': int(outcomes[:, j].sum()),
                  'total': len(ids), 'accuracy': float(outcomes[:, j].mean())}
                 for j, a in enumerate(names)]
    pairs = []
    for a in range(len(names)):
        for b in range(a + 1, len(names)):
            ya, yb = outcomes[:, a], outcomes[:, b]
            ao, bo = int(((ya == 1) & (yb == 0)).sum()), int(((yb == 1) & (ya == 0)).sum())
            pairs.append({'a': names[a], 'b': names[b], 'a_only': ao, 'b_only': bo,
                          'both_correct': int(((ya == 1) & (yb == 1)).sum()),
                          'both_wrong': int(((ya == 0) & (yb == 0)).sum()),
                          'difference_a_minus_b': float((ya - yb).mean()),
                          'generator_cluster_ci95': cluster_ci(ya - yb, groups),
                          'mcnemar_task_level_diagnostic_p': exact_mcnemar(ao, bo),
                          'passes_frozen_rescue_screen': ao >= 10 and bo >= 10})
    best = int(outcomes.sum(axis=0).argmax())
    oracle = outcomes.max(axis=1)
    return {'scope': 'public historical leaderboard exploratory capacity analysis',
            'tasks': len(ids), 'generators': len(set(groups)), 'agents': len(names),
            'per_agent': per_agent, 'pairs': pairs,
            'gate_a_pass': any(p['passes_frozen_rescue_screen'] for p in pairs),
            'qualifying_pair_count': sum(p['passes_frozen_rescue_screen'] for p in pairs),
            'retrospective_best_single': names[best],
            'retrospective_best_single_correct': int(outcomes[:, best].sum()),
            'oracle_correct': int(oracle.sum()),
            'oracle_headroom_tasks': int((oracle - outcomes[:, best]).sum()),
            'caution': 'Oracle and retrospective best are diagnostics. Pair p-values unadjusted and ignore clustering; no method-superiority inference.',
            'cost_scope': 'One agent invocation is a count, not equal compute or dollar cost; usage metadata absent.'}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--repo', type=Path, default=Path('/private/tmp/repguard_appworld_leaderboard'))
    p.add_argument('--manifest', type=Path, default=Path('docs/analysis/dart_leaderboard_pool_manifest_2026-10-04.json'))
    p.add_argument('--output', type=Path, default=Path('results/dart_leaderboard_v1'))
    args = p.parse_args()
    manifest = json.loads(args.manifest.read_text())
    names, ids, y, provenance = load_pool(args.repo, manifest)
    report = analyze(names, ids, y)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'capability.json').write_text(json.dumps(report, indent=2) + '\n')
    (args.output / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    # Protected derived data: results/ is ignored and must not be published unencrypted.
    (args.output / 'outcomes_private.json').write_text(json.dumps(
        {'agents': names, 'task_ids': ids, 'success': y.tolist()}, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('pairs', 'per_agent')}, indent=2))
    for row in sorted(report['per_agent'], key=lambda x: -x['correct']):
        print(row['agent'], row['correct'], '/', row['total'])


if __name__ == '__main__':
    main()
