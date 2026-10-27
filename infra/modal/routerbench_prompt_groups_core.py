"""Prompt-only MATH500 near-template groups; no outcome fields accepted."""
import hashlib
import re
import unicodedata


def canonical(text):
    return ' '.join(unicodedata.normalize('NFKC', text).casefold().split())


def query_hash(text):
    return hashlib.sha256(canonical(text).encode()).hexdigest()


def prompt_records(events):
    """Retain only prompt strings from a streaming JSON tokenizer."""
    item = {}
    for prefix, event, value in events:
        if prefix == 'records.item' and event == 'start_map':
            item = {}
        elif prefix in ('records.item.origin_query', 'records.item.prompt') and event == 'string':
            item[prefix.rsplit('.', 1)[1]] = value
        elif prefix == 'records.item' and event == 'end_map':
            text = item.get('origin_query') or item.get('prompt', '')
            if text.strip():
                yield {'query_sha256': query_hash(text), 'prompt': text}


def grams(text, n):
    return {text[i:i+n] for i in range(len(text) - n + 1)} if len(text) >= n else {text}


def word_grams(tokens, n):
    return {tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)} if len(tokens) >= n else {tuple(tokens)}


def jaccard(a, b):
    return len(a & b) / len(a | b) if a or b else 1.


def group(prompts, pilot_ids):
    if len(prompts) != 500 or len(set(prompts)) != 500 or not set(pilot_ids) <= set(prompts) or len(set(pilot_ids)) != 48:
        raise ValueError('Changed common/pilot question coverage')
    ids = sorted(prompts)
    texts = [canonical(prompts[q]) for q in ids]
    if any(query_hash(prompts[q]) != q for q in ids):
        raise ValueError('Prompt hash mismatch')
    raw = [grams(t, 5) for t in texts]
    masked = [word_grams(re.findall(r'\w+|[^\w\s]', re.sub(r'\d+', '0', t)), 3) for t in texts]
    parent = list(range(len(ids)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    def union(i, j):
        a, b = find(i), find(j)
        if a != b:
            parent[max(a, b)] = min(a, b)
    edges, review = [], []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            length_ratio = min(len(texts[i]), len(texts[j])) / max(len(texts[i]), len(texts[j]))
            if length_ratio < .70:
                continue
            r = jaccard(raw[i], raw[j])
            m = jaccard(masked[i], masked[j]) if r >= .35 else 0.
            entry = {'a': ids[i], 'b': ids[j], 'raw_char5': round(r, 8),
                     'masked_word3': round(m, 8), 'length_ratio': round(length_ratio, 8)}
            if r >= .82 or (m >= .80 and r >= .45):
                edges.append(entry)
                union(i, j)
            elif r >= .65 or (m >= .70 and r >= .35):
                review.append(entry)
    groups = {}
    for i, q in enumerate(ids):
        groups.setdefault(find(i), []).append(q)
    components = sorted((sorted(members) for members in groups.values()), key=lambda x: x[0])
    pilot = set(pilot_ids)
    marked = [x for x in components if pilot.intersection(x)]
    clean = [x for x in components if not pilot.intersection(x)]
    return {'components': components, 'linked_edges': edges, 'review_edges': review,
            'total_questions': 500, 'total_groups': len(components),
            'multi_question_groups': sum(len(x) > 1 for x in components),
            'largest_group': max(map(len, components)),
            'pilot_questions': 48, 'pilot_touched_groups': len(marked),
            'pilot_touched_questions': sum(map(len, marked)),
            'remaining_groups': len(clean), 'remaining_questions': sum(map(len, clean)),
            'linked_edge_count': len(edges), 'review_edge_count': len(review)}
