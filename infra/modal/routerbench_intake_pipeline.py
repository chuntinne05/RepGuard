"""Detached hash-verified archive download and resumable outcome-blind inventory."""
import hashlib
import json
import tarfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from routerbench_intake_core import digest, classify, inspect_json, summarize


def atomic(path, data):
    temp = path.with_suffix('.tmp'); temp.write_text(json.dumps(data, indent=2, allow_nan=False)); temp.replace(path)


def file_sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def verify(packet):
    if digest({k: v for k, v in packet.items() if k != 'run_id'})[:24] != packet['run_id']:
        raise ValueError('Packet identity mismatch')
    for name in ('routerbench_intake_core.py', 'routerbench_intake_pipeline.py'):
        if file_sha(Path(__file__).with_name(name)) != packet['source_sha256']['infra/modal/' + name]:
            raise ValueError('Source mismatch')


def run(packet, root, commit):
    verify(packet)
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    ip = root / 'input_private.json'
    if ip.exists() and json.loads(ip.read_text()) != packet:
        raise ValueError('Existing run differs')
    atomic(ip, packet)
    sp = root / 'status.json'
    ledger = {}
    for path in root.glob('member_*.json'):
        row = json.loads(path.read_text())
        if digest({k: v for k, v in row.items() if k != 'artifact_sha256'}) != row['artifact_sha256']:
            raise ValueError('Corrupt member checkpoint')
        if row['run_id'] != packet['run_id']:
            raise ValueError('Mixed member checkpoint')
        ledger[row['member']] = {'file': path.name, 'sha256': row['artifact_sha256']}
    if sp.exists() and json.loads(sp.read_text())['state'] == 'completed_inventory':
        saved = json.loads(sp.read_text())
        if saved['completed_files'] != len(ledger):
            raise ValueError('Missing completed checkpoints')
        return saved
    def status(state, **fields):
        atomic(root / 'ledger.json', ledger)
        atomic(sp, {'run_id': packet['run_id'], 'state': state, 'completed_files': len(ledger),
                    'updated_at': datetime.now(timezone.utc).isoformat(), **fields})
        commit(); print(sp.read_text(), flush=True)
    try:
        archive = root / 'bench-release.tar.gz'
        if not archive.exists():
            partial = root / 'download.partial'
            offset = partial.stat().st_size if partial.exists() else 0
            if offset < packet['archive_bytes']:
                request = urllib.request.Request(packet['url'], headers={'Range': f'bytes={offset}-'} if offset else {})
                with urllib.request.urlopen(request, timeout=120) as response:
                    if offset and (response.status != 206 or not response.headers.get('Content-Range', '').startswith(f'bytes {offset}-')):
                        raise ValueError('Invalid resumed download range')
                    with partial.open('ab' if offset else 'wb') as target:
                        checkpoint = offset
                        status('downloading', downloaded_bytes=offset, total_bytes=packet['archive_bytes'])
                        for chunk in iter(lambda: response.read(8 * 1024 * 1024), b''):
                            target.write(chunk); offset += len(chunk)
                            if offset > packet['archive_bytes']:
                                raise ValueError('Archive larger than pinned metadata')
                            if offset - checkpoint >= 128 * 1024 * 1024:
                                target.flush(); status('downloading', downloaded_bytes=offset, total_bytes=packet['archive_bytes']); checkpoint = offset
            if partial.stat().st_size != packet['archive_bytes'] or file_sha(partial) != packet['archive_sha256']:
                raise ValueError('Archive integrity mismatch')
            partial.replace(archive); commit()
        if archive.stat().st_size != packet['archive_bytes'] or file_sha(archive) != packet['archive_sha256']:
            raise ValueError('Cached archive integrity mismatch')
        status('inventory_running', archive_verified=True)
        members, skipped, files, expanded = [], {}, [], 0
        with tarfile.open(archive, 'r|gz') as tar:
            for member in tar:
                if not member.isfile():
                    continue
                expanded += member.size
                if expanded > 64 * 1024**3:
                    raise ValueError('Uncompressed archive bound exceeded')
                meta = classify(member.name)
                members.append({'member': member.name, 'bytes': member.size, **meta})
                if 'skip' in meta:
                    skipped[meta['skip']] = skipped.get(meta['skip'], 0) + 1
                    continue
                name = 'member_' + hashlib.sha256(member.name.encode()).hexdigest() + '.json'
                path = root / name
                if path.exists():
                    row = json.loads(path.read_text())
                else:
                    stream = tar.extractfile(member)
                    with stream:
                        metadata = inspect_json(stream)
                    row = {'run_id': packet['run_id'], 'member': member.name, 'bytes': member.size, **meta, **metadata}
                    row['artifact_sha256'] = digest(row); atomic(path, row)
                    ledger[member.name] = {'file': name, 'sha256': row['artifact_sha256']}
                    if len(ledger) % 25 == 0:
                        status('inventory_running', last_member=member.name, supported_records=sum(f['supported_count'] for f in files) + row['supported_count'])
                files.append(row)
        atomic(root / 'archive_members.json', members)
        summary = {'run_id': packet['run_id'], 'archive_sha256': packet['archive_sha256'], 'skipped_files': skipped,
                   'parsed_files': len(files), 'supported_records': sum(f['supported_count'] for f in files),
                   'unsupported_records': sum(f['unsupported_count'] for f in files), 'datasets': summarize(files),
                   'score_values_exported': False, 'excluded_mmlu_payloads_parsed': False,
                   'license_status': 'No root license or HF dataset license declared in checked metadata; no redistribution'}
        atomic(root / 'inventory.json', summary)
        status('completed_inventory', supported_records=summary['supported_records'], datasets=len(summary['datasets']), skipped_files=skipped)
        return json.loads(sp.read_text())
    except Exception as error:
        status('pipeline_failed', error=repr(error)); raise
