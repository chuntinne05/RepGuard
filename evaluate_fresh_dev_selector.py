#!/usr/bin/env python3
"""Frozen Qwen14-vs-thinking selector evaluation on 560 fresh development IDs.

The ridge feature set, penalty and zero switch threshold were chosen on the
previously inspected 420-question pool. This file is written before inspecting
new development outcomes. It requires both complete real-output ledgers.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np

from analyze_contextual_selector import RIDGE_PENALTY, features, fitted_predictor
from analyze_real_dev_pool import load_validated
from analyze_real_pool_gate import load_answers

OUTPUT = Path("results/real_dev_pool_v1/selector_evaluation.json")


def stratified_ci(values: list[int], subjects: list[str], seed: int = 20260930):
    rng = np.random.default_rng(seed)
    groups = [[i for i, subject in enumerate(subjects) if subject == name]
              for name in sorted(set(subjects))]
    draws = []
    for _ in range(5000):
        chosen = np.concatenate([rng.choice(group, len(group), replace=True)
                                 for group in groups])
        draws.append(float(np.mean([values[i] for i in chosen])))
    return [round(float(v), 5) for v in np.quantile(draws, [0.025, 0.975])]


def run() -> dict:
    old_tasks, old_answers = load_answers()
    old_ids = sorted(old_answers)
    old_think = [old_answers[tid]["qwen3_8b_thinking"] for tid in old_ids]
    old_other = [old_answers[tid]["qwen3:14b"] for tid in old_ids]
    old_different = np.array([a["answer"] != b["answer"]
                              for a, b in zip(old_think, old_other)], dtype=bool)
    old_x = np.array([features(old_tasks[tid], row)
                      for tid, row in zip(old_ids, old_think)], dtype=float)
    old_y = np.array([
        int(b["answer"] == old_tasks[tid].ground_truth_answer)
        - int(a["answer"] == old_tasks[tid].ground_truth_answer)
        for tid, a, b in zip(old_ids, old_think, old_other)], dtype=float)

    manifest, tasks, rows = load_validated()
    ids = sorted({tid for name, tid in rows if name == "qwen3_8b_thinking"})
    if len(ids) != 560 or any(("qwen3_14b_direct", tid) not in rows for tid in ids):
        raise RuntimeError("Need all 560 thinking and Qwen14 direct development answers")
    think = [rows["qwen3_8b_thinking", tid] for tid in ids]
    other = [rows["qwen3_14b_direct", tid] for tid in ids]
    different = np.array([a["answer"] != b["answer"]
                          for a, b in zip(think, other)], dtype=bool)
    x = np.array([features(tasks[tid], row) for tid, row in zip(ids, think)], dtype=float)
    predictions = np.full(len(ids), np.nan)
    predictions[different] = fitted_predictor(old_x[old_different],
                                               old_y[old_different], x[different])
    subjects = [tasks[tid].metadata.subject for tid in ids]
    baseline = []
    fallback = []
    selector = []
    counts = Counter()
    for i, tid in enumerate(ids):
        gold = tasks[tid].ground_truth_answer
        invalid = not think[i]["valid_answer"]
        switch = bool(invalid or (different[i] and predictions[i] > 0))
        baseline.append(int(think[i]["answer"] == gold))
        fallback.append(int((other[i] if invalid else think[i])["answer"] == gold))
        selector.append(int((other[i] if switch else think[i])["answer"] == gold))
        counts["switches"] += switch
        counts["rescues"] += switch and other[i]["answer"] == gold and think[i]["answer"] != gold
        counts["harms"] += switch and other[i]["answer"] != gold and think[i]["answer"] == gold
        counts["thinking_invalid"] += invalid
    result = {
        "status": "fresh_development_not_sealed_holdout",
        "training_source": "inspected 420-question pool, fixed ridge penalty and zero threshold",
        "new_protocol_hash": manifest["protocol_hash"],
        "ridge_penalty": RIDGE_PENALTY,
        "n": len(ids),
        "thinking_correct": sum(baseline),
        "invalid_fallback_correct": sum(fallback),
        "selector_correct": sum(selector),
        "selector_minus_thinking_ci": stratified_ci(
            [a - b for a, b in zip(selector, baseline)], subjects),
        "selector_minus_fallback_ci": stratified_ci(
            [a - b for a, b in zip(selector, fallback)], subjects),
        **dict(counts),
        "qwen14_all_calls_output_tokens": sum(row["output_tokens"] for row in other),
        "qwen14_all_calls_summed_request_seconds": round(
            sum(row["latency_ms"] for row in other) / 1000, 2),
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
