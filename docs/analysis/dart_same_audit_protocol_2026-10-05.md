# DART: controlled same-audit forensics — 2026-10-05

Status: fixed before running the new counterfactuals. Exploratory development on
already inspected public AppWorld normal data; not preregistration or confirmation.

## Question and invariants

Separate proxy representation, estimation, candidate selection, and use of paid
labels. Reuse all 5 generator folds × 20 seeds × 3 budgets (5%, 10%, 20%), both
self-report and completed real-judge feedback, and the RandomHistory and
DARTContrast acquisition designs. No new solver or judge inference. Never access
sealed MMLU420 or AppWorld challenge outcomes. Preserve original outputs.

For each of 1,200 channel/design/fold/seed/budget cases, reconstruct the original
bank, every inclusion probability, sampled indices and actions. Require exact
probability hash, sample, selected policy and held-out prediction agreement before
computing any counterfactual. Keep C/S/T splits, C anchors, S audit labels, budget,
tie rule, candidate routes and original acquisition probabilities fixed.

## Locked variants (12; 14,400 policy selections)

1. Original: categorical partial-pool proxy + HT correction, 17 policies.
2. ZeroHT: zero proxy, same correction and 17 policies.
3. AgentPriorHT: construction-only Beta(1,1) global agent means as proxy.
4. BinaryRidgeHT: ridge least-squares calibration of binary feedback.
5. ContinuousRidgeHT: identical calibration using continuous judge probability.
6. RawHT: raw continuous probability (binary self-report in that channel).
7. Binary14HT: Original estimator, only the 14 constant-agent candidates.
8. BinarySN: Original proxy, self-normalized residual correction.
9. ZeroSN: zero proxy, same self-normalized correction.
10. SGlobal: Beta(1,1) empirical agent means on the exact paid S labels.
11. CSGlobal: identical learner after pooling exact paid C and S labels.
12. CSStratifiedHT: constant agents; combine gold-only HT values from C and S
    with stratum task-count weights. No fitted proxy.

Ridge form: prediction = clip(agent intercept + shared slope × (score − 0.5),
0,1). Fit only finite construction labels, minimizing squared error plus
1 × slope² + 4 × sum((agent intercept − construction pooled Beta(1,1) mean)²).
All hyperparameters fixed here; no test-driven tuning. Missing score disallowed
for this complete-valid-ledger ablation. BinaryRidge and ContinuousRidge must be
identical in the self-report channel. Continuous versus binary ridge isolates
representation **within this calibrator**, not all possible continuous methods.

HT = full proxy mean + sum(observed residual / q) / N. SN = full proxy mean +
sum(observed residual / q) / sum(observed route-match weights 1/q); with no
route-matching audited cells, residual correction is zero. SN can be biased;
no finite-sample safety or optimality claim. SGlobal/CSGlobal intentionally do not
correct unequal inclusion: they diagnose empirical label use, not unbiasedness.
The adaptive design makes naive reverse cross-fitting invalid; not done here.

## Analysis and interpretation

Primary budget 10%; report all budgets and all variants, including losses.
Paired task differences averaged over audit seeds, then 5,000 generator-cluster
bootstrap draws. CIs exploratory and unadjusted; no claims of independent
confirmation or multiplicity-controlled superiority. Compare against Original,
and prespecified mechanism pairs: ContinuousRidge–BinaryRidge, Binary14–Original,
BinarySN–Original, ZeroSN–ZeroHT, CSGlobal–SGlobal. Compare every variant with
existing UniformAuditGlobal; report PairedGlobal separately as a strong external
control, whose audit set differs.

Offline diagnostics may read full S gold **only after actions are fixed**:
candidate RMSE, selected optimism, policy-selection regret, proxy Brier, number
of paid labels matching the chosen route and effective weights. Never feed these
diagnostics back into learners. CS variants target C∪S; do not compare their
training RMSE against S-only estimators as if targets were identical.

One-factor changes identify the effect on this replay of that implementation
choice. They do not establish a universal cause, LLM mental process, or guaranteed
fix. The protocols already inspected this dataset, so any winner still requires
an independent locked evaluation and relevant external baselines.

## Primary literature informing the investigation

- [PPI++](https://arxiv.org/html/2311.01453v2): reliability of a corrected estimator
  does not imply efficiency; tune contribution of predictions. Its asymptotic iid
  guarantees are not automatically valid for this adaptive pivotal design.
- [Cross-PPI](https://arxiv.org/html/2309.16598v2): motivates efficient reuse of
  labeled data; its iid assumptions require a separate adaptation here.
- [Confident off-policy selection](https://proceedings.mlr.press/v130/kuzborskij21a.html):
  motivates studying normalization and selection uncertainty. Our SN ablation is
  not a reimplementation of their confidence-bound algorithm.
- [Active Statistical Inference](https://proceedings.mlr.press/v235/zrnic24a.html):
  calibrated predictions and active annotation alone are established prior art.
