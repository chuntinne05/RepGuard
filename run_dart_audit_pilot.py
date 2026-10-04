"""Exploratory DART replay on real AppWorld trajectories and observed self-reports.

No generated/model correctness is simulated. Only the audit sampling is random.
Official success labels are revealed to learners only at paid historical audits;
outer evaluation labels are used after routing choices have been frozen.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
from repguard.audit.routing import (
    TextFeatures, calibrated_proxy, construction_selection_split, generator_id,
    global_means, knn_routes, policy_bank, select_policy,
)
from analyze_dart_leaderboard import cluster_ci

AUDIT_METHODS = ('AuditOnly', 'RandomHistory', 'UncertaintyHistory', 'DART')
BUDGETS = (0.05, 0.10, 0.20)


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def write_status(output: Path, **fields: object) -> None:
    value = {'updated_at': datetime.now(timezone.utc).isoformat(), **fields}
    temporary = output / 'status.tmp'
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(output / 'status.json')


def observed_feedback(log: Path) -> int:
    messages = []
    for line in log.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row['url'].split('?')[0].rstrip('/') == '/supervisor/message':
            messages.append(row)
    if not messages:
        return 0
    status = messages[-1].get('data', {}).get('status', 'success')
    if status not in ('success', 'fail', 'failure'):
        raise ValueError(f'Unknown completion self-report status: {status!r}')
    return int(status == 'success')


def prepare_inputs(args: argparse.Namespace) -> tuple[dict, dict, np.ndarray, np.ndarray, list[str]]:
    frozen = json.loads(args.manifest.read_text())
    matrix = json.loads((args.capability / 'outcomes_private.json').read_text())
    gate = json.loads((args.capability / 'capability.json').read_text())
    if not gate['gate_a_pass']:
        raise RuntimeError('Preregistered capability gate is closed')
    ids, agents = matrix['task_ids'], matrix['agents']
    if agents != [a['name'] for a in frozen['agents']]:
        raise ValueError('Pilot requires entire frozen pool; exclusions need an amendment')
    actual_ids = (args.data_root / 'datasets/test_normal.txt').read_text().splitlines()
    if set(ids) != set(actual_ids):
        raise ValueError('Matching-version data IDs differ from outcome matrix')
    texts, feedback = [], []
    for task_id in ids:
        spec = json.loads((args.data_root / 'tasks' / task_id / 'specs.json').read_text())
        if spec['db_version'] != '0.1.0':
            raise ValueError('Wrong instruction/data version')
        texts.append(spec['instruction'])
        feedback.append([observed_feedback(args.repo / 'experiments/outputs' /
                        (agent + '_test_normal') / 'tasks' / task_id / 'logs/api_calls.jsonl')
                         for agent in agents])
    y = np.array(matrix['success'], dtype=float)
    f = np.array(feedback, dtype=int)
    if y.shape != f.shape or not np.isin(y, [0, 1]).all():
        raise ValueError('Invalid outcome matrix')
    return frozen, matrix, y, f, texts


def summarize(predictions: dict, ids: list[str], seeds: int) -> dict:
    groups = [generator_id(t) for t in ids]
    result = {}
    for budget, methods in predictions.items():
        arrays = {m: np.array(v, dtype=float) for m, v in methods.items()}
        if any(a.shape != (seeds, len(ids)) or not np.isfinite(a).all() for a in arrays.values()):
            raise ValueError('Incomplete out-of-fold predictions')
        summary = {}
        for name, values in arrays.items():
            summary[name] = {'mean_correct': float(values.sum(axis=1).mean()),
                             'mean_accuracy': float(values.mean()),
                             'seed_min_correct': int(values.sum(axis=1).min()),
                             'seed_max_correct': int(values.sum(axis=1).max())}
        contrasts = {}
        for name in ('AuditOnly', 'RandomHistory', 'UncertaintyHistory', 'AnchorOnly'):
            delta = (arrays['DART'] - arrays[name]).mean(axis=0)
            contrasts[name] = {'difference': float(delta.mean()),
                              'generator_cluster_ci95': cluster_ci(delta, groups),
                              'mean_rescues': float(((arrays['DART'] == 1) & (arrays[name] == 0)).sum(axis=1).mean()),
                              'mean_harms': float(((arrays['DART'] == 0) & (arrays[name] == 1)).sum(axis=1).mean())}
        result[budget] = {'methods': summary, 'DART_contrasts': contrasts}
    primary = result['0.1']['DART_contrasts']
    gate = all(primary[m]['generator_cluster_ci95'][0] > 0
               for m in ('AuditOnly', 'RandomHistory', 'UncertaintyHistory'))
    return {'scope': 'exploratory grouped out-of-fold replay of official real trajectories',
            'feedback': 'actual agent completion self-report requests; not LLM judge or verified success',
            'tasks': len(ids), 'generators': len(set(groups)), 'audit_seeds': seeds,
            'budgets': result, 'primary_budget': 0.1, 'exploratory_method_gate_pass': gate,
            'deployment_certified': False, 'independent_confirmation': False,
            'cost_scope': 'equal unique historical task-agent gold labels and one chosen agent invocation per test task; no compute/USD parity claim',
            'uncertainty_scope': 'unadjusted exploratory generator bootstrap after seed averaging; not an audit-design or deployment guarantee'}


def run(args: argparse.Namespace) -> None:
    frozen, matrix, y, feedback, texts = prepare_inputs(args)
    ids, agents = matrix['task_ids'], matrix['agents']
    methods = (*AUDIT_METHODS, 'AnchorOnly', 'ProxyGlobal', 'ProxyKNN',
               'GoldTrainSingle', 'GoldTrainKNN')
    source_files = [Path(__file__), Path('src/repguard/audit/design.py'),
                    Path('src/repguard/audit/routing.py')]
    protocol = {'name': 'dart_observed_completion_audit_pilot_v1', 'budgets': BUDGETS,
                'seeds': list(range(args.seeds)), 'pool_manifest_sha256': digest(frozen),
                'outcome_matrix_sha256': digest(matrix), 'feedback_sha256': digest(feedback.tolist()),
                'instructions_sha256': digest(texts),
                'source_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files},
                'protocol_document': 'docs/analysis/dart_first_implementation_protocol_2026-10-04.md',
                'cost_unit': 'one trusted task-agent label', 'feedback_source': 'agent self-report request log',
                'sealed_mmlu_holdout_read': False, 'challenge_outcomes_read': False}
    protocol['hash'] = digest(protocol)
    args.output.mkdir(parents=True, exist_ok=True)
    manifest_path = args.output / 'manifest.json'
    if manifest_path.exists() and json.loads(manifest_path.read_text()) != json.loads(json.dumps(protocol)):
        raise ValueError('Refusing to mix a different protocol into this output directory')
    manifest_path.write_text(json.dumps(protocol, indent=2) + '\n')
    (args.output / 'feedback_private.json').write_text(json.dumps({
        'task_ids': ids, 'agents': agents, 'feedback': feedback.tolist(),
        'provenance': 'last supervisor message request status, no gold access'}, indent=2) + '\n')
    fold_ids = np.array([frozen['normal_outer_fold_by_generator'][generator_id(t)] for t in ids])
    predictions = {str(b): {m: np.full((args.seeds, len(ids)), np.nan) for m in methods} for b in BUDGETS}
    traces_path = args.output / 'audit_trace_private.jsonl'
    if traces_path.exists():
        raise ValueError('Existing trace: use a fresh output directory, do not overwrite a partial run')
    steps = 0
    total = 5 * len(BUDGETS) * args.seeds
    write_status(args.output, state='running', completed=steps, total=total)
    for fold in range(5):
        train = np.flatnonzero(fold_ids != fold)
        test = np.flatnonzero(fold_ids == fold)
        c_rel, s_rel = construction_selection_split([ids[i] for i in train])
        c, s = train[c_rel], train[s_rel]
        assert not ({generator_id(ids[i]) for i in c} & {generator_id(ids[i]) for i in s})
        assert not ({generator_id(ids[i]) for i in train} & {generator_id(ids[i]) for i in test})
        encoder = TextFeatures([texts[i] for i in c])
        xc = encoder.transform([texts[i] for i in c])
        sim_s = encoder.transform([texts[i] for i in s]) @ xc.T
        sim_t = encoder.transform([texts[i] for i in test]) @ xc.T
        # Full-gold learnability controls are never supplied to an audited learner.
        gold_encoder = TextFeatures([texts[i] for i in train])
        all_sim = gold_encoder.transform([texts[i] for i in test]) @ gold_encoder.transform([texts[i] for i in train]).T
        gold_single = np.full(len(test), int(y[train].mean(axis=0).argmax()))
        gold_knn = knn_routes(all_sim, y[train], 10)
        raw_single = np.full(len(test), int(feedback[train].mean(axis=0).argmax()))
        raw_knn = knn_routes(all_sim, feedback[train].astype(float), 10)
        for fraction in BUDGETS:
            budget = int(len(train) * len(agents) * fraction)
            anchor_budget = budget // 3
            selection_budget = budget - anchor_budget
            for seed in range(args.seeds):
                anchor_rng = np.random.default_rng(41004 + seed * 100 + fold)
                anchors = np.full((len(c), len(agents)), np.nan)
                anchor_indices = anchor_rng.permutation(anchors.size)[:anchor_budget]
                anchors.ravel()[anchor_indices] = y[c].ravel()[anchor_indices]
                names, routes_s = policy_bank(sim_s, anchors)
                _, routes_t = policy_bank(sim_t, anchors)
                baseline = int(global_means(anchors).argmax())
                proxy = calibrated_proxy(feedback[c], anchors, feedback[s])
                choices = {'AnchorOnly': routes_t[baseline], 'ProxyGlobal': raw_single,
                           'ProxyKNN': raw_knn, 'GoldTrainSingle': gold_single, 'GoldTrainKNN': gold_knn}
                traces = []
                for method in AUDIT_METHODS:
                    revealed = []

                    def audit(requested: np.ndarray) -> np.ndarray:
                        if revealed or len(requested) != selection_budget or len(set(requested)) != selection_budget:
                            raise ValueError('Audit budget exceeded or repeated request')
                        revealed.extend(requested.tolist())
                        return y[s].ravel()[requested].copy()

                    selection = select_policy(method, routes_s, proxy, baseline, selection_budget,
                                              np.random.default_rng(22004 + seed * 100 + fold), audit)
                    chosen = selection['selected_policy']
                    choices[method] = routes_t[chosen]
                    q = np.array(selection.pop('audit_probabilities'))
                    selection['sampled_probabilities'] = q[selection['audit_indices']].tolist()
                    selection['all_probability_sha256'] = digest(q.tolist())
                    traces.append({'fold': fold, 'seed': seed, 'budget_fraction': fraction,
                                   'method': method, 'anchor_budget': anchor_budget,
                                   'selection_budget': selection_budget, 'total_audits': budget,
                                   'construction_ids': [ids[i] for i in c],
                                   'selection_ids': [ids[i] for i in s],
                                   'anchor_indices': anchor_indices.tolist(),
                                   'chosen_policy_name': names[chosen], **selection,
                                   'test_ids': [ids[i] for i in test], 'test_agent_choices': choices[method].tolist()})
                # Every action above is fixed before looking up held-out success.
                for method, actions in choices.items():
                    predictions[str(fraction)][method][seed, test] = y[test, actions]
                with traces_path.open('a') as handle:
                    for trace in traces:
                        handle.write(json.dumps(trace) + '\n')
                steps += 1
                write_status(args.output, state='running', completed=steps, total=total,
                             fold=fold, budget_fraction=fraction, seed=seed,
                             audit_policy_runs=steps * len(AUDIT_METHODS))
            print(f'fold={fold} budget={fraction} completed={steps}/{total}', flush=True)
    report = summarize(predictions, ids, args.seeds)
    (args.output / 'analysis.json').write_text(json.dumps(report, indent=2) + '\n')
    serial = {b: {m: v.tolist() for m, v in methods.items()} for b, methods in predictions.items()}
    (args.output / 'predictions_private.json').write_text(json.dumps({'task_ids': ids, 'predictions': serial}) + '\n')
    write_status(args.output, state='completed', completed=steps, total=total,
                 audit_policy_runs=steps * len(AUDIT_METHODS),
                 method_gate_pass=report['exploratory_method_gate_pass'],
                 next_stage='real_judge_validation_required', inference_calls=0)
    for fraction, data in report['budgets'].items():
        print('budget', fraction, {m: round(v['mean_correct'], 2) for m, v in data['methods'].items()})
    print('primary_gate', report['exploratory_method_gate_pass'])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=Path, default=Path('/private/tmp/repguard_appworld_leaderboard'))
    parser.add_argument('--data-root', type=Path, default=Path('/private/tmp/repguard_appworld_data010/data'))
    parser.add_argument('--manifest', type=Path, default=Path('docs/analysis/dart_leaderboard_pool_manifest_2026-10-04.json'))
    parser.add_argument('--capability', type=Path, default=Path('results/dart_leaderboard_v1'))
    parser.add_argument('--output', type=Path, default=Path('results/dart_audit_selfreport_v1'))
    parser.add_argument('--seeds', type=int, default=20)
    args = parser.parse_args()
    if args.seeds != 20:
        parser.error('Frozen pilot requires all 20 seeds; change protocol before other research runs')
    try:
        run(args)
    except Exception as exc:
        args.output.mkdir(parents=True, exist_ok=True)
        write_status(args.output, state='failed', error_type=type(exc).__name__, error=str(exc))
        raise


if __name__ == '__main__':
    main()
