"""Re-execute every v4 final SQL through new tools; no gold/model calls.

This checks artifact reproducibility and tool integration, not task accuracy.
"""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import shutil

from experiments.relational_v5.tools import AuditedWorkspaceTools
from repguard.verification.relational import QueryContract

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / 'results/workspace_v4'
OUT = ROOT / 'results/relational_v5/analysis_v2'


def run():
    dest = OUT / 'execution_replay.json'
    if dest.exists():
        raise RuntimeError('Do not overwrite execution replay')
    plan = json.loads((OUT / 'development_plan.json').read_text())
    rows = []
    for tid, definitions in plan['contracts'].items():
        if not definitions:
            continue
        contract = QueryContract.model_validate(definitions[0])
        adapter = 'derived_v2' if tid in ('task_269', 'task_391') else 'derived_v3'
        runid = '6a325835a376d02f1440fadf' if tid in ('task_269', 'task_391') else '3af22795afdac39d725c3351'
        for wf in ('A', 'B', 'AA', 'BB', 'AB', 'BA'):
            trajectory = json.loads((OLD / 'runs' / runid / 'trajectories' / tid / wf / 'trajectory.json').read_text())
            original = trajectory.get('final_result') or {}
            if 'sql' not in original:
                continue
            tools = AuditedWorkspaceTools(OLD / 'inputs/input' / tid / 'context',
                                          OLD / adapter / tid / 'workspace.sqlite', OUT / 'execution_artifacts' / tid / wf,
                                          contract=contract)
            executed = tools.dispatch({'tool': 'query', 'args': {'sql': original['sql']}})
            reaudit = tools.dispatch({'tool': 'query_audit', 'args': {'result_id': executed['result_id']}})
            rows.append({'task_id': tid, 'workflow': wf, 'sql_sha256': hashlib.sha256(original['sql'].encode()).hexdigest(),
                         'rows': executed['rows'], 'historical_output_sha256': original['output_sha256'],
                         'replayed_output_sha256': executed['output_sha256'],
                         'output_bytes_reproduced': original['output_sha256'] == executed['output_sha256'],
                         'host_execution_recorded': reaudit['host_execution_recorded'],
                         'query_obligations': reaudit['query_obligations']})
    summary = {'created_utc': datetime.now(timezone.utc).isoformat(),
               'scope': 'Development engineering reproducibility; SAME old SQL, no repair, gold, scorer or new model inference',
               'new_model_calls': 0, 'read_only_sql_executions': len(rows),
               'output_bytes_reproduced': sum(r['output_bytes_reproduced'] for r in rows),
               'interpretation_policy': 'First contract used for wrapper only; ambiguous task371 remains needs_review, alternatives retained in separate structural replay',
               'business_accuracy_measured': False, 'human_annotations_added': 0, 'observations': rows,
               'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), ROOT / 'experiments/relational_v5/tools.py', ROOT / 'src/repguard/verification/relational.py')}}
    assert len(rows) == 20 and all(not r['query_obligations']['semantic_truth_certified'] for r in rows)
    dest.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    shutil.copyfile(dest, ROOT / 'docs/reports/2026-11-09/relational_v5_execution_replay.json')
    print(json.dumps({k: v for k, v in summary.items() if k != 'observations'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    run()
