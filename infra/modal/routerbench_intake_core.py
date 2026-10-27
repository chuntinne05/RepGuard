"""Outcome-blind metadata intake for a pinned public archive. Never extract paths."""
import hashlib
import json
import unicodedata
from pathlib import PurePosixPath


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def normalized_query(value):
    return ' '.join(unicodedata.normalize('NFKC', value).casefold().split())


def classify(name):
    p = PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts:
        raise ValueError('Unsafe archive member')
    if 'mmlu' in name.casefold():
        return {'skip': 'excluded_mmlu'}
    if p.suffix.lower() != '.json':
        return {'skip': 'not_json'}
    if 'bench' not in p.parts:
        return {'skip': 'outside_bench'}
    tail = p.parts[p.parts.index('bench') + 1:]
    if len(tail) < 4:
        return {'skip': 'unsupported_path'}
    return {'dataset': tail[0], 'partition': '/'.join(tail[1:-2]), 'model': tail[-2]}


def metadata_from_events(events):
    """Tokenization traverses JSON; only allowed metadata values are retained/read.

    Gold/reference/output values never enter artifacts or selection. Excluded
    MMLU files are not tokenized at all. No claim that downloading a tar excludes bytes.
    """
    records, fields, item, total, unsupported = [], set(), {}, 0, 0
    for prefix, event, value in events:
        if prefix == 'records.item' and event == 'start_map':
            item = {}
        elif prefix == 'records.item' and event == 'map_key':
            fields.add(value)
        elif prefix in ('records.item.origin_query', 'records.item.prompt') and event == 'string':
            item[prefix.rsplit('.', 1)[1]] = value
        elif prefix == 'records.item.index' and event in ('string', 'number'):
            item['index'] = str(value)
        elif prefix == 'records.item' and event == 'end_map':
            total += 1
            key = 'origin_query' if item.get('origin_query', '').strip() else 'prompt'
            text = item.get(key, '')
            if not text.strip():
                unsupported += 1
                continue
            canonical = normalized_query(text)
            records.append({'query_sha256': hashlib.sha256(canonical.encode()).hexdigest(),
                            'index': item.get('index'), 'chars': len(text), 'query_field': key})
    return {'record_count': total, 'supported_count': len(records), 'unsupported_count': unsupported,
            'record_fields': sorted(fields), 'records': records}


def inspect_json(stream):
    import ijson
    return metadata_from_events(ijson.parse(stream))


def summarize(files):
    by_dataset = {}
    for item in files:
        if 'dataset' not in item or not item.get('supported_count'):
            continue
        key = item['dataset'] + '/' + item['partition']
        models = by_dataset.setdefault(key, {})
        model = models.setdefault(item['model'], {'queries': set(), 'files': [], 'record_count': 0})
        model['queries'].update(r['query_sha256'] for r in item['records'])
        model['files'].append(item['member'])
        model['record_count'] += item['record_count']
    out = {}
    for key, models in sorted(by_dataset.items()):
        sets = [m['queries'] for m in models.values()]
        out[key] = {'model_count': len(models), 'union_queries': len(set.union(*sets)),
                    'common_queries_all_models': len(set.intersection(*sets)),
                    'models': {m: {'unique_queries': len(v['queries']), 'records': v['record_count'],
                                   'files': v['files']} for m, v in sorted(models.items())}}
    return out
