"""Reputation Baselines for RepGuard — HistRepEval v0.1 (Week 2).

Implements all mandatory baselines from the research plan (Section 9):
    1. UniformReputation      — equal weight (no reputation, pure majority)
    2. GlobalBetaReputation   — Beta(α,β) across all domains (no skill conditioning)
    3. SkillConditionedReputation — independent Beta per domain
    4. OracleReputation       — Beta from true correctness (upper bound, diagnostic)
    5. ZeroEvidenceGate       — abstain when evidence count < threshold

All Beta-based reputations follow the ECRT data model (Section 5):
    α_i = α_0 + Σ_t τ_it · m_it · p_it
    β_i = β_0 + Σ_t τ_it · m_it · (1 - p_it)
    μ_i = α_i / (α_i + β_i)

For Week 2 baselines, τ_it = 1.0 (no transfer discounting yet — that is ECRT in Week 3).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Sequence

from repguard.reputation.episode import EpisodeRecord


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class BetaParams:
    """Beta distribution parameters (α, β) for one agent × domain slot.

    Attributes:
        alpha: Pseudo-success count (≥ alpha_0 prior).
        beta:  Pseudo-failure count (≥ beta_0 prior).
    """
    alpha: float = 1.0  # Prior: uniform Beta(1,1)
    beta: float = 1.0

    @property
    def mean(self) -> float:
        """Posterior mean: μ = α / (α + β)."""
        return self.alpha / (self.alpha + self.beta)

    @property
    def lower_credible_bound(self) -> float:
        """Conservative 5th percentile (uncertainty-discounted estimate).

        Uses Wilson-style approximation for speed; sufficient for our purposes.
        A more precise version would use scipy.stats.beta.ppf(0.05, α, β).
        """
        n = self.alpha + self.beta
        p = self.mean
        z = 1.645  # 90% one-sided / 5th pct
        return max(0.0, (p - z * (p * (1 - p) / n) ** 0.5))

    @property
    def evidence_count(self) -> float:
        """Total evidence mass (α + β minus priors = actual observed evidence)."""
        return (self.alpha - 1.0) + (self.beta - 1.0)

    def update(self, p_correct: float, weight: float = 1.0) -> None:
        """Bayesian update with soft evidence.

        Args:
            p_correct: Probability (or 0/1 signal) that the answer was correct.
            weight:    Evidence weight (τ_it · m_it in ECRT; = 1.0 for baselines).
        """
        self.alpha += weight * p_correct
        self.beta += weight * (1.0 - p_correct)

    def __repr__(self) -> str:
        return f"Beta(α={self.alpha:.2f}, β={self.beta:.2f}, μ={self.mean:.3f})"


@dataclass
class ReputationScore:
    """Reputation estimate for one agent on a target domain.

    Attributes:
        agent_id:       Agent identifier.
        target_domain:  Domain for which reputation is estimated.
        mean:           Posterior mean reputation ∈ [0, 1].
        lower_bound:    Conservative credible lower bound ∈ [0, 1].
        evidence_count: Number of informative episodes used.
        source:         Which baseline/method produced this score.
    """
    agent_id: str
    target_domain: str
    mean: float
    lower_bound: float
    evidence_count: float
    source: str

    @property
    def confidence_adjusted(self) -> float:
        """Return lower_bound when evidence is weak, mean otherwise.

        Threshold: ≥ 5 informative episodes considered sufficient.
        """
        return self.mean if self.evidence_count >= 5 else self.lower_bound

    def __repr__(self) -> str:
        return (
            f"Rep({self.agent_id}@{self.target_domain} | "
            f"μ={self.mean:.3f} | lb={self.lower_bound:.3f} | "
            f"n={self.evidence_count:.1f} | {self.source})"
        )


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class BaseReputation(ABC):
    """Abstract base class for all reputation mechanisms.

    Subclasses must implement:
        fit(episodes): Learn reputation from historical episodes.
        score(agent_id, target_domain): Return ReputationScore.
    """

    ALPHA_0: float = 1.0  # Beta prior: uniform Beta(1,1)
    BETA_0: float = 1.0

    @abstractmethod
    def fit(self, episodes: Sequence[EpisodeRecord]) -> "BaseReputation":
        """Learn reputation parameters from historical episodes.

        Args:
            episodes: Historical episode records (feedback may be corrupted).

        Returns:
            self (for chaining)
        """

    @abstractmethod
    def score(self, agent_id: str, target_domain: str) -> ReputationScore:
        """Return reputation estimate for an agent on a target domain.

        Args:
            agent_id:      Agent to estimate reputation for.
            target_domain: Domain of the current (target) task.

        Returns:
            ReputationScore with posterior statistics.
        """

    def score_all(
        self,
        agent_ids: Sequence[str],
        target_domain: str,
    ) -> dict[str, ReputationScore]:
        """Convenience: score all agents for a target domain."""
        return {aid: self.score(aid, target_domain) for aid in agent_ids}

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier for this baseline."""


# ---------------------------------------------------------------------------
# 1. Uniform (no reputation — equal weight, pure majority vote reference)
# ---------------------------------------------------------------------------

class UniformReputation(BaseReputation):
    """Assigns equal reputation (0.5) to all agents, regardless of history.

    This is the no-reputation baseline: equivalent to unweighted majority vote.
    Any reputation mechanism that fails to beat this is not useful.
    """

    def fit(self, episodes: Sequence[EpisodeRecord]) -> "UniformReputation":
        # Collect agent IDs to know who exists
        self._agents: set[str] = {ep.agent_id for ep in episodes}
        return self

    def score(self, agent_id: str, target_domain: str) -> ReputationScore:
        return ReputationScore(
            agent_id=agent_id,
            target_domain=target_domain,
            mean=0.5,
            lower_bound=0.5,
            evidence_count=0.0,
            source=self.name,
        )

    @property
    def name(self) -> str:
        return "uniform"


# ---------------------------------------------------------------------------
# 2. Global Beta Reputation (no skill conditioning)
# ---------------------------------------------------------------------------

class GlobalBetaReputation(BaseReputation):
    """Global reputation baseline: Beta(α, β) pooled across ALL domains.

    This is the naïve reputation baseline — it treats all historical interactions
    as equally informative regardless of which domain they came from.

    Failure mode (hypothesis H2): An agent that is excellent at Math but poor at
    History will have the same global reputation as a moderate agent in all domains.
    This will be shown to mismatch when the current task is History.
    """

    def __init__(self) -> None:
        # agent_id → BetaParams (global, domain-agnostic)
        self._params: dict[str, BetaParams] = defaultdict(
            lambda: BetaParams(alpha=self.ALPHA_0, beta=self.BETA_0)
        )

    def fit(self, episodes: Sequence[EpisodeRecord]) -> "GlobalBetaReputation":
        """Update global Beta parameters from observed feedback."""
        for ep in episodes:
            if not ep.has_feedback:
                continue  # Skip missing feedback (sparse regime)
            p_correct = ep.observed_feedback  # Could be noisy signal
            self._params[ep.agent_id].update(p_correct=p_correct, weight=1.0)
        return self

    def score(self, agent_id: str, target_domain: str) -> ReputationScore:
        params = self._params.get(
            agent_id, BetaParams(alpha=self.ALPHA_0, beta=self.BETA_0)
        )
        return ReputationScore(
            agent_id=agent_id,
            target_domain=target_domain,
            mean=params.mean,
            lower_bound=params.lower_credible_bound,
            evidence_count=params.evidence_count,
            source=self.name,
        )

    @property
    def name(self) -> str:
        return "global_beta"


# ---------------------------------------------------------------------------
# 3. Skill-Conditioned Reputation (independent Beta per domain)
# ---------------------------------------------------------------------------

class SkillConditionedReputation(BaseReputation):
    """Independent Beta reputation per (agent, domain) pair.

    This is the skill-conditioned baseline: it only uses history from the
    exact same domain as the current task (transfer condition = SAME only).

    Strength: correctly identifies domain specialists (e.g., Gemma2 for Math).
    Weakness: high variance when domain history is sparse; ignores related-domain
              evidence that ECRT would exploit.
    """

    def __init__(self) -> None:
        # (agent_id, domain) → BetaParams
        self._params: dict[tuple[str, str], BetaParams] = defaultdict(
            lambda: BetaParams(alpha=self.ALPHA_0, beta=self.BETA_0)
        )

    def fit(self, episodes: Sequence[EpisodeRecord]) -> "SkillConditionedReputation":
        """Update per-domain Beta parameters from observed feedback."""
        for ep in episodes:
            if not ep.has_feedback:
                continue
            key = (ep.agent_id, ep.domain)
            self._params[key].update(p_correct=ep.observed_feedback, weight=1.0)
        return self

    def score(self, agent_id: str, target_domain: str) -> ReputationScore:
        key = (agent_id, target_domain)
        params = self._params.get(
            key, BetaParams(alpha=self.ALPHA_0, beta=self.BETA_0)
        )
        return ReputationScore(
            agent_id=agent_id,
            target_domain=target_domain,
            mean=params.mean,
            lower_bound=params.lower_credible_bound,
            evidence_count=params.evidence_count,
            source=self.name,
        )

    def domain_params(self, agent_id: str) -> dict[str, BetaParams]:
        """Return all domain-specific Beta params for one agent (for diagnostics)."""
        return {
            domain: params
            for (aid, domain), params in self._params.items()
            if aid == agent_id
        }

    @property
    def name(self) -> str:
        return "skill_conditioned"


# ---------------------------------------------------------------------------
# 4. Oracle Reputation (diagnostic upper bound)
# ---------------------------------------------------------------------------

class OracleReputation(BaseReputation):
    """Oracle reputation: uses TRUE correctness (z_it) instead of feedback.

    This is the diagnostic upper bound — it answers:
        "If feedback were perfect, how good would reputation be?"

    Never deploy this in real systems (ground truth is not available online).
    Used exclusively for calibration diagnostics and bottleneck analysis.

    Note: This is the ONLY baseline that calls ep.oracle_correct().
    """

    def __init__(self) -> None:
        # (agent_id, domain) → BetaParams
        self._params: dict[tuple[str, str], BetaParams] = defaultdict(
            lambda: BetaParams(alpha=self.ALPHA_0, beta=self.BETA_0)
        )
        # Also maintain global params for fair comparison with GlobalBeta
        self._global_params: dict[str, BetaParams] = defaultdict(
            lambda: BetaParams(alpha=self.ALPHA_0, beta=self.BETA_0)
        )

    def fit(self, episodes: Sequence[EpisodeRecord]) -> "OracleReputation":
        """Update using TRUE correctness (ground truth revealed for diagnostics)."""
        for ep in episodes:
            z = 1.0 if ep.oracle_correct() else 0.0  # True correctness
            key = (ep.agent_id, ep.domain)
            self._params[key].update(p_correct=z, weight=1.0)
            self._global_params[ep.agent_id].update(p_correct=z, weight=1.0)
        return self

    def score(self, agent_id: str, target_domain: str) -> ReputationScore:
        """Score from oracle domain-specific Beta (skill-conditioned oracle)."""
        key = (agent_id, target_domain)
        params = self._params.get(
            key, BetaParams(alpha=self.ALPHA_0, beta=self.BETA_0)
        )
        return ReputationScore(
            agent_id=agent_id,
            target_domain=target_domain,
            mean=params.mean,
            lower_bound=params.lower_credible_bound,
            evidence_count=params.evidence_count,
            source=self.name,
        )

    def global_score(self, agent_id: str) -> ReputationScore:
        """Oracle global (domain-agnostic) reputation for comparison."""
        params = self._global_params.get(
            agent_id, BetaParams(alpha=self.ALPHA_0, beta=self.BETA_0)
        )
        return ReputationScore(
            agent_id=agent_id,
            target_domain="__global__",
            mean=params.mean,
            lower_bound=params.lower_credible_bound,
            evidence_count=params.evidence_count,
            source="oracle_global",
        )

    @property
    def name(self) -> str:
        return "oracle"


# ---------------------------------------------------------------------------
# 5. Zero-Evidence Gate
# ---------------------------------------------------------------------------

class ZeroEvidenceGate(BaseReputation):
    """Abstain / fall back to uniform when evidence count < threshold.

    Wraps any other reputation mechanism and returns a uniform (0.5) score
    when insufficient historical evidence exists for the target domain.

    This prevents low-evidence estimates from dominating aggregation.
    Based on zero-evidence gate from Xia & Wang (2026).
    """

    def __init__(
        self,
        inner: BaseReputation,
        min_evidence: float = 3.0,
    ) -> None:
        """
        Args:
            inner:        The underlying reputation mechanism to wrap.
            min_evidence: Minimum evidence count required to return inner score.
                          Below this threshold, returns uniform 0.5 fallback.
        """
        self._inner = inner
        self.min_evidence = min_evidence

    def fit(self, episodes: Sequence[EpisodeRecord]) -> "ZeroEvidenceGate":
        self._inner.fit(episodes)
        return self

    def score(self, agent_id: str, target_domain: str) -> ReputationScore:
        inner_score = self._inner.score(agent_id, target_domain)
        if inner_score.evidence_count < self.min_evidence:
            # Insufficient evidence — fall back to uninformative prior
            return ReputationScore(
                agent_id=agent_id,
                target_domain=target_domain,
                mean=0.5,
                lower_bound=0.5,
                evidence_count=inner_score.evidence_count,
                source=f"{self.name}(gated→uniform)",
            )
        # Replace source label to reflect gating was applied but not triggered
        return ReputationScore(
            agent_id=inner_score.agent_id,
            target_domain=inner_score.target_domain,
            mean=inner_score.mean,
            lower_bound=inner_score.lower_bound,
            evidence_count=inner_score.evidence_count,
            source=f"{self.name}({inner_score.source})",
        )

    @property
    def name(self) -> str:
        return f"zero_evidence_gate[min={self.min_evidence}]"
