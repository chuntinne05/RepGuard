"""Fixed-budget randomized auditing and design-unbiased policy contrasts.

Pivotal sampling preserves supplied first-order inclusion probabilities while
selecting exactly B distinct records. It is not independent Bernoulli sampling;
ordinary iid standard errors must not be attached to its HT estimates.
"""
from __future__ import annotations

import numpy as np


def inclusion_probabilities(weights: np.ndarray, budget: int, floor_share: float = 0.2) -> np.ndarray:
    weights = np.asarray(weights, dtype=float)
    if weights.ndim != 1 or not len(weights) or not np.isfinite(weights).all():
        raise ValueError('Expected a nonempty finite weight vector')
    if (weights < 0).any() or not 0 < budget <= len(weights) or not 0 < floor_share <= 1:
        raise ValueError('Invalid weights, budget or audit floor')
    if budget == len(weights):
        return np.ones(len(weights))
    if not weights.any():
        return np.full(len(weights), budget / len(weights))
    floor = floor_share * budget / len(weights)
    # Water filling: sum(min(1, floor + scale * weight)) = budget.
    weights = weights / weights.max() + 1e-12
    low, high = 0.0, float(budget) / weights.min()
    for _ in range(100):
        scale = (low + high) / 2
        if np.minimum(1.0, floor + scale * weights).sum() < budget:
            low = scale
        else:
            high = scale
    q = np.minimum(1.0, floor + (low + high) / 2 * weights)
    if not np.isclose(q.sum(), budget, atol=1e-8):
        raise ArithmeticError('Inclusion probability budget mismatch')
    return q


def pivotal_sample(probabilities: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Randomized pivotal rounding, with exact sample size and known marginals."""
    q = np.asarray(probabilities, dtype=float)
    if q.ndim != 1 or not np.isfinite(q).all() or (q < 0).any() or (q > 1).any():
        raise ValueError('Invalid inclusion probabilities')
    budget = round(float(q.sum()))
    if not np.isclose(q.sum(), budget, atol=1e-8):
        raise ValueError('Inclusion probabilities must sum to an integer')
    work = q.copy()
    order = list(rng.permutation(np.flatnonzero((work > 1e-10) & (work < 1 - 1e-10))))
    while len(order) >= 2:
        i, j = order.pop(), order.pop()
        up = min(1 - work[i], work[j])
        down = min(work[i], 1 - work[j])
        if rng.random() < down / (up + down):
            work[i] += up
            work[j] -= up
        else:
            work[i] -= down
            work[j] += down
        for k in (i, j):
            if 1e-10 < work[k] < 1 - 1e-10:
                order.append(k)
    selected = np.flatnonzero(work > 0.5)
    if len(selected) != budget:
        raise ArithmeticError('Pivotal sampler violated exact budget')
    return selected


def corrected_policy_values(
    routes: np.ndarray, proxy: np.ndarray, audited: np.ndarray, inclusion: np.ndarray,
) -> np.ndarray:
    """Evaluate fixed policies on audit history using only revealed gold.

    routes: policies x tasks; proxy/audited/inclusion: tasks x agents.
    Unaudited entries MUST be NaN. Proxy and routes must be frozen before these
    audit labels are revealed. The resulting values need not lie in [0, 1].
    They are estimates, never probabilities or Beta pseudo-counts.
    """
    routes = np.asarray(routes)
    proxy, audited, inclusion = (np.asarray(x, dtype=float) for x in (proxy, audited, inclusion))
    if proxy.ndim != 2 or audited.shape != proxy.shape or inclusion.shape != proxy.shape:
        raise ValueError('Audit arrays must have identical tasks x agents shapes')
    if not np.isfinite(proxy).all() or (proxy < 0).any() or (proxy > 1).any():
        raise ValueError('Proxy must be finite and bounded in [0, 1]')
    if not np.isfinite(inclusion).all() or (inclusion <= 0).any() or (inclusion > 1).any():
        raise ValueError('Positive inclusion probability required for every eligible record')
    if routes.ndim != 2 or routes.shape[1] != len(proxy) or routes.dtype.kind not in 'iu':
        raise ValueError('Routes must be a policies x tasks integer array')
    if (routes < 0).any() or (routes >= proxy.shape[1]).any():
        raise ValueError('Route agent index outside pool')
    mask = ~np.isnan(audited)
    if not np.isfinite(audited[mask]).all() or not np.isin(audited[mask], [0, 1]).all():
        raise ValueError('Trusted audit labels must be binary')
    corrected = proxy.copy()
    corrected[mask] += (audited[mask] - proxy[mask]) / inclusion[mask]
    return corrected[np.arange(len(proxy))[None, :], routes].mean(axis=1)


def disagreement_weights(routes: np.ndarray, proxy: np.ndarray, active: np.ndarray) -> np.ndarray:
    """Frozen acquisition heuristic: policy disagreement x residual uncertainty.

    This is a testable heuristic, not a proven optimal acquisition function.
    It has no access to audit-history or future task outcomes.
    """
    chosen = routes[active]
    frequency = np.zeros_like(proxy, dtype=float)
    for route in chosen:
        frequency[np.arange(len(proxy)), route] += 1 / len(chosen)
    frequency = np.clip(frequency, 0, 1)
    return np.sqrt(frequency * (1 - frequency) * (proxy * (1 - proxy) + 0.01))


def contrast_allocation(routes: np.ndarray, proxy: np.ndarray, budget: int) -> tuple[np.ndarray, dict]:
    """Allocate against ALL selectable policy contrasts, retaining uniform design.

    The objective is a diagonal residual-second-moment surrogate, not the true
    pivotal-sampling variance (which also involves joint inclusion probabilities).
    A bounded dual search proposes designs; uniform is retained if none improve
    the objective. No safety/optimality theorem is asserted for this heuristic.
    """
    n, agents = proxy.shape
    one_hot = np.eye(agents)[routes].reshape(len(routes), -1)
    second_moment = (proxy * (1-proxy) + 0.01).ravel()
    coefficients = []
    for a in range(len(routes)):
        for b in range(a + 1, len(routes)):
            contrast = (one_hot[a] - one_hot[b])**2
            if contrast.any():
                coefficients.append(contrast * second_moment)
    uniform = np.full(proxy.size, budget / proxy.size)
    if not coefficients:
        return uniform, {'uniform_objective': 0.0, 'selected_objective': 0.0}
    matrix = np.array(coefficients)
    best = uniform.copy()
    initial = best_score = float((matrix @ (1/best)).max())
    dual = np.full(len(matrix), 1/len(matrix))
    for _ in range(24):
        importance = np.sqrt(dual @ matrix)
        candidate = inclusion_probabilities(importance, budget)
        risks = matrix @ (1/candidate)
        score = float(risks.max())
        if score < best_score:
            best, best_score = candidate, score
        dual *= np.exp(risks / max(score, 1e-12))
        dual /= dual.sum()
    return best, {'uniform_objective': initial / n**2,
                  'selected_objective': best_score / n**2,
                  'selectable_contrasts': len(matrix), 'iterations': 24,
                  'objective_is_exact_sampling_variance': False}
