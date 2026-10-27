"""Use exact original paired masks with unchanged cross-fitted estimators."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import run_dart_gain as transport

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'infra/modal'))
from neural_pipeline import atomic,digest
from history_pipeline import verify
from neural_core import observed_gold,means

OUTPUT=ROOT/'results/dart_paired_history_v1'


def prepare():
    prior=ROOT/'results/dart_history_rectifier_v1/cloud'
    old=json.loads((prior/'input_private.json').read_text()); verify(old)
    assert json.loads((prior/'status.json').read_text())['state']=='completed_review_required'
    packet={k:v for k,v in old.items() if k not in ('run_id','source_sha256','audits')}
    ids=packet['task_ids']; y=np.array(packet['success']); folds=np.array(packet['folds'])
    expected_budget={(r['fold'],r['seed'],r['budget_fraction']):len(r['audit_indices']) for r in old['audits']}
    audits=[]
    source=ROOT/'results/dart_paired_judge_v1/audit_trace_private.jsonl'
    for line in source.read_text().splitlines():
        r=json.loads(line)
        if r['method']!='PairedGlobal':
            continue
        tr,te=np.flatnonzero(folds!=r['fold']),np.flatnonzero(folds==r['fold'])
        assert r['training_ids']==[ids[i] for i in tr] and r['test_ids']==[ids[i] for i in te]
        ix=r['audit_indices']
        assert len(ix)==len(set(ix))==r['total_audits']==expected_budget[r['fold'],r['seed'],r['budget_fraction']]
        assert min(ix)>=0 and max(ix)<len(tr)*len(packet['agents'])
        base=int(means(observed_gold(y[tr],ix)).argmax())
        assert [base]*len(te)==r['test_agent_choices']
        assert np.array_equal(y[te,base],np.array(packet['controls'][str(r['budget_fraction'])]['PairedGlobal'])[r['seed'],te])
        audits.append({k:r[k] for k in ('fold','seed','budget_fraction','audit_indices','test_agent_choices')})
    assert len(audits)==len({(r['fold'],r['seed'],r['budget_fraction']) for r in audits})==300
    packet['audits']=audits
    for b in ('0.05','0.1','0.2'):
        values=np.full((20,len(ids)),np.nan)
        for p in prior.glob('case_'+b+'_*.json'):
            r=json.loads(p.read_text()); te=np.array(r['test_indices'])
            values[r['seed'],te]=y[te,r['agent_choices']['CFJudgeFactor']]
        assert np.isfinite(values).all()
        packet['controls'][b]['UniformCFJudgeFactor']=values.tolist()
    packet['uniform_history_run_id']=old['run_id']
    packet['paired_trace_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
    paths=[ROOT/'infra/modal'/n for n in ('paired_history_core.py','paired_history_pipeline.py','paired_history_modal.py','history_core.py','gain_core.py','neural_core.py','neural_pipeline.py')]
    paths += [Path(__file__),ROOT/'run_dart_gain.py',ROOT/'docs/analysis/dart_paired_history_v1_protocol_2026-10-05.md']
    packet['source_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    packet['run_id']=digest(packet)[:24]
    OUTPUT.mkdir(parents=True,exist_ok=True); path=OUTPUT/'packet_private.json'
    if path.exists() and json.loads(path.read_text())!=packet:
        raise ValueError('Existing packet differs')
    atomic(path,packet)
    print(json.dumps({'run_id':packet['run_id'],'paired_cases_validated':300}))


if __name__=='__main__':
    transport.OUTPUT=OUTPUT; transport.APP='repguard-paired-history-v1'; transport.prepare=prepare
    transport.main()
