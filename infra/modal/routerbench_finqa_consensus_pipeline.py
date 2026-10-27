"""Detached gold-blind consensus extraction followed by selected-score analysis."""
import hashlib
import json
import tarfile
from datetime import datetime, timezone
from pathlib import Path

import ijson
import numpy as np

from routerbench_finqa_feedback_core import query_hash
from routerbench_finqa_consensus_core import agreement_proxy, analyze


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def atomic(path, value):
    path = Path(path)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    tmp.replace(path)


def save(path, value):
    row = {key: item for key, item in value.items() if key != 'artifact_sha256'}
    row['artifact_sha256'] = digest(row)
    atomic(path, row)
    return row


def validate(value):
    if digest({key: item for key, item in value.items() if key != 'artifact_sha256'}) != value['artifact_sha256']:
        raise ValueError('Consensus artifact checksum mismatch')


def file_sha(path):
    checksum = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            checksum.update(chunk)
    return checksum.hexdigest()


def verify(packet):
    if digest({key: item for key, item in packet.items() if key != 'run_id'})[:24] != packet['run_id']:
        raise ValueError('Consensus packet identity mismatch')
    if packet['archive_sha256'] != 'b79f8cde1a6f029c2efa663a3a3b6f7748defb22341fe59f328cebef6648c8f1':
        raise ValueError('Changed pinned archive')
    if packet['parent_headroom_run_id'] != '58bcf5179974f10ebe94c405' or packet['parent_judge_run_id'] != '0fad63edd346eb0591fd99e1':
        raise ValueError('Unexpected parent study')
    if len(packet['models']) != 20 or len(packet['query_ids']) != 48 or len(set(packet['query_ids'])) != 48:
        raise ValueError('Changed consensus dimensions')
    if set(packet['query_ids']) & set(packet['old_pilot_query_ids']) or len(packet['old_pilot_query_ids']) != 48:
        raise ValueError('Consensus questions overlap judge pilot')
    if len(packet['members']) != 20 or len(set(packet['members'].values())) != 20:
        raise ValueError('Changed archive members')
    for model in packet['models']:
        if set(packet['positions'][model]) != set(packet['query_ids']):
            raise ValueError('Missing selected record position')
    for name in ('routerbench_finqa_consensus_core.py', 'routerbench_finqa_consensus_pipeline.py'):
        path = Path(__file__).with_name(name)
        if file_sha(path) != packet['source_sha256']['infra/modal/' + name]:
            raise ValueError('Frozen consensus source changed: ' + name)


def status(root, packet, commit, state, **fields):
    value = {'run_id': packet['run_id'], 'state': state,
             'updated_at': datetime.now(timezone.utc).isoformat(), **fields}
    atomic(Path(root) / 'status.json', value)
    commit()
    print(json.dumps(value), flush=True)
    return value


def selected_predictions(packet, archive):
    """First pass allowlists only question identity and prediction strings."""
    by_member = {name: model for model, name in packet['members'].items()}
    observed = {}
    with tarfile.open(archive, 'r|gz') as tar:
        for member in tar:
            if member.name not in by_member:
                continue
            model = by_member[member.name]
            if not member.isfile() or member.size > 100 * 1024 * 1024:
                raise ValueError('Unsupported selected archive member')
            wanted = {int(pos): q for q, pos in packet['positions'][model].items()}
            position = -1
            row = {}
            with tar.extractfile(member) as stream:
                for prefix, event, value in ijson.parse(stream):
                    if prefix == 'records.item' and event == 'start_map':
                        position += 1
                        row = {}
                    elif position in wanted and prefix in ('records.item.origin_query', 'records.item.prediction') and event == 'string':
                        row[prefix.rsplit('.', 1)[1]] = value
                    elif position in wanted and prefix == 'records.item' and event == 'end_map':
                        q = wanted[position]
                        if query_hash(row.get('origin_query', '')) != q or (q, model) in observed:
                            raise ValueError('Missing/duplicate selected prediction identity')
                        prediction = row.get('prediction', '')
                        if len(prediction) > 1000:
                            raise ValueError('Unexpected oversize parsed prediction')
                        observed[q, model] = prediction
    if len(observed) != 960:
        raise ValueError('Incomplete selected predictions')
    return [[observed[q, model] for model in packet['models']] for q in packet['query_ids']]


def selected_gold(packet, archive):
    """Second pass allowlists score only at frozen selected positions."""
    by_member = {name: model for model, name in packet['members'].items()}
    scores = {}
    with tarfile.open(archive, 'r|gz') as tar:
        for member in tar:
            if member.name not in by_member:
                continue
            model = by_member[member.name]
            if not member.isfile() or member.size > 100 * 1024 * 1024:
                raise ValueError('Unsupported selected archive member')
            wanted = {int(pos): q for q, pos in packet['positions'][model].items()}
            position = -1
            row = {}
            with tar.extractfile(member) as stream:
                for prefix, event, value in ijson.parse(stream):
                    if prefix == 'records.item' and event == 'start_map':
                        position += 1
                        row = {}
                    elif position in wanted and prefix == 'records.item.origin_query' and event == 'string':
                        row['origin_query'] = value
                    elif position in wanted and prefix == 'records.item.score' and event in ('number', 'boolean'):
                        key = (wanted[position], model)
                        if key in scores or float(value) not in (0., 1.):
                            raise ValueError('Duplicate/nonbinary selected score')
                        row['score'] = float(value)
                    elif position in wanted and prefix == 'records.item' and event == 'end_map':
                        q = wanted[position]
                        if query_hash(row.get('origin_query', '')) != q or 'score' not in row or (q, model) in scores:
                            raise ValueError('Missing/duplicate selected gold identity')
                        scores[q, model] = row['score']
    if len(scores) != 960:
        raise ValueError('Incomplete selected scores')
    return np.array([[scores[q, model] for model in packet['models']] for q in packet['query_ids']])


def run(packet, root, archive, commit=lambda: None):
    verify(packet)
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    target = root / 'input_private.json'
    if target.exists() and json.loads(target.read_text()) != packet:
        raise ValueError('Changed consensus packet at checkpoint')
    atomic(target, packet)
    try:
        if (root / 'analysis.json').exists():
            result = json.loads((root / 'analysis.json').read_text())
            validate(result)
            if result['run_id'] != packet['run_id']:
                raise ValueError('Mixed consensus analysis')
            return status(root, packet, commit, 'completed_development_review_required',
                          cells=960, expansion_signal_pass=result['expansion_signal_pass'])
        proxy_path = root / 'proxy_private.json'
        predictions_path = root / 'predictions_private.json'
        if proxy_path.exists() and predictions_path.exists():
            proxy = json.loads(proxy_path.read_text())
            predictions = json.loads(predictions_path.read_text())
            validate(proxy); validate(predictions)
            if proxy['run_id'] != packet['run_id'] or predictions['run_id'] != packet['run_id']:
                raise ValueError('Mixed proxy checkpoint')
            p, missing = agreement_proxy(predictions['matrix'])
            if p.tolist() != proxy['probability'] or missing.tolist() != proxy['missing']:
                raise ValueError('Changed proxy checkpoint')
        else:
            status(root, packet, commit, 'verifying_archive')
            if Path(archive).stat().st_size != packet['archive_bytes'] or file_sha(archive) != packet['archive_sha256']:
                raise ValueError('Pinned archive integrity mismatch')
            status(root, packet, commit, 'reading_gold_blind_predictions')
            matrix = selected_predictions(packet, archive)
            p, missing = agreement_proxy(matrix)
            save(predictions_path, {'run_id': packet['run_id'], 'matrix': matrix})
            save(proxy_path, {'run_id': packet['run_id'], 'probability': p.tolist(),
                              'missing': missing.tolist(), 'gold_fields_present': False})
            commit()
        status(root, packet, commit, 'proxy_complete', cells=960,
               prediction_coverage=float((~missing).mean()))
        status(root, packet, commit, 'reading_selected_gold', cells=960)
        y = selected_gold(packet, archive)
        atomic(root / 'pilot_gold_private.json', {'query_ids': packet['query_ids'],
                                                 'models': packet['models'], 'success': y.tolist()})
        status(root, packet, commit, 'analyzing', cells=960)
        result = analyze(y, p, missing)
        save(root / 'analysis.json', {'run_id': packet['run_id'], **result})
        commit()
        return status(root, packet, commit, 'completed_development_review_required',
                      cells=960, expansion_signal_pass=result['expansion_signal_pass'],
                      operational_pass=result['operational_pass'])
    except Exception as error:
        status(root, packet, commit, 'pipeline_failed', error=repr(error))
        raise
