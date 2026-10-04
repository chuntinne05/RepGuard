"""Small policy class and gold-isolated learner for the exploratory DART pilot."""
from __future__ import annotations

import hashlib
import re
from collections import Counter
from collections.abc import Callable, Sequence

import numpy as np

from repguard.audit.design import (
    contrast_allocation, corrected_policy_values, disagreement_weights,
    inclusion_probabilities, pivotal_sample,
)


def generator_id(task_id: str) -> str:
    return task_id.rsplit('_', 1)[0]


def construction_selection_split(task_ids: Sequence[str]) -> tuple[np.ndarray, np.ndarray]:
    groups = sorted({generator_id(t) for t in task_ids},
                    key=lambda g: hashlib.sha256(('dart-inner-v1:' + g).encode()).hexdigest())
    construction = set(groups[:len(groups)//2])
    c = np.array([i for i, t in enumerate(task_ids) if generator_id(t) in construction])
    s = np.array([i for i, t in enumerate(task_ids) if generator_id(t) not in construction])
    if not len(c) or not len(s):
        raise ValueError('Need at least two training generators')
    return c, s


class TextFeatures:
    """Instruction-only TF-IDF; vocabulary and IDF are fitted on construction data."""
    @staticmethod
    def terms(text: str) -> list[str]:
        words = re.findall(r'[a-z][a-z0-9_]+', text.lower())
        return words + [a + ' ' + b for a, b in zip(words, words[1:])]

    def __init__(self, texts: Sequence[str]):
        counts = Counter(t for text in texts for t in set(self.terms(text)))
        terms = sorted(counts, key=lambda term: (-counts[term], term))[:4096]
        self.vocabulary = {t: i for i, t in enumerate(terms)}
        self.idf = np.array([np.log((1+len(texts))/(1+counts[t]))+1 for t in terms])

    def transform(self, texts: Sequence[str]) -> np.ndarray:
        x = np.zeros((len(texts), len(self.vocabulary)))
        for i, text in enumerate(texts):
            for term, n in Counter(self.terms(text)).items():
                if term in self.vocabulary:
                    j = self.vocabulary[term]
                    x[i, j] = (1 + np.log(n)) * self.idf[j]
        norm = np.linalg.norm(x, axis=1, keepdims=True)
        return x / np.maximum(norm, 1e-12)


def global_means(observed: np.ndarray) -> np.ndarray:
    return (np.nansum(observed, axis=0) + 1) / ((~np.isnan(observed)).sum(axis=0) + 2)


def knn_routes(similarity: np.ndarray, observed: np.ndarray, k: int) -> np.ndarray:
    means = global_means(observed)
    result = []
    for similarity_row in similarity:
        neighbors = np.argsort(-similarity_row, kind='stable')[:k]
        weight = np.maximum(similarity_row[neighbors], 0)[:, None]
        labels = observed[neighbors]
        scores = (np.nansum(labels * weight, axis=0) + means) / (
            (np.isfinite(labels) * weight).sum(axis=0) + 1)
        result.append(int(scores.argmax()))
    return np.array(result, dtype=int)


def policy_bank(similarity: np.ndarray, anchors: np.ndarray) -> tuple[list[str], np.ndarray]:
    agents = anchors.shape[1]
    names = [f'constant_{a}' for a in range(agents)] + ['anchor_knn3', 'anchor_knn10', 'anchor_knn30']
    routes = [np.full(len(similarity), a, dtype=int) for a in range(agents)]
    routes += [knn_routes(similarity, anchors, k) for k in (3, 10, 30)]
    return names, np.array(routes)


def uniform_audit_routes(
    similarity: np.ndarray, shape: tuple[int, int], budget: int,
    rng: np.random.Generator, audit: Callable[[np.ndarray], np.ndarray],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Strong simple controls: use the entire budget for fitting, with no split.

    Uniformly sampled historical labels train a smoothed global agent selector
    and kNN10 router. Both controls share this audit set, each costing B labels.
    """
    if similarity.shape[1] != shape[0] or not 0 < budget <= np.prod(shape):
        raise ValueError('Invalid history dimensions or audit budget')
    indices = rng.permutation(int(np.prod(shape)))[:budget]
    labels = np.asarray(audit(indices), dtype=float)
    if labels.shape != indices.shape or not np.isin(labels, [0, 1]).all():
        raise ValueError('Invalid trusted audit response')
    observed = np.full(shape, np.nan)
    observed.ravel()[indices] = labels
    constant = np.full(len(similarity), int(global_means(observed).argmax()))
    return constant, knn_routes(similarity, observed, 10), indices


def calibrated_proxy(feedback_c: np.ndarray, anchors: np.ndarray, feedback_s: np.ndarray) -> np.ndarray:
    """Partial-pool source channels using only shared construction audit labels."""
    out = np.empty(feedback_s.shape, dtype=float)
    for bit in (0, 1):
        mask = (feedback_c == bit) & np.isfinite(anchors)
        pooled = (anchors[mask].sum() + 1) / (mask.sum() + 2)
        for a in range(anchors.shape[1]):
            selected = mask[:, a]
            mean = (anchors[selected, a].sum() + 4 * pooled) / (selected.sum() + 4)
            out[feedback_s[:, a] == bit, a] = mean
    return out


def select_policy(
    method: str, routes: np.ndarray, proxy: np.ndarray, baseline: int, budget: int,
    rng: np.random.Generator, audit: Callable[[np.ndarray], np.ndarray],
) -> dict:
    """No gold parameter: trusted labels are available solely through audit().

    The acquisition design and candidate actions are fixed before calling audit.
    There is intentionally no unproved per-task safety certificate here.
    """
    proxy_values = proxy[np.arange(len(proxy))[None, :], routes].mean(axis=1)
    active = np.flatnonzero(proxy_values >= proxy_values.max() - 0.15)
    active = np.unique(np.append(active, baseline))
    design_diagnostics = {}
    if method == 'DARTContrast':
        weights = None
        active = np.arange(len(routes))
    elif method == 'DART':
        weights = disagreement_weights(routes, proxy, active)
    elif method == 'UncertaintyHistory':
        weights = np.sqrt(proxy * (1-proxy) + 0.01)
    elif method in ('AuditOnly', 'RandomHistory'):
        weights = np.ones_like(proxy)
    else:
        raise ValueError(f'Unknown audit method: {method}')
    if method == 'DARTContrast':
        q, design_diagnostics = contrast_allocation(routes, proxy, budget)
        q = q.reshape(proxy.shape)
    else:
        q = inclusion_probabilities(weights.ravel(), budget).reshape(proxy.shape)
    indices = pivotal_sample(q.ravel(), rng)
    labels = np.asarray(audit(indices), dtype=float)
    if labels.shape != indices.shape:
        raise ValueError('Audit must return exactly one label per requested record')
    observed = np.full(proxy.size, np.nan)
    observed[indices] = labels
    correction_proxy = np.zeros_like(proxy) if method == 'AuditOnly' else proxy
    values = corrected_policy_values(routes, correction_proxy, observed.reshape(proxy.shape), q)
    # Fixed tie-breaking: prefer the anchor baseline when value ties to tolerance.
    best = int(values.argmax())
    if np.isclose(values[baseline], values[best], atol=1e-12, rtol=0):
        best = baseline
    return {'selected_policy': best, 'estimated_values': values.tolist(),
            'audit_indices': indices.tolist(), 'audit_probabilities': q.ravel().tolist(),
            'active_candidates': active.tolist(), 'audits': len(indices),
            'effective_sample_size': float((1/q.ravel()[indices]).sum()**2 /
                                           ((1/q.ravel()[indices])**2).sum()),
            'design_diagnostics': design_diagnostics, 'certified': False}
