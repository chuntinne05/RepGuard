#!/usr/bin/env python3
"""Exploratory cross-fitted decision gate on the real 420-question model pool.

Every proposed policy learns only from other folds. This is a development
diagnostic, not independent confirmation, because the 420-question pool and
its outcomes have already been inspected.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from repguard.data.mmlu_pro import load_mmlu_pro
from analyze_real_pool_overlap import analyze
from run_real_pool_overlap import MODELS, OUTPUT

SOURCE = Path("results/real_week4_thinking_pilot_v3/predictions.jsonl")
POLICIES = ("qwen3_8b_thinking", "qwen3_8b_direct", *MODELS)


def load_answers() -> tuple[dict, dict]:
    summary = analyze()
    if summary["completed_rows"] != 1260:
        raise RuntimeError("Cross-fitted gate requires all 1260 valid pool rows")
    task_map = {task.task_id: task for task in load_mmlu_pro(data_dir="data")}
    answers: dict[str, dict] = defaultdict(dict)
    for line in SOURCE.open():
        row = json.loads(line)
        if row["task_id"] in task_map:
            policy = {"direct64": "qwen3_8b_direct",
                      "thinking8192": "qwen3_8b_thinking"}.get(row["variant"])
            if policy:
                answers[row["task_id"]][policy] = row
    for line in (OUTPUT / "predictions.jsonl").open():
        row = json.loads(line)
        answers[row["task_id"]][row["model_id"]] = row
    selected = set().union(*[set(ids) for ids in
                             json.loads((OUTPUT / "manifest.json").read_text())["selected_train_ids"].values()])
    answers = {tid: answers[tid] for tid in selected}
    if len(answers) != 420 or any(set(rows) != set(POLICIES) for rows in answers.values()):
        raise RuntimeError("Missing source or pool answer")
    # Invalid/truncated source answers remain in the denominator and score wrong.
    # The new direct-model pool itself must be valid; analyze() enforces its raw output.
    if any(not rows[policy]["valid_answer"] for rows in answers.values() for policy in MODELS):
        raise RuntimeError("Invalid output in the new direct-model pool")
    return task_map, answers


def fold(tid: str) -> int:
    return int(hashlib.sha256(("repguard_pool_gate_5fold_v1|" + tid).encode()).hexdigest(), 16) % 5


def choose_best(train: list[str], answers: dict, task_map: dict,
                subject: str | None) -> str:
    subset = [tid for tid in train if subject is None or task_map[tid].metadata.subject == subject]
    if not subset:
        raise RuntimeError("Empty training subject")
    counts = {policy: sum(answers[tid][policy]["answer"] == task_map[tid].ground_truth_answer
                          for tid in subset) for policy in POLICIES}
    return max(POLICIES, key=lambda policy: (counts[policy], -POLICIES.index(policy)))


def paired_bootstrap(diff: list[int], subjects: list[str], seed: int = 20260930) -> list[float]:
    rng = np.random.default_rng(seed)
    groups = [[i for i, s in enumerate(subjects) if s == subject]
              for subject in sorted(set(subjects))]
    draws = []
    for _ in range(10000):
        indices = np.concatenate([rng.choice(group, len(group), replace=True) for group in groups])
        draws.append(sum(diff[i] for i in indices) / len(indices))
    return [round(float(x), 4) for x in np.quantile(draws, [0.025, 0.975])]


def run() -> dict:
    task_map, answers = load_answers()
    ids = sorted(answers)
    if set(POLICIES) != set(next(iter(answers.values()))):
        raise RuntimeError("Policy mismatch")
    eval_rows = []
    for tid in ids:
        train = [other for other in ids if fold(other) != fold(tid)]
        subject = task_map[tid].metadata.subject
        global_policy = choose_best(train, answers, task_map, None)
        subject_policy = choose_best(train, answers, task_map, subject)
        gold = task_map[tid].ground_truth_answer
        eval_rows.append({"task_id": tid, "subject": subject,
                          "gold": gold, "global": global_policy,
                          "subject_route": subject_policy,
                          "fold": fold(tid)})

    by_policy = {}
    for policy in (*POLICIES, "global", "subject_route"):
        chosen = [row[policy] if policy in {"global", "subject_route"} else policy
                  for row in eval_rows]
        correct = [int(answers[row["task_id"]][p]["answer"] == row["gold"])
                   for row, p in zip(eval_rows, chosen)]
        base = [int(answers[row["task_id"]]["qwen3_8b_thinking"]["answer"] == row["gold"])
                for row in eval_rows]
        delta = [a-b for a, b in zip(correct, base)]
        by_policy[policy] = {
            "correct": sum(correct), "accuracy": round(sum(correct)/len(ids), 4),
            "delta_vs_thinking_count": sum(delta),
            "delta_vs_thinking_95pct_subject_stratified_ci": paired_bootstrap(
                delta, [row["subject"] for row in eval_rows]),
            "output_tokens": sum(answers[row["task_id"]][p]["output_tokens"]
                                 for row, p in zip(eval_rows, chosen)),
            "summed_request_seconds": round(sum(answers[row["task_id"]][p]["latency_ms"]
                                                for row, p in zip(eval_rows, chosen))/1000, 2),
            "selection_counts": dict(Counter(chosen)),
        }

    base_only_wrong = [row for row in eval_rows
                       if answers[row["task_id"]]["qwen3_8b_thinking"]["answer"] != row["gold"]]
    rescue = {policy: sum(answers[row["task_id"]][policy]["answer"] == row["gold"]
                          for row in base_only_wrong) for policy in POLICIES
              if policy != "qwen3_8b_thinking"}
    any_rescue = sum(any(answers[row["task_id"]][policy]["answer"] == row["gold"]
                         for policy in POLICIES if policy != "qwen3_8b_thinking")
                     for row in base_only_wrong)
    result = {"status": "exploratory_crossfit_on_inspected_420_question_pool",
              "n_questions": 420, "folds": 5,
              "models": list(POLICIES), "policies": by_policy,
              "thinking_wrong": len(base_only_wrong),
              "rescue_by_policy": rescue, "any_other_rescue_oracle": any_rescue,
              "selected_policy_by_subject": {
                  subject: dict(Counter(row["subject_route"] for row in eval_rows
                                        if row["subject"] == subject))
                  for subject in sorted(set(row["subject"] for row in eval_rows))}}
    output = OUTPUT / "crossfit_gate.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
