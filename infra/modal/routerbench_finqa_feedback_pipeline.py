"""Detached, resumable gold-blind FinQA judge collection and evaluator-only analysis."""
import hashlib
import json
import tarfile
from datetime import datetime, timezone
from pathlib import Path
import ijson
import numpy as np
from routerbench_finqa_feedback_core import (MODEL, SYSTEM, SCHEMA, query_hash,
                                            visible_records, prompt_for, probability, analyze)

TOTAL = 960


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
        raise ValueError('FinQA judge artifact checksum mismatch')


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def verify(packet):
    if digest({k: v for k, v in packet.items() if k != 'run_id'})[:24] != packet['run_id']:
        raise ValueError('FinQA pilot packet identity mismatch')
    if packet['parent_headroom_run_id'] != '58bcf5179974f10ebe94c405':
        raise ValueError('Changed development parent')
    if packet['archive_sha256'] != 'b79f8cde1a6f029c2efa663a3a3b6f7748defb22341fe59f328cebef6648c8f1':
        raise ValueError('Changed archive')
    if packet['total_cases'] != TOTAL or packet['max_attempts_per_case'] != 2 or packet['selection_reads_outcomes'] or packet['new_solver_calls'] != 0:
        raise ValueError('Changed collection limits')
    if len(packet['models']) != 20 or len(packet['query_ids']) != 48 or len(set(packet['query_ids'])) != 48:
        raise ValueError('Changed pilot dimensions')
    if len(packet['members']) != 20 or len(set(packet['members'].values())) != 20:
        raise ValueError('Changed source files')
    for model in packet['models']:
        if set(packet['positions'][model]) != set(packet['query_ids']):
            raise ValueError('Changed selected positions')
    for name in ('routerbench_finqa_feedback_core.py', 'routerbench_finqa_feedback_pipeline.py'):
        if file_sha(Path(__file__).with_name(name)) != packet['source_sha256']['infra/modal/' + name]:
            raise ValueError('Frozen pilot source changed: ' + name)


def status(root, packet, commit, state, **fields):
    value = {'run_id': packet['run_id'], 'state': state, 'updated_at': datetime.now(timezone.utc).isoformat(),
             'total_cases': TOTAL, **fields}
    atomic(Path(root) / 'status.json', value)
    commit()
    print(json.dumps(value), flush=True)
    return value


def prepare_inputs(packet, root, archive, commit):
    verify(packet)
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    ip = root / 'input_private.json'
    if ip.exists() and json.loads(ip.read_text()) != packet:
        raise ValueError('Changed pilot packet')
    atomic(ip, packet)
    target = root / 'judge_inputs_private.json'
    if target.exists():
        row = json.loads(target.read_text()); validate(row)
        if row['run_id'] != packet['run_id'] or len(row['cases']) != TOTAL:
            raise ValueError('Mixed cached judge inputs')
        return row
    status(root, packet, commit, 'verifying_archive', completed_cases=0)
    if Path(archive).stat().st_size != packet['archive_bytes'] or file_sha(archive) != packet['archive_sha256']:
        raise ValueError('Pinned archive integrity mismatch')
    status(root, packet, commit, 'preparing_gold_blind_inputs', completed_cases=0)
    members = {name: model for model, name in packet['members'].items()}
    visible = {}
    with tarfile.open(archive, 'r|gz') as tar:
        for member in tar:
            if member.name not in members:
                continue
            model = members[member.name]
            if not member.isfile() or member.size > 100 * 1024 * 1024:
                raise ValueError('Unsupported selected member')
            by_position = {int(position): q for q, position in packet['positions'][model].items()}
            with tar.extractfile(member) as stream:
                for position, record in visible_records(stream, by_position):
                    q = by_position[position]
                    if query_hash(record.get('origin_query', '')) != q or (q, model) in visible:
                        raise ValueError('Missing/duplicate selected execution identity')
                    visible[q, model] = {'position': position, **record}
    if len(visible) != TOTAL:
        raise ValueError('Missing selected judge input')
    cases = []
    for qi, q in enumerate(packet['query_ids']):
        for mi, model in enumerate(packet['models']):
            record = visible[q, model]
            prompt, meta = prompt_for(record)
            cases.append({'index': len(cases), 'query_index': qi, 'model_index': mi,
                          'query_sha256': q, 'record_position': record['position'],
                          'prompt': prompt, **meta})
    row = save(target, {'run_id': packet['run_id'], 'cases': cases, 'gold_fields_present': False})
    commit()
    return row


def collect(packet, root, commit, request):
    """Persist every intent; at most two real requests per case across retries."""
    verify(packet)
    root = Path(root)
    inputs = json.loads((root / 'judge_inputs_private.json').read_text()); validate(inputs)
    if inputs['run_id'] != packet['run_id'] or len(inputs['cases']) != TOTAL:
        raise ValueError('Mixed judge inputs')
    ledger = {}; attempts_total = 0
    for case in inputs['cases']:
        path = root / f"case_{case['index']:04d}.json"
        row = json.loads(path.read_text()) if path.exists() else {'run_id': packet['run_id'],
            'index': case['index'], 'prompt_sha256': case['prompt_sha256'], 'attempts': []}
        if path.exists():
            validate(row)
        if row['run_id'] != packet['run_id'] or row['prompt_sha256'] != case['prompt_sha256']:
            raise ValueError('Mixed judge checkpoint')
        if not row.get('complete'):
            # A valid response may already have been persisted before a crash
            # interrupted the final complete flag. Do not dispatch it twice.
            if 'probability' in row:
                row['complete'] = True
                row = save(path, row); commit()
                ledger[str(case['index'])] = row['artifact_sha256']
                attempts_total += len(row['attempts'])
                atomic(root / 'ledger.json', ledger); commit()
                continue
            for attempt in row['attempts']:
                if attempt['state'] == 'started':
                    attempt['state'] = 'interrupted_usage_unknown'
            for _ in range(len(row['attempts']), 2):
                row['attempts'].append({'state': 'started', 'started_at': datetime.now(timezone.utc).isoformat()})
                row = save(path, row); commit()
                entry = row['attempts'][-1]
                try:
                    response = request({'model': MODEL, 'messages': [{'role': 'system', 'content': SYSTEM},
                        {'role': 'user', 'content': case['prompt']}], 'stream': False, 'think': False,
                        'format': SCHEMA, 'options': {'temperature': 0, 'seed': 1404,
                                                     'num_ctx': 16384, 'num_predict': 128}})
                    entry.update({'state': 'response_received', 'response': response})
                    if not response.get('done') or response.get('prompt_eval_count', 0) >= 16000:
                        raise ValueError('Incomplete judge response or context near capacity')
                    row['probability'] = probability(response['message']['content'])
                    row['invalid'] = False
                except Exception as error:
                    entry['state'] = 'failed'; entry['error'] = repr(error)
                row = save(path, row); commit()
                if 'probability' in row:
                    break
            if 'probability' not in row:
                row.update(probability=.5, invalid=True)
            row['complete'] = True; row = save(path, row); commit()
        ledger[str(case['index'])] = row['artifact_sha256']
        attempts_total += len(row['attempts'])
        atomic(root / 'ledger.json', ledger)
        if len(ledger) % 10 == 0 or len(ledger) == TOTAL:
            status(root, packet, commit, 'judging', completed_cases=len(ledger),
                   attempts_started=attempts_total, latest_case=case['index'])
        else:
            commit()
    return status(root, packet, commit, 'judgments_completed', completed_cases=TOTAL,
                  attempts_started=attempts_total)


def selected_gold(packet, archive):
    """CPU evaluator only. Retain score solely at preselected record positions."""
    by_member = {name: model for model, name in packet['members'].items()}
    scores = {}
    with tarfile.open(archive, 'r|gz') as tar:
        for member in tar:
            if member.name not in by_member:
                continue
            model = by_member[member.name]
            wanted = {int(pos): q for q, pos in packet['positions'][model].items()}
            position = -1
            with tar.extractfile(member) as stream:
                for prefix, event, value in ijson.parse(stream):
                    if prefix == 'records.item' and event == 'start_map':
                        position += 1
                    elif prefix == 'records.item.score' and position in wanted and event in ('number', 'boolean'):
                        key = (wanted[position], model)
                        if key in scores or float(value) not in (0., 1.):
                            raise ValueError('Duplicate/nonbinary selected score')
                        scores[key] = float(value)
    if len(scores) != TOTAL:
        raise ValueError('Missing selected gold score')
    return np.array([[scores[q, m] for m in packet['models']] for q in packet['query_ids']])


def finish(packet, root, archive, commit):
    verify(packet)
    root = Path(root)
    inputs = json.loads((root / 'judge_inputs_private.json').read_text()); validate(inputs)
    ledger = json.loads((root / 'ledger.json').read_text())
    if len(ledger) != TOTAL:
        raise ValueError('Cannot analyze incomplete judge collection')
    p = np.full((48, 20), np.nan); invalid = np.zeros((48, 20), bool); boxed = np.zeros((48, 20), bool)
    usage = {'attempts_started': 0, 'responses_recorded': 0, 'prompt_tokens_recorded': 0,
             'completion_tokens_recorded': 0, 'unknown_usage_attempts': 0,
             'inference_seconds_recorded': 0.}
    for case in inputs['cases']:
        row = json.loads((root / f"case_{case['index']:04d}.json").read_text()); validate(row)
        if not row['complete'] or row['artifact_sha256'] != ledger[str(case['index'])]:
            raise ValueError('Judge ledger mismatch')
        qi, mi = case['query_index'], case['model_index']
        p[qi, mi] = row['probability']; invalid[qi, mi] = row['invalid']
        boxed[qi, mi] = case['extraction_mode'] == 'complete_boxed'
        for attempt in row['attempts']:
            usage['attempts_started'] += 1
            if 'response' not in attempt:
                usage['unknown_usage_attempts'] += 1
            else:
                r = attempt['response']; usage['responses_recorded'] += 1
                usage['prompt_tokens_recorded'] += r.get('prompt_eval_count', 0)
                usage['completion_tokens_recorded'] += r.get('eval_count', 0)
                usage['inference_seconds_recorded'] += r.get('total_duration', 0) / 1e9
    y = selected_gold(packet, archive)
    result = analyze(y, p, invalid, boxed)
    result.update({'run_id': packet['run_id'], 'usage': usage})
    atomic(root / 'pilot_gold_private.json', {'query_ids': packet['query_ids'],
                                             'models': packet['models'], 'success': y.tolist()})
    atomic(root / 'analysis.json', result)
    commit()
    return status(root, packet, commit, 'completed_pilot_review_required', completed_cases=TOTAL,
                  expansion_signal_pass=result['expansion_signal_pass'],
                  operational_pass=result['operational_pass'], usage=usage)
