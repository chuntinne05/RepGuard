"""Experimental audited reputation with agent-specific feedback channels.

The method uses ground truth only for explicitly supplied audit episodes. Its
channel-strength weight is a conservative heuristic, not a Bayesian posterior
or a certified bound on downstream decision risk. Kept separate from the
historical ECRT implementation to preserve Week 3 reproducibility.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from repguard.reputation.baselines import BetaParams, ReputationScore
from repguard.reputation.episode import EpisodeRecord
from repguard.reputation.transfer import TransferEstimator


def _wilson_lower(successes: int, total: int, z: float = 1.645) -> float:
    if total <= 0:
        return 0.0
    p = successes / total
    z2 = z * z
    denominator = 1 + z2 / total
    center = (p + z2 / (2 * total)) / denominator
    radius = z * math.sqrt(p * (1 - p) / total + z2 / (4 * total * total)) / denominator
    return max(0.0, center - radius)


@dataclass(frozen=True)
class AuditedChannel:
    """A feedback channel estimated for one agent and source domain."""

    sensitivity: float
    specificity: float
    correctness_prior: float
    conservative_signal: float
    n_audited: int

    def correctness_given(self, feedback_positive: bool) -> float:
        pi = self.correctness_prior
        if feedback_positive:
            numerator = self.sensitivity * pi
            denominator = numerator + (1 - self.specificity) * (1 - pi)
        else:
            numerator = (1 - self.sensitivity) * pi
            denominator = numerator + self.specificity * (1 - pi)
        return numerator / denominator if denominator > 0 else pi


class AuditedECRTReputation:
    """Use gold audits as competence evidence and calibrate feedback per agent.

    Each observed history record contributes at most its source channel's
    conservative signal. A channel with no demonstrated positive signal adds
    no history evidence. Audited cases are always counted at their transfer
    weight and are never passed back through the noisy feedback channel.
    """

    def __init__(self, transfer_estimator: TransferEstimator | None = None) -> None:
        self.transfer_estimator = transfer_estimator or TransferEstimator()
        self._history: list[EpisodeRecord] = []
        self._audits: list[EpisodeRecord] = []
        self._channels: dict[tuple[str, str], AuditedChannel] = {}
        self._fitted = False

    @staticmethod
    def _estimate_channel(episodes: Sequence[EpisodeRecord]) -> AuditedChannel:
        tp = tn = positives = negatives = 0
        for episode in episodes:
            if episode.observed_feedback is None:
                continue
            if episode.oracle_correct():
                positives += 1
                tp += episode.feedback_positive
            else:
                negatives += 1
                tn += not episode.feedback_positive
        n = positives + negatives
        # Jeffreys smoothing avoids impossible zero-probability events.
        sensitivity = (tp + 0.5) / (positives + 1)
        specificity = (tn + 0.5) / (negatives + 1)
        prior = (positives + 0.5) / (n + 1)
        signal = max(0.0, _wilson_lower(tp, positives)
                     + _wilson_lower(tn, negatives) - 1.0)
        return AuditedChannel(sensitivity, specificity, prior, signal, n)

    def fit(self, history: Sequence[EpisodeRecord],
            audits: Sequence[EpisodeRecord]) -> AuditedECRTReputation:
        history_ids = {(episode.agent_id, episode.task_id) for episode in history}
        audit_ids = {(episode.agent_id, episode.task_id) for episode in audits}
        if history_ids & audit_ids:
            raise ValueError("History and gold audit episodes must be disjoint")
        self._history = list(history)
        self._audits = list(audits)
        grouped: dict[tuple[str, str], list[EpisodeRecord]] = {}
        for episode in self._audits:
            grouped.setdefault((episode.agent_id, episode.domain), []).append(episode)
        self._channels = {key: self._estimate_channel(rows)
                          for key, rows in grouped.items()}
        self._fitted = True
        return self

    def channel(self, agent_id: str, source_domain: str) -> AuditedChannel | None:
        if not self._fitted:
            raise RuntimeError("AuditedECRTReputation must be fitted")
        return self._channels.get((agent_id, source_domain))

    def score(self, agent_id: str, target_domain: str) -> ReputationScore:
        if not self._fitted:
            raise RuntimeError("AuditedECRTReputation must be fitted")
        beta = BetaParams()
        for episode in self._audits:
            if episode.agent_id != agent_id:
                continue
            tau = self.transfer_estimator.estimate(episode.domain, target_domain).tau
            if tau > 0:
                beta.update(float(episode.oracle_correct()), tau)
        for episode in self._history:
            if episode.agent_id != agent_id or episode.observed_feedback is None:
                continue
            tau = self.transfer_estimator.estimate(episode.domain, target_domain).tau
            channel = self._channels.get((agent_id, episode.domain))
            if tau <= 0 or channel is None or channel.conservative_signal <= 0:
                continue
            p = channel.correctness_given(episode.feedback_positive)
            beta.update(p, tau * channel.conservative_signal)
        return ReputationScore(agent_id, target_domain, beta.mean,
                               beta.lower_credible_bound, beta.evidence_count,
                               "audited_ecrt_experimental")
