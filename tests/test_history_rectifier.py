import sys
from pathlib import Path
import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'infra/modal'))
from history_core import rectify,cross_proxy,routes,design
from neural_core import means,observed_gold,inner_folds


def data():
    rng=np.random.default_rng(44)
    agents=['react_gpt4o','react_llama3','plan_gpt4o','plan_llama3']
    y=rng.integers(0,2,(36,4)).astype(float)
    p=rng.uniform(0,1,y.shape); invalid=np.zeros_like(y,dtype=bool)
    groups=[str(i//3) for i in range(36)]
    return rng,agents,y,p,invalid,groups


def test_null_proxy_exact_original_global_including_ties():
    rng,_,y,*_=data(); ids=rng.choice(y.size,50,replace=False)
    obs=observed_gold(y,ids)
    assert np.array_equal(rectify(obs,np.full(y.shape,.5)),means(obs))


def test_prediction_excludes_own_generator_gold():
    _,agents,y,p,invalid,groups=data()
    folds=inner_folds(groups); altered=y.copy(); altered[folds==0]=1-y[folds==0]
    a,trace=cross_proxy(y,p,invalid,agents,groups,True)
    b,_=cross_proxy(altered,p,invalid,agents,groups,True)
    assert np.array_equal(a[folds==0],b[folds==0])
    for row in trace:
        assert not (set(row['train_groups'])&set(row['prediction_groups']))


def test_hidden_gold_changes_cannot_change_any_decision():
    rng,agents,y,p,invalid,groups=data(); ids=rng.choice(y.size,65,replace=False)
    z=1-y; z.ravel()[ids]=y.ravel()[ids]
    a=routes(observed_gold(y,ids),p,invalid,agents,groups)
    b=routes(observed_gold(z,ids),p,invalid,agents,groups)
    assert a==b


def test_gold_only_predictor_does_not_consume_judge_information():
    _,agents,y,p,invalid,groups=data()
    a,_=cross_proxy(y,p,invalid,agents,groups,False)
    b,_=cross_proxy(y,1-p,~invalid,agents,groups,False)
    assert np.array_equal(a,b)
    x,penalty=design(agents,p,invalid,True)
    assert x.shape==(36,4,13) and len(penalty)==13
    assert np.array_equal(x[:,:,-4],p-.5)


def test_bad_or_empty_inputs_fail_closed():
    _,agents,y,p,invalid,groups=data()
    with pytest.raises(ValueError):
        cross_proxy(np.full(y.shape,np.nan),p,invalid,agents,groups,True)
    with pytest.raises(ValueError):
        design(agents,p+2,invalid,True)


@pytest.mark.parametrize('module_name',['history_pipeline','paired_history_pipeline'])
def test_history_pipeline_resume_and_excludes_test_feedback(tmp_path,monkeypatch,module_name):
    import importlib
    pipeline=importlib.import_module(module_name)
    METHODS=pipeline.METHODS
    monkeypatch.setattr(pipeline,'verify',lambda p:None)
    calls=[]
    def stub(observed,p,invalid,agents,groups):
        assert len(observed)==len(p)==len(invalid)==len(groups)==4
        calls.append(1)
        if len(calls)==2:
            raise RuntimeError('injected interruption')
        return {'agent_choices':{m:0 for m in METHODS}}
    monkeypatch.setattr(pipeline,'routes',stub)
    packet={'run_id':'test','groups':[str(i) for i in range(5)],'folds':list(range(5)),
            'agents':['a','b'],'success':[[1.,0.]]*5,'judge_scores':[[.5,.5]]*5,
            'judge_invalid':[[False,False]]*5}
    packet['audits']=[{'fold':f,'seed':s,'budget_fraction':b,'audit_indices':list(range(8)),
                       'test_agent_choices':[0]} for b in (.05,.1,.2) for f in range(5) for s in range(20)]
    packet['controls']={str(b):{m:[[1.]*5]*20 for m in ('UniformAuditGlobal','PairedGlobal','TunedFactorRidge','UniformCFJudgeFactor')} for b in (.05,.1,.2)}
    with pytest.raises(RuntimeError,match='injected'):
        pipeline.run(packet,tmp_path,lambda:None)
    assert len(list(tmp_path.glob('case_*.json')))==1
    result=pipeline.run(packet,tmp_path,lambda:None)
    assert result['state']=='completed_review_required' and result['completed']==300
    assert len(calls)==301
    pipeline.run(packet,tmp_path,lambda:None)
    assert len(calls)==301


def test_paired_wrapper_changes_only_control_name():
    from paired_history_core import routes as paired_routes
    _,agents,y,p,invalid,groups=data()
    a=routes(y,p,invalid,agents,groups)
    b=paired_routes(y,p,invalid,agents,groups)
    for field in ('agent_choices','scores'):
        a[field]['PairedGlobal']=a[field].pop('UniformAuditGlobal')
    assert a==b
