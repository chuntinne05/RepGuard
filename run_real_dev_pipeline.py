#!/usr/bin/env python3
"""Watchdog for the long real thinking run after direct collection completes.

The collector is append-only and resumable. This controller checks ledger growth,
retries transient exits/stalls, validates all 2,800 rows, then runs the frozen
development analyses. A living process alone is never counted as progress.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from analyze_real_dev_pool import analyze
from evaluate_fresh_dev_audit import run as evaluate_audit
from evaluate_fresh_dev_selector import run as evaluate_selector

OUTPUT = Path("results/real_dev_pool_v1")
LEDGER = OUTPUT / "predictions.jsonl"
STATUS = OUTPUT / "status.json"
LOG = OUTPUT / "thinking_runner.log"
DIRECT = ("qwen3_8b_direct", "qwen3_14b_direct", "gemma2_direct", "qwen3_06b_direct")
EXPECTED_THINKING = 560


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def counts() -> Counter:
    result = Counter()
    if LEDGER.exists():
        with LEDGER.open() as handle:
            for line in handle:
                if line.strip():
                    result[json.loads(line)["variant"]] += 1
    return result


def status(stage: str, **details) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    payload = {"timestamp": now(), "stage": stage,
               "completed_by_variant": dict(counts()), **details}
    temp = STATUS.with_suffix(".json.tmp")
    temp.write_text(json.dumps(payload, indent=2) + "\n")
    temp.replace(STATUS)
    print(json.dumps(payload), flush=True)


def run_thinking() -> None:
    if any(counts()[name] != 560 for name in DIRECT):
        raise RuntimeError("Direct variants must be complete before thinking watchdog starts")
    attempts_without_growth = 0
    while counts()["qwen3_8b_thinking"] < EXPECTED_THINKING:
        start_n = counts()["qwen3_8b_thinking"]
        status("thinking_launch", completed=start_n, expected=EXPECTED_THINKING,
               attempts_without_growth=attempts_without_growth)
        command = [sys.executable, "run_real_dev_pool.py", "--collect", "--variants",
                   "qwen3_8b_thinking", "--limit-per-subject", "40", "--timeout-seconds", "600"]
        with LOG.open("a") as log:
            log.write(f"\n=== {now()} thinking restart from {start_n} ===\n")
            log.flush()
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
            last_n = start_n
            last_progress = time.monotonic()
            while process.poll() is None:
                time.sleep(60)
                current = counts()["qwen3_8b_thinking"]
                if current > last_n:
                    last_n = current
                    last_progress = time.monotonic()
                    attempts_without_growth = 0
                    status("thinking_running", completed=current,
                           expected=EXPECTED_THINKING, runner_pid=process.pid)
                elif time.monotonic() - last_progress > 2400:
                    status("thinking_stalled_restarting", completed=current,
                           stale_seconds=round(time.monotonic() - last_progress),
                           runner_pid=process.pid)
                    process.terminate()
                    try:
                        process.wait(timeout=30)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                    break
        current = counts()["qwen3_8b_thinking"]
        if current >= EXPECTED_THINKING:
            break
        if current == start_n:
            attempts_without_growth += 1
        else:
            attempts_without_growth = 0
        status("thinking_retry", completed=current, expected=EXPECTED_THINKING,
               exit_code=process.returncode,
               attempts_without_growth=attempts_without_growth)
        if attempts_without_growth >= 3:
            raise RuntimeError("Thinking runner exited/stalled three times without ledger growth")
        time.sleep(30)
    status("thinking_ledger_complete", completed=counts()["qwen3_8b_thinking"])


def main() -> None:
    try:
        run_thinking()
        validated = analyze()
        if validated["status"] != "complete" or validated["total_completed"] != 2800:
            raise RuntimeError("Real development ledger failed completeness validation")
        status("ledger_validated", ledger_sha256=validated["ledger_sha256"])
        selector = evaluate_selector()
        audit = evaluate_audit()
        selector_gate = selector["selector_correct"] - selector["invalid_fallback_correct"] >= 12
        related = audit["paired_effects"]["related"]
        attack_gain = related["AuditedECRT_minus_FixedPlusAudit_under_attack"]
        audit_only_gain = related["AuditedECRT_minus_AuditOnly_under_attack"]
        clean_a = audit["cells"]["related"]["clean"]["AuditedECRT"]["estimate"]
        clean_b = audit["cells"]["related"]["clean"]["FixedPlusAudit"]["estimate"]
        audit_gate = (attack_gain["ci_lo"] > 0 and audit_only_gain["ci_lo"] > 0
                      and clean_a - clean_b >= -0.01)
        status("pipeline_complete", ledger_sha256=validated["ledger_sha256"],
               selector_correct=selector["selector_correct"],
               selector_gate=selector_gate,
               audited_attack_gain=attack_gain,
               audited_minus_audit_only=audit_only_gain,
               audited_clean_delta=clean_a - clean_b,
               audit_gate=audit_gate)
    except Exception as exc:
        status("pipeline_failed", error_type=type(exc).__name__, error=str(exc)[:500])
        raise


if __name__ == "__main__":
    main()
