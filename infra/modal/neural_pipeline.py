"""Resumable cloud pipeline. All artifacts live on a committed Modal Volume."""
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from neural_core import HEADS, route_case, observed_gold, cluster_ci

ENCODER = 'sentence-transformers/all-MiniLM-L6-v2'
REVISION = '1110a243fdf4706b3f48f1d95db1a4f5529b4d41'


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


def atomic(path, obj):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(obj, indent=2, allow_nan=False))
    temp.replace(path)


def ensure_identity(root, packet):
    path = root / 'input_private.json'
    if path.exists() and json.loads(path.read_text()) != packet:
        raise ValueError('Checkpoint identity mismatch')
    if not path.exists():
        atomic(path, packet)


def verify_packet(packet):
    identity = {k: v for k, v in packet.items() if k != 'run_id'}
    if digest(identity)[:24] != packet['run_id']:
        raise ValueError('Input hash mismatch')
    for name in ('neural_core.py', 'neural_pipeline.py', 'neural_smoke.py'):
        actual = hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
        if actual != packet['source_sha256']['infra/modal/'+name]:
            raise ValueError('Deployed source differs from prepared packet: '+name)


def embeddings(texts, progress):
    import torch
    from transformers import AutoTokenizer, AutoModel
    torch.set_num_threads(2)
    tokenizer = AutoTokenizer.from_pretrained(ENCODER, revision=REVISION)
    model = AutoModel.from_pretrained(ENCODER, revision=REVISION).eval()
    vectors, counts = [], []
    for i, text in enumerate(texts):
        tokens = tokenizer.encode(text, add_special_tokens=False, truncation=False)
        if not tokens:
            raise ValueError('Empty instruction')
        chunks = [tokens[j:j+240] for j in range(0, len(tokens), 240)]
        pooled = []
        for chunk in chunks:
            inputs = tokenizer.prepare_for_model(chunk, return_tensors='pt', truncation=False)
            inputs = {k: v.unsqueeze(0) if v.ndim == 1 else v for k, v in inputs.items()}
            with torch.no_grad():
                h = model(**inputs).last_hidden_state
                mask = inputs['attention_mask'].unsqueeze(-1)
                v = (h*mask).sum(1)/mask.sum(1)
                pooled.append(torch.nn.functional.normalize(v, dim=1).numpy()[0])
        vector = np.average(pooled, axis=0, weights=[len(c) for c in chunks])
        vectors.append(vector/max(np.linalg.norm(vector), 1e-12))
        counts.append({'tokens': len(tokens), 'chunks': len(chunks)})
        if (i+1) % 12 == 0:
            progress(i+1)
    return np.array(vectors), counts


def summarize(records, y, groups, controls=None):
    methods = ('Global', *HEADS, 'Selected')
    seeds = max(r['seed'] for r in records)+1
    values = {h: np.full((seeds, len(y)), np.nan) for h in methods}
    for row in records:
        idx = np.array(row['test_indices'])
        for h, choices in row['actions'].items():
            values[h][row['seed'], idx] = y[idx, choices]
    if any(not np.isfinite(v).all() for v in values.values()):
        raise ValueError('Incomplete evaluation')
    if controls:
        for h, v in controls.items():
            values[h] = np.array(v, dtype=float)
        if not np.array_equal(values['Global'], values['UniformAuditGlobal']):
            raise ValueError('Global outcome mismatch with saved control')
    references = ('UniformAuditGlobal', 'PairedGlobal') if controls else ('Global',)
    contrasts = {}
    for h in methods:
        contrasts[h] = {}
        for c in references:
            delta = (values[h]-values[c]).mean(0)
            contrasts[h][c] = {'difference': float(delta.mean()), 'ci95': cluster_ci(delta, groups),
                'mean_rescues': float(((values[h] == 1) & (values[c] == 0)).sum(1).mean()),
                'mean_harms': float(((values[h] == 0) & (values[c] == 1)).sum(1).mean())}
    return {'methods': {h: {'mean_correct': float(v.sum(1).mean()), 'accuracy': float(v.mean())} for h,v in values.items()},
            'contrasts': contrasts, 'gate_pass': all(contrasts['Selected'][c]['ci95'][0] > 0 for c in references),
            'scope': 'exploratory public normal; generator bootstrap after seed averaging; no independent confirmation'}


def run(packet, root, commit):
    import torch, transformers
    verify_packet(packet)
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    ensure_identity(root, packet)
    status_path = root / 'status.json'
    def status(state, **kw):
        atomic(status_path, {'state': state, 'run_id': packet['run_id'],
                            'updated_at': datetime.now(timezone.utc).isoformat(), **kw})
        commit()
        print(json.dumps(json.loads(status_path.read_text())), flush=True)
    if status_path.exists() and json.loads(status_path.read_text())['state'] in ('stopped_p0_gate', 'completed_p1_review_required'):
        return json.loads(status_path.read_text())
    try:
        atomic(root/'environment.json', {'python': platform.python_version(), 'numpy': np.__version__,
               'torch': torch.__version__, 'transformers': transformers.__version__, 'encoder': ENCODER, 'revision': REVISION})
        from neural_smoke import smoke
        status('self_test', completed=0, total=5)
        atomic(root/'self_test.json', smoke())
        feature_path = root/'embeddings_private.json'
        if not feature_path.exists():
            status('encoding', completed=0, total=len(packet['texts']))
            x, counts = embeddings(packet['texts'], lambda n: status('encoding', completed=n, total=len(packet['texts'])))
            atomic(feature_path, {'embeddings': x.tolist(), 'counts': counts})
            commit()
        x = np.array(json.loads(feature_path.read_text())['embeddings'])
        y = np.array(packet['success'], dtype=float)
        folds = np.array(packet['folds'])
        groups = packet['groups']
        def case(stage, fold, seed=0, audit=None):
            key = f'{stage}_fold{fold}_seed{seed}'
            path = root/(key+'.json')
            if path.exists():
                row = json.loads(path.read_text())
                if row['run_id'] != packet['run_id'] or row['case'] != key:
                    raise ValueError('Invalid case checkpoint')
                return row
            train, test = np.flatnonzero(folds != fold), np.flatnonzero(folds == fold)
            obs = y[train].copy() if audit is None else observed_gold(y[train], audit['audit_indices'])
            completed = len(list(root.glob(stage+'_fold*.json')))
            total = 5 if stage == 'p0' else 100
            def progress(detail):
                status('training', stage=stage, case=key, detail=detail, completed=completed, total=total)
            actions, trace = route_case(x[train], obs, x[test], [groups[i] for i in train], progress)
            if audit is not None and actions['Global'] != audit['test_agent_choices']:
                raise ValueError('UniformAuditGlobal action mismatch')
            row = {'run_id': packet['run_id'], 'case': key, 'fold': fold, 'seed': seed,
                   'test_indices': test.tolist(), 'actions': actions, 'trace': trace,
                   'audits': int(np.isfinite(obs).sum())}
            atomic(path, row)
            status('case_completed', stage=stage, case=key, completed=completed+1, total=total)
            return row
        records = [case('p0', fold) for fold in range(5)]
        p0 = summarize(records, y, groups)
        atomic(root/'p0_analysis.json', p0)
        commit()
        if not p0['gate_pass']:
            status('stopped_p0_gate', completed=5, total=5, reason='Selected minus Global CI lower endpoint is not positive', p0=p0)
            return json.loads(status_path.read_text())
        analyses = {}
        for budget in ('0.05', '0.1', '0.2'):
            rows = [r for r in packet['audits'] if str(r['budget_fraction']) == budget]
            records = [case('p1_'+budget, r['fold'], r['seed'], r) for r in rows]
            analyses[budget] = summarize(records, y, groups, packet['controls'][budget])
            atomic(root/('p1_'+budget+'_analysis.json'), analyses[budget])
            commit()
        atomic(root/'p1_analysis.json', analyses)
        status('completed_p1_review_required', completed=300, total=300, primary_gate_pass=analyses['0.1']['gate_pass'])
        return json.loads(status_path.read_text())
    except Exception as e:
        status('pipeline_failed', error=repr(e))
        raise
