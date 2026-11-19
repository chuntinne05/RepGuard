"""Pinned external source preparation; no model outputs or upstream code run.

Splits databases by metadata before inspecting any query/reference values.
Public prompts and reference packages are saved separately. Only development
databases are downloaded. This is preparation, not an executed model study.
"""
import hashlib
import json
import sqlite3
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'results/relational_v5/source_intake/SpecBridge'
REPO = 'Xyc-arch/specbridge-artifact'
REVISION = 'a51be850a113a6b7c0ada57ad3c7806c6c3f25a4'


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as target:
        target.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def fetch(path, expected, cap):
    dest = BASE / 'pinned' / path
    if dest.exists():
        data = dest.read_bytes()
    else:
        with urllib.request.urlopen(f'https://raw.githubusercontent.com/{REPO}/{REVISION}/{path}', timeout=90) as response:
            data = response.read(cap + 1)
        if len(data) > cap:
            raise ValueError('Source byte cap')
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    if hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() != expected:
        raise ValueError('Git blob hash failed: ' + path)
    return dest, data


def main():
    receipt = BASE / 'external_preparation.json'
    if receipt.exists():
        raise RuntimeError('Already prepared; do not overwrite splits')
    tree = json.loads((BASE / 'tree.json').read_text())
    entries = {r['path']: r for r in tree['tree'] if r['type'] == 'blob'}
    _, raw = fetch('benchmark/request_sets.jsonl', entries['benchmark/request_sets.jsonl']['sha'], 10_000_000)
    records = [json.loads(line) for line in raw.decode().splitlines() if line.strip()]
    eligible = [r for r in records if r.get('accepted') is True]
    # Only metadata is consulted for this split. Do not hash SQL/answers/prompts.
    by_source = defaultdict(set)
    for record in eligible:
        by_source[record['source']].add(record['database'])
    allocation = {}
    for source, databases in sorted(by_source.items()):
        ordered = sorted(databases, key=lambda db: hashlib.sha256(('repguard-external-v5-20261109|' + source + '|' + db).encode()).hexdigest())
        if len(ordered) < 3:
            raise ValueError('Too few databases for source-disjoint stages')
        allocation.update({db: ('development' if i == 0 else 'validation' if i == 1 else 'reserved_confirmation') for i, db in enumerate(ordered)})
    metadata = [{'id': r['id'], 'database': r['database'], 'source': r['source'],
                 'choice_type': r.get('choice_type'), 'split': allocation[r['database']]} for r in eligible]
    split = {'created_utc': datetime.now(timezone.utc).isoformat(), 'repository': REPO, 'revision': REVISION,
             'purpose': 'External preparation only, NOT registered confirmation or new human annotations',
             'selection': 'Upstream accepted metadata, then SHA256 database order within each upstream source; no model outcomes/reference SQL consulted for allocation',
             'raw_bank_sha256': hashlib.sha256(raw).hexdigest(), 'records': len(records), 'upstream_accepted_tasks': len(eligible),
             'database_split': allocation, 'counts': dict(Counter(r['split'] for r in metadata)), 'metadata': metadata,
             'dependency_warning': 'Same choice templates/generator may cross database splits; this is schema/source splitting, not independent choice-family or benchmark-level generalization.'}
    write(BASE / 'metadata_split.json', split)
    # Public agent input fields are exactly the requests/schema/docs; no hidden
    # reference SQL, grading values or source-derived operator hints are added.
    for record in eligible:
        tid = str(record['id'])
        if any(c in tid for c in ('/', '\\')) or tid in ('.', '..'):
            raise ValueError('Unsafe task ID')
        stage = allocation[record['database']]
        write(BASE / 'public' / stage / (tid + '.json'), {k: record[k] for k in ('id', 'database', 'requests', 'context')})
        write(BASE / 'evaluation' / stage / (tid + '.json'), record)
    databases = []
    for database, stage in sorted(allocation.items()):
        if stage != 'development':
            continue
        path = 'benchmark/databases/' + database + '.sqlite'
        if path not in entries:
            raise ValueError('Database mapping needs source review: ' + database)
        location, content = fetch(path, entries[path]['sha'], 100_000_000)
        if not content.startswith(b'SQLite format 3\0'):
            raise ValueError('Not an actual SQLite database')
        connection = sqlite3.connect(location.resolve().as_uri() + '?mode=ro&immutable=1', uri=True)
        try:
            connection.execute('PRAGMA query_only=ON'); connection.execute('PRAGMA trusted_schema=OFF')
            integrity = connection.execute('PRAGMA quick_check').fetchall()
            tables = [r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        finally:
            connection.close()
        if integrity != [('ok',)]:
            raise ValueError('Source database quick_check failed')
        databases.append({'database': database, 'path': str(location.relative_to(ROOT)), 'bytes': len(content),
                          'sha256': hashlib.sha256(content).hexdigest(), 'quick_check': 'ok', 'table_count': len(tables)})
    value = {'created_utc': datetime.now(timezone.utc).isoformat(), 'repository': REPO, 'revision': REVISION,
             'source_code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             'task_metadata_split_sha256': hashlib.sha256((BASE / 'metadata_split.json').read_bytes()).hexdigest(),
             'accepted_tasks': len(eligible), 'counts': split['counts'], 'database_split': allocation,
             'downloaded_development_databases': databases, 'validation_and_confirmation_databases_downloaded': False,
             'public_prompt_and_evaluation_packages_separate': True, 'cached_model_outputs_downloaded': False,
             'upstream_scorer_executed': False, 'new_model_calls': 0, 'new_human_annotations': 0,
             'licence': 'Code MIT; request-set benchmark/databases CC BY-SA4.0 per pinned DATA_LICENSE.md; retain upstream attribution/share-alike for any derived data release',
             'not_ready_for_model_confirmation': ['Native scorer and interpretation oracle still need validation',
                                                   'Operator/ambiguity coverage qualification still needed',
                                                   'Strong-single and same-checker controls not yet run',
                                                   'Protocol/sample size not frozen; no user benefit measured']}
    write(receipt, value)
    write(ROOT / 'docs/reports/2026-11-09/relational_v5_external_preparation.json', value)
    print(json.dumps(value, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
