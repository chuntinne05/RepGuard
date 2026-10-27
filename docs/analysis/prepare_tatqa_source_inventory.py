"""Source/metric inventory, not a new inference experiment or result.

Select64 TRAIN contexts by metadata before extracting annotations. No dev/test
downloaded. Gold-only fields are kept separately from solver-visible records.
"""
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
SRC=Path('/tmp/repguard_tatqa_source');DEST=ROOT/'results/thesis_tatqa_source_v1'

def read(p):return json.loads(p.read_text())
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def norm(s):return ' '.join(str(s).casefold().split())

def main():
    manifest=read(SRC/'manifest.json')
    assert manifest['revision']=='870accc41953dcde885aabeb963d94aabdc0fbc3'
    for name,item in manifest['files'].items():assert hashlib.sha256((SRC/Path(name).name).read_bytes()).hexdigest()==item['sha256']
    rows=read(SRC/'tatqa_dataset_train.json');finqa=read(ROOT/'results/thesis_real_pilot_v2/finqa_train_private.json')
    excluded_questions={digest(norm(r['qa']['question'])) for r in finqa}
    excluded_tables={digest([[norm(x) for x in row] for row in r['table']]) for r in finqa}
    available=[];removed_q=0;removed_table=0
    for row in rows:
        if digest([[norm(x) for x in rr] for rr in row['table']['table']]) in excluded_tables:
            removed_table+=1;continue
        eligible=[]
        for q in row['questions']:
            if q['answer_type']!='arithmetic':continue
            if digest(norm(q['question'])) in excluded_questions:removed_q+=1;continue
            eligible.append(q)
        if eligible:
            q=min(eligible,key=lambda q:digest('repguard-tatqa-inventory-question:'+q['uid']))
            available.append((row,q))
    chosen=sorted(available,key=lambda rq:digest('repguard-tatqa-inventory-context:'+rq[0]['table']['uid']))[:64]
    assert len(chosen)==64 and len({r['table']['uid'] for r,q in chosen})==64
    public=[];private={}
    for r,q in chosen:
        public.append({'id':q['uid'],'context_id':r['table']['uid'],'question':q['question'],
                       'table':r['table']['table'],'paragraphs':[{'uid':p['uid'],'order':p['order'],'text':p['text']} for p in r['paragraphs']]})
        # Only after the selection above: never include these fields in prompts.
        private[q['uid']]={k:q[k] for k in ['answer','scale','derivation','answer_type','answer_from','rel_paragraphs','req_comparison']}
    inventory={'scope':'Preparation only.64 arithmetic TRAIN contexts; zero model calls. Not an independent test of any method.',
               'source':manifest,'train_contexts':len(rows),'train_questions':sum(len(r['questions']) for r in rows),
               'answer_types':dict(Counter(q['answer_type'] for r in rows for q in r['questions'])),
               'arithmetic_scale_distribution':dict(Counter(q['scale'] for r in rows for q in r['questions'] if q['answer_type']=='arithmetic')),
               'selection':'One arithmetic question per context; SHA256 context then question; exclude exact normalized questions and exact normalized tables in FinQA TRAIN6251, before extracting selected answers.',
               'finqa_duplicate_questions_removed':removed_q,'finqa_duplicate_context_tables_removed':removed_table,
               'selected':len(public),'public_sha256':digest(public),'case_ids':[c['id'] for c in public],
               'known_limits':['Context UID is not document/report identity; report-disjointness NOT established','Exact dedup does not exclude paraphrases, related tables or pretraining contamination','Do not send scale/derivation/rel_paragraphs/answer_from/req_comparison annotations to solver','Official evaluator requires model-predicted scale; cannot fill it from gold','Official numeric normalization rounds differently from strict FinQA round5; preserve separate metric','Pass predictions as nonempty list/string so a legitimate zero is not mistaken for no prediction','No benchmark-level official score until original evaluator actually runs'],
               'model_calls':0,'dev_or_test_downloaded':False}
    DEST.mkdir(exist_ok=True)
    for name in manifest['files']:
        f=SRC/Path(name).name;target=DEST/f.name
        if target.exists():assert target.read_bytes()==f.read_bytes()
        else:target.write_bytes(f.read_bytes())
    for name,value in [('manifest.json',manifest),('public_development_inventory.json',public),('annotations_private.json',private),('inventory.json',inventory)]:
        f=DEST/name
        if f.exists():assert read(f)==value
        else:f.write_text(json.dumps(value,ensure_ascii=False,indent=2))
    (HERE/'repguard_tatqa_source_inventory_2026-10-19.json').write_text(json.dumps(inventory,indent=2))
    print(json.dumps({k:v for k,v in inventory.items() if k not in ['case_ids','source']},indent=2))

if __name__=='__main__':main()
