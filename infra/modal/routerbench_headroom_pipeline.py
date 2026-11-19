"""Read only frozen positions of archived objective scores from a pinned tar."""
import hashlib
import json
import tarfile
from datetime import datetime, timezone
from pathlib import Path
import ijson
import numpy as np
from routerbench_headroom_core import DATASETS, N_DEV, analyze


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def atomic(path, value):
    path = Path(path)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    tmp.replace(path)


def save(path, value):
    row = {k: v for k, v in value.items() if k != 'artifact_sha256'}
    row['artifact_sha256'] = digest(row)
    atomic(path, row)
    return row


def validate(value):
    if digest({k: v for k, v in value.items() if k != 'artifact_sha256'}) != value['artifact_sha256']:
        raise ValueError('Headroom checkpoint checksum mismatch')


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def verify(packet):
    if digest({k: v for k, v in packet.items() if k != 'run_id'})[:24] != packet['run_id']:
        raise ValueError('Headroom input identity mismatch')
    if packet['archive_sha256'] != 'b79f8cde1a6f029c2efa663a3a3b6f7748defb22341fe59f328cebef6648c8f1':
        raise ValueError('Changed archive')
    if list(packet['datasets']) != list(DATASETS):
        raise ValueError('Changed dataset selection')
    for dataset in DATASETS:
        row = packet['datasets'][dataset]
        if row['common_questions'] - row['duplicate_query_hashes_excluded'] != row['eligible_unique_questions']:
            raise ValueError('Duplicate exclusion counts inconsistent')
        if len(row['query_ids']) != N_DEV or len(set(row['query_ids'])) != N_DEV or len(row['models']) != 20:
            raise ValueError('Changed development selection')
        if len(row['members']) != 20 or len(set(row['members'].values())) != 20:
            raise ValueError('Ambiguous model files')
        for model in row['models']:
            positions = row['positions'][model]
            if set(positions) != set(row['query_ids']) or len(set(positions.values())) != N_DEV:
                raise ValueError('Missing/duplicate selected positions')
    for name in ('routerbench_headroom_core.py', 'routerbench_headroom_pipeline.py'):
        if file_sha(Path(__file__).with_name(name)) != packet['source_sha256']['infra/modal/' + name]:
            raise ValueError('Headroom source differs')


def selected_scores(stream, positions):
    wanted = {int(v): q for q, v in positions.items()}
    if len(wanted) != len(positions):
        raise ValueError('Duplicate selected record positions')
    found = {}
    index = -1
    for prefix, event, value in ijson.parse(stream):
        if prefix == 'records.item' and event == 'start_map':
            index += 1
        elif prefix == 'records.item.score' and index in wanted and event in ('number', 'boolean'):
            if index in found:
                raise ValueError('Duplicate score field')
            score = float(value)
            if not np.isfinite(score) or not 0 <= score <= 1:
                raise ValueError('Invalid selected score')
            found[index] = score
    if set(found) != set(wanted):
        raise ValueError('Selected score missing')
    return {wanted[i]: value for i, value in found.items()}


def run(packet, root, archive, commit=lambda: None):
    verify(packet)
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    ip = root / 'input_private.json'
    if ip.exists() and json.loads(ip.read_text()) != packet:
        raise ValueError('Changed headroom checkpoint input')
    atomic(ip, packet)
    def status(state, **fields):
        row = {'run_id': packet['run_id'], 'state': state,
               'updated_at': datetime.now(timezone.utc).isoformat(), **fields}
        atomic(root / 'status.json', row); commit(); print(json.dumps(row), flush=True)
        return row
    try:
        if (root / 'analysis.json').exists():
            analysis = json.loads((root / 'analysis.json').read_text()); validate(analysis)
            if analysis['run_id'] != packet['run_id']:
                raise ValueError('Mixed headroom analysis')
            return status('completed_development_headroom_review_required', datasets=len(DATASETS))
        status('verifying_archive')
        if Path(archive).stat().st_size != packet['archive_bytes'] or file_sha(archive) != packet['archive_sha256']:
            raise ValueError('Pinned archive integrity mismatch')
        members = {}
        for dataset in DATASETS:
            for model, name in packet['datasets'][dataset]['members'].items():
                if name in members:
                    raise ValueError('Member reused by datasets')
                members[name] = (dataset, model)
        ledger = {}
        status('reading_selected_gold', files=0, total_files=40)
        with tarfile.open(archive, 'r|gz') as tar:
            for member in tar:
                if member.name not in members:
                    continue
                dataset, model = members[member.name]
                key = dataset + '/' + model
                if key in ledger or not member.isfile() or member.size > 100 * 1024 * 1024:
                    raise ValueError('Duplicate or unsupported selected member')
                path = root / ('member_' + hashlib.sha256(member.name.encode()).hexdigest() + '.json')
                if path.exists():
                    row = json.loads(path.read_text()); validate(row)
                    if row['member'] != member.name or row['run_id'] != packet['run_id']:
                        raise ValueError('Mixed member checkpoint')
                else:
                    with tar.extractfile(member) as stream:
                        scores = selected_scores(stream, packet['datasets'][dataset]['positions'][model])
                    row = save(path, {'run_id': packet['run_id'], 'dataset': dataset, 'model': model,
                                      'member': member.name, 'scores': scores})
                    commit()
                ledger[key] = {'file': path.name, 'sha256': row['artifact_sha256']}
                atomic(root / 'ledger.json', ledger); commit()
                if len(ledger) % 5 == 0:
                    status('reading_selected_gold', files=len(ledger), total_files=40)
        if len(ledger) != 40:
            raise ValueError('Missing selected archive member')
        status('analyzing', files=40, total_files=40)
        result = {}
        for dataset in DATASETS:
            spec = packet['datasets'][dataset]
            matrix = np.full((N_DEV, 20), np.nan)
            for mi, model in enumerate(spec['models']):
                item = ledger[dataset + '/' + model]
                row = json.loads((root / item['file']).read_text()); validate(row)
                matrix[:, mi] = [row['scores'][qid] for qid in spec['query_ids']]
            result[dataset] = analyze(matrix, spec['models'])
        save(root / 'analysis.json', {'run_id': packet['run_id'], 'datasets': result})
        commit()
        return status('completed_development_headroom_review_required', datasets=2, files=40)
    except Exception as error:
        status('pipeline_failed', error=repr(error))
        raise
