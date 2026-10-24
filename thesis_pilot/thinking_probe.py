"""Eight real HISTORY calls for typed-tool feasibility, not confirmation."""
import hashlib
import json
import time
import zipfile
from pathlib import Path
from .cli import ROOT,OUT,read
from .core import correct,digest
from .pipeline import atomic
from .typed_tools import messages,catalogue

DEST=ROOT/'results/thesis_typed_thinking_probe_v1'


def main():
    import modal
    read(ROOT/'results/thesis_contract_repair_v1/summary.json')
    packet=read(OUT/'packet_private.json')
    cases=[c for c in packet['visible']['cases'] if packet['visible']['partition'][c['id']]=='history'][:8]
    files=['typed_tools.py','live_app.py','thinking_probe.py','core.py','source_checks.py']
    plan={'scope':'8 HISTORY questions, typed native-thinking feasibility; NOT independent evaluation',
        'parent_run':packet['run_id'],'case_ids':[c['id'] for c in cases],
        'agent':'B','model':'qwen3:14b','max_new_model_calls':8,'think':True,'num_predict':4096,
        'screen_used':False,'quality_retries':False,'numeric_targets':'Unchanged FinQA exe_ans,5 decimals; no factor100 matching',
        'known_limit':'History includes semantic/unit ambiguity; typed outputs do not establish reputation gain',
        'source_sha256':{f:hashlib.sha256(Path(__file__).with_name(f).read_bytes()).hexdigest() for f in files},
        'catalogue_entries':[len(catalogue(c)) for c in cases],
        'serialized_prompt_chars':[len(json.dumps(messages(c))) for c in cases]}
    plan['run_id']=digest(plan)[:24]
    if (DEST/'plan.json').exists() and read(DEST/'plan.json')!=plan:raise RuntimeError('Changed typed probe')
    atomic(DEST/'plan.json',plan)
    if not (DEST/'frozen_source.zip').exists():
        with zipfile.ZipFile(DEST/'frozen_source.zip','w') as z:
            for f in files:z.write(Path(__file__).with_name(f),f)
    server=modal.Cls.from_name('repguard-thesis-real-pilot-20261018','LiveOllama')()
    rows=[]
    for i,case in enumerate(cases):
        target=DEST/f'case_{i:02d}.json'
        if target.exists():
            row=read(target)
            if row.get('state')!='completed':raise RuntimeError('Unresolved real input; do not retry silently')
        else:
            atomic(target,{'state':'initiated','case_id':case['id'],'epoch':time.time()})
            output=server.typed_solve.remote(case,True)
            row={'state':'completed','case_id':case['id'],'output':output};atomic(target,row)
        rows.append(row);print('typed_reasoning',i+1,'/8',row['output']['verification']['errors'],flush=True)
    checks=[(r['output']['verification'],packet['evaluation']['gold'][r['case_id']]) for r in rows]
    result={**plan,'actual_new_model_calls':len(rows),'mock_model_calls':0,
        'responses_with_native_thinking':sum(bool(r['output']['response']['message'].get('thinking')) for r in rows),
        'source_bound_executable':sum(v['hard_pass'] for v,g in checks),
        'candidate_correct':sum(correct(v['value'],g) for v,g in checks),
        'checked_and_correct':sum(v['hard_pass'] and correct(v['value'],g) for v,g in checks),
        'input_tokens':sum(r['output']['response'].get('prompt_eval_count',0) for r in rows),
        'output_tokens':sum(r['output']['response'].get('eval_count',0) for r in rows)}
    atomic(DEST/'summary.json',result)
    atomic(ROOT/'docs/analysis/repguard_typed_thinking_probe_2026-10-18.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':main()
