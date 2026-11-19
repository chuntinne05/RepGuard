#!/usr/bin/env python3
"""Verify and score real Modal judge feedback without exposing gold online."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from repguard.data.mmlu_pro import load_mmlu_pro
from run_real_week5_modal_judge import prompt_for


def ratio(a: int, b: int) -> float | None:
    return round(a / b, 4) if b else None


def cluster_bootstrap_accuracy(rows: list[dict], labels: dict[str, str],
                               *, repetitions: int = 10000) -> list[float] | None:
    by_task = defaultdict(list)
    for row in rows:
        if row["valid_judgment"]:
            by_task[row["task_id"]].append(row)
    task_ids = sorted(by_task)
    if not task_ids:
        return None
    rng = random.Random(1618033)
    values = []
    for _ in range(repetitions):
        picked = [rng.choice(task_ids) for _ in task_ids]
        observations = [row for task_id in picked for row in by_task[task_id]]
        correct = sum(row["verdict"] ==
                      (row["candidate_answer"] == labels[row["task_id"]])
                      for row in observations)
        values.append(correct / len(observations))
    values.sort()
    return [round(values[int(0.025 * repetitions)], 4),
            round(values[int(0.975 * repetitions)], 4)]


def cluster_bootstrap_gain_over_reject(rows: list[dict], labels: dict[str, str],
                                       *, repetitions: int = 10000) -> list[float] | None:
    by_task = defaultdict(list)
    for row in rows:
        if row["valid_judgment"]:
            by_task[row["task_id"]].append(row)
    task_ids = sorted(by_task)
    if not task_ids:
        return None
    rng = random.Random(2718281)
    values = []
    for _ in range(repetitions):
        picked = [rng.choice(task_ids) for _ in task_ids]
        observations = [row for task_id in picked for row in by_task[task_id]]
        gain = sum((row["verdict"] ==
                    (row["candidate_answer"] == labels[row["task_id"]])) -
                   (row["candidate_answer"] != labels[row["task_id"]])
                   for row in observations)
        values.append(gain / len(observations))
    values.sort()
    return [round(values[int(0.025 * repetitions)], 4),
            round(values[int(0.975 * repetitions)], 4)]


def analyze(output: Path) -> dict:
    manifest = json.loads((output / "manifest.json").read_text())
    path = output / "judgments.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []
    cases = {(case["task_id"], case["candidate_answer"]): case
             for case in manifest["candidate_cases"]}
    if len(cases) != len(manifest["candidate_cases"]):
        raise RuntimeError("Duplicate case in frozen judge manifest")
    task_map = {task.task_id: task for task in load_mmlu_pro(data_dir="data")}
    labels = {tid: task.ground_truth_answer for tid, task in task_map.items()}
    dataset_hash = hashlib.sha256("\n".join(sorted(task_map)).encode()).hexdigest()
    if dataset_hash != manifest["dataset_task_id_sha256"]:
        raise RuntimeError("Local MMLU-Pro dataset changed")
    seen = set()
    for row in rows:
        key = (row["task_id"], row["candidate_answer"])
        if key in seen or key not in cases:
            raise RuntimeError(f"Duplicate/unknown judge case: {key}")
        seen.add(key)
        case = cases[key]
        if (row["protocol_hash"] != manifest["protocol_hash"] or
            row["judge_model_id"] != manifest["judge_model_id"] or
            row["subject"] != case["subject"] or
            row["agents"] != case["agents"] or
            row["prompt_hash"] != case["prompt_hash"] or
            row["model_digest"] != manifest["judge_model_digest"]):
            raise RuntimeError("Judge row metadata differs from frozen manifest")
        actual_prompt_hash = hashlib.sha256(prompt_for(
            task_map[row["task_id"]], row["candidate_answer"]).encode()).hexdigest()
        if actual_prompt_hash != case["prompt_hash"]:
            raise RuntimeError("Judge prompt changed from frozen manifest")
        try:
            parsed = json.loads(row["raw_response"])
        except json.JSONDecodeError:
            parsed = {}
        if row["valid_judgment"]:
            if (parsed.get("verdict") != row["verdict"] or
                parsed.get("chosen_letter") != row["chosen_letter"] or
                parsed.get("confidence") != row["confidence"]):
                raise RuntimeError("Parsed judge output differs from raw response")

    valid = [row for row in rows if row["valid_judgment"]]
    counts = Counter()
    by_subject = defaultdict(Counter)
    by_agent = defaultdict(Counter)
    for row in valid:
        truth = row["candidate_answer"] == labels[row["task_id"]]
        verdict = row["verdict"]
        cell = ("tp" if truth and verdict else
                "fn" if truth else "fp" if verdict else "tn")
        counts[cell] += 1
        by_subject[row["subject"]][cell] += 1
        for agent in row["agents"]:
            by_agent[agent][cell] += 1
    n_valid = sum(counts.values())
    contradictions = sum(row["verdict"] !=
                         (row["candidate_answer"] == row["chosen_letter"])
                         for row in valid)
    chosen_by_task = defaultdict(set)
    case_count_by_task = Counter()
    for row in valid:
        chosen_by_task[row["task_id"]].add(row["chosen_letter"])
        case_count_by_task[row["task_id"]] += 1
    multi_candidate_tasks = sum(n > 1 for n in case_count_by_task.values())
    inconsistent_choice_tasks = sum(len(choices) > 1
                                    for choices in chosen_by_task.values())
    reject_correct = counts["tn"] + counts["fp"]
    result = {
        "protocol_hash": manifest["protocol_hash"],
        "judge_model_id": manifest["judge_model_id"],
        "selected_questions": sum(map(len, manifest["selected_history_ids"].values())),
        "planned_unique_cases": len(cases),
        "completed_unique_cases": len(rows),
        "judged_questions": len({row["task_id"] for row in rows}),
        "invalid": len(rows) - len(valid),
        "contradictions_verdict_vs_chosen_letter": contradictions,
        "confusion_unique_cases": dict(counts),
        "accuracy_unique_cases": ratio(counts["tp"]+counts["tn"], n_valid),
        "accuracy_cluster_bootstrap_95ci": cluster_bootstrap_accuracy(valid, labels),
        "always_reject_accuracy": ratio(reject_correct, n_valid),
        "gain_over_always_reject": (round((counts["tp"] + counts["tn"] - reject_correct) /
                                          n_valid, 4) if n_valid else None),
        "gain_over_always_reject_cluster_bootstrap_95ci":
            cluster_bootstrap_gain_over_reject(valid, labels),
        "false_positive_rate": ratio(counts["fp"], counts["fp"]+counts["tn"]),
        "false_negative_rate": ratio(counts["fn"], counts["fn"]+counts["tp"]),
        "multi_candidate_questions": multi_candidate_tasks,
        "questions_with_inconsistent_chosen_letter": inconsistent_choice_tasks,
        "mean_reported_confidence": (round(sum(row["confidence"] for row in valid) /
                                           len(valid), 4) if valid else None),
        "reported_confidence_at_least_0_9": ratio(
            sum(row["confidence"] >= 0.9 for row in valid), len(valid)),
        "chosen_letter_accuracy": ratio(
            sum(row["chosen_letter"] == labels[row["task_id"]] for row in valid),
            len(valid)),
        "total_input_tokens": sum(row["input_tokens"] for row in rows),
        "total_output_tokens": sum(row["output_tokens"] for row in rows),
        "truncated_outputs": sum(row.get("done_reason") == "length" for row in rows),
        "total_request_seconds": round(sum(row["latency_ms"] for row in rows)/1000, 2),
        "by_subject": {},
        "by_agent_weighted": {},
    }
    for name, cells in by_subject.items():
        total = sum(cells.values())
        result["by_subject"][name] = {**cells,
            "n_unique_cases": total,
            "accuracy": ratio(cells["tp"]+cells["tn"], total)}
    for name, cells in by_agent.items():
        total = sum(cells.values())
        result["by_agent_weighted"][name] = {**cells,
            "n_agent_answers": total,
            "accuracy": ratio(cells["tp"]+cells["tn"], total)}
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="results/real_week5_modal_judge_v1")
    args = p.parse_args()
    print(json.dumps(analyze(Path(args.output)), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
