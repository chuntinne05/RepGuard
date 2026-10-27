"""Secondary single-agent control: accept an explicit final variable expression.

After inspecting HWM: the real program computes difference=6-5, then ends with
`difference` instead of assigning `answer`. Read the existing final expression;
do not repair arithmetic, select numbers or consult a target. Preserve strict
and whitespace-only results separately. No extra model calls.
"""
import ast
import hashlib
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))
from thesis_pilot.core import correct
from thesis_pilot.pot_tools import verify
from repguard_pot_format_control import canonical as whitespace
from repguard_paired_history_probe import harm_upper

def read(p):return json.loads(p.read_text())

def canonical(raw):
    base,changed=whitespace(raw)
    if base['hard_pass']:return base,False
    try:
        a=json.loads(raw)
        if a.get('status')!='answer':return base,False
        code='\n'.join(s.lstrip() for s in a['code'].splitlines()).strip()
        if code.startswith('```python\n') and code.endswith('```'):code=code[len('```python\n'):-3].strip()
        tree=ast.parse(code)
        if not tree.body or not isinstance(tree.body[-1],ast.Expr) or not isinstance(tree.body[-1].value,ast.Name):return base,False
        if not all(isinstance(s,ast.Assign) for s in tree.body[:-1]):return base,False
        if any(isinstance(t,ast.Name) and t.id=='answer' for s in tree.body[:-1] for t in s.targets):return base,False
        final=tree.body[-1].value
        tree.body[-1]=ast.Assign(targets=[ast.Name(id='answer',ctx=ast.Store())],value=final)
        a['code']=ast.unparse(ast.fix_missing_locations(tree))
        return verify(json.dumps(a)),True
    except (ValueError,TypeError,KeyError,IndexError,SyntaxError):return base,False

def main():
    src=ROOT/'results/thesis_pot_control_v1';original=read(src/'summary.json')
    gold=read(ROOT/'results/thesis_causal_repair_v1/private.json')['gold']
    history=ROOT/'results/thesis_paired_history_probe_v1';policy=read(history/'summary.json');traces=read(history/'traces_private.json')
    tt={t['id']:t for t in traces['traces']};data=traces['data'];rows=[]
    for f in sorted(src.glob('*.json')):
        r=read(f)
        if r.get('state')!='completed':continue
        i=r['case_id'];v,rewritten=canonical(r['output']['response']['message']['content'])
        rows.append({'id':i,'response_file_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),
          'readout_rewritten':rewritten,'verification':v,'correct':bool(v['hard_pass'] and correct(v['value'],gold[i]))})
    assert len(rows)==24
    rr={r['id']:r for r in rows};base={i:int(r['correct']) for i,r in rr.items()};methods={}
    discretionary_unchanged=all((base[i] if rr[i]['verification']['hard_pass'] else data[i]['cheap'])==data[i]['regen'] for i in rr if not data[i]['guard'])
    for name in policy['methods']:
        outcomes={}
        for i in rr:
            if name=='direct_pot':y=base[i]
            else:
                d=data[i];t=tt[i]
                invoke=(name=='always_regenerate_with_fallback' or (name=='rule_guard_only' and d['guard']) or
                  (name=='oof_global_history' and t['global_regenerate']) or (name=='oof_local_history' and t['local_regenerate']))
                y=(base[i] if rr[i]['verification']['hard_pass'] else d['cheap']) if invoke else d['cheap']
            outcomes[i]=int(y)
        harm=sum(base[i] and not outcomes[i] for i in rr)
        methods[name]={'correct':sum(outcomes.values()),'n':24,'rescue_vs_robust_direct_pot':sum(outcomes[i] and not base[i] for i in rr),
          'harm_vs_robust_direct_pot':harm,'harm_probability_exact_upper95':harm_upper(harm,24),
          'mean_ollama_eval_seconds':policy['methods'][name]['mean_ollama_eval_seconds'],
          'mean_model_calls':policy['methods'][name]['mean_model_calls']}
    summary={'scope':'Post-hoc deterministic output-format/readout control, not reputation or a new model',
      'n':24,'new_model_calls':0,'strict_original_correct':original['correct'],
      'whitespace_control_correct':read(ROOT/'results/thesis_pot_format_control_v2/summary.json')['normalized_correct'],
      'robust_direct_pot_correct':sum(base.values()),'readout_rewritten':sum(r['readout_rewritten'] for r in rows),
      'primary_scores_preserved':True,'source_verified':False,'discretionary_training_targets_unchanged':discretionary_unchanged,
      'same_frozen_decisions':methods,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    dest=ROOT/'results/thesis_pot_readout_control_v3';dest.mkdir(exist_ok=True)
    (dest/'rows_private.json').write_text(json.dumps(rows,indent=2));(dest/'summary.json').write_text(json.dumps(summary,indent=2))
    (HERE/'repguard_pot_readout_control_2026-10-18.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
