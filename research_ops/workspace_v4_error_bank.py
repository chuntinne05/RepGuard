"""Describe audited development outcomes without inventing semantic labels."""
import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from experiments.workspace_v4.agent import write
from experiments.workspace_v4.tools import sha


def build(prefix_result, recovery_result, prefix_root, recovery_root, destination):
    first = json.loads(prefix_result.read_text())
    second = json.loads(recovery_result.read_text())
    assert first['receipt_audit'] == second['receipt_audit'] == 'PASS'
    assert first['study_complete'] is False and first['interrupted_prefix_diagnostic_only'] is True
    assert second['study_complete'] is True
    expected = {'task_269', 'task_391', 'task_380', 'task_371', 'task_44', 'task_35'}
    assert set(first['scored_task_ids']).isdisjoint(second['scored_task_ids'])
    assert set(first['scored_task_ids']) | set(second['scored_task_ids']) == expected
    rows = []
    for result, root, block in ((first, prefix_root, 'interrupted_prefix_original_binding'),
                                (second, recovery_root, 'recovery_python_numeric_binding')):
        for score in result['tasks']:
            task, workflow = score['task_id'], score['workflow']
            trajectory_path = root / 'trajectories' / task / workflow / 'trajectory.json'
            trajectory = json.loads(trajectory_path.read_text())
            observations = trajectory['tool_observations']
            match = score['official_relation_result']['passed']
            category = ('reference_relation_match' if match else 'no_final_artifact' if not trajectory['final_result']
                        else 'final_relation_mismatch')
            parent = None
            if len(workflow) == 2:
                parent = json.loads((root / 'trajectories' / task / workflow[0] / 'trajectory.json').read_text())
            rows.append({**score, 'plan_id': result['plan_id'], 'adapter_block': block,
                         'observable_category': category, 'trajectory_sha256': sha(trajectory_path),
                         'tool_counts': dict(Counter(o.get('action', {}).get('tool', 'invalid_action') for o in observations)),
                         'zero_row_queries': sum(o.get('action', {}).get('tool') == 'query' and o.get('observation', {}).get('rows') == 0 for o in observations),
                         'successful_artifacts_created_or_reused': len(trajectory['result_records']),
                         'final_retains_parent_bytes': bool(parent and trajectory['prediction_sha256'] and trajectory['prediction_sha256'] == parent['prediction_sha256']),
                         'review_without_new_tool_observations': len(workflow) == 2 and not observations,
                         'tool_errors': [o['error'] for o in observations if 'error' in o],
                         'semantic_error_annotation': None, 'independent_human_review_completed': False})
    assert len(rows) == 36 and len({(r['task_id'], r['workflow']) for r in rows}) == 36
    summary = {'created_utc': datetime.now(timezone.utc).isoformat(),
               'scope': 'Composite engineering diagnostic: interrupted first2 + numeric-binding-amended remaining4. NOT completion of original six-task plan, official-original benchmark score or confirmation.',
               'blocks': [{'plan_id': r['plan_id'], 'tasks': r['scored_task_ids'], 'study_complete': r['study_complete'],
                           'actual_corpus_model_calls': r['actual_corpus_model_calls']} for r in (first, second)],
               'input_amended_tasks': ['task_391'], 'actual_corpus_model_calls': first['actual_corpus_model_calls'] + second['actual_corpus_model_calls'],
               'actual_input_tokens': first['actual_input_tokens'] + second['actual_input_tokens'],
               'actual_output_tokens': first['actual_output_tokens'] + second['actual_output_tokens'],
               'length_stops': first['length_stops'] + second['length_stops'],
               'observable_counts': dict(Counter(r['observable_category'] for r in rows)),
               'tool_or_schema_errors': sum(r['tool_or_schema_errors'] for r in rows),
               'workflows': {w: {'reference_relation_matches': sum(r['official_relation_result']['passed'] for r in rows if r['workflow'] == w),
                                 'tasks': 6, 'policy_cost_including_parent': {k: sum(r['policy_cost_including_parent'][k] for r in rows if r['workflow'] == w)
                                  for k in ('model_calls', 'input_tokens', 'output_tokens', 'terminal_serving_seconds')}}
                             for w in ('A', 'B', 'AA', 'BB', 'AB', 'BA')},
               'tasks': rows, 'scientific_primary_effect': None, 'scientific_expansion_gate': 'NOT_OPENED',
               'history_fitted': False, 'human_annotations_completed': 0,
               'observables_are_not_causal_or_semantic_failure_labels': True,
               'source_score_files': [{'path': str(p), 'sha256': sha(p)} for p in (prefix_result, recovery_result)],
               'error_bank_source_sha256': sha(Path(__file__))}
    assert not destination.exists(), 'Do not overwrite error bank'
    write(destination, summary)
    print(json.dumps({k: v for k, v in summary.items() if k != 'tasks'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('prefix-result', 'recovery-result', 'prefix-root', 'recovery-root', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    build(args.prefix_result, args.recovery_result, args.prefix_root, args.recovery_root, args.output)
