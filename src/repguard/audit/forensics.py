"""Learners for the frozen same-audit ablation; no full-gold input allowed."""
from __future__ import annotations

import numpy as np


def ridge_proxy(scores_c: np.ndarray, anchors: np.ndarray, scores_s: np.ndarray) -> np.ndarray:
    """Fixed shared-slope calibration; only finite construction labels are used."""
    if scores_c.shape != anchors.shape or scores_s.shape[1] != anchors.shape[1]:
        raise ValueError('Calibration dimensions differ')
    if any(not np.isfinite(x).all() or (x < 0).any() or (x > 1).any()
           for x in (scores_c, scores_s)):
        raise ValueError('Scores must be finite probabilities')
    mask = np.isfinite(anchors)
    if not np.isin(anchors[mask], [0, 1]).all():
        raise ValueError('Calibration labels must be binary')
    row, agent = np.where(mask)
    k = anchors.shape[1]
    x = np.zeros((len(row), k+1))
    x[np.arange(len(row)), agent] = 1
    x[:, -1] = scores_c[mask] - .5
    pooled = (anchors[mask].sum()+1)/(mask.sum()+2)
    penalty = np.array([4.]*k+[1.])
    prior = np.array([pooled]*k+[0.])
    beta = np.linalg.solve(x.T@x+np.diag(penalty), x.T@anchors[mask]+penalty*prior)
    return np.clip(beta[:-1][None, :]+beta[-1]*(scores_s-.5), 0, 1)


def sampled_values(routes: np.ndarray, proxy: np.ndarray, indices: np.ndarray,
                   labels: np.ndarray, q: np.ndarray, *, normalized: bool = False) -> np.ndarray:
    """HT or normalized residual estimates using only observed q (never invented q)."""
    indices, labels, q = np.asarray(indices), np.asarray(labels), np.asarray(q)
    if (indices.ndim != 1 or labels.shape != indices.shape or q.shape != indices.shape
            or len(np.unique(indices)) != len(indices) or (indices < 0).any()
            or (indices >= proxy.size).any() or not np.isin(labels, [0, 1]).all()
            or not np.isfinite(q).all() or (q <= 0).any() or (q > 1).any()):
        raise ValueError('Invalid sampled labels or inclusion probabilities')
    if (proxy.ndim != 2 or not np.isfinite(proxy).all() or (proxy < 0).any()
            or (proxy > 1).any() or routes.ndim != 2 or routes.shape[1] != len(proxy)
            or routes.dtype.kind not in 'iu' or (routes < 0).any()
            or (routes >= proxy.shape[1]).any()):
        raise ValueError('Invalid proxy or routes')
    task, agent = np.divmod(indices, proxy.shape[1])
    matches = routes[:, task] == agent
    numerator = matches @ ((labels-proxy.ravel()[indices])/q)
    denominator = matches @ (1/q) if normalized else np.full(len(routes), len(proxy))
    correction = np.divide(numerator, denominator, out=np.zeros(len(routes)), where=denominator > 0)
    return proxy[np.arange(len(proxy))[None, :], routes].mean(axis=1)+correction


def choose(values: np.ndarray, baseline: int) -> int:
    best = int(values.argmax())
    return baseline if np.isclose(values[baseline], values[best], atol=1e-12, rtol=0) else best
