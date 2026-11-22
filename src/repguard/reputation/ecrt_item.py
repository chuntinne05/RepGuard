"""ECRT-v2: item-level feedback reliability (protocol 2026-11-22).

Only ECRT-1 changes: a positive feedback is converted to p_it = q(bin(d_it)) with
q(b) = P(F=1 | B=1, d in b) calibrated on a calibration split, Beta(1,1). Negative feedback keeps the
ECRT Bayes inversion with the pooled sensitivity/specificity. tau = 1 (single domain).
Episodes flagged ``metadata["audited"]`` carry gold evidence: p = oracle correctness.
"""

from __future__ import annotations

from typing import Sequence

from repguard.reputation.ecrt import ECRTReputation, FeedbackReliabilityParams
from repguard.reputation.episode import EpisodeRecord

BIN_EDGES = (0.0, 0.1, 0.5)  # bins: d=0 | 0<d<=0.1 | 0.1<d<=0.5 | d>0.5


def d_bin(d: float) -> int:
    if d <= BIN_EDGES[0]:
        return 0
    return 1 if d <= BIN_EDGES[1] else 2 if d <= BIN_EDGES[2] else 3


def calibrate_q(cells: Sequence[tuple[float, bool]]) -> list[float]:
    """cells: (d, F==1) for calibration cells with B=1. Returns q per bin, Beta(1,1) posterior mean."""
    k, n = [0] * 4, [0] * 4
    for d, f in cells:
        b = d_bin(d)
        n[b] += 1
        k[b] += int(f)
    return [(k[b] + 1) / (n[b] + 2) for b in range(4)]


class ECRTItemReputation(ECRTReputation):
    def __init__(self, q_by_bin: Sequence[float], reliability_params: FeedbackReliabilityParams | None = None) -> None:
        super().__init__(reliability_params=reliability_params, mode="no_transfer", uncertainty_mode="lower_bound")
        self.q_by_bin = list(q_by_bin)

    def q(self, d: float) -> float:
        return self.q_by_bin[d_bin(d)]

    def _compute_p_correct(self, episode: EpisodeRecord) -> tuple[float, float]:
        if episode.observed_feedback is None:
            return (0.5, 0.0)
        if episode.metadata.get("audited"):
            return self.reliability_estimator.oracle_p_correct(episode)
        if episode.feedback_positive and "d" in episode.metadata:
            return (self.q(episode.metadata["d"]), 1.0)
        return self.reliability_estimator.infer_p_correct(episode, self.reliability_params)

    @property
    def name(self) -> str:
        return "ECRT-v2"
