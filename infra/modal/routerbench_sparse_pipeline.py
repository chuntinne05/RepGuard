"""Checkpointed finite development replay, with evaluator-owned gold access."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from routerbench_sparse_core import (Audit, METHODS, PRIMARY, CONTROLS, BUDGETS, SEEDS, MODELS,
                                    select_case, observed_from_log, predict)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def atomic(path, value):
    path = Path(path)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temp.replace(path)


def save(path, value):
    value = {k: v for k, v in value.items() if k != 'artifact_sha256'}
    value['artifact_sha256'] = digest(value)
    atomic(path, value)
    return value


def validate(value):
    if digest({k: v for k, v in value.items() if k != 'artifact_sha256'}) != value['artifact_sha256']:
        raise ValueError('Sparse replay artifact checksum mismatch')


def verify(packet):
    if digest({k: v for k, v in packet.items() if k != 'run_id'})[:24] != packet['run_id']:
        raise ValueError('Sparse replay input identity mismatch')
    if packet['parent_run_id'] != 'bad5a513bd5d227711eb1e0d' or packet['models'] != list(MODELS):
        raise ValueError('Changed pilot or model pool')
    for name in ('routerbench_sparse_core.py', 'routerbench_sparse_pipeline.py'):
        actual = hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
        if actual != packet['source_sha256']['infra/modal/' + name]:
            raise ValueError('Sparse replay source changed: ' + name)
    y = np.array(packet['success'], float)
    p = np.array(packet['judge_scores'], float)
    invalid = np.array(packet['judge_invalid'], bool)
    if y.shape != (48, 6) or p.shape != y.shape or invalid.shape != y.shape or not np.isin(y, [0, 1]).all():
        raise ValueError('Invalid fixed pilot matrix')
    if not np.isfinite(p).all() or not ((p >= 0) & (p <= 1)).all():
        raise ValueError('Invalid feedback')
    if packet['folds'] != (np.arange(48) % 4).tolist() or len(set(packet['query_ids'])) != 48:
        raise ValueError('Changed question split')
    expected = [{'budget_fraction': b, 'budget': int(np.ceil(b * 216)), 'fold': f,
                 'seed': s, 'rng_seed': 1404 + 1000 * f + s}
                for b in BUDGETS for f in range(4) for s in SEEDS]
    if packet['cases'] != expected or packet['methods'] != list(METHODS):
        raise ValueError('Changed cases/methods')


def case(packet, spec):
    """The evaluator slices history before providing any feedback or gold callback."""
    y = np.array(packet['success'], float)
    p = np.array(packet['judge_scores'], float)
    invalid = np.array(packet['judge_invalid'], bool)
    folds = np.array(packet['folds'])
    train, test = np.flatnonzero(folds != spec['fold']), np.flatnonzero(folds == spec['fold'])
    servers = {}

    def factory(name):
        if name in servers:
            raise ValueError('Audit server reused by an acquisition path')
        servers[name] = Audit(y[train], spec['budget'])
        return servers[name].query

    selections = select_case(p[train], invalid[train], spec['budget'], spec['rng_seed'], factory)
    if set(selections['agent_choices']) != set(METHODS):
        raise ValueError('Incomplete selections')
    logs = {}
    for name, server in servers.items():
        if len(server.indices) != len(set(server.indices)) or len(server.indices) != spec['budget']:
            raise ValueError('Gold budget not fully and uniquely used')
        logs[name] = {'indices': server.indices, 'labels': server.labels}
    # Choices are already fixed. Evaluation feedback is used only for predictive diagnostics.
    paired = logs['paired']
    observed = observed_from_log(len(train), 6, paired['indices'], paired['labels'])
    diag = {}
    for name, use_judge in (('gold', False), ('judge', True)):
        diag[name + '_predictions'] = predict(observed, p[train], invalid[train], p[test], invalid[test], use_judge).tolist()
    return {'spec': spec, 'train_indices': train.tolist(), 'test_indices': test.tolist(),
            'selections': selections, 'audits': logs, 'diagnostic': diag}


def summarize(packet, records):
    if len(records) != 240:
        raise ValueError('Cannot summarize incomplete sparse replay')
    y = np.array(packet['success'], float)
    best_fixed = float(y.mean(0).max())
    rng = np.random.default_rng(1404)
    bootstrap = rng.integers(0, 48, (5000, 48))
    pairs = [(a, b) for a in range(6) for b in range(a + 1, 6)]
    summaries = {}
    for budget in BUDGETS:
        outcomes = {m: np.full((20, 48), np.nan) for m in METHODS}
        choices = {m: np.full((20, 48), -1, int) for m in METHODS}
        predictions = {m: np.full((20, 48, 6), np.nan) for m in ('gold', 'judge')}
        empty_folds = []
        model_counts = []
        train_best_matches = {m: [] for m in METHODS}
        for row in records:
            spec = row['spec']
            if spec['budget_fraction'] != budget:
                continue
            s, ids = spec['seed'], np.array(row['test_indices'])
            train = np.array(packet['folds']) != spec['fold']
            train_means = y[train].mean(0)
            best_train = set(np.flatnonzero(np.isclose(train_means, train_means.max(), atol=1e-12, rtol=0)))
            for m, choice in row['selections']['agent_choices'].items():
                if np.isfinite(outcomes[m][s, ids]).any():
                    raise ValueError('Duplicate evaluation assignment')
                outcomes[m][s, ids] = y[ids, choice]
                choices[m][s, ids] = choice
                train_best_matches[m].append(choice in best_train)
            for m in predictions:
                predictions[m][s, ids] = row['diagnostic'][m + '_predictions']
            empty_folds.extend(t['empty_training_fallback'] for t in row['selections']['judge_crossfit_trace'])
            model_counts.append(np.bincount(np.array(row['audits']['paired']['indices']) % 6, minlength=6))
        if any(not np.isfinite(v).all() for v in (*outcomes.values(), *predictions.values())):
            raise ValueError('Missing evaluation assignments')
        methods = {m: {'mean_correct': float(v.sum(1).mean()), 'accuracy': float(v.mean()),
                       'regret_vs_posthoc_best_fixed': best_fixed - float(v.mean()),
                       'gold_labels_per_history': 0 if m == 'RawJudge' else int(np.ceil(budget * 216)),
                       'fraction_selecting_full_gold_train_best_reference': float(np.mean(train_best_matches[m])),
                       'model_choice_frequency': (np.bincount(choices[m].ravel(), minlength=6) / choices[m].size).tolist()}
                   for m, v in outcomes.items()}
        contrasts = {}
        for control in METHODS:
            if control == PRIMARY:
                continue
            diff = (outcomes[PRIMARY] - outcomes[control]).mean(0)
            ci = np.quantile(diff[bootstrap].mean(1), [.025, .975]).tolist()
            contrasts[control] = {'difference': float(diff.mean()), 'ci95': ci,
                                 'mean_rescues': float(((outcomes[PRIMARY] == 1) & (outcomes[control] == 0)).sum(1).mean()),
                                 'mean_harms': float(((outcomes[PRIMARY] == 0) & (outcomes[control] == 1)).sum(1).mean())}
        errors = {m: ((z - y) ** 2).mean(axis=(0, 2)) for m, z in predictions.items()}
        brier_gain = errors['gold'] - errors['judge']
        dy = np.column_stack([y[:, a] - y[:, b] for a, b in pairs])
        residuals = y[None, :, :] - predictions['judge']
        dr = np.stack([residuals[:, :, a] - residuals[:, :, b] for a, b in pairs], axis=2)
        denom = dy.var(0, ddof=1).sum()
        ratio = float(dr.var(1, ddof=1).sum(1).mean() / denom) if denom else None
        ratios = []
        for indices in bootstrap:
            d = dy[indices].var(0, ddof=1).sum()
            if d:
                ratios.append(float(dr[:, indices].var(1, ddof=1).sum(1).mean() / d))
        summaries[str(budget)] = {'methods': methods, 'primary_contrasts': contrasts,
            'diagnostic': {'crossfit_outer_brier': {m: float(v.mean()) for m, v in errors.items()},
                           'brier_gain': float(brier_gain.mean()),
                           'brier_gain_ci95': np.quantile(brier_gain[bootstrap].mean(1), [.025, .975]).tolist(),
                           'pair_residual_variance_ratio': ratio,
                           'pair_residual_variance_ratio_ci95': np.quantile(ratios, [.025, .975]).tolist() if len(ratios) == 5000 else None,
                           'empty_inner_training_partitions': int(sum(empty_folds)),
                           'total_inner_partitions': len(empty_folds),
                           'mean_paired_labels_per_model': np.mean(model_counts, axis=0).tolist()}}
    primary = summaries['0.1']['primary_contrasts']
    return {'budgets': summaries, 'development_expansion_gate_pass':
            all(primary[c]['ci95'][0] > 0 and primary[c]['difference'] >= .01 for c in CONTROLS),
            'tasks': 48, 'models': 6, 'cases': 240, 'method_selections': 2400,
            'posthoc_best_fixed_accuracy': best_fixed,
            'posthoc_per_model_accuracy': y.mean(0).tolist(),
            'posthoc_oracle_per_question_accuracy': float(y.max(1).mean()),
            'posthoc_model_disagreement_fraction': float((y.min(1) != y.max(1)).mean()),
            'scope': 'Development replay on already observed pilot; global model selection, not fresh solver calls or independent confirmation',
            'uncertainty': 'Question bootstrap of seed-averaged fixed decisions; no training refit, template grouping or adaptivity adjustment',
            'new_solver_calls': 0, 'new_judge_calls': 0}


def run(packet, root, commit=lambda: None):
    verify(packet)
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    ip = root / 'input_private.json'
    if ip.exists() and json.loads(ip.read_text()) != packet:
        raise ValueError('Changed sparse replay checkpoint identity')
    atomic(ip, packet)
    ledger = {}

    def status(state, **fields):
        value = {'run_id': packet['run_id'], 'state': state, 'total_cases': 240,
                 'updated_at': datetime.now(timezone.utc).isoformat(), **fields}
        atomic(root / 'status.json', value)
        commit()
        print(json.dumps(value), flush=True)
        return value

    try:
        status('replaying', completed_cases=0)
        records = []
        for index, spec in enumerate(packet['cases']):
            path = root / f'case_{index:04d}.json'
            if path.exists():
                row = json.loads(path.read_text())
                validate(row)
                if row['run_id'] != packet['run_id'] or row['index'] != index or row['spec'] != spec:
                    raise ValueError('Mixed sparse replay case')
            else:
                row = save(path, {'run_id': packet['run_id'], 'index': index, **case(packet, spec)})
            records.append(row)
            ledger[str(index)] = row['artifact_sha256']
            atomic(root / 'ledger.json', ledger)
            commit()
            if (index + 1) % 20 == 0:
                status('replaying', completed_cases=index + 1)
        status('analyzing', completed_cases=240)
        summary = summarize(packet, records)
        save(root / 'analysis.json', {'run_id': packet['run_id'], **summary})
        return status('completed_development_review_required', completed_cases=240,
                      method_selections=2400, development_expansion_gate_pass=summary['development_expansion_gate_pass'])
    except Exception as error:
        status('pipeline_failed', completed_cases=len(ledger), error=repr(error))
        raise
