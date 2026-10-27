"""Real-judge historical rectifier; reuses detached submit/status/fetch transport."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import run_dart_gain as transport

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from repguard.audit.feedback import judge_feedback
from neural_pipeline import atomic,digest

OUTPUT=ROOT/'results/dart_history_rectifier_v1'


def prepare():
    gain=json.loads((ROOT/'results/dart_gain_v1/packet_private.json').read_text())
    packet={k:v for k,v in gain.items() if k not in ('embeddings','source_sha256','run_id')}
    ids,agents=packet['task_ids'],packet['agents']
    directory=ROOT/'results/dart_modal_judge_v1'
    _,metadata=judge_feedback(directory,ids,agents)
    scores=np.full((len(ids),len(agents)),np.nan); invalid=np.zeros_like(scores,dtype=bool)
    positions={(t,a):(i,j) for i,t in enumerate(ids) for j,a in enumerate(agents)}
    for line in (directory/'judgments_private.jsonl').read_text().splitlines():
        r=json.loads(line); i,j=positions[r['case']['task_id'],r['case']['agent']]
        scores[i,j]=r['success_probability'] if r['valid'] else .5
        invalid[i,j]=not r['valid']
    assert np.isfinite(scores).all()
    packet['judge_scores']=scores.tolist(); packet['judge_invalid']=invalid.tolist(); packet['judge_provenance']=metadata
    check=json.loads((ROOT/'results/dart_gain_v1/factor_independent_check_private.json').read_text())
    assert check['run_id']==gain['run_id'] and len(check['trace'])==300
    y=np.array(packet['success']); fold=np.array(packet['folds'])
    for b in ('0.05','0.1','0.2'):
        vals=np.full((20,len(ids)),np.nan)
        for a in packet['audits']:
            if str(a['budget_fraction'])!=b:
                continue
            key=f"r1_{b}_fold{a['fold']}_seed{a['seed']}"
            choice=check['trace'][key]['agent_choice']; te=np.flatnonzero(fold==a['fold'])
            vals[a['seed'],te]=y[te,choice]
        assert np.isfinite(vals).all()
        packet['controls'][b]['TunedFactorRidge']=vals.tolist()
    packet['gain_run_id']=gain['run_id']
    paths=[ROOT/'infra/modal'/n for n in ('history_core.py','history_pipeline.py','history_modal.py','gain_core.py','neural_core.py','neural_pipeline.py')]
    paths += [Path(__file__),ROOT/'run_dart_gain.py',ROOT/'src/repguard/audit/feedback.py',
              ROOT/'docs/analysis/dart_history_rectifier_v1_protocol_2026-10-05.md']
    packet['source_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    packet['run_id']=digest(packet)[:24]
    OUTPUT.mkdir(parents=True,exist_ok=True); target=OUTPUT/'packet_private.json'
    if target.exists() and json.loads(target.read_text())!=packet:
        raise ValueError('Prepared input differs; preserve existing experiment')
    atomic(target,packet)
    print(json.dumps({'run_id':packet['run_id'],'cases':300,'judge_records':metadata['records']}))


if __name__=='__main__':
    transport.OUTPUT=OUTPUT
    transport.APP='repguard-history-rectifier-v1'
    transport.prepare=prepare
    transport.main()
