"""Conservative live unit review; never changes frozen scientific scores."""
import copy


def review_units(verification):
    checked=copy.deepcopy(verification)
    answer=checked.get('answer')
    if not isinstance(answer,dict):return checked
    steps=answer.get('steps',[])
    if not isinstance(steps,list):return checked
    final=next((s for s in steps if isinstance(s,dict) and s.get('id')==answer.get('result')),None)
    if (answer.get('display_unit')=='percent' and final and final.get('op')=='multiply'
            and 'c100' in [final.get('left'),final.get('right')]):
        checked['errors'].append('percentage_scale_requires_review: explicit x100 plus percent display')
        checked['hard_pass']=False
        checked['unit_review_required']=True
    return checked
