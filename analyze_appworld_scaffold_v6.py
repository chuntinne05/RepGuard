#!/usr/bin/env python3
"""Summarize paired, fresh-process state checks for the two v6 train policies."""

from __future__ import annotations

import json
from pathlib import Path

from run_appworld_train_pilot_v6 import OUTPUT, POLICIES


def main() -> None:
    manifest = json.loads((OUTPUT / "manifest.json").read_text())
    evaluation = json.loads((OUTPUT / "evaluation.json").read_text())
    if evaluation["protocol_hash"] != manifest["protocol_hash"]:
        raise RuntimeError("Manifest/evaluation mismatch")
    left_name, right_name = POLICIES
    left_cells = evaluation["cells"][left_name]
    right_cells = evaluation["cells"][right_name]
    rows = []
    paired = {"both_success": 0, "both_failure": 0,
              "control_only": 0, "verified_only": 0}
    totals = {name: {"task_success": 0, "steps": 0, "input_tokens": 0,
                     "output_tokens": 0} for name in POLICIES}
    for task_id in manifest["task_ids"]:
        if task_id not in left_cells or task_id not in right_cells:
            continue
        left = left_cells[task_id]
        right = right_cells[task_id]
        if left["total_checks"] != right["total_checks"]:
            raise RuntimeError(f"Evaluator check count differs for {task_id}")
        outcome = ("both_success" if left["success"] and right["success"] else
                   "both_failure" if not left["success"] and not right["success"] else
                   "control_only" if left["success"] else "verified_only")
        paired[outcome] += 1
        rows.append({"task_id": task_id, "control": left,
                     "verified": right, "outcome": outcome})
        for name, cell in ((left_name, left), (right_name, right)):
            totals[name]["task_success"] += int(cell["success"])
            for metric in ("steps", "input_tokens", "output_tokens"):
                totals[name][metric] += cell[metric]
    report = {"split": "train", "protocol_hash": manifest["protocol_hash"],
              "model_digest": manifest["model_digest"],
              "n_planned": len(manifest["task_ids"]), "n_paired": len(rows),
              "paired": paired, "totals": totals, "rows": rows,
              "scope": "Custom-harness train scaffold comparison, equal inference budget; not an official AppWorld baseline or method claim"}
    (OUTPUT / "paired.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("n_paired", "paired", "totals")},
                     indent=2))


if __name__ == "__main__":
    main()
