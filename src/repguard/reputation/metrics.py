"""Reputation evaluation metrics for HistRepEval v0.1 (Week 2).

Implements the three primary metrics from the RepGuard research plan Section 8:
    1. Expected Calibration Error (ECE)   — reputation ≈ true accuracy?
    2. Expert Leverage (EL)               — does high-rep agent get more weight?
    3. Reputation Rank Correlation (RRC)  — Spearman ρ(μ_i, true_accuracy_i)

These metrics measure the *quality* of the reputation mechanism itself,
independently from final team accuracy (which is also computed for completeness).

All metrics accept ReputationScore dicts and ground truth accuracy dicts.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Sequence

from repguard.reputation.baselines import ReputationScore


@dataclass
class MetricsResult:
    """Container for all reputation quality metrics.

    Attributes:
        ece:               Expected Calibration Error ∈ [0, 1]. Lower is better.
        expert_leverage:   Spearman ρ(reputation, true_accuracy) ∈ [-1, 1]. Higher is better.
        rank_correlation:  Spearman ρ(reputation_rank, accuracy_rank). Higher is better.
        team_accuracy:     Final team answer accuracy ∈ [0, 1].
        n_agents:          Number of agents evaluated.
        method:            Name of reputation method these metrics come from.
        domain:            Target domain (or "__all__" for pooled).
        extra:             Additional diagnostic values.
    """
    ece: float = 0.0
    expert_leverage: float = 0.0
    rank_correlation: float = 0.0
    team_accuracy: float = 0.0
    n_agents: int = 0
    method: str = "unknown"
    domain: str = "__all__"
    extra: dict[str, float] = field(default_factory=dict)

    def summary(self) -> str:
        return (
            f"[{self.method}@{self.domain}] "
            f"ECE={self.ece:.3f} | EL={self.expert_leverage:.3f} | "
            f"RRC={self.rank_correlation:.3f} | TeamAcc={self.team_accuracy:.3f}"
        )

    def __repr__(self) -> str:
        return self.summary()


class ReputationMetrics:
    """Compute reputation quality metrics from scores and ground truth.

    Usage:
        metrics = ReputationMetrics()
        result = metrics.evaluate(
            reputation_scores={"agent_a": score_a, "agent_b": score_b},
            true_accuracies={"agent_a": 0.8, "agent_b": 0.4},
            team_correct_flags=[True, False, True, ...],
            method="skill_conditioned",
            domain="math",
        )
    """

    def evaluate(
        self,
        reputation_scores: dict[str, ReputationScore],
        true_accuracies: dict[str, float],
        team_correct_flags: Sequence[bool] | None = None,
        method: str = "unknown",
        domain: str = "__all__",
        n_ece_bins: int = 10,
    ) -> MetricsResult:
        """Compute all reputation quality metrics.

        Args:
            reputation_scores:  Dict of agent_id → ReputationScore (posterior means).
            true_accuracies:    Dict of agent_id → true observed accuracy (ground truth).
                                Used for calibration and rank correlation.
            team_correct_flags: Optional list of booleans — team decision correctness
                                per task (for team accuracy computation).
            method:             Name of reputation method being evaluated.
            domain:             Target domain label.
            n_ece_bins:         Number of calibration bins for ECE.

        Returns:
            MetricsResult with all computed metrics.
        """
        agents = [aid for aid in reputation_scores if aid in true_accuracies]
        if not agents:
            return MetricsResult(method=method, domain=domain)

        rep_means = [reputation_scores[aid].mean for aid in agents]
        true_accs = [true_accuracies[aid] for aid in agents]

        ece = self._compute_ece(rep_means, true_accs, n_bins=n_ece_bins)
        el = self._compute_expert_leverage(rep_means, true_accs)
        rrc = self._spearman_correlation(rep_means, true_accs)

        team_acc = 0.0
        if team_correct_flags is not None and len(team_correct_flags) > 0:
            team_acc = sum(team_correct_flags) / len(team_correct_flags)

        return MetricsResult(
            ece=ece,
            expert_leverage=el,
            rank_correlation=rrc,
            team_accuracy=team_acc,
            n_agents=len(agents),
            method=method,
            domain=domain,
        )

    def _compute_ece(
        self,
        rep_means: list[float],
        true_accs: list[float],
        n_bins: int = 10,
    ) -> float:
        """Expected Calibration Error — does μ_i ≈ true_accuracy_i?

        Bins agents by reputation mean, computes weighted avg |mean_rep - mean_acc|
        across bins. Perfect calibration = ECE of 0.

        Note: With small agent pools (4 agents), ECE is coarse but still informative
        for comparing mechanisms (relative ECE).
        """
        if not rep_means:
            return 0.0

        n = len(rep_means)
        bin_size = 1.0 / n_bins
        bin_totals: dict[int, list[tuple[float, float]]] = {}

        for rep, acc in zip(rep_means, true_accs):
            bin_idx = min(int(rep / bin_size), n_bins - 1)
            bin_totals.setdefault(bin_idx, []).append((rep, acc))

        ece = 0.0
        for pairs in bin_totals.values():
            bin_n = len(pairs)
            avg_rep = sum(r for r, _ in pairs) / bin_n
            avg_acc = sum(a for _, a in pairs) / bin_n
            ece += (bin_n / n) * abs(avg_rep - avg_acc)

        return ece

    def _compute_expert_leverage(
        self,
        rep_means: list[float],
        true_accs: list[float],
    ) -> float:
        """Expert Leverage — does the reputation mechanism assign higher weight to
        the agents that are actually more accurate?

        Computed as: Spearman ρ(reputation, true_accuracy).
        Positive values indicate reputation correctly identifies better agents.
        Values near 0 indicate reputation is uninformative.
        Values < 0 indicate reputation is inversely correlated with truth (harmful!).
        """
        return self._spearman_correlation(rep_means, true_accs)

    def _spearman_correlation(
        self,
        x: list[float],
        y: list[float],
    ) -> float:
        """Spearman rank correlation between two lists.

        Returns 0.0 if insufficient data or zero variance in ranks.
        """
        n = len(x)
        if n < 2:
            return 0.0

        def rank(vals: list[float]) -> list[float]:
            """Average-rank assignment for tied values."""
            indexed = sorted(enumerate(vals), key=lambda iv: iv[1])
            ranks = [0.0] * n
            i = 0
            while i < n:
                j = i
                while j < n - 1 and indexed[j + 1][1] == indexed[j][1]:
                    j += 1
                avg_rank = (i + j) / 2.0 + 1
                for k in range(i, j + 1):
                    ranks[indexed[k][0]] = avg_rank
                i = j + 1
            return ranks

        rx = rank(x)
        ry = rank(y)

        mean_rx = sum(rx) / n
        mean_ry = sum(ry) / n

        num = sum((rx[i] - mean_rx) * (ry[i] - mean_ry) for i in range(n))
        den_x = math.sqrt(sum((r - mean_rx) ** 2 for r in rx))
        den_y = math.sqrt(sum((r - mean_ry) ** 2 for r in ry))

        if den_x < 1e-9 or den_y < 1e-9:
            return 0.0

        return num / (den_x * den_y)

    def compare_baselines(
        self,
        results: Sequence[MetricsResult],
    ) -> str:
        """Pretty-print a comparison table of multiple baseline results."""
        header = (
            f"{'Method':<30} {'Domain':<18} {'ECE':>6} "
            f"{'EL':>6} {'RRC':>6} {'TeamAcc':>8}"
        )
        sep = "-" * len(header)
        rows = [header, sep]
        for r in sorted(results, key=lambda m: m.team_accuracy, reverse=True):
            rows.append(
                f"{r.method:<30} {r.domain:<18} {r.ece:>6.3f} "
                f"{r.expert_leverage:>6.3f} {r.rank_correlation:>6.3f} "
                f"{r.team_accuracy:>8.3f}"
            )
        return "\n".join(rows)
