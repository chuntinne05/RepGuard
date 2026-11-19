from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from repguard.verification import Candidate, Contract, EvidenceStore, Fact, Operand, Scope, verify
from repguard.verification.adapters import csv_row_fact, json_pointer_fact
from repguard.verification.handoff import review_once


def scope(**changes):
    return Scope(entity="shop", metric="revenue", period="2026-Q1", population="all_orders", state="observed", **changes)


def fact(fid="f", value="120", unit="USD", **changes):
    args=dict(id=fid,value=value,unit=unit,scope=scope(),source_id="ledger",snapshot_sha256="a"*64,
              locator="/revenue",root_ids=("ledger-root",))
    args.update(changes);return Fact(**args)


def contract(**changes):
    args=dict(id="c",question="What was revenue?",authority_ref="reviewed-task-1",approval="approved",
              operation="lookup",operands={"value":Operand(scope=scope(),unit="USD")},output_unit="USD")
    args.update(changes);return Contract(**args)


def candidate(value="120",unit="USD",**changes):
    args=dict(claim_id="c",value=value,unit=unit,bindings={"value":"f"});args.update(changes);return Candidate(**args)


def test_numeric_units_and_currency_are_not_interchangeable():
    store=EvidenceStore([fact(value="1.2",unit="million_USD")],['f'])
    assert verify(contract(),candidate("1200000"),store).verdict=="consistent"
    assert verify(contract(),candidate("1200000","EUR"),store).verdict=="inconsistent"


@pytest.mark.parametrize('axis,value',[("entity","other"),("metric","production"),("period","2026-Q2"),
                                     ("population","completed_orders"),("state","forecast")])
def test_each_scope_axis_blocks_same_number_wrong_context(axis,value):
    s=scope().model_copy(update={axis:value})
    store=EvidenceStore([fact(scope=s)],['f'])
    r=verify(contract(),candidate(),store)
    assert r.verdict=="unresolved" and r.reasons==('scope_mismatch:value',)


def test_scientific_split_and_model_qualifiers_must_match():
    target=scope(qualifiers={"split":"test","model":"A"})
    wrong=scope(qualifiers={"split":"dev","model":"A"})
    c=contract(operands={"value":Operand(scope=target,unit="USD")})
    assert verify(c,candidate(),EvidenceStore([fact(scope=wrong)],['f'])).verdict=="unresolved"


def test_agent_cannot_inject_gold_scope_or_approval():
    for extra in ({"approval":"approved"},{"scope":scope().model_dump()},{"expected_value":"120"}):
        with pytest.raises(ValidationError):candidate(**extra)
    c=contract(approval="review_required")
    assert verify(c,candidate(),EvidenceStore([fact()],['f'])).verdict=="unresolved"


def test_unadmitted_and_peer_facts_do_not_become_truth():
    assert verify(contract(),candidate(),EvidenceStore([fact()])).verdict=="unresolved"
    store=EvidenceStore([fact(origin="peer_assertion")],['f'])
    assert verify(contract(),candidate(),store).verdict=="unresolved"


def test_conflicting_uncited_facts_are_not_hidden_by_cherry_picking():
    fs=[fact(),fact('other',value='121',source_id='export')]
    r=verify(contract(),candidate(),EvidenceStore(fs,['f','other']))
    assert r.verdict=="unresolved" and r.reasons==('conflicting_applicable_evidence:value',)


def test_copies_share_a_root_and_do_not_increase_independence():
    fs=[fact(),fact('copy',source_id='copy')]
    r=verify(contract(),candidate(),EvidenceStore(fs,['f','copy']))
    assert r.verdict=="consistent" and r.root_ids==('ledger-root',)


def test_validity_boundary_and_unknown_time_require_evidence():
    start=datetime(2026,1,1,tzinfo=timezone.utc);end=datetime(2026,2,1,tzinfo=timezone.utc)
    f=fact(valid_from=start,valid_until=end)
    st=EvidenceStore([f],['f'])
    assert verify(contract(as_of=start),candidate(),st).verdict=="consistent"
    assert verify(contract(as_of=end),candidate(),st).verdict=="unresolved"
    assert verify(contract(),candidate(),st).verdict=="unresolved"
    assert verify(contract(as_of=start),candidate(),EvidenceStore([fact()],['f'])).verdict=="unresolved"


def test_explicit_nonoverlapping_revisions_can_be_resolved():
    at=datetime(2026,2,1,tzinfo=timezone.utc)
    st=EvidenceStore([fact(valid_until=at),fact('new',value='130',valid_from=at)],['f','new'])
    r=verify(contract(as_of=at),candidate('130',bindings={'value':'new'}),st)
    assert r.verdict=='consistent'


def test_percent_change_and_rate_difference_have_distinct_units():
    old=scope().model_copy(update={'period':'2025-Q1'})
    fs=[fact('old',value='100',scope=old),fact('new',value='120')]
    c=contract(operation='percent_change',operands={'new':Operand(scope=scope(),unit='USD'),'old':Operand(scope=old,unit='USD')},output_unit='percent',absolute_tolerance='0.01')
    st=EvidenceStore(fs,['old','new'])
    a=candidate('0.2','ratio',bindings={'new':'new','old':'old'})
    assert verify(c,a,st).verdict=='consistent'
    assert verify(c,a.model_copy(update={'unit':'percentage_point'}),st).verdict=='inconsistent'
    fs=[fact('left',value='7.4',unit='percent'),fact('right',value='0.069',unit='ratio')]
    c=contract(operation='difference',operands={'left':Operand(scope=scope(),unit='ratio'),'right':Operand(scope=scope(),unit='ratio')},output_unit='percentage_point')
    # Same scope with different values is a conflict, even for a clever formula.
    assert verify(c,candidate('0.5','percentage_point',bindings={'left':'left','right':'right'}),EvidenceStore(fs,['left','right'])).verdict=='unresolved'


def test_zero_denominator_no_nan_or_fake_certificate():
    old=scope().model_copy(update={'period':'old'})
    fs=[fact('new'),fact('old',value='0',scope=old)]
    c=contract(operation='percent_change',operands={'new':Operand(scope=scope(),unit='USD'),'old':Operand(scope=old,unit='USD')},output_unit='percent')
    r=verify(c,candidate('0','percent',bindings={'new':'new','old':'old'}),EvidenceStore(fs,['new','old']))
    assert r.verdict=='unresolved' and not r.semantic_truth_certified


def test_rate_difference_converts_fraction_to_percentage_points():
    left=scope().model_copy(update={'metric':'rd_ratio'})
    right=scope().model_copy(update={'metric':'capex_ratio'})
    fs=[fact('left',value='0.074',unit='ratio',scope=left),fact('right',value='6.9',unit='percent',scope=right)]
    c=contract(operation='difference',operands={'left':Operand(scope=left,unit='ratio'),'right':Operand(scope=right,unit='ratio')},output_unit='percentage_point',absolute_tolerance='0.001')
    st=EvidenceStore(fs,['left','right'])
    a=candidate('0.5','percentage_point',bindings={'left':'left','right':'right'})
    assert verify(c,a,st).verdict=='consistent'
    assert verify(c,a.model_copy(update={'unit':'percent'}),st).verdict=='inconsistent'


def test_workflow_submission_is_not_completion():
    s=scope().model_copy(update={'metric':'deployment_status','state':'effect_observed'})
    c=contract(operands={'value':Operand(scope=s,unit='status')},output_unit='status')
    f=fact(value='submitted',unit='status',scope=s)
    r=verify(c,candidate('completed','status'),EvidenceStore([f],['f']))
    assert r.verdict=='inconsistent'


def test_json_adapter_hash_and_locator_bind_actual_file(tmp_path):
    p=tmp_path/'a.json';p.write_text('{"a/b":{"~x":12}}')
    f=json_pointer_fact(p,'/a~1b/~0x',fact_id='f',scope=scope(),unit='USD',source_id='s',root_ids=('s',))
    assert f.value=='12' and f.locator=='/a~1b/~0x'
    before=f.snapshot_sha256;p.write_text('{"a/b":{"~x":13}}')
    f2=json_pointer_fact(p,'/a~1b/~0x',fact_id='f',scope=scope(),unit='USD',source_id='s',root_ids=('s',))
    assert f2.snapshot_sha256!=before


def test_bounded_handoff_cannot_change_contract_to_make_wrong_claim_pass():
    st=EvidenceStore([fact()],['f']);calls=[]
    def reviewer(c,a,r):
        calls.append(1);c.operands.clear()
        return candidate('120')
    out=review_once(contract(),candidate('999'),st,reviewer)
    assert out.receipt.verdict=='consistent' and out.reviewer_calls==1 and len(calls)==1
    assert len(out.trajectory)==2
    assert review_once(contract(),candidate('999'),st,reviewer,reviewer_call_budget=0).reviewer_calls==0


def test_bad_roles_unknown_unit_and_duplicate_ids():
    with pytest.raises(ValidationError):contract(operation='ratio')
    with pytest.raises(ValueError):EvidenceStore([fact(),fact()],['f'])
    assert verify(contract(),candidate('120','unknown'),EvidenceStore([fact()],['f'])).verdict=='unresolved'


def test_scale_conversion_does_not_round_source_before_comparison():
    raw='1.234567890123456789012345678901'
    st=EvidenceStore([fact(value=raw,unit='million_USD')],['f'])
    a=candidate('1234567.890123456789012345678901')
    assert verify(contract(),a,st).verdict=='consistent'


def test_additive_total_cannot_double_count_same_fact_or_copied_scope():
    c=contract(operation='sum',operands={'x':Operand(scope=scope(),unit='USD'),'y':Operand(scope=scope(),unit='USD')})
    st=EvidenceStore([fact(),fact('copy')],['f','copy'])
    assert verify(c,candidate('240',bindings={'x':'f','y':'f'}),st).verdict=='unresolved'
    assert verify(c,candidate('240',bindings={'x':'f','y':'copy'}),st).verdict=='unresolved'


def test_additive_total_over_explicit_distinct_metrics():
    s=scope().model_copy(update={'metric':'other_revenue'})
    fs=[fact(),fact('other',value='30',scope=s)]
    c=contract(operation='sum',operands={'x':Operand(scope=scope(),unit='USD'),'y':Operand(scope=s,unit='USD')})
    r=verify(c,candidate('150',bindings={'x':'f','y':'other'}),EvidenceStore(fs,['f','other']))
    assert r.verdict=='consistent'


def test_csv_adapter_requires_unique_row_and_exact_metric(tmp_path):
    p=tmp_path/'operations.csv';p.write_text('period,metric,value\nQ1,delivered,12\nQ1,produced,20\n')
    args=dict(fact_id='f',scope=scope(),unit='count',source_id='ops',root_ids=('ops',))
    f=csv_row_fact(p,match={'period':'Q1','metric':'delivered'},value_column='value',**args)
    assert f.value=='12' and 'row=1;' in f.locator
    with pytest.raises(ValueError,match='ambiguous'):
        csv_row_fact(p,match={'period':'Q1'},value_column='value',**args)


def test_csv_duplicate_headers_are_not_silently_overwritten(tmp_path):
    p=tmp_path/'bad.csv';p.write_text('key,value,value\nx,1,2\n')
    with pytest.raises(ValueError,match='header'):
        csv_row_fact(p,match={'key':'x'},value_column='value',fact_id='f',scope=scope(),unit='count',source_id='s',root_ids=('s',))
