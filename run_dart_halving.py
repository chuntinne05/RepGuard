"""Prepare frozen-candidate comparison with budget-adaptive gold-only baselines."""
import hashlib
import json
from pathlib import Path
import numpy as np
import run_dart_gain as transport
from neural_pipeline import atomic, digest
from paired_history_pipeline import verify, validate

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / 'results/dart_halving_v1'


def prepare():
    prior = ROOT / 'results/dart_paired_history_v1/cloud'
    old = json.loads((prior / 'input_private.json').read_text()); verify(old)
    assert json.loads((prior / 'status.json').read_text())['completed'] == 300
    ledger = json.loads((prior / 'ledger.json').read_text())
    packet = {k: old[k] for k in ('task_ids', 'agents', 'success', 'groups', 'folds')}
    packet['parent_run_id'] = old['run_id']
    packet['parent_ledger_sha256'] = hashlib.sha256((prior / 'ledger.json').read_bytes()).hexdigest()
    packet['cases'] = []
    for a in old['audits']:
        key = f"{a['budget_fraction']}_fold{a['fold']}_seed{a['seed']}"
        seed = int(hashlib.sha256(('dart-halving-v1:' + key).encode()).hexdigest()[:16], 16)
        packet['cases'].append({'fold': a['fold'], 'seed': a['seed'], 'budget_fraction': a['budget_fraction'],
                                'budget': len(a['audit_indices']), 'rng_seed': seed})
    assert len(packet['cases']) == len({(c['fold'], c['seed'], c['budget_fraction']) for c in packet['cases']}) == 300
    packet['controls'] = {}
    y = np.array(old['success']); folds = np.array(old['folds'])
    for b in ('0.05', '0.1', '0.2'):
        controls = {k: old['controls'][b][k] for k in ('PairedGlobal', 'UniformAuditGlobal', 'TunedFactorRidge')}
        values = np.full((20, len(y)), np.nan)
        for path in prior.glob('case_' + b + '_*.json'):
            row = json.loads(path.read_text()); validate(row)
            assert row['run_id'] == old['run_id'] and ledger[row['case']] == row['artifact_sha256']
            te = np.flatnonzero(folds == row['fold'])
            assert te.tolist() == row['test_indices']
            values[row['seed'], te] = y[te, row['agent_choices']['CFJudgeFactor']]
        assert np.isfinite(values).all()
        controls['FrozenPairedCFJudgeFactor'] = values.tolist()
        packet['controls'][b] = controls
    paths = [ROOT / 'infra/modal' / n for n in ('halving_core.py', 'halving_pipeline.py', 'halving_modal.py', 'neural_core.py', 'neural_pipeline.py')]
    paths += [Path(__file__), ROOT / 'run_dart_gain.py', ROOT / 'docs/analysis/dart_halving_v1_protocol_2026-10-05.md']
    packet['source_sha256'] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    packet['run_id'] = digest(packet)[:24]
    OUTPUT.mkdir(parents=True, exist_ok=True)
    target = OUTPUT / 'packet_private.json'
    if target.exists() and json.loads(target.read_text()) != packet:
        raise ValueError('Existing prepared experiment differs')
    atomic(target, packet)
    print(json.dumps({'run_id': packet['run_id'], 'cases': 300, 'methods_per_case': 2}))


if __name__ == '__main__':
    transport.OUTPUT = OUTPUT; transport.APP = 'repguard-halving-v1'; transport.prepare = prepare
    transport.main()
