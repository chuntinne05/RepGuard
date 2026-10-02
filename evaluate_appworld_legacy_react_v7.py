#!/usr/bin/env python3
"""Score completed v7 AppWorld rollouts in isolated evaluator processes."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from run_appworld_legacy_react_v7 import DATA_ROOT, OUTPUT


def evaluate(task_id: str, experiment: str) -> dict:
    worker = (
        "import json, os, sys\n"
        "os.environ['APPWORLD_ROOT'] = sys.argv[1]\n"
        "from appworld.evaluator import evaluate_task\n"
        "t = evaluate_task(task_id=sys.argv[2], experiment_name=sys.argv[3], save_report=False)\n"
        "print(json.dumps({'success': t.success, 'passed_checks': t.pass_count, "
        "'total_checks': t.num_tests}))\n"
    )
    done = subprocess.run(
        [sys.executable, "-c", worker, str(DATA_ROOT), task_id, experiment],
        capture_output=True, text=True, timeout=120, check=True,
    )
    return json.loads(done.stdout.strip())


def main() -> None:
    manifest = json.loads((OUTPUT / "manifest.json").read_text())
    calls_path = OUTPUT / "model_calls.jsonl"
    calls = [json.loads(line) for line in calls_path.read_text().splitlines()] if calls_path.exists() else []
    cells = {}
    for task_id in manifest["task_ids"]:
        run_path = OUTPUT / "runs" / (task_id + ".json")
        if not run_path.exists():
            continue
        run = json.loads(run_path.read_text())
        if run["protocol_hash"] != manifest["protocol_hash"]:
            raise RuntimeError("v7 protocol mismatch")
        score = evaluate(task_id, run["experiment"])
        task_calls = [row for row in calls if row["task_id"] == task_id]
        cells[task_id] = {
            **score,
            "environment_steps": run["steps"],
            "model_calls": len(task_calls),
            "input_tokens": sum(row.get("prompt_tokens") or 0 for row in task_calls),
            "output_tokens": sum(row.get("completion_tokens") or 0 for row in task_calls),
        }
    result = {"protocol_hash": manifest["protocol_hash"],
              "scope": "AppWorld 0.1.3 train-only adapted legacy ReAct capability reference",
              "planned": len(manifest["task_ids"]), "completed": len(cells), "cells": cells}
    (OUTPUT / "evaluation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
