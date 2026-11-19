import json

from experiments.arqa_v2.oracle import source_table
from research_ops.source_receipt import inspect


def packet():
    case={"question":"Revenue growth in2020 vs2019?","table":source_table({
        "table_id":"t","doc_id":"d","year":2020,"page":1,"title":"Revenue and profit",
        "merged_headers":["EUR million","2020","2019"],"rows":[["Revenue","120","100"],["Profit","12","10"]]})}
    answer={"answer_value":20,"unit":"%","program":[
        {"op":"read","cell_id":"r0c1","as":"new"},{"op":"read","cell_id":"r0c2","as":"old"},
        {"op":"sub","inputs":["new","old"],"as":"diff"},{"op":"div","inputs":["diff","old"],"as":"ratio"},
        {"op":"mul","inputs":["ratio",100],"as":"pct"}],
        "claim_slots":{"entity":"Group","metric":"Revenue","period":"2020 vs2019","operation":"pct_change"},"explanation":"growth"}
    return case,answer


def test_read_then_constant_only_tail_is_not_source_bound():
    case,a=packet()
    a['program']=[a['program'][0],{"op":"add","inputs":[1,1],"as":"constant"}]
    a['answer_value']=2
    r=inspect(case,json.dumps(a))
    assert r['parsed']['source_bound']  # Frozen v2 parser's weaker field stays unchanged.
    assert not r['source_and_arithmetic_pass']
    assert 'final_result_has_no_source_dependency' in r['dataflow']['warnings']


def test_passing_receipt_never_approves_semantics():
    case,a=packet();r=inspect(case,json.dumps(a))
    assert r['source_and_arithmetic_pass']
    assert r['status']=='needs_semantic_review' and not r['semantic_verified']


def test_wrong_metric_can_pass_mechanics_and_still_requires_review():
    case,a=packet()
    a['program'][0]['cell_id']='r1c1';a['program'][1]['cell_id']='r1c2'
    r=inspect(case,json.dumps(a))
    assert r['source_and_arithmetic_pass'] and not r['semantic_verified']
    assert all(c['row']=='Profit' for c in r['final_source_cells'])


def test_extra_read_marked_unused():
    case,a=packet()
    a['program'].insert(0,{"op":"read","cell_id":"r1c1","as":"unused"})
    r=inspect(case,json.dumps(a))
    assert r['source_and_arithmetic_pass'] and r['dataflow']['unused_read_ids']==['r1c1']


def test_bad_json_does_not_pass():
    case,_=packet();r=inspect(case,'not JSON')
    assert not r['source_and_arithmetic_pass']
