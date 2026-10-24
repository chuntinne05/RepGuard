"""Source-dependency checks for future versions, independent of target labels.

This does not establish semantic correctness. Unit warnings request review;
they never silently rewrite a value or look for a target-matching scale.
"""

def inspect_program(answer):
    result={'errors':[],'warnings':[],'final_source_dependencies':[],'used_steps':[]}
    if not isinstance(answer,dict) or answer.get('status')!='answer':
        result['errors'].append('no_answer_program');return result
    steps=answer.get('steps',[])
    if not steps:
        result['errors'].append('empty_program');return result
    used=set()
    def visit_arg(arg,before):
        if '@' in arg:return {arg}
        if arg.startswith('K'):return set()
        if arg.startswith('#'):
            index=int(arg[1:])
            if not 0<=index<before:raise ValueError('forward_or_invalid_step_reference')
            return visit_step(index)
        raise ValueError('invalid_argument_namespace')
    def visit_step(index):
        used.add(index);deps=set()
        for arg in steps[index]['args']:deps.update(visit_arg(arg,index))
        return deps
    try:
        deps=visit_step(len(steps)-1)
        result['final_source_dependencies']=sorted(deps);result['used_steps']=sorted(used)
        if not deps:result['errors'].append('result_has_no_evidence_dependency')
        all_refs={a for s in steps for a in s['args'] if '@' in a}
        if all_refs-deps:result['warnings'].append('source_lookups_unused_by_result')
        if answer.get('display_unit')=='percent':
            last=steps[-1]
            if last.get('op')=='multiply' and any(a in ['K100','K1000','K1000000'] for a in last.get('args',[])):
                result['warnings'].append('possible_duplicate_percent_or_scale_conversion')
    except (ValueError,TypeError,KeyError,IndexError) as e:result['errors'].append(str(e))
    return result
