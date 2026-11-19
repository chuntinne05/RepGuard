# RepGuard real MMLU-Pro Week 3 protocol (registered before outcome analysis)

Date: 2026-09-29. The legacy Week 2/3 simulator outputs remain exploratory and
are excluded from claims based on this protocol.

## Dataset and sampling

- Source: local parsed copy of `TIGER-Lab/MMLU-Pro`, 12,032 questions in 14
  subjects. The run manifest records selected task IDs and a dataset task-ID hash.
- Hash split seed 42: train/calibration pool 60%, dev 20%, held-out test 20%.
- For each subject select, without using answer labels, 100 questions from
  train/calibration for reputation history, 50 from dev to calibrate feedback
  reliability, and 70 from test for outcomes. A subject shortfall is recorded in
  the manifest rather than silently replaced from another split.
- Four configured Ollama models answer the same questions at temperature 0,
  `think=false`, `num_predict=64`, with an Ollama JSON-schema enum constrained
  to the available answer letters. The exact model digests are saved separately.
  This is a controlled zero-shot direct-answer protocol, not a reproduction of
  the benchmark's published chain-of-thought/few-shot leaderboard settings.
- Predictions are append-only and contain task ID, split, model, prompt hash,
  raw response, extracted answer, tokens, and latency. Ground truth is never
  sent in the prompt or stored in the prediction ledger.

## Capability audit

- Score each model on the 70 held-out test questions per subject, with Wilson
  intervals for accuracy. Select a candidate specialist from the disjoint
  history split, then compare it with each of the other three models on matched
  test questions using paired bootstrap intervals.
- A subject winner is *confirmed* only when its paired test-accuracy advantage
  over every other model has a 95% bootstrap interval strictly above zero.
  These intervals are exploratory across 14 subjects; the full comparison
  matrix is reported instead of treating the gate as a formal multiplicity-
  adjusted hypothesis test. A second confirmed winner is
  required before asserting robust skill heterogeneity.
- As a diagnostic, route each subject to the model selected on history and
  compare its held-out test accuracy with a single global model selected on
  history. Also report the per-subject best model chosen using test labels as
  an explicitly optimistic ceiling, never as a deployable baseline.

## Q x T characterization

- For each target subject, reuse exactly the same held-out questions and model
  answers across all feedback-quality and source-subject conditions.
- Source-subject strata are `same`, `related`, and `unrelated` according to the
  fixed metadata taxonomy. The clusters are life science (biology, chemistry,
  health), physical/technical (computer science, engineering, math, physics),
  social/behavioral (business, economics, psychology), humanities (history,
  law, philosophy), and general (`other`). `Related` means distinct subjects
  within one cluster; `unrelated` means different clusters. All available
  sources in each stratum are run. A
  target with no related source (currently `other`) is excluded from the full
  three-stratum factorial analysis, but remains in capability audit.
- Historical feedback is generated from real model-answer correctness and then
  corrupted at Q = oracle, symmetric 25% flips, symmetric 50% flips, or 40%
  false-positive bias on incorrect answers. The last regime is directional and
  is interpreted separately from symmetric noise. Corruption seeds: 42, 123,
  456. Calibration feedback is corrupted independently on disjoint dev tasks.
- Compare Uniform, GlobalBeta, independent SkillConditioned, ZeroEvidenceGate,
  FixedBorrow with the same transfer weights as ECRT, ECRT, and ECRT ablations
  without feedback calibration, transfer, and uncertainty discounting.
- Primary measures: per-task team accuracy, binary-outcome Brier score for
  agent competence predictions, mean absolute error against held-out
  per-agent subject accuracy, and success rate when exactly one agent is
  correct. Unknown answers abstain from voting; exact vote ties are resolved
  by a deterministic hash of task ID and answer letter, independent of agent
  order. Report source/target pairs and answer validity.
- For inferential summaries, average source pairs and corruption seeds within
  each target subject. Bootstrap target subjects for 95% intervals. Report
  paired Q contrasts, paired T contrasts, and Q x T differences in differences.
  This is a deliberately conservative analysis with approximately 13 clusters;
  narrow effects may remain unresolved.
- Primary method contrasts are ECRT versus FixedBorrow and independent
  SkillConditioned in the *related-source, 25% symmetric-noise* regime, with
  ECRT versus its no-reliability ablation isolating feedback calibration.
  Clean same-subject utility is checked for regression. Other cells describe
  the regime map and will not be mined selectively for a superiority claim.

## Decision rule

The Week 3 gate is not passed by a file existing or by a threshold applied to
unpaired means. It requires (1) valid real-answer traces, (2) a credible
heterogeneous pool, (3) a paired Q x T analysis without target-domain
confounding, and (4) an honest comparison to the strongest relevant baseline.
If the pool lacks robust heterogeneity, revise the pool before claiming a
reputation-transfer effect. If ECRT does not add value over simple conditional
trust or fixed borrowing, center the paper on the reproducible empirical
finding and do not make a method-superiority claim.

## Amendment after the initial 70-question-per-subject capability pilot

Date: 2026-09-29. The four-model test pilot completed all 14 subjects without
invalid answers. Several provisional winners differed from the runner-up by
only 2-3 of 70 questions. To improve precision, collect **every remaining
question in the pre-existing held-out test split for all 14 subjects**, not
only the subjects with a favorable result. The original sample and manifest
remain unchanged; `test_extension.json` records the added task IDs and reason.
The final capability audit and Q x T analysis will use the full held-out test
split (2,416 distinct questions per model) and will label this expansion as a
post-pilot protocol amendment. No history or calibration task is moved into
the test split.
