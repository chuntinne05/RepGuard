"""Verify32 real responses and recompute paired backbone outcomes, no inference."""
import hashlib
import json
import sys
import zipfile
from datetime import datetime
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))
from thesis_pilot.core import digest,correct
from thesis_pilot.pot_tools import messages
from thesis_pilot.composition_tools import canonical

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    dest=ROOT/'results/thesis_backbone_diversity_probe_v1';plan=read(dest/'plan.json');reg=read(dest/'registration.json');s=read(dest/'summary.json')
    assert digest({k:v for k,v in plan.items() if k!='run_id'})[:24]==plan['run_id']==s['run_id']==reg['run_id']
    assert reg['new_responses_at_registration']==0 and sha(dest/'plan.json')==reg['plan_sha256']
    with zipfile.ZipFile(dest/'frozen_source.zip') as z:
        for f,h in plan['source_sha256'].items():assert sha(ROOT/'thesis_pilot'/f)==h==hashlib.sha256(z.read(f)).hexdigest()
    reserved=read(HERE/'repguard_reserved_report_splits_2026-10-19.json');assert sha(HERE/'repguard_reserved_report_splits_2026-10-19.json')==plan['reservation_sha256']
    assert plan['case_ids']==[c['id'] for c in reserved['splits']['development'][:16]]
    reports={c['report'] for c in plan['public_cases']};assert len(reports)==16
    assert not reports & {c['report'] for c in reserved['splits']['confirmation']}
    pp=read(ROOT/'results/thesis_real_pilot_v2/packet_private.json')['visible'];old=pp['cases']+read(ROOT/'results/thesis_causal_repair_v1/plan.json')['fresh_cases']
    assert not reports & {c['report'] for c in old}
    for f,h in pp['source_sha256'].items():assert sha(ROOT/'thesis_pilot'/f)==h
    raw={r['id']:r for r in read(ROOT/'results/thesis_real_pilot_v2/finqa_train_private.json')};ys={};files=[];thinking=0
    for model in plan['models']:
        outcomes={};cost=0.;tokens=[0,0];valid=0
        for c in plan['public_cases']:
            assert set(c)=={'id','report','question','table','pre_text','post_text'}
            f=dest/'responses'/f'{digest(c["id"])[:16]}_{model.replace(":","_")}.json';r=read(f);o=r['output'];response=o['response']
            assert r['state']=='completed' and r['model']==o['model']==response['model']==model and r['case_id']==c['id']
            assert o['model_digest']==plan['model_digests'][model] and o['app']=='repguard-thesis-backbone-probe-20261019'
            assert o['gpu']=='NVIDIA L4' and o['live_inference'] and not o['evaluation_volume_mounted'] and response['done']
            assert o['prompt_sha256']==digest(messages(c)) and o['verification']==canonical(response['message']['content'])
            assert datetime.fromisoformat(response['created_at'].replace('Z','+00:00'))>datetime.fromisoformat(reg['utc'].replace('Z','+00:00'))
            v=o['verification'];outcomes[c['id']]=bool(v['hard_pass'] and correct(v['value'],raw[c['id']]['qa']['exe_ans']))
            valid+=int(v['hard_pass']);cost+=(response.get('prompt_eval_duration',0)+response.get('eval_duration',0))/1e9
            tokens[0]+=response.get('prompt_eval_count',0);tokens[1]+=response.get('eval_count',0);thinking+=bool(o['actual_thinking_chars'])
            files.append({'path':str(f.relative_to(ROOT)),'sha256':sha(f),'prompt_sha256':o['prompt_sha256']})
        ys[model]=outcomes;m=s['methods'][model]
        assert m['correct']==sum(outcomes.values()) and m['valid']==valid and m['input_tokens']==tokens[0] and m['output_tokens']==tokens[1]
        assert abs(m['mean_ollama_eval_seconds']-cost/16)<1e-8
    assert len(files)==32==len(list((dest/'responses').glob('*.json')))
    for model in plan['models']:
        other=next(m for m in plan['models'] if m!=model)
        assert s['methods'][model]['uniquely_correct']==sum(ys[model][i] and not ys[other][i] for i in plan['case_ids'])
    union=sum(any(y[i] for y in ys.values()) for i in plan['case_ids']);best=max(sum(y.values()) for y in ys.values())
    assert s['oracle_union']==union and s['best_fixed']==best
    assert s['gate_for_larger_history_collection']==(union>=best+2 and all(m['uniquely_correct']>=1 for m in s['methods'].values()))
    result={'status':'PASS','run_id':plan['run_id'],'real_responses':32,'mock_calls':0,'distinct_new_live_report_groups':16,
            'same_public_prompts_per_question_both_models':True,'native_thinking_nonempty':thinking,'pinned_model_and_source_hashes_verified':True,
            'arithmetic_and_outcomes_recomputed':True,'costs_and_gate_recomputed':True,'primary_seven_files_unchanged':True,
            'reserved_confirmation_reports_used':0,'archive_report_disjointness':'UNRESOLVED, not claimed','independent_final_test':False,
            'methods':s['methods'],'oracle_union':union,'gate_for_larger_history_collection':s['gate_for_larger_history_collection']}
    (HERE/'repguard_backbone_diversity_verification_2026-10-19.json').write_text(json.dumps(result,indent=2))
    (HERE/'repguard_backbone_diversity_manifest_2026-10-19.json').write_text(json.dumps({'plan_sha256':sha(dest/'plan.json'),'summary_sha256':sha(dest/'summary.json'),'responses':files},indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
