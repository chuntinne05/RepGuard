from __future__ import annotations

import pytest

from repguard.evaluation.decision_value import paired_decision_value


def test_paired_decision_value_keeps_rescue_ceiling_separate_from_realized_gain():
    gold = {"a": "A", "b": "B", "c": "C", "d": "D", "e": "E"}
    baseline = {"a": "A", "b": None, "c": "A", "d": "D", "e": "A"}
    candidate = {"a": "A", "b": "B", "c": "C", "d": "A", "e": "B"}
    outcome = paired_decision_value(baseline, candidate, gold)

    assert outcome.n_tasks == 5
    assert outcome.baseline_correct == 2
    assert outcome.candidate_correct == 3
    assert outcome.changed_answers == 4
    assert outcome.candidate_only_correct == 2
    assert outcome.baseline_only_correct == 1
    assert outcome.both_wrong == 1
    assert outcome.oracle_either_correct == 4
    assert outcome.realized_gain == 1
    assert outcome.sensitivity == 0.8


def test_paired_decision_value_rejects_unpaired_or_empty_evaluations():
    with pytest.raises(ValueError):
        paired_decision_value({"a": "A"}, {"b": "B"}, {"a": "A"})
    with pytest.raises(ValueError):
        paired_decision_value({}, {}, {})
