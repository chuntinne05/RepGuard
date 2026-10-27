"""Verify the pinned tar and extract only prompts from one preselected member."""
import hashlib
import json
import tarfile
from datetime import datetime, timezone
from pathlib import Path
import ijson
from routerbench_prompt_groups_core import group, prompt_records


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def atomic(path, value):
    path = Path(path)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    tmp.replace(path)


def save(path, value):
    value = {k: v for k, v in value.items() if k != 'artifact_sha256'}
    value['artifact_sha256'] = digest(value)
    atomic(path, value)
    return value


def validate(value):
    if digest({k: v for k, v in value.items() if k != 'artifact_sha256'}) != value['artifact_sha256']:
        raise ValueError('Prompt grouping checksum mismatch')


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def verify(packet):
    if digest({k: v for k, v in packet.items() if k != 'run_id'})[:24] != packet['run_id']:
        raise ValueError('Prompt grouping packet mismatch')
    if packet['archive_sha256'] != 'b79f8cde1a6f029c2efa663a3a3b6f7748defb22341fe59f328cebef6648c8f1':
        raise ValueError('Changed archive')
    if len(packet['expected_query_ids']) != 500 or len(set(packet['expected_query_ids'])) != 500:
        raise ValueError('Changed common query set')
    if len(packet['pilot_query_ids']) != 48 or not set(packet['pilot_query_ids']) <= set(packet['expected_query_ids']):
        raise ValueError('Changed pilot membership')
    for name in ('routerbench_prompt_groups_core.py', 'routerbench_prompt_groups_pipeline.py'):
        path = Path(__file__).with_name(name)
        if file_sha(path) != packet['source_sha256']['infra/modal/' + name]:
            raise ValueError('Deployed source changed: ' + name)


def run(packet, root, archive, commit=lambda: None):
    verify(packet)
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    input_path = root / 'input_private.json'
    if input_path.exists() and json.loads(input_path.read_text()) != packet:
        raise ValueError('Changed grouping input')
    atomic(input_path, packet)
    def status(state, **fields):
        value = {'run_id': packet['run_id'], 'state': state, 'updated_at': datetime.now(timezone.utc).isoformat(), **fields}
        atomic(root / 'status.json', value)
        commit()
        print(json.dumps(value), flush=True)
        return value
    try:
        analysis_path = root / 'analysis.json'
        if analysis_path.exists():
            analysis = json.loads(analysis_path.read_text()); validate(analysis)
            if analysis['run_id'] != packet['run_id']:
                raise ValueError('Mixed grouping analysis')
            return status('completed_prompt_grouping_review_required', **{k: analysis[k] for k in ('total_groups', 'remaining_groups', 'remaining_questions')})
        status('verifying_archive')
        if Path(archive).stat().st_size != packet['archive_bytes'] or file_sha(archive) != packet['archive_sha256']:
            raise ValueError('Pinned archive integrity mismatch')
        status('reading_prompts')
        prompts = {}
        found = 0
        with tarfile.open(archive, 'r|gz') as tar:
            for member in tar:
                if member.name != packet['selected_member']:
                    continue
                if not member.isfile() or member.size > 100 * 1024 * 1024:
                    raise ValueError('Unexpected selected member')
                found += 1
                if found != 1:
                    raise ValueError('Duplicate selected member')
                with tar.extractfile(member) as stream:
                    for record in prompt_records(ijson.parse(stream)):
                        qid = record['query_sha256']
                        if qid in prompts:
                            raise ValueError('Duplicate question in selected member')
                        prompts[qid] = record['prompt']
        if found != 1 or set(prompts) != set(packet['expected_query_ids']):
            raise ValueError('Selected member prompt coverage mismatch')
        save(root / 'prompts_private.json', {'run_id': packet['run_id'], 'prompts': prompts})
        commit()
        status('grouping', prompts_read=len(prompts))
        result = group(prompts, packet['pilot_query_ids'])
        save(analysis_path, {'run_id': packet['run_id'], **result})
        commit()
        return status('completed_prompt_grouping_review_required', total_groups=result['total_groups'],
                      remaining_groups=result['remaining_groups'], remaining_questions=result['remaining_questions'])
    except Exception as error:
        status('pipeline_failed', error=repr(error))
        raise
