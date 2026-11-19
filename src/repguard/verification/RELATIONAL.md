# Relational obligations and source-aware handoffs

`relational.py` extends the scalar kernel with explicit SQL field/operator
obligations. It is engineering infrastructure, not a demonstrated new algorithm,
complete SQL verifier or natural-language semantic judge.

The host supplies a `Catalog` and `QueryContract`: source bindings, projected
fields/aggregations, mandatory predicates, joins, grouping, ordering,
multiplicity and full-output/no-LIMIT conditions. Contracts contain no expected
answer rows. Source admission and interpretation remain host responsibilities.
The SQL candidate cannot replace the contract through the tool interface.

Two dimensions are kept separate:

- `obligation_status`: `met`, `violated`, `unresolved`, for supported structural checks.
- `release_status`: `needs_review`, `blocked`, or `eligible_for_host_review`.
  A development/unreviewed contract or open interpretation always needs review.
  Eligibility never authorizes publication or certifies business correctness.

Every receipt binds contract/catalog/query digests and records checker/parser
versions. `validate_handoff` re-computes checks; it does not merely trust matching
hashes or an agent-supplied `met` label. Hashes are not signatures. The host must
control contract/catalog authority and result storage.

Supported query profile: one flat SQLite SELECT, explicit fields, simple
count/sum/avg/min/max, mandatory conjunctive scalar comparisons, INNER equijoins,
group/order keys and DISTINCT/LIMIT presence. Aliases resolve to source columns.
Reading Nationality in a projection does not establish a nationality filter;
renaming Name to Nationality does not change its source. An OR branch cannot
discharge a mandatory conjunctive predicate. Unsupported forms, including CTEs,
subqueries, windows, complex expressions, outer/self joins and many equivalent
predicate rewrites, stay unresolved. This deliberately sacrifices coverage.

Checks do not prove foreign-key cardinality, row completeness, null-order policy,
unit meaning, temporal “latest”, arbitrary SQL equivalence, source quality or NL
interpretation. `execution_verified=false` and `semantic_truth_certified=false`
in static query receipts. A correct query can remain unresolved or violate a
strict structural contract; do not score every refusal as an error caught.

`search_schema` searches all supplied table/column names, including original
SQLite metadata. It is bounded literal retrieval, not automatic mapping between
business terminology and fields.

`experiments/relational_v5/tools.py` integrates these checks with the existing
read-only source tools, without modifying frozen v4 experiments. `query` records
actual SQL execution and separate contract diagnostics; `query_audit` checks
artifact bytes and re-audits on the fixed catalog. Agent-asserted tables remain
unresolved for SQL execution evidence. Source/derived byte drift stops the
adapter. No automatic rewrite, gold lookup or result-column deletion occurs.
`review_query_once` is a host callback with a0/1call budget and fixed inputs;
it contains no model provider. Host Python callbacks are trusted code, not an
agent-code sandbox.

Install optional dependencies with `pip install -e '.[analytics]'`, or use the
hash-pinned pure-Python requirement in `research_ops/requirements-query-audit.txt`
in an isolated environment. The development run used SQLGlot30.30.0 under
`/private/tmp/repguard-query-deps`, preserving the prior virtualenv.

```sh
PYTHONPATH=/private/tmp/repguard-query-deps:src:. .venv/bin/python -m pytest -q \
  tests/test_relational_obligations.py tests/test_relational_workspace_tools.py

PYTHONPATH=/private/tmp/repguard-query-deps:src:. .venv/bin/python \
  -m repguard.verification.query_cli \
  --contracts results/relational_v5/analysis_v2/contracts/task_371.json \
  --manifest results/workspace_v4/derived_v3/task_371/workspace.manifest.json \
  --sql-file /private/tmp/candidate.sql
```

For multiple supplied interpretations the CLI evaluates all and requires a
choice; it never picks the interpretation matching a benchmark gold answer.
The development replay includes36old trajectories, not36new model results.
The20final SQL queries were actually re-executed and all20reproduced their old
output bytes. This is reproducibility, not accuracy. Contracts were authored
after inspecting old outcomes; they are not independent human labels. See the
latest Vietnamese report under `docs/reports/2026-11-09/`.
