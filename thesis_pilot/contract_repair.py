"""Real, bounded history-only validation of explicit output-contract repair."""
import hashlib
import json
import time
import zipfile
from pathlib import Path
from .cli import ROOT,OUT,read
from .core import correct,digest
from .pipeline import atomic

DEST=ROOT/'results/thesis_contract_repair_v1'


def main():
    import modal
    previous=read(ROOT/'results/thesis_contract_diagnostic_v1/summary.json')
    packet=read(OUT/'packet_private.json')
    cases=[c for c in packet['visible']['cases'] if packet['visible']['partition'][c['id']]=='history'][:8]
    plan={'scope':'HISTORY-only integration repair; not independent evaluation',
          'case_ids':[c['id'] for c in cases],'parent_run':packet['run_id'],
          'agent':'B','variants':['explicit_status','schema_prompt'],'max_new_model_calls':16,
          'screen_used':False,'quality_retries':False,
          'source_sha256':{f:hashlib.sha256(Path(__file__).with_name(f).read_bytes()).hexdigest()
              for f in ['core.py','live_app.py','source_checks.py','contract_repair.py']}}
    plan['run_id']=digest(plan)[:24]
    path=DEST/'plan.json'
    if path.exists() and read(path)!=plan:raise RuntimeError('Contract-repair plan changed')
    atomic(path,plan)
    if not (DEST/'frozen_source.zip').exists():
        with zipfile.ZipFile(DEST/'frozen_source.zip','w') as z:
            for f in plan['source_sha256']:z.write(Path(__file__).with_name(f),f)
    server=modal.Cls.from_name('repguard-thesis-real-pilot-20261018','LiveOllama')()
    rows=[]
    for variant in plan['variants']:
        for index,case in enumerate(cases):
            target=DEST/f'{variant}_{index:02d}.json'
            if target.exists():
                row=read(target)
                if row.get('state')!='completed':raise RuntimeError('Unresolved call; no silent retry')
            else:
                atomic(target,{'state':'initiated','case_id':case['id'],'variant':variant,'epoch':time.time()})
                result=server.solve.remote(case,'B',variant)
                row={'state':'completed','case_id':case['id'],'variant':variant,'output':result}
                atomic(target,row)
            rows.append(row)
            print(variant,index+1,'/8',row['output']['verification']['errors'],flush=True)
    summary={**plan,'actual_new_model_calls':len(rows),'mock_model_calls':0,'variants':{},
             'previous_8_history_results':previous['variants'],
             'frozen_B_same_8_history':previous['frozen_B_same_8_history']}
    for variant in plan['variants']:
        group=[r for r in rows if r['variant']==variant]
        checks=[(r['output']['verification'],packet['evaluation']['gold'][r['case_id']]) for r in group]
        summary['variants'][variant]={'questions':len(group),
            'source_bound_executable':sum(c['hard_pass'] for c,g in checks),
            'candidate_correct':sum(correct(c['value'],g) for c,g in checks),
            'checked_and_correct':sum(c['hard_pass'] and correct(c['value'],g) for c,g in checks),
            'input_tokens':sum(r['output']['response'].get('prompt_eval_count',0) for r in group),
            'output_tokens':sum(r['output']['response'].get('eval_count',0) for r in group)}
    atomic(DEST/'summary.json',summary)
    atomic(ROOT/'docs/analysis/repguard_contract_repair_2026-10-18.json',summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':main()
