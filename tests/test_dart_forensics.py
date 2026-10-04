from itertools import combinations

import numpy as np
import pytest

from repguard.audit.design import corrected_policy_values
from repguard.audit.forensics import choose, ridge_proxy, sampled_values


def test_finite_population_unbiasedness_and_census_normalization():
    y = np.array([[1., 0.], [0., 1.], [1., 0.]])
    proxy = np.array([[.1, .9], [.8, .2], [.3, .7]])
    routes = np.array([[0, 0, 0], [1, 1, 1], [0, 1, 0]])
    truth = y[np.arange(3)[None, :], routes].mean(axis=1)
    for budget in range(1, 7):
        values = []
        for subset in combinations(range(6), budget):
            ix = np.array(subset)
            q = np.full(budget, budget/6)
            estimate = sampled_values(routes, proxy, ix, y.ravel()[ix], q)
            observed = np.full_like(y, np.nan); observed.ravel()[ix] = y.ravel()[ix]
            np.testing.assert_allclose(estimate, corrected_policy_values(routes, proxy, observed, np.full_like(y, budget/6)), atol=1e-14)
            values.append(estimate)
        np.testing.assert_allclose(np.mean(values, axis=0), truth, atol=1e-14)
    np.testing.assert_allclose(sampled_values(routes, proxy, np.arange(6), y.ravel(), np.ones(6), normalized=True), truth)


def test_only_paid_labels_enter_calibration_and_estimation():
    rng = np.random.default_rng(42)
    scores = rng.random((12, 3)); gold = rng.integers(0, 2, scores.shape).astype(float)
    mask = rng.random(scores.shape) < .4
    anchors = np.where(mask, gold, np.nan)
    changed = np.where(mask, gold, 1-gold)
    expected = ridge_proxy(scores, anchors, scores)
    np.testing.assert_array_equal(expected, ridge_proxy(scores, np.where(mask, changed, np.nan), scores))
    assert np.isfinite(expected).all() and (expected >= 0).all() and (expected <= 1).all()
    ix = np.flatnonzero(mask); routes = np.zeros((1,12), dtype=int)
    np.testing.assert_array_equal(sampled_values(routes, expected, ix, gold.ravel()[ix], np.full(len(ix),.4)),
                                  sampled_values(routes, expected, ix, changed.ravel()[ix], np.full(len(ix),.4)))


def test_no_match_normalized_fallback_empty_calibration_and_invalid_input():
    p = np.array([[.2, .6], [.4, .8]])
    routes = np.array([[0, 0]])
    np.testing.assert_allclose(sampled_values(routes, p, np.array([1,3]), np.array([1,0]), np.array([.5,.5]), normalized=True), [.3])
    np.testing.assert_allclose(ridge_proxy(p, np.full_like(p,np.nan), p), .5)
    assert choose(np.array([.4,.4]), 1) == 1
    with pytest.raises(ValueError):
        sampled_values(routes, p, np.array([1,1]), np.array([1,0]), np.array([.5,.5]))
