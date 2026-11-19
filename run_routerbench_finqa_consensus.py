"""Freeze and control the detached FinQA exact-answer consensus replay."""
import hashlib
import json
from pathlib import Path
import sys

import run_dart_gain as transport

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'infra/modal'))
from routerbench_finqa_consensus_core import select_queries  # noqa: E402
from routerbench_finqa_consensus_pipeline import atomic, digest, verify  # noqa: E402

OUTPUT = ROOT / 'results/routerbench_finqa_consensus_v1'
APP = 'repguard-routerbench-finqa-consensus-v1'


def prepare():
    prior = ROOT / 'results/routerbench_headroom_v1/cloud'
    parent = json.loads((prior / 'input_private.json').read_text())
    parent_status = json.loads((prior / 'status.json').read_text())
    judge_root = ROOT / 'results/routerbench_finqa_feedback_v1'
    old = json.loads((judge_root / 'packet_private.json').read_text())
    old_status = json.loads((judge_root / 'cloud/status.json').read_text())
    if parent['run_id'] != '58bcf5179974f10ebe94c405' or parent_status['state'] != 'completed_development_headroom_review_required':
        raise ValueError('Expected completed headroom development')
    if old['run_id'] != '0fad63edd346eb0591fd99e1' or old_status['state'] != 'completed_pilot_review_required' or old_status['expansion_signal_pass']:
        raise ValueError('Expected completed negative judge pilot')
    spec = parent['datasets']['finqa/test']
    queries = select_queries(spec['query_ids'], old['query_ids'])
    packet = {'parent_headroom_run_id': parent['run_id'], 'parent_judge_run_id': old['run_id'],
              'parent_input_sha256': hashlib.sha256((prior / 'input_private.json').read_bytes()).hexdigest(),
              'parent_analysis_sha256': hashlib.sha256((prior / 'analysis.json').read_bytes()).hexdigest(),
              'old_pilot_query_ids': old['query_ids'],
              'archive_sha256': parent['archive_sha256'], 'archive_bytes': parent['archive_bytes'],
              'models': spec['models'], 'query_ids': queries, 'members': spec['members'],
              'positions': {model: {q: spec['positions'][model][q] for q in queries}
                            for model in spec['models']},
              'new_solver_calls': 0, 'new_judge_calls': 0,
              'selection_reads_outcomes': False}
    files = [ROOT / 'infra/modal' / name for name in (
        'routerbench_finqa_consensus_core.py', 'routerbench_finqa_consensus_pipeline.py',
        'routerbench_finqa_consensus_modal.py', 'routerbench_finqa_feedback_core.py',
        'routerbench_intake_core.py')]
    files += [Path(__file__), ROOT / 'report_routerbench_finqa_consensus.py',
              ROOT / 'docs/analysis/routerbench_finqa_consensus_v1_protocol_2026-10-06.md']
    packet['source_sha256'] = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                               for path in files}
    packet['run_id'] = digest(packet)[:24]
    verify(packet)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    target = OUTPUT / 'packet_private.json'
    if target.exists() and json.loads(target.read_text()) != packet:
        raise ValueError('Refusing to overwrite changed consensus packet')
    atomic(target, packet)
    print(json.dumps({'run_id': packet['run_id'], 'questions': 48, 'models': 20,
                      'archived_predictions': 960, 'new_model_calls': 0}))


if __name__ == '__main__':
    transport.OUTPUT = OUTPUT
    transport.APP = APP
    transport.prepare = prepare
    transport.main()
