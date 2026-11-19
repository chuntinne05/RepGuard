import importlib.util
from pathlib import Path
import sys
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'infra/modal'))
from neural_core import observed_gold, inner_folds, features, ht_score, means
from neural_pipeline import ensure_identity, summarize


def test_mask_cannot_expose_unpaid_labels():
    a = np.arange(24).reshape(6,4) % 2
    idx = np.array([0, 3, 7, 18])
    b = 1-a
    b.ravel()[idx] = a.ravel()[idx]
    assert np.array_equal(observed_gold(a,idx), observed_gold(b,idx), equal_nan=True)
    assert np.isfinite(observed_gold(a,idx)).sum() == len(idx)


def test_group_isolation_and_pca_train_only():
    groups = [f'g{i//3}' for i in range(30)]
    f = inner_folds(groups)
    for k in range(3):
        assert not (set(np.array(groups)[f==k]) & set(np.array(groups)[f!=k]))
    rng = np.random.default_rng(1)
    x = rng.normal(size=(30, 20))
    train1, _ = features(x[:20], x[20:])
    train2, _ = features(x[:20], x[20:]*1000)
    assert np.array_equal(train1, train2)


def test_ht_only_observed_and_empty_fails():
    y = np.array([[1., np.nan], [np.nan, 0.]])
    assert ht_score(y, np.array([0,1])) == 2
    with pytest.raises(ValueError):
        ht_score(np.full((2,2),np.nan),np.array([0,1]))


def test_identity_and_incomplete_evaluation(tmp_path):
    ensure_identity(tmp_path, {'run_id': 'a'})
    ensure_identity(tmp_path, {'run_id': 'a'})
    with pytest.raises(ValueError):
        ensure_identity(tmp_path, {'run_id': 'b'})
    record = {'seed':0, 'test_indices':[0], 'actions': {h:[0] for h in ('Global','linear','lowrank','mlp','Selected')}}
    with pytest.raises(ValueError, match='Incomplete'):
        summarize([record], np.ones((2,2)), ['a','b'])


def test_global_exact_smoothed_tie_order():
    obs = np.array([[1,np.nan,0],[0,1,1],[np.nan,0,np.nan]])
    assert np.array_equal(means(obs),np.array([.5,.5,.5]))
    assert means(obs).argmax() == 0


@pytest.mark.skipif(importlib.util.find_spec('torch') is None, reason='Torch executes in pinned Modal image')
def test_remote_training_controls():
    from neural_smoke import smoke
    assert len(smoke()) == 3


def test_crash_resume_skips_committed_case_and_gate_stops(tmp_path, monkeypatch):
    """Storage/state-machine integration test; model calls deliberately stubbed."""
    import types
    import neural_pipeline as pipeline
    import neural_smoke
    monkeypatch.setitem(sys.modules, 'torch', types.SimpleNamespace(__version__='test-stub'))
    monkeypatch.setitem(sys.modules, 'transformers', types.SimpleNamespace(__version__='test-stub'))
    monkeypatch.setattr(pipeline, 'verify_packet', lambda p: None)
    monkeypatch.setattr(neural_smoke, 'smoke', lambda: {'test': 'stub'})
    monkeypatch.setattr(pipeline, 'embeddings', lambda texts, progress: (np.ones((5,2)), []))
    calls = []
    def crashing_route(x, obs, xt, groups, progress):
        calls.append(tuple(groups))
        if len(calls) == 2:
            raise RuntimeError('injected interruption')
        return {h:[0] for h in ('Global','linear','lowrank','mlp','Selected')}, {}
    monkeypatch.setattr(pipeline, 'route_case', crashing_route)
    packet = {'run_id':'test', 'texts':['x']*5, 'success':[[1,0]]*5,
              'folds':list(range(5)), 'groups':[str(i) for i in range(5)]}
    commits = []
    with pytest.raises(RuntimeError, match='injected'):
        pipeline.run(packet, tmp_path, lambda: commits.append(1))
    assert (tmp_path/'p0_fold0_seed0.json').exists()
    result = pipeline.run(packet, tmp_path, lambda: commits.append(1))
    assert result['state'] == 'stopped_p0_gate'
    assert len(calls) == 6  # one completed + one failed + four resumed cases
    assert len(list(tmp_path.glob('p0_fold*.json'))) == 5
    assert not list(tmp_path.glob('p1*'))
    pipeline.run(packet, tmp_path, lambda: commits.append(1))
    assert len(calls) == 6  # terminal invocation returns without retraining
