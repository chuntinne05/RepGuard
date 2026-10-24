"""Post-hoc public-output surgery, NOT a model call or confirmed repair method.

Rule proposed after seeing early initial outputs, before repair outcomes.
Never uses target to decide edit; gold is only used in evaluation below.
Keep all original study scores. Removing scale can harm legitimate conversion.
"""
import copy
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from thesis_pilot.core import correct
from thesis_pilot.causal_tools import verify

def surgery(answer):
    a=copy.deepcopy(answer)
    if not isinstance(a,dict) or a.get('display_unit')!='percent':return a,False
    steps=a.get('steps',[])
    if len(steps)<2 or steps[-1].get('op')!='multiply':return a,False
    args=steps[-1].get('args',[]);previous=f'#{len(steps)-2}'
    if len(args)!=2 or previous not in args:return a,False
    other=args[1] if args[0]==previous else args[0]
    if other not in ['K100','K1000','K1000000']:return a,False
    a['steps']=steps[:-1]
    return a,True

def main():
    dest=ROOT/'results/thesis_causal_repair_v1'
    plan=json.loads((dest/'plan.json').read_text());private=json.loads((dest/'private.json').read_text());rows=[]
    cases={c['id']:c for c in plan['fresh_cases']}
    for f in sorted((dest/'fresh').glob('*_initial.json')):
        r=json.loads(f.read_text())
        if r['state']!='completed':continue
        c=cases[r['case_id']];v=r['output']['verification'];a,changed=surgery(v['answer'])
        after=verify(c,json.dumps(a)) if changed else v
        gold=private['gold'][c['id']]
        before_ok=v['hard_pass'] and correct(v['value'],gold)
        after_ok=after['hard_pass'] and correct(after['value'],gold)
        rows.append({'id':c['id'],'changed_by_source_only_rule':changed,'original_value':v['value'],'counterfactual_value':after['value'],
            'official_target':gold,'original_correct':before_ok,'counterfactual_correct':after_ok})
    out={'scope':'Exploratory post-hoc diagnostic, not preregistered method result; no inference, unchanged primary scores',
        'n':len(rows),'modified':sum(r['changed_by_source_only_rule'] for r in rows),
        'original_correct':sum(r['original_correct'] for r in rows),'counterfactual_correct':sum(r['counterfactual_correct'] for r in rows),
        'rescues':sum(not r['original_correct'] and r['counterfactual_correct'] for r in rows),
        'harms':sum(r['original_correct'] and not r['counterfactual_correct'] for r in rows),'rows':rows}
    # Apply identical postprocessing to ALL actual action outputs, after the
    # original acceptance/fallback rule. No per-case gold-based action choice.
    actions=['initial','self_repair','evidence_repair','plan_repair'];paired={}
    for i,c in cases.items():
        rr={}
        for f in (dest/'fresh').glob('*.json'):
            r=json.loads(f.read_text())
            if r['state']=='completed' and r['case_id']==i:rr[r['action']]=r['output']['verification']
        if set(rr)!=set(actions):continue
        paired[i]={}
        for action,v in rr.items():
            v=v if v['hard_pass'] else rr['initial']
            a,changed=surgery(v['answer']);v=verify(c,json.dumps(a)) if changed else v
            paired[i][action]=bool(v['hard_pass'] and correct(v['value'],private['gold'][i]))
    out['same_unit_pass_all_actions']={'paired_n':len(paired),'methods':{a:{'correct':sum(r[a] for r in paired.values()),
        'rescue_vs_normalized_initial':sum(r[a] and not r['initial'] for r in paired.values()),
        'harm_vs_normalized_initial':sum(r['initial'] and not r[a] for r in paired.values())} for a in actions},
        'oracle_union':sum(any(r.values()) for r in paired.values()),'oracle_union_is_not_a_method':True}
    Path(__file__).with_suffix('.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='rows'},indent=2))

if __name__=='__main__':main()
