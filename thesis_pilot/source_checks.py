"""Additional mechanical token-boundary audit, separate from the frozen pilot.

Prevents a stripped sign/percent in a source token being treated as the same
numeric value. It uses source text only, never a gold answer.
"""
import math
import re
from .core import number,source_map,verify

NUMERIC = re.compile(r'(?<![\w.])(?:\(\s*[-+−]?\s*\$?\s*(?:\d[\d,]*(?:\.\d+)?|\.\d+)\s*%?\s*\)|[-+−]?\s*\$?\s*(?:\d[\d,]*(?:\.\d+)?|\.\d+)\s*%?)')


def numeric_binding_errors(case,answer):
    errors=[];sources=source_map(case)
    if not isinstance(answer,dict):return errors
    operands=answer.get('operands',[])
    if not isinstance(operands,list):return errors  # Base verifier rejects it.
    for item in operands:
        try:
            expected=number(item['token']);text=sources.get(item['source'],'')
            values=[]
            for match in NUMERIC.finditer(text):
                try:values.append(number(re.sub(r'\s+','',match.group())))
                except ValueError:pass
            if not any(math.isclose(expected,value,rel_tol=1e-12,abs_tol=1e-12) for value in values):
                errors.append('numeric_token_boundary:'+item['source'])
        except (KeyError,ValueError,TypeError):pass  # Base verifier records malformed inputs.
    return errors


def strict_verify(case,raw):
    check=verify(case,raw)
    extra=numeric_binding_errors(case,check['answer'])
    if extra:
        check['errors'].extend(extra);check['source_valid']=False;check['hard_pass']=False
    check['numeric_boundary_audit']=True
    return check
