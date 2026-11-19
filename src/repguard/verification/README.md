# Structured evidence verification

The optional [relational extension](RELATIONAL.md) adds SQL source/operator
obligations, bounded schema discovery and independently rechecked handoffs.
It preserves unresolved interpretations and does not certify business truth.

Reusable local checks for numerical claims and exact workflow states across
analytical tasks. This is engineering infrastructure, not a demonstrated novel
method or a universal natural-language verifier.

The caller supplies an independently approved `Contract` and an `EvidenceStore`.
An agent supplies only a `Candidate`: value, unit and bindings to existing fact
IDs. It cannot insert a new expected value, approve its own contract or replace
the evidence store through that schema.

Supported operations: lookup, difference, sum of explicitly distinct operands,
ratio, percentage change; exact status lookup. Scope checks include entity,
metric, period, population, state and qualifiers such as split/run/model IDs.
Units are explicit and dimension checked; fractions, percentages and percentage
points have distinct meanings. No currency exchange or locale is guessed.

Conflicting applicable records, unknown validity, an unreviewed contract, an
unadmitted fact or a peer assertion yield `unresolved`. Explicit half-open
validity intervals can distinguish revisions at a caller-specified `as_of`.
There is no automatic latest-timestamp-wins rule or voting by source copies.
Unknown does not mean false.

`consistent` and `inconsistent` are conditional on the contract, trusted
source admission and metadata. Every receipt has `semantic_truth_certified=false`.
The engine does not establish correctness of natural-language interpretation,
source extraction/mapping, original experiments, source completeness or live
world state. The host must control contract approval and source admission;
passing arbitrary agent-authored files as trusted inputs defeats that boundary.

Adapters read a scalar from a JSON pointer or an exact unique CSV row. They bind
file bytes and a locator, not the semantic interpretation of the field. Units,
scope and lineage are supplied by a caller-owned adapter or reviewed mapping.
An end-to-end system still needs evidence discovery, parsing and mapping.

`handoff.review_once` is a bounded callback integration: verify a real draft,
optionally ask one reviewer, then verify the returned candidate against the
original contract/store. No model provider is called by this package. This
callback is a host integration, not an isolation boundary for arbitrary code.

Run the examples from repository root:

```bash
PYTHONPATH=src:. .venv/bin/python research_ops/general_verification_demo.py
PYTHONPATH=src:. .venv/bin/python -m repguard.verification \
  --contract results/general_verification_v1/examples/sales_operations/contract.json \
  --store results/general_verification_v1/examples/sales_operations/store.json \
  --candidate results/general_verification_v1/examples/sales_operations/candidate.json
```

The examples are explicitly labeled synthetic fixtures, real recorded artifact
claims and controlled mutations. They are not benchmark performance estimates.
Tests are in `tests/test_verification_contracts.py`. Old frozen experiment code,
scores, source hashes and deployments are unchanged.
