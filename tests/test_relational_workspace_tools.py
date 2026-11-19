import pytest

pytest.importorskip('sqlglot')

from experiments.relational_v5.tools import AuditedWorkspaceTools
from experiments.workspace_v4.tools import materialize
from repguard.verification.relational import ColumnRef, FilterSpec, OutputSpec, QueryContract


@pytest.fixture
def workspace(tmp_path):
    ctx = tmp_path / 'context'; ctx.mkdir()
    (ctx / 'orders.csv').write_text('id,state,amount\n1,delivered,100\n2,shipped,200\n')
    db = tmp_path / 'derived.sqlite'; materialize(ctx, db)
    contract = QueryContract(id='delivered', question='Amounts for delivered orders',
                             authority_ref='Engineering fixture, not a human annotation', approval='development_only',
                             outputs=(OutputSpec(field=ColumnRef(table='orders', column='amount')),),
                             filters=(FilterSpec(field=ColumnRef(table='orders', column='state'), operator='eq', value='delivered'),))
    return AuditedWorkspaceTools(ctx, db, tmp_path / 'artifacts', contract=contract), ctx, db


def test_executes_real_source_but_does_not_certify_wrong_population(workspace):
    w, _, _ = workspace
    bad = w.dispatch({'tool': 'query', 'args': {'sql': "SELECT amount FROM orders WHERE state='shipped'"}})
    assert bad['execution_ok'] and bad['rows'] == 1
    assert bad['query_obligations']['obligation_status'] == 'violated'
    assert bad['query_obligations']['release_status'] == 'needs_review'
    audit = w.dispatch({'tool': 'query_audit', 'args': {'result_id': bad['result_id']}})
    assert audit['host_execution_recorded'] and not audit['semantic_truth_certified']


def test_no_gold_required_and_no_agent_replacement_contract(workspace):
    w, _, _ = workspace
    good = w.query("SELECT amount FROM orders WHERE state='delivered'")
    assert good['query_obligations']['obligation_status'] == 'met'
    assert w.schema_search('state')['hits'][0]['table'] == 'orders'
    with pytest.raises(TypeError):
        w.dispatch({'tool': 'query', 'args': {'sql': 'SELECT amount FROM orders', 'contract': {}}})


def test_tampered_artifact_or_source_stops_reaudit(workspace):
    w, ctx, _ = workspace
    result = w.query("SELECT amount FROM orders WHERE state='delivered'")
    (w.artifacts / (result['result_id'] + '.csv')).write_text('changed')
    with pytest.raises(ValueError, match='Result bytes changed'):
        w.query_audit(result['result_id'])
    (ctx / 'orders.csv').write_text('id,state,amount\n1,delivered,999\n')
    with pytest.raises(ValueError, match='Source bytes changed'):
        w.schema_search('amount')


def test_asserted_table_cannot_inherit_query_execution_assurance(workspace):
    w, _, _ = workspace
    result = w.save_table(['amount'], [[100]])
    audit = w.query_audit(result['result_id'])
    assert audit['state'] == 'unresolved' and not audit['semantic_truth_certified']
