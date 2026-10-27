"""A standard-form arithmetic-program control on all24 existing development cases."""
import hashlib
import json
import time
import zipfile
from pathlib import Path
from .cli import ROOT,read
from .core import digest,correct
from .pipeline import atomic
from .pot_tools import messages,verify

DEST=ROOT/'results/thesis_pot_control_v1'
FILES=['pot_tools.py','pot_probe.py','live_app.py','core.py']

def main():
    import modal
    source=read(ROOT/'results/thesis_causal_repair_v1/plan.json')
    private=read(ROOT/'results/thesis_causal_repair_v1/private.json');cases=source['fresh_cases']
    plan={'scope':'All24 previous development reports, standard arithmetic-program control, not independent confirmation',
     'parent_run':source['run_id'],'case_ids':[c['id'] for c in cases],'max_new_calls':24,'max_collection_wall_seconds':3600,
     'model':'qwen3:14b','thinking':True,'num_predict':4096,'num_ctx':16384,'seed':18102026,'temperature':0,
     'quality_retries':False,'source_binding_required':False,'gold_at_inference':False,
     'numeric_scoring':'Unchanged FinQA exe_ans exact final round5; no factor100 oracle or new tolerance',
     'known_limit':'Not output-cap matched to nonthinking1536 DSL; code execution does not prove source fidelity; development-only',
     'motivation':'Primary repair pool has no headroom; direct numeric controls have rounding/truncation confounds; add familiar variable-name Python arithmetic with runtime execution',
     'prior_art':'PoT2211.12588/PAL2211.10435 inspired arithmetic-Python control, not a reproduction of the complete published protocols',
     'source_sha256':{f:hashlib.sha256(Path(__file__).with_name(f).read_bytes()).hexdigest() for f in FILES}}
    plan['run_id']=digest(plan)[:24]
    if (DEST/'plan.json').exists():assert read(DEST/'plan.json')==plan
    else:
        atomic(DEST/'plan.json',plan)
        with zipfile.ZipFile(DEST/'frozen_source.zip','w') as z:
            for f in FILES:z.write(Path(__file__).with_name(f),f)
    begin=time.monotonic();server=modal.Cls.from_name('repguard-thesis-real-pilot-20261018','LiveOllama')();rows=[]
    for c in cases:
        f=DEST/f'{digest(c["id"])[:16]}.json'
        if f.exists():
            row=read(f)
            if row['state']!='completed':raise RuntimeError('Unresolved initiated real call; no silent retry')
        else:
            if time.monotonic()-begin>plan['max_collection_wall_seconds']:raise RuntimeError('PoT collection wall cap')
            atomic(f,{'state':'initiated','case_id':c['id'],'epoch':time.time()})
            o=server.pot_solve.remote(c);row={'state':'completed','case_id':c['id'],'output':o};atomic(f,row)
        o=row['output'];assert digest(messages(c))==o['prompt_sha256']
        assert verify(o['response']['message']['content'])==o['verification']
        assert o['model_digest']=='bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8'
        rows.append(row);print(len(rows),c['id'],'value',o['verification']['value'],'errors',o['verification']['errors'],flush=True)
    score=sum(r['output']['verification']['hard_pass'] and correct(r['output']['verification']['value'],private['gold'][r['case_id']]) for r in rows)
    b=read(ROOT/'results/thesis_causal_repair_v1/outcomes_private.json')['outcomes']
    result={**plan,'actual_new_calls':len(rows),'mock_calls':0,'correct':score,'n':len(rows),
      'executable':sum(r['output']['verification']['hard_pass'] for r in rows),
      'native_thinking_nonempty':sum(bool(r['output']['actual_thinking_chars']) for r in rows),
      'rescues_vs_original_initial':sum(r['output']['verification']['hard_pass'] and correct(r['output']['verification']['value'],private['gold'][r['case_id']]) and not b[r['case_id']]['initial'] for r in rows),
      'harms_vs_original_initial':sum(b[r['case_id']]['initial'] and not (r['output']['verification']['hard_pass'] and correct(r['output']['verification']['value'],private['gold'][r['case_id']])) for r in rows),
      'input_tokens':sum(r['output']['response'].get('prompt_eval_count',0) for r in rows),
      'output_tokens':sum(r['output']['response'].get('eval_count',0) for r in rows),
      'request_wall_seconds':sum(r['output']['wall_seconds'] for r in rows)}
    atomic(DEST/'summary.json',result);atomic(ROOT/'docs/analysis/repguard_pot_control_results_2026-10-18.json',result)
    print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':main()
