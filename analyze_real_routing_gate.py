#!/usr/bin/env python3
"""Exploratory routing gate using already collected real model responses.

Train on Week 4's 420 train questions, evaluate once on disjoint Week 5 dev
questions. This is offline replay of actual direct/thinking outputs; the dev
results have already been inspected and are not a fresh confirmatory holdout.
"""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from repguard.data.mmlu_pro import load_mmlu_pro


TRAIN = Path("results/real_week4_thinking_pilot_v3/predictions.jsonl")
EVAL = Path("results/real_week5_validation_v1/predictions.jsonl")
OUTPUT = Path("results/real_next_study_v1/offline_routing_gate.json")
SUBJECTS = ("biology", "business", "chemistry", "computer science", "economics",
            "engineering", "health", "history", "law", "math", "other",
            "philosophy", "physics", "psychology")
FRACTIONS = (0.25, 0.5, 0.75)


def read_pairs(path: Path) -> dict[str, dict]:
    pairs: dict[str, dict] = {}
    for line in path.open():
        row = json.loads(line)
        pair = pairs.setdefault(row["task_id"], {})
        if row["variant"] in pair:
            raise RuntimeError(f"Duplicate {row['task_id']} {row['variant']}")
        pair[row["variant"]] = row
    if any(set(pair) != {"direct64", "thinking8192"} for pair in pairs.values()):
        raise RuntimeError("Incomplete paired ledger")
    return pairs


def features(task, direct: dict, *, after_direct: bool) -> list[float]:
    view = task.to_online_view()
    question = view.question
    options = view.options
    qlower = question.lower()
    values = [1.0,
              math.log1p(len(question)),
              math.log1p(sum(len(x) for x in options) / len(options)),
              len(options) / 10.0,
              float(bool(re.search(r"\d|[=+*/^]", question))),
              float("except" in qlower or "not " in qlower),
              float("following" in qlower),
              float("which" in qlower)]
    values.extend(float(view.metadata.subject == subject) for subject in SUBJECTS)
    if after_direct:
        answer = direct["answer"]
        values.extend([float(answer is None),
                       (ord(answer) - ord("A")) / max(len(options) - 1, 1) if answer else 0.0,
                       math.log1p(direct["latency_ms"] / 1000.0),
                       float(direct["output_tokens"] >= 64)])
    return values


def fit_ridge(x: np.ndarray, y: np.ndarray, penalty: float = 20.0) -> np.ndarray:
    regularizer = np.eye(x.shape[1]) * penalty
    regularizer[0, 0] = 0.0
    return np.linalg.solve(x.T @ x + regularizer, x.T @ y)


def evaluate(train: dict, dev: dict, tasks: dict, *, after_direct: bool,
             feature_mode: str = "full") -> dict:
    train_ids = sorted(train)
    dev_ids = sorted(dev)
    x_train = np.array([features(tasks[tid], train[tid]["direct64"],
                                 after_direct=after_direct) for tid in train_ids])
    x_dev = np.array([features(tasks[tid], dev[tid]["direct64"],
                               after_direct=after_direct) for tid in dev_ids])
    if feature_mode == "subject_only":
        columns = [0, *range(8, 22)]
        x_train = x_train[:, columns]
        x_dev = x_dev[:, columns]
    elif feature_mode == "question_only":
        x_train = x_train[:, :8]
        x_dev = x_dev[:, :8]
    elif feature_mode != "full":
        raise ValueError(f"Unknown feature mode: {feature_mode}")
    y = np.array([int(train[tid]["thinking8192"]["answer"] == tasks[tid].ground_truth_answer)
                  - int(train[tid]["direct64"]["answer"] == tasks[tid].ground_truth_answer)
                  for tid in train_ids], dtype=float)
    weights = fit_ridge(x_train, y)
    scores = x_dev @ weights
    order = sorted(range(len(dev_ids)), key=lambda i: (-scores[i], dev_ids[i]))
    results = {}
    for fraction in FRACTIONS:
        n_thinking = round(len(dev_ids) * fraction)
        escalate = {dev_ids[i] for i in order[:n_thinking]}
        correct = 0
        output_tokens = 0
        request_seconds = 0.0
        for tid in dev_ids:
            direct = dev[tid]["direct64"]
            thinking = dev[tid]["thinking8192"]
            chosen = thinking if tid in escalate else direct
            correct += int(chosen["answer"] == tasks[tid].ground_truth_answer)
            if after_direct:
                output_tokens += direct["output_tokens"]
                request_seconds += direct["latency_ms"] / 1000.0
                if tid in escalate:
                    output_tokens += thinking["output_tokens"]
                    request_seconds += thinking["latency_ms"] / 1000.0
            else:
                output_tokens += chosen["output_tokens"]
                request_seconds += chosen["latency_ms"] / 1000.0
        results[str(fraction)] = {"thinking_calls": n_thinking, "correct": correct,
                                  "accuracy": round(correct / len(dev_ids), 4),
                                  "output_tokens": output_tokens,
                                  "summed_request_seconds": round(request_seconds, 2),
                                  "random_escalation_expected_correct": round(
                                      sum(int(dev[tid]["direct64"]["answer"] == tasks[tid].ground_truth_answer)
                                          + fraction * (int(dev[tid]["thinking8192"]["answer"] == tasks[tid].ground_truth_answer)
                                                        - int(dev[tid]["direct64"]["answer"] == tasks[tid].ground_truth_answer))
                                          for tid in dev_ids), 2)}
    return {"feature_count": x_train.shape[1], "ridge_penalty": 20.0,
            "train_questions": len(train_ids), "dev_questions": len(dev_ids),
            "policies": results}


def main() -> None:
    train = read_pairs(TRAIN)
    dev = read_pairs(EVAL)
    if set(train) & set(dev):
        raise RuntimeError("Train/dev task ID overlap")
    tasks = {task.task_id: task for task in load_mmlu_pro(data_dir="data")}
    result = {
        "status": "exploratory_real_output_replay_not_confirmatory",
        "train_ledger": str(TRAIN), "eval_ledger": str(EVAL),
        "baseline_direct": {"correct": sum(dev[tid]["direct64"]["answer"] == tasks[tid].ground_truth_answer
                                          for tid in dev),
                            "output_tokens": sum(dev[tid]["direct64"]["output_tokens"] for tid in dev)},
        "baseline_thinking": {"correct": sum(dev[tid]["thinking8192"]["answer"] == tasks[tid].ground_truth_answer
                                            for tid in dev),
                              "output_tokens": sum(dev[tid]["thinking8192"]["output_tokens"] for tid in dev)},
        "preanswer_router": evaluate(train, dev, tasks, after_direct=False),
        "direct_first_router": evaluate(train, dev, tasks, after_direct=True),
        "subject_only_router": evaluate(train, dev, tasks, after_direct=False,
                                         feature_mode="subject_only"),
        "question_only_router": evaluate(train, dev, tasks, after_direct=False,
                                          feature_mode="question_only"),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
