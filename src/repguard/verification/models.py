"""Strict separation of agent proposals from caller-owned facts and contracts."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Scope(FrozenModel):
    entity: str = Field(min_length=1)
    metric: str = Field(min_length=1)
    period: str = Field(min_length=1)
    population: str = Field(min_length=1)
    state: str = Field(min_length=1)
    qualifiers: tuple[tuple[str, str], ...] = ()

    @field_validator("qualifiers", mode="before")
    @classmethod
    def immutable_qualifiers(cls, value):
        if isinstance(value, dict):
            value = sorted(value.items())
        pairs = tuple(tuple(p) for p in value)
        if any(len(p) != 2 or not all(isinstance(x, str) and x for x in p) for p in pairs):
            raise ValueError("Invalid qualifier")
        if len({p[0] for p in pairs}) != len(pairs):
            raise ValueError("Duplicate qualifier")
        return tuple(sorted(pairs))


class Fact(FrozenModel):
    id: str = Field(min_length=1)
    value: str
    unit: str
    scope: Scope
    source_id: str = Field(min_length=1)
    snapshot_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    locator: str = Field(min_length=1)
    root_ids: tuple[str, ...] = Field(min_length=1)
    origin: Literal["structured_record", "peer_assertion"] = "structured_record"
    valid_from: datetime | None = None
    valid_until: datetime | None = None

    @field_validator("valid_from", "valid_until")
    @classmethod
    def aware(cls, value):
        if value is not None and value.utcoffset() is None:
            raise ValueError("Validity requires timezone-aware timestamps")
        return value

    @model_validator(mode="after")
    def interval(self):
        if self.valid_from and self.valid_until and self.valid_from >= self.valid_until:
            raise ValueError("Empty validity interval")
        return self


class Operand(FrozenModel):
    scope: Scope
    unit: str


class Contract(FrozenModel):
    id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    authority_ref: str = Field(min_length=1)
    approval: Literal["review_required", "approved"] = "review_required"
    operation: Literal["lookup", "difference", "sum", "ratio", "percent_change"]
    operands: dict[str, Operand] = Field(min_length=1)
    output_unit: str
    absolute_tolerance: str = "0"
    as_of: datetime | None = None

    @field_validator("as_of")
    @classmethod
    def aware(cls, value):
        if value is not None and value.utcoffset() is None:
            raise ValueError("as_of requires a timezone")
        return value

    @model_validator(mode="after")
    def roles(self):
        expected = {"lookup": {"value"}, "difference": {"left", "right"},
                    "ratio": {"numerator", "denominator"}, "percent_change": {"new", "old"}}
        if self.operation in expected and set(self.operands) != expected[self.operation]:
            raise ValueError("Wrong operation roles")
        return self


class Candidate(FrozenModel):
    """Agent can propose a value and cite IDs; it cannot redefine scope or truth."""
    claim_id: str = Field(min_length=1)
    value: str
    unit: str
    bindings: dict[str, str]


class Receipt(FrozenModel):
    contract_id: str
    contract_sha256: str
    candidate_sha256: str
    authority_ref: str
    verdict: Literal["consistent", "inconsistent", "unresolved"]
    reasons: tuple[str, ...]
    used_fact_ids: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()
    root_ids: tuple[str, ...] = ()
    source_snapshots: tuple[tuple[str, str], ...] = ()
    expected_value_in_output_unit: str | None = None
    semantic_truth_certified: Literal[False] = False
    assurance: str = "Conditional on caller-approved contract, admitted metadata and source snapshots; no independent NL interpretation or live-state certification."
