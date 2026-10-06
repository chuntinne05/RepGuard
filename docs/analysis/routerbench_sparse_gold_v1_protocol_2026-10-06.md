# MATH500 sparse-gold development replay v1: protocol

## Scope and identity

Reuse only the verified pilot `bad5a513bd5d227711eb1e0d`: 48 development questions,
six fixed models, 288 archived solver outcomes and 288 real Qwen3-14B judgments.
No fresh solver/judge calls, no additional questions or sealed holdout access.
This is a development replay, not independent confirmation, a contextual router,
or a measurement of new human annotation expenditure. Protocol and code hashes
are recorded in the immutable input packet before replay.

## Splits, budgets and randomness

Keep query order and outer folds `query_index % 4`: 36 history questions and
12 evaluation questions. Gold access is through a bounded callback on history
cells only. All gold used for calibration, correction or selection is charged.
Primary budget is 10%; secondary budgets are 5% and 20%. Use
`ceil(fraction * 36 * 6)` unique cells: **11, 22, 44** (actual fractions
5.093%, 10.185%, 20.370%). Twenty seeds 0..19; case seed `1404+1000*fold+seed`.
There are 240 cases and ten selections/case.

Uniform audits use a random permutation of all history cells, truncated to the
budget, without replacement. Paired audits use a random history-row order:
complete six-model rows first, then one partial row in random model order. No
labels are filled in for unaudited cells. Audit masks are nested across budgets.
Tie priority is a common model permutation from `case_seed+991`, with score ties
defined by absolute tolerance 1e-12; no dependence on gold or observed winners.

## Fixed candidate and controls

Model-only design: intercept and six one-hot model IDs. Judge features are
`p-.5`, `I(p>=.9)-.5`, row mean `p-.5`, invalid indicator. No task encoder or
heuristic model/scaffold parsing. Target `y-.5`; ridge penalties intercept 0,
model 4, judge features 1; predictions clipped to [0,1]. Same features and
penalties as the completed pilot; no hyperparameter search.

For calibration on history, use three inner folds `local_history_index % 3`.
Only audited labels from other inner folds enter each predictor. An empty
training partition produces an explicit .5 predictor, recorded in the trace.
Never use unaudited or evaluation gold to fill that partition.

The frozen primary candidate is **CFJudgeRectifier** on paired audits:
mean history out-of-fold prediction plus sum of audited out-of-fold residuals
per model divided by `(model_audit_count+2)`. This is a regularized estimator;
no unbiasedness or adaptive-sampling guarantee is asserted. CFGoldRectifier
removes judge features; a constant .5 proxy reduces exactly to Beta(1,1) means.

Ten methods:

- UniformGlobal: Beta(1,1) mean on uniform cell audits.
- PairedGlobal: same mean on paired audits.
- GoldRidge: fit model-only ridge to all paired audited labels; rank its history
  mean prediction. Does not access judge feedback.
- CFGoldRectifier: cross-fitted model-only predictor plus regularized correction.
- RawJudgeRectifier: raw judge prediction plus the same paired residual correction.
- CalibratedJudge: mean cross-fitted paired judge prediction, no correction.
- CFJudgeRectifier: primary candidate, as above.
- IndependentSH and PairedSH: exact-budget finite-archive Sequential Halving.
- RawJudge: history mean raw feedback; **zero gold**, a separate cost reference.

All methods except RawJudge receive exactly B gold cells. The six paired fixed
methods share a mask to isolate estimation; the uniform and two adaptive controls
have their own acquisition paths. Shared-mask ablations reuse the same replay
reads, not six newly paid real annotations. Only RawJudge, RawJudgeRectifier,
CalibratedJudge and CFJudgeRectifier consume judge information.

## Low-budget SH adaptation

Six arms require three stages with active counts 6, 3, 2: the minimum feasible
budget is 11, rather than the conservative `K*ceil(log2 K)=18` bound of the
earlier implementation. Allocate complete blocks each nonfinal stage using
`max(1, floor(remaining/(stages_left*active_count)))`, reserve at least one
observation per arm for future stages, carry remainders forward. The last stage
spends every remaining cell, with partial-block arms ordered by common tie
priority. Rank by **stage-only** mean, retain ceil(active/2), and never requery a
cell. Paired SH shares the task order across arms; IndependentSH has separate
orders. Report stage allocations. This finite-budget adaptation does not inherit
the original IID theorem; old AppWorld sources/results remain unchanged.

## Evaluation and diagnostic access

Lock all model choices before reading evaluation outcomes. Each method selects
one model for all 12 held-out tasks; evaluation feedback is not passed to the
selector. Record unique audit IDs, labels, scores, choices, cross-fit training
rows and SH stage traces in private checkpoints.

After decisions, fit a separate diagnostic predictor on the same B paired gold
cells and evaluate Brier/residual variance on the held-out tasks. Evaluation
judge scores may enter this **diagnostic only**, never the selection decision.
For each budget, average diagnostic quantities over 20 seeds. The variance ratio
uses the mean over seeds of the sum of sample variances of 15 pairwise residual
differences, divided by the corresponding gold outcome variance sum. It does
not reuse the pilot's full-gold calibrated predictions.

Report success/48, accuracy, differences, rescue/harm, model-choice frequencies,
and regret versus the post-hoc best fixed model on the 48 evaluation questions
(reference only, not a deployable control). Also report diagnostic Brier, ratio,
empty-calibration partitions and paid labels/model. No omitted negative outcome.
After choices, report full-gold TRAIN-best agreement, per-model gold accuracy,
per-question oracle and outcome disagreement as descriptive pool references;
none enter training, acquisition, method choice or the gate.

## Uncertainty and development gate

Average seed outcomes within each question first. Use 5,000 question bootstrap
resamples, seed 1404, paired across methods. Diagnostic bootstrap resamples the
same question indices across seeds. These intervals condition on fitted learners
and the 48 observed questions; they do not refit training or account for previous
research adaptivity, near-duplicate groups or independent confirmation.

At primary 10%, development expansion gate requires CFJudgeRectifier to have a
strictly positive lower 95% bootstrap bound and a point improvement of at least
**1 percentage point against each** of UniformGlobal, PairedGlobal, GoldRidge,
CFGoldRectifier, IndependentSH, PairedSH. Gate remains FAIL if any condition is
unmet; no switching candidate, budget or contrast after results. It is a screening
rule with multiple exploratory comparisons, not a familywise error guarantee.

Automatically stop after 240 cases and local independent recomputation. No
automatic larger judge collection. If PASS, complete prompt-only grouping and
precision/power planning before locking a new study. If FAIL, report whether
calibration/variance or selection failed and do not tune on this pool to force
a positive interval. Preserve all prior failed gates.

[Verified pilot](routerbench_pilot_assessment_2026-10-06.md) ·
[Next evidence plan](routerbench_next_evidence_plan_2026-10-06.md) ·
[Sequential Halving source](https://proceedings.mlr.press/v28/karnin13.pdf)
