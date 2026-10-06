"""Gold-blind audit of selected FinQA solver-output fields after pilot failure."""
import json
from pathlib import Path

import modal

app = modal.App('repguard-finqa-field-audit-v1')
archive = modal.Volume.from_name('repguard-routerbench-intake-checkpoints-v1')
image = modal.Image.debian_slim(python_version='3.11').pip_install('ijson==3.3.0')
SOURCE = '/archive/runs/8844b39df2d3d6b37eface11/bench-release.tar.gz'


@app.function(image=image, volumes={'/archive': archive}, cpu=1, memory=4096, timeout=1800)
def inspect(selections: dict[str, dict]):
    import ijson
    import tarfile

    archive.reload()
    if len(selections) != 20 or any(len(item['positions']) != 48 for item in selections.values()):
        raise ValueError('Expected frozen 20-model, 48-question selection')
    result = {}
    with tarfile.open(SOURCE, 'r|gz') as tar:
        for member in tar:
            if member.name not in selections:
                continue
            if member.name in result or not member.isfile() or member.size > 100 * 1024 * 1024:
                raise ValueError('Duplicate or unsupported selected member')
            item = selections[member.name]
            positions = set(item['positions'])
            metrics = {'model': item['model'], 'selected': 0,
                       'prediction_present': 0, 'prediction_same_as_raw': 0,
                       'prediction_has_boxed': 0, 'raw_has_boxed': 0,
                       'no_raw_box_prediction_present': 0,
                       'prediction_lengths': [], 'raw_lengths': [],
                       'no_raw_box_prediction_examples': []}
            row = {}; position = -1
            with tar.extractfile(member) as stream:
                for prefix, event, value in ijson.parse(stream):
                    if prefix == 'records.item' and event == 'start_map':
                        row = {}; position += 1
                    elif position in positions and prefix in ('records.item.raw_output', 'records.item.prediction') and event == 'string':
                        row[prefix.rsplit('.', 1)[1]] = value
                    elif position in positions and prefix == 'records.item' and event == 'end_map':
                        raw = row.get('raw_output', '')
                        pred = row.get('prediction', '')
                        raw_box = '\\boxed{' in raw
                        metrics['selected'] += 1
                        metrics['prediction_present'] += bool(pred.strip())
                        metrics['prediction_same_as_raw'] += bool(pred) and pred == raw
                        metrics['prediction_has_boxed'] += '\\boxed{' in pred
                        metrics['raw_has_boxed'] += raw_box
                        metrics['no_raw_box_prediction_present'] += not raw_box and bool(pred.strip())
                        metrics['prediction_lengths'].append(len(pred))
                        metrics['raw_lengths'].append(len(raw))
                        if (not raw_box and pred.strip() and
                                len(metrics['no_raw_box_prediction_examples']) < 2):
                            metrics['no_raw_box_prediction_examples'].append({
                                'position': position, 'prediction_prefix': pred[:240],
                                'raw_tail': raw[-240:]})
            if metrics['selected'] != 48:
                raise ValueError('Missing selected record in member')
            result[member.name] = metrics
    if set(result) != set(selections):
        raise ValueError('Missing selected member')
    return result


@app.local_entrypoint()
def main():
    root = Path(__file__).resolve().parents[2]
    packet = json.loads((root / 'results/routerbench_finqa_feedback_v1/packet_private.json').read_text())
    if packet['run_id'] != '0fad63edd346eb0591fd99e1':
        raise ValueError('Unexpected FinQA pilot packet')
    selection = {packet['members'][model]: {
        'model': model, 'positions': list(packet['positions'][model].values())}
        for model in packet['models']}
    result = inspect.remote(selection)
    out = root / 'results/routerbench_finqa_feedback_v1/field_audit_private.json'
    out.write_text(json.dumps({'parent_run_id': packet['run_id'], 'members': result}, indent=2) + '\n')
    print(json.dumps({'parent_run_id': packet['run_id'], 'member_count': len(result),
                      'selected_records': sum(x['selected'] for x in result.values()),
                      'prediction_present': sum(x['prediction_present'] for x in result.values()),
                      'no_raw_box_prediction_present': sum(x['no_raw_box_prediction_present'] for x in result.values()),
                      'private_result': str(out)}))
