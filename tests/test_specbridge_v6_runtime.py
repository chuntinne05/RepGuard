import json
from pathlib import Path

import pytest

from experiments.specbridge_v6.runtime import digest, parse_candidate, run_one


def provider(sql):
    return {'response':{'message':{'content':json.dumps({'sql':sql})},'prompt_eval_count':20,'eval_count':10,'total_duration':1_000_000}}


def test_non_sql_objects_and_multiple_candidates_are_not_silently_repaired():
    for text in ('```sql\nSELECT1\n```','{"sql":"SELECT1","alternatives":[]}', '{"sql":3}'):
        assert parse_candidate(text)[0] is None


def test_actual_parent_and_execution_preview_shared_without_labels(tmp_path, monkeypatch):
    import experiments.specbridge_v6.runtime as runtime
    monkeypatch.setattr(runtime, 'execute', lambda db, sql:{'state':'ok','rows':[[7]],'columns':['value']})
    plan={'plan_id':'a'*24};case={'case_id':'t__A','task_id':'t','reading':'A','database':'data','question':'Specified interpretation','context':{'schema':'source'}}
    initial=run_one(plan,case,'A',tmp_path,tmp_path/'A',lambda role,msg:provider('SELECT7'),lambda:None)
    def review(role,messages):
        packet=json.loads(messages[0]['content'].split('TASK_JSON=',1)[1])
        assert set(packet['earlier_work'])=={'raw_response','sql','execution'}
        assert packet['earlier_work']['execution']['rows_preview']==[[7]]
        assert 'grade' not in json.dumps(packet)
        return provider('SELECT8')
    result=run_one(plan,case,'AB',tmp_path,tmp_path/'AB',review,lambda:None,initial)
    assert result['parent_sha256']==digest(initial) and result['model_calls']==1


def test_unresolved_attempt_never_regenerated(tmp_path):
    calls=[];plan={'plan_id':'a'*24};case={'case_id':'t__A','task_id':'t','reading':'A','database':'data','question':'q','context':{}}
    def fail(*args):calls.append(1);raise TimeoutError('unknown outcome')
    with pytest.raises(TimeoutError):run_one(plan,case,'A',tmp_path,tmp_path/'A',fail,lambda:None)
    with pytest.raises(RuntimeError,match='Already started'):run_one(plan,case,'A',tmp_path,tmp_path/'A',fail,lambda:None)
    assert len(calls)==1


def test_invalid_model_json_is_recorded_without_an_extra_call(tmp_path):
    plan={'plan_id':'a'*24};case={'case_id':'t__A','task_id':'t','reading':'A','database':'data','question':'q','context':{}}
    def invalid(*args):
        p=provider('SELECT1');p['response']['message']['content']='notJSON';return p
    result=run_one(plan,case,'A',tmp_path,tmp_path/'A',invalid,lambda:None)
    assert result['parse_state']=='invalid_json' and result['execution']['rows'] is None
    assert (tmp_path/'A/response.json').exists()
