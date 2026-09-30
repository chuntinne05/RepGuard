#!/usr/bin/env python3
"""Offline AppWorld state-check scoring for the gold-blind train pilot."""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_ROOT = ROOT / "results/appworld_external_v1"
OUTPUT = DATA_ROOT / "train_pilot_v1"


def main() -> None:
    os.environ["APPWORLD_ROOT"] = str(DATA_ROOT)
    from appworld.evaluator import evaluate_task

    manifest = json.loads((OUTPUT / "manifest.json").read_text())
    cells: dict[str, dict[str, dict]] = {}
    for policy in manifest["policies"]:
        cells[policy] = {}
        for task_id in manifest["task_ids"]:
            path = OUTPUT / "runs" / policy / f"{task_id}.json"
            if not path.exists():
                continue
            run = json.loads(path.read_text())
            if run["protocol_hash"] != manifest["protocol_hash"] or run["task_id"] != task_id:
                raise RuntimeError(f"Incompatible run: {path}")
            tracker = evaluate_task(task_id=task_id, experiment_name=run["experiment"],
                                    save_report=False)
            cells[policy][task_id] = {
                "success": tracker.success,
                "passed_checks": tracker.pass_count,
                "total_checks": tracker.num_tests,
                "steps": run["steps"],
                "completed_task_api": run["completed_task_api"],
                "input_tokens": sum(s.get("input_tokens") or 0 for s in run["trajectory"]),
                "output_tokens": sum(s.get("output_tokens") or 0 for s in run["trajectory"]),
            }
    policies = list(manifest["policies"])
    common = sorted(set(cells[policies[0]]) & set(cells[policies[1]]))
    paired = {"both_success": 0, "both_failure": 0,
              f"{policies[0]}_only": 0, f"{policies[1]}_only": 0}
    for task_id in common:
        left = cells[policies[0]][task_id]["success"]
        right = cells[policies[1]][task_id]["success"]
        key = ("both_success" if left and right else "both_failure" if not left and not right
               else f"{policies[0]}_only" if left else f"{policies[1]}_only")
        paired[key] += 1
    result = {"protocol_hash": manifest["protocol_hash"], "n_planned": len(manifest["task_ids"]),
              "n_paired": len(common), "cells": cells, "paired": paired,
              "scope": "train feasibility only; custom local ReAct harness; no paper score"}
    (OUTPUT / "evaluation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"n_paired": len(common), "paired": paired,
                      "success_by_policy": {p: sum(v["success"] for v in rows.values())
                                            for p, rows in cells.items()}}, indent=2))


if __name__ == "__main__":
    main()
