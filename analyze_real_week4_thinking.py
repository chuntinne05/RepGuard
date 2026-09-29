#!/usr/bin/env python3
"""Score completed paired Week 4 thinking calls offline, keeping labels out of the ledger."""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import hashlib
from collections import defaultdict
from pathlib import Path

from repguard.data.mmlu_pro import load_mmlu_pro
from repguard.harness.prompts import format_prompt
from run_real_week3 import load_dataset_and_splits


def describe(values: list[float]) -> dict:
    if not values:
        return {"median": None, "p95": None}
    ordered = sorted(values)
    return {"median": round(statistics.median(ordered), 2),
            "p95": round(ordered[max(0, int(0.95 * len(ordered) + 0.999) - 1)], 2)}


def paired_bootstrap_ci(by_subject: dict[str, list[str]], deltas: dict[str, int],
                        repetitions: int = 10000) -> list[float] | None:
    """Resample tasks within each subject; exploratory subject-balanced CI."""
    subjects = [ids for ids in by_subject.values() if ids]
    if not subjects:
        return None
    rng = random.Random(314159)
    estimates = []
    for _ in range(repetitions):
        sampled = [deltas[rng.choice(ids)] for ids in subjects for _ in ids]
        estimates.append(100 * sum(sampled) / len(sampled))
    estimates.sort()
    return [round(estimates[int(0.025 * repetitions)], 2),
            round(estimates[int(0.975 * repetitions)], 2)]


def analyze(output: Path, predictions_file: Path | None = None) -> dict:
    manifest = json.loads((output / "manifest.json").read_text())
    variants = list(manifest["variants"])
    source = predictions_file or output / "predictions.jsonl"
    rows = [json.loads(line) for line in source.read_text().splitlines()
            if line.strip()]
    if any(row["protocol_hash"] != manifest["protocol_hash"] for row in rows):
        raise RuntimeError("Ledger contains a different protocol")
    indexed = {(row["task_id"], row["variant"]): row for row in rows}
    if len(indexed) != len(rows):
        raise RuntimeError("Duplicate task/variant predictions")
    tasks = load_mmlu_pro(data_dir="data")
    task_map = {task.task_id: task for task in tasks}
    labels = {task.task_id: task.ground_truth_answer for task in tasks}
    selected = {tid: subject for subject, ids in manifest["selected_train_ids"].items()
                for tid in ids}
    if len(selected) != sum(map(len, manifest["selected_train_ids"].values())):
        raise RuntimeError("Duplicate selected task ID")
    week3 = json.loads(Path("results/real_week3_json_v1/manifest.json").read_text())
    _, splits = load_dataset_and_splits(manifest["split_seed"])
    train_ids = {task.task_id for task in splits["train_calibration"].records}
    week3_ids = {tid for ids in week3["selected"]["train_calibration"].values() for tid in ids}
    if not set(selected) <= train_ids or set(selected) & week3_ids:
        raise RuntimeError("Week 4 selection is not unused train data")
    if manifest["dataset_task_id_sha256"] != hashlib.sha256(
            "\n".join(sorted(task_map)).encode()).hexdigest():
        raise RuntimeError("Dataset digest mismatch")
    for row in rows:
        task_id, variant = row["task_id"], row["variant"]
        if task_id not in selected or variant not in manifest["variants"]:
            raise RuntimeError("Prediction outside frozen manifest")
        settings = manifest["variants"][variant]
        if (row["model_digest"] != manifest["model_digest"] or
            row["model_id"] != manifest["model_id"] or
            row["subject"] != selected[task_id] or
            row["think"] != settings["think"] or
            row["max_tokens"] != settings["max_tokens"]):
            raise RuntimeError("Prediction metadata differs from frozen protocol")
        task = task_map[task_id]
        prompt = format_prompt(task.to_online_view(), mode="direct")
        prompt_text = prompt.text + "\nRespond as JSON with only one key: answer."
        if row["prompt_hash"] != hashlib.sha256(prompt_text.encode()).hexdigest():
            raise RuntimeError("Prompt hash mismatch")
        try:
            parsed = json.loads(row["raw_response"]).get("answer")
        except (json.JSONDecodeError, AttributeError):
            parsed = None
        valid_letters = {chr(ord("A") + i) for i in range(len(task.options))}
        if parsed not in valid_letters:
            parsed = None
        if parsed != row["answer"] or row["valid_answer"] != (parsed is not None):
            raise RuntimeError("Stored answer differs from raw response")
        if row["output_tokens"] > settings["max_tokens"]:
            raise RuntimeError("Output exceeded protocol token budget")
    by_subject = defaultdict(list)
    for subject, ids in manifest["selected_train_ids"].items():
        for task_id in ids:
            if all((task_id, variant) in indexed for variant in variants):
                by_subject[subject].append(task_id)
    paired_ids = [task_id for ids in by_subject.values() for task_id in ids]
    summary = {"protocol_hash": manifest["protocol_hash"],
               "selected_n": sum(map(len, manifest["selected_train_ids"].values())),
               "completed_calls": len(rows), "paired_n": len(paired_ids),
               "subjects_paired": len([x for x in by_subject.values() if x]),
               "variants": {}, "subjects": {}}
    for variant in variants:
        arm = [indexed[(task_id, variant)] for task_id in paired_ids]
        correct = sum(row["answer"] == labels[row["task_id"]] for row in arm)
        summary["variants"][variant] = {
            "correct": correct, "n": len(arm),
            "accuracy": round(correct / len(arm), 4) if arm else None,
            "invalid": sum(not row["valid_answer"] for row in arm),
            "truncated": sum(row.get("done_reason") == "length" for row in arm),
            "thinking_present": sum(bool(row.get("thinking_present")) for row in arm),
            "total_output_tokens": sum(row["output_tokens"] for row in arm),
            "total_request_seconds": round(sum(row["latency_ms"] for row in arm) / 1000, 2),
            "output_tokens": describe([row["output_tokens"] for row in arm]),
            "latency_seconds": describe([row["latency_ms"] / 1000 for row in arm]),
        }
    if len(variants) == 2:
        a, b = variants
        wins = sum(indexed[(tid, b)]["answer"] == labels[tid] and
                   indexed[(tid, a)]["answer"] != labels[tid] for tid in paired_ids)
        losses = sum(indexed[(tid, a)]["answer"] == labels[tid] and
                     indexed[(tid, b)]["answer"] != labels[tid] for tid in paired_ids)
        deltas = {tid: int(indexed[(tid, b)]["answer"] == labels[tid]) -
                  int(indexed[(tid, a)]["answer"] == labels[tid]) for tid in paired_ids}
        discordant = wins + losses
        exact_p = min(1.0, 2 * sum(math.comb(discordant, k)
                                   for k in range(min(wins, losses) + 1)) / 2 ** discordant)
        summary["paired_difference"] = {"thinking_only_correct": wins,
                                         "direct_only_correct": losses,
                                         "net_questions": wins - losses,
                                         "accuracy_pp": round(100 * (wins-losses) / len(paired_ids), 2)
                                         if paired_ids else None,
                                         "bootstrap_95ci_pp": paired_bootstrap_ci(by_subject, deltas),
                                         "exact_mcnemar_p": round(exact_p, 5)}
    for subject, ids in by_subject.items():
        if ids:
            summary["subjects"][subject] = {"n": len(ids), **{
                variant: sum(indexed[(tid, variant)]["answer"] == labels[tid]
                             for tid in ids) for variant in variants},
                "thinking_truncated": sum(indexed[(tid, variants[1])].get("done_reason") == "length"
                                          for tid in ids) if len(variants) == 2 else None}
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/real_week4_thinking_pilot_v3")
    parser.add_argument("--predictions-file")
    args = parser.parse_args()
    print(json.dumps(analyze(Path(args.output), Path(args.predictions_file)
                             if args.predictions_file else None), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
