# Prospective amendment: DARTContrast, after first exploratory failure

The first self-report pilot completed all 300 fold/budget/seed combinations and
1,200 audit-policy runs. At the primary 10% budget, DART obtained mean 55.5/168,
AuditOnly 62.85, RandomHistory 64.4, UncertaintyHistory 65.5. The three primary
paired CIs for DART were below zero. These are mean counts across audit seeds,
not fractional task outcomes or independently replicated trials.

Diagnosis before v2: DART concentrated audit mass on proxy-plausible policies but
allowed all 17 candidates to win the value comparison. At 10% budget, 83/100
selected policies were outside its acquisition active set, versus 42/100 with
random history. Mean audit effective sample size fell from 125.4 uniform to
43.38 under DART. This is consistent with high-variance selection error; the
observational diagnosis alone is not a causal proof.

**Change locked before v2:** add DARTContrast, leaving v1 recorded. Allocate against
all selectable policy differences, with a 24-iteration dual-weighted design search.
The objective is the largest diagonal residual-second-moment term across policy
pairs. It is a design surrogate; it omits joint-inclusion covariance under pivotal
sampling and is not advertised as exact variance or a theorem. Uniform allocation
is an eligible design and retained if no proposal improves this predicted objective.
All prior budgets, splits, anchor labels, seeds, priors, candidate policies and
comparators stay fixed. No test result enters acquisition. The change addresses a
specific mismatch, not an unrestricted threshold search.

Run into `results/dart_audit_selfreport_v2`, with `--primary-method DARTContrast`.
Report every v1 and v2 method/budget and the same three contrasts. This is further
development on already-inspected public tasks, not new confirmation. Improvement
in the acquisition objective does not imply improved task success. The fresh
real-judge stage and independent task/pool replication remain necessary.
