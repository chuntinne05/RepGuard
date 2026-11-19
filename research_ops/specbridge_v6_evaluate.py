"""Complete-corpus receipt audit and native interpretation scoring, offline."""
from collections import Counter
from datetime import datetime, timezone
import json
import math
from pathlib import Path

from experiments.specbridge_v6.grading import SOURCE, load_grader, run_readonly
from experiments.specbridge_v6.runtime import MODELS, INSTRUCTION, digest, parse_candidate, sha, write

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/specbridge_v6'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def rows_reproduced(recorded, replayed):
    """Same shape/order/text/null; numeric backend noise at1e-12 only.

    This is substantially stricter than the upstream grader's default1e-6.
    Two equally wrong labels alone never count as execution reproduction.
    """
    if recorded is None or replayed is None:
        return recorded is replayed
    if len(recorded) != len(replayed):
        return False
    for left, right in zip(recorded, replayed):
        if len(left) != len(right):
            return False
        for a, b in zip(left, right):
            if a == b:
                continue
            if isinstance(a,int) and isinstance(b,int):
                return False
            if isinstance(a,(int,float)) and isinstance(b,(int,float)) and math.isfinite(a) and math.isfinite(b) and math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12):
                continue
            return False
    return True


def audit_response(response, attempt, plan, case, workflow):
    expected_id = digest([plan['plan_id'], case['case_id'], workflow])[:28]
    require(response['request_id'] == attempt['request_id'] == expected_id, 'Request identity')
    require(attempt['plan_id'] == plan['plan_id'] and attempt['case_id'] == case['case_id'] and attempt['workflow'] == workflow, 'Attempt membership')
    require(response['messages_sha256'] == attempt['messages_sha256'] == digest(response['messages']), 'Actual prompt digest')
    body = response['request_body']; config = MODELS[workflow[-1]]
    require(body['messages'] == response['messages'], 'Provider payload differs from logged prompt')
    require(response['model'] == body['model'] == response['response']['model'] == config['name'], 'Model name')
    require(response['model_digest'] == config['digest'] and response['ollama_version'] == '0.40.6', 'Weights/server version')
    require(response['provider'] == 'ollama_modal' and response['live_inference'] is True, 'Native model receipt')
    require(response['evaluation_volume_mounted'] is False and response['weights_read_only'] is True and 'L40S' in response['gpu'], 'Isolation/hardware receipt')
    require(response['response']['done'] is True and body['think'] is False and body['stream'] is False and body['format'] == 'json', 'Generation completion/config')
    require(body['options'] == {'temperature':0,'seed':20261109,'num_ctx':32768,'num_predict':8192}, 'Generation options')
    for key in ('prompt_eval_count','eval_count','total_duration'):
        require(isinstance(response['response'][key],int) and response['response'][key] >= 0, 'Invalid usage counter')


def expected_messages(case, parent=None):
    task = {'question':case['question'],'context':case['context']}
    if parent is not None:
        execution = parent['execution']; preview = {k:v for k,v in execution.items() if k != 'rows'}
        preview.update(rows_preview=(execution.get('rows') or [])[:8], rows_count=len(execution['rows']) if execution.get('rows') is not None else None,
                       preview_truncated=bool(execution.get('rows') and len(execution['rows']) > 8))
        task['earlier_work'] = {'raw_response':parent['raw_response'],'sql':parent['sql'],'execution':preview}
        task['review_instruction'] = 'Independently check the original specified request. Return a corrected or retained SQL query. Earlier agent identity is hidden.'
    return [{'role':'user','content':INSTRUCTION+'\nTASK_JSON='+json.dumps(task,ensure_ascii=False)}]


def policy_cost(trajectory, parent=None):
    records = [trajectory] + ([parent] if parent else [])
    return {key:sum(r[key] for r in records) for key in ('model_calls','input_tokens','output_tokens','serving_seconds')}


def evaluate(run_root, destination):
    plan = json.loads((OUT/'registered_plan.json').read_text()); packet = json.loads((OUT/'public_packet.json').read_text())
    require(digest({k:v for k,v in plan.items() if k != 'plan_id'})[:24] == plan['plan_id'], 'Plan digest')
    require(digest(packet) == plan['public_packet_digest'] and sha(OUT/'public_packet.json') == plan['public_packet_file_sha256'], 'Public packet')
    for path, expected in plan['source_hashes'].items():
        require(sha(ROOT/path) == expected, 'Frozen source changed: '+path)
    require(sha(OUT/'qualification.json') == plan['qualification_sha256'], 'Qualification record changed')
    require(json.loads((run_root/'plan.json').read_text()) == plan, 'Remote plan')
    status = json.loads((run_root/'status.json').read_text())
    require(status['state'] == 'completed_ready_for_offline_scoring' and not (run_root/'worker_error.json').exists(), 'Cannot score an incomplete/failed corpus')
    isolation = json.loads((run_root/'isolation_receipt.json').read_text())
    require(isolation['plan_id'] == plan['plan_id'] and isolation['runtime_hashes'] == plan['runtime_hashes'], 'Runtime identity')
    require(set(isolation['runtime_members']) == set(plan['runtime_hashes']) and isolation['sqlite_version'] == '3.42.0', 'Runtime membership/engine')
    require(not isolation['grader_or_reference_code_present'] and not isolation['evaluation_volume_present'] and not isolation['automatic_source_inclusion'], 'Runtime isolation')
    require(set(isolation['source_files']) == {'databases/'+d['database']+'.sqlite' for d in plan['source_databases']}, 'Source volume membership')
    for database in plan['source_databases']:
        require(sha(ROOT/database['path']) == database['sha256'], 'Source DB bytes changed')
    cases = {c['case_id']:c for c in packet['cases']}
    expected = {(case_id,wf) for case_id in cases for wf in plan['workflows']}
    paths = list((run_root/'trajectories').glob('*/*/trajectory.json'))
    require({(p.parent.parent.name,p.parent.name) for p in paths} == expected, 'Trajectory membership')
    for pattern in ('attempt.json','response.json','execution.json'):
        require(len(list((run_root/'trajectories').glob('*/*/'+pattern))) == len(expected), 'Missing/extra '+pattern)
    trajectories = {(cid,wf):json.loads((run_root/'trajectories'/cid/wf/'trajectory.json').read_text()) for cid,wf in expected}
    matches, grade_receipt = load_grader()
    scored = []; responses = []; replay_failures = []
    for case_id, case in cases.items():
        task = json.loads((SOURCE/'evaluation/development'/(case['task_id']+'.json')).read_text())
        database = SOURCE/'pinned/benchmark/databases'/(case['database']+'.sqlite')
        for workflow in plan['workflows']:
            directory = run_root/'trajectories'/case_id/workflow
            trajectory = trajectories[(case_id,workflow)]
            require((trajectory['plan_id'],trajectory['case_id'],trajectory['task_id'],trajectory['reading'],trajectory['workflow']) == (plan['plan_id'],case_id,case['task_id'],case['reading'],workflow), 'Trajectory identity')
            require(trajectory['database']==case['database'] and trajectory['model_role']==workflow[-1], 'Trajectory source/model role')
            attempt = json.loads((directory/'attempt.json').read_text()); response = json.loads((directory/'response.json').read_text())
            audit_response(response,attempt,plan,case,workflow)
            parent = trajectories[(case_id,workflow[0])] if len(workflow)==2 else None
            require(trajectory['parent_sha256'] == (digest(parent) if parent else None), 'Actual parent identity')
            require(response['messages'] == expected_messages(case,parent), 'Original request/actual parent/feedback mismatch')
            raw = response['response']['message']['content']; sql, parse_state = parse_candidate(raw)
            require(sql == trajectory['sql'] and raw == trajectory['raw_response'] and parse_state == trajectory['parse_state'], 'Parsed candidate changed')
            execution = json.loads((directory/'execution.json').read_text())
            require(sha(directory/'execution.json') == trajectory['execution_file_sha256'] and execution == trajectory['execution'], 'Execution artifact identity')
            require(trajectory['model_calls']==1 and trajectory['input_tokens']==response['response']['prompt_eval_count'] and trajectory['output_tokens']==response['response']['eval_count'], 'Usage sum')
            require(abs(trajectory['serving_seconds'] - response['response']['total_duration']/1e9)<1e-6, 'Serving duration')
            replay = run_readonly(database,sql) if sql else {'state':parse_state,'rows':None}
            reproduced = replay['state']==execution['state'] and rows_reproduced(execution['rows'],replay['rows'])
            if execution['state']=='ok':
                reproduced = reproduced and replay['columns']==execution['columns']
            if not reproduced:
                replay_failures.append({'case_id':case_id,'workflow':workflow,'recorded_state':execution['state'],'replayed_state':replay['state']})
            labels = matches(task,execution['rows'])
            scored.append({'case_id':case_id,'task_id':case['task_id'],'reading':case['reading'],'database':case['database'],'workflow':workflow,
                           'parse_state':parse_state,'execution_state':execution['state'],'native_matches':labels,'passed':case['reading'] in labels,
                           'opposite_only':labels==['B' if case['reading']=='A' else 'A'],
                           'rows':len(execution['rows']) if execution.get('rows') is not None else None,
                           'execution_reproduced':reproduced,'execution_rows_exactly_equal':execution['rows']==replay['rows'],
                           'policy_cost_including_parent':policy_cost(trajectory,parent),
                           'response_sha256':sha(directory/'response.json'),'trajectory_sha256':sha(directory/'trajectory.json')})
            responses.append(response)
    require(not replay_failures, 'Recorded SQL executions not reproduced: '+repr(replay_failures))
    require(len(responses)==status['model_calls']==status['completed_trajectories']==plan['max_model_calls']==144, 'Corpus cap/status')
    passed = {(r['case_id'],r['workflow']):r['passed'] for r in scored}
    workflows = {wf:{'passed':sum(r['passed'] for r in scored if r['workflow']==wf),'cases':len(cases),
                      'opposite_only':sum(r['opposite_only'] for r in scored if r['workflow']==wf),
                      'policy_cost_including_parent':{k:sum(r['policy_cost_including_parent'][k] for r in scored if r['workflow']==wf)
                                                     for k in ('model_calls','input_tokens','output_tokens','serving_seconds')}} for wf in plan['workflows']}
    transitions = {wf:{'rescues':[cid for cid in cases if not passed[cid,wf[0]] and passed[cid,wf]],
                       'harms':[cid for cid in cases if passed[cid,wf[0]] and not passed[cid,wf]]} for wf in ('AA','BB','AB','BA')}
    result = {'created_utc':datetime.now(timezone.utc).isoformat(),'plan_id':plan['plan_id'],'receipt_audit':'PASS',
              'scope':'12metadata-selected development tasks/24specified variants/3DB; native relation correctness, not semantic trace truth, V5 checker efficacy or independent confirmation',
              'actual_model_calls':len(responses),'actual_input_tokens':sum(r['response']['prompt_eval_count'] for r in responses),
              'actual_output_tokens':sum(r['response']['eval_count'] for r in responses),
              'length_stops':sum(r['response'].get('done_reason')=='length' for r in responses),
              'native_thinking_nonempty':sum(bool(r['response']['message'].get('thinking')) for r in responses),
              'parse_states':dict(Counter(r['parse_state'] for r in scored)),'execution_states':dict(Counter(r['execution_state'] for r in scored)),
              'execution_replay_matches':len(scored),'workflows':workflows,'transitions':transitions,
              'replay_numeric_tolerance':{'relative':1e-12,'absolute':1e-12,'fixed_before_reading_model_outcomes':True},
              'replay_exact_row_matches':sum(r['execution_rows_exactly_equal'] for r in scored),
              'by_database':{db:{wf:sum(r['passed'] for r in scored if r['database']==db and r['workflow']==wf) for wf in plan['workflows']}
                             for db in sorted({c['database'] for c in cases.values()})},
              'balanced_cross_minus_self_descriptive':(workflows['AB']['passed']+workflows['BA']['passed']-workflows['AA']['passed']-workflows['BB']['passed'])/(2*len(cases)),
              'native_grade_receipt':grade_receipt,'tasks':scored,'scientific_expansion_gate':'NOT_OPENED','history_fitted':False,
              'frontier_baseline':'MISSING_synthetic_probe_unknown_outcome','new_human_annotations':0,'evaluation_code_sha256':sha(Path(__file__))}
    require(not destination.exists(),'Do not overwrite results')
    write(destination,result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('tasks','native_grade_receipt')},ensure_ascii=False,indent=2))
    return result


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--run-root',type=Path,required=True);parser.add_argument('--output',type=Path,default=OUT/'offline_results.json')
    args=parser.parse_args();evaluate(args.run_root,args.output)
