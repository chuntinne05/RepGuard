from repguard.reputation.ecrt import ECRTReputation, FeedbackReliabilityParams
from repguard.reputation.ecrt_item import ECRTItemReputation, calibrate_q, d_bin
from repguard.reputation.episode import EpisodeRecord


def ep(i, b, f, d=None, audited=False):
    md = {} if d is None else {"d": d}
    if audited:
        md["audited"] = True
    return EpisodeRecord(f"e{i}", "a", f"t{i}", "mbpp", "1", "1" if f else "0", float(b), metadata=md)


def test_bins():
    assert [d_bin(x) for x in (0, 0.05, 0.1, 0.3, 0.5, 0.9)] == [0, 1, 1, 2, 2, 3]


def test_calibrate_q_beta11():
    q = calibrate_q([(0.0, True), (0.0, True), (0.0, False), (0.9, False)])
    assert q[0] == 3 / 5 and q[3] == 1 / 3 and q[1] == 0.5


def test_item_reputation_uses_bin_q_and_audit():
    q = [0.9, 0.5, 0.5, 0.1]
    rep = ECRTItemReputation(q).fit([ep(1, 1, 0, d=0.0), ep(2, 1, 0, d=0.9)])
    s = rep.score("a", "mbpp")
    assert abs(s.mean - (1 + 0.9 + 0.1) / 4) < 1e-9
    rep.fit([ep(3, 1, 0, d=0.0, audited=True)])
    assert abs(rep.score("a", "mbpp").mean - 1 / 3) < 1e-9  # gold F=0 overrides q


def test_equals_ecrt_when_q_is_pooled_bayes_and_no_d():
    params = FeedbackReliabilityParams(0.8, 0.7, 0.4)
    eps = [ep(1, 1, 1), ep(2, 0, 0), ep(3, 1, 0)]
    base = ECRTReputation(reliability_params=params, mode="no_transfer").fit(eps).score("a", "mbpp")
    v2 = ECRTItemReputation([0.5] * 4, params).fit(eps).score("a", "mbpp")
    assert abs(base.mean - v2.mean) < 1e-12
