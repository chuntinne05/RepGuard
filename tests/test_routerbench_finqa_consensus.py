import io
import json
import sys
import tarfile
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'infra/modal'))
from routerbench_finqa_consensus_core import agreement_proxy, select_queries, analyze
from routerbench_finqa_consensus_pipeline import selected_predictions, selected_gold
from routerbench_finqa_feedback_core import query_hash


def test_selection_excludes_pilot_and_is_order_invariant():
    pool = [f'{i:064x}' for i in range(200)]
    pilot = pool[:48]
    selected = select_queries(pool, pilot)
    assert len(selected) == len(set(selected)) == 48
    assert not set(selected) & set(pilot)
    assert selected == select_queries(pool[::-1], pilot[::-1])
    with pytest.raises(ValueError):
        select_queries(pool[:-1], pilot)


def test_agreement_self_exclusion_unicode_and_missing():
    matrix = [['  Ａ  ', 'a', 'a', '', '   '] + [f'unique-{i}' for i in range(15)] for _ in range(48)]
    p, missing = agreement_proxy(matrix)
    assert np.allclose(p[:, :3], 2 / 19)
    assert np.all(p[:, 3:] == 0)
    assert np.all(missing[:, 3:5]) and not np.any(missing[:, :3])
    changed = [r[:] for r in matrix]
    changed[0][0] = 'other'
    p2, _ = agreement_proxy(changed)
    assert p2[0, 0] == 0 and p2[0, 1] == 1 / 19
    assert np.array_equal(p[1:], p2[1:])


def test_archive_prediction_pass_ignores_score_and_selected_gold_checks_identity(tmp_path):
    models = [f'm{i}' for i in range(20)]
    questions = [f'selected question {i}' for i in range(48)]
    ids = [query_hash(question) for question in questions]
    members = {}
    positions = {}
    packet = {'models': models, 'query_ids': ids, 'members': members, 'positions': positions}

    def make_archive(path, unselected_score=0, selected_score=1, selected_query=None):
        with tarfile.open(path, 'w:gz') as tar:
            for i, model in enumerate(models):
                name = f'bench-release/finqa/test/{model}/output.json'
                members[model] = name
                positions[model] = {q: j + 1 for j, q in enumerate(ids)}
                rows = {'records': [{'origin_query': 'ignore', 'prediction': 'x', 'score': unselected_score}]
                        + [{'origin_query': selected_query if j == 0 and selected_query else question,
                            'prediction': 'A', 'score': selected_score}
                           for j, question in enumerate(questions)]
                        + [{'origin_query': 'ignore2', 'prediction': 'z', 'score': 'BAD'}]}
                data = json.dumps(rows).encode()
                member = tarfile.TarInfo(name)
                member.size = len(data)
                tar.addfile(member, io.BytesIO(data))

    first = tmp_path / 'first.tar.gz'
    second = tmp_path / 'second.tar.gz'
    make_archive(first)
    make_archive(second, unselected_score='BAD', selected_score=0)
    assert selected_predictions(packet, first) == selected_predictions(packet, second) == [['A'] * 20 for _ in range(48)]
    assert np.array_equal(selected_gold(packet, first), np.ones((48, 20)))
    assert np.array_equal(selected_gold(packet, second), np.zeros((48, 20)))
    wrong = tmp_path / 'wrong.tar.gz'
    make_archive(wrong, selected_query='different')
    with pytest.raises(ValueError, match='identity'):
        selected_gold(packet, wrong)


def test_crossfit_analysis_does_not_use_heldout_gold():
    rng = np.random.default_rng(314)
    y = rng.integers(0, 2, (48, 20))
    p = rng.random((48, 20))
    missing = np.zeros((48, 20), bool)
    a = analyze(y, p, missing)
    altered = y.copy()
    altered[::4] = 1 - altered[::4]
    b = analyze(altered, p, missing)
    assert np.array_equal(np.asarray(a['calibrated_predictions'])[::4],
                          np.asarray(b['calibrated_predictions'])[::4])
    assert a['cells'] == 960 and a['operational_pass']
