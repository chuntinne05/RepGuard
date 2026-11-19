"""Post-hoc development replay of ALL v4 final artifacts, zero new inference.

Contracts are developer source interpretations, never independent human labels.
No gold files/scorer/reference reconstructions are imported or opened here.
"""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import json
import shutil
import zipfile

from repguard.verification.relational import (
    Catalog, ColumnRef, FilterSpec, JoinSpec, OrderSpec, OutputSpec, QueryContract,
    audit_query, fingerprint, search_schema,
)

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / 'results/workspace_v4'
OUT = ROOT / 'results/relational_v5'


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def field(table, name):
    return ColumnRef(table=table, column=name)


def contracts():
    def build(tid, outputs, **kwargs):
        return QueryContract(id=tid, question=next(t['question'] for t in packet['tasks'] if t['id'] == tid),
                             authority_ref='Developer-authored source/task interpretation, NOT independent human adjudication',
                             approval='development_only', outputs=tuple(OutputSpec(field=field(t, c)) for t, c in outputs), **kwargs)
    packet = json.loads((OLD / 'public_packet.json').read_text())
    a, b = 'mf_fundmanagernew', 'mf_personalinfo'
    balance = '其他存款性公司资产负债表'
    return {
        'task_269': [build('task_269', [('lc_largeshsubscription', c) for c in ('SHName', 'ActualShares', 'OughtShares')],
                           filters=(FilterSpec(field=field('lc_largeshsubscription', 'SecuCode'), operator='eq', value='000423'),))],
        'task_391': [build('task_391', [(balance, c) for c in ('截止日期', '总资产', '总负债', '国外净资产', '国外负债')],
                           filters=(FilterSpec(field=field(balance, '总资产'), operator='gt', value=50000000),),
                           ordering=(OrderSpec(field=field(balance, '截止日期'), descending=True),), limit='any',
                           open_questions=('Latest-row selection and date meaning not verified by this bounded checker',))],
        'task_380': [build('task_380', [(a, 'Name')], filters=(
                           FilterSpec(field=field(b, 'Nationality'), operator='ne', value='中国'),
                           FilterSpec(field=field(b, 'Nationality'), operator='not_null'),
                           FilterSpec(field=field(b, 'Nationality'), operator='ne', value='')),
                           joins=(JoinSpec(left=field(a, 'PersonalCode'), right=field(b, 'PersonalCode')),),
                           distinct='require')],
        'task_371': [build('task_371', [('mf_netvalueperformancehis', c), ('mf_netvalueperformancehis', 'RRSinceStart')],
                           distinct='forbid', open_questions=('SecuAbbr versus ChiNameAbbr is not independently adjudicated',))
                     for c in ('SecuAbbr', 'ChiNameAbbr')],
        'task_44': [build('task_44', [('treatment', 'treatmentname')],
                          filters=(FilterSpec(field=field('treatment', 'patientunitstayid'), operator='eq', value=2602861),),
                          exact_filters=False, ordering=(OrderSpec(field=field('treatment', 'treatmentid')),),
                          open_questions=('Patient ID mapping and latest timestamp need separate source-bound verification',))],
        'task_35': [],  # PDF assertions need another evidence adapter, never coerced into SQL proof.
    }


def run(out=OUT, report_name='relational_v5_development_replay.json'):
    destination = out / 'development_replay.json'
    if destination.exists():
        raise RuntimeError('Do not overwrite development readout')
    definitions = contracts()
    frozen_sources = [Path(__file__), ROOT / 'src/repguard/verification/relational.py', ROOT / 'experiments/relational_v5/tools.py', ROOT / 'research_ops/requirements-query-audit.txt']
    protocol = {'created_utc': datetime.now(timezone.utc).isoformat(),
                'status': 'POSTHOC_DEVELOPMENT; v4 model outcomes were already inspected; NOT preregistration or held-out evaluation',
                'tasks': list(definitions), 'include_all_36_final_trajectories': True, 'new_model_calls': 0,
                'gold_or_official_scorer_access': False, 'contract_approval': 'development_only',
                'human_annotations': 0, 'source_sha256': {str(p.relative_to(ROOT)): __import__('hashlib').sha256(p.read_bytes()).hexdigest() for p in frozen_sources},
                'contracts': {t: [c.model_dump(mode='json') for c in cs] for t, cs in definitions.items()},
                'interpretation_policy': 'Keep BOTH abbreviation contracts; do not select one using reference score. Missing/non-SQL finals remain unavailable.'}
    write(out / 'development_plan.json', protocol)
    with zipfile.ZipFile(out / 'development_source.zip', 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for p in frozen_sources:
            archive.write(p, str(p.relative_to(ROOT)))
    observations = []
    catalogs = {}
    for task in definitions:
        adapter = 'derived_v2' if task in ('task_269', 'task_391') else 'derived_v3'
        catalog = Catalog.from_manifest(json.loads((OLD / adapter / task / 'workspace.manifest.json').read_text()))
        catalogs[task] = catalog
        write(out / 'contracts' / (task + '.json'), [c.model_dump(mode='json') for c in definitions[task]])
        runid = '6a325835a376d02f1440fadf' if task in ('task_269', 'task_391') else '3af22795afdac39d725c3351'
        for workflow in ('A', 'B', 'AA', 'BB', 'AB', 'BA'):
            path = OLD / 'runs' / runid / 'trajectories' / task / workflow / 'trajectory.json'
            trajectory = json.loads(path.read_text())
            sql = (trajectory.get('final_result') or {}).get('sql')
            status = 'sql_artifact' if sql else 'non_sql_assertion' if trajectory.get('final_result') else 'no_final_artifact'
            receipts = [audit_query(c, sql, catalog).model_dump(mode='json') for c in definitions[task]] if sql else []
            observations.append({'task_id': task, 'workflow': workflow, 'kind': status,
                                 'trajectory_sha256': __import__('hashlib').sha256(path.read_bytes()).hexdigest(),
                                 'query_receipts': receipts, 'deployment_release_claim': False})
    summary = {'created_utc': datetime.now(timezone.utc).isoformat(), 'scope': protocol['status'],
               'new_model_calls': 0, 'human_annotations': 0, 'oracle_access_in_replay': False,
               'source_plan_sha256': fingerprint(protocol), 'observed_trajectories': len(observations),
               'artifact_types': dict(Counter(o['kind'] for o in observations)),
               'sql_receipts': sum(len(o['query_receipts']) for o in observations),
               'obligation_status_counts_over_interpretations_not_independent_tasks': dict(Counter(r['obligation_status'] for o in observations for r in o['query_receipts'])),
               'release_status_counts': dict(Counter(r['release_status'] for o in observations for r in o['query_receipts'])),
               'schema_discovery_example': search_schema(catalogs['task_380'], 'Nationality'),
               'observations': observations, 'scientific_gate': 'NOT_OPENED', 'history_fitted': False,
               'known_limitations': ['Posthoc developer contracts', 'No independent semantic labels', 'Flat SELECT subset only',
                                     'No universal SQL equivalence or NL/PDF verification', 'No measured human/product/transfer utility',
                                     'No gold values required by checker; contract formation cost still external']}
    assert len(observations) == 36
    assert all(r['release_status'] == 'needs_review' for o in observations for r in o['query_receipts'])
    write(destination, summary)
    report = ROOT / 'docs/reports/2026-11-09' / report_name
    if report.exists():
        raise RuntimeError('Do not overwrite published development artifact')
    shutil.copyfile(destination, report)
    print(json.dumps({k: v for k, v in summary.items() if k != 'observations'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, default=OUT)
    parser.add_argument('--report-name', default='relational_v5_development_replay.json')
    args = parser.parse_args()
    run(args.output_dir, args.report_name)
