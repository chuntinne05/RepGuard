#!/usr/bin/env python3
"""Exploratory Week 5 impact of real Modal judge feedback on Week 3 routing.

The 280 history questions are split in two folds per subject. One half
calibrates judge reliability; the disjoint half supplies reputation evidence.
Both folds are evaluated on the already explored Week 3 test predictions, so
this is diagnostic and must not be reported as independent confirmation.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from analyze_real_week3 import (
    AGENTS, FixedBorrow, StudyTransferEstimator, clean_json,
    cluster_bootstrap, eval_cell, load_inputs, mean,
)
from repguard.reputation.baselines import UniformReputation
from repguard.reputation.ecrt import ECRTReputation, FeedbackReliabilityEstimator
from repguard.reputation.episode import EpisodeRecord


def load_judgments(output: Path) -> tuple[dict, dict[tuple[str, str], dict]]:
    manifest = json.loads((output / "manifest.json").read_text())
    cases = {(case["task_id"], case["candidate_answer"]): case
             for case in manifest["candidate_cases"]}
    rows = [json.loads(line) for line in (output / "judgments.jsonl").read_text().splitlines()
            if line.strip()]
    judged = {}
    for row in rows:
        key = (row["task_id"], row["candidate_answer"])
        if (key not in cases or key in judged or
            row["protocol_hash"] != manifest["protocol_hash"] or
            row["model_digest"] != manifest["judge_model_digest"] or
            row["agents"] != cases[key]["agents"] or
            row["prompt_hash"] != cases[key]["prompt_hash"] or
            not row["valid_judgment"]):
            raise RuntimeError(f"Invalid, duplicate or mismatched judgment: {key}")
        judged[key] = row
    if set(judged) != set(cases):
        raise RuntimeError(f"Judge ledger incomplete: {len(judged)}/{len(cases)}")
    return manifest, judged


def episodes_for(ids: list[str], subject: str, tasks, predictions,
                 judgments: dict[tuple[str, str], dict]) -> list[EpisodeRecord]:
    episodes = []
    for task_id in ids:
        task = tasks[task_id]
        for agent in AGENTS:
            answer = predictions[(agent, task_id)]["answer"]
            row = judgments[(task_id, answer)]
            if agent not in row["agents"] or row["subject"] != subject:
                raise RuntimeError("Judge case does not match historical agent answer")
            episodes.append(EpisodeRecord(
                episode_id=f"{agent}:{task_id}", agent_id=agent,
                task_id=task_id, domain=subject, agent_answer=answer,
                _ground_truth=task.ground_truth_answer,
                observed_feedback=float(row["verdict"]),
                feedback_regime="modal_qwen3_14b_judge_v1",
            ))
    return episodes


def oracle_feedback(episodes: list[EpisodeRecord]) -> list[EpisodeRecord]:
    return [ep.with_corrupted_feedback(float(ep.oracle_correct()))
            for ep in episodes]


def write_cells(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows: list[dict]) -> dict:
    metrics = ("team_accuracy", "brier_binary", "competence_mae")
    grouped = defaultdict(list)
    for row in rows:
        for metric in metrics:
            grouped[(row["target"], row["t"], row["method"], metric)].append(row[metric])
    per_target = {key: mean(values) for key, values in grouped.items()}
    targets = sorted({row["target"] for row in rows})
    methods = sorted({row["method"] for row in rows})
    conditions = sorted({row["t"] for row in rows})
    summary = {"design": {
        "status": "exploratory_reused_week3_test_not_independent_validation",
        "inference_unit": "target subject",
        "folds": 2,
        "history_questions_per_source_per_fold": 10,
        "calibration_questions_per_source_per_fold": 10,
        "related_sources_and_folds": "averaged within target",
    }, "cells": {}, "paired_differences": {}}
    for condition in conditions:
        summary["cells"][condition] = {}
        summary["paired_differences"][condition] = {}
        for metric in metrics:
            summary["cells"][condition][metric] = {}
            summary["paired_differences"][condition][metric] = {}
            for method in methods:
                values = {target: per_target[(target, condition, method, metric)]
                          for target in targets
                          if (target, condition, method, metric) in per_target}
                summary["cells"][condition][metric][method] = cluster_bootstrap(values)
            for a, b in (("ECRT", "FixedBorrow"),
                         ("ECRT", "Uniform"),
                         ("ECRT", "OracleFixedBorrow")):
                values = {
                    target: per_target[(target, condition, a, metric)] -
                            per_target[(target, condition, b, metric)]
                    for target in targets
                    if (target, condition, a, metric) in per_target and
                       (target, condition, b, metric) in per_target
                }
                summary["paired_differences"][condition][metric][f"{a}_minus_{b}"] = (
                    cluster_bootstrap(values))
    return summary


def run(week3: Path, judge: Path, output: Path) -> dict:
    week3_manifest, tasks, predictions, missing = load_inputs(week3)
    if missing:
        raise RuntimeError(f"Week 3 prediction ledger incomplete: {len(missing)}")
    judge_manifest, judgments = load_judgments(judge)
    selected = judge_manifest["selected_history_ids"]
    if (judge_manifest["dataset_task_id_sha256"] !=
        week3_manifest["dataset_task_id_sha256"]):
        raise RuntimeError("Week 3 and judge datasets differ")
    for subject, ids in selected.items():
        if len(ids) != 20 or not set(ids).issubset(
            week3_manifest["selected"]["train_calibration"][subject]):
            raise RuntimeError("Judge history selection differs from Week 3")

    transfer = StudyTransferEstimator()
    rows = []
    fold_reliability = []
    for fold in (0, 1):
        calibration = []
        for subject, ids in sorted(selected.items()):
            cal_ids = ids[:10] if fold == 0 else ids[10:]
            calibration.extend(episodes_for(cal_ids, subject, tasks,
                                            predictions, judgments))
        reliability = FeedbackReliabilityEstimator().calibrate(calibration)
        fold_reliability.append({"fold": fold, "n_episodes": len(calibration),
                                 "sensitivity": reliability.sensitivity,
                                 "specificity": reliability.specificity,
                                 "p_correct_prior": reliability.p_correct_prior})
        for source, ids in sorted(selected.items()):
            hist_ids = ids[10:] if fold == 0 else ids[:10]
            history = episodes_for(hist_ids, source, tasks, predictions, judgments)
            methods = {
                "Uniform": UniformReputation().fit(history),
                "FixedBorrow": FixedBorrow(history, transfer),
                "ECRT": ECRTReputation(transfer, reliability, mode="ecrt").fit(history),
                "OracleFixedBorrow": FixedBorrow(oracle_feedback(history), transfer),
            }
            for target in sorted(week3_manifest["selected"]["test"]):
                condition = transfer.estimate(source, target).condition.value
                if condition not in ("same", "related"):
                    continue
                target_ids = week3_manifest["selected"]["test"][target]
                evaluated = eval_cell(target_ids, target, tasks, predictions,
                                      methods, "real_modal_judge", condition,
                                      source, fold)
                rows.extend(evaluated)
    output.mkdir(parents=True, exist_ok=True)
    write_cells(output / "cells.csv", rows)
    result = summarize(rows)
    result["provenance"] = {
        "judge_protocol_hash": judge_manifest["protocol_hash"],
        "judge_model_digest": judge_manifest["judge_model_digest"],
        "week3_manifest": str(week3 / "manifest.json"),
        "test_set": "Week 3 test including its earlier viewed extension",
        "n_cell_rows": len(rows),
        "reliability_by_fold": fold_reliability,
    }
    (output / "analysis.json").write_text(json.dumps(clean_json(result), indent=2) + "\n")
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--week3", type=Path, default=Path("results/real_week3_json_v1"))
    p.add_argument("--judge", type=Path, default=Path("results/real_week5_modal_judge_v1"))
    p.add_argument("--output", type=Path, default=Path("results/real_week5_feedback_impact_v1"))
    args = p.parse_args()
    result = run(args.week3, args.judge, args.output)
    print(json.dumps({"design": result["design"],
                      "provenance": result["provenance"],
                      "paired_differences": result["paired_differences"]},
                     indent=2))


if __name__ == "__main__":
    main()
