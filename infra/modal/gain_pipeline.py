"""Detached, finite R0/R1 run; primary endpoint frozen in the linked protocol."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from neural_core import observed_gold, cluster_ci
from neural_pipeline import atomic, digest, ensure_identity
from gain_core import FAMILIES, feature_bank, route_case, synthetic_smoke

TERMINAL = 'completed_review_required'


def verify(packet):
    if digest({k:v for k,v in packet.items() if k!='run_id'})[:24] != packet['run_id']:
        raise ValueError('Packet hash mismatch')
    for name in ('gain_core.py','gain_pipeline.py','neural_core.py','neural_pipeline.py'):
        actual = hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
        if actual != packet['source_sha256']['infra/modal/'+name]:
            raise ValueError('Source mismatch: '+name)


def analysis(rows,packet,controls=None):
    y = np.array(packet['success'])
    n = len(y); seeds = 1+max(r['seed'] for r in rows)
    outcomes = {m:np.full((seeds,n),np.nan) for m in (*FAMILIES,'Selected')}
    actions = {m:np.full((seeds,n),-1,dtype=int) for m in outcomes}
    for r in rows:
        ix = np.array(r['test_indices'])
        for m,a in r['actions'].items():
            if (actions[m][r['seed'],ix]>=0).any():
                raise ValueError('Duplicate evaluation task')
            actions[m][r['seed'],ix] = a
            outcomes[m][r['seed'],ix] = y[ix,a]
    if any(not np.isfinite(v).all() for v in outcomes.values()):
        raise ValueError('Incomplete out-of-fold evaluation')
    if controls:
        for m,v in controls.items():
            outcomes[m] = np.array(v)
        if not np.array_equal(outcomes['Global'],outcomes['UniformAuditGlobal']):
            raise ValueError('Saved control reproduction mismatch')
    refs = ('UniformAuditGlobal','PairedGlobal') if controls else ('Global',)
    contrasts = {}
    for m in actions:
        contrasts[m] = {}
        for ref in refs:
            delta = (outcomes[m]-outcomes[ref]).mean(0)
            contrasts[m][ref] = {'difference':float(delta.mean()),
                'ci95':cluster_ci(delta,packet['groups']),
                'rescues':float(((outcomes[m]==1)&(outcomes[ref]==0)).sum(1).mean()),
                'harms':float(((outcomes[m]==0)&(outcomes[ref]==1)).sum(1).mean())}
    return {'methods':{m:{'mean_correct':float(v.sum(1).mean()),'accuracy':float(v.mean())} for m,v in outcomes.items()},
        'contrasts':contrasts,'switches_from_global':{m:float((a!=actions['Global']).sum(1).mean()) for m,a in actions.items()},
        'primary_signal_pass':all(contrasts['Selected'][r]['ci95'][0]>0 for r in refs),
        'scope':'adaptive public-normal development, not independent confirmation'}


def validate_case(row,run_id,key):
    if row['run_id']!=run_id or row['case']!=key:
        raise ValueError('Case identity mismatch')
    expected = digest({k:v for k,v in row.items() if k!='artifact_sha256'})
    if row['artifact_sha256']!=expected:
        raise ValueError('Case checksum mismatch')


def run(packet,root,commit):
    verify(packet)
    root = Path(root); root.mkdir(parents=True,exist_ok=True)
    ensure_identity(root,packet)
    status_path = root/'status.json'
    if status_path.exists() and json.loads(status_path.read_text())['state']==TERMINAL:
        return json.loads(status_path.read_text())
    ledger = {}
    for p in root.glob('case_*.json'):
        r = json.loads(p.read_text()); validate_case(r,packet['run_id'],p.stem[5:])
        ledger[r['case']] = r['artifact_sha256']
    def status(state,**kw):
        atomic(status_path,{'run_id':packet['run_id'],'state':state,'completed':len(ledger),'total':305,
                           'updated_at':datetime.now(timezone.utc).isoformat(),**kw})
        commit(); print(status_path.read_text(),flush=True)
    try:
        import importlib.metadata
        atomic(root/'environment.json',{d.metadata['Name']:d.version for d in importlib.metadata.distributions()})
        status('self_test')
        atomic(root/'self_test.json',synthetic_smoke()); commit()
        x = np.array(packet['embeddings']); y = np.array(packet['success'],dtype=float)
        f = np.array(packet['folds']); banks = {}
        def case(stage,fold,seed=0,audit=None):
            key = f'{stage}_fold{fold}_seed{seed}'
            path = root/('case_'+key+'.json')
            if path.exists():
                row = json.loads(path.read_text()); validate_case(row,packet['run_id'],key)
                return row
            train,test = np.flatnonzero(f!=fold),np.flatnonzero(f==fold)
            if fold not in banks:
                status('features',stage=stage,case=key)
                banks[fold] = feature_bank(x,packet['texts'],packet['groups'],train,test)
            obs = y[train].copy() if audit is None else observed_gold(y[train],audit['audit_indices'])
            result = route_case(banks[fold],obs,packet['agents'],lambda detail:status('training',stage=stage,case=key,detail=detail))
            if audit is not None and result['actions']['Global']!=audit['test_agent_choices']:
                raise ValueError('Exact audit-control choices differ')
            row = {'case':key,'run_id':packet['run_id'],'fold':fold,'seed':seed,
                   'test_indices':test.tolist(),'audit_count':int(np.isfinite(obs).sum()),**result}
            row['artifact_sha256'] = digest(row)
            atomic(path,row); ledger[key] = row['artifact_sha256']
            atomic(root/'ledger.json',ledger)
            status('case_completed',stage=stage,case=key)
            return row
        r0 = [case('r0',fold) for fold in range(5)]
        atomic(root/'r0_analysis.json',analysis(r0,packet)); commit()
        summaries = {}
        for budget in ('0.05','0.1','0.2'):
            audits = sorted([r for r in packet['audits'] if str(r['budget_fraction'])==budget],key=lambda r:(r['fold'],r['seed']))
            if len(audits)!=100:
                raise ValueError('Missing audits')
            records = [case('r1_'+budget,r['fold'],r['seed'],r) for r in audits]
            summaries[budget] = analysis(records,packet,packet['controls'][budget])
            atomic(root/('r1_'+budget+'_analysis.json'),summaries[budget]); commit()
        atomic(root/'r1_analysis.json',summaries)
        status(TERMINAL,primary_signal_pass=summaries['0.1']['primary_signal_pass'],primary=summaries['0.1']['methods'])
        return json.loads(status_path.read_text())
    except Exception as e:
        status('pipeline_failed',error=repr(e)); raise
