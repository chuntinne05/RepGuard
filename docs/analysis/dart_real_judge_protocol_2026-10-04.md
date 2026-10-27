# Prospective real-judge quality pilot

Locked after the self-report v2 analysis, before any judge inference. This is a
new feedback channel on the same development tasks, not independent confirmation.

## Fixed collection

- Existing Modal L4/A10 Ollama endpoint; qwen3:14b digest
  `bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8`.
- No thinking; temperature 0, seed 1404, context 8192, output cap 128 tokens.
  This stage measures an inexpensive feedback source, not solver reasoning.
- Judge sees public version-0.1.0 task instruction and actual environment I/O.
  No agent identity, official checks, gold outcome, reference code, or hidden state.
- Logs over 12,000 characters: first 2,000 plus last 10,000, marked incomplete.
  Store full log hashes and coverage. No claim that truncated traces are sufficient
  to establish true success. Response: probability that all requirements passed.
- Full order: within each of 14 frozen agents, sort 168 IDs by SHA256 of
  `dart-judge-v1:{agent}:{task_id}`, then interleave agents. First 12 per agent =
  168 pilot calls. All 2,352 cases and their prompt hashes frozen before call one.
- Collector has no outcome-matrix dependency. Separate analyzer reads gold only
  after the pilot. Append-only ledger, OS exclusive lock, hash-checked resume.
  Transient retries may incur duplicate server work and are not free billing.

## Fixed quality gate and stopping rule

At 168 records, require at least 95% valid structured responses; balanced accuracy
at probability threshold 0.5 at least 0.60; and the lower 95% percentile bootstrap
bound above 0.50. Bootstrap 5,000 times by task generator (seed 141004), preserving
all sampled task-agent rows per selected generator. At least 95% of bootstrap
draws must contain both classes. Otherwise stop and diagnose; no threshold or
prompt tuning followed by relabeling the same pilot as confirmation.

Passing authorizes completing the already frozen 2,352 matrix, not a claim of
usefulness for routing. Failure stops expansion. Do not rerun invalid responses
to improve validity rates. Transport retries do not select on response content.
Report accuracy, balanced accuracy, Brier score, class counts, clipped fraction,
token counts, call latency, and both successful and failed gates.

The earlier self-report DART superiority gate remains failed. An informative judge
is necessary evidence for this channel, not sufficient evidence for a strong DART
paper. Further equal-budget replay, relevant baselines, untouched replication,
cost measurement, and defensible statistical guarantees remain separate gates.
