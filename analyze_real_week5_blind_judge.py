#!/usr/bin/env python3
"""Compare candidate-blind Modal judgments with candidate-conditioned judgments."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from repguard.data.mmlu_pro import load_mmlu_pro
from run_real_week5_blind_judge import prompt_for


def ratio(a: int, b: int) -> float | None:
    return round(a / b, 4) if b else None


def paired_cluster_ci(cases: list[dict], *, repetitions: int = 10000) -> list[float] | None:
    by_task = defaultdict(list)
    for case in cases:
        by_task[case["task_id"]].append(case)
    ids = sorted(by_task)
    if not ids:
        return None
    rng = random.Random(3141592)
    values = []
    for _ in range(repetitions):
        sampled = [rng.choice(ids) for _ in ids]
        rows = [row for task_id in sampled for row in by_task[task_id]]
        values.append(sum(row["blind_correct"] - row["candidate_correct"]
                          for row in rows) / len(rows))
    values.sort()
    return [round(values[int(.025 * repetitions)], 4),
            round(values[int(.975 * repetitions)], 4)]


def analyze(blind_dir: Path, candidate_dir: Path) -> dict:
    manifest = json.loads((blind_dir / "manifest.json").read_text())
    source = json.loads((candidate_dir / "manifest.json").read_text())
    if manifest["source_judge_protocol_hash"] != source["protocol_hash"]:
        raise RuntimeError("Blind manifest points to another candidate judge")
    if manifest["judge_model_digest"] != source["judge_model_digest"]:
        raise RuntimeError("Model digest differs between judge conditions")
    tasks = {task.task_id: task for task in load_mmlu_pro(data_dir="data")}
    digest = hashlib.sha256("\n".join(sorted(tasks)).encode()).hexdigest()
    if digest != manifest["dataset_task_id_sha256"]:
        raise RuntimeError("Local MMLU-Pro dataset changed")
    planned = {case["task_id"]: case for case in manifest["candidate_blind_cases"]}
    if len(planned) != len(manifest["candidate_blind_cases"]):
        raise RuntimeError("Duplicate blind case in frozen manifest")
    blind = {}
    path = blind_dir / "judgments.jsonl"
    for line in path.read_text().splitlines() if path.exists() else []:
        if not line.strip():
            continue
        row = json.loads(line)
        task_id = row["task_id"]
        if task_id in blind or task_id not in planned:
            raise RuntimeError("Duplicate or unknown blind judgment")
        task = tasks[task_id]
        prompt_hash = hashlib.sha256(prompt_for(task).encode()).hexdigest()
        if (row["protocol_hash"] != manifest["protocol_hash"] or
            row["model_digest"] != manifest["judge_model_digest"] or
            row["prompt_hash"] != prompt_hash or
            row["prompt_hash"] != planned[task_id]["prompt_hash"] or
            row["subject"] != planned[task_id]["subject"]):
            raise RuntimeError("Blind response metadata differs from manifest")
        try:
            parsed = json.loads(row["raw_response"])
        except json.JSONDecodeError:
            parsed = {}
        if row["valid_judgment"] and (
            parsed.get("chosen_letter") != row["chosen_letter"] or
            parsed.get("confidence") != row["confidence"]):
            raise RuntimeError("Blind parsed response differs from raw JSON")
        blind[task_id] = row

    candidate_planned = {(c["task_id"], c["candidate_answer"]): c
                         for c in source["candidate_cases"]}
    candidate = {}
    for line in (candidate_dir / "judgments.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        key = (row["task_id"], row["candidate_answer"])
        if key in candidate or key not in candidate_planned or not row["valid_judgment"]:
            raise RuntimeError("Candidate judge ledger mismatch")
        candidate[key] = row
    if set(candidate) != set(candidate_planned):
        raise RuntimeError("Candidate judge ledger incomplete")

    comparable = []
    blind_confusion = Counter()
    candidate_confusion = Counter()
    by_subject = defaultdict(Counter)
    for (task_id, answer), old in candidate.items():
        new = blind.get(task_id)
        if new is None or not new["valid_judgment"]:
            continue
        truth = answer == tasks[task_id].ground_truth_answer
        blind_verdict = answer == new["chosen_letter"]
        for verdict, counts in ((blind_verdict, blind_confusion),
                                (old["verdict"], candidate_confusion)):
            counts["tp" if truth and verdict else
                   "fn" if truth else "fp" if verdict else "tn"] += 1
        blind_correct = int(blind_verdict == truth)
        candidate_correct = int(old["verdict"] == truth)
        comparable.append({"task_id": task_id, "subject": old["subject"],
                           "blind_correct": blind_correct,
                           "candidate_correct": candidate_correct})
        by_subject[old["subject"]]["blind_correct"] += blind_correct
        by_subject[old["subject"]]["candidate_correct"] += candidate_correct
        by_subject[old["subject"]]["n"] += 1

    valid = [row for row in blind.values() if row["valid_judgment"]]
    n = len(comparable)
    result = {
        "blind_protocol_hash": manifest["protocol_hash"],
        "candidate_protocol_hash": source["protocol_hash"],
        "model_digest": manifest["judge_model_digest"],
        "planned_questions": len(planned),
        "completed_questions": len(blind),
        "valid_questions": len(valid),
        "blind_choice_accuracy_per_question": ratio(
            sum(row["chosen_letter"] == tasks[row["task_id"]].ground_truth_answer
                for row in valid), len(valid)),
        "comparable_unique_answer_cases": n,
        "blind_verdict_confusion": dict(blind_confusion),
        "candidate_verdict_confusion": dict(candidate_confusion),
        "blind_verdict_accuracy": ratio(
            blind_confusion["tp"] + blind_confusion["tn"], n),
        "candidate_verdict_accuracy": ratio(
            candidate_confusion["tp"] + candidate_confusion["tn"], n),
        "blind_minus_candidate_accuracy": (round(sum(
            row["blind_correct"] - row["candidate_correct"] for row in comparable
        ) / n, 4) if n else None),
        "blind_minus_candidate_cluster_bootstrap_95ci": paired_cluster_ci(comparable),
        "blind_input_tokens": sum(row["input_tokens"] for row in blind.values()),
        "blind_output_tokens": sum(row["output_tokens"] for row in blind.values()),
        "blind_request_seconds": round(sum(row["latency_ms"] for row in blind.values())/1000, 2),
        "candidate_request_seconds": round(sum(row["latency_ms"] for row in candidate.values())/1000, 2),
        "by_subject": {subject: {"n": c["n"],
            "blind_accuracy": ratio(c["blind_correct"], c["n"]),
            "candidate_accuracy": ratio(c["candidate_correct"], c["n"])}
            for subject, c in sorted(by_subject.items())},
    }
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--blind", type=Path, default=Path("results/real_week5_blind_judge_v1"))
    p.add_argument("--candidate", type=Path,
                   default=Path("results/real_week5_modal_judge_v1"))
    args = p.parse_args()
    print(json.dumps(analyze(args.blind, args.candidate), indent=2))


if __name__ == "__main__":
    main()
