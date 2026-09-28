"""Convenience entrypoint for RepGuard Week 2 Experiments (HistRepEval v0.1).

Runs all Week 2 experimental scenarios:
    1. Baseline Comparison (Uniform, GlobalBeta, SkillConditioned, ZeroEvidenceGate, Oracle)
    2. Feedback Quality (Q) Degradation Sweep
    3. Controlled Task-Mismatch Failure Demonstration

Usage:
    python run_week2.py
    python run_week2.py --seed 42 --output results/week2_reputation
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure src/ is on sys.path
_SRC_DIR = Path(__file__).resolve().parent / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from repguard.reputation.experiment import Week2Experiments


def main() -> None:
    parser = argparse.ArgumentParser(
        description="RepGuard Week 2 — Baseline Reputation & HistRepEval v0.1 Experiments",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible history generation (default: 42)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/week2_reputation",
        help="Directory to save Week 2 results (default: results/week2_reputation)",
    )
    parser.add_argument(
        "--research-ops",
        type=str,
        default="research_ops",
        help="Path to research_ops directory (default: research_ops)",
    )
    parser.add_argument(
        "--n-episodes",
        type=int,
        default=25,
        help="Number of historical episodes per domain per agent (default: 25)",
    )

    args = parser.parse_args()

    runner = Week2Experiments(
        seed=args.seed,
        output_dir=args.output,
        research_ops_dir=args.research_ops,
    )

    # 1. Mandatory Baselines Comparison
    exp1_res = runner.run_baselines_comparison(
        n_episodes_per_domain=args.n_episodes,
        n_target_tasks_per_domain=25,
    )

    # 2. Feedback Quality Sweep
    exp2_res = runner.run_feedback_corruption_sweep(
        domain="biology",
        n_episodes=30,
        n_target_tasks=30,
    )

    # 3. Controlled Task-Mismatch Failure Demonstration
    exp3_res = runner.run_task_mismatch_failure_demo(
        source_domain="biology",
        target_domain="math",
        n_source_episodes=35,
        n_target_tasks=50,
    )

    # Save results and update research ops
    runner.save_and_log(exp1_res, exp2_res, exp3_res)


if __name__ == "__main__":
    main()
