import io
import json
import sys
import tarfile
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'infra/modal'))
from routerbench_intake_core import classify, inspect_json, summarize, digest


def test_metadata_invariant_to_scores_references_outputs():
    first = {'performance': .1, 'records': [{'index': 3, 'origin_query': '  Ａ + b  ', 'prompt': 'different wrapper',
                                           'ground_truth': 'SECRET_GOLD', 'score': 0, 'prediction': 'SECRET_OUTPUT'}]}
    second = json.loads(json.dumps(first))
    second['performance'] = .9
    second['records'][0].update(score=1, ground_truth='OTHER_GOLD', prediction='OTHER_OUTPUT')
    a = inspect_json(io.BytesIO(json.dumps(first).encode()))
    b = inspect_json(io.BytesIO(json.dumps(second).encode()))
    assert a == b and a['record_count'] == 1
    assert not any(v in json.dumps(a) for v in ('SECRET', 'OTHER', 'different wrapper', 'Ａ'))
    from hashlib import sha256
    assert a['records'][0]['query_sha256'] == sha256(b'a + b').hexdigest()


def test_excluded_and_unsafe_paths():
    assert classify('bench/mmlu_pro/test/model/run.json') == {'skip': 'excluded_mmlu'}
    assert classify('bench/MMLU/test/model/run.json') == {'skip': 'excluded_mmlu'}
    for name in ('/bench/a/test/m/a.json', '../bench/a/test/m/a.json'):
        with pytest.raises(ValueError):
            classify(name)
    assert classify('bench/math500/test/model/run.json')['model'] == 'model'


def test_coverage_and_unsupported_queries():
    raw = {'records': [{'prompt': 'p'}, {'origin_query': None}, {'origin_query': 'Q', 'index': 4}]}
    r = inspect_json(io.BytesIO(json.dumps(raw).encode()))
    assert r['supported_count'] == 2 and r['unsupported_count'] == 1
    files = [{'dataset': 'math', 'partition': 'test', 'model': m, 'member': m, **r} for m in ('m1', 'm2')]
    summary = summarize(files)['math/test']
    assert summary['model_count'] == 2 and summary['common_queries_all_models'] == 2


def test_real_tar_exclusion_integrity_resume(tmp_path, monkeypatch):
    import routerbench_intake_pipeline as p
    archive = tmp_path / 'bench-release.tar.gz'
    with tarfile.open(archive, 'w:gz') as tar:
        for name, data in [('bench/math/test/m1/a.json', b'{"records":[{"origin_query":"one","score":1}]}'),
                           ('bench/math/test/m2/a.json', b'{"records":[{"origin_query":"one","score":0}]}'),
                           ('bench/mmlu/test/m1/a.json', b'INVALID JSON MUST NOT BE PARSED')]:
            info = tarfile.TarInfo(name); info.size = len(data); tar.addfile(info, io.BytesIO(data))
    packet = {'run_id': 'test', 'archive_bytes': archive.stat().st_size, 'archive_sha256': p.file_sha(archive)}
    monkeypatch.setattr(p, 'verify', lambda _: None)
    original = p.inspect_json
    calls = []
    def crash(stream):
        calls.append(1)
        if len(calls) == 2:
            raise RuntimeError('injected')
        return original(stream)
    monkeypatch.setattr(p, 'inspect_json', crash)
    with pytest.raises(RuntimeError, match='injected'):
        p.run(packet, tmp_path, lambda: None)
    assert len(list(tmp_path.glob('member_*.json'))) == 1
    result = p.run(packet, tmp_path, lambda: None)
    assert result['state'] == 'completed_inventory' and result['completed_files'] == 2
    assert len(calls) == 3
    assert p.run(packet, tmp_path, lambda: None) == result and len(calls) == 3
    inventory = json.loads((tmp_path / 'inventory.json').read_text())
    assert inventory['skipped_files']['excluded_mmlu'] == 1
    row_path = next(tmp_path.glob('member_*.json'))
    row = json.loads(row_path.read_text()); row['record_count'] = 99; p.atomic(row_path, row)
    # Even a terminal resumed run must reject corrupt member checkpoints.
    with pytest.raises(ValueError, match='Corrupt'):
        p.run(packet, tmp_path, lambda: None)
