"""Separate archive access, gold-blind GPU collection and post-collection evaluation."""
import hashlib
import json
import tarfile
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from routerbench_intake_core import digest
from routerbench_intake_pipeline import atomic, file_sha
from routerbench_pilot_core import MODELS, MODEL, SYSTEM, SCHEMA, visible_records, prompt_for, probability, query_hash, analyze


def verify(packet):
    if digest({k: v for k, v in packet.items() if k != 'run_id'})[:24] != packet['run_id']:
        raise ValueError('Pilot input identity mismatch')
    for name in ('routerbench_pilot_core.py', 'routerbench_pilot_pipeline.py', 'routerbench_intake_core.py', 'routerbench_intake_pipeline.py'):
        if file_sha(Path(__file__).with_name(name)) != packet['source_sha256']['infra/modal/' + name]:
            raise ValueError('Pilot source identity mismatch: ' + name)


def validate(row):
    if digest({k: v for k, v in row.items() if k != 'artifact_sha256'}) != row['artifact_sha256']:
        raise ValueError('Artifact checksum mismatch')


def save(path, row):
    row = {k: v for k, v in row.items() if k != 'artifact_sha256'}
    row['artifact_sha256'] = digest(row); atomic(path, row)
    return row


def update(root, packet, commit, state, **fields):
    value = {'run_id': packet['run_id'], 'state': state, 'updated_at': datetime.now(timezone.utc).isoformat(),
             'total_cases': 288, **fields}
    atomic(root / 'status.json', value); commit(); print(json.dumps(value), flush=True)
    return value


def prepare_inputs(packet, root, archive, commit):
    verify(packet); root = Path(root); root.mkdir(parents=True, exist_ok=True)
    ip = root / 'input_private.json'
    if ip.exists() and json.loads(ip.read_text()) != packet:
        raise ValueError('Changed pilot input')
    atomic(ip, packet)
    path = root / 'judge_inputs_private.json'
    if path.exists():
        obj = json.loads(path.read_text()); validate(obj)
        if obj['run_id'] != packet['run_id'] or len(obj['cases']) != 288:
            raise ValueError('Incomplete/mixed judge inputs')
        return obj
    if file_sha(archive) != packet['archive_sha256']:
        raise ValueError('Archive changed')
    update(root, packet, commit, 'preparing_gold_blind_inputs', completed_cases=0)
    queries = packet['query_ids']; members = packet['members']; selected = set(queries)
    visible = {}
    with tarfile.open(archive, 'r|gz') as tar:
        for member in tar:
            if member.name not in members.values():
                continue
            model = next(m for m, name in members.items() if name == member.name)
            with tar.extractfile(member) as stream:
                for record in visible_records(stream):
                    qid = record['query_sha256']
                    if qid in selected:
                        key = (qid, model)
                        if key in visible:
                            raise ValueError('Duplicate selected execution; do not pick based on correctness')
                        visible[key] = record
    cases = []
    for qi, qid in enumerate(queries):
        for mi, model in enumerate(MODELS):
            record = visible[qid, model]
            prompt, meta = prompt_for(record)
            cases.append({'index': len(cases), 'query_index': qi, 'model_index': mi, 'query_sha256': qid,
                          'record_position': record['record_position'],
                          'prompt': prompt, **meta})
    obj = save(path, {'run_id': packet['run_id'], 'cases': cases, 'gold_fields_present': False})
    commit(); return obj


def collect(packet, root, commit, request):
    """Each call intent persisted before dispatch; at most two attempts per case."""
    verify(packet); root = Path(root)
    inputs = json.loads((root / 'judge_inputs_private.json').read_text()); validate(inputs)
    if inputs['run_id'] != packet['run_id']:
        raise ValueError('Mixed pilot inputs')
    ledger = {}; attempts_total = 0
    for case in inputs['cases']:
        path = root / f"case_{case['index']:04d}.json"
        row = json.loads(path.read_text()) if path.exists() else {'run_id': packet['run_id'], 'index': case['index'],
                                                                  'prompt_sha256': case['prompt_sha256'], 'attempts': []}
        if path.exists():
            validate(row)
        if row['run_id'] != packet['run_id'] or row['prompt_sha256'] != case['prompt_sha256']:
            raise ValueError('Mixed judge checkpoint')
        if not row.get('complete'):
            for attempt in row['attempts']:
                if attempt['state'] == 'started':
                    attempt['state'] = 'interrupted_usage_unknown'
            for _ in range(len(row['attempts']), 2):
                entry = {'state': 'started', 'started_at': datetime.now(timezone.utc).isoformat()}
                row['attempts'].append(entry); row = save(path, row); commit()
                entry = row['attempts'][-1]
                try:
                    response = request({'model': MODEL, 'messages': [{'role': 'system', 'content': SYSTEM},
                                        {'role': 'user', 'content': case['prompt']}], 'stream': False, 'think': False,
                                        'format': SCHEMA, 'options': {'temperature': 0, 'seed': 1404,
                                        'num_ctx': 16384, 'num_predict': 128}})
                    entry.update({'state': 'response_received', 'response': response})
                    if not response.get('done') or response.get('prompt_eval_count', 0) >= 16000:
                        raise ValueError('Incomplete response or context near capacity')
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
        update(root, packet, commit, 'judging', completed_cases=len(ledger), attempts_started=attempts_total,
               latest_case=case['index'])
    return update(root, packet, commit, 'judgments_completed', completed_cases=len(ledger), attempts_started=attempts_total)


def selected_gold(packet, archive, cases):
    """Evaluator-only reader, invoked only after all judgment artifacts are frozen."""
    import ijson
    members = packet['members']; scores = {}
    positions = {(MODELS[c['model_index']], c['record_position']): c['query_sha256'] for c in cases}
    with tarfile.open(archive, 'r|gz') as tar:
        for member in tar:
            if member.name not in members.values():
                continue
            model = next(m for m, name in members.items() if name == member.name)
            # Positions were fixed by gold-blind extraction, before any judging.
            position = -1
            with tar.extractfile(member) as stream:
                for prefix, event, value in ijson.parse(stream):
                    if prefix == 'records.item' and event == 'start_map':
                        position += 1
                    elif prefix == 'records.item.score' and event in ('number', 'boolean') and (model, position) in positions:
                        key = (positions[model, position], model)
                        if key in scores or float(value) not in (0., 1.):
                            raise ValueError('Duplicated/nonbinary objective score')
                        scores[key] = float(value)
    return np.array([[scores[q, m] for m in MODELS] for q in packet['query_ids']])


def finish(packet, root, archive, commit):
    verify(packet); root = Path(root)
    inputs = json.loads((root / 'judge_inputs_private.json').read_text()); validate(inputs)
    ledger = json.loads((root / 'ledger.json').read_text())
    if len(ledger) != 288:
        raise ValueError('No evaluation before complete judgments')
    p = np.full((48, 6), np.nan); invalid = np.zeros((48, 6), bool); clipped = np.zeros((48, 6), bool)
    totals = {'attempts_started': 0, 'responses_recorded': 0, 'prompt_tokens_recorded': 0,
              'completion_tokens_recorded': 0, 'unknown_usage_attempts': 0, 'inference_seconds_recorded': 0.}
    for case in inputs['cases']:
        row = json.loads((root / f"case_{case['index']:04d}.json").read_text()); validate(row)
        if not row['complete'] or row['artifact_sha256'] != ledger[str(case['index'])]:
            raise ValueError('Judge ledger mismatch')
        qi, mi = case['query_index'], case['model_index']
        p[qi, mi] = row['probability']; invalid[qi, mi] = row['invalid']; clipped[qi, mi] = case['answer_clipped']
        for attempt in row['attempts']:
            totals['attempts_started'] += 1
            if 'response' not in attempt:
                totals['unknown_usage_attempts'] += 1
            else:
                r = attempt['response']; totals['responses_recorded'] += 1
                totals['prompt_tokens_recorded'] += r.get('prompt_eval_count', 0)
                totals['completion_tokens_recorded'] += r.get('eval_count', 0)
                totals['inference_seconds_recorded'] += r.get('total_duration', 0) / 1e9
    y = selected_gold(packet, archive, inputs['cases'])
    result = analyze(y, p, invalid, clipped)
    result.update({'run_id': packet['run_id'], 'usage': totals})
    atomic(root / 'pilot_gold_private.json', {'query_ids': packet['query_ids'], 'models': list(MODELS), 'success': y.tolist()})
    atomic(root / 'analysis.json', result)
    return update(root, packet, commit, 'completed_pilot_review_required', completed_cases=288,
                  expansion_signal_pass=result['expansion_signal_pass'], operational_pass=result['operational_pass'], usage=totals)
