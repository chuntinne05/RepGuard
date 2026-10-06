import io
import json
from pathlib import Path
import sys
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'infra/modal'))
from routerbench_pilot_core import visible_records, prompt_for, crossfit, select_queries, dev_query, probability, analyze


def test_gold_does_not_enter_prompt_or_change_selection():
    source = {'records': [{'origin_query': 'Solve 2+2.', 'raw_output': '4', 'score': 0, 'ground_truth': 'SECRET'}]}
    a = list(visible_records(io.BytesIO(json.dumps(source).encode())))
    source['records'][0].update(score=1, ground_truth='CHANGED')
    b = list(visible_records(io.BytesIO(json.dumps(source).encode())))
    assert a == b
    prompt, _ = prompt_for(a[0])
    assert not any(s in prompt for s in ('SECRET', 'CHANGED', 'score', 'ground_truth'))
    qids = [str(i) for i in range(1000)]
    selected = select_queries(qids)
    assert len(selected) == 48 and all(dev_query(q) for q in selected)
    assert select_queries(qids[::-1]) == selected


def test_crossfit_excludes_all_labels_of_heldout_questions():
    rng = np.random.default_rng(6)
    y = rng.integers(0, 2, (48, 6)); p = rng.random(y.shape); invalid = np.zeros_like(y, dtype=bool)
    first, _ = crossfit(y, p, invalid)
    altered = y.copy(); altered[np.arange(48) % 4 == 0] = 1 - altered[np.arange(48) % 4 == 0]
    second, _ = crossfit(altered, p, invalid)
    assert np.array_equal(first[::4], second[::4])


def test_clipping_and_strict_probability():
    _, meta = prompt_for({'question': 'Question', 'answer': 'a' * 10001, 'answer_field': 'raw_output'})
    assert meta['answer_clipped']
    for raw in ('{"success_probability":true}', '{"success_probability":NaN}', '{"success_probability":1.1}', '{"p":0.2}'):
        with pytest.raises(ValueError):
            probability(raw)
    assert probability('{"success_probability":0.2}') == .2


def test_diagnostic_is_finite_and_operational_failure_stops_expansion():
    rng = np.random.default_rng(4); y = rng.integers(0, 2, (48, 6))
    report = analyze(y, np.full(y.shape, .5), np.ones(y.shape, bool), np.zeros(y.shape, bool))
    assert not report['operational_pass'] and not report['expansion_signal_pass']
    json.dumps(report, allow_nan=False)


def test_collector_recovers_interrupted_attempt_without_repeating_completed_case(tmp_path, monkeypatch):
    import routerbench_pilot_pipeline as p
    monkeypatch.setattr(p, 'verify', lambda _: None)
    packet = {'run_id': 'test'}
    cases = [{'index': i, 'prompt_sha256': str(i), 'prompt': 'problem ' + str(i)} for i in range(2)]
    p.save(tmp_path / 'judge_inputs_private.json', {'run_id': 'test', 'cases': cases})
    calls = []
    def request(body):
        assert set(body) == {'model', 'messages', 'stream', 'think', 'format', 'options'}
        calls.append(body['messages'][1]['content'])
        if len(calls) == 2:
            raise KeyboardInterrupt('simulate container termination after dispatch')
        return {'done': True, 'prompt_eval_count': 20, 'eval_count': 10,
                'message': {'content': '{"success_probability":0.6}'}}
    with pytest.raises(KeyboardInterrupt):
        p.collect(packet, tmp_path, lambda: None, request)
    p.collect(packet, tmp_path, lambda: None, request)
    assert calls == ['problem 0', 'problem 1', 'problem 1']
    row = json.loads((tmp_path / 'case_0001.json').read_text()); p.validate(row)
    assert row['attempts'][0]['state'] == 'interrupted_usage_unknown' and len(row['attempts']) == 2
    assert row['complete'] and not row['invalid']
    p.collect(packet, tmp_path, lambda: None, request)
    assert len(calls) == 3


def test_failed_judge_bounded_and_explicit_invalid(tmp_path, monkeypatch):
    import routerbench_pilot_pipeline as p
    monkeypatch.setattr(p, 'verify', lambda _: None)
    p.save(tmp_path / 'judge_inputs_private.json', {'run_id': 'test', 'cases': [{'index': 0, 'prompt_sha256': 'x', 'prompt': 'x'}]})
    calls = []
    def request(_):
        calls.append(1); return {'done': True, 'message': {'content': 'not JSON'}}
    p.collect({'run_id': 'test'}, tmp_path, lambda: None, request)
    row = json.loads((tmp_path / 'case_0000.json').read_text())
    assert len(calls) == 2 and row['invalid'] and row['probability'] == .5
    assert all(a['response']['message']['content'] == 'not JSON' for a in row['attempts'])


def test_evaluator_retains_only_preselected_record_positions(tmp_path):
    import tarfile
    from routerbench_pilot_core import MODELS
    from routerbench_pilot_pipeline import selected_gold
    archive = tmp_path / 'a.tar.gz'; members = {}; cases = []
    with tarfile.open(archive, 'w:gz') as tar:
        for i, model in enumerate(MODELS):
            name = 'bench-release/math500/test/' + model + '/a.json'; members[model] = name
            raw = json.dumps({'records': [{'score': 'UNSELECTED'}, {'score': 1}, {'score': 'UNSELECTED'}]}).encode()
            member = tarfile.TarInfo(name); member.size = len(raw); tar.addfile(member, io.BytesIO(raw))
            cases.append({'model_index': i, 'record_position': 1, 'query_sha256': 'selected'})
    assert np.array_equal(selected_gold({'members': members, 'query_ids': ['selected']}, archive, cases), [[1.] * 6])
