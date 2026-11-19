"""Independent receipt, provenance, privacy and local-execution audit (no API calls)."""
import datetime as dt
import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from thesis_pilot.core import digest
from thesis_pilot.tatqa_scope_tools import messages,verify,incumbent,accept,scope_ok,combined

def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def audit():
    folder=ROOT/'results/thesis_tatqa_scoped_repair_v1';p=load(folder/'plan.json');reg=load(folder/'registration.json')
    assert digest({k:v for k,v in p.items() if k!='run_id'})[:24]==p['run_id']
    assert reg['run_id']==p['run_id'] and reg['plan_sha256']==sha(folder/'plan.json') and reg['new_responses_at_registration']==0
    assert load(folder/'collection_started.json')['epoch']>reg['epoch']
    with zipfile.ZipFile(folder/'frozen_source.zip') as z:
        for name,h in p['source_sha256'].items():
            assert hashlib.sha256(z.read(name)).hexdigest()==h
            assert sha(ROOT/'thesis_pilot'/name)==h
    src=ROOT/'results/thesis_tatqa_source_v1'
    assert sha(src/'public_development_inventory.json')==p['public_inventory_sha256']
    assert sha(src/'tatqa_metric.py')==p['metric_sha256'] and sha(src/'tatqa_utils.py')==p['utils_sha256']
    assert p['public_cases']==load(src/'public_development_inventory.json')[:24]
    assert len({c['id'] for c in p['public_cases']})==24 and len({c['context_id'] for c in p['public_cases']})==24
    complete=load(folder/'collection_complete.json');assert complete['actual_new_calls']==144 and complete['mock_calls']==0
    paths=list((folder/'responses').glob('*.json'));assert len(paths)==144
    stats={'completed':0,'unresolved':0,'length_stops':0,'input_tokens':0,'output_tokens':0,'scoped_permission_violations':{'evidence':0,'operation':0},'raw_invalid_by_action':{a:0 for a in p['actions']}}
    identities=set();earliest=float('inf');latest=0
    for c in p['public_cases']:
        assert set(c)=={'id','context_id','question','table','paragraphs'}
        assert all(set(x)=={'uid','order','text'} for x in c['paragraphs'])
        effective={};raw={}
        for action in p['actions']:
            file=folder/'responses'/f'{digest(c["id"])[:16]}_{action}.json';r=load(file)
            assert r['state']=='completed' and r['run_id']==p['run_id'] and r['case_id']==c['id'] and r['action']==action
            key=(c['id'],action);assert key not in identities;identities.add(key)
            o=r['output'];resp=o['response'];v=verify(c,resp['message']['content'],plain=action=='plain');assert v==o['verification']
            a='self' if action.startswith('self') else action
            b=effective['self1'] if action=='self2' else effective.get('initial')
            current=incumbent(b) if action in ['evidence','operation','self1','self2'] else None
            assert o['prompt_sha256']==digest(messages(c,a,current))
            assert o['app']==p['app'] and o['model']==p['model'] and o['model_digest']==p['model_digest']
            assert o['live_inference'] is True and o['evaluation_volume_mounted'] is False
            assert o['actual_thinking_chars']==0 and not resp['message'].get('thinking') and 'L40S' in o['gpu']
            assert resp['done'] and resp['model']==p['model'] and resp['eval_count']<=p['num_predict'] and resp['prompt_eval_count']<=12288
            created=dt.datetime.fromisoformat(resp['created_at'].replace('Z','+00:00')).timestamp()
            assert created>reg['epoch'] and created<=r['completed_epoch']+10
            earliest=min(earliest,created);latest=max(latest,created)
            if action in ['plain','initial']:effective[action]=v
            elif action.startswith('self'):effective[action]=accept(b,v)
            else:
                permitted=scope_ok(b['proposal'],v['proposal'],action);stats['scoped_permission_violations'][action]+=not permitted
                effective[action]=accept(b,v,permitted)
            raw[action]=v;stats['completed']+=1;stats['length_stops']+=resp.get('done_reason')=='length'
            stats['raw_invalid_by_action'][action]+=not v['hard_pass'];stats['input_tokens']+=resp.get('prompt_eval_count',0);stats['output_tokens']+=resp.get('eval_count',0)
        eo,info=combined(c,effective['initial'],raw['evidence'],raw['operation'])
        if info['accepted']:assert eo['hard_pass']
    assert stats['completed']==144
    # The original primary seven-source study must remain reproducible.
    old=load(ROOT/'results/thesis_real_pilot_v2/packet_private.json')['visible']['source_sha256']
    for name,h in old.items():assert sha(ROOT/'thesis_pilot'/name)==h
    result={'audit':'PASS','run_id':p['run_id'],'real_responses':stats,'frozen_sources_verified':len(p['source_sha256']),
            'original_primary_sources_unchanged':True,'earliest_response_utc':dt.datetime.fromtimestamp(earliest,dt.timezone.utc).isoformat(),
            'latest_response_utc':dt.datetime.fromtimestamp(latest,dt.timezone.utc).isoformat(),
            'privacy':'Public allowlists verified; remote API only mounts research weights volume. No gold annotations passed.',
            'note':'Deterministic software replay of REAL model outputs, not new inference or a semantic-label audit.'}
    dest=Path(__file__).with_name('repguard_cycle03_audit_2026-10-20.json');dest.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':audit()
