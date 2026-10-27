"""Fast independent recomputation of the predeclared structured baseline only.

This does not select a new primary method or replace the cloud's complete batch.
Only Global/FactorRidge are computed; no fabricated results for unrun families.
"""
import json
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'infra/modal'))
from gain_core import factor_scores
from neural_core import observed_gold,inner_folds,ht_score,cluster_ci
from neural_pipeline import atomic


def main():
    out=ROOT/'results/dart_gain_v1'
    p=json.loads((out/'packet_private.json').read_text())
    y=np.array(p['success']); folds=np.array(p['folds'])
    results={}; trace={}
    for budget in (.05,.1,.2):
        values=np.full((20,len(y)),np.nan)
        for r in p['audits']:
            if r['budget_fraction']!=budget:
                continue
            tr,te=np.flatnonzero(folds!=r['fold']),np.flatnonzero(folds==r['fold'])
            observed=observed_gold(y[tr],r['audit_indices'])
            inner=inner_folds([p['groups'][i] for i in tr])
            scores={4.:0.,16.:0.}
            for f in range(3):
                a,b=inner!=f,inner==f
                for reg in scores:
                    choice=int(factor_scores(observed[a],p['agents'],reg).argmax())
                    scores[reg]+=ht_score(observed[b],np.full(b.sum(),choice,dtype=int))
            reg=max(scores,key=scores.get)
            choice=int(factor_scores(observed,p['agents'],reg).argmax())
            values[r['seed'],te]=y[te,choice]
            key=f"r1_{budget}_fold{r['fold']}_seed{r['seed']}"
            trace[key]={'agent_choice':choice,'regularization':reg}
        assert np.isfinite(values).all()
        contrasts={}
        for control,vs in p['controls'][str(budget)].items():
            v=np.array(vs); delta=(values-v).mean(0)
            contrasts[control]={'difference':float(delta.mean()),'ci95':cluster_ci(delta,p['groups'])}
        results[str(budget)]={'FactorRidge_mean_correct':float(values.sum(1).mean()),'contrasts':contrasts}
    atomic(out/'factor_independent_check_private.json',{'run_id':p['run_id'],'cases':300,'results':results,'trace':trace,
        'scope':'predeclared FactorRidge only; cloud primary Selected remains pending'})
    print(json.dumps({'cases':300,'results':results,'scope':'preliminary single-family recomputation, not the primary endpoint'},indent=2))


if __name__=='__main__':
    main()
