# ARQA cycle02 — frozen pilot

Plan `deaee6167f9609bd2f045f46`, registered2026-11-09T06:59:25UTC before corpus inference.
24 questions from24 connected source groups, two prompt profiles × six direct/self/cross workflows.
288 real responses completed; no automatic retries. Raw artifacts are gitignored in `results/arqa_v2/`.

Primary+2.083pp,95%CI[-4.167,+8.333]pp: expansion gateFAIL.
Receipt/lineage/attempt/source auditsPASS;274schema-valid,1length stop,0transport errors.
No history fitted, no new inference scheduled; study app stopped and container list empty.

The code is frozen by hashes in `registered_plan.json`; do not edit/relaunch this run.
Source preflight passes561/623 arithmetic items under explicit parser/binding/rounding rules,
but does not establish semantic correctness. Postrun question/source/precision/unit flags
require human adjudication before another study. This is a provided-table pilot, not an
official ARQA score or validated business-accuracy result.

Offline reproduction (existing artifacts required, no model calls):

```bash
PYTHONPATH=. .venv/bin/python -m experiments.arqa_v2.study evaluate \
  results/arqa_v2/runs/deaee6167f9609bd2f045f46
PYTHONPATH=. .venv/bin/python research_ops/arqa_oracle_sensitivity.py
PYTHONPATH=. .venv/bin/python research_ops/report_arqa_v2.py \
  results/arqa_v2/runs/deaee6167f9609bd2f045f46
```

Tests: `tests/test_arqa_v2.py`11passed; `tests/test_source_receipt.py`5passed.
This is not a fresh whole-repository suite result.

See [results](../../docs/reports/2026-11-09/ARQA_CYCLE02_RESULTS_VA_QUYET_DINH.md),
[oracle findings and next path](../../docs/reports/2026-11-09/ARQA_CYCLE02_ORACLE_VA_PATH_TIEP.md),
[protocol](../../docs/reports/2026-11-09/ARQA_CYCLE02_PROTOCOL.md), and
[source receipt / human review](../../docs/reports/2026-11-09/SOURCE_RECEIPT_VA_HUMAN_REVIEW.md).
