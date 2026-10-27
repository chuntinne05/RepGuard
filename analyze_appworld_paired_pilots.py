#!/usr/bin/env python3
"""Compare two AppWorld train pilots on shared IDs after official state checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_pilot(path: Path) -> tuple[dict, dict[str, dict]]:
    manifest = json.loads((path / "manifest.json").read_text())
    evaluation = json.loads((path / "evaluation.json").read_text())
    if evaluation["protocol_hash"] != manifest["protocol_hash"]:
        raise ValueError(f"Manifest/evaluation mismatch: {path}")
    if manifest["split"] != "train":
        raise ValueError(f"Only train pilots may be compared: {path}")
    if len(evaluation["cells"]) != 1:
        raise ValueError(f"Expected exactly one policy in {path}")
    return manifest, next(iter(evaluation["cells"].values()))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--left", required=True, type=Path)
    parser.add_argument("--right", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    left_manifest, left_cells = load_pilot(args.left)
    right_manifest, right_cells = load_pilot(args.right)
    if left_manifest["model_digest"] != right_manifest["model_digest"]:
        raise ValueError("Model digests differ")
    if left_manifest["task_ids"] != right_manifest["task_ids"]:
        raise ValueError("Paired task plans differ")
    ids = [task_id for task_id in left_manifest["task_ids"]
           if task_id in left_cells and task_id in right_cells]
    rows = []
    paired = {"both_success": 0, "both_failure": 0,
              "left_only": 0, "right_only": 0}
    for task_id in ids:
        left = left_cells[task_id]
        right = right_cells[task_id]
        if left["total_checks"] != right["total_checks"]:
            raise ValueError(f"State-check count differs: {task_id}")
        key = ("both_success" if left["success"] and right["success"] else
               "both_failure" if not left["success"] and not right["success"] else
               "left_only" if left["success"] else "right_only")
        paired[key] += 1
        rows.append({"task_id": task_id, "left": left, "right": right,
                     "outcome": key})
    result = {"split": "train", "model_digest": left_manifest["model_digest"],
              "left_protocol_hash": left_manifest["protocol_hash"],
              "right_protocol_hash": right_manifest["protocol_hash"],
              "n_planned": len(left_manifest["task_ids"]), "n_paired": len(ids),
              "paired": paired, "rows": rows,
              "scope": "Exploratory train comparison; different inference and token budgets"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"n_paired": len(ids), "paired": paired}, indent=2))


if __name__ == "__main__":
    main()
