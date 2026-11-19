"""Domain-neutral checks against an independently approved structured contract.

This is reusable engineering infrastructure, not a novel research method or an
automatic natural-language truth checker. Source/contract admission is external.
"""

from .engine import EvidenceStore, verify
from .models import Candidate, Contract, Fact, Operand, Scope

__all__ = ["Candidate", "Contract", "EvidenceStore", "Fact", "Operand", "Scope", "verify"]
