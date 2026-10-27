#!/usr/bin/env python3
"""Reproduce ECRT/DART failure diagnostics from validated real ledgers.

This reads the already inspected Week 3 grid and 420-question development pool.
It does not generate answers or inspect the sealed holdout.
"""

from __future__ import annotations

import csv
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path

from analyze_real_week3 import (
    SEEDS,
    FeedbackReliabilityEstimator,
    corrupt,
    load_inputs,
    make_episodes,
)
from analyze_real_pool_gate import load_answers

WEEK3 = Path("results/real_week3_json_v1")
OUTPUT = Path("results/real_next_study_v1/failure_forensics.json")
REGIMES = ("oracle", "noisy_025", "noisy_050", "adversarial_040")


def grid_diagnostics() -> dict:
    cells: dict[tuple[str, ...], dict] = defaultdict(dict)
    with (WEEK3 / "analysis/qt_grid_results.csv").open(newline="") as handle:
        for row in csv.DictReader(handle):
            key = tuple(row[field] for field in ("target", "source", "t", "q", "seed"))
            cells[key][row["method"]] = row

    result = {}
    for regime in REGIMES:
        result[regime] = {}
        for relation in ("same", "related", "unrelated"):
            chosen = [methods for key, methods in cells.items()
                      if key[2] == relation and key[3] == regime]
            if not chosen or any(not {"ECRT", "FixedBorrow"} <= set(m) for m in chosen):
                raise RuntimeError(f"Incomplete grid: {regime}/{relation}")
            counts = Counter()
            for methods in chosen:
                ecrt, fixed = methods["ECRT"], methods["FixedBorrow"]
                e_scores = json.loads(ecrt["scores"])
                f_scores = json.loads(fixed["scores"])
                agents = sorted(e_scores)
                counts["same_means"] += all(abs(e_scores[a] - f_scores[a]) < 1e-6
                                             for a in agents)
                counts["same_ranking"] += sorted(agents, key=lambda a: e_scores[a]) == sorted(
                    agents, key=lambda a: f_scores[a])
                for a, b in itertools.combinations(agents, 2):
                    counts["agent_pairs"] += 1
                    counts["pair_inversions"] += (
                        (e_scores[a] - e_scores[b]) * (f_scores[a] - f_scores[b]) < 0)
                e_correct, f_correct = int(ecrt["n_correct"]), int(fixed["n_correct"])
                counts["ecrt_team_better"] += e_correct > f_correct
                counts["fixed_team_better"] += e_correct < f_correct
                counts["team_equal"] += e_correct == f_correct
            result[regime][relation] = {"cells": len(chosen), **dict(counts)}
    return result


def reliability_diagnostics() -> dict:
    manifest, tasks, predictions, missing = load_inputs(WEEK3)
    if missing:
        raise RuntimeError(f"Week 3 ledger missing {len(missing)} answers")
    result = {}
    for regime in REGIMES:
        sums = []
        for source in sorted(manifest["selected"]["train_calibration"]):
            raw = make_episodes(manifest["selected"]["dev"][source], source,
                                tasks, predictions)
            for seed in SEEDS:
                observed = corrupt(raw, regime, seed + 20_000)
                params = FeedbackReliabilityEstimator().calibrate(observed)
                sums.append(params.sensitivity + params.specificity)
        result[regime] = {"source_seed_calibrations": len(sums),
                          "negative_feedback_signal": sum(value < 1 for value in sums),
                          "signal_min": min(sums), "signal_max": max(sums)}
    return result


def pool_disagreement() -> dict:
    tasks, answers = load_answers()
    result: dict[str, Counter] = defaultdict(Counter)
    direct = ("qwen3_8b_direct", "gemma2:latest", "llama3:8b", "qwen3:14b")
    for task_id, rows in answers.items():
        think = rows["qwen3_8b_thinking"]
        votes = Counter(rows[model]["answer"] for model in direct)
        top = max(votes.values())
        winners = [answer for answer, n in votes.items() if n == top]
        if len(winners) != 1 or winners[0] == think["answer"]:
            continue
        key = f"{'valid' if think['valid_answer'] else 'invalid'}_direct_plurality_{top}"
        gold = tasks[task_id].ground_truth_answer
        result[key]["questions"] += 1
        result[key]["thinking_correct"] += think["answer"] == gold
        result[key]["direct_plurality_correct"] += winners[0] == gold
    return {key: dict(value) for key, value in sorted(result.items())}


def main() -> None:
    data = {"provenance": "real_ledgers_inspected_development_data_no_holdout",
            "grid": grid_diagnostics(), "reliability": reliability_diagnostics(),
            "pool_disagreement": pool_disagreement()}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
