"""Audit120 new real responses plus24 reused lineage; no API inference."""
import datetime as dt
import hashlib
import json
import sys
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from thesis_pilot.core import digest
from thesis_pilot.tatqa_crossfamily_study import prepare,replay,path,parent,DEST,PARENT,SOURCE
from thesis_pilot.tatqa_scope_tools import verify,incumbent,accept
from thesis_pilot.tatqa_plain_tools import messages
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def audit():
    p,cases=prepare();reg=read(DEST/'registration.json');assert reg['new_responses_at_registration']==0
    assert reg['plan_sha256']==sha(DEST/'plan.json') and reg['run_id']==p['run_id']
    assert read(DEST/'collection_started.json')['epoch']>reg['epoch']
    assert read(DEST/'collection_complete.json')['actual_new_calls']==120
    assert read(DEST/'collection_complete.json')['mock_calls']==0 and len(list((DEST/'responses').glob('*.json')))==120
    assert sha(SOURCE/'tatqa_metric.py')==p['metric_sha256'] and sha(SOURCE/'tatqa_utils.py')==p['utils_sha256']
    assert sha(PARENT/'plan.json')==p['parent_plan_sha256']
    assert sha(DEST/'model_manifest.json')==p['gemma_manifest_sha256']
    with zipfile.ZipFile(DEST/'frozen_source.zip') as z:
        for name,h in p['source_sha256'].items():assert sha(ROOT/'thesis_pilot'/name)==h and hashlib.sha256(z.read(name)).hexdigest()==h
    stats={'new_completed':0,'cached_real_qwen_direct':0,'unresolved':0,'native_thinking_nonempty':0,'length_stops':0,'new_input_tokens':0,'new_output_tokens':0,'raw_invalid':{}}
    identities=set();earliest=float('inf');latest=0
    for c in cases:
        assert set(c)=={'id','context_id','question','table','paragraphs'} and all(set(x)=={'uid','order','text'} for x in c['paragraphs'])
        effective,outputs=replay(c,p)
        for family in ['qwen','gemma']:
            previous=None;cfg=p['models'][family]
            for action in ['plain','self1','self2']:
                name=f'{family}_{action}';o=outputs[name];response=o['response']
                assert o['model']==cfg['name'] and o['app']==cfg['app'] and o['model_digest']==cfg['digest']
                assert o['live_inference'] is True and o['evaluation_volume_mounted'] is False and o['actual_thinking_chars']==0 and not response['message'].get('thinking')
                assert 'L40S' in o['gpu'] and response['done'] and response['model']==cfg['name']
                assert response['eval_count']<=4096 and response['prompt_eval_count']<=12288
                assert o['prompt_sha256']==digest(messages(c,incumbent(previous) if previous is not None else None))
                v=verify(c,response['message']['content'],plain=True);assert v==o['verification']
                previous=accept(previous,v) if previous is not None else v
                if name=='qwen_plain':
                    assert o==parent(c);stats['cached_real_qwen_direct']+=1;continue
                r=read(path(c['id'],family,action));assert r['state']=='completed' and r['run_id']==p['run_id'] and r['case_id']==c['id'] and r['family']==family and r['action']==action
                ident=(c['id'],name);assert ident not in identities;identities.add(ident)
                timestamp=dt.datetime.fromisoformat(response['created_at'].replace('Z','+00:00')).timestamp();assert timestamp>reg['epoch'] and timestamp<=r['completed_epoch']+10
                earliest=min(earliest,timestamp);latest=max(latest,timestamp)
                stats['new_completed']+=1;stats['length_stops']+=response.get('done_reason')=='length'
                stats['new_input_tokens']+=response.get('prompt_eval_count',0);stats['new_output_tokens']+=response.get('eval_count',0)
                stats['raw_invalid'][name]=stats['raw_invalid'].get(name,0)+(not v['hard_pass'])
    assert stats['new_completed']==120 and stats['cached_real_qwen_direct']==24
    result={'audit':'PASS','run_id':p['run_id'],'stats':stats,'source_files_verified':len(p['source_sha256']),
            'earliest_new_response_utc':dt.datetime.fromtimestamp(earliest,dt.timezone.utc).isoformat(),
            'latest_new_response_utc':dt.datetime.fromtimestamp(latest,dt.timezone.utc).isoformat(),
            'no_new_inference_in_audit':True,'private_annotation_fields_in_prompts':False,'human_semantic_audit':False}
    out=Path(__file__).with_name('repguard_cycle03_crossfamily_audit_2026-10-20.json');out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':audit()
