# DART implementation pilot: fixed-budget policy auditing

This protocol specifies an **exploratory** implementation study after the public
leaderboard capability analysis. It is not independent method confirmation. The
14-agent pool and 5 generator folds remain those frozen in commit e7e741e.
Capability analysis found 45 qualifying pairs, 82/168 for the retrospectively best
single agent and 134/168 for the diagnostic oracle. No router results have been
computed at this protocol's creation.

## First feedback source and data

Use official AppWorld 0.1.0 trajectories, archived 0.1.0 success labels and matching
0.1.0 public instructions. Never use newer task specifications without validation.
The first feedback source is **observed agent self-report in API request logs**:
the last `/supervisor/message` request is positive when its status is `success`
or absent (the completion default), negative for `fail`/`failure`, or negative
when no completion request exists. This reports a claimed completion, not a
verified successful API response. It is a deterministic extraction of actual
behavior, not a simulated response, gold-derived corruption, or an LLM judge.
No official state check, test text, difficulty or hidden skill label is an input.
A separate real-judge study will be needed; this pilot does not substitute for it.

## Outer and inner separation

Each outer test fold is held out by generator. Split its training generators into
construction and selection history by deterministic salted SHA256 ordering,
approximately half each. Construction history provides public instruction features
and a shared uniform random anchor audit. Selection history supports policy-value
estimation. Test outcomes are accessed only after each policy's actions are frozen.

Use 20 audit seeds (0..19), and total trusted-label budgets of 5%, 10%, 20% of the
outer training task-agent records (floor to integer). Reserve one third for the
shared construction anchor audit; the rest is selection-history auditing. Every
audit-aware method receives exactly the same total number of unique task-agent
labels. One AppWorld task-agent outcome costs one audit unit. Uniform anchor
sampling is shared across methods within a fold/seed/budget.

## Frozen policy class and signals

Policy candidates: all 14 constant-agent policies plus anchor-only contextual
policies with k=3,10,30 nearest construction tasks. Use word unigram/bigram TF-IDF
fit only on construction instructions. For a candidate agent with no nearby
audited label, shrink toward its anchor global mean with a Beta(1,1) prior.
Candidates see only anchors and task instructions, not selection-history gold or
self-report. They are frozen before selection audits.

For selection-history outcome proxies, estimate success given the binary
self-report using only construction anchors, partial pooling each agent's channel
to the pooled channel with strength 4. No hyperparameter search in this pilot.

## Compared methods

- **AnchorOnly:** best constant agent from shared anchor labels; reports actual
  anchor cost only and is not advertised as a full-budget comparison.
- **AuditOnly:** uniform selection audit, HT values with zero proxy, same candidates.
- **RandomHistory:** uniform selection audit and proxy plus audited residual correction.
- **UncertaintyHistory:** probabilities proportional to proxy residual-variance
  heuristic, with randomized floor and the same correction.
- **DART:** prioritize disagreement among proxy-plausible candidate policies times
  proxy residual uncertainty, with the same correction. Active candidates are within
  0.15 of the highest mean proxy score, plus the anchor baseline. Audit floor consumes
  20% of inclusion-probability mass. This acquisition is a heuristic, not optimality
  or adversarial robustness proved by a theorem.
- **ProxyGlobal / ProxyKNN:** history-only controls using observed self-report;
  no trusted labels, so report their information/cost difference explicitly.
- **GoldTrainSingle / GoldTrainKNN:** full-training-label diagnostics for learnability,
  never equal-budget deployment baselines or oracle upper bounds on all routers.

All audit designs select a fixed number of distinct records using randomized
pivotal sampling with known first-order inclusion probabilities. Value estimates
use `m + A/q * (y-m)`. They may lie outside [0,1]; no clipping into probabilities
or Beta pseudo-count updates. Ordinary iid/Bernoulli CIs are invalid for this
sampling design and will not be used. The policy guard/certification module is
deferred until its statistical assumptions are implemented and tested; this pilot
does not provide a deployment safety guarantee.

## Evaluation and interpretation

One selected agent per held-out task; no test-time access to other outputs or gold.
Report all budgets and all methods, mean exact success, paired rescue/harm and
generator-cluster bootstrap CIs after averaging predictions across audit seeds
for each task. Seeds are algorithmic variability, not extra independent tasks.
Pairwise intervals are exploratory and unadjusted. Primary pilot budget is 10%;
the three required contrasts are DART vs AuditOnly, RandomHistory, UncertaintyHistory.
If any CI includes zero, this pilot does not establish DART superiority. Even if
all pass, public-data reuse and tuning history prevent confirmatory claims.

Agent-invocation and trusted-label counts are not dollar/compute equivalence.
Historic bundles lack uniform token accounting. Include this limitation in every
reported outcome. Keep decrypted data and per-task derived outputs under ignored
results/; publish only code, protocol and permitted aggregate research findings.
Keep MMLU-Pro sealed holdout and AppWorld challenge outcomes closed.
