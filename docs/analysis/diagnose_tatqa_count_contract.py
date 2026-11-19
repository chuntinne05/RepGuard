"""Post-hoc software diagnostic on REAL outputs; not another inference experiment.

Normalize only additive-mean divisors proven equal to their term count. The
numeric program is unchanged. Do NOT reroute or regenerate downstream reviews.
Report raw branches and frozen workflow final artifacts separately.
"""
import ast
import collections
import copy
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from thesis_pilot.tatqa_scope_tools import verify
from thesis_pilot.tatqa_scope_study import prepare,replay,path,read,DEST,SOURCE,ACTIONS

def normalize(proposal):
    a=copy.deepcopy(proposal)
    if not isinstance(a,dict) or not isinstance(a.get('code'),str):return a,[]
    code='\n'.join(x.lstrip() for x in a['code'].splitlines()).strip()
    try:tree=ast.parse(code)
    except SyntaxError:return a,[]
    assignments={};proofs=[]
    def expand(x,seen=()):
        if isinstance(x,ast.Name) and x.id in assignments and x.id not in seen:return expand(assignments[x.id],seen+(x.id,))
        return x
    def terms(x):
        x=expand(x)
        if isinstance(x,ast.BinOp) and isinstance(x.op,ast.Add):return terms(x.left)+terms(x.right)
        if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='sum' and len(x.args)==1:
            seq=expand(x.args[0])
            if isinstance(seq,(ast.List,ast.Tuple)):return len(seq.elts)
        return 1
    class Rewrite(ast.NodeTransformer):
        def visit_BinOp(self,node):
            node=self.generic_visit(node)
            if isinstance(node.op,ast.Div) and isinstance(node.right,ast.Constant) and type(node.right.value) is int and 2<=node.right.value<=16:
                n=node.right.value
                if terms(node.left)==n:
                    proofs.append({'divisor':n,'summand_count':n,'original_expression':ast.unparse(node)})
                    node.right=ast.Call(func=ast.Name(id='len',ctx=ast.Load()),args=[ast.List(elts=[ast.Constant(value=1) for _ in range(n)],ctx=ast.Load())],keywords=[])
            return node
    rewrite=Rewrite()
    for i,statement in enumerate(tree.body):
        tree.body[i]=rewrite.visit(statement)
        if isinstance(statement,ast.Assign) and len(statement.targets)==1 and isinstance(statement.targets[0],ast.Name):assignments[statement.targets[0].id]=statement.value
    if proofs:a['code']=ast.unparse(ast.fix_missing_locations(tree))
    return a,proofs

def run():
    plan,cases=prepare();assert read(DEST/'collection_complete.json')['actual_new_calls']==144
    sys.path.insert(0,'/tmp/repguard_tatqa_eval_deps');sys.path.insert(0,str(SOURCE))
    from tatqa_metric import TaTQAEmAndF1
    labels=read(SOURCE/'annotations_private.json');rawchanges=[];finalchanges=[];invalid=collections.Counter()
    def diag(case,action,base,kind,plain=False):
        nonlocal rawchanges,finalchanges
        if plain:return
        for err in base['errors']:invalid[err]+=1 if kind=='raw_branch' else 0
        if base['hard_pass'] or 'Unbound numeric constant' not in base['errors']:return
        a,proofs=normalize(base['proposal'])
        if not proofs:return
        v=verify(case,json.dumps(a))
        if not v['hard_pass']:return
        # Numerical program equivalence: execute ORIGINAL unrestricted arithmetic,
        # supplying the SAME source-derived binding prefix through a plain schema.
        from thesis_pilot.tatqa_scope_tools import catalogue
        cat=catalogue(case);original=base['proposal'];prefix=[f'{b["name"]}={cat[b["source"]]["value"]!r}' for b in original['bindings']]
        plain_a={k:original[k] for k in ['reasoning','status','code','scale']};plain_a['code']='\n'.join(prefix+[plain_a['code']])
        orig=verify(case,json.dumps(plain_a),plain=True)
        assert orig['hard_pass'] and orig['value']==v['value'] and orig['scale']==v['scale']
        metric=TaTQAEmAndF1();metric(ground_truth=labels[case['id']],prediction=[str(v['value'])],pred_scale=v['scale'])
        em=metric.get_overall_metric()[0]
        row={'case':case['id'],'action':action,'value_unchanged':True,'value':v['value'],'scale':v['scale'],'official_em_if_readable':em,'count_proofs':proofs}
        (rawchanges if kind=='raw_branch' else finalchanges).append(row)
    for c in cases:
        finals,raw,_=replay(c)
        for action in ACTIONS:diag(c,action,raw[action]['verification'],'raw_branch',plain=action=='plain')
        for action,v in finals.items():diag(c,action,v,'frozen_workflow_terminal',plain=action=='plain')
    out={'scope':'Post-hoc equivalence-preserving readout diagnostic ONLY. No new inference, no prompt changes, no revised primary scores or reputation claims.',
         'run_id':plan['run_id'],'new_model_calls':0,'raw_invalid_errors':dict(invalid),'raw_readability_changes':rawchanges,
         'frozen_workflow_terminal_readability_changes':finalchanges,
         'warning':'Workflow decisions and downstream generation contexts stay exactly as collected. This is NOT a rollout of a new acceptance policy. No hidden targets used to choose rewrites.'}
    dest=Path(__file__).with_name('repguard_tatqa_count_contract_diagnostic_2026-10-20.json');dest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'raw_responses_newly_readable':len(rawchanges),'raw_newly_readable_official_correct':sum(x['official_em_if_readable'] for x in rawchanges),'frozen_terminal_artifacts_newly_readable':len(finalchanges),'new_model_calls':0}))

if __name__=='__main__':run()
