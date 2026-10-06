import json
import sys
from pathlib import Path
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'infra/modal'))
from routerbench_sparse_core import (Audit, METHODS, audit_order, cross_proxy, design,
                                    halving, means, observed_from_log, predict, rectify, select_case)


def data():
    rng = np.random.default_rng(71)
    y = rng.integers(0, 2, (36, 6)).astype(float)
    p = rng.uniform(0, 1, y.shape)
    return y, p, np.zeros_like(y, bool)


def select(y, p, invalid, budget=22, seed=1404):
    audits = {}
    def factory(name):
        audits[name] = Audit(y, budget)
        return audits[name].query
    result = select_case(p, invalid, budget, seed, factory)
    return result, audits


def test_audit_enforces_history_unique_cells_and_budget():
    server = Audit(np.ones((2, 3)), 2)
    assert server.query(0, 2) == 1
    for i, a in ((0, 2), (2, 0), (-1, 0), (0, 3)):
        with pytest.raises(ValueError):
            server.query(i, a)
    server.query(1, 2)
    with pytest.raises(ValueError):
        server.query(0, 0)
    assert server.indices == [2, 5]


@pytest.mark.parametrize('budget', [11, 22, 44])
def test_all_acquisition_paths_exact_budget_and_nested_fixed_masks(budget):
    y, p, invalid = data()
    result, servers = select(y, p, invalid, budget)
    assert set(result['agent_choices']) == set(METHODS)
    assert set(servers) == {'uniform', 'paired', 'IndependentSH', 'PairedSH'}
    for name, server in servers.items():
        assert len(server.indices) == len(set(server.indices)) == budget
        assert np.array_equal(y.ravel()[server.indices], server.labels)
        if name in ('IndependentSH', 'PairedSH'):
            trace = result['halving'][name]
            assert trace['audit_indices'] == server.indices
            assert trace['audit_labels'] == server.labels
            assert [len(t['active']) for t in trace['rounds']] == [6, 3, 2]
            for stage in trace['rounds']:
                idx = server.indices[stage['audit_start']:stage['audit_stop']]
                for a in stage['active']:
                    labels = [y.flat[i] for i in idx if i % 6 == a]
                    assert stage['scores'][str(a)] == float(np.mean(labels))
    for paired in (True, False):
        order = audit_order(36, 6, 1404, paired)
        assert len(set(order)) == 216
        assert order[:11] == order[:44][:11]
        if paired:
            assert len(set(i // 6 for i in order[:6])) == 1


@pytest.mark.parametrize('paired', [True, False])
def test_low_budget_halving_and_unqueried_gold_invariance(paired):
    y, _, _ = data()
    priority = [3, 0, 4, 2, 1, 5]
    for b in (11, 12, 13, 22, 44):
        s = Audit(y, b)
        first = halving(36, 6, b, 1404, paired, priority, s.query)
        z = 1 - y
        z.ravel()[s.indices] = y.ravel()[s.indices]
        assert halving(36, 6, b, 1404, paired, priority, Audit(z, b).query) == first
    for b in (0, 10):
        with pytest.raises(ValueError):
            halving(36, 6, b, 1404, paired, priority, Audit(y, b).query)
    tie = halving(36, 6, 11, 0, paired, priority, Audit(np.zeros_like(y), 11).query)
    assert tie['agent'] == priority[0]


def test_unaudited_gold_cannot_change_any_choice_or_adaptive_path():
    y, p, invalid = data()
    first, servers = select(y, p, invalid)
    z = 1 - y
    for server in servers.values():
        z.ravel()[server.indices] = y.ravel()[server.indices]
    second, changed_servers = select(z, p, invalid)
    assert first == second
    assert {n: s.indices for n, s in servers.items()} == {n: s.indices for n, s in changed_servers.items()}


def test_crossfit_excludes_own_question_labels_and_handles_empty_fold():
    y, p, invalid = data()
    obs = np.full_like(y, np.nan)
    obs[:3] = y[:3]
    altered = obs.copy()
    altered[np.arange(36) % 3 == 0] = 1 - altered[np.arange(36) % 3 == 0]
    first, trace = cross_proxy(obs, p, invalid, True)
    second, _ = cross_proxy(altered, p, invalid, True)
    assert np.array_equal(first[np.arange(36) % 3 == 0], second[np.arange(36) % 3 == 0])
    for row in trace:
        assert not set(row['training_rows']) & set(row['prediction_rows'])
        assert row['paid_training_labels'] == int(np.isfinite(obs[row['training_rows']]).sum())
    empty = np.full_like(y, np.nan)
    empty[0] = y[0]
    out, trace = cross_proxy(empty, p, invalid, True)
    assert trace[0]['empty_training_fallback']
    assert np.equal(out[np.arange(36) % 3 == 0], .5).all()
    assert np.array_equal(rectify(obs, np.full_like(obs, .5)), means(obs))


def test_gold_only_predictor_feedback_invariant_and_fixed_design():
    y, p, invalid = data()
    assert np.array_equal(predict(y, p, invalid, p, invalid, False),
                          predict(y, 1-p, ~invalid, 1-p, ~invalid, False))
    x, penalty = design(p, invalid, True)
    assert x.shape == (36, 6, 11)
    assert np.array_equal(penalty, [0.] + [4.] * 6 + [1.] * 4)
    assert np.array_equal(x[:, :, -4], p-.5)
    with pytest.raises(ValueError):
        observed_from_log(36, 6, [0, 0], [1, 0])


def packet():
    rng = np.random.default_rng(88)
    return {'success': rng.integers(0, 2, (48, 6)).tolist(),
            'judge_scores': rng.uniform(0, 1, (48, 6)).tolist(),
            'judge_invalid': np.zeros((48, 6), bool).tolist(), 'folds': (np.arange(48) % 4).tolist()}


def test_evaluation_gold_and_feedback_changes_leave_choices_identical():
    from routerbench_sparse_pipeline import case
    p = packet()
    spec = {'budget': 22, 'budget_fraction': .1, 'fold': 0, 'seed': 0, 'rng_seed': 1404}
    first = case(p, spec)
    rows = np.array(p['folds']) == 0
    q = json.loads(json.dumps(p))
    for key in ('success', 'judge_scores'):
        z = np.array(q[key]); z[rows] = 1-z[rows]; q[key] = z.tolist()
    second = case(q, spec)
    assert first['selections'] == second['selections']
    assert first['audits'] == second['audits']
    assert first['diagnostic'] != second['diagnostic']


def test_checkpoint_resume_does_not_repeat_finished_case_and_rejects_corruption(tmp_path, monkeypatch):
    import routerbench_sparse_pipeline as module
    monkeypatch.setattr(module, 'verify', lambda p: None)
    monkeypatch.setattr(module, 'summarize', lambda p, r: {'development_expansion_gate_pass': False})
    calls = []
    def stub(p, spec):
        calls.append(spec['index'])
        if len(calls) == 2:
            raise RuntimeError('injected interruption')
        return {'spec': spec}
    monkeypatch.setattr(module, 'case', stub)
    p = {'run_id': 'test', 'cases': [{'index': i} for i in range(240)]}
    with pytest.raises(RuntimeError, match='injected'):
        module.run(p, tmp_path)
    assert json.loads((tmp_path / 'status.json').read_text())['state'] == 'pipeline_failed'
    module.run(p, tmp_path)
    assert len(calls) == 241
    module.run(p, tmp_path)
    assert len(calls) == 241
    path = tmp_path / 'case_0000.json'
    row = json.loads(path.read_text()); row['index'] = 12; path.write_text(json.dumps(row))
    with pytest.raises(ValueError, match='checksum'):
        module.run(p, tmp_path)


def test_summarizer_gate_and_question_seed_averaging():
    from routerbench_sparse_pipeline import summarize
    p = packet()
    y = np.array(p['success'], float)
    rows = []
    for b in (.05, .1, .2):
        for f in range(4):
            ids = np.flatnonzero(np.array(p['folds']) == f)
            for s in range(20):
                rows.append({'spec': {'budget_fraction': b, 'fold': f, 'seed': s},
                             'test_indices': ids.tolist(),
                             'selections': {'agent_choices': {m: 0 for m in METHODS},
                                            'judge_crossfit_trace': [{'empty_training_fallback': False}] * 3},
                             'diagnostic': {'gold_predictions': np.full((12, 6), .5).tolist(),
                                            'judge_predictions': np.full((12, 6), .5).tolist()},
                             'audits': {'paired': {'indices': list(range(11))}}})
    result = summarize(p, rows)
    assert not result['development_expansion_gate_pass']
    assert result['method_selections'] == 2400
    for b in result['budgets'].values():
        assert b['methods']['CFJudgeRectifier']['mean_correct'] == float(y[:, 0].sum())
        assert b['diagnostic']['pair_residual_variance_ratio'] == pytest.approx(1.)
        assert b['primary_contrasts']['PairedGlobal']['ci95'] == [0., 0.]


def test_modal_module_imports_with_only_declared_cloud_files(tmp_path):
    import subprocess
    for n in ('routerbench_sparse_core.py', 'routerbench_sparse_pipeline.py', 'routerbench_sparse_modal.py'):
        (tmp_path / n).write_bytes((ROOT / 'infra/modal' / n).read_bytes())
    script = ('import sys; sys.path.insert(0, sys.argv[1]); '
              'import routerbench_sparse_core, routerbench_sparse_pipeline, routerbench_sparse_modal')
    subprocess.run([sys.executable, '-I', '-c', script, str(tmp_path)], cwd=tmp_path, check=True, timeout=30)
