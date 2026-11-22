"""Unit tests for the EvalPlus partial-feedback pilot (no inference, no Modal)."""

import random

import pytest

sklearn = pytest.importorskip("sklearn")

from thesis_pilot import evalplus_replay as R  # noqa: E402
from thesis_pilot.evalplus_study import wilson  # noqa: E402

MODELS = ["a", "b", "c"]
TIDS = [f"t{i}" for i in range(10)]


def _bank(seed=0):
    rng = random.Random(seed)
    bank = {}
    for m in MODELS:
        for t in TIDS:
            b = int(rng.random() < 0.6)
            bank[(m, t, 0)] = (b, int(b and rng.random() < 0.7))
    return bank


def test_censoring_structure_never_violated_in_fixture():
    assert all(f <= b for b, f in _bank().values())


def test_censored_audit_only_reveals_basic_pass_cells():
    bank = _bank()
    hist = [(m, t) for t in TIDS[1:] for m in MODELS]
    for policy in ["CensoredUniform", "Disagreement"]:
        A = R._audit(policy, hist, bank, MODELS, 5, random.Random(1))
        assert len(A) <= 5 and all(bank[(m, t, 0)][0] == 1 for m, t in A)
    A = R._audit("Uniform", hist, bank, MODELS, 5, random.Random(1))
    assert len(A) == 5


def test_replay_is_deterministic_and_bounded(monkeypatch):
    monkeypatch.setattr(R, "SEEDS", 2)
    monkeypatch.setattr(R, "BOOT", 50)
    bank = _bank()
    a = R.run_replay(bank, MODELS, TIDS)
    b = R.run_replay(bank, MODELS, TIDS)
    assert a["table"] == b["table"]
    for row in a["table"]:
        for s in R.SELECTORS:
            assert 0 <= row[s] <= a["summary"]["oracle"] + 1e-9


def test_wilson_interval_contains_point_estimate():
    lo, hi = wilson(3, 20)
    assert lo < 0.15 < hi
