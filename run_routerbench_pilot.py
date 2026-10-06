"""Prepare only from verified outcome-free metadata; run bounded real judge pilot."""
import hashlib
import json
from pathlib import Path
import run_dart_gain as transport
from routerbench_intake_core import digest
from routerbench_intake_pipeline import atomic
from routerbench_pilot_core import MODELS, select_queries

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / 'results/routerbench_pilot_v1'


def prepare():
    import modal
    volume = modal.Volume.from_name('repguard-routerbench-intake-checkpoints-v1')
    prior = ROOT / 'results/routerbench_intake_v2/cloud'
    old = json.loads((prior / 'input_private.json').read_text())
    inventory = json.loads((prior / 'inventory.json').read_text())
    ledger = json.loads((prior / 'ledger.json').read_text())
    assert json.loads((prior / 'status.json').read_text())['state'] == 'completed_inventory'
    assert inventory['run_id'] == old['run_id'] == 'c387f6364d2266bf1bf370a9'
    members, sets, hashes = {}, [], {}
    for model in MODELS:
        files = inventory['datasets']['math500/test']['models'][model]['files']
        # Actual inventory has one file/model. Refuse ambiguity rather than selecting by outcome.
        if len(files) != 1:
            raise ValueError('Ambiguous execution run for ' + model)
        member = files[0]; entry = ledger[member]
        path = prior / entry['file']
        if not path.exists():
            path.write_bytes(b''.join(volume.read_file('/runs/' + old['run_id'] + '/' + entry['file'])))
        row = json.loads(path.read_text())
        assert digest({k: v for k, v in row.items() if k != 'artifact_sha256'}) == row['artifact_sha256'] == entry['sha256']
        assert row['run_id'] == old['run_id'] and row['member'] == member and row['model'] == model
        members[model] = member; hashes[model] = row['artifact_sha256']
        sets.append({r['query_sha256'] for r in row['records']})
    common = set.intersection(*sets)
    packet = {'parent_intake_run_id': old['run_id'], 'archive_sha256': old['archive_sha256'],
              'members': members, 'member_metadata_sha256': hashes, 'models': list(MODELS),
              'query_ids': select_queries(common), 'common_queries': len(common),
              'selection_reads_outcomes': False, 'max_attempts_per_case': 2, 'total_cases': 288}
    paths = [ROOT / 'infra/modal' / n for n in ('routerbench_pilot_core.py', 'routerbench_pilot_pipeline.py',
             'routerbench_pilot_modal.py', 'routerbench_intake_core.py', 'routerbench_intake_pipeline.py', 'ollama_modal_recovery.py')]
    paths += [Path(__file__), ROOT / 'run_dart_gain.py', ROOT / 'docs/analysis/routerbench_pilot_protocol_2026-10-06.md']
    packet['source_sha256'] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    packet['run_id'] = digest(packet)[:24]
    OUTPUT.mkdir(parents=True, exist_ok=True); path = OUTPUT / 'packet_private.json'
    if path.exists() and json.loads(path.read_text()) != packet:
        raise ValueError('Prepared pilot identity differs')
    atomic(path, packet)
    print(json.dumps({'run_id': packet['run_id'], 'common_queries': len(common), 'pilot_questions': 48, 'planned_judgments': 288}))


if __name__ == '__main__':
    transport.OUTPUT = OUTPUT; transport.APP = 'repguard-routerbench-pilot-v1'; transport.prepare = prepare
    transport.main()
