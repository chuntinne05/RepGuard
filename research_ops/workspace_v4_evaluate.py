"""Offline receipt audit and pinned relation scoring. Never calls a model.

No score is published until all registered trajectories and receipts pass audit.
The six development tasks cannot establish method superiority or transfer.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import hashlib
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from experiments.workspace_v4.agent import digest, write
from experiments.workspace_v4.tools import relation_fingerprint, sha

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/workspace_v4'
SCORER = ROOT / 'results/general_verification_v1/source_intake/DataSpace/evaluation/evaluate.py'
SCORER_SHA = '9eeb1edcc72d963610f497ebf98287887659f52656092ada0a55290a066bfbc8'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit_response(record, attempt, plan, task, workflow, step):
    rid = digest([plan['plan_id'], task, workflow, step])[:28]
    require(record['request_id'] == attempt['request_id'] == rid, 'Request identity')
    require(record['plan_id'] == plan['plan_id'] and record['task_id'] == task
            and record['workflow'] == workflow and record['step'] == step, 'Response membership')
    require(record['messages_sha256'] == attempt['messages_sha256'] == digest(record['messages']), 'Message digest')
    body = record['request_body']
    require(body['messages'] == record['messages'], 'Actual provider messages')
    model = plan['models'][workflow[-1]]
    require(record['model'] == body['model'] == record['response']['model'] == model['name'], 'Model name')
    require(record['model_digest'] == model['digest'], 'Model digest')
    require(record['provider'] == 'ollama_modal' and record['live_inference'] is True, 'Provider receipt')
    require(record['evaluation_volume_mounted'] is False and record['reference_reconstruction_code_in_image'] is False, 'Oracle isolation receipt')
    require(record['weights_read_only'] is True and 'L40S' in record['gpu'], 'Serving hardware')
    require(record['ollama_version'] == plan['ollama'] and record['response']['done'] is True, 'Serving completion')
    require(body['stream'] is False and body['think'] is False and body['format'] == 'json', 'Provider options')
    require(body['options'] == {'temperature': 0, 'seed': 20261109, 'num_ctx': 32768, 'num_predict': 2048}, 'Generation parameters')
    for field in ('prompt_eval_count', 'eval_count', 'total_duration'):
        require(isinstance(record['response'][field], int) and record['response'][field] >= 0, 'Usage counter')


def policy_cost(terminal, parent=None):
    records = [terminal] + ([parent] if parent else [])
    return {key: sum(r[key] for r in records)
            for key in ('model_calls', 'input_tokens', 'output_tokens', 'terminal_serving_seconds')}


def audit_run(plan, run_root, source_archive=None, interrupted_prefix=None):
    require(digest({k: v for k, v in plan.items() if k != 'plan_id'})[:24] == plan['plan_id'], 'Plan identity')
    if source_archive:
        with zipfile.ZipFile(source_archive) as archive:
            for rel, expected in plan['source_hashes'].items():
                require(hashlib.sha256(archive.read(rel)).hexdigest() == expected, 'Frozen archived source changed: ' + rel)
    else:
        for rel, expected in plan['source_hashes'].items():
            require(sha(ROOT / rel) == expected, 'Frozen source changed: ' + rel)
    require(json.loads((run_root / 'plan.json').read_text()) == plan, 'Remote plan')
    status = json.loads((run_root / 'status.json').read_text())
    tasks = plan['tasks']
    if interrupted_prefix is None:
        require(status['state'] == 'completed_ready_for_offline_scoring', 'Run not complete; do not score partial corpus')
        require(not (run_root / 'worker_error.json').exists(), 'Worker exception')
    else:
        # Narrow diagnostic exception, never a complete registered study score.
        require(0 < len(interrupted_prefix) < len(tasks) and tasks[:len(interrupted_prefix)] == interrupted_prefix, 'Not a completed prefix')
        require(status['state'] == 'STOP_exception_no_automatic_retry', 'Interrupted run must be stopped')
        error = json.loads((run_root / 'worker_error.json').read_text())
        require(error == {'type': 'ValueError', 'message': 'Derived logical adapter is not reproducible'}, 'Unexpected interruption; no diagnostic scoring')
        tasks = interrupted_prefix
    isolation = json.loads((run_root / 'isolation_receipt.json').read_text())
    require(isolation['plan_id'] == plan['plan_id'] and isolation['runtime_hashes'] == plan['runtime_hashes'], 'Isolation identity')
    require(set(isolation['runtime_python_files']) == set(plan['runtime_hashes']), 'Runtime membership')
    require(not isolation['evaluation_path_present'] and not isolation['source_output_path_present']
            and not isolation['automatic_source_inclusion'], 'Runtime isolation')
    if plan.get('continues_interrupted_plan'):
        adapters = json.loads((run_root / 'adapter_preflight_receipt.json').read_text())
        require(adapters['plan_id'] == plan['plan_id'] and adapters['all_tasks_checked_before_inference'] is True
                and adapters['relation_fingerprints'] == plan['derived_relation_sha256'], 'All-task adapter preflight receipt')
    receipt = json.loads((OUT / 'source_receipt.json').read_text())
    for file in receipt['public_input_files']:
        require(sha(OUT / 'inputs' / file['path']) == file['sha256'], 'Input changed: ' + file['path'])
    for file in receipt['evaluation_files']:
        require(sha(OUT / 'evaluation' / file['path']) == file['sha256'], 'Evaluation reference changed: ' + file['path'])
    packet_file = OUT / plan.get('public_packet_file', 'public_packet.json')
    require(sha(packet_file) == plan['public_packet_file_sha256'], 'Public packet bytes')
    require(digest(json.loads(packet_file.read_text())) == plan['public_packet_digest'], 'Public packet object')
    expected = {(t, w) for t in tasks for w in plan['final_workflows']}
    files = list((run_root / 'trajectories').glob('*/*/trajectory.json'))
    require({(p.parent.parent.name, p.parent.name) for p in files} == expected, 'Trajectory membership')
    trajectories = {(t, w): json.loads((run_root / 'trajectories' / t / w / 'trajectory.json').read_text()) for t, w in expected}
    responses = []
    for task in tasks:
        require(relation_fingerprint(run_root / 'derived' / task / 'workspace.sqlite') == plan['derived_relation_sha256'][task], 'Derived logical content')
        for workflow in plan['final_workflows']:
            trajectory = trajectories[(task, workflow)]
            directory = run_root / 'trajectories' / task / workflow
            require((trajectory['task_id'], trajectory['workflow'], trajectory['plan_id']) == (task, workflow, plan['plan_id']), 'Trajectory identity')
            ids = trajectory['request_ids']
            require(0 < len(ids) == trajectory['model_calls'] <= (plan['initial_call_cap'] if len(workflow) == 1 else plan['review_call_cap']), 'Trajectory budget')
            require({p.stem for p in (directory / 'attempts').glob('*.json')} == set(ids)
                    == {p.stem for p in (directory / 'responses').glob('*.json')}, 'Unresolved or extra attempts')
            if len(workflow) == 2:
                parent = trajectories[(task, workflow[0])]
                require(trajectory['parent_trajectory_sha256'] == digest(parent), 'Actual parent hash')
                first = json.loads((directory / 'responses' / (ids[0] + '.json')).read_text())
                task_packet = json.loads(first['messages'][0]['content'].split('\nTASK_JSON=', 1)[1])
                prior = task_packet['untrusted_earlier_work']
                require(prior == {k: parent.get(k) for k in ('task_id', 'final_action', 'final_result', 'tool_observations', 'messages')}, 'Parent actually supplied')
                for rid, artifact in parent['result_records'].items():
                    require(sha(directory / 'artifacts' / (rid + '.csv')) == artifact['output_sha256'], 'Reused parent artifact')
            else:
                require(trajectory['parent_trajectory_sha256'] is None, 'Unexpected parent')
            calls = []
            for step, rid in enumerate(ids):
                record = json.loads((directory / 'responses' / (rid + '.json')).read_text())
                attempt = json.loads((directory / 'attempts' / (rid + '.json')).read_text())
                audit_response(record, attempt, plan, task, workflow, step)
                if calls:
                    require(record['messages'][:len(calls[-1]['messages'])] == calls[-1]['messages'], 'Conversation continuity')
                    require(record['messages'][-2] == {'role': 'assistant', 'content': calls[-1]['response']['message']['content']}, 'Actual prior response')
                calls.append(record)
            require(trajectory['input_tokens'] == sum(r['response']['prompt_eval_count'] for r in calls)
                    and trajectory['output_tokens'] == sum(r['response']['eval_count'] for r in calls), 'Usage sum')
            require(abs(trajectory['terminal_serving_seconds'] - sum(r['response']['total_duration'] / 1e9 for r in calls)) < 1e-6, 'Duration sum')
            for rid, artifact in trajectory['result_records'].items():
                require(sha(directory / 'artifacts' / (rid + '.csv')) == artifact['output_sha256'], 'Artifact hash')
                require(artifact['task_semantics_verified'] is False, 'Unsupported semantic certification')
                for source in artifact.get('sources', []):
                    require(sha(OUT / 'inputs/input' / task / 'context' / source['source']) == source['source_sha256'], 'Artifact source lineage')
            prediction = directory / 'prediction.csv'
            if trajectory['final_result']:
                require(prediction.exists() and sha(prediction) == trajectory['prediction_sha256'] == trajectory['final_result']['output_sha256'], 'Final output identity')
                final = json.loads(calls[-1]['response']['message']['content'])
                require(final == trajectory['final_action'] and final['final_result_id'] in trajectory['result_records'], 'Final action')
            else:
                require(not prediction.exists() and trajectory['prediction_sha256'] is None, 'Unexpected prediction')
            responses.extend(calls)
    require(len(responses) == status['actual_model_calls'] <= plan['max_model_calls'], 'Corpus budget/status')
    require(status['completed_trajectories'] == len(expected), 'Status membership count')
    require(len(list(run_root.glob('trajectories/*/*/responses/*.json'))) == len(responses), 'Extra response files')
    require(len(list(run_root.glob('trajectories/*/*/attempts/*.json'))) == len(responses), 'Unresolved attempt outside completed block')
    return trajectories, responses


def load_scorer():
    require(sha(SCORER) == SCORER_SHA, 'Scorer changed')
    spec = importlib.util.spec_from_file_location('pinned_workspace_v4_scorer', SCORER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def evaluate(plan_path, run_root, destination, source_archive=None, interrupted_prefix=None):
    plan = json.loads(plan_path.read_text())
    trajectories, responses = audit_run(plan, run_root, source_archive, interrupted_prefix)
    tasks = interrupted_prefix if interrupted_prefix is not None else plan['tasks']
    scorer = load_scorer()
    rows = []
    for task in tasks:
        config = scorer.load_task_config(OUT / 'evaluation/configs' / (task + '.json'))
        for workflow in plan['final_workflows']:
            trajectory = trajectories[(task, workflow)]
            score = scorer.evaluate_task(config=config, prediction_path=run_root / 'trajectories' / task / workflow / 'prediction.csv',
                                         gold_path=OUT / 'evaluation/output' / task / 'gold.csv').to_dict()
            parent = trajectories[(task, workflow[0])] if len(workflow) == 2 else None
            rows.append({'task_id': task, 'workflow': workflow, 'input_amended': task in plan['input_amended_tasks'],
                         'state': trajectory['state'], 'official_relation_result': score,
                         'tool_or_schema_errors': sum('error' in o for o in trajectory['tool_observations']),
                         'final_origin': (trajectory.get('final_result') or {}).get('origin', 'query' if trajectory.get('final_result') else None),
                         'policy_cost_including_parent': policy_cost(trajectory, parent),
                         'terminal_new_calls': trajectory['model_calls']})
    passed = {(r['task_id'], r['workflow']): r['official_relation_result']['passed'] for r in rows}
    workflows = {w: {'passed': sum(passed[t, w] for t in tasks), 'tasks': len(tasks),
                     'cost_including_parent': {k: sum(r['policy_cost_including_parent'][k] for r in rows if r['workflow'] == w)
                                               for k in ('model_calls', 'input_tokens', 'output_tokens', 'terminal_serving_seconds')}}
                 for w in plan['final_workflows']}
    transitions = {w: {'rescues': [t for t in tasks if not passed[t, w[0]] and passed[t, w]],
                       'harms': [t for t in tasks if passed[t, w[0]] and not passed[t, w]]}
                   for w in ('AA', 'BB', 'AB', 'BA')}
    summary = {'created_utc': datetime.now(timezone.utc).isoformat(), 'plan_id': plan['plan_id'],
               'scope': 'Adapted development tasks; engineering feasibility/error bank only, not official-original DataSpace or confirmed research effect.',
               'study_complete': interrupted_prefix is None, 'scored_task_ids': tasks,
               'interrupted_prefix_diagnostic_only': interrupted_prefix is not None,
               'receipt_audit': 'PASS', 'scorer_sha256': SCORER_SHA, 'actual_corpus_model_calls': len(responses),
               'actual_input_tokens': sum(r['response']['prompt_eval_count'] for r in responses),
               'actual_output_tokens': sum(r['response']['eval_count'] for r in responses),
               'length_stops': sum(r['response'].get('done_reason') == 'length' for r in responses),
               'native_thinking_nonempty': sum(bool(r['response']['message'].get('thinking')) for r in responses),
               'tool_or_schema_errors': sum(r['tool_or_schema_errors'] for r in rows),
               'terminal_state_counts': dict(Counter(r['state'] for r in rows)), 'workflows': workflows,
               'transitions_from_actual_parent': transitions,
               'cross_minus_self_descriptive': ((workflows['AB']['passed'] + workflows['BA']['passed'] - workflows['AA']['passed'] - workflows['BB']['passed']) / (2 * len(tasks))) if interrupted_prefix is None else None,
               'tasks': rows, 'scientific_expansion_gate': 'NOT_OPENED', 'history_fitted': False,
               'human_annotations_added': 0, 'strong_frontier_single_baseline': 'MISSING_quota0',
               'evaluator_source_sha256': sha(Path(__file__))}
    require(not destination.exists(), 'Do not overwrite scored result')
    write(destination, summary)
    print(json.dumps({k: v for k, v in summary.items() if k != 'tasks'}, ensure_ascii=False, indent=2))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', type=Path, default=OUT / 'registered_plan_packaging2.json')
    parser.add_argument('--run-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=OUT / 'offline_results.json')
    parser.add_argument('--source-archive', type=Path)
    parser.add_argument('--interrupted-prefix', nargs='+', help='Diagnostic completed prefix only; no registered corpus score')
    args = parser.parse_args()
    evaluate(args.plan, args.run_root, args.output, args.source_archive, args.interrupted_prefix)
