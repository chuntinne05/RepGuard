"""Wait for the existing frozen run, then execute the locked follow-up analyses."""
from __future__ import annotations

import fcntl
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from run_dart_modal_judge import atomic_json, now

ROOT=Path(__file__).resolve().parent
OUTPUT=ROOT/'results/dart_followup_v1'


def status(state,**fields):
    atomic_json(OUTPUT/'status.json',{'state':state,'updated_at':now(),'pid':os.getpid(),**fields})


def command(script,*args):
    with (OUTPUT/'runner.log').open('a') as log:
        subprocess.run([sys.executable,'-u',script,*args],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,
                       env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'},check=True)


def main():
    OUTPUT.mkdir(parents=True,exist_ok=True)
    with (OUTPUT/'run.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        deadline=time.monotonic()+4*3600
        while True:
            pipeline=json.loads((ROOT/'results/dart_modal_judge_v1/pipeline_status.json').read_text())
            if pipeline['state']=='completed':
                break
            if pipeline['state'] in ('pipeline_failed','stopped_quality_gate'):
                status('stopped_upstream',upstream_state=pipeline['state'])
                return
            if time.monotonic()>deadline:
                raise TimeoutError('Four-hour upstream wait expired')
            collector=json.loads((ROOT/'results/dart_modal_judge_v1/status.json').read_text())
            status('waiting_for_frozen_pipeline',completed_judge_records=collector['completed'],
                   collector_updated_at=collector['updated_at'])
            time.sleep(15)
        status('postrun_diagnostics')
        command('analyze_dart_postrun.py')
        paired=ROOT/'results/dart_paired_judge_v1'
        if paired.exists():
            if json.loads((paired/'status.json').read_text())['state']!='completed':
                raise RuntimeError('Inspect partial paired run; no automatic overwrite')
        else:
            status('paired_judge_ablation')
            command('run_dart_paired_ablation.py','--reference','results/dart_audit_judge_v1',
                    '--output','results/dart_paired_judge_v1')
        status('reporting')
        command('report_dart_followup.py')
        status('completed',report='docs/analysis/dart_followup_report_2026-10-04.md',
               new_inference_calls=0,independent_confirmation=False)


if __name__=='__main__':
    try:
        main()
    except BlockingIOError:
        raise
    except Exception as exc:
        status('pipeline_failed',error_type=type(exc).__name__,error=str(exc))
        raise
