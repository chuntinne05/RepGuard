#!/usr/bin/env python3
"""Gold-blind at decision time, selective Qwen14 fallback on fresh dev IDs.

The ridge model is trained once on the inspected 420-question pool. Features
are observable after Qwen8 thinking and before any Qwen14 call. A positive
estimated Qwen14-minus-thinking correctness delta triggers Qwen14; invalid
thinking always triggers it. No fresh development labels tune this policy.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np

from analyze_contextual_selector import RIDGE_PENALTY, features, fitted_predictor
from analyze_real_dev_pool import load_validated
from analyze_real_pool_gate import fold, load_answers
from evaluate_fresh_dev_selector import stratified_ci

OUTPUT = Path("results/real_dev_pool_v1/selective_router_evaluation.json")
OLD_OUTPUT = Path("results/real_pool_overlap_v1/selective_router_crossfit.json")
THRESHOLD = 0.0


def decisions(train_x: np.ndarray, train_y: np.ndarray,
              test_x: np.ndarray, invalid: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    estimated_delta = fitted_predictor(train_x, train_y, test_x)
    return np.logical_or(invalid, estimated_delta > THRESHOLD), estimated_delta


def old_crossfit() -> dict:
    tasks, answers = load_answers()
    ids = sorted(answers)
    if len(ids) != 420:
        raise RuntimeError("Expected the 420 inspected old-pool questions")
    think = [answers[tid]["qwen3_8b_thinking"] for tid in ids]
    other = [answers[tid]["qwen3:14b"] for tid in ids]
    x = np.array([features(tasks[tid], row) for tid, row in zip(ids, think)], dtype=float)
    y = np.array([int(b["answer"] == tasks[tid].ground_truth_answer)
                  - int(a["answer"] == tasks[tid].ground_truth_answer)
                  for tid, a, b in zip(ids, think, other)], dtype=float)
    invalid = np.array([not row["valid_answer"] for row in think], dtype=bool)
    route = np.zeros(len(ids), dtype=bool)
    scores = np.zeros(len(ids))
    for held in range(5):
        train = np.array([fold(tid) != held for tid in ids])
        test = ~train
        route[test], scores[test] = decisions(x[train], y[train], x[test], invalid[test])
    gold = [tasks[tid].ground_truth_answer for tid in ids]
    thinking_correct = sum(a["answer"] == answer for a, answer in zip(think, gold))
    fallback_correct = sum((b if bad else a)["answer"] == answer
                           for a, b, bad, answer in zip(think, other, invalid, gold))
    router_correct = sum((b if chosen else a)["answer"] == answer
                         for a, b, chosen, answer in zip(think, other, route, gold))
    report = {"status": "exploratory_5fold_on_inspected_pool", "n": len(ids),
              "ridge_penalty": RIDGE_PENALTY, "threshold": THRESHOLD,
              "feature_stage": "after Qwen8 thinking, before Qwen14 call",
              "thinking_correct": thinking_correct, "invalid_fallback_correct": fallback_correct,
              "router_correct": router_correct, "qwen14_calls": int(route.sum()),
              "rescues": int(sum(chosen and b["answer"] == answer and a["answer"] != answer
                                 for a, b, chosen, answer in zip(think, other, route, gold))),
              "harms": int(sum(chosen and b["answer"] != answer and a["answer"] == answer
                               for a, b, chosen, answer in zip(think, other, route, gold))),
              "qwen14_called_output_tokens": sum(b["output_tokens"] for b, chosen in zip(other, route)
                                                 if chosen),
              "qwen14_called_request_seconds": round(sum(b["latency_ms"] for b, chosen
                                                          in zip(other, route) if chosen) / 1000, 2),
              "qwen14_all_output_tokens": sum(b["output_tokens"] for b in other),
              "qwen14_all_request_seconds": round(sum(b["latency_ms"] for b in other) / 1000, 2)}
    OLD_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OLD_OUTPUT.write_text(json.dumps(report, indent=2) + "\n")
    return report


def run() -> dict:
    old_tasks, old_answers = load_answers()
    old_ids = sorted(old_answers)
    if len(old_ids) != 420:
        raise RuntimeError("Need the full inspected 420-question training pool")
    old_think = [old_answers[tid]["qwen3_8b_thinking"] for tid in old_ids]
    old_other = [old_answers[tid]["qwen3:14b"] for tid in old_ids]
    old_x = np.array([features(old_tasks[tid], row) for tid, row in zip(old_ids, old_think)],
                     dtype=float)
    old_y = np.array([int(b["answer"] == old_tasks[tid].ground_truth_answer)
                      - int(a["answer"] == old_tasks[tid].ground_truth_answer)
                      for tid, a, b in zip(old_ids, old_think, old_other)], dtype=float)

    manifest, tasks, rows = load_validated()
    ids = sorted({tid for name, tid in rows if name == "qwen3_8b_thinking"})
    if len(ids) != 560 or any(("qwen3_14b_direct", tid) not in rows for tid in ids):
        raise RuntimeError("Need all 560 paired new thinking and Qwen14 answers")
    think = [rows["qwen3_8b_thinking", tid] for tid in ids]
    other = [rows["qwen3_14b_direct", tid] for tid in ids]
    x = np.array([features(tasks[tid], row) for tid, row in zip(ids, think)], dtype=float)
    invalid = np.array([not row["valid_answer"] for row in think], dtype=bool)
    route, scores = decisions(old_x, old_y, x, invalid)
    gold = [tasks[tid].ground_truth_answer for tid in ids]
    subjects = [tasks[tid].metadata.subject for tid in ids]
    think_ok = [int(a["answer"] == answer) for a, answer in zip(think, gold)]
    fallback_ok = [int((b if bad else a)["answer"] == answer)
                   for a, b, bad, answer in zip(think, other, invalid, gold)]
    router_ok = [int((b if chosen else a)["answer"] == answer)
                 for a, b, chosen, answer in zip(think, other, route, gold)]
    q14_ok = [int(b["answer"] == answer) for b, answer in zip(other, gold)]
    counts = Counter()
    for a, b, chosen, answer in zip(think, other, route, gold):
        counts["rescues"] += bool(chosen and b["answer"] == answer and a["answer"] != answer)
        counts["harms"] += bool(chosen and b["answer"] != answer and a["answer"] == answer)
    result = {
        "status": "fresh_development_not_sealed_holdout",
        "training_source": "inspected old 420 only; all rows including agreement",
        "feature_stage": "after Qwen8 thinking, before Qwen14 call",
        "new_protocol_hash": manifest["protocol_hash"],
        "ridge_penalty": RIDGE_PENALTY, "threshold": THRESHOLD,
        "n": len(ids), "thinking_correct": sum(think_ok),
        "invalid_fallback_correct": sum(fallback_ok), "qwen14_always_correct": sum(q14_ok),
        "router_correct": sum(router_ok), "qwen14_calls": int(route.sum()),
        "thinking_invalid": int(invalid.sum()),
        "rescues": counts["rescues"], "harms": counts["harms"],
        "router_minus_fallback_ci": stratified_ci(
            [a - b for a, b in zip(router_ok, fallback_ok)], subjects),
        "router_minus_thinking_ci": stratified_ci(
            [a - b for a, b in zip(router_ok, think_ok)], subjects),
        "router_minus_qwen14_ci": stratified_ci(
            [a - b for a, b in zip(router_ok, q14_ok)], subjects),
        "qwen14_called_output_tokens": sum(b["output_tokens"] for b, chosen in zip(other, route)
                                             if chosen),
        "qwen14_called_request_seconds": round(sum(b["latency_ms"] for b, chosen
                                                      in zip(other, route) if chosen) / 1000, 2),
        "qwen14_all_output_tokens": sum(b["output_tokens"] for b in other),
        "qwen14_all_request_seconds": round(sum(b["latency_ms"] for b in other) / 1000, 2),
        "mean_predicted_delta": round(float(np.mean(scores)), 6),
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--old-crossfit-only", action="store_true")
    args = parser.parse_args()
    print(json.dumps(old_crossfit() if args.old_crossfit_only else run(), indent=2))
