import io
import json
import sys
import tarfile
from pathlib import Path
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'infra/modal'))
from routerbench_finqa_feedback_core import (final_answer, prompt_for, visible_records,
                                            select_queries, crossfit, analyze, query_hash)


def test_final_box_extraction_and_full_context_without_gold():
    raw = 'reasoning' * 10000 + '\\boxed{\\frac{5}{2}}'
    answer, mode, partial = final_answer(raw)
    assert answer == '\\boxed{\\frac{5}{2}}' and mode == 'complete_boxed' and not partial
    assert final_answer('short') == ('short', 'tail_fallback', True)
    tail, mode, partial = final_answer('a' * 3000 + '\\boxed{incomplete')
    assert len(tail) == 2500 and mode == 'tail_fallback' and partial
    row = {'origin_query': 'What is the increase?', 'prompt': 'Full table context ' * 100,
           'raw_output': raw, 'score': 0, 'ground_truth': 'SECRET'}
    prompt, meta = prompt_for(row)
    parsed = json.loads(prompt)
    assert parsed['problem'] == row['prompt'] and parsed['candidate_final_answer'] == answer
    assert meta['query_sha256'] == query_hash(row['origin_query'])
    assert 'SECRET' not in prompt and 'score' not in prompt
    with pytest.raises(ValueError):
        prompt_for({**row, 'prompt': 'p' * 16001})


def test_visible_reader_changes_only_when_selected_visible_fields_change():
    original = {'records': [{'origin_query': 'unselected', 'prompt': 'a', 'raw_output': 'x', 'score': 1},
                            {'origin_query': 'selected', 'prompt': 'full context', 'raw_output': 'answer',
                             'score': 0, 'ground_truth': 'PRIVATE'}]}
    a = list(visible_records(io.BytesIO(json.dumps(original).encode()), [1]))
    changed = json.loads(json.dumps(original))
    changed['records'][0]['score'] = 0
    changed['records'][1]['score'] = 1
    changed['records'][1]['ground_truth'] = 'DIFFERENT'
    b = list(visible_records(io.BytesIO(json.dumps(changed).encode()), [1]))
    assert a == b == [(1, {'origin_query': 'selected', 'prompt': 'full context', 'raw_output': 'answer'})]


def test_query_selection_and_crossfit_heldout_labels():
    ids = [f'{i:064x}' for i in range(200)]
    assert select_queries(ids) == select_queries(ids[::-1])
    rng = np.random.default_rng(54)
    y = rng.integers(0, 2, (48, 20)); p = rng.random(y.shape); invalid = np.zeros(y.shape, bool)
    a, _ = crossfit(y, p, invalid)
    changed = y.copy(); changed[::4] = 1 - changed[::4]
    b, _ = crossfit(changed, p, invalid)
    assert np.array_equal(a[::4], b[::4])
    r = analyze(y, p, invalid, np.ones_like(invalid))
    assert r['judgments'] == 960 and np.isfinite(r['brier']['crossfit_judge'])


def test_selected_gold_ignores_unselected_score_and_requires_binary(tmp_path, monkeypatch):
    import routerbench_finqa_feedback_pipeline as pipeline
    models = [f'm{i}' for i in range(20)]
    members = {}; positions = {}
    archive = tmp_path / 'test.tar.gz'
    with tarfile.open(archive, 'w:gz') as tar:
        for i, model in enumerate(models):
            name = f'bench-release/finqa/test/{model}/a.json'
            members[model] = name; positions[model] = {'selected': 1}
            data = json.dumps({'records': [{'score': 'UNSELECTED'}, {'score': i % 2},
                                           {'score': 'UNSELECTED'}]}).encode()
            info = tarfile.TarInfo(name); info.size = len(data); tar.addfile(info, io.BytesIO(data))
    packet = {'members': members, 'positions': positions, 'models': models, 'query_ids': ['selected']}
    monkeypatch.setattr(pipeline, 'TOTAL', 20)
    assert np.array_equal(pipeline.selected_gold(packet, archive), [[i % 2 for i in range(20)]])


def test_collector_bounded_recovery_and_no_duplicate_after_persisted_response(tmp_path, monkeypatch):
    import routerbench_finqa_feedback_pipeline as pipeline
    monkeypatch.setattr(pipeline, 'verify', lambda _: None)
    monkeypatch.setattr(pipeline, 'TOTAL', 2)
    cases = [{'index': i, 'prompt_sha256': str(i), 'prompt': 'question' + str(i)} for i in range(2)]
    pipeline.save(tmp_path / 'judge_inputs_private.json', {'run_id': 'test', 'cases': cases})
    packet = {'run_id': 'test'}
    calls = []
    def request(body):
        calls.append(body['messages'][1]['content'])
        if len(calls) == 2:
            raise KeyboardInterrupt('interrupted after dispatch')
        return {'done': True, 'prompt_eval_count': 12, 'eval_count': 6,
                'message': {'content': '{"success_probability":0.7}'}}
    with pytest.raises(KeyboardInterrupt):
        pipeline.collect(packet, tmp_path, lambda: None, request)
    pipeline.collect(packet, tmp_path, lambda: None, request)
    assert calls == ['question0', 'question1', 'question1']
    row = json.loads((tmp_path / 'case_0001.json').read_text())
    assert row['complete'] and len(row['attempts']) == 2
    pipeline.collect(packet, tmp_path, lambda: None, request)
    assert len(calls) == 3
    # Crash after response but before setting complete must not send again.
    first = json.loads((tmp_path / 'case_0000.json').read_text())
    first['complete'] = False
    pipeline.save(tmp_path / 'case_0000.json', first)
    pipeline.collect(packet, tmp_path, lambda: None, request)
    assert len(calls) == 3


def test_deployed_module_imports_only_mounted_files(tmp_path):
    import shutil
    import subprocess
    names = ('routerbench_finqa_feedback_modal.py', 'routerbench_finqa_feedback_core.py',
             'routerbench_finqa_feedback_pipeline.py', 'routerbench_intake_core.py')
    for name in names:
        shutil.copyfile(ROOT / 'infra/modal' / name, tmp_path / name)
    subprocess.run([sys.executable, '-c', 'import routerbench_finqa_feedback_modal'],
                   cwd=tmp_path, capture_output=True, text=True, check=True, timeout=30)
