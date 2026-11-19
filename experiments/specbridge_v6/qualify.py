"""Development-only native grading/engine qualification, zero model calls."""
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path

from .grading import ROOT, SOURCE, load_grader, run_readonly, sha

OUT = ROOT / 'results/specbridge_v6'


def profile(sql):
    import sqlglot
    from sqlglot import exp
    root = sqlglot.parse_one(sql, read='sqlite')
    return {'select_scopes': len(list(root.find_all(exp.Select))), 'cte': bool(root.find(exp.CTE)),
            'subquery': bool(root.find(exp.Subquery)), 'window': bool(root.find(exp.Window)),
            'outer_join': any(j.args.get('side') for j in root.find_all(exp.Join)),
            'group': bool(root.find(exp.Group)), 'having': bool(root.find(exp.Having)),
            'distinct': bool(root.find(exp.Distinct)), 'limit': bool(root.find(exp.Limit)),
            'arithmetic': any(root.find(t) is not None for t in (exp.Add, exp.Sub, exp.Mul, exp.Div)),
            'case': bool(root.find(exp.Case)), 'or': bool(root.find(exp.Or)),
            'joins': len(list(root.find_all(exp.Join)))}


def main():
    destination = OUT / 'qualification.json'
    if destination.exists():
        raise RuntimeError('Do not overwrite qualification')
    matches, grader_receipt = load_grader()
    split = json.loads((SOURCE / 'metadata_split.json').read_text())
    tasks = sorted((r for r in split['metadata'] if r['split'] == 'development'), key=lambda r: r['id'])
    source_receipt = json.loads((SOURCE / 'external_preparation.json').read_text())
    for db in source_receipt['downloaded_development_databases']:
        if sha(ROOT / db['path']) != db['sha256']:
            raise ValueError('Development source changed')
    records = []
    controls = []
    system_differences = []
    import sqlite3
    import sqlean
    for meta in tasks:
        task = json.loads((SOURCE / 'evaluation/development' / (meta['id'] + '.json')).read_text())
        database = SOURCE / 'pinned/benchmark/databases' / (task['database'] + '.sqlite')
        for reading in ('A', 'B'):
            executed = run_readonly(database, task['sql'][reading])
            got = matches(task, executed['rows'])
            other = 'B' if reading == 'A' else 'A'
            record = {'id': task['id'], 'database': task['database'], 'reading': reading,
                      'state': executed['state'], 'native_matches': got, 'own_match': reading in got,
                      'opposite_rejected': other not in got, 'rows': len(executed['rows']) if executed['rows'] is not None else None,
                      'seconds': executed.get('seconds'), 'error': executed.get('error'), 'features': profile(task['sql'][reading])}
            records.append(record)
            if executed['state'] == 'ok':
                rows = executed['rows']
                width = len(rows[0]) if rows else task['grading']['grader']['columns']
                extra = rows + [list(rows[0]) if rows else ['__extra__'] * width]
                controls.append({'id': task['id'], 'reading': reading,
                                 'extra_row_rejected': reading not in matches(task, extra),
                                 'missing_output_rejected': matches(task, None) == []})
            system = run_readonly(database, task['sql'][reading], engine=sqlite3)
            if system['state'] != 'ok' or matches(task, system['rows']) != got:
                system_differences.append({'id': task['id'], 'reading': reading, 'system_state': system['state'],
                                           'system_matches': matches(task, system['rows']), 'native_matches': got})
    all_reference_pass = len(records) == 90 and all(r['state'] == 'ok' and r['own_match'] for r in records)
    distinct = all(r['opposite_rejected'] for r in records)
    controls_pass = len(controls) == 90 and all(c['extra_row_rejected'] and c['missing_output_rejected'] for c in controls)
    features = {k: sum(bool(r['features'][k]) for r in records) for k in records[0]['features']}
    result = {'created_utc': datetime.now(timezone.utc).isoformat(), 'scope': 'ALL45development tasks only; no validation/reserve execution',
              'upstream_revision': 'a51be850a113a6b7c0ada57ad3c7806c6c3f25a4', 'grade_loading': grader_receipt,
              'native_engine': {'package': 'sqlean.py==0.21.5.3', 'sqlite': sqlean.sqlite_version}, 'system_sqlite': sqlite3.sqlite_version,
              'development_tasks': len(tasks), 'reference_queries': len(records), 'own_reference_matches': sum(r['own_match'] for r in records),
              'opposite_reference_rejected': sum(r['opposite_rejected'] for r in records), 'controls': controls,
              'all_reference_checks_pass': all_reference_pass, 'all_control_checks_pass': controls_pass,
              'all_interpretations_distinguishable': distinct, 'engine_grading_differences': system_differences,
              'native_profile': features, 'profile_is_not_semantic_contract_coverage': True,
              'references': records, 'new_model_calls': 0, 'new_human_annotations': 0,
              'go_for_bounded_development_baseline': all_reference_pass and controls_pass and distinct,
              'scientific_expansion_gate': 'NOT_OPENED', 'qualification_source_sha256': sha(Path(__file__))}
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    (ROOT / 'docs/reports/2026-11-09/specbridge_v6_qualification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('references', 'controls', 'grade_loading')}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
