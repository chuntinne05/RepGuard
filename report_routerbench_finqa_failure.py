"""Post-hoc, development-only diagnosis of the completed FinQA judge pilot."""
import hashlib
import json
from collections import Counter
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'infra/modal'))
from routerbench_finqa_feedback_core import MODEL, crossfit, probability  # noqa: E402
from routerbench_finqa_feedback_pipeline import validate  # noqa: E402

PRIVATE = ROOT / 'results/routerbench_finqa_feedback_v1/cloud'
OUT = ROOT / 'docs/analysis'


def pair_decomposition(y, predicted, models):
    columns = [i for i, model in enumerate(models) if model != 'MiMo-7B-RL-0530'] if models else list(range(y.shape[1]))
    pairs = [(a, b) for a in columns for b in columns if a < b]
    dy = np.column_stack([y[:, a] - y[:, b] for a, b in pairs])
    dp = np.column_stack([predicted[:, a] - predicted[:, b] for a, b in pairs])
    outcome_variance = float(dy.var(0, ddof=1).sum())
    predicted_variance = float(dp.var(0, ddof=1).sum())
    covariance = float(sum(np.cov(dy[:, i], dp[:, i], ddof=1)[0, 1] for i in range(len(pairs))))
    ratio = (outcome_variance + predicted_variance - 2 * covariance) / outcome_variance
    return {'pairs': len(pairs), 'outcome_variance_sum': outcome_variance,
            'predicted_variance_sum': predicted_variance, 'covariance_sum': covariance,
            'residual_variance_ratio': float(ratio)}


def subset_crossfit(y, p, features):
    n, k = y.shape
    base = np.tile(np.column_stack([np.ones(k), np.eye(k)])[None, :, :], (n, 1, 1))
    named = {'raw_p': p - .5, 'high_p': (p >= .9).astype(float) - .5,
             'question_mean': np.broadcast_to(p.mean(1, keepdims=True) - .5, p.shape)}
    x = np.concatenate([base, np.stack([named[name] for name in features], axis=2)], axis=2) if features else base
    penalty = np.array([0.] + [4.] * k + [1.] * len(features))
    result = np.zeros_like(y)
    for fold in range(4):
        train = np.arange(n) % 4 != fold
        test = ~train
        design = x[train].reshape(-1, x.shape[-1])
        beta = np.linalg.solve(design.T @ design + np.diag(penalty),
                               design.T @ (y[train].ravel() - .5))
        result[test] = np.clip(.5 + x[test] @ beta, 0, 1)
    return result


def corr(a, b):
    return float(np.corrcoef(np.asarray(a).ravel(), np.asarray(b).ravel())[0, 1])


def main():
    status = json.loads((PRIVATE / 'status.json').read_text())
    packet = json.loads((PRIVATE / 'input_private.json').read_text())
    ledger = json.loads((PRIVATE / 'ledger.json').read_text())
    inputs = json.loads((PRIVATE / 'judge_inputs_private.json').read_text())
    gold = json.loads((PRIVATE / 'pilot_gold_private.json').read_text())
    saved = json.loads((PRIVATE / 'analysis.json').read_text())
    audit = json.loads((ROOT / 'results/routerbench_finqa_feedback_v1/field_audit_private.json').read_text())
    validate(inputs)
    if not (status['state'] == 'completed_pilot_review_required' and len(ledger) == 960 and
            len(inputs['cases']) == 960 and audit['parent_run_id'] == packet['run_id'] == saved['run_id']):
        raise ValueError('Incomplete or mixed FinQA diagnostic inputs')
    models = gold['models']
    if models != packet['models'] or gold['query_ids'] != packet['query_ids']:
        raise ValueError('Mixed pilot gold')
    y = np.array(gold['success'], float)
    p = np.full((48, 20), np.nan)
    invalid = np.zeros((48, 20), bool)
    boxed = np.zeros((48, 20), bool)
    modes = Counter()
    for case in inputs['cases']:
        if hashlib.sha256(case['prompt'].encode()).hexdigest() != case['prompt_sha256']:
            raise ValueError('Changed judge input prompt')
        index = case['index']
        row = json.loads((PRIVATE / f'case_{index:04d}.json').read_text())
        validate(row)
        if not row['complete'] or row['artifact_sha256'] != ledger[str(index)]:
            raise ValueError('Case/ledger checksum mismatch')
        if not row['invalid']:
            response = row['attempts'][-1]['response']
            if response['model'] != MODEL or probability(response['message']['content']) != row['probability']:
                raise ValueError('Changed judge response')
        i, j = case['query_index'], case['model_index']
        p[i, j] = row['probability']
        invalid[i, j] = row['invalid']
        boxed[i, j] = case['extraction_mode'] == 'complete_boxed'
        modes[case['extraction_mode']] += 1
    if not np.isin(y, [0, 1]).all() or not np.isfinite(p).all() or invalid.any():
        raise ValueError('Unexpected pilot matrix')
    fit, gold_only = crossfit(y, p, invalid)
    if not np.allclose(fit, saved['calibrated_predictions']) or not np.allclose(gold_only, saved['gold_only_predictions']):
        raise ValueError('Cloud/local prediction mismatch')
    if abs(((fit-y)**2).mean() - saved['brier']['crossfit_judge']) > 1e-12:
        raise ValueError('Cloud/local Brier mismatch')
    full_pair = pair_decomposition(y, fit, None)
    no_mimo_pair = pair_decomposition(y, fit, models)
    if abs(full_pair['residual_variance_ratio'] - saved['pair_residual_variance_ratio']) > 1e-12:
        raise ValueError('Cloud/local pair ratio mismatch')
    ablations = {}
    for label, feature_names in (('gold_only', ()), ('question_mean_only', ('question_mean',)),
                                 ('raw_p_only', ('raw_p',)),
                                 ('raw_p_and_threshold', ('raw_p', 'high_p')),
                                 ('full', ('raw_p', 'high_p', 'question_mean'))):
        candidate = subset_crossfit(y, p, feature_names)
        if label == 'full' and not np.allclose(candidate, fit):
            raise ValueError('Ablation full model mismatch')
        ablations[label] = {'features': feature_names or ('model_identity',),
                            'brier': float(((candidate - y)**2).mean()),
                            'pair_residual_variance_ratio': pair_decomposition(y, candidate, None)['residual_variance_ratio']}
    mimo = models.index('MiMo-7B-RL-0530')
    fallback = ~boxed[:, mimo]
    counts = Counter(float(value) for value in p.ravel())
    fields = audit['members']
    if len(fields) != 20 or sum(x['selected'] for x in fields.values()) != 960:
        raise ValueError('Incomplete field audit')
    summary = {
        'parent_run_id': packet['run_id'], 'scope': 'Post-hoc descriptive development diagnosis; frozen gate unchanged',
        'questions': 48, 'models': 20, 'judgments': 960,
        'gold_success_fraction': float(y.mean()), 'raw_judge_mean': float(p.mean()),
        'raw_judge_distinct_values': dict(sorted(counts.items())),
        'raw_judge_threshold_accuracy': float(((p >= .5) == y).mean()),
        'raw_judge_false_high_p_ge_0_9': int(((p >= .9) & (y == 0)).sum()),
        'raw_judge_false_low_p_le_0_1': int(((p <= .1) & (y == 1)).sum()),
        'correlations': {
            'pooled_raw_probability_and_gold': corr(p, y),
            'question_means': corr(p.mean(1), y.mean(1)),
            'within_question_demeaned': corr(p-p.mean(1,keepdims=True), y-y.mean(1,keepdims=True)),
            'model_means': corr(p.mean(0), y.mean(0)),
            'model_means_excluding_MiMo': corr(np.delete(p,mimo,1).mean(0), np.delete(y,mimo,1).mean(0))},
        'pair_decomposition': full_pair,
        'pair_ratio_excluding_MiMo': no_mimo_pair['residual_variance_ratio'],
        'posthoc_feature_ablations': ablations,
        'extraction_modes': dict(modes),
        'mimo_fallback': {'count': int(fallback.sum()), 'gold_successes': int(y[fallback,mimo].sum()),
                          'judge_mean': float(p[fallback,mimo].mean()),
                          'false_high_p_ge_0_9': int(((p[fallback,mimo]>=.9)&(y[fallback,mimo]==0)).sum())},
        'raw_judge_global_reference': {'model': models[int(p.mean(0).argmax())],
                                       'gold_successes_on_48': int(y[:,p.mean(0).argmax()].sum())},
        'posthoc_best_fixed_reference': {'model': models[int(y.mean(0).argmax())],
                                         'gold_successes_on_48': int(y[:,y.mean(0).argmax()].sum())},
        'posthoc_question_oracle_successes_on_48': int(y.max(1).sum()),
        'field_audit': {key: int(sum(x[key] for x in fields.values())) for key in
                        ('selected','prediction_present','prediction_same_as_raw','prediction_has_boxed',
                         'raw_has_boxed','no_raw_box_prediction_present')},
    }
    path = OUT / 'routerbench_finqa_feedback_v1_diagnostics_2026-10-06.json'
    path.write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'diagnostics': str(path), 'gate': saved['expansion_signal_pass'],
                      'pair_ratio': full_pair['residual_variance_ratio'],
                      'no_MiMo_pair_ratio': no_mimo_pair['residual_variance_ratio'],
                      'field_prediction_present': summary['field_audit']['prediction_present']}))


if __name__ == '__main__':
    main()
