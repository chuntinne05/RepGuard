"""Layout amendment based exclusively on verified archive member names."""
from pathlib import PurePosixPath
from routerbench_intake_core import digest, normalized_query, metadata_from_events, inspect_json, summarize


def classify(name):
    p = PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts:
        raise ValueError('Unsafe archive member')
    if 'mmlu' in name.casefold():
        return {'skip': 'excluded_mmlu'}
    if p.suffix.lower() != '.json':
        return {'skip': 'not_json'}
    if not p.parts or p.parts[0] != 'bench-release':
        return {'skip': 'outside_release'}
    tail = p.parts[1:]
    if len(tail) < 3:
        return {'skip': 'unsupported_path'}
    return {'dataset': tail[0], 'partition': '/'.join(tail[1:-2]) or 'unspecified', 'model': tail[-2]}
