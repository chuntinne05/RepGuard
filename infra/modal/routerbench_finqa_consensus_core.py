"""Frozen exact-answer agreement proxy for FinQA historical executions."""
import hashlib
import unicodedata

import numpy as np
from routerbench_finqa_feedback_core import crossfit


def select_queries(headroom_ids, old_pilot_ids):
    if len(headroom_ids) != 200 or len(set(headroom_ids)) != 200:
        raise ValueError('Changed 200-question development pool')
    if len(old_pilot_ids) != 48 or not set(old_pilot_ids) <= set(headroom_ids):
        raise ValueError('Changed previous pilot membership')
    remaining = set(headroom_ids) - set(old_pilot_ids)
    return sorted(remaining, key=lambda q: hashlib.sha256(
        ('repguard-finqa-consensus-v1:' + q).encode()).hexdigest())[:48]


def canonical(answer):
    return ' '.join(unicodedata.normalize('NFKC', answer).casefold().split())


def agreement_proxy(predictions):
    if len(predictions) != 48 or any(len(row) != 20 for row in predictions):
        raise ValueError('Expected 48 questions by 20 models')
    p = np.zeros((48, 20), float)
    missing = np.zeros((48, 20), bool)
    for i, row in enumerate(predictions):
        normalized = [canonical(value) for value in row]
        for j, answer in enumerate(normalized):
            missing[i, j] = not bool(answer)
            if answer:
                p[i, j] = sum(answer == normalized[k] for k in range(20) if k != j) / 19
    return p, missing


def pair_ratio(y, predicted, indices):
    pairs = [(a, b) for a in range(20) for b in range(a + 1, 20)]
    dy = np.column_stack([y[indices, a] - y[indices, b] for a, b in pairs])
    dp = np.column_stack([predicted[indices, a] - predicted[indices, b] for a, b in pairs])
    base = dy.var(0, ddof=1).sum()
    return float((dy - dp).var(0, ddof=1).sum() / base) if base > 0 else None


def analyze(y, p, missing):
    y = np.asarray(y, float)
    p = np.asarray(p, float)
    missing = np.asarray(missing, bool)
    if y.shape != (48, 20) or p.shape != y.shape or missing.shape != y.shape:
        raise ValueError('Incomplete consensus diagnostic matrix')
    if not np.isin(y, [0, 1]).all() or not np.isfinite(p).all() or not ((p >= 0) & (p <= 1)).all():
        raise ValueError('Invalid consensus diagnostic matrix')
    if np.any(p[missing] != 0):
        raise ValueError('Missing answer cannot receive positive proxy score')
    fit, gold = crossfit(y, p, missing)
    rng = np.random.default_rng(1404)
    samples = rng.integers(0, 48, (2000, 48))
    ratios = [pair_ratio(y, fit, ix) for ix in samples]
    ci = np.quantile(ratios, [.025, .975]).tolist() if all(r is not None for r in ratios) else None
    point = pair_ratio(y, fit, np.arange(48))
    operational = float((~missing).mean()) >= .9
    signal = operational and point is not None and point <= .9 and ci is not None and ci[1] < 1
    return {'questions': 48, 'models': 20, 'cells': 960,
            'prediction_coverage': float((~missing).mean()),
            'brier': {'raw_agreement': float(((p - y)**2).mean()),
                      'crossfit_agreement': float(((fit - y)**2).mean()),
                      'crossfit_gold_only': float(((gold - y)**2).mean())},
            'pair_residual_variance_ratio': point,
            'pair_residual_variance_ratio_ci95': ci,
            'raw_agreement_pair_ratio': pair_ratio(y, p, np.arange(48)),
            'operational_pass': operational, 'expansion_signal_pass': bool(signal),
            'scope': 'New 48-question development feedback diagnostic; full gold in cross-fit, no sparse-gold routing',
            'uncertainty': 'Question bootstrap of fixed cross-fit predictions; no refit or independent confirmation',
            'calibrated_predictions': fit.tolist(), 'gold_only_predictions': gold.tolist()}
