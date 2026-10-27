#!/usr/bin/env python3
"""Score completed AppWorld 0.2 v10 trajectories in isolated official evaluators."""

from __future__ import annotations

import json
import os
import subprocess
import sys

from run_appworld_v10_simplified import DATA_ROOT, EXPERIMENT, OUTPUT, TASK_IDS


def evaluate(task_id: str) -> dict:
    worker = (
        "import json, os, sys\n"
        "os.environ['APPWORLD_ROOT'] = sys.argv[1]\n"
        "os.environ['APPWORLD_CACHE'] = '/private/tmp/repguard_appworld_02_cache'\n"
        "from appworld.evaluator import evaluate_task\n"
        "t = evaluate_task(task_id=sys.argv[2], experiment_name=sys.argv[3], save_report=False)\n"
        "print(json.dumps({'success': t.success, 'passed_checks': t.pass_count, "
        "'total_checks': t.num_tests}))\n"
    )
    env = os.environ.copy()
    env["APPWORLD_ROOT"] = str(DATA_ROOT)
    env["APPWORLD_CACHE"] = "/private/tmp/repguard_appworld_02_cache"
    done = subprocess.run(
        [sys.executable, "-c", worker, str(DATA_ROOT), task_id, EXPERIMENT],
        capture_output=True, text=True, timeout=180, check=True, env=env,
    )
    return json.loads(done.stdout.strip())


def main() -> None:
    manifest = json.loads((OUTPUT / "manifest.json").read_text())
    calls_path = OUTPUT / "model_calls.jsonl"
    calls = [json.loads(line) for line in calls_path.read_text().splitlines()] if calls_path.exists() else []
    cells = {}
    for task_id in TASK_IDS:
        finished = DATA_ROOT / "experiments/outputs" / EXPERIMENT / "tasks" / task_id / "misc/finished"
        if not finished.exists():
            continue
        score = evaluate(task_id)
        task_calls = [row for row in calls if row["task_id"] == task_id]
        cells[task_id] = {
            **score,
            "model_calls": len(task_calls),
            "input_tokens": sum(row.get("prompt_tokens") or 0 for row in task_calls),
            "output_tokens": sum(row.get("completion_tokens") or 0 for row in task_calls),
        }
    result = {
        "protocol_hash": manifest["protocol_hash"],
        "scope": "AppWorld 0.2 train-only official simplified ReAct capability screen",
        "planned": len(manifest["task_ids"]), "completed": len(cells), "cells": cells,
    }
    (OUTPUT / "evaluation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
