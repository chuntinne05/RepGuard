"""Paired acquisition version; estimator math is imported unchanged."""
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from neural_core import observed_gold,cluster_ci
from neural_pipeline import atomic,digest,ensure_identity
from paired_history_core import routes,METHODS


def verify(packet):
    if digest({k:v for k,v in packet.items() if k!='run_id'})[:24]!=packet['run_id']:
        raise ValueError('Input identity mismatch')
    for name in ('paired_history_core.py','paired_history_pipeline.py','history_core.py','gain_core.py','neural_core.py','neural_pipeline.py'):
        if hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()!=packet['source_sha256']['infra/modal/'+name]:
            raise ValueError('Source mismatch '+name)


def validate(row):
    if digest({k:v for k,v in row.items() if k!='artifact_sha256'})!=row['artifact_sha256']:
        raise ValueError('Checkpoint checksum mismatch')


def summarize(rows,packet,budget):
    y=np.array(packet['success']); vals={m:np.full((20,len(y)),np.nan) for m in METHODS}
    for r in rows:
        ix=np.array(r['test_indices'])
        for m,a in r['agent_choices'].items():
            if np.isfinite(vals[m][r['seed'],ix]).any():
                raise ValueError('Duplicate evaluation')
            vals[m][r['seed'],ix]=y[ix,a]
    if any(not np.isfinite(v).all() for v in vals.values()):
        raise ValueError('Incomplete evaluation')
    controls=packet['controls'][budget]
    if not np.array_equal(vals['PairedGlobal'],controls['PairedGlobal']):
        raise ValueError('Control mismatch')
    vals['UniformAuditGlobal']=np.array(controls['UniformAuditGlobal'])
    vals['TunedFactorRidge']=np.array(controls['TunedFactorRidge'])
    vals['UniformCFJudgeFactor']=np.array(controls['UniformCFJudgeFactor'])
    refs=('PairedGlobal','UniformAuditGlobal','CFGoldFactor','TunedFactorRidge','UniformCFJudgeFactor')
    contrasts={}
    for m in METHODS:
        contrasts[m]={}
        for ref in refs:
            delta=(vals[m]-vals[ref]).mean(0)
            contrasts[m][ref]={'difference':float(delta.mean()),'ci95':cluster_ci(delta,packet['groups']),
                'rescues':float(((vals[m]==1)&(vals[ref]==0)).sum(1).mean()),
                'harms':float(((vals[m]==0)&(vals[ref]==1)).sum(1).mean())}
    return {'methods':{m:{'mean_correct':float(v.sum(1).mean()),'accuracy':float(v.mean())} for m,v in vals.items()},
            'contrasts':contrasts,'primary_signal_pass':all(contrasts['CFJudgeFactor'][ref]['ci95'][0]>0 for ref in refs[:2]),
            'scope':'adaptive public-normal exploration, no independent confirmation'}


def run(packet,root,commit):
    verify(packet); root=Path(root); root.mkdir(parents=True,exist_ok=True)
    ensure_identity(root,packet)
    sp=root/'status.json'
    if sp.exists() and json.loads(sp.read_text())['state']=='completed_review_required':
        return json.loads(sp.read_text())
    ledger={}
    for p in root.glob('case_*.json'):
        r=json.loads(p.read_text()); validate(r)
        if r['run_id']!=packet['run_id']:
            raise ValueError('Mixed run checkpoint')
        ledger[r['case']]=r['artifact_sha256']
    def status(state,**fields):
        atomic(sp,{'run_id':packet['run_id'],'state':state,'completed':len(ledger),'total':300,
                   'updated_at':datetime.now(timezone.utc).isoformat(),**fields})
        commit(); print(sp.read_text(),flush=True)
    try:
        import platform
        atomic(root/'environment.json',{'python':platform.python_version(),'numpy':np.__version__})
        y=np.array(packet['success']); fold=np.array(packet['folds'])
        p=np.array(packet['judge_scores']); invalid=np.array(packet['judge_invalid'],dtype=bool)
        analyses={}
        for b in ('0.05','0.1','0.2'):
            rows=[]
            for a in sorted([r for r in packet['audits'] if str(r['budget_fraction'])==b],key=lambda r:(r['fold'],r['seed'])):
                key=f"{b}_fold{a['fold']}_seed{a['seed']}"; path=root/('case_'+key+'.json')
                if path.exists():
                    r=json.loads(path.read_text()); validate(r)
                    if r['case']!=key or r['run_id']!=packet['run_id']:
                        raise ValueError('Checkpoint identity mismatch')
                else:
                    tr,te=np.flatnonzero(fold!=a['fold']),np.flatnonzero(fold==a['fold'])
                    obs=observed_gold(y[tr],a['audit_indices'])
                    result=routes(obs,p[tr],invalid[tr],packet['agents'],[packet['groups'][i] for i in tr])
                    if [result['agent_choices']['PairedGlobal']]*len(te)!=a['test_agent_choices']:
                        raise ValueError('Saved audit action mismatch')
                    r={'case':key,'run_id':packet['run_id'],'seed':a['seed'],'fold':a['fold'],
                       'test_indices':te.tolist(),'audit_count':len(a['audit_indices']),**result}
                    r['artifact_sha256']=digest(r); atomic(path,r); ledger[key]=r['artifact_sha256']
                    atomic(root/'ledger.json',ledger); status('case_completed',budget=b,case=key)
                rows.append(r)
            analyses[b]=summarize(rows,packet,b); atomic(root/('analysis_'+b+'.json'),analyses[b]); commit()
        atomic(root/'analysis.json',analyses)
        status('completed_review_required',primary_signal_pass=analyses['0.1']['primary_signal_pass'],primary=analyses['0.1']['methods'])
        return json.loads(sp.read_text())
    except Exception as e:
        status('pipeline_failed',error=repr(e)); raise
