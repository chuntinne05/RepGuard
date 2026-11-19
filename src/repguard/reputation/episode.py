"""EpisodeRecord — the atomic unit of historical interaction data in HistRepEval.

Each episode captures one agent answering one task in the historical period.
The ground-truth correctness (z) is hidden from reputation mechanisms except
in the explicit oracle condition, enforced via the 'oracle_only' access pattern.

Data model follows Section 5 of the RepGuard research plan:
    h_it = (q_t, y_it, x_t, F_it)
where z_it ∈ {0,1} is sealed and only exposed to evaluation metrics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DomainTransferCondition(str, Enum):
    """Transfer relationship between a historical episode and the current task.

    Used by TransferEstimator to compute τ(h_it, q*).
    """

    SAME = "same"           # Historical and target tasks share the exact domain
    RELATED = "related"     # Overlapping skill cluster (e.g., biology ↔ chemistry)
    UNRELATED = "unrelated" # Structurally different domains (e.g., math ↔ history)


@dataclass(frozen=True)
class EpisodeRecord:
    """Atomic historical interaction record for one agent on one task.

    Attributes:
        episode_id:   Unique identifier (e.g., "{agent_id}_{task_id}_{t}").
        agent_id:     Agent identifier (matches capability matrix row labels).
        task_id:      MMLU-Pro task identifier.
        domain:       Subject domain (e.g., "math", "biology").
        agent_answer: Agent's answer choice letter (A–J), or "" if abstained.
        _ground_truth: True correct answer (SEALED — access via oracle_correct only).
        observed_feedback: Feedback signal received (1.0 = correct, 0.0 = incorrect,
                           None = missing/sparse). May be noisy (corrupted feedback).
        feedback_regime:   Regime label under which feedback was generated.
        metadata:     Optional additional metadata dict (difficulty, question text, etc.).
    """

    episode_id: str
    agent_id: str
    task_id: str
    domain: str
    agent_answer: str
    _ground_truth: str  # Sealed — only expose via oracle_correct()
    observed_feedback: float | None  # None = missing (sparse feedback)
    feedback_regime: str = "oracle"
    metadata: dict[str, Any] = field(default_factory=dict)

    def oracle_correct(self) -> bool:
        """Return the true correctness (z_it).

        IMPORTANT: This must ONLY be called by:
        - OracleReputation baseline
        - Offline evaluation metrics

        Never call this inside any non-oracle reputation update method.
        """
        return self.agent_answer.upper() == self._ground_truth.upper()

    @property
    def has_feedback(self) -> bool:
        """Return True if observed feedback is available (not sparse-masked)."""
        return self.observed_feedback is not None

    @property
    def feedback_positive(self) -> bool:
        """Return True if available feedback indicates a correct answer.

        Returns False if feedback is missing. Check has_feedback first.
        """
        return self.observed_feedback is not None and self.observed_feedback >= 0.5

    def with_corrupted_feedback(self, new_feedback: float | None) -> "EpisodeRecord":
        """Return a new EpisodeRecord with corrupted/modified feedback signal.

        The ground truth remains sealed and unchanged.
        """
        return EpisodeRecord(
            episode_id=self.episode_id,
            agent_id=self.agent_id,
            task_id=self.task_id,
            domain=self.domain,
            agent_answer=self.agent_answer,
            _ground_truth=self._ground_truth,
            observed_feedback=new_feedback,
            feedback_regime=self.feedback_regime,
            metadata=self.metadata,
        )

    def __repr__(self) -> str:
        correct_str = "✓" if self.oracle_correct() else "✗"
        fb_str = f"{self.observed_feedback:.2f}" if self.observed_feedback is not None else "∅"
        return (
            f"Episode({self.agent_id} | {self.domain} | "
            f"ans={self.agent_answer} [{correct_str}] | fb={fb_str} | {self.feedback_regime})"
        )
