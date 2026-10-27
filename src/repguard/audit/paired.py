"""Uniform task-block audits with exact record budgets and known inclusion.

This is a sampling-design control, not a claim of a novel routing method.
"""
from __future__ import annotations

import numpy as np
from collections.abc import Callable

from repguard.audit.design import corrected_policy_values


def paired_sample(shape: tuple[int, int], budget: int, rng: np.random.Generator) -> np.ndarray:
    n, k = shape
    if n < 1 or k < 1 or not 0 < budget <= n*k:
        raise ValueError('Invalid task-agent dimensions or audit budget')
    full, remainder = divmod(budget, k)
    rows = rng.permutation(n)
    selected = (rows[:full, None]*k + np.arange(k)[None, :]).ravel()
    if remainder:
        selected = np.concatenate([selected, rows[full]*k+rng.permutation(k)[:remainder]])
    return selected


def joint_inclusion(shape: tuple[int, int], budget: int) -> tuple[float, float, float]:
    """Return marginal q, joint q for distinct same-row and different-row cells."""
    n, k = shape
    if n < 1 or k < 1 or not 0 < budget <= n*k:
        raise ValueError('Invalid dimensions/budget')
    full, r = divmod(budget, k)
    q = budget/(n*k)
    same = full/n + r*(r-1)/(n*k*(k-1)) if k > 1 else 0.
    different = (full*(full-1)+2*full*r/k)/(n*(n-1)) if n > 1 else 0.
    return q, same, different


def exact_ht_total_variance(values: np.ndarray, budget: int) -> float:
    """Finite-population design variance using ALL fixed values (diagnostic only).

    For policy differences, values include signed route coefficients and residuals.
    This is not an observable deployment variance estimator or confidence bound.
    """
    if values.ndim != 2 or not np.isfinite(values).all():
        raise ValueError('Expected a finite task-agent matrix')
    q, same, different = joint_inclusion(values.shape, budget)
    diagonal = float((values**2).sum())
    row_square = float((values.sum(axis=1)**2).sum())
    total_square = float(values.sum()**2)
    result = ((1/q-1)*diagonal + (same/q**2-1)*(row_square-diagonal)
              + (different/q**2-1)*(total_square-row_square))
    return max(0., result)  # remove roundoff at full budget / constant totals


def select_paired(routes: np.ndarray, proxy: np.ndarray, baseline: int, budget: int,
                  rng: np.random.Generator, audit: Callable[[np.ndarray], np.ndarray],
                  use_proxy: bool = True) -> dict:
    indices = paired_sample(proxy.shape, budget, rng)
    labels = np.asarray(audit(indices), dtype=float)
    if labels.shape != indices.shape or not np.isin(labels, [0,1]).all():
        raise ValueError('Invalid audit labels')
    observed = np.full(proxy.size, np.nan)
    observed[indices] = labels
    q = np.full(proxy.shape, budget/proxy.size)
    estimates = corrected_policy_values(routes, proxy if use_proxy else np.zeros_like(proxy),
                                        observed.reshape(proxy.shape), q)
    best = int(estimates.argmax())
    if np.isclose(estimates[baseline], estimates[best], atol=1e-12, rtol=0):
        best = baseline
    return {'selected_policy': best, 'audit_indices': indices.tolist(),
            'estimated_values': estimates.tolist(), 'marginal_inclusion': float(q.flat[0]),
            'certified': False}
