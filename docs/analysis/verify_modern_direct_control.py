"""Verify whole-cohort non-native-thinking control; no model calls."""
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
    dest=ROOT/'results/thesis_modern_direct_control_v1';p=read(dest/'plan.json');s=read(dest/'summary.json');reg=read(dest/'registration.json')
    parentpath=ROOT/'results/thesis_modern_backbone_control_v1/plan.json';parent=read(parentpath)
    assert read(HERE/'repguard_modern_control_verification_2026-10-19.json')['status']=='PASS'
    assert digest({k:v for k,v in p.items() if k!='run_id'})[:24]==p['run_id']==s['run_id']==reg['run_id']
    assert sha(dest/'plan.json')==reg['plan_sha256'] and reg['new_responses_at_registration']==0
    assert sha(parentpath)==p['parent_plan_sha256'] and p['public_cases']==parent['public_cases'] and p['case_ids']==parent['case_ids']
    assert p['model_digest']==parent['model_digest'] and p['thinking'] is False and p['num_predict']==4096
    with zipfile.ZipFile(dest/'frozen_source.zip') as z:
        for f,h in p['source_sha256'].items():assert sha(ROOT/'thesis_pilot'/f)==h==hashlib.sha256(z.read(f)).hexdigest()
    raw={r['id']:r for r in read(ROOT/'results/thesis_real_pilot_v2/finqa_train_private.json')};old=read(ROOT/'results/thesis_modern_backbone_control_v1/traces_private.json')['rows']
    n=valid=ok=inp=out=stops=native=0;seconds=0.;files=[];ys={}
    for c in p['public_cases']:
        assert set(c)=={'id','report','question','table','pre_text','post_text'}
        f=dest/'responses'/f'{digest(c["id"])[:16]}.json';r=read(f);o=r['output'];rr=o['response'];v=canonical(rr['message']['content'])
        assert r['state']=='completed' and r['case_id']==c['id'] and o['model']==rr['model']==p['model'] and rr['done']
        assert o['model_digest']==p['model_digest'] and o['app']==p['app'] and o['gpu']=='NVIDIA L40S'
        assert o['live_inference'] and not o['evaluation_volume_mounted'] and o['verification']==v
        assert o['prompt_sha256']==digest(messages(c))
        assert datetime.fromisoformat(rr['created_at'].replace('Z','+00:00'))>datetime.fromisoformat(reg['utc'].replace('Z','+00:00'))
        y=bool(v['hard_pass'] and correct(v['value'],raw[c['id']]['qa']['exe_ans']));ys[c['id']]=y;ok+=y;valid+=v['hard_pass'];n+=1
        inp+=rr.get('prompt_eval_count',0);out+=rr.get('eval_count',0);seconds+=(rr.get('prompt_eval_duration',0)+rr.get('eval_duration',0))/1e9
        native+=bool(o['actual_thinking_chars']);stops+=rr.get('done_reason')=='length'
        files.append({'path':str(f.relative_to(ROOT)),'sha256':sha(f),'prompt_sha256':o['prompt_sha256']})
    assert n==16==len(list((dest/'responses').glob('*.json')))==read(dest/'collection_complete.json')['actual_new_calls']
    assert native==0,'Server did not honor non-native-thinking control'
    m=s['method'];assert (m['correct'],m['valid'],m['input_tokens'],m['output_tokens'],m['length_stops'],m['native_thinking_nonempty'])==(ok,valid,inp,out,stops,native)
    assert abs(m['mean_ollama_eval_seconds']-seconds/16)<1e-8
    for other in ['qwen3:14b','qwen3.5:27b']:
        assert s['paired'][other]['direct_only_correct']==sum(ys[i] and not old[i][other]['correct'] for i in ys)
        assert s['paired'][other]['other_only_correct']==sum(old[i][other]['correct'] and not ys[i] for i in ys)
    for f,h in read(ROOT/'results/thesis_real_pilot_v2/packet_private.json')['visible']['source_sha256'].items():assert sha(ROOT/'thesis_pilot'/f)==h
    result={'status':'PASS','run_id':p['run_id'],'real_completed_responses':16,'mock_calls':0,'correct':ok,'n':16,'valid':valid,
            'native_thinking_nonempty':native,'length_stops':stops,'input_tokens':inp,'output_tokens':out,
            'whole_cohort_same_cases_prompt_weights_caps_except_thinking_verified':True,'source_weights_timestamps_and_execution_verified':True,
            'primary_seven_files_unchanged':True,'original_native_results_preserved':True,'posthoc_adequacy_control':True,'independent_final_test':False}
    (HERE/'repguard_modern_direct_verification_2026-10-19.json').write_text(json.dumps(result,indent=2))
    (HERE/'repguard_modern_direct_manifest_2026-10-19.json').write_text(json.dumps({'plan_sha256':sha(dest/'plan.json'),'summary_sha256':sha(dest/'summary.json'),'responses':files},indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
