"""TransferEstimator — task transferability strata (experimental variable T).

Implements the transfer condition T from the RepGuard research plan Section 8:
    T = transfer_condition ∈ {same, related, unrelated}

This module computes τ(h_it, q*) — how relevant a historical episode from domain
`source_domain` is as evidence of competence on current task in `target_domain`.

Week 2 implementation: domain taxonomy / metadata-based (no learned model).
Week 3: may upgrade to empirical cross-domain performance correlation.

Domain groupings follow MMLU-Pro subject structure:
    STEM cluster:    math, physics, chemistry, biology, computer science, engineering
    Social cluster:  economics, psychology, business, history
    Humanities:      philosophy, history, law
    Health:          health, biology
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from repguard.reputation.episode import DomainTransferCondition


@dataclass(frozen=True)
class TransferEstimate:
    """Result of transfer estimation between source and target domains.

    Attributes:
        source_domain:   Domain of the historical episode.
        target_domain:   Domain of the current task.
        condition:       Categorical transfer condition (same/related/unrelated).
        tau:             Continuous transferability weight τ ∈ [0, 1].
    """
    source_domain: str
    target_domain: str
    condition: DomainTransferCondition
    tau: float

    def __repr__(self) -> str:
        return (
            f"Transfer({self.source_domain}→{self.target_domain} | "
            f"{self.condition.value} | τ={self.tau:.2f})"
        )


class TransferEstimator:
    """Estimate task transferability τ(h_it, q*) using domain taxonomy.

    Uses a predefined domain cluster hierarchy to assign continuous τ values:
        SAME:       τ = 1.0  (maximum relevance)
        RELATED:    τ = 0.5  (partial relevance — same cluster)
        UNRELATED:  τ = 0.0  (no relevance — different cluster)

    For Week 2 baselines, τ is used as a gate/mask rather than a soft weight.
    In ECRT (Week 3), τ will be used as a continuous multiplicative discount.

    Args:
        tau_same:      Transferability weight for SAME condition.
        tau_related:   Transferability weight for RELATED condition.
        tau_unrelated: Transferability weight for UNRELATED condition.
    """

    # Domain clusters for MMLU-Pro (simplified taxonomy)
    # Domains in the same cluster are considered "related"
    _CLUSTERS: ClassVar[dict[str, str]] = {
        # STEM
        "math":             "stem",
        "physics":          "stem",
        "chemistry":        "stem",
        "biology":          "stem_bio",
        "computer science": "stem",
        "engineering":      "stem",
        # Social science
        "economics":        "social",
        "psychology":       "social",
        "business":         "social",
        # Humanities & Law
        "history":          "humanities",
        "philosophy":       "humanities",
        "law":              "humanities",
        # Health
        "health":           "health_bio",
        # Other
        "other":            "other",
    }

    # Cross-cluster links: pairs that are considered "related" despite different clusters
    # Based on empirical skill overlap patterns in MMLU-Pro
    _RELATED_CROSS_CLUSTER: ClassVar[set[frozenset[str]]] = {
        frozenset({"stem_bio", "health_bio"}),  # Biology ↔ Health
        frozenset({"stem", "stem_bio"}),         # Eng/CS ↔ Biology (data sci overlap)
        frozenset({"social", "humanities"}),     # Economics ↔ History/Law
    }

    def __init__(
        self,
        tau_same: float = 1.0,
        tau_related: float = 0.5,
        tau_unrelated: float = 0.0,
    ) -> None:
        self.tau_same = tau_same
        self.tau_related = tau_related
        self.tau_unrelated = tau_unrelated

    def estimate(self, source_domain: str, target_domain: str) -> TransferEstimate:
        """Estimate transferability between source and target domains.

        Args:
            source_domain: Domain of the historical episode (where agent worked before).
            target_domain: Domain of the current task (where we need reputation).

        Returns:
            TransferEstimate with condition and τ weight.
        """
        src = source_domain.lower().strip()
        tgt = target_domain.lower().strip()

        if src == tgt:
            condition = DomainTransferCondition.SAME
            tau = self.tau_same

        elif self._is_related(src, tgt):
            condition = DomainTransferCondition.RELATED
            tau = self.tau_related

        else:
            condition = DomainTransferCondition.UNRELATED
            tau = self.tau_unrelated

        return TransferEstimate(
            source_domain=src,
            target_domain=tgt,
            condition=condition,
            tau=tau,
        )

    def _is_related(self, src: str, tgt: str) -> bool:
        """Check if source and target domains are in the same or related cluster."""
        src_cluster = self._CLUSTERS.get(src)
        tgt_cluster = self._CLUSTERS.get(tgt)

        if src_cluster is None or tgt_cluster is None:
            return False  # Unknown domains → unrelated (conservative)

        if src_cluster == tgt_cluster:
            return True  # Same cluster → related

        # Check cross-cluster related links
        pair = frozenset({src_cluster, tgt_cluster})
        return pair in self._RELATED_CROSS_CLUSTER

    def filter_episodes_by_condition(
        self,
        episodes: list,
        target_domain: str,
        min_condition: DomainTransferCondition = DomainTransferCondition.SAME,
    ) -> list:
        """Filter episodes to those meeting a minimum transfer condition.

        Args:
            episodes:      List of EpisodeRecord objects.
            target_domain: Target task domain.
            min_condition: Minimum acceptable transfer condition.
                           SAME → only exact same domain.
                           RELATED → same + related domains.
                           UNRELATED → all domains (no filtering).

        Returns:
            Filtered list of EpisodeRecords with sufficient transfer relevance.
        """
        if min_condition == DomainTransferCondition.UNRELATED:
            return list(episodes)  # No filter

        filtered = []
        for ep in episodes:
            est = self.estimate(ep.domain, target_domain)
            if min_condition == DomainTransferCondition.SAME:
                if est.condition == DomainTransferCondition.SAME:
                    filtered.append(ep)
            elif min_condition == DomainTransferCondition.RELATED:
                if est.condition in {
                    DomainTransferCondition.SAME,
                    DomainTransferCondition.RELATED,
                }:
                    filtered.append(ep)
        return filtered

    def tau_weights(
        self, episodes: list, target_domain: str
    ) -> list[float]:
        """Return τ weight for each episode relative to target_domain.

        Args:
            episodes:      List of EpisodeRecord objects.
            target_domain: Target task domain.

        Returns:
            List of τ values (same length as episodes).
        """
        return [
            self.estimate(ep.domain, target_domain).tau
            for ep in episodes
        ]
