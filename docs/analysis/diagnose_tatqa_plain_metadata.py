"""Common post-hoc normalization of inert unit metadata in actual terminal artifacts."""
import ast
import copy
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from thesis_pilot.tatqa_crossfamily_study import prepare,replay,SOURCE,DEST
from thesis_pilot.tatqa_scope_tools import verify

def normalize(proposal):
    a=copy.deepcopy(proposal);removed=[]
    if not isinstance(a,dict) or not isinstance(a.get('code'),str):return a,removed
    code='\n'.join(x.lstrip() for x in a['code'].splitlines()).strip()
    try:tree=ast.parse(code)
    except SyntaxError:return a,removed
    loaded={x.id for x in ast.walk(tree) if isinstance(x,ast.Name) and isinstance(x.ctx,ast.Load)}
    keep=[]
    for node in tree.body:
        if (isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name)
            and node.targets[0].id!='answer' and node.targets[0].id not in loaded
            and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str)):
            removed.append({'name':node.targets[0].id,'literal':node.value.value,'proof':'pure literal assignment; variable never read; not final answer'})
        else:keep.append(node)
    if removed:tree.body=keep;a['code']=ast.unparse(ast.fix_missing_locations(tree))
    return a,removed

def run():
    p,cases=prepare();assert json.loads((DEST/'collection_complete.json').read_text())['actual_new_calls']==120
    sys.path.insert(0,'/tmp/repguard_tatqa_eval_deps');sys.path.insert(0,str(SOURCE));from tatqa_metric import TaTQAEmAndF1
    labels=json.loads((SOURCE/'annotations_private.json').read_text());metrics={};rows={};changes=[]
    for c in cases:
        terminal,raw=replay(c,p);r={}
        for name,v in terminal.items():
            a,proof=normalize(v['proposal']);vv=verify(c,json.dumps(a),plain=True)
            if v['hard_pass']:assert vv['hard_pass'] and vv['value']==v['value'] and vv['scale']==v['scale']
            m=TaTQAEmAndF1();m(ground_truth=labels[c['id']],prediction=[str(vv['value'])] if vv['hard_pass'] else [],pred_scale=vv['scale']);em=m.get_overall_metric()[0]
            r[name]={'correct':bool(em),'valid':vv['hard_pass'],'value':vv['value'],'scale':vv['scale']}
            metric=metrics.setdefault(name,{'correct':0,'valid':0,'n':24});metric['correct']+=bool(em);metric['valid']+=vv['hard_pass']
            if proof:changes.append({'case':c['id'],'workflow':name,'newly_readable':not v['hard_pass'] and vv['hard_pass'],'proofs':proof})
        rows[c['id']]=r
    q=['qwen_plain','qwen_self1','qwen_self2'];g=['gemma_plain','gemma_self1','gemma_self2'];best=max(x['correct'] for x in metrics.values());union=sum(any(x['correct'] for x in r.values()) for r in rows.values())
    unique={f:sum(any(r[a]['correct'] for a in own) and not any(r[a]['correct'] for a in other) for r in rows.values()) for f,own,other in [('qwen',q,g),('gemma',g,q)]}
    out={'scope':'Post-hoc common terminal-artifact readout only. Actual generation contexts and registered acceptance decisions frozen. Not a new rollout, model call, primary score rewrite or method gain.',
         'new_model_calls':0,'run_id':p['run_id'],'methods':metrics,'oracle_union_diagnostic':union,'best_fixed':best,'unique_family_cases':unique,'changes':changes,'rows':rows}
    dest=Path(__file__).with_name('repguard_tatqa_plain_metadata_diagnostic_2026-10-20.json');dest.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ['methods','oracle_union_diagnostic','best_fixed','unique_family_cases','new_model_calls']},indent=2))
if __name__=='__main__':run()
