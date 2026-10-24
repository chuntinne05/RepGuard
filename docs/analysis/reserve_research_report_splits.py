"""Reserve future report-disjoint development/calibration/confirmation IDs.

No outcome extraction or inference. Public TRAIN source only. Exclude reports
from previous live pilots and any resolvable archive question matches. Report
disjointness from the hash-only archive is unresolved; see the separate audit.
"""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]

def read(p):return json.loads(p.read_text())
def sha(x):return hashlib.sha256(x.encode()).hexdigest()
def norm(x):return ' '.join(str(x).casefold().split())

def main():
    path=ROOT/'results/thesis_real_pilot_v2/finqa_train_private.json'
    assert hashlib.sha256(path.read_bytes()).hexdigest()=='49f237eb9779b569473b26b08048867d04635a7cc39ad6a7a5664c55bb428db6'
    raw=read(path);pilot=read(ROOT/'results/thesis_real_pilot_v2/packet_private.json')['visible']['cases']
    cycle1=read(ROOT/'results/thesis_causal_repair_v1/plan.json')['fresh_cases']
    prior=ROOT/'results/routerbench_headroom_v1/cloud/input_private.json'
    hashes=set(read(prior)['datasets']['finqa/test']['query_ids']) if prior.exists() else set()
    live_reports={c['report'] for c in pilot+cycle1}
    archive_reports={'/'.join(r['filename'].split('/')[:2]) for r in raw if sha(norm(r['qa']['question'])) in hashes}
    excluded=live_reports | archive_reports;groups={}
    for r in raw:
        report='/'.join(r['filename'].split('/')[:2])
        if report in excluded:continue
        groups.setdefault(report,[]).append({'id':r['id'],'report':report,'question_sha256':sha(norm(r['qa']['question']))})
    reports=sorted(groups,key=lambda g:sha('repguard-future-report-reservation-20261019:'+g))
    if len(reports)<400:raise RuntimeError('Insufficient remaining report groups for prespecified200/50/150 split')
    # First reserve confirmation, then calibration, then development, without
    # reading answers/programs/gold_inds of the selected future cases.
    counts={'confirmation':150,'calibration':50,'development':200};splits={};start=0;seen_q=set()
    for part,n in counts.items():
        selected=[]
        for report in reports[start:start+n]:
            options=sorted(groups[report],key=lambda c:sha('repguard-future-question-reservation-20261019:'+c['id']))
            c=next((c for c in options if c['question_sha256'] not in seen_q),None)
            if c is None:raise RuntimeError('No unique question in selected report; freeze selection rule before retry')
            selected.append(c);seen_q.add(c['question_sha256'])
        start+=n;splits[part]=selected
    assert len({c['report'] for ss in splits.values() for c in ss})==400
    assert len(seen_q)==400
    out={'scope':'Reserved future IDs only; not a run, not outcome analysis, not official FinQA test split',
         'dataset':'FinQA public TRAIN at pinned revision0f16e2867befa6840783e58be38c9efb9229d742',
         'dataset_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
         'total_train_report_keys':len({'/'.join(r['filename'].split('/')[:2]) for r in raw}),
         'previous_live_reports_excluded':len(live_reports),'archive_hash_count':len(hashes),'archive_matched_reports_excluded':len(archive_reports),
         'union_seen_reports_excluded':len(excluded),'eligible_report_count':len(reports),
         'selection':'SHA256 report and question with fixed20261019 salts; one question per company/year report; no outcome-based selection',
         'splits':splits,'annotations_extracted':False,'new_model_calls':0,
         'confirmation_locked':True,'forbidden_use':'Do not run confirmation cases for prompt/method/model selection. Freeze final method, comparator, scoring and statistical plan before any confirmation inference.',
         'known_limits':['Public TRAIN reports may be in model pretraining; this is a held-out report split for method research, not contamination-free benchmark evidence','Company/year filename is the report grouping key, not issuer-disjointness','150cases are a reservation, not a claim of statistical power. Size may need expansion before opening outcomes based on independently planned effect/margin.','Dataset raw JSON includes annotations, but this reservation code only accesses ID/filename/question and does not extract selected outcomes.']}
    f=HERE/'repguard_reserved_report_splits_2026-10-19.json'
    if f.exists():assert read(f)==out
    else:f.write_text(json.dumps(out,indent=2))
    print(json.dumps({k:v for k,v in out.items() if k!='splits'},indent=2))

if __name__=='__main__':main()
