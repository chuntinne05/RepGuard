"""Accounting percent-token fix for FUTURE studies, never retroactive v1 scoring.

No question/gold dependency. Handles a percent sign after the closing parenthesis.
Does not infer implicit header units; source semantic adjudication remains needed.
"""
import math
import re

NUMERIC_V2=re.compile(r'(?<![\w.])(?:\(\s*[-+−]?\s*\$?\s*(?:\d[\d,]*(?:\.\d+)?|\.\d+)\s*%?\s*\)\s*%?|[-+−]?\s*\$?\s*(?:\d[\d,]*(?:\.\d+)?|\.\d+)\s*%?)')

def parse_quantity(token):
    s=re.sub(r'\s+','',token).replace('−','-').replace(',','').replace('$','')
    percent='%' in s;paren=s.startswith('(')
    numeric=s.replace('%','')
    if paren:
        if not numeric.endswith(')'):raise ValueError('Unbalanced accounting token')
        numeric=numeric[1:-1]
    if not re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)',numeric):raise ValueError('Invalid quantity')
    value=float(numeric)
    if paren:value=-abs(value)
    if percent:value/=100
    if not math.isfinite(value) or abs(value)>1e15:raise ValueError('Invalid numeric range')
    return {'token':token,'value':value,'printed_percent':percent,'accounting_negative':paren}

def numeric_tokens(text):
    return [parse_quantity(m.group().strip()) for m in NUMERIC_V2.finditer(text)]
