"""Native-thinking competence check on eight already-seen HISTORY items only."""
import hashlib
import json
import time
import zipfile
from pathlib import Path
from .cli import ROOT,read
from .core import digest,correct
from .pipeline import atomic
from .competence_tools import messages,verify

DEST=ROOT/'results/thesis_competence_probe_v1'
FILES=['competence_tools.py','competence_probe.py','live_app.py','causal_tools.py','typed_tools.py','source_checks.py','core.py']

def main():
    import modal
    source=read(ROOT/'results/thesis_causal_repair_v1/plan.json')
    private=read(ROOT/'results/thesis_causal_repair_v1/private.json')
    cases=source['history_diagnostic'];arms=['dsl_native','numeric_native','numeric_raw_native']
    plan={'scope':'8 repeatedly seen HISTORY questions, competence diagnostics only; not confirmation',
     'parent_run':source['run_id'],'case_ids':[c['id'] for c in cases],
     'arms':arms,'max_new_calls':24,'thinking':True,'num_predict':4096,'num_ctx':16384,
     'model':'qwen3:14b','same_public_evidence':True,'quality_retries':False,
     'comparison':'DSL native vs nonthinking same DSL has different generation cap. Numeric native vs DSL native changes output contract/instructions with same data. Numeric raw native vs numeric native has identical system/output contract but changes serialization (raw matrix vs catalogue). Not cost matched by input tokens.',
     'scoring':'Unchanged FinQA exe_ans round5, no factor100 oracle. Numeric arm has no source-verification claim.',
     'source_sha256':{f:hashlib.sha256(Path(__file__).with_name(f).read_bytes()).hexdigest() for f in FILES}}
    plan['run_id']=digest(plan)[:24]
    if (DEST/'plan.json').exists():assert read(DEST/'plan.json')==plan
    else:
        atomic(DEST/'plan.json',plan)
        with zipfile.ZipFile(DEST/'frozen_source.zip','w') as z:
            for f in FILES:z.write(Path(__file__).with_name(f),f)
    server=modal.Cls.from_name('repguard-thesis-real-pilot-20261018','LiveOllama')();rows=[]
    for c in cases:
        for arm in arms:
            f=DEST/f'{digest(c["id"])[:16]}_{arm}.json'
            if f.exists():
                row=read(f)
                if row['state']!='completed':raise RuntimeError('Unresolved real call; no silent retry')
            else:
                atomic(f,{'state':'initiated','case_id':c['id'],'contract':arm,'epoch':time.time()})
                o=server.competence_solve.remote(c,arm)
                row={'state':'completed','case_id':c['id'],'contract':arm,'output':o};atomic(f,row)
            o=row['output'];assert o['prompt_sha256']==digest(messages(c,arm))
            assert o['verification']==verify(c,o['response']['message']['content'],arm)
            assert o['live_inference'] and not o['evaluation_volume_mounted']
            assert o['model_digest']=='bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8'
            rows.append(row);print(len(rows),c['id'],arm,'value',o['verification']['value'],'errors',o['verification']['errors'],flush=True)
    result={**plan,'actual_new_calls':len(rows),'mock_calls':0,
       'input_tokens':sum(r['output']['response'].get('prompt_eval_count',0) for r in rows),
       'output_tokens':sum(r['output']['response'].get('eval_count',0) for r in rows),
       'native_thinking_nonempty':sum(bool(r['output']['actual_thinking_chars']) for r in rows),'results':{}}
    for arm in arms:
        rr=[r for r in rows if r['contract']==arm]
        result['results'][arm]={'n':len(rr),'valid':sum(r['output']['verification']['hard_pass'] for r in rr),
          'correct':sum(r['output']['verification']['hard_pass'] and correct(r['output']['verification']['value'],private['gold'][r['case_id']]) for r in rr),
          'source_verified':arm=='dsl_native'}
    atomic(DEST/'summary.json',result);atomic(ROOT/'docs/analysis/repguard_competence_probe_2026-10-18.json',result)
    print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':main()
