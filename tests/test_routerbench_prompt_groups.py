import io
import json
import sys
from pathlib import Path
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'infra/modal'))
from routerbench_prompt_groups_core import canonical, group, prompt_records, query_hash
from routerbench_prompt_groups_pipeline import run


def test_parser_retains_only_prompts_when_outcomes_change():
    import ijson
    first = {'records': [{'origin_query': 'What is 2+2?', 'prompt': 'ignored',
                          'raw_output': 'secret answer', 'score': 1, 'reference_answer': '4'}]}
    second = {'records': [{'origin_query': 'What is 2+2?', 'prompt': 'ignored',
                           'raw_output': 'another answer', 'score': 0, 'reference_answer': '5'}]}
    a = list(prompt_records(ijson.parse(io.BytesIO(json.dumps(first).encode()))))
    b = list(prompt_records(ijson.parse(io.BytesIO(json.dumps(second).encode()))))
    assert a == b == [{'query_sha256': query_hash('What is 2+2?'), 'prompt': 'What is 2+2?'}]
    assert canonical('  K  MATH\n  ') == 'k math'


def synthetic():
    prompts = {query_hash(f'Find the sum of integers from 1 through {i+1000}. Explain your work.'):
               f'Find the sum of integers from 1 through {i+1000}. Explain your work.' for i in range(500)}
    ids = sorted(prompts)
    return prompts, ids[:48]


def test_grouping_is_deterministic_and_marks_pilot_components():
    prompts, pilot = synthetic()
    a = group(prompts, pilot)
    b = group(dict(reversed(list(prompts.items()))), pilot[::-1])
    assert a == b
    assert a['total_questions'] == 500
    assert a['total_groups'] == 1
    assert a['pilot_touched_questions'] == 500
    assert a['remaining_questions'] == 0
    assert a['linked_edge_count'] > 0


def test_grouping_rejects_wrong_coverage_and_prompt_hash():
    prompts, pilot = synthetic()
    with pytest.raises(ValueError):
        group({k: v for k, v in list(prompts.items())[:-1]}, pilot)
    changed = dict(prompts); changed[sorted(prompts)[0]] = 'Different text'
    with pytest.raises(ValueError, match='hash'):
        group(changed, pilot)


def test_pipeline_rejects_changed_archive_and_does_not_read_gold(tmp_path, monkeypatch):
    import tarfile
    import routerbench_prompt_groups_pipeline as p
    prompts, pilot = synthetic()
    payload = {'records': [{'origin_query': text, 'score': 1, 'raw_output': 'private'} for text in prompts.values()]}
    archive = tmp_path / 'archive.tar.gz'
    data = json.dumps(payload).encode()
    with tarfile.open(archive, 'w:gz') as tar:
        info = tarfile.TarInfo('bench-release/math500/test/Qwen3-8B/test.json'); info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    packet = {'run_id': 'test', 'archive_bytes': archive.stat().st_size,
              'archive_sha256': p.file_sha(archive), 'selected_member': info.name,
              'expected_query_ids': sorted(prompts), 'pilot_query_ids': pilot}
    monkeypatch.setattr(p, 'verify', lambda _: None)
    root = tmp_path / 'run'
    result = run(packet, root, archive)
    assert result['state'] == 'completed_prompt_grouping_review_required'
    output = (root / 'prompts_private.json').read_text()
    assert 'private' not in output and 'score' not in output and 'raw_output' not in output
    assert run(packet, root, archive)['state'] == result['state']
    bad = dict(packet); bad['run_id'] = 'changed'
    with pytest.raises(ValueError, match='Changed grouping input'):
        run(bad, root, archive)
