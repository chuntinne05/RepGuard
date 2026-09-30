#!/usr/bin/env python3
"""Wait for the real dev controller, then run all frozen follow-up analyses."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "results/real_dev_pool_v1"
STATUS = OUTPUT / "status.json"
POST = OUTPUT / "post_analysis_status.json"


def write(stage: str, **kwargs) -> None:
    payload = {"timestamp": datetime.now(timezone.utc).isoformat(),
               "stage": stage, **kwargs}
    temp = POST.with_suffix(".json.tmp")
    temp.write_text(json.dumps(payload, indent=2) + "\n")
    temp.replace(POST)
    print(json.dumps(payload), flush=True)


def main() -> None:
    while True:
        if STATUS.exists():
            state = json.loads(STATUS.read_text())
            if state.get("stage") == "pipeline_complete":
                break
            if state.get("stage") == "pipeline_failed":
                write("source_pipeline_failed", source_error=state.get("error"))
                return
        time.sleep(60)
    write("post_analysis_running", source_ledger_sha256=state["ledger_sha256"])
    try:
        subprocess.run([sys.executable, "evaluate_fresh_dev_router.py"],
                       cwd=ROOT, check=True)
        subprocess.run([sys.executable, "evaluate_fresh_dev_audit.py"],
                       cwd=ROOT, check=True)
        router = json.loads((OUTPUT / "selective_router_evaluation.json").read_text())
        audit = json.loads((OUTPUT / "audit_evaluation.json").read_text())
        if router["n"] != 560 or router["new_protocol_hash"] != audit["new_protocol_hash"]:
            raise RuntimeError("Post analyses do not match complete 560-question protocol")
        if "SingleQwen14Direct" not in audit["cells"]["related"]["clean"]:
            raise RuntimeError("Updated Qwen14 descriptive audit baseline is missing")
        write("post_analysis_complete", source_ledger_sha256=state["ledger_sha256"],
              router_correct=router["router_correct"], qwen14_calls=router["qwen14_calls"],
              audit_qwen14_baseline_present=True)
    except Exception as exc:
        write("post_analysis_failed", error_type=type(exc).__name__, error=str(exc)[:500])
        raise


if __name__ == "__main__":
    main()
