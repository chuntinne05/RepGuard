"""Prepare public normal packet; submit detached cloud job; inspect or fetch."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'infra/modal'))
from neural_pipeline import digest, atomic

OUTPUT = ROOT/'results/dart_neural_v1'
APP_NAME = 'repguard-neural-p0p1-v1'


def prepare(data_root):
    import numpy as np
    manifest = json.loads((ROOT/'docs/analysis/dart_leaderboard_pool_manifest_2026-10-04.json').read_text())
    matrix = json.loads((ROOT/'results/dart_leaderboard_v1/outcomes_private.json').read_text())
    ids = matrix['task_ids']
    assert len(ids) == 168 and len(set(ids)) == 168
    assert matrix['agents'] == [a['name'] for a in manifest['agents']]
    assert set(ids) == set((data_root/'datasets/test_normal.txt').read_text().splitlines())
    y = np.array(matrix['success'])
    assert y.shape == (168, 14) and np.isin(y, [0,1]).all()
    texts = []
    for task in ids:
        spec = json.loads((data_root/'tasks'/task/'specs.json').read_text())
        assert spec['db_version'] == '0.1.0'
        texts.append(spec['instruction'])
    groups = [t.rsplit('_', 1)[0] for t in ids]
    folds = [manifest['normal_outer_fold_by_generator'][g] for g in groups]
    audits = []
    for line in (ROOT/'results/dart_audit_judge_v1/audit_trace_private.jsonl').read_text().splitlines():
        row = json.loads(line)
        if row['method'] != 'UniformAuditGlobal':
            continue
        train = np.flatnonzero(np.array(folds) != row['fold'])
        test = np.flatnonzero(np.array(folds) == row['fold'])
        assert [ids[i] for i in train] == row['training_ids']
        assert [ids[i] for i in test] == row['test_ids']
        idx = row['audit_indices']
        assert len(idx) == len(set(idx)) == row['total_audits']
        assert min(idx) >= 0 and max(idx) < len(train)*14
        audits.append({k: row[k] for k in ('fold','seed','budget_fraction','audit_indices','test_agent_choices')})
    assert len(audits) == 300
    assert len({(a['fold'], a['seed'], a['budget_fraction']) for a in audits}) == 300
    controls = {}
    uniform = json.loads((ROOT/'results/dart_audit_judge_v1/predictions_private.json').read_text())
    paired = json.loads((ROOT/'results/dart_paired_judge_v1/predictions_private.json').read_text())
    assert uniform['task_ids'] == paired['task_ids'] == ids
    for b in ('0.05', '0.1', '0.2'):
        controls[b] = {'UniformAuditGlobal': uniform['predictions'][b]['UniformAuditGlobal'],
                       'PairedGlobal': paired['predictions'][b]['PairedGlobal']}
    paths = [ROOT/'infra/modal'/n for n in ('neural_core.py','neural_pipeline.py','neural_smoke.py','neural_modal.py')]
    paths += [Path(__file__), ROOT/'docs/analysis/dart_neural_p0_p1_protocol_2026-10-05.md']
    packet = {'task_ids': ids, 'agents': matrix['agents'], 'success': matrix['success'], 'texts': texts,
              'groups': groups, 'folds': folds, 'audits': audits, 'controls': controls,
              'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
              'pool_manifest_sha256': digest(manifest), 'scope': 'public AppWorld 0.1.0 normal only'}
    packet['run_id'] = digest(packet)[:24]
    OUTPUT.mkdir(parents=True, exist_ok=True)
    atomic(OUTPUT/'packet_private.json', packet)
    print(json.dumps({'run_id': packet['run_id'], 'tasks': len(ids), 'audits': len(audits), 'packet_bytes': (OUTPUT/'packet_private.json').stat().st_size}))


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('action', choices=['prepare','submit','status','fetch'])
    parser.add_argument('--data-root', type=Path, default=Path('/private/tmp/repguard_appworld_data010/data'))
    parser.add_argument('--resume', action='store_true', help='Resubmit only after the prior cloud call has failed')
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare(args.data_root)
        return
    import modal
    packet = json.loads((OUTPUT/'packet_private.json').read_text())
    run_id = packet['run_id']
    if args.action == 'submit':
        receipt = OUTPUT/'receipt.json'
        if receipt.exists():
            old = json.loads(receipt.read_text())
            if old['run_id'] != run_id:
                raise ValueError('Existing receipt belongs to another run')
            # Do not blindly duplicate a live or completed cloud invocation.
            try:
                result = modal.FunctionCall.from_id(old['call_id']).get(timeout=0)
                print(json.dumps(result)); return
            except TimeoutError:
                print(json.dumps({'already_submitted': old})); return
            except Exception:
                if not args.resume:
                    raise
                state = modal.Function.from_name(APP_NAME,'inspect_run').remote(run_id)
                if state['state'] in ('stopped_p0_gate', 'completed_p1_review_required'):
                    print(json.dumps(state)); return
                # Same immutable input and source; worker skips committed cases.
        call = modal.Function.from_name(APP_NAME, 'worker').spawn(packet)
        value = {'app': APP_NAME, 'run_id': run_id, 'call_id': call.object_id}
        atomic(receipt, value)
        print(json.dumps(value))
    elif args.action == 'status':
        print(json.dumps(modal.Function.from_name(APP_NAME,'inspect_run').remote(run_id), indent=2))
    else:
        import io, zipfile
        data = modal.Function.from_name(APP_NAME,'inspect_run').remote(run_id, archive=True)
        target = OUTPUT/'cloud'
        target.mkdir(exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for name in z.namelist():
                if Path(name).name != name or not name.endswith('.json'):
                    raise ValueError('Unexpected artifact path')
            z.extractall(target)
        print(json.dumps({'artifacts': len(z.namelist()), 'directory': str(target)}))


if __name__ == '__main__':
    main()
