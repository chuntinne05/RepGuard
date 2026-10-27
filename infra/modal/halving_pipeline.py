"""Bounded detached baseline audit. Frozen candidate predictions are comparators only."""
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from halving_core import METHODS, select
from neural_core import cluster_ci
from neural_pipeline import atomic, digest, ensure_identity


def verify(packet):
    if digest({k: v for k, v in packet.items() if k != 'run_id'})[:24] != packet['run_id']:
        raise ValueError('Input identity mismatch')
    for name in ('halving_core.py', 'halving_pipeline.py', 'neural_core.py', 'neural_pipeline.py'):
        if hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() != packet['source_sha256']['infra/modal/' + name]:
            raise ValueError('Source mismatch: ' + name)


def validate(row):
    if digest({k: v for k, v in row.items() if k != 'artifact_sha256'}) != row['artifact_sha256']:
        raise ValueError('Checkpoint checksum mismatch')


def summarize(rows, packet, budget):
    y = np.array(packet['success'])
    values = {m: np.full((20, len(y)), np.nan) for m in METHODS}
    for row in rows:
        te = np.array(row['test_indices'])
        for m in METHODS:
            if np.isfinite(values[m][row['seed'], te]).any():
                raise ValueError('Duplicate evaluation')
            values[m][row['seed'], te] = y[te, row['methods'][m]['agent']]
    if any(not np.isfinite(v).all() for v in values.values()):
        raise ValueError('Incomplete evaluation')
    values.update({m: np.array(v) for m, v in packet['controls'][budget].items()})
    candidate = values['FrozenPairedCFJudgeFactor']
    contrasts = {}
    for m, v in values.items():
        if m == 'FrozenPairedCFJudgeFactor':
            continue
        delta = (candidate - v).mean(0)
        contrasts[m] = {'difference': float(delta.mean()), 'ci95': cluster_ci(delta, packet['groups']),
                        'rescues': float(((candidate == 1) & (v == 0)).sum(1).mean()),
                        'harms': float(((candidate == 0) & (v == 1)).sum(1).mean())}
    return {'methods': {m: {'mean_correct': float(v.sum(1).mean()), 'accuracy': float(v.mean())} for m, v in values.items()},
            'candidate_contrasts': contrasts,
            'new_baseline_signal_pass': all(contrasts[m]['ci95'][0] > 0 for m in METHODS),
            'scope': 'Development stress test; does not replace original failed primary gate'}


def run(packet, root, commit):
    verify(packet)
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    ensure_identity(root, packet)
    sp = root / 'status.json'
    ledger = {}
    for path in root.glob('case_*.json'):
        row = json.loads(path.read_text()); validate(row)
        if row['run_id'] != packet['run_id'] or path.stem[5:] != row['case']:
            raise ValueError('Mixed checkpoint identity')
        ledger[row['case']] = row['artifact_sha256']
    if sp.exists() and json.loads(sp.read_text())['state'] == 'completed_review_required':
        if len(ledger) != 300:
            raise ValueError('Incomplete terminal state')
        return json.loads(sp.read_text())

    def status(state, **fields):
        atomic(root / 'ledger.json', ledger)
        atomic(sp, {'run_id': packet['run_id'], 'state': state, 'completed': len(ledger), 'total': 300,
                    'updated_at': datetime.now(timezone.utc).isoformat(), **fields})
        commit(); print(sp.read_text(), flush=True)

    try:
        atomic(root / 'environment.json', {'python': platform.python_version(), 'numpy': np.__version__})
        y = np.array(packet['success']); folds = np.array(packet['folds'])
        analyses = {}
        status('running')
        for b in ('0.05', '0.1', '0.2'):
            rows = []
            for case in sorted([a for a in packet['cases'] if str(a['budget_fraction']) == b], key=lambda a: (a['fold'], a['seed'])):
                key = f"{b}_fold{case['fold']}_seed{case['seed']}"
                path = root / ('case_' + key + '.json')
                if path.exists():
                    row = json.loads(path.read_text()); validate(row)
                else:
                    tr, te = np.flatnonzero(folds != case['fold']), np.flatnonzero(folds == case['fold'])
                    if set(np.array(packet['groups'])[tr]) & set(np.array(packet['groups'])[te]):
                        raise ValueError('Generator leakage')
                    # Only this callback exposes paid TRAIN cells to the algorithm.
                    train = y[tr].copy()
                    methods = {m: select(len(tr), y.shape[1], case['budget'], case['rng_seed'], m == 'PairedSH',
                                          lambda i, a: train[i, a]) for m in METHODS}
                    row = {'run_id': packet['run_id'], 'case': key, 'fold': case['fold'], 'seed': case['seed'],
                           'budget': case['budget'], 'test_indices': te.tolist(), 'methods': methods}
                    row['artifact_sha256'] = digest(row)
                    atomic(path, row); ledger[key] = row['artifact_sha256']
                    if len(ledger) % 25 == 0:
                        status('running', case=key, budget=b)
                rows.append(row)
            analyses[b] = summarize(rows, packet, b)
            atomic(root / ('analysis_' + b + '.json'), analyses[b]); status('budget_completed', budget=b)
        atomic(root / 'analysis.json', analyses)
        status('completed_review_required', new_baseline_signal_pass=analyses['0.1']['new_baseline_signal_pass'],
               primary=analyses['0.1']['methods'])
        return json.loads(sp.read_text())
    except Exception as error:
        status('pipeline_failed', error=repr(error)); raise
