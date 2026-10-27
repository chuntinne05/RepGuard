"""Verify the real pilot and freeze a sparse-gold replay before submitting it."""
import hashlib
import json
from pathlib import Path
import numpy as np
import run_dart_gain as transport
from routerbench_sparse_core import METHODS, BUDGETS, SEEDS
from routerbench_sparse_pipeline import atomic, digest, verify

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / 'results/routerbench_sparse_v1'
APP = 'repguard-routerbench-sparse-v1'


def prepare():
    from report_routerbench_pilot import load_verified_pilot
    prior = load_verified_pilot()
    packet = {'parent_run_id': prior['packet']['run_id'], 'models': prior['packet']['models'],
              'query_ids': prior['packet']['query_ids'], 'success': prior['gold'].tolist(),
              'judge_scores': prior['probabilities'].tolist(), 'judge_invalid': prior['invalid'].tolist(),
              'folds': (np.arange(48) % 4).tolist(), 'methods': list(METHODS),
              'new_solver_calls': 0, 'new_judge_calls': 0,
              'parent_artifact_sha256': {n: hashlib.sha256((ROOT / 'results/routerbench_pilot_v1/cloud' / n).read_bytes()).hexdigest()
                  for n in ('input_private.json', 'pilot_gold_private.json', 'ledger.json', 'analysis.json', 'judge_environment.json')}}
    packet['cases'] = [{'budget_fraction': b, 'budget': int(np.ceil(b * 216)), 'fold': f,
                        'seed': s, 'rng_seed': 1404 + 1000 * f + s}
                       for b in BUDGETS for f in range(4) for s in SEEDS]
    paths = [ROOT / 'infra/modal' / n for n in ('routerbench_sparse_core.py', 'routerbench_sparse_pipeline.py', 'routerbench_sparse_modal.py')]
    paths += [Path(__file__), ROOT / 'report_routerbench_pilot.py', ROOT / 'run_dart_gain.py',
              ROOT / 'report_routerbench_sparse.py', ROOT / 'tests/test_routerbench_sparse.py',
              ROOT / 'docs/analysis/routerbench_sparse_gold_v1_protocol_2026-10-06.md']
    packet['source_sha256'] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    packet['run_id'] = digest(packet)[:24]
    verify(packet)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    target = OUTPUT / 'packet_private.json'
    if target.exists() and json.loads(target.read_text()) != packet:
        raise ValueError('Refusing changed experiment identity')
    atomic(target, packet)
    print(json.dumps({'run_id': packet['run_id'], 'cases': 240, 'method_selections': 2400,
                      'unique_gold_per_case': [11, 22, 44], 'new_model_calls': 0}))


if __name__ == '__main__':
    transport.OUTPUT = OUTPUT
    transport.APP = APP
    transport.prepare = prepare
    transport.main()
