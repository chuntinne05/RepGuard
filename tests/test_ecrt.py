"""Unit tests for repguard.reputation.ecrt (ECRT method & components)."""

import pytest

from repguard.reputation.baselines import BetaParams
from repguard.reputation.ecrt import (
    ECRTReputation,
    FeedbackReliabilityEstimator,
    FeedbackReliabilityParams,
    build_ecrt_variants,
)
from repguard.reputation.episode import EpisodeRecord
from repguard.reputation.transfer import TransferEstimator


def _make_episode(
    agent_id: str = "agent-1",
    domain: str = "biology",
    model_answer: str = "A",
    ground_truth: str = "A",
    observed_feedback: float | None = 1.0,
) -> EpisodeRecord:
    return EpisodeRecord(
        episode_id=f"{agent_id}_t1_0",
        agent_id=agent_id,
        task_id="t1",
        domain=domain,
        agent_answer=model_answer,
        _ground_truth=ground_truth,
        observed_feedback=observed_feedback,
    )


class TestFeedbackReliabilityEstimator:
    def test_default_params(self):
        params = FeedbackReliabilityParams()
        assert params.sensitivity == 0.9
        assert params.specificity == 0.9
        assert params.p_correct_prior == 0.5

    def test_calibration_perfect_feedback(self):
        episodes = [
            _make_episode(model_answer="A", ground_truth="A", observed_feedback=1.0),
            _make_episode(model_answer="A", ground_truth="A", observed_feedback=1.0),
            _make_episode(model_answer="B", ground_truth="A", observed_feedback=0.0),
            _make_episode(model_answer="B", ground_truth="A", observed_feedback=0.0),
        ]
        estimator = FeedbackReliabilityEstimator()
        params = estimator.calibrate(episodes)
        assert params.sensitivity == pytest.approx(1.0)
        assert params.specificity == pytest.approx(1.0)
        assert params.p_correct_prior == pytest.approx(0.5)

    def test_calibration_skips_none_feedback(self):
        episodes = [
            _make_episode(model_answer="A", ground_truth="A", observed_feedback=None),
            _make_episode(model_answer="A", ground_truth="A", observed_feedback=1.0),
        ]
        estimator = FeedbackReliabilityEstimator()
        params = estimator.calibrate(episodes)
        assert params.sensitivity == pytest.approx(1.0)

    def test_infer_p_correct_positive_feedback(self):
        estimator = FeedbackReliabilityEstimator()
        params = FeedbackReliabilityParams(sensitivity=0.9, specificity=0.9, p_correct_prior=0.5)
        ep = _make_episode(observed_feedback=1.0)
        p, mass = estimator.infer_p_correct(ep, params)
        assert p == pytest.approx(0.9)
        assert mass == 1.0

    def test_infer_p_correct_negative_feedback(self):
        estimator = FeedbackReliabilityEstimator()
        params = FeedbackReliabilityParams(sensitivity=0.9, specificity=0.9, p_correct_prior=0.5)
        ep = _make_episode(observed_feedback=0.0)
        p, mass = estimator.infer_p_correct(ep, params)
        assert p == pytest.approx(0.1)
        assert mass == 1.0

    def test_infer_p_correct_missing_feedback(self):
        estimator = FeedbackReliabilityEstimator()
        params = FeedbackReliabilityParams(p_correct_prior=0.42)
        ep = _make_episode(observed_feedback=None)
        p, mass = estimator.infer_p_correct(ep, params)
        assert p == pytest.approx(0.42)
        assert mass == 0.0

    def test_oracle_p_correct(self):
        estimator = FeedbackReliabilityEstimator()
        ep_correct = _make_episode(model_answer="A", ground_truth="A")
        ep_wrong = _make_episode(model_answer="B", ground_truth="A")
        assert estimator.oracle_p_correct(ep_correct) == (1.0, 1.0)
        assert estimator.oracle_p_correct(ep_wrong) == (0.0, 1.0)


class TestECRTReputation:
    def test_unfitted_score_raises(self):
        ecrt = ECRTReputation()
        with pytest.raises(RuntimeError, match="called before fit"):
            ecrt.score("agent-1", "biology")

    def test_fit_returns_self(self):
        ecrt = ECRTReputation()
        res = ecrt.fit([])
        assert res is ecrt
        assert ecrt._fitted

    def test_score_same_domain(self):
        episodes = [
            _make_episode(agent_id="a1", domain="biology", model_answer="A", ground_truth="A", observed_feedback=1.0)
            for _ in range(10)
        ]
        params = FeedbackReliabilityParams(sensitivity=1.0, specificity=1.0, p_correct_prior=0.5)
        ecrt = ECRTReputation(reliability_params=params, mode="ecrt")
        ecrt.fit(episodes)
        score = ecrt.score("a1", "biology")
        # 10 correct episodes with weight 1.0 -> alpha = 1 + 10 = 11, beta = 1 -> mean = 11/12
        assert score.mean == pytest.approx(11.0 / 12.0)
        assert score.agent_id == "a1"
        assert score.target_domain == "biology"
        assert score.source == "ECRT-ecrt"

    def test_score_unrelated_domain_filters_out(self):
        episodes = [
            _make_episode(agent_id="a1", domain="psychology", model_answer="A", ground_truth="A", observed_feedback=1.0)
            for _ in range(10)
        ]
        # psychology -> math is unrelated in transfer taxonomy (tau = 0.0)
        ecrt = ECRTReputation(mode="ecrt")
        ecrt.fit(episodes)
        score = ecrt.score("a1", "math")
        # Zero evidence transferred -> prior Beta(1, 1) -> mean = 0.5
        assert score.mean == pytest.approx(0.5)

    def test_score_no_transfer_mode_allows_cross_domain(self):
        episodes = [
            _make_episode(agent_id="a1", domain="psychology", model_answer="A", ground_truth="A", observed_feedback=1.0)
            for _ in range(10)
        ]
        params = FeedbackReliabilityParams(sensitivity=1.0, specificity=1.0, p_correct_prior=0.5)
        ecrt = ECRTReputation(reliability_params=params, mode="no_transfer")
        ecrt.fit(episodes)
        score = ecrt.score("a1", "math")
        # In no_transfer mode, tau = 1.0 for all domains
        assert score.mean == pytest.approx(11.0 / 12.0)

    def test_score_no_reliability_mode(self):
        episodes = [
            _make_episode(agent_id="a1", domain="biology", observed_feedback=0.8),
            _make_episode(agent_id="a1", domain="biology", observed_feedback=0.2),
        ]
        ecrt = ECRTReputation(mode="no_reliability")
        ecrt.fit(episodes)
        score = ecrt.score("a1", "biology")
        # alpha = 1 + 0.8 + 0.2 = 2.0; beta = 1 + 0.2 + 0.8 = 2.0 -> mean = 2/4 = 0.5
        assert score.mean == pytest.approx(0.5)

    def test_name_and_repr(self):
        ecrt = ECRTReputation(mode="ecrt")
        assert ecrt.name == "ECRT-ecrt"
        assert "ECRTReputation" in repr(ecrt)


class TestBuildECRTVariants:
    def test_build_all_variants(self):
        variants = build_ecrt_variants()
        expected_keys = {
            "ECRT",
            "ECRT-noTransfer",
            "ECRT-noReliab",
            "ECRT-noUncert",
            "ECRT-oracleF",
            "ECRT-oracleFT",
        }
        assert set(variants.keys()) == expected_keys
        for name, v in variants.items():
            assert isinstance(v, ECRTReputation)
            assert not v._fitted
