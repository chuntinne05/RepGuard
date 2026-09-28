"""FeedbackCorruptor — controlled feedback noise and sparsity injection.

Implements the two experimental variables Q (Feedback Quality) from the
RepGuard research plan Section 8 factorial design:

    Q = feedback_quality ∈ {oracle, noisy, sparse, adversarial}

Usage:
    corruptor = FeedbackCorruptor(regime=FeedbackRegime.NOISY, noise_eta=0.2, seed=42)
    corrupted_episodes = corruptor.corrupt(episodes)

Design invariant:
    Ground truth (z_it) is NEVER modified. Only observed_feedback changes.
"""

from __future__ import annotations

import random
from enum import Enum
from typing import Sequence

from repguard.reputation.episode import EpisodeRecord


class FeedbackRegime(str, Enum):
    """Feedback quality regime (experimental variable Q).

    ORACLE:       Feedback = true correctness. Perfect signal. Upper bound.
    NOISY:        Feedback is flipped with probability eta (evaluator error).
    SPARSE:       Feedback is missing with probability (1 - rho). Only when available = oracle.
    NOISY_SPARSE: Both noise and sparsity applied simultaneously.
    ADVERSARIAL:  Attacker deliberately sends false positive feedback on incorrect answers.
    """

    ORACLE = "oracle"
    NOISY = "noisy"
    SPARSE = "sparse"
    NOISY_SPARSE = "noisy_sparse"
    ADVERSARIAL = "adversarial"


class FeedbackCorruptor:
    """Apply controlled feedback corruption to a list of EpisodeRecords.

    Args:
        regime:     The feedback quality regime to apply.
        noise_eta:  Flip probability ∈ [0, 1]. 0 = no noise, 1 = fully inverted.
                    Only used for NOISY, NOISY_SPARSE, ADVERSARIAL regimes.
        sparsity_rho: Feedback availability rate ∈ [0, 1]. 1.0 = fully observed,
                      0.0 = fully missing. Only used for SPARSE, NOISY_SPARSE.
        seed:       Random seed for reproducibility.
    """

    def __init__(
        self,
        regime: FeedbackRegime | str = FeedbackRegime.ORACLE,
        noise_eta: float = 0.0,
        sparsity_rho: float = 1.0,
        seed: int = 42,
    ) -> None:
        self.regime = FeedbackRegime(regime)
        self.noise_eta = noise_eta
        self.sparsity_rho = sparsity_rho
        self._rng = random.Random(seed)

    def corrupt(self, episodes: Sequence[EpisodeRecord]) -> list[EpisodeRecord]:
        """Apply feedback corruption to a sequence of episodes.

        Returns a new list of EpisodeRecords with modified observed_feedback.
        Ground truth (_ground_truth) is never modified.

        Args:
            episodes: Input episodes with oracle feedback.

        Returns:
            New list of EpisodeRecords with corrupted feedback signal.
        """
        corrupted = []
        for ep in episodes:
            corrupted.append(self._corrupt_episode(ep))
        return corrupted

    def _corrupt_episode(self, ep: EpisodeRecord) -> EpisodeRecord:
        """Corrupt a single episode according to the configured regime."""
        regime = self.regime

        # Start from oracle feedback (true correctness as float)
        oracle_fb: float = 1.0 if ep.oracle_correct() else 0.0

        if regime == FeedbackRegime.ORACLE:
            return ep.with_corrupted_feedback(oracle_fb)

        elif regime == FeedbackRegime.NOISY:
            noisy_fb = self._apply_noise(oracle_fb)
            return ep.with_corrupted_feedback(noisy_fb)

        elif regime == FeedbackRegime.SPARSE:
            if self._rng.random() > self.sparsity_rho:
                return ep.with_corrupted_feedback(None)  # Masked out
            return ep.with_corrupted_feedback(oracle_fb)

        elif regime == FeedbackRegime.NOISY_SPARSE:
            if self._rng.random() > self.sparsity_rho:
                return ep.with_corrupted_feedback(None)
            noisy_fb = self._apply_noise(oracle_fb)
            return ep.with_corrupted_feedback(noisy_fb)

        elif regime == FeedbackRegime.ADVERSARIAL:
            # Adversary: sends false positive feedback on incorrect answers
            # Models strategic reputation farming (agent pumps reputation by
            # providing false "correct" feedback on questions it got wrong)
            if not ep.oracle_correct() and self._rng.random() < self.noise_eta:
                return ep.with_corrupted_feedback(1.0)  # False positive attack
            return ep.with_corrupted_feedback(oracle_fb)

        else:
            raise ValueError(f"Unknown feedback regime: {regime}")

    def _apply_noise(self, feedback: float) -> float:
        """Flip feedback with probability noise_eta (random evaluator error)."""
        if self._rng.random() < self.noise_eta:
            return 1.0 - feedback  # Flip: correct→incorrect or vice versa
        return feedback

    def describe(self) -> str:
        """Human-readable description of this corruption configuration."""
        return (
            f"FeedbackCorruptor("
            f"regime={self.regime.value}, "
            f"η={self.noise_eta:.2f}, "
            f"ρ={self.sparsity_rho:.2f})"
        )

    def __repr__(self) -> str:
        return self.describe()
