"""Audit sub-package for RepGuard capability analysis."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from repguard.audit.capability_audit import (
        AgentConfig,
        AgentDomainResult,
        CapabilityAudit,
        CapabilityAuditConfig,
        CapabilityMatrix,
        HeterogeneityGateResult,
        update_research_ops,
    )

_EXPORTS = {
    "AgentConfig",
    "AgentDomainResult",
    "CapabilityAudit",
    "CapabilityAuditConfig",
    "CapabilityMatrix",
    "HeterogeneityGateResult",
    "update_research_ops",
}


def __getattr__(name: str) -> Any:
    if name in _EXPORTS:
        import repguard.audit.capability_audit as _mod

        return getattr(_mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = list(_EXPORTS)
