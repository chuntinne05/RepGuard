"""Independent artifact verification, no model calls or generated solver outputs."""
import hashlib,json,zipfile,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from thesis_pilot.pipeline import verify_visible,load_responses,validate,atomic
from thesis_pilot.source_checks import strict_verify
from thesis_pilot.typed_tools import verify as typed_verify
from thesis_pilot.core import correct

root=Path.cwd()
def read(path):return json.loads(path.read_text())
out=root/'results/thesis_real_pilot_v2';packet=read(out/'packet_private.json')
verify_visible(packet['visible']);responses=load_responses(packet['visible'],out/'cloud/responses')
analysis=read(out/'cloud/evaluation/analysis_private.json');validate(analysis)
main_report=read(root/'docs/analysis/repguard_thesis_pilot_results_2026-10-18.json')
assert main_report['verification']['cloud_local_recomputation_match'] is True
cases={c['id']:c for c in packet['visible']['cases']}
groups={'thesis_contract_diagnostic_v1':16,'thesis_contract_repair_v1':16,
        'thesis_typed_tools_probe_v1':8,'thesis_typed_thinking_probe_v1':8}
result={};hashes={}
paired_prompts={}
for name,count in groups.items():
    directory=root/'results'/name;plan=read(directory/'plan.json');read(directory/'summary.json')
    with zipfile.ZipFile(directory/'frozen_source.zip') as z:
        for file,expected in plan['source_sha256'].items():
            assert hashlib.sha256(z.read(file)).hexdigest()==expected,(name,file)
    rows=[read(p) for p in directory.glob('*.json') if 'output' in read(p)]
    assert len(rows)==count,(name,len(rows))
    for row in rows:
        assert row['state']=='completed';o=row['output'];case=cases[row['case_id']]
        assert o['app']=='repguard-thesis-real-pilot-20261018' and o['live_inference']
        assert o['evaluation_volume_mounted'] is False and o['gpu']=='NVIDIA L4'
        assert o['model_digest']==packet['visible']['model_digests']['qwen3:14b']
        assert o['response']['model']=='qwen3:14b' and o['response']['done']
        raw=o['response']['message']['content'];variant=o['contract_variant']
        if variant in ['typed_tools','typed_reasoning']:
            paired_prompts[(variant,row['case_id'])]=o['prompt_sha256']
        if variant in ['typed_tools','typed_reasoning']:v=typed_verify(case,raw)
        else:
            if variant in ['reasoning_first','explicit_status','schema_prompt']:
                try:
                    decoded=json.loads(raw);decoded.pop('reasoning',None);raw=json.dumps(decoded)
                except (ValueError,TypeError,AttributeError):pass
            v=strict_verify(case,raw)
        assert v==o['verification'],(name,row['case_id'])
    result[name]={'run_id':plan['run_id'],'actual_responses_verified':count,
        'source_snapshot_hashes_valid':True,'executor_recomputation_match':True,
        'native_thinking_responses':sum(bool(r['output']['response']['message'].get('thinking')) for r in rows)}
    for path in directory.iterdir():
        if path.suffix in ['.json','.zip']:
            hashes[str(path.relative_to(root))]=hashlib.sha256(path.read_bytes()).hexdigest()
for case_id in read(root/'results/thesis_typed_tools_probe_v1/plan.json')['case_ids']:
    assert paired_prompts[('typed_tools',case_id)]==paired_prompts[('typed_reasoning',case_id)]
live=[]
for path in sorted((root/'results/thesis_live_prototype').glob('live-*.json')):
    r=read(path)
    assert r['runtime_case_has_gold'] is False and r['used_cached_solver_output'] is False
    live.append({'id':r['id'],'contract':r.get('contract','frozen'),'actual_model_calls':r['actual_model_calls'],
                 'status':r['status']})
    hashes[str(path.relative_to(root))]=hashlib.sha256(path.read_bytes()).hexdigest()
typed=[read(p) for p in (root/'results/thesis_live_prototype').glob('live-*.json') if read(p).get('contract')=='typed_tools']
assert len(typed)==1
demo=typed[0];v=demo['trace'][0]['verification']
assert v['value']==round(256917/371999,5) and v['hard_pass'] and demo['uses_history_audits']==0
summary={'scope':'Artifact/software verification; no new inference',
    'app':'repguard-thesis-real-pilot-20261018','main_run':packet['run_id'],
    'frozen_main_source_unchanged':True,'main_real_responses_checksum_verified':len(responses),
    'main_cloud_local_recomputation_previously_passed':True,'followups':result,
    'live_runs':live,'actual_live_model_calls':sum(r['actual_model_calls'] for r in live),
    'typed_demo':{'id':demo['id'],'answer':demo['candidate'],'manual_arithmetic_match':True},
    'mock_model_calls':0,'aborted_v1_preserved_separately':True,'earlier_live_failure_artifacts_preserved':True,
    'typed_thinking_pair_same_public_messages':True,'typed_thinking_comparison_has_different_output_budget':True,
    'modal_billing_usd':None}
aborted=[]
for path in (root/'results/thesis_real_pilot_v1/cloud/responses').glob('case_*.json'):
    aborted.append(read(path))
summary['aborted_v1_local_checkpoint']={'known_completed_real_responses':sum(r.get('state')=='complete' for r in aborted),
    'initiated_unresolved':sum(r.get('state')!='complete' for r in aborted),
    'note':'Cancelled arithmetic-bug run; unresolved request usage unknown; never reused in v2'}
atomic(root/'results/thesis_delivery_verification_private.json',{**summary,'file_sha256':hashes})
atomic(root/'docs/analysis/repguard_delivery_verification_2026-10-18.json',summary)
print(json.dumps(summary,ensure_ascii=False,indent=2))
