# DART gain/structure v1: bounded development experiment

Locked before this batch's outcomes, after observing the negative neural P0.
This is an explicitly adaptive research follow-up on public normal, NOT a new
untouched test set. Preserve every family and loss; no guarantee of improvement.

## Scientific motivation and prior art

The first P0 tested representation-conditioned routing with all historical train
labels. It did not test whether structured sharing across agent identities helps
estimate the best agent with sparse labels. Consequently this NEW protocol runs
both full-gold diagnosis and sparse-audit evaluation, regardless of full-gold gain.
The old stopped run and its gate remain unchanged.

Sources read before implementation:

- [Causal LLM Routing](https://arxiv.org/html/2505.16037v2): directly optimize a
  softmax-weighted utility/regret objective. Our small linear, multi-observation,
  fixed-cost adaptation is not an exact reproduction of that paper.
- [RouteLLM](https://arxiv.org/html/2406.18665v4): preference routing and shared
  model representations precede this work; neural/pairwise routing is not new.
- [Offline Multi-Action Policy Learning](https://arxiv.org/abs/1810.04778):
  policy learning and counterfactual value estimation must separate optimization
  from honest out-of-sample evaluation.

Subtracting a common anchor from linear ridge targets, with identical design,
penalty, and complete labels, gives the same ranking as independent outcome
regression. Include a numerical equivalence test; do not rename this algebraic
reparameterization as a new method. The direct-utility loss changes optimization.

## Frozen data and features

Same 168 tasks / 56 generators / 14 agents / five original outer folds, exact
300 UniformAuditGlobal masks (3 budgets × 20 seeds × 5 folds), and original
UniformAuditGlobal / PairedGlobal outcomes. No challenge, no MMLU sealed labels.
Use prior real MiniLM embeddings, verify input identity and artifact checksum.
Features at routing time are only instruction text and known agent identities.

Two contextual representations: normalized full 384-dimensional MiniLM (no PCA,
center fitted on each train partition), and training-only TF-IDF unigrams/bigrams
with max 4096 terms, log TF, smoothed IDF, row normalization. No test vocabulary
or IDF fitting. No task/generator ID as learner feature. Agent scaffold/model
metadata are parsed from frozen names, without outcome-dependent pooling.

## Families and fixed hyperparameter shortlist

1. **Global**: identical Beta(1,1) per-agent mean, exact original tie order.
2. **FactorRidge**: global score per agent, fit audited outcomes with squared
   loss and design [intercept, model indicators, scaffold indicators, agent
   indicators]. Center target at .5; do not penalize intercept. Shared model and
   scaffold coefficients have penalty 1; agent residual penalty either 4 or 16.
   This is a structured baseline, not contextual routing or novel DART.
3. **SemanticRidge**: per-agent centered MiniLM ridge residual around Beta mean,
   fit only that agent's observed labels; sum squared loss + alpha norm²,
   alpha in {1,10}; no additional intercept (Beta mean is the intercept).
4. **TextRidge**: identical learner with training-only TF-IDF instead of MiniLM.
5. **DirectUtility**: linear softmax policy on centered MiniLM, initial logits
   equal Beta means / .2; train residual W,b from zero. Fixed Adam lr .02,
   300 epochs, L2 sum over residual parameters lambda in {.0001,.001}.
   Utility table uses audited outcomes: m + A/q*(Y-m), m=training Beta mean,
   q=realized uniform sampling fraction. Subtract anchor's table column as a
   common per-task baseline; optimize negative mean expected signed utility.
   Never apply BCE to these unbounded values. This is a variance-prone plug-in
   training objective, NOT an unbiased value certificate when m/policy are fitted
   on the same labels. Outer test outcomes remain isolated.

Deterministic fits; DirectUtility is linear with zero initialization and full
batch optimization (no random restarts or extra ensemble search). All five family
predictions are reported, plus **Selected**, the primary candidate chosen across
Global and the best hyperparameter of each other family. Same grouped inner
3-fold split and seed-free hash assignment as preceding P0. Inner scores use
audited outcomes only, HT weighting conditional on within-fold audit count.
Fail closed if a required training/validation partition has no labels. Ties favor
Global then FactorRidge, SemanticRidge, TextRidge, DirectUtility; within-family
ties favor the FIRST listed parameter. Hyperparameters are never chosen from T.

Save outer probabilities/scores, choices, train fit diagnostics, inner scores,
chosen configurations and group membership to support causal-mechanism review.
DirectUtility probabilities are policy weights, NOT calibrated success estimates.

## Execution, endpoints and limits

- R0: full-label outer-train diagnosis, five cases. Interpret separately from R1.
- R1: all 300 original uniform-audit cases, including when R0 fails; this tests
  sparse-label estimation as a separate hypothesis (no changed old P0 gate).
- Primary: Selected at 10% versus both UniformAuditGlobal and PairedGlobal.
- Report all budgets/families and switches/rescues/harms. Exploratory paired
  5000-generator bootstrap after seed averaging, seed 1404. Strict signal flag:
  lower endpoint >0 for both primary comparisons. A positive point difference
  alone is a development improvement, not proof of superiority or A* readiness.
- Same known test history means a fresh independent benchmark is still needed,
  even if the new primary endpoint passes. No auto-opening of sealed data.
- Finish the whole fixed batch once; no repeated tuning until a favorable score.
  Terminal state `completed_review_required`, including losses.

Deployed Modal CPU worker, detached `.spawn()`, persistent Volume, atomic hashed
per-case checkpoints and ledger, bounded 24h calls/two retries, one worker at a
time. Skip verified completed cases after retry. Raw inputs/choices stay under
ignored results; aggregate report enters Git. No new expensive solver/judge calls
are required for this learner experiment. No Codex-dependent loop between R0/R1.

Tests before real data: audit-mask isolation, train-only vocabulary/centering,
ridge/anchor equivalence, signed objective shift invariance, agent factor metadata,
exact control reproduction, masked gold injection invariance and crash/resume.
Synthetic controls remain explicitly separate from empirical observations.
