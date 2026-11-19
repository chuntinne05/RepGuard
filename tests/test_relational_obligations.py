import pytest

pytest.importorskip('sqlglot')

from repguard.verification.relational import (
    Catalog, ColumnRef, FilterSpec, JoinSpec, OrderSpec, OutputSpec, QueryContract,
    TableSchema, audit_query, review_query_once, search_schema, validate_handoff,
)


@pytest.fixture
def setup():
    catalog = Catalog(snapshot_ref='snapshot1', tables=(
        TableSchema(name='people', columns=('id', 'name', 'nationality'), source='people.csv', source_sha256='a'*64),
        TableSchema(name='work', columns=('person_id', 'amount'), source='work.json', source_sha256='b'*64),
    ))
    contract = QueryContract(id='names', question='Names of people not having nationality China',
                             authority_ref='Independent source/task review record', approval='independently_reviewed',
                             outputs=(OutputSpec(field=ColumnRef(table='people', column='name')),),
                             filters=(FilterSpec(field=ColumnRef(table='people', column='nationality'), operator='ne', value='中国'),))
    return catalog, contract


def states(receipt):
    return {c.id: c.status for c in receipt.checks}


def test_source_predicate_passes_but_is_not_semantic_or_execution_certificate(setup):
    catalog, contract = setup
    r = audit_query(contract, "SELECT p.name AS result FROM people p WHERE p.nationality <> '中国'", catalog)
    assert r.obligation_status == 'met' and r.release_status == 'eligible_for_host_review'
    assert not r.execution_verified and not r.semantic_truth_certified


def test_names_are_not_nationality_and_alias_cannot_launder_source(setup):
    catalog, contract = setup
    for query in ("SELECT name FROM people WHERE name NOT LIKE '%中国%'",
                  "SELECT nationality AS name FROM people WHERE nationality <> '中国'"):
        r = audit_query(contract, query, catalog)
        assert r.obligation_status == 'violated'


def test_reading_required_field_in_projection_does_not_prove_filter(setup):
    catalog, contract = setup
    r = audit_query(contract, 'SELECT name,nationality FROM people', catalog)
    assert states(r)['filter_bindings'] == 'violated'
    assert states(r)['output_bindings'] == 'violated'


@pytest.mark.parametrize('predicate', ["nationality <> '中国' OR 1=1", "NOT(nationality = '中国')", "coalesce(nationality,'x') <> '中国'"])
def test_complex_or_equivalent_predicate_stays_unresolved(setup, predicate):
    catalog, contract = setup
    r = audit_query(contract, 'SELECT name FROM people WHERE ' + predicate, catalog)
    assert states(r)['filter_bindings'] == 'unresolved'
    assert r.release_status == 'needs_review'


@pytest.mark.parametrize('query', [
    'WITH p AS (SELECT * FROM people) SELECT name FROM p',
    'SELECT name FROM people UNION SELECT name FROM people',
    'SELECT name FROM people WHERE id IN (SELECT person_id FROM work)',
    'SELECT name, row_number() OVER () FROM people',
    'SELECT name FROM people; DELETE FROM people',
    'DELETE FROM people',
    'SELECT * FROM people',
])
def test_unsupported_forms_never_become_met(setup, query):
    catalog, contract = setup
    r = audit_query(contract, query, catalog)
    assert r.obligation_status != 'met'


def test_unknown_contract_field_not_treated_as_truth(setup):
    catalog, contract = setup
    bad = contract.model_copy(update={'outputs': (OutputSpec(field=ColumnRef(table='people', column='invented')), )})
    r = audit_query(bad, "SELECT name FROM people WHERE nationality <> '中国'", catalog)
    assert r.obligation_status == 'unresolved'


def test_no_release_without_independent_review_or_with_open_interpretations(setup):
    catalog, contract = setup
    for updates in ({'approval': 'development_only'}, {'approval': 'review_required'}, {'open_questions': ('Which abbreviation?',)}):
        r = audit_query(contract.model_copy(update=updates), "SELECT name FROM people WHERE nationality <> '中国'", catalog)
        assert r.release_status == 'needs_review'


def test_exact_filter_prevents_silent_population_narrowing(setup):
    catalog, contract = setup
    r = audit_query(contract, "SELECT name FROM people WHERE nationality <> '中国' AND id > 100", catalog)
    assert states(r)['filter_bindings'] == 'violated'


def test_joins_and_counting_unit_are_explicit(setup):
    catalog, contract = setup
    contract = contract.model_copy(update={'outputs': (OutputSpec(operation='sum', field=ColumnRef(table='work', column='amount')),),
                                          'joins': (JoinSpec(left=ColumnRef(table='people', column='id'), right=ColumnRef(table='work', column='person_id')), )})
    good = "SELECT SUM(w.amount) FROM work w JOIN people p ON w.person_id=p.id WHERE p.nationality <> '中国'"
    assert audit_query(contract, good, catalog).obligation_status == 'met'
    assert audit_query(contract, good.replace('w.person_id=p.id', 'w.person_id=p.name'), catalog).obligation_status == 'violated'
    assert audit_query(contract, good.replace('JOIN', 'LEFT JOIN'), catalog).obligation_status != 'met'


def test_limits_distinct_group_and_sort_are_not_silent(setup):
    catalog, contract = setup
    query = "SELECT name FROM people WHERE nationality <> '中国'"
    assert states(audit_query(contract, query + ' LIMIT 12', catalog))['limit'] == 'violated'
    preserve = contract.model_copy(update={'distinct': 'forbid'})
    assert states(audit_query(preserve, query.replace('SELECT', 'SELECT DISTINCT'), catalog))['multiplicity'] == 'violated'
    ordered = contract.model_copy(update={'ordering': (OrderSpec(field=ColumnRef(table='people', column='id')), )})
    assert states(audit_query(ordered, query + ' ORDER BY id DESC', catalog))['ordering'] == 'violated'


def test_numeric_literal_canonicalization_and_reversed_comparison(setup):
    catalog, contract = setup
    contract = contract.model_copy(update={'filters': (FilterSpec(field=ColumnRef(table='people', column='id'), operator='gt', value=100),)})
    for predicate in ('id > 100', '100 < id', 'id > 100.0', 'id > 1e2'):
        assert audit_query(contract, 'SELECT name FROM people WHERE ' + predicate, catalog).obligation_status == 'met'


def test_changed_query_contract_or_source_invalidates_old_handoff(setup):
    catalog, contract = setup
    sql = "SELECT name FROM people WHERE nationality <> '中国'"
    r = audit_query(contract, sql, catalog)
    assert validate_handoff(r, contract, sql, catalog)
    assert not validate_handoff(r, contract, sql + ' LIMIT 1', catalog)
    assert not validate_handoff(r, contract.model_copy(update={'question': 'Different task'}), sql, catalog)
    assert not validate_handoff(r, contract, sql, catalog.model_copy(update={'snapshot_ref': 'new_snapshot'}))


def test_schema_search_covers_sqlite_columns_and_preserves_source_roots(setup):
    catalog, _ = setup
    r = search_schema(catalog, 'NATIONALITY')
    assert len(r['hits']) == 1 and r['hits'][0]['source_sha256'] == 'a'*64
    assert not r['semantic_mapping_verified']
    with pytest.raises(ValueError):
        search_schema(catalog, '', limit=100)


def test_reviewer_uses_fixed_contract_and_must_return_candidate_only(setup):
    catalog, contract = setup
    bad = "SELECT name FROM people WHERE name NOT LIKE '%中国%'"
    def review(c, sql, receipt, sources):
        assert sql == bad and receipt.obligation_status == 'violated' and c == contract and sources == catalog
        return "SELECT name FROM people WHERE nationality <> '中国'"
    r = review_query_once(contract, bad, catalog, review)
    assert r['reviewer_calls'] == 1 and r['receipt'].obligation_status == 'met'
    assert len(r['trajectory']) == 2
    with pytest.raises(TypeError):
        review_query_once(contract, bad, catalog, lambda *args: contract)
    assert review_query_once(contract, bad, catalog, review, reviewer_call_budget=0)['reviewer_calls'] == 0


def test_two_copies_of_one_source_do_not_count_as_independent_evidence(setup):
    catalog, contract = setup
    c = Catalog(snapshot_ref='two_views', tables=catalog.tables + (TableSchema(name='people_copy', columns=('id','name','nationality'), source='same.csv', source_sha256='a'*64),))
    r = audit_query(contract, "SELECT name FROM people WHERE nationality <> '中国'", c)
    assert r.source_roots == ('a'*64,)


def test_forged_status_with_matching_hashes_does_not_validate(setup):
    catalog, contract = setup
    sql = "SELECT name FROM people WHERE name NOT LIKE '%中国%'"
    receipt = audit_query(contract, sql, catalog)
    forged = receipt.model_copy(update={'obligation_status': 'met', 'release_status': 'eligible_for_host_review'})
    assert not validate_handoff(forged, contract, sql, catalog)


def test_long_numeric_literals_do_not_round_to_same_contract_value(setup):
    catalog, contract = setup
    contract = contract.model_copy(update={'filters': (FilterSpec(field=ColumnRef(table='people', column='id'), operator='eq', value=12345678901234567890123456789),)})
    bad = audit_query(contract, 'SELECT name FROM people WHERE id=12345678901234567890123456790', catalog)
    assert states(bad)['filter_bindings'] == 'violated'
    huge = audit_query(contract, 'SELECT name FROM people WHERE id=1e99999999999999999999999', catalog)
    assert huge.obligation_status != 'met'
