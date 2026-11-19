"""Synthetic fixtures test statistics only; they are never research outcomes."""
import numpy as np
import pytest

from repguard.audit.design import (
    corrected_policy_values, inclusion_probabilities, pivotal_sample,
)


def test_exact_budget_and_empirical_inclusion_probabilities():
    q = inclusion_probabilities(np.array([0, 0.1, 0.4, 2, 8, 50.0]), 3)
    rng = np.random.default_rng(711)
    counts = np.zeros(6)
    for _ in range(12000):
        selected = pivotal_sample(q, rng)
        assert len(selected) == len(set(selected)) == 3
        counts[selected] += 1
    assert np.max(np.abs(counts / 12000 - q)) < 0.018
    assert q.min() >= 0.2 * 3 / 6 - 1e-9


def test_residual_correction_unbiased_with_wrong_proxy():
    # Exactly enumerate two equiprobable one-label samples. Proxy ranking is wrong.
    proxy = np.array([[0.9, 0.1]])
    truth = np.array([[0.0, 1.0]])
    routes = np.array([[0], [1]])
    q = np.full((1, 2), 0.5)
    estimates = []
    for agent in range(2):
        seen = np.full((1, 2), np.nan)
        seen[0, agent] = truth[0, agent]
        estimates.append(corrected_policy_values(routes, proxy, seen, q))
    np.testing.assert_allclose(np.mean(estimates, axis=0), [0, 1], atol=1e-12)
    assert np.max(estimates) > 1  # HT correction is deliberately not clipped.


def test_all_labels_revealed_recovers_exact_policy_success():
    y = np.array([[1, 0], [0, 1], [1, 1]], dtype=float)
    routes = np.array([[0, 0, 0], [1, 1, 1], [0, 1, 0]])
    out = corrected_policy_values(routes, 1-y, y, np.ones_like(y))
    np.testing.assert_allclose(out, [2/3, 2/3, 1])


def test_invalid_probabilities_and_route_indices_fail_closed():
    with pytest.raises(ValueError):
        pivotal_sample(np.array([0.1, 0.3]), np.random.default_rng(0))
    with pytest.raises(ValueError):
        corrected_policy_values(np.array([[2]]), np.zeros((1, 2)),
                                np.full((1, 2), np.nan), np.ones((1, 2)))
    with pytest.raises(ValueError):
        inclusion_probabilities(np.array([1.0, -1.0]), 1)


def test_fixed_seed_is_reproducible():
    q = inclusion_probabilities(np.arange(20.0), 7)
    a = pivotal_sample(q, np.random.default_rng(4))
    b = pivotal_sample(q, np.random.default_rng(4))
    np.testing.assert_array_equal(a, b)
