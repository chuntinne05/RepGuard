#!/usr/bin/env python3
"""Validate the frozen 560-question development ledger and score complete variants.

Reads no sealed-holdout outcomes. Every raw response, task ID, prompt and model
configuration is checked before any accuracy is computed.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from repguard.data.mmlu_pro import load_mmlu_pro
from repguard.harness.prompts import format_prompt
from run_real_dev_pool import FROZEN, OUTPUT, VARIANTS
from run_real_week4_thinking import canonical_hash


def load_validated(output: Path = OUTPUT):
    frozen = json.loads(FROZEN.read_text())
    protocol = {key: value for key, value in frozen.items()
                if key not in ("created_at", "protocol_hash")}
    if canonical_hash(protocol) != frozen["protocol_hash"]:
        raise RuntimeError("Frozen source manifest changed")
    manifest = json.loads((output / "manifest.json").read_text())
    own_protocol = {key: value for key, value in manifest.items()
                    if key not in ("created_at", "protocol_hash")}
    if canonical_hash(own_protocol) != manifest["protocol_hash"]:
        raise RuntimeError("Development pool manifest hash mismatch")
    if manifest["source_protocol_hash"] != frozen["protocol_hash"] or (
            manifest["variants"] != VARIANTS or
            manifest["selected_development_ids"] != frozen["selected"]["development"]):
        raise RuntimeError("Development manifest differs from frozen protocol")
    selected = {task_id: subject for subject, ids in
                manifest["selected_development_ids"].items() for task_id in ids}
    holdout_ids = {task_id for ids in frozen["selected"]["holdout"].values()
                   for task_id in ids}
    if len(selected) != 560 or set(selected) & holdout_ids:
        raise RuntimeError("Development IDs incomplete or overlap sealed holdout")
    tasks = {task.task_id: task for task in load_mmlu_pro(data_dir="data")}
    digest = hashlib.sha256("\n".join(sorted(tasks)).encode()).hexdigest()
    if digest != manifest["dataset_task_id_sha256"]:
        raise RuntimeError("MMLU-Pro task IDs differ from frozen protocol")

    ledger = output / "predictions.jsonl"
    rows = {}
    if ledger.exists():
        for line in ledger.open():
            if not line.strip():
                continue
            row = json.loads(line)
            variant, task_id = row["variant"], row["task_id"]
            if variant not in VARIANTS or task_id not in selected:
                raise RuntimeError("Ledger contains a non-development task or variant")
            settings = VARIANTS[variant]
            if (row["protocol_hash"] != manifest["protocol_hash"] or
                row["model_id"] != settings["model_id"] or
                row["model_digest"] != manifest["model_digests"][settings["model_id"]] or
                row["think"] != settings["think"] or
                row["max_tokens"] != settings["max_tokens"] or
                row["subject"] != selected[task_id] or
                row["split"] != "development"):
                raise RuntimeError("Ledger row differs from model or split protocol")
            task = tasks[task_id]
            prompt = format_prompt(task.to_online_view(), mode="direct").text
            prompt += "\nRespond as JSON with only one key: answer."
            if hashlib.sha256(prompt.encode()).hexdigest() != row["prompt_hash"]:
                raise RuntimeError("Ledger prompt hash mismatch")
            valid_choices = {chr(ord("A") + i) for i in range(len(task.options))}
            try:
                parsed = json.loads(row["raw_response"]).get("answer")
            except (json.JSONDecodeError, AttributeError):
                parsed = None
            parsed = parsed if parsed in valid_choices else None
            if (parsed != row["answer"] or
                (parsed is not None) != row["valid_answer"] or
                row["num_options"] != len(task.options)):
                raise RuntimeError("Stored answer does not match raw response")
            key = variant, task_id
            if key in rows:
                raise RuntimeError(f"Duplicate model answer: {key}")
            rows[key] = row
    return manifest, tasks, rows


def analyze(output: Path = OUTPUT) -> dict:
    manifest, tasks, rows = load_validated(output)
    by_variant = {}
    for variant in VARIANTS:
        selected = [row for (name, _), row in rows.items() if name == variant]
        complete = len(selected) == 560
        by_variant[variant] = {
            "completed": len(selected), "expected": 560,
            "invalid": sum(not row["valid_answer"] for row in selected),
            "output_tokens": sum(row["output_tokens"] for row in selected),
            "summed_request_seconds": round(
                sum(row["latency_ms"] for row in selected) / 1000, 2),
            "correct_if_complete": sum(row["answer"] == tasks[row["task_id"]].ground_truth_answer
                                       for row in selected) if complete else None,
        }
    result = {
        "status": "complete" if len(rows) == 2800 else "partial",
        "protocol_hash": manifest["protocol_hash"],
        "ledger_sha256": hashlib.sha256((output / "predictions.jsonl").read_bytes()).hexdigest()
        if (output / "predictions.jsonl").exists() else None,
        "total_completed": len(rows), "expected": 2800,
        "by_variant": by_variant,
    }
    (output / "analysis.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    print(json.dumps(analyze(), indent=2))
