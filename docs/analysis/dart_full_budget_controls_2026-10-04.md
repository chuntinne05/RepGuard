# Additional equal-budget controls, locked before v3

The first two exploratory runs compare acquisition/selection strategies within
one construction/selection split. This does not establish superiority over a
simple learner allowed to spend its entire label budget fitting an agent selector.

Add UniformAuditGlobal and UniformAuditKNN: sample exactly B distinct historical
task-agent cells uniformly over all outer-training tasks (seed 44004+100*seed+fold).
Use only these labels to fit Beta(1,1) global means, or the same kNN10 implementation
with instruction TF-IDF fitted on outer-training tasks. Each method uses B labels
and one selected historical agent invocation on each held-out task. They share
one sampled audit set with each other. No construction/selection split is needed
because they do not estimate and maximize values over a candidate policy bank.

Keep DART, DARTContrast, every original baseline, all budgets and seeds unchanged.
Write v3 separately. Require both additional contrasts to have a positive lower
cluster CI before any exploratory method gate passes. This is a stricter
comparison, not a new independent validation dataset. Report negative results.

These controls are still not replacements for faithful CABS, active model
selection, contextual router, and compute-aware baselines in a final paper.
