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
