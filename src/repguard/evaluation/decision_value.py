"""Paired, task-level decision-value measurements for HistRepEval.

All inputs are final choices on the same task IDs. The gold mapping is used
only by offline evaluation; online policies must never receive it.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping


@dataclass(frozen=True)
class PairedDecisionValue:
    n_tasks: int
    baseline_correct: int
    candidate_correct: int
    changed_answers: int
    candidate_only_correct: int
    baseline_only_correct: int
    both_correct: int
    both_wrong: int
    oracle_either_correct: int

    @property
    def realized_gain(self) -> int:
        return self.candidate_correct - self.baseline_correct

    @property
    def sensitivity(self) -> float:
        return self.changed_answers / self.n_tasks

    @property
    def rescue_opportunity(self) -> int:
        """Gold-aware ceiling: tasks where candidate could rescue baseline."""
        return self.candidate_only_correct

    def to_dict(self) -> dict:
        return {**asdict(self), "realized_gain": self.realized_gain,
                "sensitivity": self.sensitivity,
                "rescue_opportunity": self.rescue_opportunity}


def paired_decision_value(
    baseline: Mapping[str, str | None],
    candidate: Mapping[str, str | None],
    gold: Mapping[str, str],
) -> PairedDecisionValue:
    """Score two policies on identical task IDs, counting invalid answers wrong.

    The ``oracle_either_correct`` field is a retrospective upper reference,
    never an executable policy score. It is kept distinct from realized gain.
    """
    if not gold or set(baseline) != set(gold) or set(candidate) != set(gold):
        raise ValueError("Baseline, candidate, and gold need identical nonempty task IDs")
    if any(not answer for answer in gold.values()):
        raise ValueError("Gold answers must be nonempty")
    both_correct = candidate_only = baseline_only = both_wrong = changed = 0
    for task_id in gold:
        b_answer, c_answer = baseline[task_id], candidate[task_id]
        b_correct = b_answer == gold[task_id]
        c_correct = c_answer == gold[task_id]
        changed += b_answer != c_answer
        if b_correct and c_correct:
            both_correct += 1
        elif c_correct:
            candidate_only += 1
        elif b_correct:
            baseline_only += 1
        else:
            both_wrong += 1
    return PairedDecisionValue(
        n_tasks=len(gold),
        baseline_correct=both_correct + baseline_only,
        candidate_correct=both_correct + candidate_only,
        changed_answers=changed,
        candidate_only_correct=candidate_only,
        baseline_only_correct=baseline_only,
        both_correct=both_correct,
        both_wrong=both_wrong,
        oracle_either_correct=both_correct + candidate_only + baseline_only,
    )
