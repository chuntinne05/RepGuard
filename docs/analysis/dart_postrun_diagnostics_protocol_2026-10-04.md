# Post-run diagnostic plan — 04/10/2026

Written while full collection is incomplete (1,896/2,352 records); only the
168-record judge quality pilot and completed self-report replays have been
analyzed. This is an exploratory diagnostic plan, not independent preregistration
of a superiority claim. It changes no collector, routing method, threshold,
budget, seed, or frozen gate. Require the completed full replay before analysis.

## Questions

1. Does the judge add useful information beyond the actual completion self-report?
   On all common valid records, report confusion counts, accuracy, balanced
   accuracy, Brier, raw-score AUC, agreement, corrections and newly introduced
   errors. Report paired generator-bootstrap CIs (5,000 draws, seed 410026).
   Report per-agent and clipped/unclipped strata descriptively. Clipping was not
   randomized; differences cannot identify the causal effect of clipping.
2. Are inference records complete, unique, protocol-matched and correctly aligned
   to task-agent cells? Do non-feedback-dependent routing controls have identical
   predictions under self-report and judge feedback? Any failure stops analysis.
3. Does changing feedback improve held-out routing outcomes at each frozen budget?
   Compare the same methods on paired task predictions, averaging audit seeds
   within task before generator bootstrap. Do not treat seeds as new tasks.
4. Is the bottleneck noisy policy selection or a weak candidate bank? Reconstruct
   each saved candidate bank from exactly its audited construction labels and
   verify its selected test actions against the saved trace. Only in this separate
   post-run analyzer, inspect complete selection/test gold to compute:
   - selected policy's finite selection-history value and estimation optimism;
   - RMSE of all candidate value estimates on the selection history;
   - test success if full selection-history gold chose a candidate (diagnostic);
   - best whole candidate on the test fold after seeing its outcomes (diagnostic).
   These gold-aware choices are never supplied to a deployed method, never
   substituted into primary results, and never called achieved routing scores.
5. Record wall-clock interruptions, sum of completed-call latencies, tokens,
   logical request attempts and duplicate request starts. Billing is not inferred
   from ledger count; lower-level transport retries are not fully logged.

## Interpretation and next decision

If judge feedback adds no routing gain, do not equate higher feedback accuracy
with a method contribution. If full-history gold selection cannot improve over
the simple full-budget learner, investigate candidate learning/generalization
before another audit-acquisition redesign. If a large selection-estimation gap
remains, examine budget splitting and max-selection noise. These are diagnostic
signals, not causal proofs. Any new algorithm or ablation needs its own frozen
development protocol, every tested variant reported, and later independent
confirmation. Do not access challenge or sealed MMLU outcomes here.
