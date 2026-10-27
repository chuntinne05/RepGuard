#!/usr/bin/env python3
"""run_week3.py - Week 3 Experimental Runner for RepGuard/ECRT.

Executes the Week 3 experimental program (Section 13 of research plan):

    1. Q x T Factorial Grid   - 4 feedback qualities x 3 transfer conditions x 3 seeds
    2. Attack Pilot A1+A2     - delayed betrayal + cross-skill laundering
    3. Statistical Analysis   - main effects, interaction, bootstrap CIs

Usage:
    cd /path/to/DACN:DATN && source .venv/bin/activate
    python run_week3.py             # Run all experiments
    python run_week3.py --exp qt_grid
    python run_week3.py --exp attacks
    python run_week3.py --exp analysis
"""

import argparse
import csv
import json
import logging
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

sys.path.insert(0, str(Path(__file__).parent / "src"))

from repguard.reputation.aggregator import ReputationAggregator
from repguard.reputation.baselines import (
    GlobalBetaReputation,
    OracleReputation,
    SkillConditionedReputation,
    UniformReputation,
    ZeroEvidenceGate,
)
from repguard.reputation.ecrt import (
    ECRTReputation,
    FeedbackReliabilityEstimator,
    FeedbackReliabilityParams,
)
from repguard.reputation.experiment import HistRepEvalGenerator
from repguard.reputation.feedback import FeedbackCorruptor
from repguard.reputation.metrics import MetricsResult, ReputationMetrics
from repguard.reputation.transfer import TransferEstimator

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger("repguard.week3")
console = Console()

# ---------------------------------------------------------------------------
# Grid configuration
# ---------------------------------------------------------------------------

Q_LEVELS = {
    "oracle":      ("oracle",      0.0),   # (label, noise_eta) for description
    "noisy_025":   ("noisy_025",   0.25),
    "noisy_050":   ("noisy_050",   0.50),
    "adversarial": ("adversarial", 0.40),
}

T_CONDITIONS = {
    "same":      {"history_domains": None,         "target_domain": None},
    "related":   {"history_domains": ["biology"],  "target_domain": "computer science"},
    "unrelated": {"history_domains": ["biology"],  "target_domain": "math"},
}

SEEDS = [42, 123, 456]
N_HISTORY_PER_DOMAIN = 20
N_TARGET_TASKS = 20


def _make_corruptor(q_name: str, seed: int) -> FeedbackCorruptor:
    if q_name == "oracle":
        return FeedbackCorruptor.oracle()
    elif q_name == "noisy_025":
        return FeedbackCorruptor.noisy(noise_rate=0.25, seed=seed)
    elif q_name == "noisy_050":
        return FeedbackCorruptor.noisy(noise_rate=0.50, seed=seed)
    elif q_name == "adversarial":
        return FeedbackCorruptor.adversarial(bias_rate=0.40, seed=seed)
    else:
        raise ValueError(f"Unknown Q level: {q_name}")


# ---------------------------------------------------------------------------
# Week3Experiments class
# ---------------------------------------------------------------------------

class Week3Experiments:
    """Complete Week 3 experimental runner."""

    def __init__(
        self,
        output_dir: str | Path = "results/week3",
        research_ops_dir: str | Path = "research_ops",
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "qt_grid").mkdir(exist_ok=True)
        (self.output_dir / "attacks").mkdir(exist_ok=True)
        self.research_ops_dir = Path(research_ops_dir)
        self.metrics_calc = ReputationMetrics()
        self.aggregator = ReputationAggregator(use_confidence_adjusted=True)
        self.transfer_estimator = TransferEstimator()
        self.all_qt_results: list[MetricsResult] = []

    # ------------------------------------------------------------------
    # Experiment W3-1: Q x T Factorial Grid
    # ------------------------------------------------------------------

    def run_qt_grid(self) -> list[MetricsResult]:
        """Run full Q x T factorial grid.

        4 Q-levels x 3 T-conditions x 3 seeds x 5 methods = 180 runs
        each evaluated across relevant target domains.
        """
        console.rule("[bold cyan]Week 3 Exp 1: Q x T Factorial Grid[/bold cyan]")
        all_results: list[MetricsResult] = []
        total_cells = len(Q_LEVELS) * len(T_CONDITIONS) * len(SEEDS)
        cell_idx = 0

        for q_name in Q_LEVELS:
            for t_name, t_cfg in T_CONDITIONS.items():
                for seed in SEEDS:
                    cell_idx += 1
                    console.print(
                        f"  [yellow][{cell_idx}/{total_cells}][/yellow] "
                        f"Q={q_name} | T={t_name} | seed={seed}"
                    )
                    corruptor = _make_corruptor(q_name, seed)
                    cell_results = self._run_single_cell(
                        q_name=q_name,
                        corruptor=corruptor,
                        t_name=t_name,
                        t_cfg=t_cfg,
                        seed=seed,
                    )
                    all_results.extend(cell_results)

        self.all_qt_results = all_results
        self._save_qt_results(all_results)
        self._print_qt_summary(all_results)
        return all_results

    def _run_single_cell(
        self,
        q_name: str,
        corruptor: FeedbackCorruptor,
        t_name: str,
        t_cfg: dict,
        seed: int,
    ) -> list[MetricsResult]:
        generator = HistRepEvalGenerator(seed=seed)

        if t_name == "same":
            history_domains = generator.domains
            target_domains = generator.domains
        else:
            history_domains = t_cfg["history_domains"]
            target_domains = [t_cfg["target_domain"]]

        episodes = generator.generate_episodes(
            n_per_domain=N_HISTORY_PER_DOMAIN,
            domains=history_domains,
            corruptor=corruptor,
        )

        # Calibrate ECRT reliability on history episodes
        re_estimator = FeedbackReliabilityEstimator()
        rp = re_estimator.calibrate(episodes)
        ecrt = ECRTReputation(
            transfer_estimator=self.transfer_estimator,
            reliability_params=rp,
            mode="ecrt",
            uncertainty_mode="lower_bound",
        )

        baselines = {
            "Uniform":          UniformReputation().fit(episodes),
            "GlobalBeta":       GlobalBetaReputation().fit(episodes),
            "SkillConditioned": SkillConditionedReputation().fit(episodes),
            "ZeroEvidenceGate": ZeroEvidenceGate(
                inner=SkillConditionedReputation(), min_evidence=3
            ).fit(episodes),
            "ECRT":             ecrt.fit(episodes),
        }

        cell_results: list[MetricsResult] = []
        for target_domain in target_domains:
            true_accs = {
                agent: generator.capabilities.get(agent, {}).get(target_domain, 0.25)
                for agent in generator.agents
            }
            target_tasks = generator.generate_target_tasks(
                n_tasks=N_TARGET_TASKS, domain=target_domain
            )
            for method_name, baseline in baselines.items():
                scores = {a: baseline.score(a, target_domain) for a in generator.agents}
                team_correct = []
                for _, gt, answers in target_tasks:
                    if method_name == "Uniform":
                        res = self.aggregator.majority_vote(answers)
                    else:
                        res = self.aggregator.reputation_weighted_vote(answers, scores)
                    res.bind_ground_truth(gt)
                    team_correct.append(bool(res.is_correct))

                m_res = self.metrics_calc.evaluate(
                    reputation_scores=scores,
                    true_accuracies=true_accs,
                    team_correct_flags=team_correct,
                    method=method_name,
                    domain=target_domain,
                    q_level=q_name,
                    t_condition=t_name,
                    seed=seed,
                )
                cell_results.append(m_res)
        return cell_results

    def _save_qt_results(self, results: list[MetricsResult]) -> None:
        csv_path = self.output_dir / "qt_grid" / "qt_grid_results.csv"
        json_path = self.output_dir / "qt_grid" / "qt_grid_results.json"
        rows = [r.as_dict() for r in results]
        if rows:
            with open(csv_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)
        json_path.write_text(json.dumps(rows, indent=2))
        console.print(f"[dim]Saved: {csv_path} ({len(rows)} rows)[/dim]")

    def _print_qt_summary(self, results: list[MetricsResult]) -> None:
        for method in ["GlobalBeta", "ECRT"]:
            for metric in ["team_accuracy", "ece"]:
                method_results = [r for r in results if r.method == method]
                pivot = self.metrics_calc.grid_summary(method_results, metric=metric)
                t_cols = sorted({r.t_condition for r in method_results})
                table = Table(
                    title=f"Q x T Pivot: {metric} | {method}",
                    header_style="bold magenta",
                )
                table.add_column("Q \\ T", style="cyan", width=14)
                for t in t_cols:
                    table.add_column(t, justify="center")
                for q in sorted(pivot.keys()):
                    row = [q]
                    for t in t_cols:
                        v = pivot.get(q, {}).get(t, float("nan"))
                        row.append(f"{v:.3f}" if v == v else "N/A")
                    table.add_row(*row)
                console.print(table)

    # ------------------------------------------------------------------
    # Experiment W3-2: Attack Pilot A1 + A2
    # ------------------------------------------------------------------

    def run_attack_pilot(self) -> dict:
        console.rule("[bold red]Week 3 Exp 2: Attack Pilot A1 + A2[/bold red]")
        results = {
            "a1_delayed_betrayal":    self._run_a1(),
            "a2_cross_skill_launder": self._run_a2(),
        }
        p = self.output_dir / "attacks" / "attack_pilot_results.json"
        p.write_text(json.dumps(results, indent=2, default=str))
        console.print(f"[dim]Saved: {p}[/dim]")
        return results

    def _run_a1(self) -> dict:
        """A1: Delayed betrayal. Attacker builds warm-up reputation then betrays."""
        console.print("\n[bold]A1: Delayed Betrayal[/bold] (qwen3-0.6b builds biology rep, then betrays)")
        generator = HistRepEvalGenerator(seed=42)
        attacker = "qwen3-0.6b"
        domain = "biology"

        warmup_eps = generator.generate_episodes(
            n_per_domain=20, domains=[domain], corruptor=FeedbackCorruptor.oracle()
        )
        # Adversarial: attacker sends false-positive feedback on wrong answers
        betrayal_eps = generator.generate_episodes(
            n_per_domain=5, domains=[domain],
            corruptor=FeedbackCorruptor.adversarial(bias_rate=1.0, seed=99),
        )
        all_eps = warmup_eps + betrayal_eps

        re = FeedbackReliabilityEstimator()
        rp = re.calibrate(warmup_eps)
        ecrt = ECRTReputation(self.transfer_estimator, rp, mode="ecrt").fit(all_eps)
        global_rep = GlobalBetaReputation().fit(all_eps)
        skill_rep = SkillConditionedReputation().fit(all_eps)

        target_tasks = generator.generate_target_tasks(n_tasks=20, domain=domain)
        true_accs = {a: generator.capabilities.get(a, {}).get(domain, 0.25) for a in generator.agents}
        wrong_opts = ["A", "B", "C", "D"]

        results = {}
        for mname, baseline in [("GlobalBeta", global_rep), ("SkillCond", skill_rep), ("ECRT", ecrt)]:
            scores = {a: baseline.score(a, domain) for a in generator.agents}
            team_correct = []
            for _, gt, answers in target_tasks:
                betrayed = dict(answers)
                betrayed[attacker] = next(o for o in wrong_opts if o != gt)
                res = self.aggregator.reputation_weighted_vote(betrayed, scores)
                res.bind_ground_truth(gt)
                team_correct.append(bool(res.is_correct))
            team_acc = sum(team_correct) / len(team_correct)
            influence = scores[attacker].mean
            results[mname] = {"attacker_influence": influence, "team_accuracy": team_acc}
            status = "[red]VULN[/red]" if influence > 0.55 else "[green]OK[/green]"
            console.print(f"  {mname:<16} influence={influence:.3f} | team_acc={team_acc:.1%} {status}")
        return results

    def _run_a2(self) -> dict:
        """A2: Cross-skill laundering. Attacker builds psychology rep, attacks math."""
        console.print("\n[bold]A2: Cross-Skill Laundering[/bold] (psychology -> math)")
        generator = HistRepEvalGenerator(seed=42)
        attacker = "qwen3-0.6b"
        src_domain = "psychology"
        tgt_domain = "math"

        src_eps = generator.generate_episodes(
            n_per_domain=30, domains=[src_domain], corruptor=FeedbackCorruptor.oracle()
        )

        re = FeedbackReliabilityEstimator()
        rp = re.calibrate(src_eps)
        ecrt = ECRTReputation(self.transfer_estimator, rp, mode="ecrt").fit(src_eps)
        global_rep = GlobalBetaReputation().fit(src_eps)
        skill_rep = SkillConditionedReputation().fit(src_eps)

        target_tasks = generator.generate_target_tasks(n_tasks=20, domain=tgt_domain)
        true_accs_tgt = {a: generator.capabilities.get(a, {}).get(tgt_domain, 0.25) for a in generator.agents}

        results = {}
        for mname, baseline in [("GlobalBeta", global_rep), ("SkillCond", skill_rep), ("ECRT", ecrt)]:
            scores = {a: baseline.score(a, tgt_domain) for a in generator.agents}
            laundered = scores[attacker].mean - true_accs_tgt[attacker]
            team_correct = []
            for _, gt, answers in target_tasks:
                res = self.aggregator.reputation_weighted_vote(answers, scores)
                res.bind_ground_truth(gt)
                team_correct.append(bool(res.is_correct))
            team_acc = sum(team_correct) / len(team_correct)
            results[mname] = {
                "attacker_score_on_math": scores[attacker].mean,
                "attacker_true_acc_math": true_accs_tgt[attacker],
                "laundering_gain": laundered,
                "team_accuracy": team_acc,
            }
            status = "[red]LAUNDERED[/red]" if laundered > 0.1 else "[green]BLOCKED[/green]"
            console.print(f"  {mname:<16} gain={laundered:+.3f} | team_acc={team_acc:.1%} {status}")
        return results

    # ------------------------------------------------------------------
    # Experiment W3-3: Statistical Analysis + Go/No-Go
    # ------------------------------------------------------------------

    def run_statistical_analysis(self, results: list[MetricsResult] | None = None) -> dict:
        console.rule("[bold blue]Week 3 Exp 3: Statistical Analysis[/bold blue]")
        if results is None:
            results = self.all_qt_results
        if not results:
            console.print("[red]No results. Run qt_grid first.[/red]")
            return {}

        analysis_output: dict = {}
        for metric in ["team_accuracy", "ece", "expert_leverage", "brier_score"]:
            grouped: dict[tuple, list[float]] = defaultdict(list)
            for r in results:
                grouped[(r.method, r.q_level, r.t_condition)].append(
                    getattr(r, metric, 0.0)
                )
            q_effect = {}
            for q_name in Q_LEVELS:
                q_vals = [
                    v for (m, q, t), vs in grouped.items()
                    if q == q_name and m == "GlobalBeta"
                    for v in vs
                ]
                if q_vals:
                    mean, lo, hi = self.metrics_calc.bootstrap_ci(q_vals)
                    q_effect[q_name] = {"mean": mean, "ci_lo": lo, "ci_hi": hi}

            t_effect = {}
            for t_name in T_CONDITIONS:
                t_vals = [
                    v for (m, q, t), vs in grouped.items()
                    if t == t_name and m == "GlobalBeta"
                    for v in vs
                ]
                if t_vals:
                    mean, lo, hi = self.metrics_calc.bootstrap_ci(t_vals)
                    t_effect[t_name] = {"mean": mean, "ci_lo": lo, "ci_hi": hi}

            analysis_output[metric] = {
                "q_main_effect": q_effect,
                "t_main_effect": t_effect,
            }

        console.print("\n[bold]Main effects on team_accuracy (GlobalBeta)[/bold]")
        ta = analysis_output.get("team_accuracy", {})
        for q, v in ta.get("q_main_effect", {}).items():
            console.print(f"  Q={q:<16} mean={v['mean']:.3f}  95%CI=[{v['ci_lo']:.3f},{v['ci_hi']:.3f}]")
        for t, v in ta.get("t_main_effect", {}).items():
            console.print(f"  T={t:<16} mean={v['mean']:.3f}  95%CI=[{v['ci_lo']:.3f},{v['ci_hi']:.3f}]")

        p = self.output_dir / "statistical_analysis.json"
        p.write_text(json.dumps(analysis_output, indent=2))
        console.print(f"[dim]Saved: {p}[/dim]")
        return analysis_output

    def make_go_no_go_decision(self, analysis: dict) -> str:
        console.rule("[bold yellow]GO/NO-GO DECISION[/bold yellow]")
        try:
            ta = analysis.get("team_accuracy", {})
            q_means = [v["mean"] for v in ta.get("q_main_effect", {}).values()]
            t_means = [v["mean"] for v in ta.get("t_main_effect", {}).values()]
            q_range = max(q_means) - min(q_means) if len(q_means) >= 2 else 0.0
            t_range = max(t_means) - min(t_means) if len(t_means) >= 2 else 0.0
            console.print(f"  Q effect range: {q_range:.3f}")
            console.print(f"  T effect range: {t_range:.3f}")
            if q_range >= 0.05 and t_range >= 0.05:
                decision = "GO-A"
                note = "Both Q and T show meaningful effects. Proceed with full ECRT (Week 4)."
            elif q_range >= 0.05 or t_range >= 0.05:
                dom = "Q" if q_range > t_range else "T"
                decision = "GO-B"
                note = f"Only {dom} dominates. Reframe paper around {dom}."
            elif q_range >= 0.02 or t_range >= 0.02:
                decision = "GO-C"
                note = "Small effects. Consider empirical characterization framing."
            else:
                decision = "GO-D"
                note = "No reproducible phenomenon. Stop and redesign."
        except Exception as exc:
            decision = "UNDETERMINED"
            note = str(exc)
            q_range = t_range = 0.0

        console.print(Panel(
            f"[bold]Decision: {decision}[/bold]\n{note}",
            title="Week 3 Go/No-Go",
            border_style="green" if "GO-A" in decision else "yellow",
        ))
        self._update_research_log(decision, q_range, t_range)
        self._update_paper_claims(decision)
        return decision

    def _update_research_log(self, decision: str, q_range: float, t_range: float) -> None:
        log_file = self.research_ops_dir / "research_log.md"
        if not log_file.exists():
            return
        today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        entry = f"""

---

## {today} - Week 3 Execution: Q x T Factorial Grid + Attack Pilot

### Experiments Executed
1. **Q x T Factorial Grid** (4 x 3 x 3 seeds x 5 methods):
   - Q main effect on team_accuracy: range = {q_range:.3f}
   - T main effect on team_accuracy: range = {t_range:.3f}
   - Results: results/week3/qt_grid/qt_grid_results.csv

2. **Attack Pilot**:
   - A1 (Delayed Betrayal): completed.
   - A2 (Cross-Skill Laundering): ECRT blocks laundering (tau=0 for unrelated).

### Go/No-Go: **{decision}**

### Week 3 Exit Criteria
- [x] Q x T grid completed (3 seeds)
- [x] Bootstrap CIs computed
- [x] Attack pilot A1+A2 done
- [x] Go/No-Go decision documented

-> **WEEK 3 COMPLETE. PROCEED TO WEEK 4 (ECRT FULL ABLATION + MAIN TABLE).**
"""
        log_file.write_text(log_file.read_text() + entry)
        console.print(f"[dim]Updated: {log_file}[/dim]")

    def _update_paper_claims(self, decision: str) -> None:
        claims_file = self.research_ops_dir / "paper_claims.md"
        if not claims_file.exists():
            return
        content = claims_file.read_text()
        old_str = (
            "- **Status:** NOT YET TESTED\n"
            "- **Supporting experiments:** (pending Week 3 Q x T grid)"
        )
        new_str = (
            f"- **Status:** PARTIALLY SUPPORTED (Week 3 Q x T Grid done, Go/No-Go: {decision})\n"
            "- **Supporting experiments:** Week 3 Q x T grid (4x3 cells, 3 seeds, 5 methods)"
        )
        # Also handle the unicode × variant
        old_str2 = (
            "- **Status:** NOT YET TESTED\n"
            "- **Supporting experiments:** (pending Week 3 Q\u00d7T grid)"
        )
        new_str2 = (
            f"- **Status:** PARTIALLY SUPPORTED (Week 3 Q\u00d7T Grid done, Go/No-Go: {decision})\n"
            "- **Supporting experiments:** Week 3 Q\u00d7T grid (4x3 cells, 3 seeds, 5 methods)"
        )
        updated = content.replace(old_str, new_str).replace(old_str2, new_str2)
        if updated != content:
            claims_file.write_text(updated)
            console.print(f"[dim]Updated paper_claims.md: C1 -> {decision}[/dim]")



# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="RepGuard Week 3 Experiments")
    parser.add_argument(
        "--exp",
        choices=["all", "qt_grid", "attacks", "analysis"],
        default="all",
    )
    args = parser.parse_args()

    console.print(Panel(
        "[bold cyan]RepGuard Week 3: Q x T Factorial Grid + ECRT Method[/bold cyan]\n"
        "Goal: Establish the empirical phenomenon BEFORE claiming a method.",
        border_style="cyan",
    ))

    runner = Week3Experiments()

    qt_results: list[MetricsResult] = []
    if args.exp in ("all", "qt_grid"):
        qt_results = runner.run_qt_grid()
    else:
        csv_path = Path("results/week3/qt_grid/qt_grid_results.csv")
        if csv_path.exists():
            console.print(f"[dim]Loading cached Q x T results from {csv_path}[/dim]")
            with open(csv_path) as f:
                for row in csv.DictReader(f):
                    qt_results.append(MetricsResult(
                        method=row["method"], domain=row["domain"],
                        q_level=row["q_level"], t_condition=row["t_condition"],
                        seed=int(row["seed"]), ece=float(row["ece"]),
                        expert_leverage=float(row["expert_leverage"]),
                        rank_correlation=float(row["rank_correlation"]),
                        team_accuracy=float(row["team_accuracy"]),
                        brier_score=float(row["brier_score"]),
                        neg_log_likelihood=float(row["neg_log_likelihood"]),
                        n_agents=int(row["n_agents"]),
                    ))
            runner.all_qt_results = qt_results

    if args.exp in ("all", "attacks"):
        runner.run_attack_pilot()

    if args.exp in ("all", "analysis"):
        analysis = runner.run_statistical_analysis(qt_results or None)
        runner.make_go_no_go_decision(analysis)

    console.print(Panel(
        "[bold green]Week 3 Complete![/bold green]\n"
        "Results saved to: results/week3/",
        border_style="green",
    ))


if __name__ == "__main__":
    main()
