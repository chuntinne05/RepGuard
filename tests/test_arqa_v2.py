import json
from decimal import Decimal
from pathlib import Path

import pytest

from experiments.arqa_v2.oracle import bind, close, execute, number, source_table
from experiments.arqa_v2.study import parse, prompt, collect, rid, unit
from experiments.arqa_v2.preflight import digest, write


@pytest.fixture
def table():
    return source_table({"table_id": "t", "doc_id": "d", "year": 2020, "page": 1, "title": "Revenue",
                         "merged_headers": ["EUR million", "REVENUE 2020", "2019", "PROFIT 2020", "2019"],
                         "rows": [["Group", "120", "100", "12", "10"]]})


def answer(**changes):
    x = {"answer_value": 20, "unit": "%", "program": [
        {"op": "read", "cell_id": "r0c1", "as": "a"}, {"op": "read", "cell_id": "r0c2", "as": "b"},
        {"op": "sub", "inputs": ["a", "b"], "as": "d"}, {"op": "div", "inputs": ["d", "b"], "as": "q"},
        {"op": "mul", "inputs": ["q", 100], "as": "pct"}],
        "claim_slots": {"entity": "Group", "metric": "Revenue", "period": "2020 vs 2019", "operation": "pct_change"}, "explanation": "growth"}
    x.update(changes); return x


def test_recomputes_from_source_and_ignores_claimed_results(table):
    x=answer();x["program"][-1]["result"]=999
    assert execute(x["program"],table)[0] == 20
    assert parse(json.dumps(x),table)["internally_consistent"]


def test_forged_source_value_rejected(table):
    x=answer();x["program"][0]["value"]=999
    p=parse(json.dumps(x),table)
    assert p["valid"] and not p["source_bound"]


def test_column_year_binding(table):
    assert bind({"table_id":"t","row":"Group","col":"REVENUE 2019"},table)["id"]=="r0c2"
    with pytest.raises(ValueError): bind({"table_id":"t","row":"Group","col":"2019"},table)
    assert bind({"table_id":"t","row":"Group","col":"2019","value":10},table)["id"]=="r0c4"


def test_bad_table_unknown_id_and_arbitrary_literal(table):
    with pytest.raises(ValueError): bind({"table_id":"other","row":"Group","col":"REVENUE 2020"},table)
    for change in ({"op":"read","cell_id":"missing","as":"a"}, {"op":"mul","inputs":[120,100],"as":"a"}):
        with pytest.raises(ValueError): execute([change],table)


def test_no_source_no_execution_and_unsafe_values(table):
    for v in (True, "NaN", "Infinity", "__import__('os').system('x')"):
        with pytest.raises(ValueError): number(v)
    with pytest.raises(ValueError): execute([{"op":"exec","as":"x","code":"anything"}],table)


def test_forward_ref_duplicate_and_zero_division(table):
    base=[{"op":"read","cell_id":"r0c1","as":"a"}]
    for step in ({"op":"add","inputs":["missing",1],"as":"b"}, {"op":"abs","inputs":["a"],"as":"a"},
                 {"op":"div","inputs":["a",0],"as":"b"}):
        with pytest.raises(ValueError): execute(base+[step],table)


def test_syntactically_bound_wrong_metric_not_certified(table):
    x=answer();x["program"][0]["cell_id"]="r0c3";x["program"][1]["cell_id"]="r0c4"
    # Profit happens to grow20% too. Arithmetic cannot prove requested metric.
    parsed=parse(json.dumps(x),table)
    assert parsed["source_bound"] and parsed["internally_consistent"]
    assert "semantic_verified" not in parsed


def test_schema_abstention_and_precision(table):
    assert parse(json.dumps(answer(answer_value=None,program=[])),table)["abstained"]
    assert not parse(json.dumps(answer(extra="gold")),table)["valid"]
    assert not close(121,120)
    assert close("0.33",str(Decimal(1)/3))
    assert unit("percent")=="%" and unit("pp")=="ppt" and unit("%")!=unit("ppt")


def test_gold_and_identity_whitelists(table):
    case={"question":"Growth?","table":table}
    with pytest.raises(ValueError): prompt({**case,"answer_value":20},"standard")
    with pytest.raises(ValueError): prompt(case,"standard",{"raw_text":"x","model":"A"})
    assert "EARLIER_DRAFT_JSON_STRING" in prompt(case,"checklist",{"raw_text":"a"})


def test_bounded_collector_parents_no_regeneration(tmp_path,table):
    public={"items":[{"id":"i","group":"g","case":{"question":"Growth?","table":table}}]}
    plan={"public_sha256":digest(public),"items":1,"max_calls":12,"plan_id":"f"*24}
    calls=[]
    def invoke(role,text):
        calls.append((role,text));return {"response":{"message":{"content":json.dumps(answer())}}}
    out=collect(plan,public,tmp_path,invoke)
    assert out["completed"]==12 and len(calls)==12
    collect(plan,public,tmp_path,invoke)
    assert len(calls)==12
    rs=[json.loads(p.read_text()) for p in (tmp_path/'responses').glob('*.json')]
    for r in rs:
        if len(r['workflow'])==2:
            assert r['parent_request_id']==rid(plan['plan_id'],'i',r['profile'],r['workflow'][0])


def test_unresolved_attempt_stops_without_retry(tmp_path,table):
    public={"items":[{"id":"i","group":"g","case":{"question":"?","table":table}}]}
    plan={"public_sha256":digest(public),"items":1,"max_calls":12,"plan_id":"f"*24}
    write(tmp_path/'attempts'/(rid(plan['plan_id'],'i','standard','A')+'.json'),{"state":"started"})
    with pytest.raises(RuntimeError,match="no retry"):
        collect(plan,public,tmp_path,lambda role,text: {})
