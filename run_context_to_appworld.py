#!/usr/bin/env python3
"""Finish the frozen context diagnostic, then run the disjoint AppWorld v2 pilot.

The inference collectors are resumable and validate their own manifests. This
driver serializes GPU work, retries interrupted collectors, and records the
actual final analysis/evaluation state for unattended continuation.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTEXT = ROOT / "results/real_dev_context_pilot_v1"
APPWORLD = ROOT / "results/appworld_external_v1/train_pilot_v2"
STATUS = CONTEXT / "followup_status.json"
APPWORLD_PYTHON = Path("/private/tmp/repguard_appworld_env/bin/python")


def record(stage: str, **details: object) -> None:
    CONTEXT.mkdir(parents=True, exist_ok=True)
    data = {"timestamp": datetime.now(timezone.utc).isoformat(),
            "stage": stage, **details}
    temp = STATUS.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2) + "\n")
    temp.replace(STATUS)
    print(json.dumps(data), flush=True)


def row_count() -> int:
    ledger = CONTEXT / "predictions.jsonl"
    if not ledger.exists():
        return 0
    return sum(bool(line.strip()) for line in ledger.open())


def retry_command(stage: str, command: list[str], *, attempts: int = 8) -> None:
    for attempt in range(1, attempts + 1):
        record(stage, attempt=attempt, context_rows=row_count())
        result = subprocess.run(command, cwd=ROOT, check=False)
        if result.returncode == 0:
            return
        record(stage + "_retry", attempt=attempt, returncode=result.returncode,
               context_rows=row_count())
        if attempt < attempts:
            time.sleep(min(30 * attempt, 120))
    raise RuntimeError(f"{stage} failed after {attempts} attempts")


def main() -> None:
    try:
        if row_count() != 70:
            retry_command("context_collecting", [sys.executable, "-u",
                "run_real_dev_context_pilot.py", "--collect", "--timeout-seconds", "600"])
        if row_count() != 70:
            raise RuntimeError(f"Expected 70 context rows, got {row_count()}")
        record("context_analyzing", context_rows=70)
        subprocess.run([sys.executable, "analyze_real_dev_context_pilot.py"],
                       cwd=ROOT, check=True)
        context_analysis = json.loads((CONTEXT / "analysis.json").read_text())
        if context_analysis["n"] != 70:
            raise RuntimeError("Context analysis did not validate all 70 rows")
        if not APPWORLD_PYTHON.exists():
            raise RuntimeError("Isolated AppWorld Python environment missing")
        retry_command("appworld_v2_collecting", [str(APPWORLD_PYTHON), "-u",
            "run_appworld_train_pilot_v2.py", "--collect", "--max-tasks", "3"],
            attempts=4)
        record("appworld_v2_evaluating", context_rows=70)
        subprocess.run([str(APPWORLD_PYTHON), "evaluate_appworld_train_pilot.py",
                        "--output", str(APPWORLD)], cwd=ROOT, check=True)
        evaluation = json.loads((APPWORLD / "evaluation.json").read_text())
        cells = evaluation["cells"]["qwen3_14b_direct"]
        if len(cells) != 3:
            raise RuntimeError(f"Expected 3 evaluated AppWorld tasks, got {len(cells)}")
        record("followup_complete", context_rows=70,
               context_accuracy_delta=context_analysis["accuracy_delta"],
               context_validity_delta=context_analysis["validity_delta"],
               appworld_tasks=3,
               appworld_successes=sum(int(cell["success"]) for cell in cells.values()))
    except Exception as exc:
        record("followup_failed", error_type=type(exc).__name__, error=str(exc)[:500],
               context_rows=row_count())
        raise


if __name__ == "__main__":
    main()
