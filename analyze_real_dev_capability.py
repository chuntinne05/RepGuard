#!/usr/bin/env python3
"""Paired capability and cost audit on the complete 560-question development pool."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from analyze_real_dev_pool import load_validated
from evaluate_fresh_dev_selector import stratified_ci

OUTPUT = Path("results/real_dev_pool_v1/capability_analysis.json")
VARIANTS = ("qwen3_8b_direct", "qwen3_14b_direct", "gemma2_direct",
            "qwen3_06b_direct", "qwen3_8b_thinking")


def run() -> dict:
    manifest, tasks, rows = load_validated()
    ids = sorted({task_id for variant, task_id in rows
                  if variant == "qwen3_8b_thinking"})
    if len(ids) != 560 or any((variant, task_id) not in rows
                               for variant in VARIANTS for task_id in ids):
        raise RuntimeError("Need all 2,800 verified paired development responses")
    subjects = [tasks[task_id].metadata.subject for task_id in ids]
    correct: dict[str, list[int]] = {}
    per_subject = defaultdict(dict)
    for variant in VARIANTS:
        correct[variant] = [int(rows[variant, task_id]["answer"] ==
                                tasks[task_id].ground_truth_answer)
                            for task_id in ids]
        for subject in sorted(set(subjects)):
            indices = [i for i, name in enumerate(subjects) if name == subject]
            per_subject[subject][variant] = sum(correct[variant][i] for i in indices)
    direct = correct["qwen3_8b_direct"]
    thinking = correct["qwen3_8b_thinking"]
    discordant = {
        "thinking_only_correct": sum(t and not d for t, d in zip(thinking, direct)),
        "direct_only_correct": sum(d and not t for t, d in zip(thinking, direct)),
        "both_correct": sum(t and d for t, d in zip(thinking, direct)),
        "both_wrong": sum(not t and not d for t, d in zip(thinking, direct)),
    }
    costs = {}
    for variant in VARIANTS:
        costs[variant] = {
            "output_tokens": sum(rows[variant, task_id]["output_tokens"] for task_id in ids),
            "summed_request_seconds": round(sum(
                rows[variant, task_id]["latency_ms"] for task_id in ids) / 1000, 2),
            "invalid": sum(not rows[variant, task_id]["valid_answer"] for task_id in ids),
        }
    report = {
        "status": "fresh_development_not_sealed_holdout",
        "protocol_hash": manifest["protocol_hash"],
        "n": len(ids),
        "subjects": len(set(subjects)),
        "correct": {variant: sum(values) for variant, values in correct.items()},
        "per_subject_correct": dict(per_subject),
        "thinking_vs_direct_qwen8": {
            "difference": round((sum(thinking) - sum(direct)) / len(ids), 5),
            "stratified_question_bootstrap_ci": stratified_ci(
                [t - d for t, d in zip(thinking, direct)], subjects),
            **discordant,
        },
        "costs": costs,
        "cost_note": "Summed request time and output tokens are measured, not GPU/USD cost; "
                     "the compared policies use different output-token caps.",
    }
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
