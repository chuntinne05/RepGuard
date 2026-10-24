"""Bounded HISTORY-only real diagnostic; never alters the completed v2 pilot."""
import hashlib
import json
import time
from pathlib import Path
from .cli import ROOT,OUT,read
from .core import correct,digest
from .pipeline import atomic
from .source_checks import strict_verify

DEST=ROOT/'results/thesis_contract_diagnostic_v1'


def main():
    import modal
    packet=read(OUT/'packet_private.json')
    if read(OUT/'cloud/evaluation/status.json')['state']!='completed_development_review_required':
        raise RuntimeError('Finish and preserve the frozen pilot first')
    cases=[c for c in packet['visible']['cases'] if packet['visible']['partition'][c['id']]=='history'][:8]
    plan={'scope':'HISTORY-only development diagnostic, not independent evaluation',
          'parent_run':packet['run_id'],'case_ids':[c['id'] for c in cases],
          'agent':'B','variants':['unconstrained_json','reasoning_first'],'max_model_calls':16,
          'source_sha256':{f:hashlib.sha256(Path(__file__).with_name(f).read_bytes()).hexdigest()
                           for f in ['core.py','live_app.py','diagnostic.py','source_checks.py']},
          'raw_json_required':True,'strip_markdown_fences':False,
          'no_quality_retries':True,'test_screen_used':False}
    plan['run_id']=digest(plan)[:24]
    path=DEST/'plan.json'
    if path.exists() and read(path)!=plan:raise RuntimeError('Diagnostic plan changed')
    atomic(path,plan)
    server=modal.Cls.from_name('repguard-thesis-real-pilot-20261018','LiveOllama')()
    rows=[]
    for variant in plan['variants']:
        for index,case in enumerate(cases):
            target=DEST/f'{variant}_{index:02d}.json'
            if target.exists():
                row=read(target)
                if row.get('state')!='completed':raise RuntimeError('Unresolved initiated request; do not retry silently')
            else:
                atomic(target,{'state':'initiated','case_id':case['id'],'variant':variant,'epoch':time.time()})
                output=server.solve.remote(case,'B',variant)
                row={'state':'completed','case_id':case['id'],'variant':variant,'output':output}
                atomic(target,row)
            rows.append(row)
            print(variant,index+1,'/8',row['output']['verification']['errors'],flush=True)
    summary={**plan,'actual_model_calls':len(rows),'mock_model_calls':0,'variants':{}}
    original={}
    for path in (OUT/'cloud/responses').glob('case_*.json'):
        row=read(path)
        if row['agent']=='B' and row['case_id'] in plan['case_ids']:original[row['case_id']]=row
    checks=[(c,strict_verify(c,original[c['id']]['response']['message']['content'])) for c in cases]
    summary['frozen_B_same_8_history']={'questions':len(checks),
        'source_bound_executable':sum(v['hard_pass'] for c,v in checks),
        'candidate_correct':sum(correct(v['value'],packet['evaluation']['gold'][c['id']]) for c,v in checks),
        'new_model_calls':0,'source':'Preserved actual v2 responses, not newly inferred'}
    for variant in plan['variants']:
        group=[r for r in rows if r['variant']==variant]
        summary['variants'][variant]={'questions':len(group),
             'source_bound_executable':sum(r['output']['verification']['hard_pass'] for r in group),
             'candidate_correct':sum(correct(r['output']['verification']['value'],packet['evaluation']['gold'][r['case_id']]) for r in group),
             'checked_and_correct':sum(r['output']['verification']['hard_pass'] and correct(r['output']['verification']['value'],packet['evaluation']['gold'][r['case_id']]) for r in group),
             'input_tokens':sum(r['output']['response'].get('prompt_eval_count',0) for r in group),
             'output_tokens':sum(r['output']['response'].get('eval_count',0) for r in group)}
    atomic(DEST/'summary.json',summary)
    atomic(ROOT/'docs/analysis/repguard_contract_diagnostic_2026-10-18.json',summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':main()
