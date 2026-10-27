"""ReputationAggregator — combine agent answers weighted by reputation scores.

Implements two aggregation strategies:
    1. Majority vote (uniform weights — no reputation)
    2. Reputation-weighted vote (soft weights from posterior mean or lower bound)

These are used to convert per-agent reputation scores into a final team decision
on each multiple-choice question.

The aggregation result includes the winning answer, confidence, and per-agent
contribution weights — needed for ExpertLeverage metric computation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from repguard.reputation.baselines import ReputationScore


@dataclass
class AggregationResult:
    """Result of aggregating agent votes into a final team answer.

    Attributes:
        chosen_answer:    The final answer letter selected (A–J).
        confidence:       Normalised confidence in chosen answer ∈ [0, 1].
        agent_weights:    Dict of agent_id → weight used in aggregation.
        vote_distribution: Dict of answer → total weight.
        method:           Name of aggregation method used.
    """
    chosen_answer: str
    confidence: float
    agent_weights: dict[str, float] = field(default_factory=dict)
    vote_distribution: dict[str, float] = field(default_factory=dict)
    method: str = "unknown"

    @property
    def is_correct(self) -> bool | None:
        """Check correctness — requires setting ground_truth after creation."""
        if not hasattr(self, "_ground_truth"):
            return None
        return self.chosen_answer.upper() == self._ground_truth.upper()

    def bind_ground_truth(self, ground_truth: str) -> "AggregationResult":
        """Attach ground truth for correctness checking."""
        self._ground_truth = ground_truth
        return self

    def __repr__(self) -> str:
        return (
            f"Agg({self.method} | answer={self.chosen_answer} | "
            f"conf={self.confidence:.3f})"
        )


class ReputationAggregator:
    """Aggregate agent votes into a team answer using reputation weights.

    Args:
        use_confidence_adjusted: If True, use lower_bound for low-evidence
                                  agents (conservative). If False, use mean.
    """

    def __init__(self, use_confidence_adjusted: bool = True) -> None:
        self.use_confidence_adjusted = use_confidence_adjusted

    def majority_vote(
        self,
        agent_answers: dict[str, str],
    ) -> AggregationResult:
        """Unweighted majority vote — baseline aggregation with no reputation.

        Args:
            agent_answers: Dict of agent_id → answer letter (A–J).

        Returns:
            AggregationResult with uniformly weighted vote.
        """
        n = len(agent_answers)
        if n == 0:
            return AggregationResult(
                chosen_answer="?",
                confidence=0.0,
                method="majority_vote",
            )

        uniform_weight = 1.0 / n
        vote_dist: dict[str, float] = {}
        agent_weights = {aid: uniform_weight for aid in agent_answers}

        for answer in agent_answers.values():
            vote_dist[answer.upper()] = vote_dist.get(answer.upper(), 0.0) + uniform_weight

        chosen = max(vote_dist, key=lambda a: vote_dist[a])
        confidence = vote_dist[chosen]

        return AggregationResult(
            chosen_answer=chosen,
            confidence=confidence,
            agent_weights=agent_weights,
            vote_distribution=vote_dist,
            method="majority_vote",
        )

    def reputation_weighted_vote(
        self,
        agent_answers: dict[str, str],
        reputation_scores: dict[str, ReputationScore],
    ) -> AggregationResult:
        """Reputation-weighted vote — weight each agent's vote by their reputation.

        Args:
            agent_answers:     Dict of agent_id → answer letter.
            reputation_scores: Dict of agent_id → ReputationScore for target domain.

        Returns:
            AggregationResult with reputation-weighted vote.
        """
        if not agent_answers:
            return AggregationResult(
                chosen_answer="?",
                confidence=0.0,
                method="reputation_weighted",
            )

        # Compute weights
        weights: dict[str, float] = {}
        for aid in agent_answers:
            if aid in reputation_scores:
                rep = reputation_scores[aid]
                w = rep.confidence_adjusted if self.use_confidence_adjusted else rep.mean
            else:
                w = 0.5  # Unknown agent → neutral weight
            weights[aid] = max(w, 1e-6)  # Prevent zero-weight

        # Normalise weights to sum to 1
        total_w = sum(weights.values())
        norm_weights = {aid: w / total_w for aid, w in weights.items()}

        # Tally weighted votes
        vote_dist: dict[str, float] = {}
        for aid, answer in agent_answers.items():
            a = answer.upper()
            vote_dist[a] = vote_dist.get(a, 0.0) + norm_weights[aid]

        chosen = max(vote_dist, key=lambda a: vote_dist[a])
        confidence = vote_dist[chosen]

        return AggregationResult(
            chosen_answer=chosen,
            confidence=confidence,
            agent_weights=norm_weights,
            vote_distribution=vote_dist,
            method="reputation_weighted",
        )

    def aggregate(
        self,
        agent_answers: dict[str, str],
        reputation_scores: dict[str, ReputationScore] | None = None,
    ) -> AggregationResult:
        """Convenience: auto-select aggregation method.

        Uses reputation-weighted if scores are provided, majority otherwise.
        """
        if reputation_scores is None:
            return self.majority_vote(agent_answers)
        return self.reputation_weighted_vote(agent_answers, reputation_scores)
