#!/usr/bin/env python3
"""Run a small real AppWorld capability pilot only after MMLU inference ends."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEV_STATUS = ROOT / "results/real_dev_pool_v1/status.json"
PILOT = ROOT / "results/appworld_external_v1/train_pilot_v1"
STATUS = PILOT / "deferred_status.json"
APPWORLD_PYTHON = Path("/private/tmp/repguard_appworld_env/bin/python")


def write(stage: str, **details) -> None:
    PILOT.mkdir(parents=True, exist_ok=True)
    payload = {"timestamp": datetime.now(timezone.utc).isoformat(),
               "stage": stage, **details}
    temp = STATUS.with_suffix(".json.tmp")
    temp.write_text(json.dumps(payload, indent=2) + "\n")
    temp.replace(STATUS)
    print(json.dumps(payload), flush=True)


def main() -> None:
    while True:
        if DEV_STATUS.exists():
            state = json.loads(DEV_STATUS.read_text())
            if state.get("stage") == "pipeline_complete":
                break
            if state.get("stage") == "pipeline_failed":
                write("waiting_stopped_source_failed", error=state.get("error"))
                return
        time.sleep(60)
    if not APPWORLD_PYTHON.exists():
        write("pilot_failed", error="Isolated AppWorld Python environment is missing")
        return
    write("pilot_running", source_ledger_sha256=state["ledger_sha256"],
          policy="qwen3_14b_direct", planned_tasks=3)
    try:
        subprocess.run([str(APPWORLD_PYTHON), "run_appworld_train_pilot.py", "--collect",
                        "--max-tasks", "3", "--policies", "qwen3_14b_direct"],
                       cwd=ROOT, check=True)
        subprocess.run([str(APPWORLD_PYTHON), "evaluate_appworld_train_pilot.py"],
                       cwd=ROOT, check=True)
        evaluation = json.loads((PILOT / "evaluation.json").read_text())
        rows = evaluation["cells"]["qwen3_14b_direct"]
        if len(rows) != 3:
            raise RuntimeError(f"Expected 3 state-checked tasks, found {len(rows)}")
        write("pilot_complete", tasks=3, state_check_successes=sum(
            int(row["success"]) for row in rows.values()),
            total_output_tokens=sum(row["output_tokens"] for row in rows.values()),
            scope="train capability smoke only; no paired policy comparison")
    except Exception as exc:
        write("pilot_failed", error_type=type(exc).__name__, error=str(exc)[:500])
        raise


if __name__ == "__main__":
    main()
