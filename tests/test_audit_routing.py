import numpy as np

from repguard.audit.routing import (
    TextFeatures, calibrated_proxy, construction_selection_split, select_policy,
)


def test_generators_never_cross_inner_partition():
    ids = [f'g{g}_{i}' for g in range(8) for i in range(3)]
    c, s = construction_selection_split(ids)
    assert not ({ids[i].split('_')[0] for i in c} & {ids[i].split('_')[0] for i in s})
    assert set(c) | set(s) == set(range(len(ids)))


def test_query_text_cannot_add_vocabulary():
    encoder = TextFeatures(['email calendar', 'calendar meeting'])
    vocab = encoder.vocabulary.copy()
    x = encoder.transform(['secretunseenterm'])
    assert encoder.vocabulary == vocab
    assert not x.any()


def test_channel_calibration_uses_only_revealed_anchors():
    feedback = np.array([[0, 1], [1, 1]])
    anchors = np.array([[np.nan, 1], [0, np.nan]])
    proxy = calibrated_proxy(feedback, anchors, feedback)
    assert np.isfinite(proxy).all()
    assert (proxy > 0).all() and (proxy < 1).all()


def test_unqueried_gold_cannot_change_policy_or_sampling():
    # Paired counterfactual fixture: change every hidden label outside the audit.
    proxy = np.array([[0.8, 0.6], [0.4, 0.6], [0.8, 0.7], [0.3, 0.5]])
    routes = np.array([[0, 0, 0, 0], [1, 1, 1, 1], [0, 1, 0, 1]])
    truth = np.array([1, 0, 1, 0, 0, 1, 0, 1])
    first = select_policy('DART', routes, proxy, 0, 3, np.random.default_rng(0),
                          lambda i: truth[i])
    altered = 1 - truth
    altered[first['audit_indices']] = truth[first['audit_indices']]
    second = select_policy('DART', routes, proxy, 0, 3, np.random.default_rng(0),
                           lambda i: altered[i])
    assert first == second
    assert first['audits'] == 3
    assert first['certified'] is False


def test_all_audit_arms_query_same_exact_budget():
    proxy = np.full((8, 3), 0.5)
    routes = np.tile(np.arange(3)[:, None], (1, 8))
    for method in ('AuditOnly', 'RandomHistory', 'UncertaintyHistory', 'DART'):
        requests = []

        def audit(indices):
            requests.extend(indices)
            return np.zeros(len(indices))

        result = select_policy(method, routes, proxy, 0, 6, np.random.default_rng(1), audit)
        assert result['audits'] == len(set(requests)) == 6
