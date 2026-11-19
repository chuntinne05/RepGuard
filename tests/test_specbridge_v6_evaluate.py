import copy

import pytest

from experiments.specbridge_v6.runtime import MODELS, digest
from research_ops.specbridge_v6_evaluate import audit_response, policy_cost, rows_reproduced


def receipt():
    plan={'plan_id':'a'*24};case={'case_id':'t__A'};rid=digest([plan['plan_id'],case['case_id'],'A'])[:28]
    messages=[{'role':'user','content':'public source only'}]
    attempt={'request_id':rid,'plan_id':plan['plan_id'],'case_id':case['case_id'],'workflow':'A','messages_sha256':digest(messages)}
    response={'request_id':rid,'messages':messages,'messages_sha256':digest(messages),'model':MODELS['A']['name'],
              'model_digest':MODELS['A']['digest'],'ollama_version':'0.40.6','provider':'ollama_modal','live_inference':True,
              'evaluation_volume_mounted':False,'weights_read_only':True,'gpu':'NVIDIA L40S',
              'request_body':{'model':MODELS['A']['name'],'messages':copy.deepcopy(messages),'think':False,'stream':False,'format':'json',
                              'options':{'temperature':0,'seed':20261109,'num_ctx':32768,'num_predict':8192}},
              'response':{'model':MODELS['A']['name'],'done':True,'prompt_eval_count':100,'eval_count':20,'total_duration':1000}}
    return response,attempt,plan,case


def test_actual_provider_prompt_must_match_logged_prompt():
    r,a,p,c=receipt();audit_response(r,a,p,c,'A')
    r['request_body']['messages'][0]['content']='different input'
    with pytest.raises(ValueError,match='Provider payload'):
        audit_response(r,a,p,c,'A')


@pytest.mark.parametrize('field,value', [('model_digest','wrong'),('evaluation_volume_mounted',True),('gpu','CPU')])
def test_model_and_isolation_tampering_rejected(field,value):
    r,a,p,c=receipt();r[field]=value
    with pytest.raises(ValueError):audit_response(r,a,p,c,'A')


def test_numeric_replay_noise_not_wrong_content_or_integer_changes():
    assert rows_reproduced([[1.0,'x',None]],[[1.0+1e-14,'x',None]])
    assert not rows_reproduced([[1.0,'x',None]],[[1.1,'x',None]])
    assert not rows_reproduced([[1,'x']],[[1,'y']])
    assert not rows_reproduced([[100000000000000]],[[100000000000001]])
    assert not rows_reproduced([[1,2]],[[1]])


def test_cached_draft_cost_counts_in_every_review_policy():
    draft={'model_calls':1,'input_tokens':100,'output_tokens':10,'serving_seconds':5}
    review={'model_calls':1,'input_tokens':150,'output_tokens':20,'serving_seconds':6}
    assert policy_cost(review,draft)=={'model_calls':2,'input_tokens':250,'output_tokens':30,'serving_seconds':11}
