"""Prepare a frozen prompt-only grouping packet from verified intake metadata."""
import hashlib
import json
from pathlib import Path
import run_dart_gain as transport
from routerbench_prompt_groups_pipeline import atomic, digest, validate, verify

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / 'results/routerbench_prompt_groups_v1'
APP = 'repguard-routerbench-prompt-groups-v1'


def prepare():
    intake = ROOT / 'results/routerbench_intake_v2/cloud'
    pilot = ROOT / 'results/routerbench_pilot_v1/cloud'
    old = json.loads((intake / 'input_private.json').read_text())
    inventory = json.loads((intake / 'inventory.json').read_text())
    assert json.loads((intake / 'status.json').read_text())['state'] == 'completed_inventory'
    assert old['run_id'] == inventory['run_id'] == 'c387f6364d2266bf1bf370a9'
    prior = json.loads((pilot / 'input_private.json').read_text())
    assert prior['run_id'] == 'bad5a513bd5d227711eb1e0d'
    member = inventory['datasets']['math500/test']['models']['Qwen3-8B']['files']
    if len(member) != 1:
        raise ValueError('Ambiguous preselected Qwen3-8B member')
    ledger = json.loads((intake / 'ledger.json').read_text())
    rowpath = intake / ledger[member[0]]['file']
    if not rowpath.exists():
        import modal
        volume = modal.Volume.from_name('repguard-routerbench-intake-checkpoints-v1')
        rowpath.write_bytes(b''.join(volume.read_file('/runs/' + old['run_id'] + '/' + rowpath.name)))
    row = json.loads(rowpath.read_text()); validate(row)
    if row['artifact_sha256'] != ledger[member[0]]['sha256'] or row['member'] != member[0]:
        raise ValueError('Intake metadata checksum mismatch')
    expected = sorted(r['query_sha256'] for r in row['records'])
    if len(expected) != len(set(expected)) or len(expected) != 500:
        raise ValueError('Changed MATH500 coverage')
    if not set(prior['query_ids']) <= set(expected):
        raise ValueError('Pilot queries missing from selected member')
    packet = {'parent_intake_run_id': old['run_id'], 'parent_pilot_run_id': prior['run_id'],
              'archive_sha256': old['archive_sha256'], 'archive_bytes': old['archive_bytes'],
              'selected_member': member[0], 'member_metadata_sha256': row['artifact_sha256'],
              'expected_query_ids': expected, 'pilot_query_ids': prior['query_ids'],
              'reads_outcomes': False, 'models_used_for_prompts': ['Qwen3-8B']}
    paths = [ROOT / 'infra/modal' / n for n in ('routerbench_prompt_groups_core.py', 'routerbench_prompt_groups_pipeline.py', 'routerbench_prompt_groups_modal.py')]
    paths += [Path(__file__), ROOT / 'report_routerbench_prompt_groups.py',
              ROOT / 'tests/test_routerbench_prompt_groups.py',
              ROOT / 'docs/analysis/routerbench_prompt_groups_v1_protocol_2026-10-06.md']
    packet['source_sha256'] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    packet['run_id'] = digest(packet)[:24]
    verify(packet)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    target = OUTPUT / 'packet_private.json'
    if target.exists() and json.loads(target.read_text()) != packet:
        raise ValueError('Prepared grouping identity differs')
    atomic(target, packet)
    print(json.dumps({'run_id': packet['run_id'], 'prompts': 500, 'selected_member': member[0], 'reads_outcomes': False}))


if __name__ == '__main__':
    transport.OUTPUT = OUTPUT
    transport.APP = APP
    transport.prepare = prepare
    transport.main()
