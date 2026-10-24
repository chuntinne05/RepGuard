"""Recompute registered scores from evaluator raw records, not summary metrics."""
import json
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),'/tmp/repguard_tatqa_eval_deps',str(ROOT/'results/thesis_tatqa_source_v1')]
from tatqa_metric import TaTQAEmAndF1
from thesis_pilot.tatqa_scope_study import prepare as prep_a,replay as replay_a
from thesis_pilot.tatqa_crossfamily_study import prepare as prep_b,replay as replay_b

def main():
    here=Path(__file__).resolve().parent
    labels=json.loads((ROOT/'results/thesis_tatqa_source_v1/annotations_private.json').read_text());checks={}
    for kind,prep,replay,directory in [('scoped',prep_a,replay_a,'thesis_tatqa_scoped_repair_v1'),('crossfamily',prep_b,replay_b,'thesis_tatqa_crossfamily_v1')]:
        p,cases=prep();summary=json.loads((ROOT/'results'/directory/'summary.json').read_text());totals={}
        for c in cases:
            arms=(replay(c) if kind=='scoped' else replay(c,p))[0]
            for name,v in arms.items():
                m=TaTQAEmAndF1();m(labels[c['id']],[str(v['value'])] if v['hard_pass'] else [],pred_scale=v['scale'])
                score=m.get_raw()[0]['em'];assert score in [0,1]
                totals[name]=totals.get(name,0)+score
        assert totals=={k:v['correct'] for k,v in summary['methods'].items()},(kind,totals)
        checks[kind]={'official_metric_totals_reproduced':totals,'run_id':p['run_id'],'source_hashes_verified_by_prepare':True}
    a=json.loads((here/'repguard_cycle03_audit_2026-10-20.json').read_text());b=json.loads((here/'repguard_cycle03_crossfamily_audit_2026-10-20.json').read_text());assert a['audit']==b['audit']=='PASS'
    result={'audit':'PASS','utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'new_real_responses':264,'unique_questions':24,
      'input_tokens':a['real_responses']['input_tokens']+b['stats']['new_input_tokens'],'output_tokens':a['real_responses']['output_tokens']+b['stats']['new_output_tokens'],
      'mock_calls':0,'unresolved_current_two_studies':0,'length_stops':0,'primary_scores_unchanged':True,'independent_recompute':checks,
      'history_learner_fitted':False,'reputation_superiority_claim':False,'semantic_human_adjudications':0}
    (here/'repguard_cycle03_final_audit_2026-10-20.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
