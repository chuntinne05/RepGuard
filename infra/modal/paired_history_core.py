"""Rename only the sampling-design control; estimation is unchanged."""
from history_core import routes as original_routes, METHODS as ORIGINAL_METHODS

METHODS=tuple('PairedGlobal' if m=='UniformAuditGlobal' else m for m in ORIGINAL_METHODS)


def routes(*args,**kwargs):
    result=original_routes(*args,**kwargs)
    for field in ('agent_choices','scores'):
        result[field]['PairedGlobal']=result[field].pop('UniformAuditGlobal')
    return result
