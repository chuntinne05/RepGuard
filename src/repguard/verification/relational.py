"""Conditional relational obligations, independent of agent assertions/gold.

This is a bounded structural checker, not SQL equivalence, NL understanding or
business-truth certification. Unsupported query forms remain unresolved.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from typing import Literal

from pydantic import Field, field_validator, model_validator

from .models import FrozenModel


def fingerprint(value):
    if hasattr(value, 'model_dump'):
        value = value.model_dump(mode='json')
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def identifier(value):
    # SQLite folds ASCII identifiers, not arbitrary Unicode case pairs.
    return value.translate(str.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'))


class ColumnRef(FrozenModel):
    table: str = Field(min_length=1)
    column: str = Field(min_length=1)

    @property
    def key(self):
        return identifier(self.table), identifier(self.column)


class TableSchema(FrozenModel):
    name: str = Field(min_length=1)
    columns: tuple[str, ...] = Field(min_length=1)
    source: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    source_table: str | None = None

    @model_validator(mode='after')
    def unique_columns(self):
        if len({identifier(c) for c in self.columns}) != len(self.columns):
            raise ValueError('Ambiguous schema columns')
        return self


class Catalog(FrozenModel):
    tables: tuple[TableSchema, ...] = Field(min_length=1)
    snapshot_ref: str = Field(min_length=1)

    @model_validator(mode='after')
    def unique_tables(self):
        if len({identifier(t.name) for t in self.tables}) != len(self.tables):
            raise ValueError('Ambiguous table names')
        return self

    @classmethod
    def from_manifest(cls, manifest):
        return cls(snapshot_ref=manifest.get('logical_relation_sha256') or manifest['derived_sha256'],
                   tables=tuple(TableSchema(name=name, columns=tuple(t['columns']), source=t['source'],
                                            source_sha256=t['source_sha256'], source_table=t.get('source_table'))
                                for name, t in sorted(manifest['tables'].items())))


class OutputSpec(FrozenModel):
    operation: Literal['column', 'count', 'sum', 'avg', 'min', 'max'] = 'column'
    field: ColumnRef | None = None

    @model_validator(mode='after')
    def needs_field(self):
        if self.field is None and self.operation != 'count':
            raise ValueError('Only count(*) may omit a field')
        return self

    @property
    def key(self):
        return self.operation, self.field.key if self.field else None


class FilterSpec(FrozenModel):
    field: ColumnRef
    operator: Literal['eq', 'ne', 'lt', 'le', 'gt', 'ge', 'is_null', 'not_null']
    value: str | int | float | None = None

    @field_validator('value', mode='before')
    @classmethod
    def scalar(cls, value):
        if isinstance(value, bool) or isinstance(value, float) and not math.isfinite(value):
            raise ValueError('Finite non-boolean scalar required')
        return value

    @model_validator(mode='after')
    def null_semantics(self):
        if (self.operator in ('is_null', 'not_null')) != (self.value is None):
            raise ValueError('Explicit NULL operator required')
        return self


class JoinSpec(FrozenModel):
    left: ColumnRef
    right: ColumnRef

    @property
    def key(self):
        return tuple(sorted((self.left.key, self.right.key)))


class OrderSpec(FrozenModel):
    field: ColumnRef
    descending: bool = False


class QueryContract(FrozenModel):
    id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    authority_ref: str = Field(min_length=1)
    approval: Literal['review_required', 'development_only', 'independently_reviewed'] = 'review_required'
    outputs: tuple[OutputSpec, ...] = Field(min_length=1)
    filters: tuple[FilterSpec, ...] = ()
    joins: tuple[JoinSpec, ...] = ()
    grouping: tuple[ColumnRef, ...] = ()
    ordering: tuple[OrderSpec, ...] = ()
    distinct: Literal['require', 'forbid', 'any'] = 'any'
    limit: Literal['forbid', 'any'] = 'forbid'
    exact_filters: bool = True
    output_order_sensitive: bool = False
    open_questions: tuple[str, ...] = ()


class ObligationCheck(FrozenModel):
    id: str
    status: Literal['met', 'violated', 'unresolved']
    detail: str


class QueryReceipt(FrozenModel):
    contract_sha256: str
    catalog_sha256: str
    sql_sha256: str
    contract_id: str
    authority_ref: str
    approval: str
    checks: tuple[ObligationCheck, ...]
    obligation_status: Literal['met', 'violated', 'unresolved']
    release_status: Literal['eligible_for_host_review', 'blocked', 'needs_review']
    source_roots: tuple[str, ...]
    checker_version: Literal['relational_obligations_v1'] = 'relational_obligations_v1'
    parser_version: str
    execution_verified: Literal[False] = False
    semantic_truth_certified: Literal[False] = False
    assurance: str = 'Conditional structural obligations only; no NL/SQL-equivalence, row completeness, live-data or business-truth certificate.'


def _literal(value):
    if value is None:
        return ('null', None)
    if isinstance(value, str):
        return ('text', value)
    return _numeric(str(value))


def _numeric(text, negative=False):
    from decimal import Decimal, InvalidOperation, localcontext
    try:
        value = Decimal(text)
        if not value.is_finite() or len(value.as_tuple().digits) > 128 or abs(value.as_tuple().exponent) > 1000:
            raise ValueError('Numeric literal bound')
        if negative:
            value = value.copy_negate()
        with localcontext() as context:
            context.prec = max(1, len(value.as_tuple().digits))
            return ('number', str(value.normalize()) if value else '0')
    except InvalidOperation as error:
        raise ValueError('Invalid numeric literal') from error


def audit_query(contract: QueryContract, sql: str, catalog: Catalog) -> QueryReceipt:
    """Check explicit source/operator obligations; never execute the query.

    Supports one flat SELECT with named tables, explicit projections, conjunctive
    scalar comparisons and INNER equijoins. CTEs/subqueries/OR/windows/complex
    expressions are unresolved; no regex-based inference of semantic roles.
    """
    import sqlglot
    from sqlglot import exp

    checks = []
    roots = set()

    def add(name, status, detail):
        checks.append(ObligationCheck(id=name, status=status, detail=detail))

    def result():
        states = {c.status for c in checks}
        status = 'violated' if 'violated' in states else 'unresolved' if 'unresolved' in states else 'met'
        if contract.approval != 'independently_reviewed' or contract.open_questions:
            release = 'needs_review'
        else:
            release = {'met': 'eligible_for_host_review', 'violated': 'blocked', 'unresolved': 'needs_review'}[status]
        return QueryReceipt(contract_sha256=fingerprint(contract), catalog_sha256=fingerprint(catalog),
                            sql_sha256=fingerprint(sql), contract_id=contract.id, authority_ref=contract.authority_ref,
                            approval=contract.approval, checks=tuple(checks), obligation_status=status,
                            release_status=release, source_roots=tuple(sorted(roots)), parser_version=sqlglot.__version__)

    if not isinstance(sql, str) or not 0 < len(sql) <= 16000:
        add('query_form', 'unresolved', 'Missing query or query byte/character bound exceeded')
        return result()
    try:
        statements = sqlglot.parse(sql, read='sqlite')
        if len(statements) != 1 or not isinstance(statements[0], exp.Select):
            raise ValueError('Exactly one SELECT required')
        query = statements[0]
        if sum(1 for _ in query.walk()) > 2000:
            raise ValueError('AST node bound exceeded')
        if len(list(query.find_all(exp.Select))) != 1 or any(query.find(t) is not None for t in (exp.CTE, exp.Subquery, exp.Window)):
            raise ValueError('Nested scopes/windows need another verifier')
        if any(query.args.get(k) for k in ('into', 'having', 'qualify', 'offset', 'locks', 'with_', 'sample')):
            raise ValueError('Unsupported query modifier')
        if query.args.get('distinct') and query.args['distinct'].args.get('on'):
            raise ValueError('DISTINCT ON is not supported')
        if query.args.get('group') and any(query.args['group'].args.get(k) for k in ('rollup', 'cube', 'grouping_sets', 'totals', 'all')):
            raise ValueError('Complex grouping is not supported')
        tables = {identifier(t.name): t for t in catalog.tables}
        bindings = {}
        seen_tables = set()
        table_nodes = [query.args['from_'].this] + [j.this for j in query.args.get('joins', [])]
        for node in table_nodes:
            if not isinstance(node, exp.Table) or node.db or node.catalog:
                raise ValueError('Only named tables in this snapshot supported')
            name = identifier(node.name)
            if name not in tables:
                raise ValueError('Unknown source table: ' + node.name)
            if name in seen_tables:
                raise ValueError('Self-join roles not supported')
            alias = identifier(node.alias_or_name)
            if alias in bindings:
                raise ValueError('Duplicate alias')
            bindings[alias] = tables[name]
            seen_tables.add(name)
            roots.add(tables[name].source_sha256)

        def column(node):
            if not isinstance(node, exp.Column) or node.is_star or node.db or node.catalog:
                raise ValueError('Explicit unambiguous source column required')
            candidates = [bindings.get(identifier(node.table))] if node.table else list(bindings.values())
            candidates = [t for t in candidates if t is not None and identifier(node.name) in {identifier(c) for c in t.columns}]
            if len(candidates) != 1:
                raise ValueError('Unknown or ambiguous source column: ' + node.sql())
            return identifier(candidates[0].name), identifier(node.name)

        # Validate contract references too: an invented expected field is not truth.
        for ref in contract.outputs:
            if ref.field and (ref.field.key[0] not in tables or ref.field.key[1] not in {identifier(c) for c in tables[ref.field.key[0]].columns}):
                raise ValueError('Contract references unknown field')
        for ref in [f.field for f in contract.filters] + [r for j in contract.joins for r in (j.left, j.right)] + list(contract.grouping) + [o.field for o in contract.ordering]:
            if ref.key[0] not in tables or ref.key[1] not in {identifier(c) for c in tables[ref.key[0]].columns}:
                raise ValueError('Contract references unknown field')
        for node in query.find_all(exp.Column):
            # ORDER aliases are handled separately below; all other references must resolve.
            if node.find_ancestor(exp.Order) is None:
                column(node)
        add('source_bindings', 'met', 'All checked identifiers resolve in caller-owned catalog')

        projections = []
        output_aliases = {}
        unknown_output = False
        for node in query.expressions:
            core = node.this if isinstance(node, exp.Alias) else node
            try:
                if isinstance(core, exp.Column):
                    key = ('column', column(core))
                elif type(core) in (exp.Count, exp.Sum, exp.Avg, exp.Min, exp.Max) and not core.expressions:
                    key = (core.key, None if isinstance(core.this, exp.Star) and isinstance(core, exp.Count) else column(core.this))
                else:
                    raise ValueError('Projection expression needs another verifier')
                projections.append(key)
                if isinstance(node, exp.Alias):
                    alias = identifier(node.alias)
                    if alias in output_aliases:
                        raise ValueError('Duplicate output aliases')
                    output_aliases[alias] = key
            except ValueError:
                unknown_output = True
        expected = [o.key for o in contract.outputs]
        equal = projections == expected if contract.output_order_sensitive else Counter(projections) == Counter(expected)
        add('output_bindings', 'unresolved' if unknown_output else 'met' if equal else 'violated',
            'Expected explicit source/operator outputs: ' + repr(expected))

        def unparen(node):
            while isinstance(node, exp.Paren):
                node = node.this
            return node

        def conjuncts(node):
            node = unparen(node)
            return conjuncts(node.this) + conjuncts(node.expression) if isinstance(node, exp.And) else [node]

        def scalar(node):
            if isinstance(node, exp.Neg) and isinstance(node.this, exp.Literal) and not node.this.is_string:
                return _numeric(node.this.this, negative=True)
            if isinstance(node, exp.Literal):
                return _literal(node.this) if node.is_string else _numeric(node.this)
            raise ValueError('Scalar literal required')

        ops = {exp.EQ: 'eq', exp.NEQ: 'ne', exp.LT: 'lt', exp.LTE: 'le', exp.GT: 'gt', exp.GTE: 'ge'}
        reverse = {'eq': 'eq', 'ne': 'ne', 'lt': 'gt', 'le': 'ge', 'gt': 'lt', 'ge': 'le'}
        filters = set()
        joins = set()
        unknown_predicate = False
        predicates = []
        if query.args.get('where'):
            predicates.extend(conjuncts(query.args['where'].this))
        for join in query.args.get('joins', []):
            if join.args.get('side') or join.args.get('kind') not in (None, '', 'INNER') or join.args.get('using'):
                raise ValueError('Only explicit INNER equijoins supported')
            if not join.args.get('on'):
                raise ValueError('Join requires explicit ON condition')
            predicates.extend(conjuncts(join.args['on']))
        for node in predicates:
            try:
                if isinstance(node, exp.Is) and isinstance(node.expression, exp.Null):
                    filters.add((column(node.this), 'is_null', _literal(None)))
                elif isinstance(node, exp.Not) and isinstance(unparen(node.this), exp.Is) and isinstance(unparen(node.this).expression, exp.Null):
                    filters.add((column(unparen(node.this).this), 'not_null', _literal(None)))
                elif type(node) in ops:
                    if isinstance(node.this, exp.Column) and isinstance(node.expression, exp.Column) and isinstance(node, exp.EQ):
                        joins.add(tuple(sorted((column(node.this), column(node.expression)))))
                    elif isinstance(node.this, exp.Column):
                        filters.add((column(node.this), ops[type(node)], scalar(node.expression)))
                    else:
                        filters.add((column(node.expression), reverse[ops[type(node)]], scalar(node.this)))
                else:
                    raise ValueError('OR/complex predicate cannot discharge conjunctive requirements')
            except ValueError:
                unknown_predicate = True
        needed = {(f.field.key, f.operator, _literal(f.value)) for f in contract.filters}
        match = filters == needed if contract.exact_filters else needed <= filters
        referenced_filter_fields = {column(c) for p in predicates for c in p.find_all(exp.Column)}
        absent_required_fields = {f.field.key for f in contract.filters} - referenced_filter_fields
        filter_status = ('violated' if absent_required_fields else 'unresolved' if unknown_predicate else 'met' if match else 'violated')
        add('filter_bindings', filter_status,
            'Required mandatory field predicates: ' + repr(sorted(needed, key=repr)))
        absent_join_tables = {r.key[0] for j in contract.joins for r in (j.left, j.right)} - seen_tables
        add('join_bindings', 'violated' if absent_join_tables else 'unresolved' if unknown_predicate else 'met' if joins == {j.key for j in contract.joins} else 'violated',
            'Only the declared equality join relationships are checked; cardinality semantics not certified')
        actual_group = tuple(column(n) for n in query.args['group'].expressions) if query.args.get('group') else ()
        add('grouping', 'met' if Counter(actual_group) == Counter(r.key for r in contract.grouping) else 'violated', 'Grouping key obligations')
        actual_order = []
        for node in query.args['order'].expressions if query.args.get('order') else []:
            field = node.this
            if isinstance(field, exp.Column) and not field.table and identifier(field.name) in output_aliases:
                key = output_aliases[identifier(field.name)]
                if key[0] != 'column':
                    raise ValueError('Ordering by aggregate expression not supported')
                ref = key[1]
            else:
                ref = column(field)
            actual_order.append((ref, bool(node.args.get('desc'))))
        expected_order = [(o.field.key, o.descending) for o in contract.ordering]
        add('ordering', 'met' if not expected_order or actual_order == expected_order else 'violated', 'Requested ordering, if specified')
        distinct = bool(query.args.get('distinct'))
        add('multiplicity', 'met' if contract.distinct == 'any' or distinct == (contract.distinct == 'require') else 'violated', 'DISTINCT presence only; join multiplicity not certified')
        add('limit', 'violated' if contract.limit == 'forbid' and query.args.get('limit') else 'met', 'No silent LIMIT when full output is required')
    except (ValueError, KeyError, TypeError, RecursionError, sqlglot.errors.SqlglotError) as error:
        add('unsupported_or_unbound', 'unresolved', str(error)[:500])
    if contract.open_questions:
        add('task_interpretation', 'unresolved', '; '.join(contract.open_questions))
    return result()


def validate_handoff(receipt: QueryReceipt, contract: QueryContract, sql: str, catalog: Catalog):
    """Recompute locally; matching hashes alone do not authenticate a verdict.

    Host must own the contract/catalog. This is not a signature scheme and does
    not authorize trusting agent-provided authority inputs.
    """
    return (receipt.contract_sha256 == fingerprint(contract)
            and receipt.catalog_sha256 == fingerprint(catalog)
            and receipt.sql_sha256 == fingerprint(sql)
            and receipt == audit_query(contract, sql, catalog))


def search_schema(catalog: Catalog, literal: str, *, limit: int = 12):
    """Bounded literal metadata lookup, not a semantic field adjudicator.

    Searches ALL table/column names, including columns of SQLite tables, unlike
    searching just raw text files. No gold, sample values or answer queries.
    """
    if not isinstance(literal, str) or not 1 <= len(literal) <= 128 or not 1 <= limit <= 30:
        raise ValueError('Schema search bounds')
    needle = identifier(literal)
    hits = []
    for table in catalog.tables:
        for col in table.columns:
            if needle in identifier(col) or needle in identifier(table.name):
                hits.append({'table': table.name, 'column': col, 'source': table.source,
                             'source_table': table.source_table, 'source_sha256': table.source_sha256})
    return {'hits': hits[:limit], 'truncated': len(hits) > limit, 'total_metadata_matches': len(hits),
            'semantic_mapping_verified': False, 'catalog_sha256': fingerprint(catalog)}


def review_query_once(contract, draft_sql, catalog, reviewer=None, *, reviewer_call_budget=1):
    """Host callback for an actual downstream agent, fixed contract/snapshot.

    No provider, automatic query rewriting or gold inside this function. A test
    callback is not evidence of model improvement. Host accounts for calls/costs.
    """
    if reviewer_call_budget not in (0, 1):
        raise ValueError('Only zero or one review callback allowed')
    initial = audit_query(contract, draft_sql, catalog)
    if initial.obligation_status == 'met' or reviewer is None or reviewer_call_budget == 0:
        return {'sql': draft_sql, 'receipt': initial, 'reviewer_calls': 0, 'trajectory': (initial,)}
    updated = reviewer(contract.model_copy(deep=True), draft_sql, initial, catalog.model_copy(deep=True))
    if not isinstance(updated, str):
        raise TypeError('Reviewer must return SQL text, not a replacement contract or receipt')
    final = audit_query(contract, updated, catalog)
    return {'sql': updated, 'receipt': final, 'reviewer_calls': 1, 'trajectory': (initial, final)}
