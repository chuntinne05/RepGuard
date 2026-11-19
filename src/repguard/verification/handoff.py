"""A bounded integration point for an actual downstream reviewer.

The callback is supplied by the host application. This module itself calls no
provider, publishes nothing, and never turns peer agreement into new evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .engine import EvidenceStore, verify
from .models import Candidate, Contract, Receipt


@dataclass(frozen=True)
class HandoffResult:
    candidate: Candidate
    receipt: Receipt
    reviewer_calls: int
    trajectory: tuple[Receipt, ...]


def review_once(contract: Contract, draft: Candidate, store: EvidenceStore,
                reviewer: Callable[[Contract, Candidate, Receipt], Candidate] | None = None,
                *, reviewer_call_budget: int = 1) -> HandoffResult:
    """One optional repair on a fixed contract/store; no silent retry or drift.

    Host is responsible for giving single-agent controls identical contracts,
    tools, feedback and budgets in an experiment. No superiority is implied.
    """
    if reviewer_call_budget not in (0, 1):
        raise ValueError("Only0or1review call allowed")
    initial = verify(contract, draft, store)
    if initial.verdict == "consistent" or reviewer is None or reviewer_call_budget == 0:
        return HandoffResult(draft, initial, 0, (initial,))
    # The reviewer cannot mutate caller-owned verification inputs in place.
    independent_contract = Contract.model_validate(contract.model_dump())
    final = reviewer(independent_contract, draft.model_copy(deep=True), initial)
    if not isinstance(final, Candidate):
        raise TypeError("Reviewer must return a Candidate")
    receipt = verify(contract, final, store)
    return HandoffResult(final, receipt, 1, (initial, receipt))
