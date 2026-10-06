# Gold-only headroom diagnostic on two new RouterBench development slices

## Purpose and scope

After the frozen MATH500 pilot found a best fixed model equal to the six-model
per-question oracle on 48 questions, check whether two other preselected domains
offer genuine model complementarity before buying more judge feedback. This
diagnostic reads **archived scores only for selected development questions**;
it does not implement or validate a new method and makes no fresh model calls.

Sources are pinned LLMRouterBench revision/archive from the completed intake.
Choose `mbpp/test` (programming) and `finqa/test` (financial quantitative QA)
from the metadata inventory because they have 970 and 1,138 questions common
across 20 archived models. The descriptions are dataset names, not a claim that
the archive grader has been independently revalidated here. Exclude MMLU and
all previous sealed holdouts. Keep the full 20-model inventory pool, one
execution file per model; do not filter models by their score.

## Selection before score access

For each dataset, intersect the 20 verified metadata query hashes. Require the
advertised common coverage and one file/model. If any model file repeats a query
hash, exclude that hash from the **entire 20-model eligible pool** using metadata
only. Do not choose one repeated execution by score; report excluded counts.
Sort eligible query IDs by
SHA256(`repguard-headroom-dev-v1:` + dataset + `:` + query ID), select first
**200**. All other question scores are out of scope. Packet fixes dataset,
model order, member names, metadata SHA256, selected query IDs and record
positions before worker reads any score.

Worker validates the pinned 1,283,503,080-byte archive SHA256; streams only
the 40 selected JSON files without extracting tar paths. It retains only
`records.item.score` at the selected positions, refusing missing, repeated,
nonfinite or out-of-range scores. If an archive score is fractional in [0,1],
preserve it as a reward; do not silently threshold. All other score values are
ignored and cannot enter selection or analysis. Private matrices/checkpoints
stay under ignored `results/` and a Modal Volume. Public reports contain only
aggregates, never per-question score.

## Fixed statistics and stop rule

For each dataset report development mean reward per model, best fixed model
mean, per-question oracle mean, headroom = oracle minus best fixed, fraction
of questions where some model exceeds the best fixed model, and number of
questions with a strict rescue. Use 5,000 question bootstrap resamples,
seed 1404, of the paired per-question oracle-minus-best-fixed difference
with the best fixed model held fixed. This interval conditions on the chosen
development sample and selected best model; it is descriptive, not a test
guarantee or model training refit.

One `headroom` value cannot prove a learnable router: the oracle sees gold of
each question. Small headroom means there is little possible accuracy gain
from selecting among these archived outputs; large headroom only supports a
later, separate feedback feasibility pilot. This run stops after the two
200-question diagnostics regardless of result. No judge collection and no
final evaluation are automatically opened. Unselected questions remain
unread by the worker and available for a separately locked future protocol.
