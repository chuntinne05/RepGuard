"""Outcome-blind query selection and descriptive headroom statistics."""
import hashlib
import numpy as np

DATASETS = ('mbpp/test', 'finqa/test')
N_DEV = 200


def select_queries(dataset, common):
    if dataset not in DATASETS or len(common) < N_DEV:
        raise ValueError('Unsupported or insufficient development pool')
    return sorted(common, key=lambda q: hashlib.sha256(('repguard-headroom-dev-v1:' + dataset + ':' + q).encode()).hexdigest())[:N_DEV]


def analyze(y, models):
    y = np.asarray(y, float)
    if y.shape != (N_DEV, 20) or len(models) != 20 or not np.isfinite(y).all() or not ((y >= 0) & (y <= 1)).all():
        raise ValueError('Invalid headroom matrix')
    averages = y.mean(0)
    incumbent = int(np.flatnonzero(np.isclose(averages, averages.max(), atol=1e-12, rtol=0))[0])
    oracle = y.max(1)
    difference = oracle - y[:, incumbent]
    rng = np.random.default_rng(1404)
    samples = rng.integers(0, N_DEV, (5000, N_DEV))
    ci = np.quantile(difference[samples].mean(1), [.025, .975]).tolist()
    return {'questions': N_DEV, 'models': 20, 'model_order': list(models),
            'mean_reward_per_model': averages.tolist(), 'best_fixed_model': models[incumbent],
            'best_fixed_mean_reward': float(averages[incumbent]),
            'oracle_mean_reward': float(oracle.mean()), 'headroom': float(difference.mean()),
            'headroom_ci95_descriptive': ci,
            'strict_rescue_questions': int((difference > 1e-12).sum()),
            'fraction_strict_rescue': float((difference > 1e-12).mean()),
            'fractional_score_cells': int(((y > 0) & (y < 1)).sum())}
