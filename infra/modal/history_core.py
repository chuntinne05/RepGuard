"""Cross-fitted historical feedback calibration and regularized rectification."""
import numpy as np
from gain_core import factor_design,factor_scores
from neural_core import means,inner_folds

METHODS=('UniformAuditGlobal','CFGoldFactor','CFJudgeFactor','RawJudgeRectifier','JudgeImpute','FixedFactorRidge')


def design(agents,p,invalid,use_judge):
    if p.shape!=invalid.shape or p.shape[1]!=len(agents) or not np.isfinite(p).all() or not ((p>=0)&(p<=1)).all():
        raise ValueError('Invalid auxiliary score matrix')
    base=factor_design(agents)
    x=np.tile(base[None,:,:],(len(p),1,1))
    penalty=np.ones(base.shape[1]); penalty[0]=0; penalty[-len(agents):]=4
    if use_judge:
        extras=np.stack([p-.5,(p>=.9).astype(float)-.5,
                         np.broadcast_to(p.mean(1,keepdims=True)-.5,p.shape),invalid.astype(float)],axis=2)
        x=np.concatenate([x,extras],axis=2)
        penalty=np.concatenate([penalty,np.ones(4)])
    return x,penalty


def cross_proxy(observed,p,invalid,agents,groups,use_judge):
    x,penalty=design(agents,p,invalid,use_judge)
    fold=inner_folds(groups)
    result=np.full(observed.shape,np.nan); trace=[]
    for f in range(3):
        train,test=fold!=f,fold==f
        mask=np.isfinite(observed)&train[:,None]
        if not mask.any():
            raise ValueError('Empty calibration partition')
        z=x[mask]
        beta=np.linalg.solve(z.T@z+np.diag(penalty),z.T@(observed[mask]-.5))
        result[test]=np.clip(.5+x[test]@beta,0,1)
        trace.append({'fold':f,'train_groups':sorted(set(np.array(groups)[train])),
                      'prediction_groups':sorted(set(np.array(groups)[test])),
                      'training_labels':int(mask.sum())})
    if not np.isfinite(result).all():
        raise ValueError('Incomplete cross predictions')
    return result,trace


def rectify(observed,proxy):
    if observed.shape!=proxy.shape or not np.isfinite(proxy).all():
        raise ValueError('Invalid prediction shape or value')
    if np.equal(proxy,.5).all():
        return means(observed)  # exact arithmetic, including ties, for the null proxy
    mask=np.isfinite(observed)
    return proxy.mean(0)+np.where(mask,np.nan_to_num(observed)-proxy,0).sum(0)/(mask.sum(0)+2)


def choose(scores):
    return int(np.flatnonzero(np.isclose(scores,scores.max(),atol=1e-12,rtol=0))[0])


def routes(observed,p,invalid,agents,groups):
    if np.isinf(observed).any() or not np.isin(observed[np.isfinite(observed)],[0,1]).all():
        raise ValueError('Invalid gold labels')
    gold,trace=cross_proxy(observed,p,invalid,agents,groups,False)
    judge,trace_j=cross_proxy(observed,p,invalid,agents,groups,True)
    scores={'UniformAuditGlobal':means(observed),'CFGoldFactor':rectify(observed,gold),
            'CFJudgeFactor':rectify(observed,judge),'RawJudgeRectifier':rectify(observed,p),
            'JudgeImpute':judge.mean(0),'FixedFactorRidge':factor_scores(observed,agents,4)}
    selected={m:choose(v) for m,v in scores.items()}
    selected['UniformAuditGlobal']=int(means(observed).argmax())
    mask=np.isfinite(observed)
    return {'agent_choices':selected,'scores':{m:v.tolist() for m,v in scores.items()},
        'gold_proxy':gold.tolist(),'judge_proxy':judge.tolist(),'crossfit_trace':trace_j,
        'diagnostics':{'gold_proxy_audited_brier':float(np.mean((gold[mask]-observed[mask])**2)),
                       'judge_proxy_audited_brier':float(np.mean((judge[mask]-observed[mask])**2)),
                       'agent_audit_counts':mask.sum(0).tolist()}}
