"""Unit tests for RepGuard Week 2 — Reputation Module (HistRepEval v0.1).

Tests cover:
    - EpisodeRecord: construction, oracle access, feedback mutation
    - FeedbackCorruptor: all regimes (oracle, noisy, sparse, adversarial)
    - GlobalBetaReputation: updates from feedback, prior behavior
    - SkillConditionedReputation: domain isolation
    - OracleReputation: ground-truth usage
    - ZeroEvidenceGate: abstain when evidence is insufficient
    - TransferEstimator: same/related/unrelated classification
    - ReputationAggregator: majority vote and reputation-weighted
    - ReputationMetrics: ECE, rank correlation
"""

from __future__ import annotations

import pytest

from repguard.reputation.episode import DomainTransferCondition, EpisodeRecord
from repguard.reputation.feedback import FeedbackCorruptor, FeedbackRegime
from repguard.reputation.baselines import (
    GlobalBetaReputation,
    OracleReputation,
    SkillConditionedReputation,
    UniformReputation,
    ZeroEvidenceGate,
    BetaParams,
)
from repguard.reputation.transfer import TransferEstimator
from repguard.reputation.aggregator import ReputationAggregator
from repguard.reputation.metrics import ReputationMetrics


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_episode(
    agent_id: str = "agent_a",
    domain: str = "math",
    agent_answer: str = "A",
    ground_truth: str = "A",
    feedback: float | None = 1.0,
    regime: str = "oracle",
    episode_id: str | None = None,
) -> EpisodeRecord:
    return EpisodeRecord(
        episode_id=episode_id or f"{agent_id}_{domain}_0",
        agent_id=agent_id,
        task_id="task_0",
        domain=domain,
        agent_answer=agent_answer,
        _ground_truth=ground_truth,
        observed_feedback=feedback,
        feedback_regime=regime,
    )


def _history_two_agents() -> list[EpisodeRecord]:
    """Minimal history: agent_a is great at math, agent_b great at biology."""
    episodes = []
    # agent_a: 4 correct, 1 wrong in math
    for i in range(4):
        episodes.append(_make_episode("agent_a", "math", "A", "A", 1.0, ep_id=f"a_math_{i}"))
    episodes.append(_make_episode("agent_a", "math", "B", "A", 0.0, ep_id="a_math_4"))
    # agent_a: 1 correct, 4 wrong in biology (bad)
    for i in range(4):
        episodes.append(_make_episode("agent_a", "biology", "B", "A", 0.0, ep_id=f"a_bio_{i}"))
    episodes.append(_make_episode("agent_a", "biology", "A", "A", 1.0, ep_id="a_bio_4"))

    # agent_b: 4 correct, 1 wrong in biology
    for i in range(4):
        episodes.append(_make_episode("agent_b", "biology", "A", "A", 1.0, ep_id=f"b_bio_{i}"))
    episodes.append(_make_episode("agent_b", "biology", "B", "A", 0.0, ep_id="b_bio_4"))
    # agent_b: 1 correct, 4 wrong in math
    for i in range(4):
        episodes.append(_make_episode("agent_b", "math", "B", "A", 0.0, ep_id=f"b_math_{i}"))
    episodes.append(_make_episode("agent_b", "math", "A", "A", 1.0, ep_id="b_math_4"))

    return episodes


def _make_episode(  # noqa: F811  (redefine with keyword ep_id)
    agent_id: str = "agent_a",
    domain: str = "math",
    agent_answer: str = "A",
    ground_truth: str = "A",
    feedback: float | None = 1.0,
    regime: str = "oracle",
    ep_id: str | None = None,
) -> EpisodeRecord:
    return EpisodeRecord(
        episode_id=ep_id or f"{agent_id}_{domain}_0",
        agent_id=agent_id,
        task_id="task_0",
        domain=domain,
        agent_answer=agent_answer,
        _ground_truth=ground_truth,
        observed_feedback=feedback,
        feedback_regime=regime,
    )


# ---------------------------------------------------------------------------
# EpisodeRecord tests
# ---------------------------------------------------------------------------

class TestEpisodeRecord:
    def test_oracle_correct_true(self) -> None:
        ep = _make_episode(agent_answer="A", ground_truth="A")
        assert ep.oracle_correct() is True

    def test_oracle_correct_false(self) -> None:
        ep = _make_episode(agent_answer="B", ground_truth="A")
        assert ep.oracle_correct() is False

    def test_case_insensitive(self) -> None:
        ep = _make_episode(agent_answer="a", ground_truth="A")
        assert ep.oracle_correct() is True

    def test_has_feedback_true(self) -> None:
        ep = _make_episode(feedback=1.0)
        assert ep.has_feedback is True

    def test_has_feedback_false(self) -> None:
        ep = _make_episode(feedback=None)
        assert ep.has_feedback is False

    def test_with_corrupted_feedback_preserves_truth(self) -> None:
        ep = _make_episode(agent_answer="A", ground_truth="A", feedback=1.0)
        corrupted = ep.with_corrupted_feedback(0.0)
        # Ground truth still accessible and still correct
        assert corrupted.oracle_correct() is True
        assert corrupted.observed_feedback == 0.0


# ---------------------------------------------------------------------------
# BetaParams tests
# ---------------------------------------------------------------------------

class TestBetaParams:
    def test_uniform_prior_mean(self) -> None:
        params = BetaParams(alpha=1.0, beta=1.0)
        assert abs(params.mean - 0.5) < 1e-9

    def test_update_increases_alpha_on_correct(self) -> None:
        params = BetaParams(alpha=1.0, beta=1.0)
        params.update(p_correct=1.0)
        assert params.alpha == 2.0
        assert params.beta == 1.0

    def test_update_increases_beta_on_incorrect(self) -> None:
        params = BetaParams(alpha=1.0, beta=1.0)
        params.update(p_correct=0.0)
        assert params.alpha == 1.0
        assert params.beta == 2.0

    def test_mean_after_5_correct(self) -> None:
        params = BetaParams(alpha=1.0, beta=1.0)
        for _ in range(5):
            params.update(1.0)
        # α=6, β=1 → mean = 6/7 ≈ 0.857
        assert abs(params.mean - 6 / 7) < 1e-9

    def test_evidence_count(self) -> None:
        params = BetaParams(alpha=1.0, beta=1.0)
        params.update(1.0)
        params.update(0.0)
        assert params.evidence_count == 2.0


# ---------------------------------------------------------------------------
# FeedbackCorruptor tests
# ---------------------------------------------------------------------------

class TestFeedbackCorruptor:
    def test_oracle_regime_matches_ground_truth(self) -> None:
        corruptor = FeedbackCorruptor(FeedbackRegime.ORACLE, seed=0)
        ep_correct = _make_episode(agent_answer="A", ground_truth="A", feedback=1.0)
        ep_wrong = _make_episode(agent_answer="B", ground_truth="A", feedback=1.0)
        out_c = corruptor._corrupt_episode(ep_correct)
        out_w = corruptor._corrupt_episode(ep_wrong)
        assert out_c.observed_feedback == 1.0
        assert out_w.observed_feedback == 0.0

    def test_noisy_flips_with_eta_one(self) -> None:
        """With η=1.0, every feedback is flipped."""
        corruptor = FeedbackCorruptor(FeedbackRegime.NOISY, noise_eta=1.0, seed=0)
        ep = _make_episode(agent_answer="A", ground_truth="A", feedback=1.0)
        out = corruptor._corrupt_episode(ep)
        assert out.observed_feedback == 0.0  # Flipped

    def test_sparse_masks_some_feedback(self) -> None:
        corruptor = FeedbackCorruptor(FeedbackRegime.SPARSE, sparsity_rho=0.5, seed=42)
        episodes = [_make_episode(ep_id=f"ep_{i}") for i in range(100)]
        corrupted = corruptor.corrupt(episodes)
        missing = sum(1 for ep in corrupted if not ep.has_feedback)
        # ~50% should be masked; allow wide range for small N
        assert 20 < missing < 80

    def test_adversarial_flips_incorrect_to_positive(self) -> None:
        """Adversarial regime sends false positive on incorrect answers."""
        corruptor = FeedbackCorruptor(FeedbackRegime.ADVERSARIAL, noise_eta=1.0, seed=0)
        ep = _make_episode(agent_answer="B", ground_truth="A", feedback=0.0)  # Wrong
        out = corruptor._corrupt_episode(ep)
        assert out.observed_feedback == 1.0  # Falsely positive

    def test_ground_truth_never_changes(self) -> None:
        """Corruption must never change the ground truth."""
        for regime in FeedbackRegime:
            corruptor = FeedbackCorruptor(regime, noise_eta=1.0, sparsity_rho=0.0, seed=0)
            ep = _make_episode(agent_answer="A", ground_truth="A")
            out = corruptor._corrupt_episode(ep)
            assert out.oracle_correct() is True  # Ground truth sealed


# ---------------------------------------------------------------------------
# GlobalBetaReputation tests
# ---------------------------------------------------------------------------

class TestGlobalBetaReputation:
    def test_prior_before_fit(self) -> None:
        rep = GlobalBetaReputation()
        rep.fit([])
        score = rep.score("agent_x", "math")
        assert abs(score.mean - 0.5) < 1e-9  # Uniform prior

    def test_all_correct_pushes_mean_high(self) -> None:
        episodes = [_make_episode(agent_answer="A", ground_truth="A", feedback=1.0, ep_id=f"e{i}") for i in range(10)]
        rep = GlobalBetaReputation()
        rep.fit(episodes)
        score = rep.score("agent_a", "math")
        assert score.mean > 0.8

    def test_all_wrong_pushes_mean_low(self) -> None:
        episodes = [_make_episode(agent_answer="B", ground_truth="A", feedback=0.0, ep_id=f"e{i}") for i in range(10)]
        rep = GlobalBetaReputation()
        rep.fit(episodes)
        score = rep.score("agent_a", "math")
        assert score.mean < 0.2

    def test_domain_agnostic(self) -> None:
        """Global Beta should give the same score regardless of target domain."""
        history = _history_two_agents()
        rep = GlobalBetaReputation()
        rep.fit(history)
        score_math = rep.score("agent_a", "math")
        score_bio = rep.score("agent_a", "biology")
        # Global beta pools all domains → same score
        assert abs(score_math.mean - score_bio.mean) < 1e-9

    def test_sparse_feedback_skipped(self) -> None:
        episodes = [_make_episode(feedback=None, ep_id=f"e{i}") for i in range(10)]
        rep = GlobalBetaReputation()
        rep.fit(episodes)
        score = rep.score("agent_a", "math")
        assert score.evidence_count == 0.0  # No feedback → no update


# ---------------------------------------------------------------------------
# SkillConditionedReputation tests
# ---------------------------------------------------------------------------

class TestSkillConditionedReputation:
    def test_domain_isolation(self) -> None:
        """Skill-conditioned: agent_a high in math, low in biology → scores reflect this."""
        history = _history_two_agents()
        rep = SkillConditionedReputation()
        rep.fit(history)

        score_a_math = rep.score("agent_a", "math")
        score_a_bio = rep.score("agent_a", "biology")

        assert score_a_math.mean > score_a_bio.mean  # Math specialist pattern

    def test_specialist_beats_generalist_in_domain(self) -> None:
        """In math, agent_a (specialist) should score higher than agent_b (weak in math)."""
        history = _history_two_agents()
        rep = SkillConditionedReputation()
        rep.fit(history)

        assert rep.score("agent_a", "math").mean > rep.score("agent_b", "math").mean
        assert rep.score("agent_b", "biology").mean > rep.score("agent_a", "biology").mean


# ---------------------------------------------------------------------------
# OracleReputation tests
# ---------------------------------------------------------------------------

class TestOracleReputation:
    def test_oracle_uses_ground_truth_not_feedback(self) -> None:
        """Oracle should be unaffected by noisy feedback."""
        # Episodes: agent is correct, but feedback says wrong
        episodes = [
            _make_episode(agent_answer="A", ground_truth="A", feedback=0.0, ep_id=f"e{i}")
            for i in range(5)
        ]
        oracle = OracleReputation()
        oracle.fit(episodes)
        score = oracle.score("agent_a", "math")
        # Oracle sees true correctness → mean should be high
        assert score.mean > 0.7

    def test_oracle_exceeds_noisy_reputation(self) -> None:
        """Oracle score (from truth) should be higher than global beta (from noisy feedback)."""
        episodes = [
            _make_episode(agent_answer="A", ground_truth="A", feedback=0.0, ep_id=f"e{i}")
            for i in range(10)
        ]  # Correct but feedback flipped
        oracle = OracleReputation().fit(episodes)
        global_beta = GlobalBetaReputation().fit(episodes)

        oracle_score = oracle.score("agent_a", "math").mean
        global_score = global_beta.score("agent_a", "math").mean

        assert oracle_score > global_score  # Oracle sees truth; global beta sees noise


# ---------------------------------------------------------------------------
# ZeroEvidenceGate tests
# ---------------------------------------------------------------------------

class TestZeroEvidenceGate:
    def test_gates_to_uniform_when_no_evidence(self) -> None:
        inner = SkillConditionedReputation().fit([])
        gate = ZeroEvidenceGate(inner, min_evidence=3.0)
        score = gate.score("agent_a", "math")
        assert abs(score.mean - 0.5) < 1e-9

    def test_passes_through_when_sufficient_evidence(self) -> None:
        episodes = [
            _make_episode(agent_answer="A", ground_truth="A", feedback=1.0, ep_id=f"e{i}")
            for i in range(5)
        ]
        inner = SkillConditionedReputation().fit(episodes)
        gate = ZeroEvidenceGate(inner, min_evidence=3.0)
        score = gate.score("agent_a", "math")
        # 5 episodes → evidence_count = 5 > 3 → pass through
        assert score.mean > 0.7


# ---------------------------------------------------------------------------
# TransferEstimator tests
# ---------------------------------------------------------------------------

class TestTransferEstimator:
    def test_same_domain_is_same(self) -> None:
        te = TransferEstimator()
        est = te.estimate("math", "math")
        assert est.condition == DomainTransferCondition.SAME
        assert est.tau == 1.0

    def test_same_cluster_is_related(self) -> None:
        te = TransferEstimator()
        est = te.estimate("math", "physics")  # Both STEM
        assert est.condition == DomainTransferCondition.RELATED
        assert est.tau == 0.5

    def test_different_cluster_is_unrelated(self) -> None:
        te = TransferEstimator()
        est = te.estimate("math", "law")  # STEM vs Humanities
        assert est.condition == DomainTransferCondition.UNRELATED
        assert est.tau == 0.0

    def test_biology_to_health_is_related(self) -> None:
        te = TransferEstimator()
        est = te.estimate("biology", "health")
        assert est.condition == DomainTransferCondition.RELATED

    def test_filter_episodes_same_only(self) -> None:
        episodes = [
            _make_episode(domain="math", ep_id="e1"),
            _make_episode(domain="physics", ep_id="e2"),
            _make_episode(domain="history", ep_id="e3"),
        ]
        te = TransferEstimator()
        filtered = te.filter_episodes_by_condition(
            episodes, "math", DomainTransferCondition.SAME
        )
        assert len(filtered) == 1
        assert filtered[0].domain == "math"

    def test_filter_episodes_related(self) -> None:
        episodes = [
            _make_episode(domain="math", ep_id="e1"),
            _make_episode(domain="physics", ep_id="e2"),
            _make_episode(domain="history", ep_id="e3"),
        ]
        te = TransferEstimator()
        filtered = te.filter_episodes_by_condition(
            episodes, "math", DomainTransferCondition.RELATED
        )
        assert len(filtered) == 2  # math + physics (STEM cluster)


# ---------------------------------------------------------------------------
# ReputationAggregator tests
# ---------------------------------------------------------------------------

class TestReputationAggregator:
    def test_majority_vote_simple(self) -> None:
        agg = ReputationAggregator()
        answers = {"a": "A", "b": "A", "c": "B"}
        result = agg.majority_vote(answers)
        assert result.chosen_answer == "A"

    def test_majority_vote_tie_deterministic(self) -> None:
        agg = ReputationAggregator()
        answers = {"a": "A", "b": "B"}
        result = agg.majority_vote(answers)
        assert result.chosen_answer in {"A", "B"}  # No crash on tie

    def test_reputation_weighted_follows_high_rep(self) -> None:
        from repguard.reputation.baselines import ReputationScore
        agg = ReputationAggregator(use_confidence_adjusted=False)
        answers = {"high_rep": "A", "low_rep": "B"}
        scores = {
            "high_rep": ReputationScore("high_rep", "math", mean=0.9, lower_bound=0.8, evidence_count=10, source="test"),
            "low_rep":  ReputationScore("low_rep",  "math", mean=0.1, lower_bound=0.05, evidence_count=10, source="test"),
        }
        result = agg.reputation_weighted_vote(answers, scores)
        # high_rep votes A with weight 0.9, low_rep votes B with weight 0.1 → A should win
        assert result.chosen_answer == "A"

    def test_empty_answers(self) -> None:
        agg = ReputationAggregator()
        result = agg.majority_vote({})
        assert result.chosen_answer == "?"


# ---------------------------------------------------------------------------
# ReputationMetrics tests
# ---------------------------------------------------------------------------

class TestReputationMetrics:
    def test_perfect_calibration_has_low_ece(self) -> None:
        from repguard.reputation.baselines import ReputationScore
        metrics = ReputationMetrics()
        scores = {
            "a": ReputationScore("a", "math", 0.8, 0.7, 10, "test"),
            "b": ReputationScore("b", "math", 0.4, 0.3, 10, "test"),
        }
        true_accs = {"a": 0.8, "b": 0.4}  # Perfect alignment
        result = metrics.evaluate(scores, true_accs, method="test", domain="math")
        assert result.ece < 0.1

    def test_rank_correlation_perfect(self) -> None:
        from repguard.reputation.baselines import ReputationScore
        metrics = ReputationMetrics()
        scores = {
            "a": ReputationScore("a", "math", 0.9, 0.8, 10, "test"),
            "b": ReputationScore("b", "math", 0.6, 0.5, 10, "test"),
            "c": ReputationScore("c", "math", 0.3, 0.2, 10, "test"),
        }
        true_accs = {"a": 0.9, "b": 0.6, "c": 0.3}
        result = metrics.evaluate(scores, true_accs, method="test", domain="math")
        assert abs(result.rank_correlation - 1.0) < 1e-6  # Perfect correlation

    def test_team_accuracy_computed(self) -> None:
        from repguard.reputation.baselines import ReputationScore
        metrics = ReputationMetrics()
        scores = {"a": ReputationScore("a", "math", 0.8, 0.7, 5, "test")}
        true_accs = {"a": 0.8}
        correct_flags = [True, True, False, True, False]
        result = metrics.evaluate(scores, true_accs, team_correct_flags=correct_flags)
        assert abs(result.team_accuracy - 0.6) < 1e-9
