import json
from pathlib import Path

import pytest

from run_dart_modal_judge import case_order, parse_probability, prompt_for, read_case, read_ledger


def test_order_balances_agents_without_outcomes():
    pool = {'agents': [{'name': 'a'}, {'name': 'b'}],
            'dataset_id_lists': {'test_normal': {'task_ids': ['g_1', 'h_1', 'i_1']}}}
    order = case_order(pool)
    assert len({(r['task_id'], r['agent']) for r in order}) == 6
    assert [r['agent'] for r in order] == ['a', 'b'] * 3
    assert order == case_order(pool)


def test_collector_reads_only_public_spec_and_trace(tmp_path):
    data = tmp_path / 'data'
    spec = data / 'tasks/g_1/specs.json'
    spec.parent.mkdir(parents=True)
    spec.write_text(json.dumps({'instruction': 'Do the task', 'db_version': '0.1.0',
                                'secret_gold': 'NEVER_INCLUDE'}))
    repo = tmp_path / 'repo'
    log = repo / 'experiments/outputs/a_test_normal/tasks/g_1/logs/environment_io.md'
    log.parent.mkdir(parents=True)
    log.write_text('x' * 15000)
    prompt, meta = read_case({'task_id': 'g_1', 'agent': 'a'}, repo, data)
    assert 'NEVER_INCLUDE' not in prompt and 'secret_gold' not in prompt
    assert meta['clipped'] and meta['visible_trace_chars'] == 12000
    assert json.loads(prompt)['log_is_partial'] is True


@pytest.mark.parametrize('raw', ['{"success_probability":true}', '{"success_probability":1.1}',
                                 '{"success_probability":NaN}', '{"success_probability":0.5,"x":1}'])
def test_invalid_judge_response_rejected(raw):
    with pytest.raises(ValueError):
        parse_probability(raw)


def test_resume_rejects_duplicate_or_changed_manifest(tmp_path):
    path = tmp_path / 'ledger.jsonl'
    manifest = {'hash': 'frozen', 'cases': [{'task_id': 'g_1'}]}
    row = {'protocol_hash': 'frozen', 'index': 0, 'case': manifest['cases'][0]}
    path.write_text(json.dumps(row) + '\n')
    assert len(read_ledger(path, manifest)) == 1
    with pytest.raises(ValueError):
        read_ledger(path, {**manifest, 'hash': 'changed'})
    path.write_text((json.dumps(row) + '\n') * 2)
    with pytest.raises(ValueError):
        read_ledger(path, manifest)
