#!/usr/bin/env python3
"""Exploratory out-of-fold Qwen14-vs-thinking answer selector on real outputs.

The 420 development-pool outcomes were already inspected. This diagnoses
whether a small, fixed feature set contains usable question-level rescue signal;
it is not a confirmatory DART evaluation. Both solver outputs are assumed to be
available, and their full call costs must be counted for the selector policy.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

import numpy as np

from analyze_real_pool_gate import fold, load_answers

OUTPUT = Path("results/real_pool_overlap_v1/contextual_selector.json")
RIDGE_PENALTY = 10.0


def features(task, thinking_row) -> list[float]:
    question = task.question
    options = task.options
    subject = task.metadata.subject
    numeric = [math.log1p(len(question)),
               math.log1p(sum(len(option) for option in options) / len(options)),
               math.log1p(thinking_row["output_tokens"]),
               float(any(character.isdigit() for character in question))]
    subjects = ("biology", "business", "chemistry", "computer science",
                "economics", "engineering", "health", "history", "law", "math",
                "other", "philosophy", "physics", "psychology")
    return numeric + [float(subject == name) for name in subjects]


def fitted_predictor(train_x: np.ndarray, train_y: np.ndarray,
                     test_x: np.ndarray) -> np.ndarray:
    # Scale only continuous features, using out-of-fold training rows.
    center = train_x[:, :3].mean(axis=0)
    scale = train_x[:, :3].std(axis=0)
    scale[scale == 0] = 1.0
    a = train_x.copy()
    b = test_x.copy()
    a[:, :3] = (a[:, :3] - center) / scale
    b[:, :3] = (b[:, :3] - center) / scale
    a = np.column_stack((np.ones(len(a)), a))
    b = np.column_stack((np.ones(len(b)), b))
    penalty = np.eye(a.shape[1]) * RIDGE_PENALTY
    penalty[0, 0] = 0.0
    coef = np.linalg.solve(a.T @ a + penalty, a.T @ train_y)
    return b @ coef


def main() -> None:
    tasks, answers = load_answers()
    ids = sorted(answers)
    if len(ids) != 420:
        raise RuntimeError("Expected exactly 420 inspected development questions")
    x = np.array([features(tasks[tid], answers[tid]["qwen3_8b_thinking"])
                  for tid in ids], dtype=float)
    think = [answers[tid]["qwen3_8b_thinking"] for tid in ids]
    other = [answers[tid]["qwen3:14b"] for tid in ids]
    gold = [tasks[tid].ground_truth_answer for tid in ids]
    delta = np.array([int(b["answer"] == y) - int(a["answer"] == y)
                      for a, b, y in zip(think, other, gold)], dtype=float)
    different = np.array([a["answer"] != b["answer"]
                          for a, b in zip(think, other)], dtype=bool)
    predictions = np.full(len(ids), np.nan)
    for held_out in range(5):
        train = np.array([fold(tid) != held_out for tid in ids]) & different
        test = np.array([fold(tid) == held_out for tid in ids]) & different
        if train.sum() < 30:
            raise RuntimeError("Insufficient out-of-fold disagreement training rows")
        predictions[test] = fitted_predictor(x[train], delta[train], x[test])

    counts = Counter()
    by_subject: dict[str, Counter] = {}
    for i, tid in enumerate(ids):
        subject = tasks[tid].metadata.subject
        local = by_subject.setdefault(subject, Counter())
        invalid = not think[i]["valid_answer"]
        switch = bool(invalid or (different[i] and predictions[i] > 0))
        fallback_switch = invalid
        selected = other[i] if switch else think[i]
        fallback = other[i] if fallback_switch else think[i]
        for bucket in (counts, local):
            bucket["questions"] += 1
            bucket["thinking_correct"] += think[i]["answer"] == gold[i]
            bucket["invalid_fallback_correct"] += fallback["answer"] == gold[i]
            bucket["selector_correct"] += selected["answer"] == gold[i]
            bucket["switches"] += switch
            bucket["rescues"] += switch and other[i]["answer"] == gold[i] and think[i]["answer"] != gold[i]
            bucket["harms"] += switch and other[i]["answer"] != gold[i] and think[i]["answer"] == gold[i]
    report = {
        "status": "exploratory_crossfit_on_inspected_420_question_pool",
        "training": "5 folds; disagreement labels from other folds only; ridge penalty fixed at 10",
        "feature_stage": "after Qwen3 8B thinking and Qwen3 14B direct outputs, before gold",
        "features": "subject, log question length, log mean option length, log thinking output tokens, digit flag",
        "additional_cost": "Qwen3 14B direct must run on all 420 questions for this selector",
        "overall": dict(counts),
        "by_subject": {name: dict(value) for name, value in sorted(by_subject.items())},
        "qwen14_output_tokens": sum(row["output_tokens"] for row in other),
        "qwen14_summed_request_seconds": round(sum(row["latency_ms"] for row in other) / 1000, 2),
        "n_disagreements": int(different.sum()),
        "n_positive_out_of_fold_prediction": int(np.sum(predictions[different] > 0)),
    }
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("overall", "n_disagreements",
                                                "n_positive_out_of_fold_prediction",
                                                "qwen14_output_tokens",
                                                "qwen14_summed_request_seconds")}, indent=2))


if __name__ == "__main__":
    main()
