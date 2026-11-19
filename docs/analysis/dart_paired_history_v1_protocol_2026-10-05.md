# Paired historical rectification v1: acquisition-only follow-up

Locked after uniform-history primary 10% result 72.00/168 versus Uniform69.70
and Paired71.95 (CI includes zero), before reading any new paired-history outcome.
Adaptive public-normal research; this is not independent confirmation.

## Single changed factor

Keep **exactly** the six fixed estimators, calibration features, regularization,
cross-fit groups, shrinkage denominator n_a+2 and tie handling of
[history rectifier v1](dart_history_rectifier_v1_protocol_2026-10-05.md).
Change ONLY paid audit acquisition: use all 300 saved original **PairedGlobal**
traces from `results/dart_paired_judge_v1/audit_trace_private.jsonl`.
They sample floor(B/14) complete task rows and B mod14 cells of another row.
Each trusted task-agent label costs one; still exactly the same B as uniform.
Never choose rows from their outcome or judge score.

Motivation: success covariance with react_gpt4o is positive for all 13 other
agents in a descriptive full-normal check (median sample covariance .05938).
Paired differences cancel some shared task difficulty. This observation motivates
the design; it does not prove this new estimator will win. The paired control
already exploits that covariance and must remain the main comparator.

Old UniformAuditGlobal name is replaced with **PairedGlobal** in this batch's
learner outputs. All other names/algorithms are unchanged. Compare the primary
CFJudgeFactor with PairedGlobal, UniformAuditGlobal, paired CFGoldFactor, and the
previous uniform CFJudgeFactor. Also retain uniform TunedFactorRidge as a control.

## Fixed endpoints

All 300 cases: 5 folds ×20 seeds ×5/10/20% audit budgets. Primary is CFJudgeFactor
at10%. Strong exploratory signal requires positive generator-bootstrap CI lower
bound against BOTH PairedGlobal and UniformAuditGlobal; report incremental judge
effect over CFGoldFactor and acquisition effect over uniform CFJudgeFactor.
5000 generator bootstrap samples, seed1404, after averaging audit seeds.
Every ablation retained; do not replace primary with the best outer-test family.

Judge predictions are available for historical TRAIN tasks only, from the same
2352 completed real calls. No new inference calls; no extra free gold; no test
feedback or sealed/challenge outcomes. No modifications to earlier results.

Validate exact original training/test order, indices, B and control choices for
every case. Record source/input hashes, predictions, cross-fit traces, checkpoint
checksums and saved audits. Cloud worker is detached, checkpointed, bounded24h
with2 retries, and completes exactly this batch then stops for review.

This changes sampling, not the correction formula or neural architecture. If it
improves only a point estimate, report that limitation. Even a positive exploratory
CI on this repeatedly used normal set does not establish novelty, deployment
safety, or an A/A* paper. Independent data and stronger evidence remain required.
