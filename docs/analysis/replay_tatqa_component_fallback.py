"""Post-hoc receiver adequacy replay over REAL patches, no new model outputs."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from thesis_pilot.tatqa_scope_study import prepare,replay,SOURCE,DEST
from thesis_pilot.tatqa_scope_tools import scope_ok

def run():
    p,cases=prepare();sys.path.insert(0,'/tmp/repguard_tatqa_eval_deps');sys.path.insert(0,str(SOURCE))
    from tatqa_metric import TaTQAEmAndF1
    labels=json.loads((SOURCE/'annotations_private.json').read_text());rows=[]
    for c in cases:
        arms,raw,joint=replay(c);v=arms['combined'];chosen='registered_joint'
        # Selection uses permissions and executable validity only, never labels.
        if not joint['accepted']:
            for action in ['operation','evidence']:
                candidate=raw[action]['verification']
                if scope_ok(arms['initial']['proposal'],candidate['proposal'],action) and candidate['hard_pass']:
                    v=candidate;chosen=action;break
        m=TaTQAEmAndF1();m(ground_truth=labels[c['id']],prediction=[str(v['value'])] if v['hard_pass'] else [],pred_scale=v['scale'])
        rows.append({'id':c['id'],'chosen_by_mechanical_rule':chosen,'correct':bool(m.get_overall_metric()[0]),'value':v['value'],'scale':v['scale']})
    out={'scope':'Post-hoc all24 receiver replay of real model patches. Not new inference, independent confirmation, or learned reputation gain.',
         'run_id':p['run_id'],'new_model_calls':0,'fixed_rule':'Try registered joint; if rejected choose valid permitted O, else E, else KEEP. Targets used only after selection for scoring.',
         'correct':sum(x['correct'] for x in rows),'n':24,'rows':rows,'primary_scores_unchanged':True}
    Path(__file__).with_name('repguard_tatqa_component_fallback_replay_2026-10-20.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'correct':out['correct'],'n':24,'new_model_calls':0,'primary_scores_unchanged':True}))
if __name__=='__main__':run()
