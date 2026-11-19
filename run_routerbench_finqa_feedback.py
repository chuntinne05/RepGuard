"""Freeze and run the bounded genuine FinQA judge pilot from verified development metadata."""
import hashlib
import json
from pathlib import Path
import run_dart_gain as transport
from routerbench_finqa_feedback_core import select_queries
from routerbench_finqa_feedback_pipeline import atomic, digest, verify, validate

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / 'results/routerbench_finqa_feedback_v1'
APP = 'repguard-routerbench-finqa-feedback-v1'


def prepare():
    previous = ROOT / 'results/routerbench_headroom_v1/cloud'
    headroom = json.loads((previous / 'input_private.json').read_text())
    old_status = json.loads((previous / 'status.json').read_text())
    old_analysis = json.loads((previous / 'analysis.json').read_text()); validate(old_analysis)
    if not (headroom['run_id'] == old_status['run_id'] == old_analysis['run_id']):
        raise ValueError('Mixed headroom parent run')
    if headroom['run_id'] != '58bcf5179974f10ebe94c405' or old_status['state'] != 'completed_development_headroom_review_required':
        raise ValueError('Expected completed frozen headroom development')
    spec = headroom['datasets']['finqa/test']
    queries = select_queries(spec['query_ids'])
    packet = {'parent_headroom_run_id': headroom['run_id'],
              'parent_input_sha256': hashlib.sha256((previous / 'input_private.json').read_bytes()).hexdigest(),
              'parent_analysis_sha256': hashlib.sha256((previous / 'analysis.json').read_bytes()).hexdigest(),
              'archive_sha256': headroom['archive_sha256'], 'archive_bytes': headroom['archive_bytes'],
              'models': spec['models'], 'query_ids': queries, 'members': spec['members'],
              'member_metadata_sha256': spec['member_metadata_sha256'],
              'positions': {m: {q: spec['positions'][m][q] for q in queries} for m in spec['models']},
              'total_cases': 960, 'max_attempts_per_case': 2,
              'selection_reads_outcomes': False, 'new_solver_calls': 0}
    paths = [ROOT / 'infra/modal' / n for n in ('routerbench_finqa_feedback_core.py',
             'routerbench_finqa_feedback_pipeline.py', 'routerbench_finqa_feedback_modal.py',
             'routerbench_finqa_preflight_modal.py', 'routerbench_intake_core.py')]
    paths += [Path(__file__), ROOT / 'report_routerbench_finqa_feedback.py',
              ROOT / 'tests/test_routerbench_finqa_feedback.py', ROOT / 'run_dart_gain.py',
              ROOT / 'docs/analysis/routerbench_finqa_feedback_v1_protocol_2026-10-06.md']
    packet['source_sha256'] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    packet['run_id'] = digest(packet)[:24]
    verify(packet)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    target = OUTPUT / 'packet_private.json'
    if target.exists() and json.loads(target.read_text()) != packet:
        raise ValueError('Prepared FinQA pilot identity differs')
    atomic(target, packet)
    print(json.dumps({'run_id': packet['run_id'], 'questions': 48,
                      'models': 20, 'planned_judgments': 960, 'new_solver_calls': 0}))


if __name__ == '__main__':
    transport.OUTPUT = OUTPUT
    transport.APP = APP
    transport.prepare = prepare
    transport.main()
