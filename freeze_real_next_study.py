#!/usr/bin/env python3
"""Freeze disjoint, label-free MMLU-Pro IDs for the post-Week-5 study.

This script selects from the original train/calibration split after excluding
every task ID named by prior real-study manifests or ledgers. It never reads
answer labels when selecting IDs. The development set may be inspected; the
holdout must remain untouched until a method and comparison are frozen.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from run_real_week3 import load_dataset_and_splits, utc_now


TASK_ID = re.compile(r"mmlu_pro_\d+\Z")
DEFAULT_OUTPUT = Path("results/real_next_study_v1/frozen_splits.json")


def canonical_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()


def ids_in(value: object) -> set[str]:
    if isinstance(value, str):
        return {value} if TASK_ID.fullmatch(value) else set()
    if isinstance(value, list):
        return set().union(*(ids_in(item) for item in value)) if value else set()
    if isinstance(value, dict):
        return set().union(*(ids_in(item) for item in value.values())) if value else set()
    return set()


def prior_ids(results: Path, output: Path) -> tuple[set[str], dict[str, str]]:
    used: set[str] = set()
    source_hashes: dict[str, str] = {}
    for path in sorted(results.glob("real_*/manifest.json")):
        if path.parent == output.parent:
            continue
        data = path.read_bytes()
        source_hashes[str(path)] = hashlib.sha256(data).hexdigest()
        used.update(ids_in(json.loads(data)))
    for path in sorted(results.glob("real_*/*.jsonl")):
        if path.parent == output.parent or path.name not in ("predictions.jsonl", "judgments.jsonl"):
            continue
        with path.open() as source:
            for line in source:
                if line.strip():
                    value = json.loads(line).get("task_id")
                    if isinstance(value, str) and TASK_ID.fullmatch(value):
                        used.add(value)
    return used, source_hashes


def freeze(results: Path, output: Path, *, seed: int, development_n: int,
           holdout_n: int) -> dict:
    base = json.loads((results / "real_week3_json_v1/manifest.json").read_text())
    tasks, splits = load_dataset_and_splits(base["split_seed"])
    dataset_hash = hashlib.sha256("\n".join(sorted(t.task_id for t in tasks)).encode()).hexdigest()
    if dataset_hash != base["dataset_task_id_sha256"]:
        raise RuntimeError("Local MMLU-Pro task IDs changed from Week 3")
    if output.exists():
        saved = json.loads(output.read_text())
        if (saved["dataset_task_id_sha256"] != dataset_hash or
            saved["selection_seed"] != seed or
            saved["counts_per_subject"] != {"development": development_n,
                                             "holdout": holdout_n}):
            raise RuntimeError("Frozen manifest differs from requested protocol")
        protocol = {k: v for k, v in saved.items() if k not in ("created_at", "protocol_hash")}
        if canonical_hash(protocol) != saved["protocol_hash"]:
            raise RuntimeError("Frozen manifest hash mismatch")
        return saved

    used, source_hashes = prior_ids(results, output)
    by_subject: dict[str, list[str]] = defaultdict(list)
    for task in splits["train_calibration"].records:
        if task.task_id not in used:
            by_subject[task.metadata.subject].append(task.task_id)
    if len(by_subject) != 14:
        raise RuntimeError(f"Expected 14 subjects, found {len(by_subject)}")
    selected = {"development": {}, "holdout": {}}
    for subject, ids in sorted(by_subject.items()):
        ordered = sorted(ids)
        random.Random(f"{seed}:next-study:{subject}").shuffle(ordered)
        if len(ordered) < development_n + holdout_n:
            raise RuntimeError(f"Only {len(ordered)} unused train items in {subject}")
        selected["development"][subject] = ordered[:development_n]
        selected["holdout"][subject] = ordered[development_n:development_n + holdout_n]
    all_selected = ids_in(selected)
    if len(all_selected) != 14 * (development_n + holdout_n) or all_selected & used:
        raise RuntimeError("Selection overlaps prior work or contains duplicates")
    protocol = {
        "name": "post_week5_development_and_sealed_holdout_v1",
        "dataset_id": base["dataset_id"],
        "dataset_task_id_sha256": dataset_hash,
        "original_split": "train_calibration",
        "original_split_seed": base["split_seed"],
        "selection_seed": seed,
        "counts_per_subject": {"development": development_n, "holdout": holdout_n},
        "excluded_prior_task_count": len(used),
        "exclusion_manifest_sha256": source_hashes,
        "selected": selected,
        "holdout_policy": "Do not inspect labels or model outcomes until methods, baselines and primary endpoint are frozen.",
    }
    frozen = {"created_at": utc_now(), "protocol_hash": canonical_hash(protocol), **protocol}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(frozen, indent=2, ensure_ascii=False) + "\n")
    return frozen


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=Path("results"))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seed", type=int, default=161803)
    parser.add_argument("--development-per-subject", type=int, default=40)
    parser.add_argument("--holdout-per-subject", type=int, default=30)
    args = parser.parse_args()
    if args.development_per_subject < 1 or args.holdout_per_subject < 1:
        parser.error("per-subject counts must be positive")
    frozen = freeze(args.results, args.output, seed=args.seed,
                    development_n=args.development_per_subject,
                    holdout_n=args.holdout_per_subject)
    print(json.dumps({"manifest": str(args.output), "protocol_hash": frozen["protocol_hash"],
                      "development_questions": sum(map(len, frozen["selected"]["development"].values())),
                      "sealed_holdout_questions": sum(map(len, frozen["selected"]["holdout"].values())),
                      "subjects": len(frozen["selected"]["development"])}))


if __name__ == "__main__":
    main()
