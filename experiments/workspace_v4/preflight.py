"""Independent source reconstruction first, official scorer second, no models.

The reconstructions are analyst-authored development checks, not new human
annotations or a replacement for the published reference.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from .tools import WorkspaceTools,sha

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results/workspace_v4'
SCORER=ROOT/'results/general_verification_v1/source_intake/DataSpace/evaluation/evaluate.py'
QUERIES={
    'task_269': "SELECT SHName, ActualShares, OughtShares FROM lc_largeshsubscription WHERE SecuCode='000423' ORDER BY id",
    'task_391': 'SELECT "总资产","总负债","国外净资产","国外负债" FROM "其他存款性公司资产负债表" WHERE "总资产">50000000 ORDER BY "截止日期" DESC LIMIT 1',
    'task_380': "SELECT DISTINCT f.Name FROM mf_fundmanagernew f JOIN mf_personalinfo p ON f.PersonalCode=p.PersonalCode WHERE p.Nationality IS NOT NULL AND trim(p.Nationality)<>'' AND p.Nationality<>'中国' ORDER BY f.Name",
    'task_371': 'SELECT SecuAbbr,RRSinceStart FROM mf_netvalueperformancehis ORDER BY id',
    'task_44': 'SELECT treatmentname FROM treatment WHERE patientunitstayid=2602861 AND treatmenttime=(SELECT MAX(treatmenttime) FROM treatment WHERE patientunitstayid=2602861) ORDER BY treatmentid',
}


def reconstruct():
    receipt=OUT/'source_reconstruction_receipt.json'
    if receipt.exists():raise RuntimeError('Source reconstruction already frozen; do not overwrite after gold')
    records={}
    for tid,sql in QUERIES.items():
        w=WorkspaceTools(OUT/'inputs/input'/tid/'context',OUT/'derived_v2'/tid/'workspace.sqlite',OUT/'source_reconstruction_artifacts'/tid)
        r=w.query(sql)
        target=OUT/'source_reconstruction'/tid/'prediction.csv';target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(w.artifacts/(r['result_id']+'.csv'),target)
        records[tid]={'kind':'source_only_sql_reconstruction','sql':sql,'source_trace':r,'prediction_sha256':sha(target)}
    # Records171/174/182: dates on PDFpage4, deposits on pages9/10,
    # currency unit explicitly RMB yuan in source. Visually inspected as well.
    tid='task_35';path=OUT/'source_reconstruction'/tid/'prediction.csv';path.parent.mkdir(parents=True,exist_ok=True)
    rows=[['2004-01-31','7015331.0','598893.0'],['2004-04-30','7587331.0','722349.0'],['2004-12-31','8467057.0','623617.0']]
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f);w.writerow(['date','enterprise_deposits_RMB_yuan','fiscal_deposits_RMB_yuan']);w.writerows(rows)
    pdf=OUT/'inputs/input/task_35/context/doc/中国金融机构人民币信贷收支表.pdf'
    records[tid]={'kind':'source_only_pdf_reconstruction','source_sha256':sha(pdf),'pages':[4,9,10],
                  'source_record_ids':[171,174,182],'prediction_sha256':sha(path),'visual_pages_inspected':True}
    value={'created_utc':datetime.now(timezone.utc).isoformat(),'stage':'source-only reconstruction frozen before gold/config contents opened',
           'code_sha256':sha(Path(__file__)),'oracle_contents_read_by_this_stage':False,'new_human_annotations':0,'model_calls':0,
           'mapping_note':'task44unitstay2602861 derived from public patient.md target identifier; this is analyst interpretation, not a hidden label.',
           'reconstructions':records}
    receipt.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'source_reconstruction':'frozen','tasks':list(records),'gold_contents_read':False},indent=2))


def load_scorer():
    if sha(SCORER)!='9eeb1edcc72d963610f497ebf98287887659f52656092ada0a55290a066bfbc8':raise ValueError('Scorer source changed')
    spec=importlib.util.spec_from_file_location('pinned_dataspace_evaluator',SCORER)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module


def score():
    frozen=json.loads((OUT/'source_reconstruction_receipt.json').read_text())
    if frozen['code_sha256']!=sha(Path(__file__)):raise ValueError('Source reconstruction code changed before scoring')
    scorer=load_scorer();results=[];controls=[]
    for tid,record in frozen['reconstructions'].items():
        prediction=OUT/'source_reconstruction'/tid/'prediction.csv'
        if sha(prediction)!=record['prediction_sha256']:raise ValueError('Frozen source reconstruction changed')
        config=scorer.load_task_config(OUT/'evaluation/configs'/f'{tid}.json')
        gold=OUT/'evaluation/output'/tid/'gold.csv'
        result=scorer.evaluate_task(config=config,prediction_path=prediction,gold_path=gold).to_dict()
        results.append(result)
        # Oracle self-consistency/negative controls are evaluator checks only.
        original=scorer.evaluate_task(config=config,prediction_path=gold,gold_path=gold)
        with gold.open(encoding='utf-8',newline='') as f:table=list(csv.reader(f))
        negative=OUT/'scorer_controls'/tid/'extra_row.csv';negative.parent.mkdir(parents=True,exist_ok=True)
        with negative.open('w',encoding='utf-8',newline='') as f:
            w=csv.writer(f);w.writerows(table);w.writerow(table[1] if len(table)>1 else ['__extra__']*len(table[0]))
        bad=scorer.evaluate_task(config=config,prediction_path=negative,gold_path=gold)
        controls.append({'task_id':tid,'gold_self_match':original.passed,'extra_row_rejected':not bad.passed})
    summary={'created_utc':datetime.now(timezone.utc).isoformat(),'scope':'Source-only analyst reconstruction and evaluator checks, NOT model performance, independent human adjudication or proof all interpretations are unique.',
             'tasks':results,'source_reconstructions_matching_official':sum(r['passed'] for r in results),
             'scorer_controls':controls,'all_scorer_controls_pass':all(c['gold_self_match'] and c['extra_row_rejected'] for c in controls),
             'model_calls':0,'new_human_annotations':0,
             'go_for_tool_readiness_only':all(r['passed'] for r in results) and all(c['gold_self_match'] and c['extra_row_rejected'] for c in controls)}
    (OUT/'oracle_preflight.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    report=ROOT/'docs/reports/2026-11-09/workspace_v4_oracle_preflight.json';report.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':
    if sys.argv[1]=='reconstruct':reconstruct()
    elif sys.argv[1]=='score':score()
