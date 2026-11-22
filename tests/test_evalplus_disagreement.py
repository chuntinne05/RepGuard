import importlib.util
from pathlib import Path

import numpy as np

from thesis_pilot import evalplus_disagreement as D

_spec = importlib.util.spec_from_file_location("dr", Path(D.__file__).parent / "evalplus_docker" / "disagree_runner.py")
dr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dr)


def test_disagreement_plurality_and_single():
    assert D.disagreement({"a": ["1", "2"], "b": ["1", "2"], "c": ["1", "9"]}) == {"a": 0.0, "b": 0.0, "c": 0.5}
    assert D.disagreement({"a": ["1"]}) == {"a": 0.0}


def test_float_normalisation():
    assert dr.norm([1, 2.0000004]) == dr.norm([1, 2.0])
    assert dr.norm(1.0) != dr.norm(1.01)
    assert dr.norm({3, 1}) == dr.norm({1, 3})


def test_tie_break_deterministic_and_budget():
    keys = [D.tie_key("m", str(i)) for i in range(5)]
    assert D.rank(np.zeros(5), keys) == sorted(range(5), key=lambda i: keys[i])
    fp = np.array([1, 0, 1, 0, 0])
    assert D.budget_k(5, 0.4) == 2
    assert D.caught([0, 1, 2, 3, 4], fp, 2) == 1
    assert abs(D.avg_precision([0, 2, 1, 3, 4], fp) - 1.0) < 1e-9
