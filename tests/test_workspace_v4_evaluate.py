import copy

import pytest

from experiments.workspace_v4.agent import digest
from research_ops.workspace_v4_evaluate import audit_response, audit_run, policy_cost


@pytest.fixture
def receipt():
    plan = {'plan_id': 'a' * 24, 'models': {'A': {'name': 'model', 'digest': 'weights'}}, 'ollama': '0.40.6'}
    messages = [{'role': 'user', 'content': 'source-only question'}]
    rid = digest([plan['plan_id'], 'task', 'A', 0])[:28]
    record = {'request_id': rid, 'plan_id': plan['plan_id'], 'task_id': 'task', 'workflow': 'A', 'step': 0,
              'messages': messages, 'messages_sha256': digest(messages), 'model': 'model', 'model_digest': 'weights',
              'provider': 'ollama_modal', 'live_inference': True, 'evaluation_volume_mounted': False,
              'reference_reconstruction_code_in_image': False, 'weights_read_only': True,
              'gpu': 'NVIDIA L40S, 580', 'ollama_version': '0.40.6',
              'request_body': {'model': 'model', 'messages': copy.deepcopy(messages), 'stream': False, 'think': False,
                               'format': 'json', 'options': {'temperature': 0, 'seed': 20261109, 'num_ctx': 32768, 'num_predict': 2048}},
              'response': {'model': 'model', 'done': True, 'prompt_eval_count': 100, 'eval_count': 5, 'total_duration': 1000}}
    attempt = {'request_id': rid, 'messages_sha256': digest(messages)}
    return record, attempt, plan


def test_provider_payload_must_match_logged_messages(receipt):
    record, attempt, plan = receipt
    audit_response(record, attempt, plan, 'task', 'A', 0)
    record['request_body']['messages'][0]['content'] = 'different prompt'
    with pytest.raises(ValueError, match='Actual provider messages'):
        audit_response(record, attempt, plan, 'task', 'A', 0)


@pytest.mark.parametrize('field,value,match', [
    ('model_digest', 'other', 'Model digest'),
    ('evaluation_volume_mounted', True, 'Oracle isolation'),
    ('gpu', 'CPU', 'Serving hardware'),
    ('live_inference', False, 'Provider receipt'),
])
def test_provenance_failures_reject_scoring(receipt, field, value, match):
    record, attempt, plan = receipt
    record[field] = value
    with pytest.raises(ValueError, match=match):
        audit_response(record, attempt, plan, 'task', 'A', 0)


def test_cached_parent_still_counts_in_each_policy_cost():
    parent = dict(model_calls=8, input_tokens=10000, output_tokens=1000, terminal_serving_seconds=50)
    review = dict(model_calls=2, input_tokens=6000, output_tokens=100, terminal_serving_seconds=5)
    assert policy_cost(review, parent) == dict(model_calls=10, input_tokens=16000, output_tokens=1100, terminal_serving_seconds=55)
    assert policy_cost(parent) == parent


def test_partial_corpus_cannot_receive_complete_study_score(tmp_path):
    plan = {'source_hashes': {}, 'tasks': ['first', 'second']}
    plan['plan_id'] = digest(plan)[:24]
    (tmp_path / 'plan.json').write_text(__import__('json').dumps(plan))
    (tmp_path / 'status.json').write_text(__import__('json').dumps({'state': 'collecting'}))
    with pytest.raises(ValueError, match='Run not complete'):
        audit_run(plan, tmp_path)


def test_unknown_interruption_cannot_use_adapter_failure_diagnostic_exception(tmp_path):
    import json
    plan = {'source_hashes': {}, 'tasks': ['first', 'second']}
    plan['plan_id'] = digest(plan)[:24]
    (tmp_path / 'plan.json').write_text(json.dumps(plan))
    (tmp_path / 'status.json').write_text(json.dumps({'state': 'STOP_exception_no_automatic_retry'}))
    (tmp_path / 'worker_error.json').write_text(json.dumps({'type': 'TimeoutError', 'message': 'unknown provider outcome'}))
    with pytest.raises(ValueError, match='Unexpected interruption'):
        audit_run(plan, tmp_path, interrupted_prefix=['first'])
