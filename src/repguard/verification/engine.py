"""Scope/validity/conflict/unit checks and a restricted numeric calculation.

No LLM calls, eval/exec, consensus truth, automatic latest-wins, or source repair.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from decimal import Decimal, localcontext
from types import MappingProxyType
from typing import Mapping

from .models import Candidate, Contract, Fact, Receipt


def number(value: str) -> Decimal:
    if not isinstance(value, str) or len(value) > 128 or not re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)", value):
        raise ValueError("noncanonical_number")
    n = Decimal(value)
    if not n.is_finite() or abs(n) > Decimal("1e30"):
        raise ValueError("number_out_of_range")
    return n


# Unit IDs are explicit: aliases belong in source adapters, never guessed here.
UNITS = {
    "count": ("count", Decimal(1)), "thousand_count": ("count", Decimal(1000)),
    "USD": ("USD", Decimal(1)), "million_USD": ("USD", Decimal(1000000)),
    "EUR": ("EUR", Decimal(1)), "million_EUR": ("EUR", Decimal(1000000)),
    "second": ("time", Decimal(1)), "millisecond": ("time", Decimal("0.001")),
    "ratio": ("ratio", Decimal(1)), "percent": ("ratio", Decimal("0.01")),
    "ratio_difference": ("ratio_difference", Decimal(1)),
    "percentage_point": ("ratio_difference", Decimal("0.01")),
    "kg": ("mass", Decimal(1)), "tonne": ("mass", Decimal(1000)),
}


def quantity(value, unit):
    if unit not in UNITS:
        raise ValueError("unknown_unit")
    dim, factor = UNITS[unit]
    with localcontext() as ctx:
        ctx.prec = 160
        return number(value) * factor, dim


@dataclass(frozen=True, init=False)
class EvidenceStore:
    facts: Mapping[str, Fact]
    admitted_fact_ids: frozenset[str]

    def __init__(self, facts, admitted_fact_ids=()):
        copied = [Fact.model_validate(f.model_dump() if isinstance(f, Fact) else f) for f in facts]
        by_id = {f.id: f for f in copied}
        if len(by_id) != len(copied):
            raise ValueError("duplicate_fact_id")
        admitted = frozenset(admitted_fact_ids)
        if not admitted <= by_id.keys():
            raise ValueError("unknown_admitted_fact")
        object.__setattr__(self, "facts", MappingProxyType(by_id))
        object.__setattr__(self, "admitted_fact_ids", admitted)


def active(fact, contract):
    if fact.valid_from is None and fact.valid_until is None:
        return contract.as_of is None
    if contract.as_of is None:
        return False
    return ((fact.valid_from is None or fact.valid_from <= contract.as_of)
            and (fact.valid_until is None or contract.as_of < fact.valid_until))


def verify(contract: Contract, candidate: Candidate, store: EvidenceStore) -> Receipt:
    used = []

    def identity(model):
        return hashlib.sha256(json.dumps(model.model_dump(mode="json"), sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    def receipt(verdict, reason, expected=None):
        facts = [store.facts[i] for i in used]
        return Receipt(contract_id=contract.id, contract_sha256=identity(contract), candidate_sha256=identity(candidate),
                       authority_ref=contract.authority_ref, verdict=verdict, reasons=(reason,),
                       used_fact_ids=tuple(used), source_ids=tuple(sorted({f.source_id for f in facts})),
                       root_ids=tuple(sorted({r for f in facts for r in f.root_ids})),
                       source_snapshots=tuple(sorted({(f.source_id, f.snapshot_sha256) for f in facts})),
                       expected_value_in_output_unit=expected)

    if contract.approval != "approved":
        return receipt("unresolved", "contract_requires_independent_review")
    if candidate.claim_id != contract.id:
        return receipt("unresolved", "claim_contract_identity_mismatch")
    if set(candidate.bindings) != set(contract.operands):
        return receipt("unresolved", "missing_or_extra_operand_roles")
    if contract.operation == "sum" and len(set(candidate.bindings.values())) != len(candidate.bindings):
        return receipt("unresolved", "reused_fact_in_additive_total")
    if contract.operation == "sum":
        scopes = [op.scope.model_dump_json() for op in contract.operands.values()]
        if len(set(scopes)) != len(scopes):
            return receipt("unresolved", "duplicate_scope_in_additive_contract")
    values, dims = {}, {}
    for role, requirement in contract.operands.items():
        fid = candidate.bindings[role]
        if fid not in store.facts:
            return receipt("unresolved", "unknown_fact:" + role)
        fact = store.facts[fid]
        used.append(fid)
        if fid not in store.admitted_fact_ids or fact.origin != "structured_record":
            return receipt("unresolved", "fact_not_independently_admitted:" + role)
        if fact.scope != requirement.scope:
            return receipt("unresolved", "scope_mismatch:" + role)
        if not active(fact, contract):
            return receipt("unresolved", "validity_unestablished_or_outside_interval:" + role)
        if requirement.unit == "status":
            if fact.unit != "status" or contract.operation != "lookup":
                return receipt("unresolved", "unsupported_status_operation")
            values[role], dims[role] = fact.value, "status"
        else:
            try:
                value, dim = quantity(fact.value, fact.unit)
                expected_dim = UNITS[requirement.unit][0]
            except (ValueError, KeyError):
                return receipt("unresolved", "unknown_or_invalid_operand_unit:" + role)
            if dim != expected_dim:
                return receipt("unresolved", "operand_unit_dimension_mismatch:" + role)
            values[role], dims[role] = value, dim
        # Conflicts are checked across caller-admitted active facts, not only citations.
        # Copies/peer agreement cannot resolve disagreement or establish independence.
        for other_id in store.admitted_fact_ids:
            other = store.facts[other_id]
            if other.origin != "structured_record" or other.scope != requirement.scope:
                continue
            if contract.as_of and other.valid_from is None and other.valid_until is None:
                return receipt("unresolved", "competing_evidence_validity_unknown:" + role)
            if not active(other, contract): continue
            try:
                ov, od = (other.value, "status") if other.unit == "status" else quantity(other.value, other.unit)
            except ValueError:
                return receipt("unresolved", "invalid_competing_evidence:" + role)
            if od != dims[role] or ov != values[role]:
                return receipt("unresolved", "conflicting_applicable_evidence:" + role)
    if contract.operation == "lookup" and dims["value"] == "status":
        if candidate.unit != "status" or contract.output_unit != "status":
            return receipt("inconsistent", "claim_unit_dimension_mismatch")
        result = values["value"]
        return receipt("consistent" if candidate.value == result else "inconsistent", "exact_status_comparison", result)
    try:
        tolerance = number(contract.absolute_tolerance)
        if tolerance < 0:
            return receipt("unresolved", "negative_tolerance")
        with localcontext() as ctx:
            ctx.prec = 160
            op = contract.operation
            if op == "lookup":
                expected, dim = values["value"], dims["value"]
            elif op in {"difference", "sum"}:
                if len(set(dims.values())) != 1:
                    return receipt("unresolved", "incompatible_operand_dimensions")
                dim = next(iter(dims.values()))
                if op == "difference":
                    expected = values["left"] - values["right"]
                    if dim == "ratio": dim = "ratio_difference"
                else:
                    expected = sum(values.values())
            else:
                left, right = ("new", "old") if op == "percent_change" else ("numerator", "denominator")
                if dims[left] != dims[right]:
                    return receipt("unresolved", "incompatible_operand_dimensions")
                if values[right] == 0:
                    return receipt("unresolved", "zero_denominator")
                expected = ((values[left] - values[right]) if op == "percent_change" else values[left]) / values[right]
                dim = "ratio"
            if contract.output_unit not in UNITS or UNITS[contract.output_unit][0] != dim:
                return receipt("unresolved", "contract_output_dimension_mismatch")
            candidate_value, candidate_dim = quantity(candidate.value, candidate.unit)
            if candidate_dim != dim:
                return receipt("inconsistent", "claim_unit_dimension_mismatch")
            factor = UNITS[contract.output_unit][1]
            consistent = abs(candidate_value - expected) <= tolerance * factor
            return receipt("consistent" if consistent else "inconsistent", "numeric_comparison", str(expected / factor))
    except (ValueError, ArithmeticError, TypeError):
        return receipt("unresolved", "unsupported_numeric_representation")
