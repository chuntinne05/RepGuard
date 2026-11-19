#!/usr/bin/env python3
"""Paired 4K-versus-8K context diagnostic on 70 frozen development IDs."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np

from analyze_real_dev_pool import load_validated
from run_real_dev_context_pilot import OUTPUT, SELECTION


def cluster_ci(deltas: list[int], subjects: list[str], seed: int = 20260930) -> list[float]:
    rng = np.random.default_rng(seed)
    names = sorted(set(subjects))
    by_subject = {name: [value for value, subject in zip(deltas, subjects)
                         if subject == name] for name in names}
    draws = []
    for _ in range(5000):
        chosen = rng.choice(names, len(names), replace=True)
        draws.append(float(np.mean([value for name in chosen for value in by_subject[name]])))
    return [round(float(value), 5) for value in np.quantile(draws, [0.025, 0.975])]


def run() -> dict:
    selection = json.loads(SELECTION.read_text())
    pilot_manifest = json.loads((OUTPUT / "manifest.json").read_text())
    if pilot_manifest["selection_protocol_hash"] != selection["protocol_hash"]:
        raise RuntimeError("Context pilot manifest does not match frozen selection")
    ids = {task_id for group in selection["selected_development_ids"].values()
           for task_id in group}
    pilot: dict[str, dict] = {}
    for line in (OUTPUT / "predictions.jsonl").open():
        row = json.loads(line)
        task_id = row["task_id"]
        if (row["protocol_hash"] != pilot_manifest["protocol_hash"] or
            row["model_digest"] != pilot_manifest["model_digest"] or
            row["num_ctx"] != 8192 or task_id not in ids or task_id in pilot):
            raise RuntimeError("Invalid context pilot ledger row")
        pilot[task_id] = row
    if len(pilot) != 70:
        raise RuntimeError(f"Need all 70 context pilot rows, got {len(pilot)}")
    main_manifest, tasks, main = load_validated()
    if len([1 for variant, _ in main if variant == "qwen3_8b_thinking"]) != 560:
        raise RuntimeError("Need complete main 560-question thinking run")
    if pilot_manifest["model_digest"] != main_manifest["model_digests"]["qwen3:8b"]:
        raise RuntimeError("Model digest differs between context runs")
    subjects = []
    delta_correct = []
    delta_valid = []
    counts = Counter()
    output_tokens = Counter()
    request_ms = Counter()
    for task_id in sorted(ids):
        old = main["qwen3_8b_thinking", task_id]
        new = pilot[task_id]
        if old["prompt_hash"] != new["prompt_hash"]:
            raise RuntimeError(f"Prompt changed for {task_id}")
        if old["max_tokens"] != new["max_tokens"] or new["max_tokens"] != 8192:
            raise RuntimeError("Max output token cap differs")
        if old["subject"] != new["subject"]:
            raise RuntimeError("Subject mismatch")
        gold = tasks[task_id].ground_truth_answer
        old_ok = int(old["answer"] == gold)
        new_ok = int(new["answer"] == gold)
        subjects.append(old["subject"])
        delta_correct.append(new_ok - old_ok)
        delta_valid.append(int(new["valid_answer"]) - int(old["valid_answer"]))
        counts["old_correct"] += old_ok
        counts["new_correct"] += new_ok
        counts["old_valid"] += old["valid_answer"]
        counts["new_valid"] += new["valid_answer"]
        counts["old_length_cap"] += old["done_reason"] == "length"
        counts["new_length_cap"] += new["done_reason"] == "length"
        counts["rescued"] += new_ok and not old_ok
        counts["harmed"] += old_ok and not new_ok
        counts["answer_changed"] += old["answer"] != new["answer"]
        output_tokens["old"] += old["output_tokens"]
        output_tokens["new"] += new["output_tokens"]
        request_ms["old"] += old["latency_ms"]
        request_ms["new"] += new["latency_ms"]
    report = {"status": "development_protocol_diagnostic_not_sealed_holdout",
              "selection_protocol_hash": selection["protocol_hash"],
              "main_protocol_hash": main_manifest["protocol_hash"],
              "context_protocol_hash": pilot_manifest["protocol_hash"],
              "n": 70, "subjects": 14, "old_num_ctx": 4096, "new_num_ctx": 8192,
              "counts": dict(counts),
              "accuracy_delta": round(float(np.mean(delta_correct)), 5),
              "accuracy_delta_cluster_ci": cluster_ci(delta_correct, subjects),
              "validity_delta": round(float(np.mean(delta_valid)), 5),
              "validity_delta_cluster_ci": cluster_ci(delta_valid, subjects),
              "output_tokens": dict(output_tokens),
              "summed_request_seconds": {key: round(value / 1000, 2)
                                         for key, value in request_ms.items()}}
    (OUTPUT / "analysis.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
