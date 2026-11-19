"""Explicit pre-model development amendment and public packet construction."""
import csv
import json
from datetime import datetime,timezone
from pathlib import Path

from .preflight import OUT,ROOT,load_scorer
from .tools import WorkspaceTools,sha


def main():
    receipt=OUT/'readiness_amendment.json'
    if receipt.exists():raise RuntimeError('Readiness already frozen')
    original=json.loads((OUT/'oracle_preflight.json').read_text())
    # Original source-only interpretation omitted the date; published output
    # expects it. Keep5/6 unchanged and make this output requirement explicit
    # BEFORE model inference. Do not call the adapted input official-original QA.
    tid='task_391'
    sql='SELECT "截止日期","总资产","总负债","国外净资产","国外负债" FROM "其他存款性公司资产负债表" WHERE "总资产">50000000 ORDER BY "截止日期" DESC LIMIT 1'
    w=WorkspaceTools(OUT/'inputs/input'/tid/'context',OUT/'derived_v2'/tid/'workspace.sqlite',OUT/'readiness_artifacts'/tid)
    result=w.query(sql);scorer=load_scorer()
    config=scorer.load_task_config(OUT/'evaluation/configs'/f'{tid}.json')
    scored=scorer.evaluate_task(config=config,prediction_path=w.artifacts/(result['result_id']+'.csv'),gold_path=OUT/'evaluation/output'/tid/'gold.csv').to_dict()
    if not scored['passed']:raise RuntimeError('Amended date-inclusive source reconstruction still disagrees')
    if not original['all_scorer_controls_pass'] or any(not r['passed'] for r in original['tasks'] if r['task_id']!=tid):raise RuntimeError('Other source gates failed')
    inputs=OUT/'inputs/input';inventory=json.loads((OUT/'source_views/input_inventory.json').read_text())
    task_order=json.loads((ROOT/'results/general_verification_v1/source_intake/DataSpace/source_inspection_public_tasks.json').read_text())['tasks']
    tasks=[]
    for row in task_order:
        ident=row['task_id'];q=json.loads((inputs/ident/'task.json').read_text())['question']
        modified=q+' Include the record date as the first column, followed by the four amounts.' if ident==tid else q
        pdfs={p['path']:json.loads((OUT/'source_views'/ident/(Path(p['path']).stem+'.pdf_text.json')).read_text()) for p in inventory['tasks'][ident]['pdfs']}
        for p in inventory['tasks'][ident]['pdfs']:
            if sha(inputs/ident/'context'/p['path'])!=p['source_sha256']:raise ValueError('PDF view source changed')
        tasks.append({'id':ident,'question':modified,'original_question':q,'input_amended':ident==tid,'pdf_views':pdfs})
    packet={'tasks':tasks,'source_archive_sha256':json.loads((OUT/'source_receipt.json').read_text())['archive_sha256']}
    (OUT/'public_packet.json').write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n')
    amendment={'created_utc':datetime.now(timezone.utc).isoformat(),'original_source_check':'5of6match,task391column_count4vs5',
               'amended_task':tid,'amendment':'Explicitly request record date followed by four amounts. Gold values unchanged.',
               'amended_source_check':scored,'all_source_checks_pass_after_declared_amendment':True,
               'source_gate_scope':'GO for engineering tool-readiness only; not semantic adjudication or scientific expansion.',
               'human_adjudications':0,'corpus_model_calls_before_amendment':0,
               'public_packet_sha256':sha(OUT/'public_packet.json'),'public_packet_contains_gold':False}
    receipt.write_text(json.dumps(amendment,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'docs/reports/2026-11-09/workspace_v4_readiness_amendment.json').write_text(json.dumps(amendment,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in amendment.items() if k!='amended_source_check'},indent=2))


if __name__=='__main__':main()
