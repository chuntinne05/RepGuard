"""ECRT — Evidence-Calibrated Reputation Transfer (Week 3–4 Core Method).

Implements the ECRT posterior update from the RepGuard research plan (Section 5):

    α_i(q*) = α_0 + Σ_t  τ_it · m_it · p_it
    β_i(q*) = β_0 + Σ_t  τ_it · m_it · (1 - p_it)
    μ_i(q*) = α_i / (α_i + β_i)

where:
    p_it  = P(z_it = 1 | F_it)   — feedback-reliability-adjusted correctness probability
    τ_it  = τ(h_it, q*)          — task transferability weight ∈ [0, 1]
    m_it  = evidence mass         — 1.0 for observed feedback, 0.0 for missing

ECRT sub-components (ablation-aligned with Section 12):
    ECRT-1: FeedbackReliabilityEstimator  — infer p_it from imperfect feedback
    ECRT-2: TransferWeight                — compute τ via domain taxonomy
    ECRT-3: SoftEvidencePosterior         — Beta(α, β) with soft evidence
    ECRT-4: UncertaintyAwareInfluence     — lower credible bound or posterior mean
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Sequence

from repguard.reputation.baselines import (
    BaseReputation,
    BetaParams,
    ReputationScore,
)
from repguard.reputation.episode import EpisodeRecord
from repguard.reputation.transfer import TransferEstimator

logger = logging.getLogger("repguard.ecrt")


# ---------------------------------------------------------------------------
# ECRT-1: Feedback Reliability Estimator
# ---------------------------------------------------------------------------

@dataclass
class FeedbackReliabilityParams:
    """Calibrated feedback-source reliability from a calibration split.

    Attributes:
        sensitivity: P(F=1 | z=1) — true positive rate.
        specificity: P(F=0 | z=0) — true negative rate.
        p_correct_prior: Prior P(z=1) from calibration data.
    """
    sensitivity: float = 0.9
    specificity: float = 0.9
    p_correct_prior: float = 0.5


class FeedbackReliabilityEstimator:
    """ECRT-1: Estimate p_it = P(z_it=1|F_it) using Bayes theorem."""

    def calibrate(
        self,
        calibration_episodes: Sequence[EpisodeRecord],
    ) -> FeedbackReliabilityParams:
        """Estimate sensitivity and specificity from calibration episodes."""
        tp = fp = tn = fn = 0
        for ep in calibration_episodes:
            if ep.observed_feedback is None:
                continue
            z_true = ep.oracle_correct()
            f_obs = ep.observed_feedback >= 0.5
            if z_true and f_obs:
                tp += 1
            elif not z_true and f_obs:
                fp += 1
            elif not z_true and not f_obs:
                tn += 1
            else:
                fn += 1

        n_positive = tp + fn
        n_negative = tn + fp
        sensitivity = tp / n_positive if n_positive > 0 else 0.9
        specificity = tn / n_negative if n_negative > 0 else 0.9
        p_prior = n_positive / (n_positive + n_negative) if (n_positive + n_negative) > 0 else 0.5
        return FeedbackReliabilityParams(
            sensitivity=sensitivity, specificity=specificity, p_correct_prior=p_prior
        )

    def infer_p_correct(
        self,
        episode: EpisodeRecord,
        params: FeedbackReliabilityParams,
    ) -> tuple[float, float]:
        """Compute p_it = P(z_it=1|F_it) via Bayes theorem.

        Returns:
            (p_correct, evidence_mass)
        """
        if episode.observed_feedback is None:
            return (params.p_correct_prior, 0.0)
        f_positive = episode.observed_feedback >= 0.5
        pi = params.p_correct_prior
        sens = params.sensitivity
        spec = params.specificity
        if f_positive:
            p_f = sens * pi + (1.0 - spec) * (1.0 - pi)
            p_correct = (sens * pi) / max(p_f, 1e-8)
        else:
            p_f = (1.0 - sens) * pi + spec * (1.0 - pi)
            p_correct = ((1.0 - sens) * pi) / max(p_f, 1e-8)
        return (max(0.0, min(1.0, p_correct)), 1.0)

    def oracle_p_correct(self, episode: EpisodeRecord) -> tuple[float, float]:
        """Oracle ablation: use ground truth directly (diagnostic only)."""
        return (1.0 if episode.oracle_correct() else 0.0, 1.0)


# ---------------------------------------------------------------------------
# ECRT Core Reputation Method
# ---------------------------------------------------------------------------

class ECRTReputation(BaseReputation):
    """Evidence-Calibrated Reputation Transfer — core RepGuard method.

    Implements:
        α_i(q*) = α_0 + Σ_t [τ_it · m_it · p_it]
        β_i(q*) = β_0 + Σ_t [τ_it · m_it · (1 - p_it)]

    Ablation modes (aligned with Section 12 ablation table):
        ecrt:           Full ECRT — reliability + transfer + uncertainty
        no_transfer:    τ=1 for all episodes (ablate transfer discounting)
        no_reliability: Raw feedback, no Bayesian inversion
        no_uncertainty: Use posterior mean instead of lower credible bound
        oracle_f:       Oracle feedback + estimated transfer (diagnostic)
        oracle_ft:      Oracle feedback + explicitly supplied oracle transfer
    """

    def __init__(
        self,
        transfer_estimator: TransferEstimator | None = None,
        reliability_params: FeedbackReliabilityParams | None = None,
        mode: str = "ecrt",
        prior_alpha: float = 1.0,
        prior_beta: float = 1.0,
        uncertainty_mode: str = "lower_bound",
        oracle_transfer_estimator: TransferEstimator | None = None,
    ) -> None:
        if uncertainty_mode not in ("lower_bound", "mean"):
            raise ValueError("uncertainty_mode must be 'lower_bound' or 'mean'")
        if mode == "no_uncertainty":
            uncertainty_mode = "mean"
        self.transfer_estimator = transfer_estimator or TransferEstimator()
        self.oracle_transfer_estimator = oracle_transfer_estimator
        self.reliability_params = reliability_params or FeedbackReliabilityParams()
        self.reliability_estimator = FeedbackReliabilityEstimator()
        self.mode = mode
        self.prior_alpha = prior_alpha
        self.prior_beta = prior_beta
        self.uncertainty_mode = uncertainty_mode
        self._episodes: list[EpisodeRecord] = []
        self._fitted = False

    def fit(self, episodes: Sequence[EpisodeRecord]) -> "ECRTReputation":
        """Store episodes for on-demand posterior computation."""
        self._episodes = list(episodes)
        self._fitted = True
        return self

    def score(self, agent_id: str, target_domain: str) -> ReputationScore:
        """Compute ECRT posterior reputation for agent on target domain."""
        if not self._fitted:
            raise RuntimeError("ECRTReputation.score() called before fit()")

        beta = BetaParams(alpha=self.prior_alpha, beta=self.prior_beta)
        agent_episodes = [ep for ep in self._episodes if ep.agent_id == agent_id]

        for ep in agent_episodes:
            tau = self._compute_tau(ep.domain, target_domain)
            if tau <= 0.0:
                continue
            p_correct, evidence_mass = self._compute_p_correct(ep)
            if evidence_mass <= 0.0:
                continue
            beta.update(p_correct=p_correct, weight=tau * evidence_mass)

        return ReputationScore(
            agent_id=agent_id,
            target_domain=target_domain,
            mean=beta.mean,
            lower_bound=beta.lower_credible_bound,
            evidence_count=beta.evidence_count,
            source=f"ECRT-{self.mode}",
        )

    def _compute_tau(self, source_domain: str, target_domain: str) -> float:
        if self.mode == "no_transfer":
            return 1.0
        if self.mode == "oracle_ft":
            if self.oracle_transfer_estimator is None:
                raise ValueError(
                    "oracle_ft requires an explicit oracle_transfer_estimator; "
                    "the metadata taxonomy is not an oracle"
                )
            return self.oracle_transfer_estimator.estimate(source_domain, target_domain).tau
        return self.transfer_estimator.estimate(source_domain, target_domain).tau

    def decision_weight(self, score: ReputationScore) -> float:
        """Select the influence statistic specified by this ablation.

        Callers that directly read ``score.mean`` or ``score.lower_bound`` must
        make their own explicit choice; ``uncertainty_mode`` cannot alter either
        posterior summary itself.
        """
        return score.mean if self.uncertainty_mode == "mean" else score.lower_bound

    def _compute_p_correct(self, episode: EpisodeRecord) -> tuple[float, float]:
        if self.mode in ("oracle_f", "oracle_ft"):
            return self.reliability_estimator.oracle_p_correct(episode)
        if self.mode == "no_reliability":
            if episode.observed_feedback is None:
                return (0.5, 0.0)
            return (episode.observed_feedback, 1.0)
        return self.reliability_estimator.infer_p_correct(episode, self.reliability_params)

    @property
    def name(self) -> str:
        return f"ECRT-{self.mode}"

    def __repr__(self) -> str:
        return (
            f"ECRTReputation(mode={self.mode}, σ={self.uncertainty_mode}, ε={len(self._episodes)}ep)"
        )


# ---------------------------------------------------------------------------
# Ablation Factory
# ---------------------------------------------------------------------------

def build_ecrt_variants(
    transfer_estimator: TransferEstimator | None = None,
    reliability_params: FeedbackReliabilityParams | None = None,
    oracle_transfer_estimator: TransferEstimator | None = None,
) -> dict[str, ECRTReputation]:
    """Build all Week 4 ablation variants.

    Returns:
        Dict of variant_name -> ECRTReputation instance (all unfitted).
    """
    te = transfer_estimator or TransferEstimator()
    rp = reliability_params or FeedbackReliabilityParams()
    return {
        "ECRT":            ECRTReputation(te, rp, mode="ecrt",           uncertainty_mode="lower_bound"),
        "ECRT-noTransfer": ECRTReputation(te, rp, mode="no_transfer",    uncertainty_mode="lower_bound"),
        "ECRT-noReliab":   ECRTReputation(te, rp, mode="no_reliability", uncertainty_mode="lower_bound"),
        "ECRT-noUncert":   ECRTReputation(te, rp, mode="ecrt",           uncertainty_mode="mean"),
        "ECRT-oracleF":    ECRTReputation(te, rp, mode="oracle_f",       uncertainty_mode="lower_bound"),
        "ECRT-oracleFT":   ECRTReputation(
            te, rp, mode="oracle_ft", uncertainty_mode="lower_bound",
            oracle_transfer_estimator=oracle_transfer_estimator),
    }
