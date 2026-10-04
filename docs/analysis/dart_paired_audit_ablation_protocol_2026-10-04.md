# Prospective paired-audit mechanism ablation

Basis: completed self-report v3 diagnostics show DARTContrast candidate-value
RMSE 0.11365 and selected-value optimism 0.15703 at 10% budget. Using complete
selection-history gold to choose the same bank yields a diagnostic 74.35/168,
versus achieved 67.40; this is not a deployable score. The full judge replay is
still pending. No full judge routing outcomes informed this amendment.

## One question, fixed design

Does jointly auditing different agents on the same historical task reduce noise
in the policy comparison? Original independent-cell allocation did not optimize
joint inclusion covariance. Positive within-task dependence can help paired
differences; there is no guarantee it helps on this dataset.

Let K be the number of agents and B the label budget. Uniformly permute historical
task rows. Audit every agent on the first floor(B/K) rows, then B mod K uniformly
chosen agents on one more row. This uses exactly B distinct task-agent labels.
Every cell has q=B/(N K). Pairwise inclusion probabilities are known exactly,
including the partial final row. No outcome or judge score selects audited rows.

Add four explicitly named CONTROLS, not a new DART superiority claim:

- PairedAuditOnly: original construction anchors/candidate bank and budget split;
  change only selection audit design, with zero proxy correction.
- PairedHistory: same, using original calibrated feedback proxy.
- PairedGlobal and PairedKNN: all B labels on outer train using the paired design,
  then the same global means/kNN10 as full-budget uniform controls.

Keep 5 grouped folds, 20 seeds, budgets 5/10/20%, original anchors, candidate bank,
calibration, tie-breaking and all primary outcomes. RNG seeds: selection audits
22004+100*seed+fold; full-budget audits 44004+100*seed+fold. PairedAuditOnly and
PairedHistory share selected cells, as do PairedGlobal and PairedKNN.

Run once for each feedback channel, with judge analysis only after the full frozen
judge replay completes. Store new outputs, never replace v1-v3 or full judge v1.
Compare every new control to its matching prior control and report every cell.
Main mechanism contrast at 10%: PairedHistory vs RandomHistory. Practical checks:
PairedHistory vs DARTContrast, UniformAuditGlobal and PairedGlobal. Require all
four lower generator CI bounds above zero for an exploratory all-comparisons gate.
No repeated threshold/seed search; a negative result is retained.

Exact design variance implemented here takes the entire fixed outcome/residual
matrix as input for diagnostics and is verified by finite enumeration. It is NOT
an available online confidence bound, safety certificate, or novel theorem.

## Closest related work and limits

[SELECT-LLM v2, 28 Sep 2026](https://arxiv.org/html/2510.09418v2) chooses reference
annotations by output-similarity information gain. One reference can score multiple
model outputs; our AppWorld cost counts each task-agent audit. A faithful comparison
must reconcile these units, not silently call one all-agent row a single label.

[CABS](https://arxiv.org/html/2607.09015v1) observes the selected arm's true reward
online and surrogate rewards for neighbors. This differs from paid historical
audits. These four controls are not implementations of CABS or SELECT-LLM.
[Active Statistical Inference](https://proceedings.mlr.press/v235/zrnic24a.html)
is relevant established theory for selective annotation with prediction support;
our ablation does not claim to originate that idea.
