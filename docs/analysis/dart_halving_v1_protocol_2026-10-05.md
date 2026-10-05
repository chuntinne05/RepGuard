# Frozen candidate versus Sequential Halving: protocol

Locked before running the new baselines. This is a development stress test on the
already explored AppWorld public normal pool, not an independent confirmation.

## Question and scope

Does the unchanged paired CFJudgeFactor candidate (run `cd0b2656876f7f973d7b67ce`)
remain competitive with adaptive gold-only allocation? The old primary gate
(positive lower CI against both uniform and paired Global) remains failed.
This experiment cannot replace that endpoint or promote a different candidate.

168 tasks, 56 generator groups, 14 agents; reuse the exact five outer group folds,
20 audit seeds and per-case label budgets at 5%, 10%, 20%: 300 cases, two baselines
per case. Primary comparison budget remains 10%. All task-agent outcomes are real
archived executions. No new solver or judge calls. Candidate predictions are
immutable comparators; neither SH algorithm receives them, features, or judge scores.

## Algorithms, fixed without outcome tuning

Reference: Karnin, Koren, Somekh, ICML 2013, Algorithm 2,
[Almost Optimal Exploration in Multi-Armed Bandits](https://proceedings.mlr.press/v28/karnin13.pdf).
Sequential Halving allocates labels over elimination rounds and retains the half
with highest round empirical rewards. We use the following explicit finite-archive
adaptation, not a claim to reproduce the original stochastic-bandit theorem.

- Four rounds: 14 → 7 → 4 → 2 → 1; retain ceil(k/2).
- At a round with R rounds left, allocate floor(remaining budget / R / k)
  fresh rows per active agent. Carry rounding remainders forward. The final round
  allocates the entire remainder, with at most one additional label per agent.
- Eliminate using **current-round** empirical mean, not cumulative means.
- Ties and final extra labels use one random agent priority drawn before queries.
- IndependentSH: a pre-drawn independent permutation of training rows per agent.
- PairedSH: one pre-drawn permutation shared by all agents; surviving agents
  receive the same fresh rows in each round (except any final remainder).
- Never audit a task-agent cell twice. Fail closed if archive capacity is exceeded.
- Both methods consume exactly the original per-case gold budget, independently.
- RNG: NumPy default_rng seeded from first 16 SHA256 hex digits of
  `dart-halving-v1:{budget}_fold{fold}_seed{seed}`. Same priority across both methods.
- Only a paid training-label callback is exposed to the selection core. Evaluation
  reads outer-test gold after actions have been fixed. No generator overlaps folds.

## Reporting and stopping

Report all budgets/methods regardless of outcome; no additional tuning. Compare
frozen candidate to both SH variants, PairedGlobal, UniformAuditGlobal and
TunedFactorRidge. Compute generator-cluster bootstrap CIs (5,000, seed1404) after
averaging the 20 audit seeds, exactly as earlier batches. A new stress-test signal
requires lower CI >0 against both SH variants at 10%; this does not override the
original gate, adjust multiple adaptive comparisons, or establish A/A* publishability.

Archive every label query, reward, stage score, survivor set and agent choice.
Recompute decisions and summaries locally after fetching. Test exact budgets,
no duplicate queries, unqueried-label invariance, tied cases, known-best-arm
synthetic case, group separation, crash resume and terminal idempotence.

Run on a detached Modal worker: 1 CPU, 4 GiB, 24h ceiling, two infrastructure
retries. Atomic case files and checksums; commit Volume every 25 cheap cases,
at each budget completion and on exceptions. At most 24 cheap cases need repeating
after abrupt container loss. Stop after the fixed 300 cases and report honestly.

Gold-budget parity is not dollar parity: historical CFJudgeFactor additionally
uses 2,352 previously collected judgments (think:false). SH uses no judge.
