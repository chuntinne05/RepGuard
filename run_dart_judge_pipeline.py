"""Bounded real-inference -> fixed quality gate -> complete replay controller."""
from __future__ import annotations

import fcntl
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from run_dart_modal_judge import atomic_json, now

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / 'results/dart_modal_judge_v1'
REPLAY = ROOT / 'results/dart_audit_judge_v1'


def status(state: str, **fields) -> None:
    atomic_json(OUTPUT / 'pipeline_status.json', {'state': state, 'updated_at': now(),
                'pid': os.getpid(), **fields})


def command(script: str, *args: str) -> int:
    with (OUTPUT / 'pipeline.log').open('a') as log:
        return subprocess.call([sys.executable, '-u', script, *args], cwd=ROOT,
                               stdout=log, stderr=subprocess.STDOUT,
                               env={**os.environ, 'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1'})


def collect(limit: int) -> None:
    for attempt in range(1, 4):
        status('collecting', target=limit, collector_attempt=attempt)
        if command('run_dart_modal_judge.py', '--limit', str(limit)) == 0:
            return
        if attempt < 3:
            time.sleep(10)
    raise RuntimeError('Collector exhausted three resumable attempts')


def run() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / 'pipeline.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        collect(168)
        status('analyzing_pilot')
        if command('analyze_dart_modal_judge.py'):
            raise RuntimeError('Quality analysis failed')
        quality = json.loads((OUTPUT / 'pilot_quality.json').read_text())
        if not quality['gate_pass']:
            if command('report_dart_judge_pipeline.py'):
                raise RuntimeError('Final quality report failed')
            status('stopped_quality_gate', completed=168, gate_pass=False)
            return
        collect(2352)
        status('audited_routing_replay', completed_judge_records=2352)
        # Replay is intentionally not silently restarted over partial traces.
        if (REPLAY / 'status.json').exists():
            previous = json.loads((REPLAY / 'status.json').read_text())
            if previous['state'] != 'completed':
                raise RuntimeError('Partial replay requires inspection; refusing overwrite')
        elif command('run_dart_audit_pilot.py', '--judge-dir', str(OUTPUT),
                     '--output', str(REPLAY), '--primary-method', 'DARTContrast'):
            raise RuntimeError('Audited replay failed')
        result = json.loads((REPLAY / 'analysis.json').read_text())
        if command('report_dart_judge_pipeline.py'):
            raise RuntimeError('Final routing report failed')
        status('completed', judge_records=2352,
               exploratory_method_gate_pass=result['exploratory_method_gate_pass'],
               deployment_certified=False, independent_confirmation=False,
               next_stage='scientific_review_no_automatic_holdout_access')


if __name__ == '__main__':
    try:
        run()
    except BlockingIOError:
        raise
    except Exception as exc:
        status('pipeline_failed', error_type=type(exc).__name__, error=str(exc))
        raise
