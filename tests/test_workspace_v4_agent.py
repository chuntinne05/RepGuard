import json
import sqlite3
from pathlib import Path

import pytest

from experiments.workspace_v4.agent import trajectory
from experiments.workspace_v4.tools import materialize,relation_fingerprint,sha


@pytest.fixture
def packet(tmp_path):
    context=tmp_path/'context';context.mkdir();(context/'data.csv').write_text('code,value\n000423,20\n')
    db=tmp_path/'derived.sqlite';materialize(context,db)
    task={'id':'t','question':'List code and value','pdf_views':{}}
    plan={'plan_id':'f'*24,'initial_call_cap':3,'review_call_cap':2,'initial_token_cap':10000,'review_token_cap':10000}
    return task,plan,context,db,tmp_path


def response(action):
    return {'response':{'message':{'content':json.dumps(action)},'prompt_eval_count':10,'eval_count':5,'total_duration':1_000_000}}


def normal(role,messages):
    if len(messages)==1:return response({'tool':'query','args':{'sql':'SELECT * FROM data'}})
    observation=json.loads(messages[-1]['content'])['observation']
    return response({'final_result_id':observation['result_id'],'explanation':'Source query output'})


def test_real_artifact_lineage_parent_is_reused_without_regenerating(packet):
    task,plan,context,db,tmp=packet;calls=[]
    def invoke(role,messages):calls.append(role);return normal(role,messages)
    parent=trajectory(plan,task,'A',context,db,tmp/'A',invoke,lambda:None)
    assert parent['state']=='finished' and parent['model_calls']==2
    def review(role,messages):
        q=json.loads(messages[0]['content'].split('TASK_JSON=',1)[1])
        prior=q['untrusted_earlier_work'];assert 'model_role' not in prior
        return response({'final_result_id':prior['final_action']['final_result_id'],'explanation':'Retain prior actual artifact'})
    reviewed=trajectory(plan,task,'AB',context,db,tmp/'AB',review,lambda:None,parent)
    assert reviewed['model_calls']==1 and len(calls)==2
    assert reviewed['prediction_sha256']==parent['prediction_sha256']
    assert reviewed['parent_trajectory_sha256']


def test_tool_errors_consume_new_steps_and_stop_at_cap(packet):
    task,plan,context,db,tmp=packet;calls=[]
    def invalid(role,messages):calls.append(role);return response({'tool':'bash','args':{}})
    r=trajectory(plan,task,'A',context,db,tmp/'A',invalid,lambda:None)
    assert len(calls)==3 and r['state']=='call_cap' and r['prediction_sha256'] is None
    assert len(set(r['request_ids']))==3


def test_unknown_transport_outcome_is_not_blindly_retried(packet):
    task,plan,context,db,tmp=packet;calls=[]
    def fail(role,messages):calls.append(role);raise TimeoutError('Unknown provider outcome')
    with pytest.raises(TimeoutError):trajectory(plan,task,'A',context,db,tmp/'A',fail,lambda:None)
    with pytest.raises(RuntimeError,match='no blind'):trajectory(plan,task,'A',context,db,tmp/'A',fail,lambda:None)
    assert len(calls)==1


def test_parent_artifact_tampering_stops_before_reviewer(packet):
    task,plan,context,db,tmp=packet
    parent=trajectory(plan,task,'A',context,db,tmp/'A',normal,lambda:None)
    path=Path(parent['artifact_directory'])/(parent['final_action']['final_result_id']+'.csv');path.write_text('changed')
    def forbidden(*args):raise AssertionError('Must not call provider')
    with pytest.raises(ValueError,match='Parent artifact changed'):
        trajectory(plan,task,'AA',context,db,tmp/'AA',forbidden,lambda:None,parent)


def test_sqlite_file_header_changes_do_not_change_logical_fingerprint(packet):
    _,_,_,db,_=packet;before=relation_fingerprint(db);raw=sha(db)
    c=sqlite3.connect(db);c.execute('PRAGMA user_version=42');c.close()
    assert sha(db)!=raw and relation_fingerprint(db)==before
