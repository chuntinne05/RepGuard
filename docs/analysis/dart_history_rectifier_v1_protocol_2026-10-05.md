# History rectifier v1: locked sparse-audit development batch

Follow-up after old P0 failure and the predeclared FactorRidge family's independent
recomputation (10%: 71.60, Uniform 69.70, Paired 71.95). The gain/structure cloud
batch is still running; none of its remaining outcomes selects this design.
Preserve its primary endpoint. This is another explicitly adaptive public-normal
development batch, not an untouched confirmatory experiment.

## Mechanism and limits

Use historical judge scores as auxiliary information to estimate each agent's
average success, correcting their errors with sparse gold. This is global agent
selection, NOT a contextual router, and does not consume feedback from the new
test task. Main question: does verified imperfect history improve on gold-only
agent sharing at the same annotation budget?

Inspired by [PPI++](https://arxiv.org/html/2311.01453v2) and
[Cross-PPI](https://arxiv.org/html/2309.16598v2). These papers motivate rectification
and cross-fitting; their theorems do not automatically cover our shrinkage, finite
uniform-cell design, dependent agents and argmax policy. Do NOT call our estimator
unbiased, confidence-certified, a faithful PPI++ implementation, or novel merely
because it combines known components.

## Frozen inputs and budgets

Same 168 tasks, 14 agents, 56 generators, outer folds and 300 uniform audit masks
as previous protocols. Only outer TRAIN historical judge probabilities are passed
to the learner. They originate from the 2,352 already-completed real Modal Qwen3
14B judgments (`think=false`); validate full ledger identity and SHA. Invalid
judgments get p=.5 plus a separate invalid feature. No new judge/solver calls.
No sealed/challenge access. All gold learner inputs are NaN outside paid audits.

Gold annotation parity does not imply compute/USD parity: judge processing is
additional historical evidence with a sunk collection cost. Disclose that cost
and allow baselines the same evidence in later comprehensive comparisons.

## Fixed estimators: no hyperparameter search in this batch

For every outer training set, use previous hash-based three grouped folds to
cross-fit a ridge outcome predictor. Its agent features are intercept, model,
scaffold and agent indicators. Squared loss centered at .5; unpenalized intercept;
model/scaffold penalty 1, agent residual penalty 4. Prediction clipped [0,1].

The judge version adds exactly four features from already-known historical scores:
own p-.5, own indicator(p>=.9)-.5, row mean p-.5 across all agents, own invalid
indicator; each coefficient has penalty 1. No text or gold-derived task feature.
Each task gets predictions from a fit that excludes ALL gold of its generator.

Given cross-fitted predictions m_ia, define a regularized rectified score:

    s_a = mean_i(m_ia) + sum_{i audited for a}(Y_ia - m_ia)/(n_a + 2).

Do not clip final score before argmax. With constant m=.5, this exactly reduces
to Beta(1,1) Global. Cross-fitting keeps an audited task's own label out of its
prediction, but does not remove every source of adaptation or shrinkage bias.

Report ALL methods:

1. UniformAuditGlobal (exact saved actions).
2. **CFGoldFactor**: cross-fitted agent-factor proxy, same rectifier, no judge.
3. **CFJudgeFactor** (PRIMARY): cross-fitted factor+judge proxy, same rectifier.
4. RawJudgeRectifier: use raw p in rectifier, no calibration.
5. JudgeImpute: average CF factor+judge predictions, no residual correction.
6. FixedFactorRidge: full observed fit, agent residual penalty 4; structural control.

Also compare to existing same-cost PairedGlobal and the predeclared CV-tuned
FactorRidge from gain v1. CFJudgeFactor is fixed primary even if an ablation wins.
Ties use original agent order (numerical ties within absolute 1e-12 for new
estimators; original Global retains its exact arithmetic/argmax).
No picking a best method from outer test scores.

## Execution and reporting

All 300 cases (three budgets ×20 seeds ×5 folds), run once on a separate deployed
Modal CPU worker with Volume checkpoints, source/input hashes, case checksums,
retry≤2, timeout24h. Does not alter or cancel gain v1. Save actual predictions,
choices, cross-fit group membership and in-audit residual diagnostics.

Primary budget10%; paired seed-averaged generator bootstrap5000, seed1404.
Strong exploratory signal requires primary lower CI >0 versus BOTH Uniform and
Paired, AND report its incremental contrast versus CFGoldFactor and tuned
FactorRidge. Family comparisons and every budget retained. No A/A* acceptance
claim, no test-until-significant loop. Terminal completed_review_required.

Before real outcomes: tests for constant-proxy exact Global equivalence, own-label
cross-fit isolation, hidden-label injection invariance, no gold-derived judge
features, no test-feedback input, grouped partition isolation and checksum/resume.
