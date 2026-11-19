import io
import json
import sys
from pathlib import Path
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'infra/modal'))
from routerbench_headroom_core import analyze, select_queries
from routerbench_headroom_pipeline import selected_scores


def test_hash_selection_does_not_depend_on_scores_or_input_order():
    ids = [f'{i:064x}' for i in range(300)]
    a = select_queries('mbpp/test', ids)
    b = select_queries('mbpp/test', ids[::-1])
    assert a == b and len(a) == len(set(a)) == 200
    assert a != select_queries('finqa/test', ids)
    with pytest.raises(ValueError):
        select_queries('math500/test', ids)


def test_selected_score_parser_ignores_unselected_gold_and_other_fields():
    records = [{'score': i % 2, 'reference_answer': 'private', 'raw_output': 'private'} for i in range(6)]
    wanted = {'a': 1, 'b': 4}
    def extract(rows):
        return selected_scores(io.BytesIO(json.dumps({'records': rows}).encode()), wanted)
    first = extract(records)
    changed = json.loads(json.dumps(records))
    for i in (0, 2, 3, 5):
        changed[i]['score'] = 1 - changed[i]['score']
    for row in changed:
        row['reference_answer'] = 'other'
        row['raw_output'] = 'other'
    assert extract(changed) == first == {'a': 1., 'b': 0.}
    changed[4]['score'] = 4
    with pytest.raises(ValueError, match='Invalid selected score'):
        extract(changed)
    with pytest.raises(ValueError, match='missing'):
        selected_scores(io.BytesIO(json.dumps({'records': records[:2]}).encode()), wanted)


def test_oracle_bound_and_fractional_scores():
    y = np.zeros((200, 20))
    y[:, 0] = .8
    y[:100, 1] = 1.
    y[100:, 2] = 1.
    models = [f'm{i}' for i in range(20)]
    result = analyze(y, models)
    assert result['best_fixed_model'] == 'm0'
    assert result['best_fixed_mean_reward'] == pytest.approx(.8)
    assert result['oracle_mean_reward'] == pytest.approx(1.)
    assert result['headroom'] == pytest.approx(.2)
    assert result['strict_rescue_questions'] == 200
    assert result['fractional_score_cells'] == 200
    with pytest.raises(ValueError):
        analyze(np.full((200, 20), np.nan), models)


def test_modal_module_imports_with_only_declared_files(tmp_path):
    import subprocess
    for name in ('routerbench_headroom_core.py', 'routerbench_headroom_pipeline.py', 'routerbench_headroom_modal.py'):
        (tmp_path / name).write_bytes((ROOT / 'infra/modal' / name).read_bytes())
    script = ('import sys; sys.path.insert(0, sys.argv[1]); '
              'import routerbench_headroom_core, routerbench_headroom_pipeline, routerbench_headroom_modal')
    subprocess.run([sys.executable, '-I', '-c', script, str(tmp_path)], cwd=tmp_path, check=True, timeout=30)
