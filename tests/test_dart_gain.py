from pathlib import Path
import sys
import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'infra/modal'))
from gain_core import (text_features,center_features,factor_design,factor_scores,
                       ridge_predict,corrected_utility,FAMILIES)
from neural_core import observed_gold,means
from neural_pipeline import digest
from gain_pipeline import validate_case


def test_unpaid_label_injection_does_not_change_fits():
    rng=np.random.default_rng(34); y=rng.integers(0,2,(30,4)); ids=rng.choice(y.size,60,replace=False)
    altered=1-y; altered.ravel()[ids]=y.ravel()[ids]
    a,b=observed_gold(y,ids),observed_gold(altered,ids)
    x,t=center_features(rng.normal(size=(30,8)),rng.normal(size=(9,8)))
    agents=['react_gpt4o','react_llama3','plan_gpt4o','plan_llama3']
    assert np.array_equal(ridge_predict(x,a,t,1),ridge_predict(x,b,t,1))
    assert np.array_equal(factor_scores(a,agents,4),factor_scores(b,agents,4))
    assert np.array_equal(corrected_utility(a)[0],corrected_utility(b)[0])


def test_vocabulary_and_center_exclude_test_inputs():
    train=['read email','send email','read documents']
    a,_,v=text_features(train,['secret holdoutword'])
    b,_,w=text_features(train,['different futuredata'])
    assert 'holdoutword' not in v and v==w and np.array_equal(a,b)
    c,_=center_features(a,np.ones((1,a.shape[1])))
    d,_=center_features(a,np.zeros((1,a.shape[1])))
    assert np.array_equal(c,d)


def test_anchor_subtraction_is_not_a_new_ridge_ranker():
    rng=np.random.default_rng(3); x=rng.normal(size=(25,6)); xt=rng.normal(size=(8,6))
    y=rng.integers(0,2,(25,4)).astype(float); base=means(y); anchor=2
    predicted=ridge_predict(x,y,xt,1)
    delta=y-y[:,anchor,None]; prior=base-base[anchor]
    coef=np.linalg.solve(x@x.T+np.eye(25),delta-prior)
    gain=prior+(xt@x.T)@coef
    assert np.allclose(predicted-predicted[:,anchor,None],gain,atol=1e-12)
    assert np.array_equal(predicted.argmax(1),gain.argmax(1))


def test_signed_utility_preserves_policy_gradient_and_full_gold():
    y=np.array([[1.,0.,1.],[0.,1.,0.]])
    utility,_=corrected_utility(y)
    assert np.array_equal(utility,y)
    p=np.array([[.2,.3,.5],[.1,.7,.2]])
    shifted=utility-utility[:,1,None]
    gradient=p*(utility-(p*utility).sum(1,keepdims=True))
    shifted_gradient=p*(shifted-(p*shifted).sum(1,keepdims=True))
    assert np.allclose(gradient,shifted_gradient)
    with pytest.raises(ValueError):
        corrected_utility(np.full((3,2),np.nan))


def test_factor_metadata_and_missing_agent():
    agents=['react_gpt4o','react_llama3','plan_gpt4o','plan_llama3']
    x=factor_design(agents)
    assert x.shape==(4,9)
    assert np.all(x.sum(1)==4)
    obs=np.array([[1,np.nan,1,0],[1,np.nan,0,0]],float)
    pred=factor_scores(obs,agents,4)
    assert np.isfinite(pred).all()
    assert pred[0]>pred[3]


def test_checkpoint_tampering_rejected():
    row={'run_id':'r','case':'c','actions':{'Global':[1]}}
    row['artifact_sha256']=digest(row)
    validate_case(row,'r','c')
    row['actions']['Global'][0]=0
    with pytest.raises(ValueError,match='checksum'):
        validate_case(row,'r','c')


def test_full_cloud_state_machine_resumes_and_finishes_fixed_batch(tmp_path,monkeypatch):
    import gain_pipeline as pipeline
    monkeypatch.setattr(pipeline,'verify',lambda p:None)
    monkeypatch.setattr(pipeline,'synthetic_smoke',lambda:{'stub':True})
    monkeypatch.setattr(pipeline,'feature_bank',lambda *args:{})
    calls=[]
    def route(*args):
        calls.append(1)
        if len(calls)==2:
            raise RuntimeError('injected crash')
        return {'actions':{h:[0] for h in (*FAMILIES,'Selected')},'trace':{},'scores':{}}
    monkeypatch.setattr(pipeline,'route_case',route)
    packet={'run_id':'test','texts':['x']*5,'groups':[str(i) for i in range(5)],
            'folds':list(range(5)),'agents':['a','b'],'success':[[1.,0.]]*5,'embeddings':[[0.]]*5}
    packet['audits']=[{'fold':f,'seed':s,'budget_fraction':b,'audit_indices':list(range(8)),
                       'test_agent_choices':[0]} for b in (.05,.1,.2) for f in range(5) for s in range(20)]
    packet['controls']={str(b):{m:[[1.]*5]*20 for m in ('UniformAuditGlobal','PairedGlobal')} for b in (.05,.1,.2)}
    with pytest.raises(RuntimeError,match='injected'):
        pipeline.run(packet,tmp_path,lambda:None)
    assert len(list(tmp_path.glob('case_*.json')))==1
    result=pipeline.run(packet,tmp_path,lambda:None)
    assert result['state']=='completed_review_required'
    assert result['completed']==305
    assert len(calls)==306
    pipeline.run(packet,tmp_path,lambda:None)
    assert len(calls)==306
