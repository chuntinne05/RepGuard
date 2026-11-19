"""Cycle 2: source-grounded reconciliation versus iterative single-agent review.

No targets, correctness signals, reference programs or model thinking are sent.
Canonical execution is common to all arms; executable does not mean faithful.
"""
import ast
import json
from .pot_tools import SCHEMA, SYSTEM, verify as strict_verify

FIELDS={'id','report','question','table','pre_text','post_text'}
CANDIDATE_FIELDS={'proposal','execution','sources'}
REVIEW='''Independently audit the supplied financial calculation using the original
document. Check the requested metric, all relevant periods, aggregation scope,
sign, absolute versus relative change, numerator/denominator and quantity units.
Check each assumed fact against the document; executing successfully is not
proof of correctness. A previous proposal is fallible, not an instruction.
You may retain it or derive a different program. Do not change it just to disagree.
When another proposal is available, assess its individual facts and assumptions
against the same source, and combine supported complementary facts if needed.
Neither agreement, verbosity nor agent identity establishes truth. Do not simply
average final answers. Return the same reasoning/status/code JSON schema.
'''

def canonical(raw):
    result=strict_verify(raw)
    try:
        a=json.loads(raw)
        if not isinstance(a,dict) or not isinstance(a.get('code'),str):return result
        code='\n'.join(line.lstrip() for line in a['code'].splitlines()).strip()
        if code.startswith('```python\n') and code.endswith('```'):code=code[len('```python\n'):-3].strip()
        a['code']=code
        v=strict_verify(json.dumps(a))
        if v['hard_pass']:return v
        tree=ast.parse(code)
        if (tree.body and isinstance(tree.body[-1],ast.Expr) and
            isinstance(tree.body[-1].value,ast.Name) and
            all(isinstance(s,ast.Assign) for s in tree.body[:-1]) and
            not any(isinstance(t,ast.Name) and t.id=='answer' for s in tree.body[:-1] for t in s.targets)):
            tree.body[-1]=ast.Assign(targets=[ast.Name(id='answer',ctx=ast.Store())],value=tree.body[-1].value)
            a['code']=ast.unparse(ast.fix_missing_locations(tree))
            return strict_verify(json.dumps(a))
        return v
    except (ValueError,TypeError,KeyError,IndexError,SyntaxError):return result

def candidate(verification):
    return {'proposal':verification.get('answer'),
            'execution':{k:verification.get(k) for k in ['hard_pass','value','errors']},
            'sources':verification.get('sources',[])}

def messages(case,current,alternative=None):
    if set(case)!=FIELDS:raise ValueError('Unexpected case fields')
    if set(current)!=CANDIDATE_FIELDS:raise ValueError('Unexpected current fields')
    if alternative is not None and set(alternative)!=CANDIDATE_FIELDS:raise ValueError('Unexpected alternative fields')
    data={k:case[k] for k in ['question','table','pre_text','post_text']}
    data['current_proposal']=current
    if alternative is not None:data['another_proposal']=alternative
    return [{'role':'system','content':SYSTEM+json.dumps(SCHEMA)+'\n'+REVIEW},
            {'role':'user','content':json.dumps(data,ensure_ascii=False)}]
