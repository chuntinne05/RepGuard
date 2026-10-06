"""Reproduce post-hoc, aggregate diagnostics after the frozen consensus gate failed."""
import json
from pathlib import Path

import numpy as np

import run_routerbench_finqa_consensus as cli
from routerbench_finqa_consensus_core import agreement_proxy, pair_ratio
from routerbench_finqa_consensus_pipeline import validate


def correlation(x, z):
    return float(np.corrcoef(np.asarray(x).ravel(), np.asarray(z).ravel())[0, 1])


def decomposition(y, predicted):
    pairs = [(a, b) for a in range(20) for b in range(a + 1, 20)]
    dy = np.column_stack([y[:, a] - y[:, b] for a, b in pairs])
    dp = np.column_stack([predicted[:, a] - predicted[:, b] for a, b in pairs])
    n = len(y)
    base = float(dy.var(0, ddof=1).sum())
    variance = float(dp.var(0, ddof=1).sum())
    covariance = float(((dy - dy.mean(0)) * (dp - dp.mean(0))).sum() / (n - 1))
    return {'gold_pair_variance_sum': base, 'proxy_pair_variance_sum': variance,
            'gold_proxy_covariance_sum': covariance,
            'identity_ratio': (base + variance - 2 * covariance) / base,
            'recomputed_ratio': pair_ratio(y, predicted, np.arange(n))}


def main():
    root = cli.OUTPUT / 'cloud'
    result = json.loads((root / 'analysis.json').read_text())
    pred = json.loads((root / 'predictions_private.json').read_text())
    validate(result); validate(pred)
    if result['expansion_signal_pass'] or result['run_id'] != pred['run_id']:
        raise ValueError('Not the failed frozen consensus run')
    gold = json.loads((root / 'pilot_gold_private.json').read_text())
    y = np.asarray(gold['success'], float)
    p, missing = agreement_proxy(pred['matrix'])
    fit = np.asarray(result['calibrated_predictions'])
    gold_fit = np.asarray(result['gold_only_predictions'])
    if y.shape != (48, 20) or fit.shape != y.shape or gold_fit.shape != y.shape:
        raise ValueError('Wrong frozen matrix dimensions')
    groups = {'missing': missing, 'nonmissing_no_match': (~missing) & (p == 0),
              'other_matches_1_to_3': (~missing) & (p > 0) & (p <= 3 / 19),
              'other_matches_4_to_9': (~missing) & (p > 3 / 19) & (p <= 9 / 19),
              'other_matches_10_plus': (~missing) & (p > 9 / 19)}
    bins = {name: {'cells': int(mask.sum()), 'correct': int(y[mask].sum()),
                   'accuracy': float(y[mask].mean()) if mask.any() else None}
            for name, mask in groups.items()}
    high_wrong = (p >= 10 / 19) & (y == 0)
    no_high_wrong = np.where(~high_wrong.any(1))[0]
    diagnostics = {
        'run_id': result['run_id'], 'analysis_type': 'posthoc_after_failed_frozen_gate',
        'raw_agreement': decomposition(y, p),
        'crossfit_agreement': decomposition(y, fit),
        'crossfit_gold_only': decomposition(y, gold_fit),
        'correlations': {
            'raw_question_mean_vs_gold_question_mean': correlation(p.mean(1), y.mean(1)),
            'raw_within_question_demeaned_vs_gold': correlation(p - p.mean(1, keepdims=True), y - y.mean(1, keepdims=True)),
            'raw_model_mean_vs_gold_model_mean': correlation(p.mean(0), y.mean(0)),
        },
        'agreement_bins': bins,
        'high_agreement_wrong_cells': int(high_wrong.sum()),
        'questions_with_high_agreement_wrong': int(high_wrong.any(1).sum()),
        'posthoc_ratio_excluding_questions_with_high_agreement_wrong': pair_ratio(y, fit, no_high_wrong),
        'best_fixed_correct': int(y.sum(0).max()),
        'question_oracle_correct': int(np.any(y == 1, axis=1).sum()),
    }
    for name in ('raw_agreement', 'crossfit_agreement', 'crossfit_gold_only'):
        d = diagnostics[name]
        if not np.isclose(d['identity_ratio'], d['recomputed_ratio'], atol=1e-12):
            raise ValueError('Pair variance identity mismatch')
    out = cli.ROOT / 'docs/analysis/routerbench_finqa_consensus_v1_diagnostics_2026-10-06.json'
    out.write_text(json.dumps(diagnostics, indent=2) + '\n')
    print(json.dumps(diagnostics, indent=2))


if __name__ == '__main__':
    main()
