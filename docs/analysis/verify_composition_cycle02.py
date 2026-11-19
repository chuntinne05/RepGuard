"""Independently recalculate frozen cycle2 from real receipts; no inference."""
import hashlib
import json
import sys
import zipfile
from datetime import datetime
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))
from thesis_pilot.core import digest,correct
from thesis_pilot.composition_tools import messages,canonical,candidate
from repguard_unit_failure_diagnostic import surgery
from thesis_pilot.causal_tools import verify as dsl_verify

def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    dest=ROOT/'results/thesis_composition_cycle_02';plan=read(dest/'plan.json');reg=read(dest/'registration.json')
    assert digest({k:v for k,v in plan.items() if k!='run_id'})[:24]==plan['run_id']==reg['run_id']
    assert sha(dest/'plan.json')==reg['plan_sha256'] and reg['new_responses_at_registration']==0
    with zipfile.ZipFile(dest/'frozen_source.zip') as z:
        for f,h in plan['source_sha256'].items():
            assert sha(ROOT/'thesis_pilot'/f)==h==hashlib.sha256(z.read(f)).hexdigest()
        assert sha(HERE/'repguard_unit_failure_diagnostic.py')==plan['helper_sha256']==hashlib.sha256(z.read('repguard_unit_failure_diagnostic.py')).hexdigest()
    for f,h in plan['parent_files'].items():assert sha(ROOT/f)==h
    primary=read(ROOT/'results/thesis_real_pilot_v2/packet_private.json')['visible']['source_sha256']
    assert len(primary)==7
    for f,h in primary.items():assert sha(ROOT/'thesis_pilot'/f)==h
    cases=read(ROOT/'results/thesis_causal_repair_v1/plan.json')['fresh_cases']
    assert [c['id'] for c in cases]==plan['case_ids'] and len({c['report'] for c in cases})==24
    gold=read(ROOT/'results/thesis_causal_repair_v1/private.json')['gold'];summary=read(dest/'summary.json')
    methods={a:{'correct':0,'output_tokens':0,'input_tokens':0,'ollama_eval_seconds':0,'rows':{}} for a in ['direct_pot','self_review_1','self_review_2','compose']}
    records=[];source_checks=[]
    def cost(o):
        r=o['response'];return [r.get('eval_count',0),r.get('prompt_eval_count',0),(r.get('eval_duration',0)+r.get('prompt_eval_duration',0))/1e9]
    for c in cases:
        assert set(c)=={'id','report','question','table','pre_text','post_text'}
        i=c['id'];h=digest(i)[:16]
        po=read(ROOT/f'results/thesis_pot_control_v1/{h}.json')['output']
        do=read(ROOT/f'results/thesis_causal_repair_v1/fresh/{h}_initial.json')['output']
        base=candidate(canonical(po['response']['message']['content']));v=do['verification']
        a,changed=surgery(v['answer']);dv=dsl_verify(c,json.dumps(a)) if changed else v
        alternative=candidate(dv);current=base;pcost=cost(po);scost=list(pcost)
        states={'direct_pot':base};costs={'direct_pot':pcost}
        for action in ['self_review_1','self_review_2','compose']:
            f=dest/'responses'/f'{h}_{action}.json';r=read(f);o=r['output'];records.append(r)
            assert r['state']=='completed' and r['case_id']==i and r['action']==action
            inp=base if action=='compose' else current;alt=alternative if action=='compose' else None
            assert r['input_current']==inp and r['input_alternative']==alt
            assert digest(messages(c,inp,alt))==o['prompt_sha256']
            assert o['model_digest']==plan['model_digest'] and o['model']==plan['model']
            assert o['app']=='repguard-thesis-real-pilot-20261018' and o['live_inference'] and not o['evaluation_volume_mounted']
            assert o['gpu']=='NVIDIA L4' and o['response']['done']
            assert datetime.fromisoformat(o['response']['created_at'].replace('Z','+00:00'))>datetime.fromisoformat(reg['utc'].replace('Z','+00:00'))
            v=canonical(o['response']['message']['content']);assert v==o['verification']
            new=candidate(v) if v['hard_pass'] else inp
            if action=='compose':costs[action]=[sum(xs) for xs in zip(pcost,cost(do),cost(o))]
            else:
                current=new;scost=[x+y for x,y in zip(scost,cost(o))];costs[action]=list(scost)
            states[action]=new
            source_checks.append({'file':str(f.relative_to(ROOT)),'sha256':sha(f),'prompt_sha256':o['prompt_sha256']})
        for action,state in states.items():
            m=methods[action];ok=bool(state['execution']['hard_pass'] and correct(state['execution']['value'],gold[i]))
            m['correct']+=ok;m['rows'][i]=int(ok)
            for k,v in zip(['output_tokens','input_tokens','ollama_eval_seconds'],costs[action]):m[k]+=v
    assert len(records)==72==len(list((dest/'responses').glob('*.json')))
    for a,m in methods.items():
        for k,v in m.items():
            target=summary['methods'][a][k]
            if isinstance(v,float):assert abs(v-target)<1e-8
            else:assert v==target
        ys=m['rows'];bb=methods['direct_pot']['rows'];s2=methods['self_review_2']['rows']
        assert summary['methods'][a]['rescue_vs_direct']==sum(ys[i] and not bb[i] for i in ys)
        assert summary['methods'][a]['harm_vs_direct']==sum(bb[i] and not ys[i] for i in ys)
        assert summary['methods'][a]['rescue_vs_self2']==sum(ys[i] and not s2[i] for i in ys)
        assert summary['methods'][a]['harm_vs_self2']==sum(s2[i] and not ys[i] for i in ys)
    union=sum(any(m['rows'][i] for m in methods.values()) for i in plan['case_ids']);best=max(m['correct'] for m in methods.values())
    assert summary['action_oracle_union']==union and summary['best_fixed']==best
    assert summary['gate_for_history_learning']==(union>=best+2 and summary['methods']['compose']['rescue_vs_self2']>=2)
    assert read(dest/'collection_complete.json')['completed']==72 and summary['mock_calls']==0
    manifest={'run_id':plan['run_id'],'plan_sha256':sha(dest/'plan.json'),'responses':source_checks,
              'summary_sha256':sha(dest/'summary.json'),'traces_sha256':sha(dest/'traces_private.json')}
    (HERE/'repguard_composition_cycle02_manifest_2026-10-19.json').write_text(json.dumps(manifest,indent=2))
    result={'status':'PASS','real_completed_responses':72,'distinct_development_reports':24,
            'primary_seven_files_unchanged':True,'registered_before_new_responses':True,
            'source_and_parent_hashes_verified':True,'prompts_and_public_field_whitelists_verified':True,
            'arithmetic_reexecuted':True,'mechanical_fallback_chain_verified':True,'outcomes_and_deployment_compute_recalculated':True,
            'gate_recalculated':True,'mock_calls':0,'independent_test':False,
            'limitation':'Verification of records/arithmetic is not independent human semantic adjudication or provider billing verification.',
            'methods':{a:{k:v for k,v in m.items() if k!='rows'} for a,m in methods.items()}}
    (HERE/'repguard_composition_cycle02_verification_2026-10-19.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
