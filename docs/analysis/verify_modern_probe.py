"""Verify the contemporary baseline from16 real receipts, without inference."""
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
    dest=ROOT/'results/thesis_modern_backbone_control_v1';p=read(dest/'plan.json');s=read(dest/'summary.json');reg=read(dest/'registration.json')
    assert digest({k:v for k,v in p.items() if k!='run_id'})[:24]==p['run_id']==s['run_id']==reg['run_id']
    assert sha(dest/'plan.json')==reg['plan_sha256'] and reg['new_responses_at_registration']==0
    assert sha(dest/'model_manifest.json')==p['model_manifest_sha256']
    manifest=read(dest/'model_manifest.json');assert manifest['models'][p['model']]['digest']==p['model_digest'] and manifest['ollama']=='0.40.6'
    assert manifest['volume']=='repguard-thesis-modern-models-20261019'
    src=ROOT/'results/thesis_backbone_diversity_probe_v1/plan.json';assert sha(src)==p['preexisting_probe_plan_sha256']
    parent=read(src);assert p['public_cases']==parent['public_cases'] and p['case_ids']==parent['case_ids']
    pre=read(HERE/'repguard_modern_control_preregistration_2026-10-19.json');assert pre['case_ids']==p['case_ids'] and pre['max_inference_calls']==16
    with zipfile.ZipFile(dest/'frozen_source.zip') as z:
        for f,h in p['source_sha256'].items():assert sha(ROOT/'thesis_pilot'/f)==h==hashlib.sha256(z.read(f)).hexdigest()
    primary=read(ROOT/'results/thesis_real_pilot_v2/packet_private.json')['visible']['source_sha256']
    for f,h in primary.items():assert sha(ROOT/'thesis_pilot'/f)==h
    raw={r['id']:r for r in read(ROOT/'results/thesis_real_pilot_v2/finqa_train_private.json')}
    n=0;valid=0;ok=0;inp=0;out=0;seconds=0.;files=[];thinking=0;stops=0
    for c in p['public_cases']:
        assert set(c)=={'id','report','question','table','pre_text','post_text'}
        f=dest/'responses'/f'{digest(c["id"])[:16]}.json';r=read(f);o=r['output'];rr=o['response']
        assert r['state']=='completed' and r['case_id']==c['id'] and o['model']==rr['model']==p['model'] and rr['done']
        assert o['model_digest']==p['model_digest'] and o['app']==p['app']=='repguard-thesis-modern-backbone-20261019'
        assert o['gpu']=='NVIDIA L40S' and o['live_inference'] and not o['evaluation_volume_mounted']
        assert digest(messages(c))==o['prompt_sha256'] and canonical(rr['message']['content'])==o['verification']
        response_time=datetime.fromisoformat(rr['created_at'].replace('Z','+00:00'))
        for registered in [reg['utc'],pre['utc']]:assert response_time>datetime.fromisoformat(registered.replace('Z','+00:00'))
        v=o['verification'];valid+=v['hard_pass'];ok+=bool(v['hard_pass'] and correct(v['value'],raw[c['id']]['qa']['exe_ans']))
        inp+=rr.get('prompt_eval_count',0);out+=rr.get('eval_count',0);seconds+=(rr.get('prompt_eval_duration',0)+rr.get('eval_duration',0))/1e9
        thinking+=bool(o['actual_thinking_chars']);stops+=rr.get('done_reason')=='length';n+=1
        files.append({'path':str(f.relative_to(ROOT)),'sha256':sha(f),'prompt_sha256':o['prompt_sha256']})
    assert n==16==len(list((dest/'responses').glob('*.json')))==read(dest/'collection_complete.json')['actual_new_calls']
    m=s['methods'][p['model']];assert m['correct']==ok and m['valid']==valid and m['input_tokens']==inp and m['output_tokens']==out
    assert abs(m['mean_ollama_eval_seconds']-seconds/16)<1e-8 and m['length_stops']==stops
    result={'status':'PASS','run_id':p['run_id'],'model':p['model'],'model_digest':p['model_digest'],'real_completed_responses':16,'mock_calls':0,
            'native_thinking_nonempty':thinking,'correct':ok,'n':16,'valid':valid,'input_tokens':inp,'output_tokens':out,'length_stops':stops,
            'same16cases_and_same_prompt_verified':True,'pinned_source_weights_and_timestamps_verified':True,'arithmetic_and_scores_recomputed':True,
            'primary_seven_files_unchanged':True,'separate_new_app_and_model_volume':True,'independent_final_test':False,
            'gpu_comparison_not_cost_matched':True,'reputation_superiority_claim':False}
    (HERE/'repguard_modern_control_verification_2026-10-19.json').write_text(json.dumps(result,indent=2))
    (HERE/'repguard_modern_control_manifest_2026-10-19.json').write_text(json.dumps({'plan_sha256':sha(dest/'plan.json'),'summary_sha256':sha(dest/'summary.json'),'responses':files},indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
