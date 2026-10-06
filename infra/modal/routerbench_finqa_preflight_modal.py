"""Gold-blind schema preflight for the selected FinQA development questions."""
from pathlib import Path
import modal

app = modal.App('repguard-finqa-schema-preflight-v1')
archive = modal.Volume.from_name('repguard-routerbench-intake-checkpoints-v1')
image = modal.Image.debian_slim(python_version='3.11').pip_install('ijson==3.3.0')


@app.function(image=image, volumes={'/archive': archive}, cpu=1, memory=2048, timeout=1800)
def inspect(member_name: str, selected_positions: list[int]):
    import ijson
    import tarfile
    archive.reload()
    wanted = set(selected_positions)
    if len(wanted) != len(selected_positions) or len(wanted) != 48 or min(wanted) < 0:
        raise ValueError('Expected exactly 48 nonnegative positions')
    source = Path('/archive/runs/8844b39df2d3d6b37eface11/bench-release.tar.gz')
    result = {}; found = 0
    with tarfile.open(source, 'r|gz') as tar:
        for member in tar:
            if member.name != member_name:
                continue
            if not member.isfile() or member.size > 100 * 1024 * 1024:
                raise ValueError('Unexpected member')
            found += 1
            row = {}; position = -1
            with tar.extractfile(member) as stream:
                for prefix, event, value in ijson.parse(stream):
                    if prefix == 'records.item' and event == 'start_map':
                        row = {}; position += 1
                    elif position in wanted and prefix in ('records.item.origin_query', 'records.item.prompt',
                                                           'records.item.raw_output', 'records.item.prediction') and event == 'string':
                        row[prefix.rsplit('.', 1)[1]] = value
                    elif position in wanted and prefix == 'records.item' and event == 'end_map':
                        origin, prompt = row.get('origin_query', ''), row.get('prompt', '')
                        output = row.get('raw_output') or row.get('prediction', '')
                        result[position] = {'origin_chars': len(origin), 'prompt_chars': len(prompt),
                                            'output_chars': len(output), 'prompt_contains_origin': origin in prompt,
                                            'prompt_prefix': prompt[:300]}
    if found != 1 or set(result) != wanted:
        raise ValueError('Incomplete selected schema preflight')
    return result


@app.function(image=image, volumes={'/archive': archive}, cpu=1, memory=4096, timeout=1800)
def inspect_many(selections: dict[str, list[int]]):
    """Aggregate only field lengths and final-answer markers; no outcomes or strings returned."""
    import ijson
    import tarfile
    archive.reload()
    if len(selections) != 20 or any(len(set(v)) != 48 or len(v) != 48 for v in selections.values()):
        raise ValueError('Expected 20 models with 48 unique positions each')
    source = Path('/archive/runs/8844b39df2d3d6b37eface11/bench-release.tar.gz')
    result = {}
    with tarfile.open(source, 'r|gz') as tar:
        for member in tar:
            if member.name not in selections:
                continue
            if member.name in result or not member.isfile() or member.size > 100 * 1024 * 1024:
                raise ValueError('Duplicate or unsupported member')
            wanted = set(selections[member.name])
            metrics = {'selected': 0, 'prompt_missing': 0, 'prompt_over_16000_chars': 0,
                       'output_missing': 0, 'output_over_10000_chars': 0,
                       'output_over_20000_chars': 0, 'has_boxed': 0,
                       'prompt_max_chars': 0, 'output_max_chars': 0}
            row = {}; position = -1
            with tar.extractfile(member) as stream:
                for prefix, event, value in ijson.parse(stream):
                    if prefix == 'records.item' and event == 'start_map':
                        row = {}; position += 1
                    elif position in wanted and prefix in ('records.item.origin_query', 'records.item.prompt',
                                                           'records.item.raw_output', 'records.item.prediction') and event == 'string':
                        row[prefix.rsplit('.', 1)[1]] = value
                    elif position in wanted and prefix == 'records.item' and event == 'end_map':
                        prompt = row.get('prompt', '')
                        output = row.get('raw_output') or row.get('prediction', '')
                        metrics['selected'] += 1
                        metrics['prompt_missing'] += int(not prompt.strip())
                        metrics['prompt_over_16000_chars'] += int(len(prompt) > 16000)
                        metrics['output_missing'] += int(not output.strip())
                        metrics['output_over_10000_chars'] += int(len(output) > 10000)
                        metrics['output_over_20000_chars'] += int(len(output) > 20000)
                        metrics['has_boxed'] += int('\\boxed{' in output)
                        metrics['prompt_max_chars'] = max(metrics['prompt_max_chars'], len(prompt))
                        metrics['output_max_chars'] = max(metrics['output_max_chars'], len(output))
            if metrics['selected'] != 48:
                raise ValueError('Incomplete preflight positions')
            result[member.name] = metrics
    if set(result) != set(selections):
        raise ValueError('Missing preflight member')
    return result
