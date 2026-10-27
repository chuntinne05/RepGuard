#!/usr/bin/env python3
"""Audit and score the real multi-model overlap ledger without test leakage."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from repguard.data.mmlu_pro import load_mmlu_pro
from repguard.harness.prompts import format_prompt
from run_real_pool_overlap import MODELS, OUTPUT, SOURCE


def analyze(output: Path = OUTPUT) -> dict:
    source_manifest = json.loads(SOURCE.read_text())
    manifest = json.loads((output / "manifest.json").read_text())
    if manifest["source_protocol_hash"] != source_manifest["protocol_hash"]:
        raise RuntimeError("Pool study points to a different Qwen screen")
    selected = {tid: subject for subject, ids in manifest["selected_train_ids"].items()
                for tid in ids}
    if len(selected) != 420:
        raise RuntimeError("Pool manifest must have 420 distinct task IDs")
    task_map = {task.task_id: task for task in load_mmlu_pro(data_dir="data")}
    digest = hashlib.sha256("\n".join(sorted(task_map)).encode()).hexdigest()
    if digest != manifest["dataset_task_id_sha256"]:
        raise RuntimeError("Local benchmark changed")

    source: dict[tuple[str, str], dict] = {}
    for line in Path("results/real_week4_thinking_pilot_v3/predictions.jsonl").open():
        row = json.loads(line)
        if row["task_id"] not in selected or row["protocol_hash"] != source_manifest["protocol_hash"]:
            raise RuntimeError("Source answer outside frozen protocol")
        key = row["task_id"], row["variant"]
        if key in source:
            raise RuntimeError("Duplicate source answer")
        source[key] = row
    if len(source) != 840:
        raise RuntimeError("Source screen incomplete")

    pool: dict[tuple[str, str], dict] = {}
    ledger = output / "predictions.jsonl"
    for line in ledger.open() if ledger.exists() else []:
        row = json.loads(line)
        tid, model = row["task_id"], row["model_id"]
        if (tid not in selected or model not in MODELS or
            row["protocol_hash"] != manifest["protocol_hash"] or
            row["model_digest"] != manifest["model_digests"][model] or
            row["subject"] != selected[tid] or row["split"] != "train_calibration" or
            row["think"] is not False or row["max_tokens"] != 64):
            raise RuntimeError("Pool row differs from frozen manifest")
        task = task_map[tid]
        prompt = format_prompt(task.to_online_view(), mode="direct").text
        prompt += "\nRespond as JSON with only one key: answer."
        if hashlib.sha256(prompt.encode()).hexdigest() != row["prompt_hash"]:
            raise RuntimeError("Pool prompt hash mismatch")
        try:
            answer = json.loads(row["raw_response"]).get("answer")
        except (json.JSONDecodeError, AttributeError):
            answer = None
        valid = {chr(ord("A") + i) for i in range(len(task.options))}
        if answer not in valid:
            answer = None
        if answer != row["answer"] or (answer is not None) != row["valid_answer"]:
            raise RuntimeError("Pool answer differs from raw response")
        key = tid, model
        if key in pool:
            raise RuntimeError("Duplicate pool answer")
        pool[key] = row

    by_model = {}
    paired_with_thinking = {}
    for model in MODELS:
        ids = [tid for tid in selected if (tid, model) in pool]
        n = len(ids)
        correct = sum(pool[tid, model]["answer"] == task_map[tid].ground_truth_answer
                      for tid in ids)
        by_model[model] = {"completed": n, "correct": correct,
                           "accuracy": round(correct / n, 4) if n else None,
                           "invalid": sum(not pool[tid, model]["valid_answer"] for tid in ids),
                           "output_tokens": sum(pool[tid, model]["output_tokens"] for tid in ids),
                           "summed_request_seconds": round(sum(pool[tid, model]["latency_ms"]
                                                               for tid in ids) / 1000, 2)}
        wins = sum(pool[tid, model]["answer"] == task_map[tid].ground_truth_answer and
                   source[tid, "thinking8192"]["answer"] != task_map[tid].ground_truth_answer
                   for tid in ids)
        losses = sum(pool[tid, model]["answer"] != task_map[tid].ground_truth_answer and
                     source[tid, "thinking8192"]["answer"] == task_map[tid].ground_truth_answer
                     for tid in ids)
        paired_with_thinking[model] = {"paired_n": n, "model_only_correct": wins,
                                        "thinking_only_correct": losses,
                                        "oracle_either_correct": sum(
                                            pool[tid, model]["answer"] == task_map[tid].ground_truth_answer or
                                            source[tid, "thinking8192"]["answer"] == task_map[tid].ground_truth_answer
                                            for tid in ids)}

    common = [tid for tid in selected if all((tid, model) in pool for model in MODELS)]
    all_oracle = sum(any(answer == task_map[tid].ground_truth_answer for answer in
                         [source[tid, "direct64"]["answer"],
                          source[tid, "thinking8192"]["answer"],
                          *(pool[tid, model]["answer"] for model in MODELS)])
                     for tid in common)
    by_subject: dict[str, dict] = defaultdict(dict)
    for subject in sorted(manifest["selected_train_ids"]):
        ids = [tid for tid in manifest["selected_train_ids"][subject] if tid in common]
        by_subject[subject] = {"n": len(ids)}
        for model in MODELS:
            by_subject[subject][model] = sum(
                pool[tid, model]["answer"] == task_map[tid].ground_truth_answer for tid in ids)
        by_subject[subject]["qwen3_8b_thinking"] = sum(
            source[tid, "thinking8192"]["answer"] == task_map[tid].ground_truth_answer
            for tid in ids)
    return {"protocol_hash": manifest["protocol_hash"], "expected_per_model": 420,
            "completed_rows": len(pool), "models": by_model,
            "paired_vs_qwen3_8b_thinking": paired_with_thinking,
            "all_models_common_n": len(common),
            "all_models_oracle_correct": all_oracle,
            "all_models_oracle_accuracy": round(all_oracle / len(common), 4) if common else None,
            "subjects_on_common_questions": by_subject}


if __name__ == "__main__":
    print(json.dumps(analyze(), indent=2))
