"""Uniform formatting-only secondary control on saved REAL PoT programs.

Proposed after APTV's unnecessary line indentation was observed. No numeric,
operator, source or target-driven edits. Original strict scores stay untouched.
The accepted language is straight-line: all leading line indentation is removed;
control-flow blocks remain forbidden by the same AST interpreter.
"""
import hashlib
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))
from thesis_pilot.core import digest,correct
from thesis_pilot.pot_tools import verify
from repguard_paired_history_probe import harm_upper

def read(p):return json.loads(p.read_text())

def canonical(raw):
    original=verify(raw)
    try:
        a=json.loads(raw);code=a['code']
        if not isinstance(code,str):return original,False
        normalized='\n'.join(line.lstrip() for line in code.splitlines())
        # No character after the first non-whitespace character of a line changes.
        assert [x.lstrip() for x in code.splitlines()]==normalized.splitlines()
        if code==normalized:return original,False
        a['code']=normalized
        return verify(json.dumps(a)),True
    except (ValueError,KeyError,TypeError):return original,False

def main():
    src=ROOT/'results/thesis_pot_control_v1';primary=read(src/'summary.json')
    study=read(ROOT/'results/thesis_causal_repair_v1/plan.json');private=read(ROOT/'results/thesis_causal_repair_v1/private.json')
    cases={c['id']:c for c in study['fresh_cases']};rows=[]
    for f in sorted(src.glob('*.json')):
        r=read(f)
        if r.get('state')!='completed':continue
        o=r['output'];v,changed=canonical(o['response']['message']['content']);i=r['case_id']
        rows.append({'id':i,'response_file_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),
          'format_normalized':changed,'verification':v,
          'strict_correct':bool(o['verification']['hard_pass'] and correct(o['verification']['value'],private['gold'][i])),
          'normalized_correct':bool(v['hard_pass'] and correct(v['value'],private['gold'][i]))})
    assert len(rows)==24
    result={'scope':'Post-hoc uniform straight-line whitespace normalization, not a new LLM or reputation method',
      'n':24,'new_model_calls':0,'strict_original_correct':primary['correct'],
      'normalized_correct':sum(r['normalized_correct'] for r in rows),
      'rescues':sum(r['normalized_correct'] and not r['strict_correct'] for r in rows),
      'harms':sum(r['strict_correct'] and not r['normalized_correct'] for r in rows),
      'normalized_programs':sum(r['format_normalized'] for r in rows),
      'original_primary_scores_preserved':True,'source_verified':False,
      'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    replay=ROOT/'results/thesis_paired_history_probe_v1/traces_private.json'
    if replay.exists():
        traces=read(replay);tt={t['id']:t for t in traces['traces']};data=traces['data'];rr={r['id']:r for r in rows}
        policy=read(ROOT/'results/thesis_paired_history_probe_v1/summary.json');metrics={}
        base={i:int(rr[i]['normalized_correct']) for i in cases}
        result['regenerate_training_outcomes_unchanged_by_formatter']=all(
            (base[i] if rr[i]['verification']['hard_pass'] else data[i]['cheap'])==data[i]['regen'] for i in cases)
        for name in policy['methods']:
            outcomes={}
            for i in cases:
                if name=='direct_pot':y=base[i]
                else:
                    t=tt[i];d=data[i]
                    invoke=(name=='always_regenerate_with_fallback' or (name=='rule_guard_only' and d['guard']) or
                      (name=='oof_global_history' and t['global_regenerate']) or (name=='oof_local_history' and t['local_regenerate']))
                    y=(base[i] if rr[i]['verification']['hard_pass'] else d['cheap']) if invoke else d['cheap']
                outcomes[i]=int(y)
            h=sum(base[i] and not outcomes[i] for i in cases)
            metrics[name]={'correct':sum(outcomes.values()),'n':24,
                'rescue_vs_normalized_direct_pot':sum(outcomes[i] and not base[i] for i in cases),
                'harm_vs_normalized_direct_pot':h,'harm_probability_exact_upper95':harm_upper(h,24),
                'policy_decisions_refit':False,'costs_unchanged_from_primary_replay':True}
        result['same_frozen_decisions_with_uniform_formatter']=metrics
    out=ROOT/'results/thesis_pot_format_control_v2';out.mkdir(exist_ok=True)
    (out/'rows_private.json').write_text(json.dumps(rows,indent=2));(out/'summary.json').write_text(json.dumps(result,indent=2))
    (HERE/'repguard_pot_format_control_2026-10-18.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
