"""Freeze metadata-selected development questions before any score access."""
import hashlib
import json
from pathlib import Path
import run_dart_gain as transport
from routerbench_headroom_core import DATASETS, select_queries
from routerbench_headroom_pipeline import atomic, digest, validate, verify

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / 'results/routerbench_headroom_v1'
APP = 'repguard-routerbench-headroom-v1'


def prepare():
    import modal
    prior = ROOT / 'results/routerbench_intake_v2/cloud'
    old = json.loads((prior / 'input_private.json').read_text())
    inventory = json.loads((prior / 'inventory.json').read_text())
    ledger = json.loads((prior / 'ledger.json').read_text())
    assert old['run_id'] == inventory['run_id'] == 'c387f6364d2266bf1bf370a9'
    assert json.loads((prior / 'status.json').read_text())['state'] == 'completed_inventory'
    volume = modal.Volume.from_name('repguard-routerbench-intake-checkpoints-v1')
    datasets = {}
    for dataset in DATASETS:
        meta = inventory['datasets'][dataset]
        if meta['model_count'] != 20:
            raise ValueError('Changed model pool')
        models = sorted(meta['models'])
        members, hashes, records, sets, duplicated = {}, {}, {}, [], set()
        for model in models:
            files = meta['models'][model]['files']
            if len(files) != 1:
                raise ValueError('Ambiguous archived execution: ' + model)
            member = files[0]
            path = prior / ledger[member]['file']
            if not path.exists():
                path.write_bytes(b''.join(volume.read_file('/runs/' + old['run_id'] + '/' + path.name)))
            row = json.loads(path.read_text()); validate(row)
            if row['artifact_sha256'] != ledger[member]['sha256'] or row['member'] != member or row['model'] != model:
                raise ValueError('Metadata checksum/identity mismatch')
            if row['record_count'] != len(row['records']):
                raise ValueError('Unsupported records would break physical position mapping')
            if 'score' not in row['record_fields']:
                raise ValueError('Archived file lacks score field')
            lookup = {}
            for i, record in enumerate(row['records']):
                qid = record['query_sha256']
                if qid in lookup:
                    duplicated.add(qid)
                else:
                    lookup[qid] = i
            members[model] = member
            hashes[model] = row['artifact_sha256']
            records[model] = lookup
            sets.append(set(lookup))
        common_all = set.intersection(*sets)
        if len(common_all) != meta['common_queries_all_models']:
            raise ValueError('Metadata common coverage differs')
        common = common_all - duplicated
        selected = select_queries(dataset, common)
        datasets[dataset] = {'models': models, 'common_questions': len(common_all),
                             'eligible_unique_questions': len(common),
                             'duplicate_query_hashes_excluded': len(duplicated & common_all),
                             'query_ids': selected,
                             'members': members, 'member_metadata_sha256': hashes,
                             'positions': {m: {q: records[m][q] for q in selected} for m in models}}
    packet = {'parent_intake_run_id': old['run_id'], 'archive_sha256': old['archive_sha256'],
              'archive_bytes': old['archive_bytes'], 'datasets': datasets,
              'scores_outside_selected_dev_read': False, 'new_model_calls': 0}
    paths = [ROOT / 'infra/modal' / n for n in ('routerbench_headroom_core.py', 'routerbench_headroom_pipeline.py', 'routerbench_headroom_modal.py')]
    paths += [Path(__file__), ROOT / 'report_routerbench_headroom.py',
              ROOT / 'tests/test_routerbench_headroom.py',
              ROOT / 'docs/analysis/routerbench_headroom_v1_protocol_2026-10-06.md']
    packet['source_sha256'] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    packet['run_id'] = digest(packet)[:24]
    verify(packet)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT / 'packet_private.json'
    if path.exists() and json.loads(path.read_text()) != packet:
        raise ValueError('Prepared headroom packet identity changed')
    atomic(path, packet)
    print(json.dumps({'run_id': packet['run_id'], 'datasets': {k: {'common': d['common_questions'],
                                                                 'eligible_unique': d['eligible_unique_questions'],
                                                                 'duplicate_hashes_excluded': d['duplicate_query_hashes_excluded'],
                                                                 'selected': len(d['query_ids']),
                                                                 'models': len(d['models'])} for k, d in datasets.items()},
                      'new_model_calls': 0}))


if __name__ == '__main__':
    transport.OUTPUT = OUTPUT
    transport.APP = APP
    transport.prepare = prepare
    transport.main()
