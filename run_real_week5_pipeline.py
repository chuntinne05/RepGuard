#!/usr/bin/env python3
"""Resume the predeclared Modal experiments sequentially after Week 4 finishes.

This controller never runs a second model while the Week 4 ledger is
incomplete. Every collector uses its own frozen manifest and append-only
ledger; a transient failure can be retried without repeating completed calls.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from analyze_real_week4_thinking import analyze as analyze_thinking


WEEK4 = Path("results/real_week4_thinking_pilot_v3")
BLIND = Path("results/real_week5_blind_judge_v1")
VALIDATION = Path("results/real_week5_validation_v1")
PIPELINE = Path("results/real_week5_pipeline_v1")
EXPECTED_WEEK4_CALLS = 840
EXPECTED_WEEK4_PAIRS = 420


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def status(stage: str, **details) -> None:
    PIPELINE.mkdir(parents=True, exist_ok=True)
    payload = {"timestamp": now(), "stage": stage, **details}
    (PIPELINE / "status.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload), flush=True)


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open() as fh:
        return sum(bool(line.strip()) for line in fh)


def week4_runner_alive() -> bool:
    result = subprocess.run(["screen", "-ls"], capture_output=True, text=True)
    return "repguard_week4" in result.stdout


def restart_week4_runner() -> None:
    command = (".venv/bin/python run_real_week4_thinking.py "
               "--limit-per-subject 30 --timeout-seconds 600 "
               ">> results/real_week4_thinking_pilot_v3/screen.log 2>&1")
    subprocess.run(["screen", "-dmS", "repguard_week4", "zsh", "-c", command],
                   check=True)


def modal_container_active() -> bool:
    modal_cli = str(Path(sys.executable).with_name("modal"))
    result = subprocess.run([modal_cli, "container", "list"],
                            capture_output=True, text=True, timeout=30, check=True)
    return "ollama-server" in result.stdout


def recover_week4_runner(*, rollover: bool) -> None:
    pattern = (r"^\.venv/bin/python run_real_week4_thinking\.py "
               r"--limit-per-subject 30 --timeout-seconds 600$")
    processes = subprocess.run(["pgrep", "-f", pattern],
                               capture_output=True, text=True)
    for pid_text in processes.stdout.splitlines():
        os.kill(int(pid_text), signal.SIGTERM)
    for _ in range(10):
        remaining = subprocess.run(["pgrep", "-f", pattern],
                                   capture_output=True, text=True)
        if not remaining.stdout.strip():
            break
        time.sleep(1)
    else:
        raise RuntimeError("Old Week 4 runner did not stop; refusing duplicate run")
    subprocess.run(["screen", "-S", "repguard_week4", "-X", "quit"],
                   capture_output=True, text=True)
    if rollover:
        modal_cli = str(Path(sys.executable).with_name("modal"))
        subprocess.run([modal_cli, "app", "rollover", "ollama-server"],
                       check=True, timeout=120)
    restart_week4_runner()


def wait_for_week4(max_wait_hours: float = 24.0) -> None:
    deadline = time.monotonic() + max_wait_hours * 3600
    last_report = -1
    last_restart_n = -1
    no_progress_restarts = 0
    last_recovery_time = 0.0
    recovery_attempts = 0
    while time.monotonic() < deadline:
        ledger = WEEK4 / "predictions.jsonl"
        n = count_jsonl(ledger)
        if n > EXPECTED_WEEK4_CALLS:
            raise RuntimeError(f"Week 4 ledger has too many calls: {n}")
        if n == EXPECTED_WEEK4_CALLS:
            status("week4_ledger_complete", completed_calls=n)
            return
        if n != last_report:
            recovery_attempts = 0
        stale_seconds = time.time() - ledger.stat().st_mtime if ledger.exists() else 0.0
        if (stale_seconds > 600 and
            time.monotonic() - last_recovery_time > 600):
            try:
                container_active = modal_container_active()
            except Exception as exc:
                status("modal_health_check_failed", completed_calls=n,
                       error_type=type(exc).__name__, error=str(exc)[:300])
                time.sleep(60)
                continue
            if not container_active or stale_seconds > 2400:
                recovery_attempts += 1
                if recovery_attempts > 3:
                    raise RuntimeError("Week 4 stalled after three recovery attempts")
                status("recovering_stalled_week4", completed_calls=n,
                       stale_seconds=round(stale_seconds),
                       modal_container_active=container_active,
                       recovery_attempt=recovery_attempts)
                recover_week4_runner(rollover=not container_active)
                last_recovery_time = time.monotonic()
                last_restart_n = n
                time.sleep(60)
                continue
        if not week4_runner_alive():
            no_progress_restarts = (no_progress_restarts + 1
                                    if n == last_restart_n else 0)
            if no_progress_restarts >= 6:
                raise RuntimeError("Week 4 runner repeatedly exits without progress")
            restart_week4_runner()
            last_restart_n = n
            status("week4_runner_restarted", completed_calls=n,
                   no_progress_restarts=no_progress_restarts)
        if n != last_report:
            status("waiting_for_week4", completed_calls=n,
                   expected_calls=EXPECTED_WEEK4_CALLS)
            last_report = n
        time.sleep(60)
    raise TimeoutError("Week 4 did not reach 840 calls within 24 hours")


def run_stage(name: str, command: list[str], *, attempts: int = 3) -> None:
    log_path = PIPELINE / f"{name}.log"
    for attempt in range(1, attempts + 1):
        status(name, attempt=attempt, command=command)
        with log_path.open("a") as log:
            log.write(f"\n=== {now()} attempt {attempt}/{attempts} ===\n")
            log.flush()
            completed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        if completed.returncode == 0:
            status(f"{name}_complete", attempt=attempt)
            return
        status(f"{name}_failed", attempt=attempt, exit_code=completed.returncode,
               log=str(log_path))
        if attempt < attempts:
            time.sleep(120)
    raise RuntimeError(f"{name} failed after {attempts} attempts; see {log_path}")


def main() -> None:
    try:
        wait_for_week4()
        result = analyze_thinking(WEEK4)
        if result["completed_calls"] != EXPECTED_WEEK4_CALLS or result["paired_n"] != EXPECTED_WEEK4_PAIRS:
            raise RuntimeError("Week 4 ledger is not a complete 420-question pair")
        (WEEK4 / "analysis_full.json").write_text(json.dumps(result, indent=2) + "\n")
        status("week4_analyzed", accuracy_pp=result["paired_difference"]["accuracy_pp"],
               ci_pp=result["paired_difference"]["bootstrap_95ci_pp"])

        blind_ok = False
        try:
            run_stage("blind_judge", [sys.executable, "run_real_week5_blind_judge.py",
                                      "--collect", "--limit-per-subject", "20",
                                      "--timeout-seconds", "180"])
            blind_result = subprocess.run(
                [sys.executable, "analyze_real_week5_blind_judge.py"],
                capture_output=True, text=True, check=True)
            blind = json.loads(blind_result.stdout)
            if blind["completed_questions"] != 280 or blind["valid_questions"] != 280:
                raise RuntimeError("Blind judge collection is incomplete or invalid")
            (BLIND / "analysis.json").write_text(json.dumps(blind, indent=2) + "\n")
            blind_ok = True
            status("blind_judge_analyzed",
                   blind_minus_candidate_accuracy=blind["blind_minus_candidate_accuracy"],
                   ci=blind["blind_minus_candidate_cluster_bootstrap_95ci"])
        except Exception as exc:
            status("blind_judge_needs_review", error_type=type(exc).__name__,
                   error=str(exc)[:500])

        thinking = result["variants"]["thinking8192"]
        ci_lo = result["paired_difference"]["bootstrap_95ci_pp"][0]
        if (ci_lo <= 0 or thinking["truncated"] / EXPECTED_WEEK4_PAIRS > .10 or
            thinking["invalid"] / EXPECTED_WEEK4_PAIRS > .10):
            status("validation_skipped_by_frozen_gate", ci_lower_pp=ci_lo,
                   thinking_truncated=thinking["truncated"],
                   thinking_invalid=thinking["invalid"],
                   blind_judge_complete=blind_ok)
            return
        run_stage("dev_validation", [sys.executable, "run_real_week5_validation.py",
                                     "--collect", "--limit-per-subject", "20",
                                     "--timeout-seconds", "600"])
        dev = analyze_thinking(VALIDATION)
        if dev["completed_calls"] != 560 or dev["paired_n"] != 280:
            raise RuntimeError("Week 5 dev validation is incomplete")
        (VALIDATION / "analysis.json").write_text(json.dumps(dev, indent=2) + "\n")
        status("pipeline_complete", blind_judge_complete=blind_ok,
               dev_accuracy_pp=dev["paired_difference"]["accuracy_pp"],
               dev_ci_pp=dev["paired_difference"]["bootstrap_95ci_pp"])
    except Exception as exc:
        status("pipeline_failed", error_type=type(exc).__name__, error=str(exc)[:500])
        raise


if __name__ == "__main__":
    main()
