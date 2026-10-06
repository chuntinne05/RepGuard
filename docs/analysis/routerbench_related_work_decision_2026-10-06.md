# RouterBench: literature check and decision after the FinQA pilot

Status: research note written while the fixed 960-judgment FinQA pilot is in
progress. No pilot outcome has been inspected to change its protocol. This note
does not register a new experiment or claim a validated method.

## Closest prior work

1. [Ao et al., *Best Arm Identification with LLM Judges and Limited Human Audits*
   (2026 preprint)](https://arxiv.org/abs/2601.21471) study potentially biased
   LLM-judge scores, selectively purchased gold labels, inverse-propensity
   residual correction, confidence sequences, and adaptive attention to
   unreliable contexts and close arms. Their abstract and method already cover
   much of a generic "judge + adaptive gold audit" contribution. Section 6 says
   all of their reported experiments use synthetic data, leaving room for a
   carefully controlled real LLM-execution evaluation; this is an empirical
   opportunity, not proof of new algorithmic novelty.
2. [Ma et al., *Best-Arm Identification with Generative Proxy* (2026
   preprint)](https://arxiv.org/abs/2607.06879) study proxy-assisted best-arm
   identification with residual-variance certification and elimination. Their
   exact guarantee assumes Gaussian rewards and proxies, independent arm
   sequences, and a known proxy mean. FinQA here has binary archived scores,
   finite shared questions across models, and an estimated judge mean; the
   guarantee cannot be imported unchanged, but PROBE is a relevant comparator.
3. [Angelopoulos et al., *Prediction-Powered Inference*
   (2023)](https://arxiv.org/abs/2301.09633) established the broader idea of
   combining plentiful predictions with scarce labels. Residual correction
   alone is not a novel contribution.

These are primary papers, not verified independent replications. This search
is a novelty and baseline check, not a claim that either implementation works
on RouterBench or that our method beats it. Ao et al. formulate online arm
sampling with observe-then-audit, whereas our current replay is a fixed
archived question-by-model matrix. Any adapted comparator must state that
difference and preserve its access and budget assumptions.

## Consequence for the current project

The fixed FinQA pilot asks only whether real judge feedback carries usable
information on 48 selected development questions and 20 archived model
executions. Its gate requires >=95% valid responses, >=90% complete boxed
answers, paired residual-variance ratio <=0.90, and bootstrap upper bound <1.
That result cannot establish best-arm selection gain, cost savings, or
generalization. The previously failed MATH500 sparse-gold and AppWorld gates
remain failed regardless of the pilot's result.

If the FinQA gate fails, stop this version of judge collection, inspect
extractor/judge error and cost, and report the negative result. A revised
judge, task, or solver pool needs a new protocol and untouched evaluation.

If the gate passes, register a *separate* sparse-gold development replay before
reading its decisions. At each outer fold, a learner sees only historical
question judge scores, a bounded callback for paid historical gold cells,
and prompt metadata available at decision time. It never sees held-out gold or
unpaid historical gold. Compare at the same gold-cell budget and report the
full judge spend:

- judge-only selection and best fixed reference;
- uniform and paired gold-only selection, plus exact-budget successive
  halving;
- raw-judge residual correction and calibrated judge;
- a propensity-corrected proxy-aided audit comparator inspired by Ao et al.,
  with logged nonzero inclusion probabilities and explicit finite-pool
  uncertainty; and
- a conservative incumbent switch, where a challenger replaces the
  proxy-selected incumbent only when a paired gold comparison clears a
  prespecified evidence threshold.

The last rule is a *candidate*, not an established safe-improvement theorem.
It should audit matched questions for incumbent/challenger, reserve positive
sampling probability for alternatives, log all model and question choices,
and count every gold label used for screening and switching. Reusing a naive
uniform residual estimator after adaptive acquisition would be invalid.
Preselecting challengers from judge scores may save gold, but must be shown
against the same proxy access in controls; it can also exclude the true best.

With 20 models and only 36 historical questions per outer fold, 10% of the
720-cell history is 72 gold labels. That is sparse for estimating 20 separate
model means and is a material power risk. Do not claim a formal confidence
guarantee from a bootstrap of repeatedly reused 48 development questions.
Inspect selection regret and paired differences, then plan an independent
larger set before a confirmatory claim. The 938 FinQA common questions whose
scores were not read in the headroom diagnostic remain potential evaluation
inventory, subject to prompt-only grouping and a newly locked protocol.

## Paper bar

A publishable method claim needs an improvement over the closest proxy-aware
and gold-only controls under the same gold budget and an honest total-cost
account, across independent tasks or datasets. A global model selector based
on historical executions is not automatically a task-contextual router: a
contextual claim needs decisions from information available before running the
new solver and separate evaluation. If the evidence does not support a new
method, HistRepEval can still be developed as a measurement contribution, but
that is a different paper claim requiring benchmark validity and broad
coverage. No A* acceptance or superiority can be guaranteed in advance.
