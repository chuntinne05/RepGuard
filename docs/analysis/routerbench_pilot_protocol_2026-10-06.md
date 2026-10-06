# External real-judge development pilot: locked protocol

## Scope

Run 288 genuine Qwen3-14B judgments of archived MATH500 executions: 48 development
questions ×6 models. This tests feedback quality and feasibility; it does not
establish DART routing superiority or replace previous failed scientific gates.
No fresh solver executions, no MMLU payloads, no existing sealed holdout access.

Source inventory `c387f6364d2266bf1bf370a9` covers467,023 metadata records in649
files; 51 MMLU files excluded. MATH500/test has500 common questions across20models.
Archive SHA256 remains pinned by the intake protocol. Root/HF license declaration
was absent in checked metadata; retain raw material privately, no redistribution.

## Selection before reading gold

- Fixed six models: Qwen3-8B, DeepSeek-R1-0528-Qwen3-8B, Llama-3.1-8B-Instruct,
  Qwen2.5-Coder-7B-Instruct, Fin-R1, gemma-2-9b-it. These IDs cover general,
  reasoning and specialist variants; no selection by observed success.
- Require one source file per model, all selected query hashes present. Refuse
  duplicate selected executions or missing output; do not replace according to gold.
- Normalize query using NFKC/casefold/whitespace collapse. Development bucket is
  first8hex(SHA256(`routerbench-split-v1:`+queryhash)) modulo10 <4. Order development
  queries by SHA256(`routerbench-pilot-v1:`+queryhash), take first48.
- Exact duplicate questions are grouped by hash. Near-duplicate/template grouping
  is not yet certified; this is explicitly a development pilot, not final evaluation.
- Model IDs are explicit features; no model/scaffold parsing from names. This is a
  model-only adaptation, not unchanged confirmation of the AppWorld factor model.

## Genuine collection and input separation

CPU preparer streams only query/output string fields. Prefer raw_output, fallback
prediction. Judge input includes problem and candidate answer only, no reference,
score, model identity, evaluator result or answer-key-derived proxy. The GPU worker
mounts sanitized pilot inputs and Ollama models, **not the raw archive**.

Judge `qwen3:14b`, expected digest
`bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8`, think=false,
temperature0, seed1404, context16,384, maximum128 output tokens, strict JSON probability.
Record actual Ollama version, GPU, prompt hashes, response, token counts and durations.
No claim that think=false is the optimal judge setting; it is fixed for this pilot.

Problem >5,000 characters causes a preparation stop. Candidate answer >10,000 chars
uses first1,500 and last8,500 with an explicit omission marker. Record clipping;
never silently equate incomplete reasoning with verified correctness.

Two attempts maximum/case, up to576 initiated requests. Persist each intent before
dispatch; interrupted unknown-usage attempts count against that limit. Record all
responses/errors/retries. After two failures, probability=.5 with invalid flag;
do not fabricate a model response. HTTP timeout180s, GPU timeout4h with two infra
retries, CPU orchestrator timeout24h. Atomic checkpoints and Volume commit each
attempt/case; detached worker survives the local/Codex session ending.

Only after288 judgments are complete does the CPU evaluator retain the selected
pilot gold scores. Positions were fixed by the gold-blind preparer; all other gold
values traversed by the streaming tokenizer are ignored. The archive is not
exposed to calibration/selection code or GPU inference.

## Fixed diagnostic and decision rule

Gold is the archived binary objective MATH500 score (answer matching/symbolic
grading in upstream evaluator). It is not a human-certified flawless answer key.
This pilot does not rerun symbolic grading; report that provenance explicitly.

- Four cross-fit folds: frozen query order modulo4; all six model outcomes for a
  question stay together. Calibration only sees labels of the other36 questions.
- Fixed model-only ridge: intercept unpenalized, six model indicators penalty4;
  four judge features penalty1: p−.5, I(p≥.9)−.5, rowmean(p)−.5, invalid indicator.
  Target y−.5, clip predictions to[0,1]. Control removes all judge features.
- Report raw/calibrated/gold-only Brier. Main mechanism diagnostic: sum of sample
  variances of15 pairwise residual differences divided by sum of sample variances
  of15 raw outcome differences, across48 held-out question predictions.
- 2,000 question bootstrap resamples, seed1404, fixed cross-fit predictions. This
  does not refit calibration or provide a deployment guarantee. Report uncertainty.
- Operational pass: ≥95% valid probability records AND ≤50% clipped answers.
- Expansion signal: operational pass AND variance ratio≤.90 AND upper95%CI<1.
  This is a screening criterion, not a claim of statistical confirmation of DART.
- Automatically stop after this pilot and analysis, even if signal passes. No
  unlabeled expansion or final test opening. Preserve negative outcomes and lock
  a separate next protocol before larger collection.

All pilot gold is used for cross-fit diagnostic, unlike a10% gold-budget routing
experiment. Never compare these Brier/variance numbers to prior routing success as
if they were equal-budget accuracy results. Token/duration logs quantify recorded
inference usage; unknown attempts and actual Modal billing remain separate.

Sources: [official code](https://github.com/ynulihao/LLMRouterBench/tree/c77cb0506949d8f959e97967d2fefca0e8ff1b05),
[MATH500 evaluator](https://github.com/ynulihao/LLMRouterBench/blob/c77cb0506949d8f959e97967d2fefca0e8ff1b05/evaluation/MATH500/math500.py).
