# RepGuard / ECRT — 6-Week Research-to-Paper Execution Plan

**Working paper title:**  
**RepGuard: Evidence-Calibrated Reputation Transfer under Imperfect Feedback in Multi-Agent LLM Systems**

**Core method:** Evidence-Calibrated Reputation Transfer (ECRT)  
**Working evaluation-suite name:** HistRepEval *(working name only; re-check name collision before public release)*  
**Plan duration:** 6 weeks  
**Start:** 31 August 2026  
**Final manuscript/release target:** 11 October 2026  
**Literature status checked through:** 30 August 2026

---

## 0. Executive Goal

The goal of the six-week sprint is not merely to implement a new reputation score. The goal is to produce a research paper with a falsifiable scientific claim, a reproducible experimental protocol, and enough evidence to determine whether the proposed mechanism deserves to be published.

The central research question is:

> **How should a multi-agent LLM system convert imperfect historical feedback into task-relevant reputation and influence?**

The paper will test the hypothesis that historical reputation quality depends on two **distinct evidence dimensions**:

1. **Feedback reliability** — how trustworthy the observed feedback about a historical interaction is.
2. **Task transferability** — how relevant that historical interaction is as evidence of competence on the current task.

This must be tested experimentally rather than assumed.

The intended core method, **ECRT**, estimates historical correctness probabilistically from imperfect feedback, discounts evidence according to task transferability, preserves uncertainty, and uses the resulting posterior expertise to weight agent influence.

Strategic reputation manipulation is a **stress test**, not the novelty claim.

---

# 1. What Counts as a Successful Research Project?

## 1.1 Minimum scientific success

The project is scientifically successful if, by the end of Week 6, it establishes all of the following:

1. A controlled experiment shows that feedback reliability and task transferability have measurable effects on the reliability of historical reputation.
2. The effects are reproducible across multiple domains, seeds, and at least two heterogeneous agent/model families or substantially different agent configurations.
3. A simple ECRT implementation improves at least one important trust-quality measure—such as reputation calibration, expert leveraging, or attack robustness—over global and skill-conditioned reputation baselines under imperfect feedback.
4. Improvements do not come from destroying clean-system utility.
5. Ablations show which parts of ECRT are actually responsible for the observed gains.
6. Ground truth used for evaluation is cleanly separated from feedback available to the online reputation mechanism.
7. Experiments, configurations, and data-generation procedures are reproducible.

## 1.2 Strong-paper success

A stronger paper additionally provides:

- a robust 2D characterization or “regime map” of feedback reliability × transferability;
- a generalizable empirical finding rather than only an accuracy improvement;
- a public evaluation suite or benchmark protocol;
- strategic attack curves showing how much reputation capital an attacker needs;
- uncertainty-aware behavior that fails safely when evidence is weak;
- results on a second, structurally different benchmark/environment;
- code, configurations, logs, benchmark card, and exact evaluation scripts.

## 1.3 Valid negative-result success

The project can still become a publishable empirical paper if ECRT does not win, provided the controlled study uncovers a strong and reproducible negative finding, for example:

- feedback reliability dominates transferability almost entirely;
- task-transfer estimates are too unstable to improve reputation;
- skill-conditioned reputation is already sufficient in most realistic regimes;
- reputation mechanisms create a fundamental clean-utility vs adversarial-robustness trade-off;
- uncertainty-aware abstention is more useful than sophisticated reputation transfer.

If this happens, the paper story must be changed rather than hiding the result.

---

# 2. Protected Novelty Boundary

The following ideas **must not be claimed as new**.

| Idea | Already represented in recent work | How this project should treat it |
|---|---|---|
| Historical credibility/reputation for aggregating multi-agent outputs | Ebrahimi et al., IJCNLP-AACL 2025 | Baseline and direct precursor |
| Skill-conditioned trust/reputation | Xia & Wang, 2026 | Baseline / related work |
| Cross-skill evidence borrowing and laundering attacks | Xia & Wang, 2026 | Known mechanism and known attack |
| Zero-evidence gate | Xia & Wang, 2026 | Baseline/safety control |
| Dynamic trust and time decay | CogTrust, 2026 | Related work / optional baseline |
| Malicious-agent detection | SentinelNet, WWW 2026 | Related work, not the core task |
| Reputation-aware red-teaming | WEREWOLF, Findings of EMNLP 2026 | Monitor closely; attacks only as stress tests |
| Untrusted tool feedback | Trust No Tool, 2026; unreliable-feedback studies | Adjacent feedback-security literature |
| Generic feedback taxonomies | IJCAI 2025 feedback survey | Background |
| Generic recalibration of historical experience | DREvo, 2026 | Adjacent evidence-recalibration literature |
| Contextual routing among heterogeneous LLMs | Online multi-LLM selection / bandit literature | Not the novelty |
| Creating a scalar Bayesian reputation score | Broad trust/reputation literature | Not sufficient novelty |

### Defensible contribution target

The contribution to investigate is narrower:

> **Historical teammate reputation under imperfect feedback should separate confidence in the historical outcome from relevance of that outcome to the current task before converting history into long-term influence.**

A safe paper claim, if supported by results, is:

> “We identify and experimentally characterize two distinct dimensions of historical evidence—feedback reliability and task transferability—and show how jointly accounting for them changes reputation calibration, expert leveraging, and robustness to strategic manipulation.”

Do **not** claim that the two dimensions are statistically independent unless the data explicitly support that statement.

---

# 3. Research Questions and Hypotheses

## RQ1 — Failure characterization

**How sensitive is historical reputation to feedback sparsity, feedback noise, and evaluator error?**

**H1:** Reputation learned from raw historical success degrades systematically as feedback becomes noisier or less available.

---

## RQ2 — Transfer mismatch

**How much does task mismatch degrade the usefulness of historical reputation?**

**H2:** Even highly reliable historical outcomes can produce misleading reputation when transferred to tasks requiring different skills or difficulty regimes.

---

## RQ3 — Two-dimensional evidence structure

**Do feedback reliability and task transferability explain different failure modes in historical reputation?**

**H3:** Manipulating feedback quality while holding task relationship fixed and manipulating task relationship while holding feedback quality fixed produce distinguishable effects on reputation quality.

This is a controlled causal/experimental statement, not a claim of probabilistic independence.

---

## RQ4 — Method

**Does ECRT improve historical-reputation quality compared with global and skill-conditioned reputation?**

**H4:** ECRT improves calibration and expert leveraging under imperfect feedback while preserving clean-task performance.

---

## RQ5 — Strategic manipulation

**Can strategic agents exploit imperfect historical feedback and task transfer to acquire inappropriate influence?**

**H5:** Reputation farming, cross-skill laundering, or evaluator corruption raise attacker influence more sharply in naive reputation systems than in ECRT.

---

## Optional RQ6 — Verification budget

**Can posterior uncertainty be used to allocate limited verification more efficiently?**

This RQ is a stretch goal and should be dropped if the core paper is not complete by the end of Week 4.

---

# 4. Research Design Before Weekly Execution

## 4.1 Primary benchmark recommendation

Use **MMLU-Pro** as the primary controlled benchmark because it provides:

- multiple subject/domain categories;
- objective answer keys;
- enough task diversity for source-target task relationships;
- straightforward offline correctness measurement;
- low infrastructure overhead;
- the ability to create histories without requiring complex interactive environments.

Ground truth is available to the experimental evaluator but must be hidden from the online reputation algorithm except in the explicit oracle condition.

## 4.2 Secondary external-validity benchmark

Preferred stretch option: a **small AppWorld slice**.

Why:

- state-based programmatic unit tests provide strong objective feedback;
- it tests whether findings survive beyond multiple-choice reasoning;
- it introduces action/tool use and richer trajectories.

However, AppWorld is infrastructure-heavy and skill-conditioned reputation work already uses heterogeneous AppWorld agents. Therefore, AppWorld should be an external-validity test, not the source of the primary novelty.

If AppWorld setup threatens the six-week deadline, skip it and release a rigorous MMLU-Pro study.

## 4.3 Agent heterogeneity

A reputation paper requires genuine heterogeneity.

Recommended agent pool:

- 4–6 frozen LLM backbones, or
- 3–4 backbones combined with distinct scaffolds/prompts/tools.

Before any main experiment, measure each agent’s per-domain performance.

### Heterogeneity gate

Proceed only if:

1. the identity of the best agent changes across at least several domains; and
2. there is a meaningful performance spread between agents.

If a single model dominates every domain, reputation transfer cannot be studied properly. Fix this in Week 2 by changing model/scaffold composition.

---

# 5. Core Data Model

For agent \(i\), historical episode \(t\):

\[
h_{it} = (q_t, y_{it}, x_t, F_{it})
\]

where:

- \(q_t\): historical task/query;
- \(y_{it}\): agent answer/action;
- \(x_t\): task metadata (domain, skill, difficulty, etc.);
- \(F_{it}\): observed feedback.

True correctness:

\[
z_{it} \in \{0,1\}
\]

is hidden from the online reputation mechanism in non-oracle settings.

Current task:

\[
q^\*
\]

The method should estimate:

\[
p_{it}=P(z_{it}=1\mid F_{it})
\]

and transferability:

\[
\tau(h_{it},q^\*) \in [0,1].
\]

A soft-evidence Beta formulation is:

\[
\alpha_i(q^\*)=
\alpha_0+\sum_t \tau_{it}m_{it}p_{it}
\]

\[
\beta_i(q^\*)=
\beta_0+\sum_t \tau_{it}m_{it}(1-p_{it})
\]

where \(m_{it}\) is evidence strength/reliability mass.

Posterior mean:

\[
\mu_i(q^\*)=\frac{\alpha_i(q^\*)}{\alpha_i(q^\*)+\beta_i(q^\*)}.
\]

The influence function should preserve uncertainty, e.g., posterior lower credible bound or uncertainty-discounted mean.

---

# 6. Feedback Conditions

Implement feedback as an experimental variable rather than a single label.

## Mandatory conditions

### F0 — Oracle objective feedback

Use true correctness.

Purpose: upper bound, debugging, and decomposition.

### F1 — Controlled noisy feedback

Flip/corrupt objective labels at controlled levels, e.g.:

\[
\eta \in \{0,0.1,0.25,0.4\}.
\]

This gives clean causal control over feedback quality.

### F2 — Sparse feedback

Reveal feedback for only a fraction of historical episodes, e.g.:

\[
\rho \in \{0.1,0.25,0.5,1.0\}.
\]

Unobserved episodes must not automatically become negative evidence.

### F3 — LLM-as-a-Judge feedback

A judge evaluates historical answers. The judge’s sensitivity, specificity, calibration, and bias must be estimated on a held-out calibration split with ground truth.

Judge output is weak evidence, not truth.

### F4 — Mixed feedback

Combine objective/noisy/judge/missing observations.

This is the closest controlled proxy for deployment.

## Optional feedback conditions

- delayed feedback;
- evidence-grounded verification;
- sparse human audit;
- correlated feedback sources.

Do not add these before the mandatory experiments are stable.

---

# 7. Transferability Conditions

Do not invent arbitrary values and call them “true transferability.”

Use two notions:

## 7.1 Controlled transfer strata

Create source-target relationships such as:

1. same subject / same skill;
2. related subject / shared skill family;
3. distant/unrelated domain.

These are experimental conditions.

## 7.2 Estimated transferability

ECRT can estimate \(\hat{\tau}\) using a deliberately simple mechanism:

- predefined task hierarchy;
- domain metadata;
- held-out empirical cross-domain performance correlation;
- or a small calibrated classifier.

Start with metadata/hierarchy. Do not train a new large neural model.

## 7.3 Oracle transfer upper bound

Construct an “oracle transfer” diagnostic based on held-out empirical agent-performance relationships.

This is not deployable; it helps answer:

> Is ECRT limited by bad feedback inference or bad transfer estimation?

---

# 8. Main Controlled Factorial Experiment

This should be the scientific center of the paper.

Manipulate:

\[
Q = \text{feedback quality}
\]

and

\[
T = \text{task transfer condition}
\]

independently.

Example:

- Feedback quality: high / medium / low / adversarial.
- Transfer: same / related / unrelated.

Measure:

- reputation calibration;
- rank correlation with true target competence;
- team accuracy;
- expert leverage;
- attacker influence when attacks are enabled.

Statistical model, if data volume permits:

\[
Y=\beta_0+\beta_1Q+\beta_2T+\beta_3(Q\times T)+u_{\text{domain}}+u_{\text{agent}}+\epsilon.
\]

For binary final accuracy, use logistic/mixed-effects logistic modeling or stratified bootstrap.

Report:

- main effect of Q;
- main effect of T;
- interaction \(Q\times T\);
- confidence intervals;
- effect sizes.

The intended finding is **not preordained**. The point is to reveal whether the two dimensions genuinely explain separate failure modes.

---

# 9. Baselines

## Required baselines

1. **Uniform / majority aggregation**
2. **Global historical reputation**
3. **Oracle global reputation**
4. **Independent skill-conditioned reputation**
5. **Skill-conditioned reputation with controlled cross-skill borrowing**
6. **Zero-evidence gate**
7. **Credibility-scoring-style historical weighting**
8. **ECRT**

## Diagnostic oracle variants

These are especially important:

- Oracle feedback + estimated transfer;
- estimated feedback + oracle transfer;
- oracle feedback + oracle transfer;
- full estimated feedback + estimated transfer.

They reveal the true bottleneck.

## Optional baselines

- simple recency-decay trust;
- a CogTrust-inspired dynamic variant;
- reputation-aware routing if implementation is trivial.

Do not spend a week reproducing SentinelNet: it solves malicious-message detection, not the exact historical-reputation inference problem.

---

# 10. Attack Stress Tests

Attacks are evaluation conditions, not novelty claims.

## A1 — Same-skill delayed betrayal

The attacker behaves correctly during warm-up, then intentionally gives a harmful target answer.

Measure:

- attack success rate;
- reputation capital required;
- influence retained after betrayal.

## A2 — Cross-skill laundering

Known from recent skill-conditioned reputation work.

The attacker accumulates cheap evidence in a source skill and attempts to transfer it into a target skill.

## A3 — Feedback poisoning

Historical feedback is corrupted or generated by a biased/unreliable evaluator.

## A4 — Combined attack

Warm-up reputation + task shift + feedback corruption.

Use only after A1–A3 are stable.

---

# 11. Metrics

## Reputation quality

- Brier score;
- negative log-likelihood;
- Expected Calibration Error (ECE);
- Spearman/Kendall rank correlation with offline target competence;
- top-expert identification accuracy;
- confidence interval coverage if applicable.

## Team utility

- final task accuracy;
- clean accuracy;
- best-agent gap;
- expert leverage rate;
- expert override rate.

## Security/robustness

- attack success rate;
- harmful influence probability;
- attack capital;
- target-task regret;
- robustness under feedback corruption.

## Evidence behavior

- effective evidence mass;
- abstention/prior-reversion rate;
- posterior entropy/variance;
- fraction of decisions requiring verification if optional verification is implemented.

## Statistical reporting

Always include:

- number of tasks/episodes;
- number of seeds;
- 95% confidence intervals;
- effect sizes;
- paired/stratified tests where possible;
- total API/model cost.

---

# 12. Ablation Study

Keep the ablation aligned to the scientific hypothesis.

| Variant | Feedback reliability | Transferability | Uncertainty-aware influence |
|---|---:|---:|---:|
| Global reputation | No | No | No |
| + Reliable feedback | Yes | No | No |
| + Transfer | Yes | Yes | No |
| ECRT | Yes | Yes | Yes |

Additional diagnostics:

1. **ECRT – feedback reliability**: treat every observed feedback signal as equally trustworthy.
2. **ECRT – transferability**: set \(\tau=1\).
3. **ECRT – uncertainty**: use posterior mean only.
4. **ECRT – abstention/gate**: force a score even with negligible evidence.
5. **Oracle-F / Estimated-T**
6. **Estimated-F / Oracle-T**
7. **Oracle-F / Oracle-T**

Do not create an ablation table with many unrelated modules such as recency, behavior detector, verifier, semantic similarity, etc. unless one becomes necessary after empirical evidence.

---

# 13. Six-Week Schedule

# Week 1 — Aug 31–Sep 6
## Goal: Lock the research gap, falsifiable claim, benchmark design, and paper skeleton

### Research tasks

Read and create structured notes for the closest work:

1. Ebrahimi et al. 2025 — credibility scoring.
2. Xia & Wang 2026 — skill-conditioned reputation and laundering.
3. CogTrust 2026 — dynamic/time-decayed trust.
4. SentinelNet 2026 — malicious-agent detection.
5. WEREWOLF 2026 — monitor for paper/preprint release.
6. Pappu et al. 2026 — expert leveraging.
7. Trust No Tool 2026 — trajectory trust under untrusted feedback.
8. DREvo 2026 — recalibration of historical experience.
9. IJCAI 2025 feedback survey.
10. MMLU-Pro / AppWorld benchmark papers.
11. LLM-as-a-Judge reliability literature.

For each paper, fill a comparison table:

- object being trusted;
- source of feedback;
- ground-truth assumption;
- task conditioning;
- uncertainty representation;
- strategic attack considered;
- whether historical evidence is recalibrated;
- whether task transfer is modeled;
- benchmark;
- open limitation relevant to RepGuard.

### Engineering tasks

- Create project repository structure.
- Freeze package versions.
- Create experiment configuration schema.
- Implement deterministic logging.
- Load MMLU-Pro and create train/calibration/dev/test partitions without leakage.
- Build a minimal single-agent evaluation harness.
- Decide model pool based on cost and availability.

### Experimental tasks

Run a small capability audit:

- 2–4 candidate models;
- ~50–100 tasks across several domains;
- estimate whether heterogeneity exists.

Do not begin full experiments.

### Paper writing

Write:

- **Introduction v0.5**
- **Related Work v0.7**
- **Problem Formulation v0.5**
- one-page “novelty boundary” memo that will later become the related-work comparison table.
- paper skeleton with all planned figures/tables.

### Expected figures/tables

- Table 1: literature/novelty comparison;
- Figure 1 draft: problem illustration;
- Figure 2 draft: feedback reliability × task transferability grid.

### End-of-week report

Report:

1. final research question;
2. final novelty statement;
3. literature collision table;
4. selected benchmark and model pool;
5. preliminary heterogeneity results;
6. exact experiment splits;
7. compute/API budget;
8. risks discovered;
9. Introduction and Related Work draft links;
10. Week 2 exit criteria.

### Week 1 exit criteria

Do not proceed to full implementation until:

- the novelty statement does not claim historical reputation, skill conditioning, dynamic trust, reputation attacks, or feedback itself as new;
- benchmark licenses/release rules are understood;
- experimental GT/online-feedback separation is specified;
- candidate models exhibit at least some domain heterogeneity.

---

# Week 2 — Sep 7–Sep 13
## Goal: Reproduce baselines and build HistRepEval v0.1

### Research tasks

Focus on implementation details from the most relevant methods:

- credibility update equations;
- skill-conditioned reputation;
- evidence borrowing / zero-evidence gate;
- judge scoring and calibration;
- Beta/Bayesian reputation formulations;
- standard calibration metrics.

### Engineering tasks

Implement:

1. uniform/majority baseline;
2. global Beta reputation;
3. oracle global reputation;
4. independent skill-conditioned reputation;
5. cross-skill borrowing baseline;
6. zero-evidence gate;
7. controlled feedback corruption;
8. sparse-feedback masks;
9. logging of complete history and score evolution;
10. task-relation strata;
11. offline target-competence evaluator.

Build **HistRepEval v0.1** as a reproducible protocol, not necessarily a redistributed dataset.

HistRepEval v0.1 should contain:

- task IDs and split generator;
- source/target episode generator;
- feedback corruption configuration;
- feedback availability masks;
- transfer-condition metadata;
- agent pool configuration;
- attack metadata schema;
- evaluation scripts.

### Experimental tasks

Run baseline sanity tests:

- Oracle reputation should converge toward observed competence with sufficient evidence.
- Low feedback quality should degrade raw reputation.
- Unrelated-task history should expose failure in global reputation.
- Zero-evidence cases should behave as specified.

Run judge calibration pilot if using LLM-as-a-Judge.

### Paper writing

Write:

- **Experimental Setup / Benchmark section v0.8**
- **Threat Model v0.8**
- **Method section skeleton v0.3**
- finalized notation table.

### Expected figures/tables

- Table 2: benchmark composition;
- Table 3: agent per-domain capability matrix;
- Figure: baseline reputation convergence;
- Figure: judge calibration reliability diagram.

### End-of-week report

Include:

- baseline reproduction status;
- any mismatch from published descriptions;
- heterogeneity matrix;
- feedback-quality implementation tests;
- judge calibration pilot;
- HistRepEval v0.1 schema;
- paper sections written;
- cost so far;
- blockers.

### Week 2 exit criteria

- all mandatory baselines run end-to-end;
- histories can be generated reproducibly from config + seed;
- no test ground-truth leakage;
- at least one clear task-mismatch failure can be produced in a controlled setting;
- agent heterogeneity gate passes.

If these fail, Week 3 begins with repair rather than ECRT.

---

# Week 3 — Sep 14–Sep 20
## Goal: Establish the empirical phenomenon before claiming a method

This is the most important go/no-go week.

### Research tasks

Read statistical methodology needed for:

- factorial experimental design;
- calibration analysis;
- mixed-effects/logistic modeling if used;
- bootstrap confidence intervals;
- interaction effect interpretation.

### Experimental tasks — Core characterization

Run the controlled grid:

\[
Q \times T
\]

where Q is feedback quality and T is task transfer condition.

Recommended initial grid:

- Q: 1.0, 0.9, 0.75, 0.6;
- T: same, related, unrelated;
- 3–5 seeds;
- multiple domains;
- multiple agents.

Run under:

- global reputation;
- skill-conditioned reputation;
- zero-evidence gate.

Answer:

1. Does Q matter?
2. Does T matter?
3. Is there a meaningful interaction?
4. Which baseline fails in which regime?
5. Does reputation help or hurt expert leveraging?
6. Is there a regime where reputation is worse than no reputation?

### Strategic pilot

Run only A1 delayed betrayal and A2 cross-skill laundering.

The purpose is to identify whether imperfect feedback/task transfer creates additional attack surface.

### Analysis

Create:

- heatmaps;
- calibration plots;
- expert-leverage plots;
- confidence intervals;
- attack-capital curves.

Fit a simple factorial model or equivalent stratified analysis.

### Go/no-go decision

At the end of Week 3 choose one:

#### GO-A: Original hypothesis supported

Both dimensions show meaningful distinct effects.

Proceed with ECRT.

#### GO-B: One dimension dominates

Reframe method and paper around the dominant factor.

#### GO-C: Existing skill-conditioned methods already solve the problem

Do not force ECRT. Reframe toward empirical characterization/benchmark or stop the method claim.

#### GO-D: No reproducible phenomenon

Stop major development and redesign the task/agent heterogeneity before spending more compute.

### Paper writing

Write:

- **Results 1: Failure Characterization v0.8**
- update **Introduction v0.8** based on actual findings;
- lock final RQs/hypotheses;
- revise Related Work after a new novelty search.

### Expected figures

- central Q×T heatmap;
- reputation-calibration plot;
- expert-leverage plot;
- initial attack curve.

### End-of-week report

This report must explicitly state:

- evidence for each hypothesis;
- effect size + CI;
- failures/non-results;
- whether the scientific story survived;
- what will be dropped;
- go/no-go decision;
- revised contribution statement.

### Week 3 exit criteria

There must be a real empirical phenomenon worth modeling.

No full ECRT development should continue solely because it was in the original proposal.

---

# Week 4 — Sep 21–Sep 27
## Goal: Implement ECRT and isolate where it helps

### Research tasks

Review only method-specific literature necessary for:

- probabilistic label/noisy annotator models;
- reliability calibration;
- Beta-Binomial/soft-evidence Bayesian updates;
- uncertainty-aware decision rules.

Avoid broad reading now. The novelty map is already established.

### Engineering — ECRT MVP

Implement in this order:

#### ECRT-1: feedback reliability

Estimate per-feedback-source reliability from a calibration split.

Start with:

- confusion matrix;
- sensitivity/specificity;
- optional probability calibration.

Infer \(p_t=P(z_t=1|F_t)\).

Do not begin with EM unless necessary.

#### ECRT-2: transferability

Implement a simple \(\hat{\tau}\):

- same-skill metadata;
- task hierarchy;
- held-out empirical relatedness.

Do not train a complex neural transfer model.

#### ECRT-3: soft-evidence posterior

Implement \(\alpha,\beta\) updates.

#### ECRT-4: uncertainty-aware influence

Compare:

- posterior mean;
- lower credible bound;
- uncertainty-discounted mean.

### Experimental tasks

Run:

1. full ECRT;
2. ECRT without feedback reliability;
3. ECRT without transfer;
4. ECRT without uncertainty handling;
5. oracle feedback + estimated transfer;
6. estimated feedback + oracle transfer;
7. oracle feedback + oracle transfer.

First on the Week 3 controlled grid, then on held-out test tasks.

### Paper writing

Write:

- **Methodology v1.0**
- **Algorithm/pseudocode v1.0**
- **Results 2: Main Method Evaluation v0.6**
- update problem formulation to match implementation exactly.

### Expected figures/tables

- ECRT system diagram;
- Algorithm 1;
- Main results table;
- Oracle-component decomposition plot;
- Ablation table draft.

### End-of-week report

Report:

- exact final equations;
- calibration method;
- transfer estimator;
- method hyperparameters;
- main effect sizes;
- oracle decomposition;
- ablation results;
- compute cost;
- whether ECRT provides incremental value over skill-conditioned trust.

### Week 4 exit criteria

A main method table must exist.

If ECRT does not beat the relevant baselines anywhere meaningful, stop adding modules and diagnose why.

---

# Week 5 — Sep 28–Oct 4
## Goal: Robustness, attacks, external validity, and complete results

### Research tasks

Only update the novelty watch:

- search for new August/September 2026 papers;
- specifically re-check WEREWOLF public availability;
- search for “reputation”, “trust”, “historical feedback”, “skill-conditioned”, “multi-agent LLM”, “agent reputation”.

### Experimental tasks

## Mandatory robustness

- different feedback sparsity;
- different feedback corruption;
- judge-only feedback;
- mixed feedback;
- task/domain shift;
- history length;
- number of agents;
- multiple seeds.

## Attack stress tests

- delayed betrayal;
- cross-skill laundering;
- feedback poisoning;
- combined attack if budget allows.

## External validity

If the core paper is stable:

- run a small AppWorld experiment, or
- another objectively scored environment.

If not stable, prioritize the primary benchmark and statistical rigor.

### Optional extension

Add uncertainty-triggered selective verification only if all mandatory tables are frozen by mid-week.

### Paper writing

Write:

- **Results v0.9**
- **Robustness / Attack Analysis v0.9**
- **Discussion v0.7**
- **Limitations v0.7**
- **Ethics / Responsible Release v0.5**
- **Abstract v0.3**

### Expected figures/tables

- Main results table frozen;
- robustness curves;
- attack-capital curve;
- calibration figure;
- ablation table frozen;
- optional external-validity table.

### End-of-week report

Include:

- frozen main results;
- all failure cases;
- external-validity result or reason for omission;
- final contribution list;
- final limitations;
- remaining missing experiment list;
- exact paper-completion checklist.

### Week 5 exit criteria

All claims in the Introduction must already be supported by a table/figure.

No new major idea may be added after this point.

---

# Week 6 — Oct 5–Oct 11
## Goal: Freeze the science, write the final paper, and prepare release artifacts

### Monday–Tuesday — final experiments

Only run:

- missing seeds;
- reviewer-critical sanity checks;
- failed-run replacements;
- final statistical tests.

Do not introduce new modules.

### Wednesday — paper v1.0

Complete:

1. Abstract
2. Introduction
3. Related Work
4. Problem Setting
5. Method
6. HistRepEval / Experimental Protocol
7. Experimental Setup
8. Main Results
9. Ablation
10. Robustness / Attacks
11. Discussion
12. Limitations
13. Conclusion
14. References
15. Appendix

### Thursday — internal review

Perform four separate review passes:

#### Scientific review
Does every claim have evidence?

#### Novelty review
Is anything already done in prior work being presented as new?

#### Leakage/reproducibility review
Can an independent researcher regenerate the experiment?

#### Writing review
Can a reader understand the problem before seeing equations?

### Friday — artifact freeze

Release candidate:

- code;
- configs;
- seeds;
- environment file;
- experiment manifest;
- generated metadata;
- evaluation scripts;
- benchmark/evaluation-suite card;
- attack configurations;
- result CSV/JSON;
- plotting scripts.

Do not redistribute benchmark content if license terms prohibit it. Prefer IDs + generation scripts when necessary.

### Weekend — final manuscript

- paper v1.1;
- appendix;
- reproducibility checklist;
- README;
- public-release note;
- final literature check;
- archive exact commit/hash.

### Final end-of-project report

Summarize:

1. research question;
2. what was actually discovered;
3. hypotheses supported/rejected;
4. method contribution;
5. benchmark/evaluation contribution;
6. attack findings;
7. limitations;
8. compute/model budget;
9. artifacts released;
10. next paper/revision steps.

---

# 14. Daily Operating Rhythm

Every experiment must be logged with:

- date;
- research question;
- config file;
- model/version;
- seed;
- dataset split;
- git commit;
- API/model cost;
- expected outcome;
- observed outcome;
- whether it changes a paper claim.

At the end of every day, update:

- `research_log.md`
- `experiment_registry.csv`
- `paper_claims.md`
- `open_questions.md`

This prevents double work and post-hoc storytelling.

---

# 15. Weekly Report Template

```markdown
# Week N Research Report

## 1. Objective
What question was this week supposed to answer?

## 2. Work Completed
- Literature:
- Engineering:
- Experiments:
- Writing:

## 3. Experimental Evidence
For each experiment:
- config:
- seed(s):
- sample size:
- primary metric:
- result:
- 95% CI:
- interpretation:

## 4. Figures and Tables Produced
- Figure X:
- Table Y:

## 5. Hypothesis Status
- H1: supported / mixed / rejected / not tested
- H2:
- H3:
- H4:
- H5:

## 6. Failures / Unexpected Results
Document negative results.

## 7. Novelty Watch
Any newly published paper that overlaps with the project?

## 8. Paper Progress
- Introduction:
- Related Work:
- Method:
- Experiments:
- Results:
- Discussion:

## 9. Compute and Cost
- calls:
- tokens:
- GPU hours:
- cost:

## 10. Decisions
What was frozen, removed, or changed?

## 11. Next-Week Exit Criteria
Concrete conditions for moving forward.
```

---

# 16. Paper Structure and Writing Targets

## 1. Abstract — 150–220 words

Write only in Week 5/6.

Structure:

1. problem;
2. gap;
3. method;
4. controlled evaluation;
5. key quantitative finding;
6. implication.

Never write unsupported numbers before experiments finish.

---

## 2. Introduction — ~1.25 pages

Paragraph flow:

1. Multi-agent LLMs need to exploit heterogeneous expertise.
2. Expert presence does not imply expert leveraging.
3. Historical reputation is a natural solution but depends on historical evidence.
4. Historical evidence has at least two distinct questions:
   - was the old outcome reliably evaluated?
   - is that evidence relevant to the new task?
5. Existing lines of work address credibility, skill conditioning, dynamic trust, attacks, or unreliable feedback separately.
6. Define the research gap precisely.
7. Present controlled study + ECRT.
8. Contributions.

Draft in Week 1; revise after Week 3; freeze Week 6.

---

## 3. Related Work — ~1 page

Subsections:

- Multi-Agent Expertise and Expert Leveraging
- Historical Credibility and Reputation
- Skill-Conditional Trust and Reputation Transfer
- Dynamic Trust and Malicious-Agent Detection
- Feedback Reliability and LLM-as-a-Judge
- Historical Experience Recalibration

Must contain a comparison table.

Draft Week 1; novelty update Week 3/5/6.

---

## 4. Problem Setting — ~0.75 page

Define:

- agents;
- histories;
- latent correctness;
- feedback channels;
- current target task;
- reputation;
- transferability;
- influence rule;
- attacker;
- oracle vs deployment information.

Draft Week 1–2; freeze Week 4.

---

## 5. Method — ~1–1.5 pages

Sections:

1. feedback reliability;
2. latent correctness inference;
3. task transferability;
4. soft-evidence expertise posterior;
5. uncertainty-aware influence;
6. computational complexity.

Draft skeleton Week 2; complete Week 4.

---

## 6. HistRepEval / Evaluation Protocol — ~1 page

Explain:

- base datasets;
- agent histories;
- feedback regimes;
- transfer strata;
- attacks;
- splits;
- leakage controls;
- metrics;
- public release format.

Draft Week 2; freeze Week 5.

---

## 7. Experimental Setup — ~0.75 page

Include:

- models;
- prompts;
- generation settings;
- agent pool;
- samples;
- seeds;
- judges;
- compute;
- statistics.

Draft Week 2; update Week 5.

---

## 8. Results — ~2 pages

Recommended order:

### 8.1 RQ1–RQ3: Characterization
Q×T experiment.

### 8.2 RQ4: ECRT vs baselines
Main method table.

### 8.3 Ablation
Which dimension matters?

### 8.4 RQ5: Strategic manipulation
Attack curves.

### 8.5 External validity
If available.

Write initial characterization Week 3; complete Week 5.

---

## 9. Discussion — ~0.75 page

Discuss:

- what reputation should mean;
- when history should be ignored;
- deployment implications;
- security–expertise trade-off;
- why noisy judges should not be treated as truth;
- limitations of transfer estimation.

Week 5–6.

---

## 10. Limitations — ~0.5 page

At minimum:

- benchmark/domain scope;
- closed-model dependence;
- simulated feedback corruption;
- imperfect proxy for deployment feedback;
- correlations between feedback sources;
- task taxonomy subjectivity;
- strategic attacker assumptions;
- compute and reproducibility constraints.

Week 5–6.

---

# 17. Planned Figures and Tables

## Figures

1. **Problem illustration:** reliable but irrelevant evidence vs relevant but unreliable evidence.
2. **RepGuard/ECRT architecture.**
3. **Q×T regime heatmap.**
4. **Reputation calibration curves.**
5. **Expert leverage vs feedback quality.**
6. **Attack success / attack capital curves.**
7. Optional: external-validity results.

## Tables

1. Related-work comparison.
2. Benchmark/agent statistics.
3. Main results.
4. ECRT ablation.
5. Oracle component decomposition.
6. Robustness.
7. Optional external-validity table.

---

# 18. Reproducibility / Anti-Double-Effort Rules

1. Re-run a novelty search at the end of Weeks 1, 3, 5, and 6.
2. Track new papers on:
   - multi-agent reputation;
   - agent trust;
   - skill-conditioned reputation;
   - reputation red-teaming;
   - feedback reliability;
   - agent credibility;
   - historical experience.
3. Maintain a “DO NOT CLAIM” file.
4. Every experiment must map to exactly one RQ or diagnostic.
5. No experiment without a planned figure/table or decision criterion.
6. Do not add a module merely because it seems useful.
7. Prefer simple estimators with interpretable ablations.
8. Use a fixed calibration/dev/test protocol.
9. Freeze model versions.
10. Never use target-test ground truth to estimate online reputation.

---

# 19. Risk Register

## Risk 1 — Novelty collision

**Risk:** new papers, especially WEREWOLF, may overlap further.

**Mitigation:** recurring novelty search; keep attacks as stress tests; frame core gap around imperfect historical feedback + task-relevant evidence conversion.

## Risk 2 — Task-transfer overlap with Xia & Wang

**Risk:** ECRT could become merely another cross-skill borrowing method.

**Mitigation:** explicitly model feedback reliability; use independent-skill baseline; compare to cross-skill borrowing; show oracle-F/estimated-T and estimated-F/oracle-T decomposition.

## Risk 3 — Overlap with DREvo

**Risk:** generic historical-evidence recalibration is already present elsewhere.

**Mitigation:** scope claim specifically to teammate expertise reputation and influence in multi-agent LLMs.

## Risk 4 — No genuine heterogeneity

**Mitigation:** run capability audit before main experiments; change model/scaffold pool if necessary.

## Risk 5 — Judge calibration is unstable

**Mitigation:** retain controlled synthetic-noise conditions as scientific backbone; judge feedback is an external-validity condition, not the only source of evidence.

## Risk 6 — ECRT becomes too complex

**Mitigation:** MVP = confusion-matrix reliability + simple transfer metadata + Beta soft evidence. EM, neural estimators, and verification are optional.

## Risk 7 — Public dataset licensing

**Mitigation:** release an evaluation suite with task IDs, split/config generators, metadata, and scripts rather than republishing restricted raw data.

## Risk 8 — API cost

**Mitigation:** pilot on small subsets; cache immutable outputs; use exact experiment registry; scale only after Week 3 go/no-go.

---

# 20. Final Deliverables by 11 October 2026

## Mandatory

1. Full research paper.
2. ECRT reference implementation.
3. Reproducible baseline implementations.
4. HistRepEval evaluation protocol.
5. Complete experiment configs/seeds.
6. Main Q×T characterization.
7. Main results + calibration + ablation.
8. Strategic stress-test results.
9. Reproducibility documentation.
10. Related-work/novelty matrix.

## Strongly preferred

11. Public evaluation suite.
12. Generated metadata/history files allowed by source licenses.
13. Attack suite.
14. Benchmark/evaluation card.
15. Result tables in machine-readable format.
16. Plotting scripts.
17. Model/judge calibration report.

## Stretch

18. AppWorld external-validation experiment.
19. Selective verification.
20. EM/hierarchical Bayesian feedback model.

The stretch outputs must never delay the core paper.

---

# 21. Reference Set to Read First

1. Ebrahimi, S., Dehghankar, M., & Asudeh, A. (2025). **An Adversary-Resistant Multi-Agent LLM System via Credibility Scoring.** IJCNLP-AACL 2025. https://aclanthology.org/2025.ijcnlp-long.90/
2. Xia, Y., & Wang, T. (2026). **When Should Agent Trust Be Conditional? Characterizing and Attacking Skill-Conditional Reputation in Agent Swarms.** arXiv:2606.14200. https://arxiv.org/abs/2606.14200
3. Wang, J. et al. (2026). **CogTrust: Cognitive Logic-Based Framework for Dynamic Trust Evaluation in Multi-Agent Systems.** Expert Systems with Applications 313, 131535. https://doi.org/10.1016/j.eswa.2026.131535
4. Feng, Y., & Pan, X. (2026). **SentinelNet: Safeguarding Multi-Agent Collaboration Through Credit-Based Dynamic Threat Detection.** WWW 2026. https://doi.org/10.1145/3774904.3792462
5. Pappu, A. et al. (2026). **Multi-Agent Teams Hold Experts Back.** arXiv:2602.01011. https://arxiv.org/abs/2602.01011
6. Yan, L. et al. (2026). **Trust No Tool: Evaluating and Defending LLM Agents under Untrusted Tool Feedback.** arXiv:2605.17453. https://arxiv.org/abs/2605.17453
7. Guo, H. et al. (2026). **DREvo: Distilling Recalibrated Historical Experience for Harness Self-Evolution.** arXiv:2607.26722. https://arxiv.org/abs/2607.26722
8. Liu, Z. et al. (2025). **A Survey on the Feedback Mechanism of LLM-based AI Agents.** IJCAI 2025. https://doi.org/10.24963/ijcai.2025/1175
9. Trivedi, H. et al. (2024). **AppWorld: A Controllable World of Apps and People for Benchmarking Interactive Coding Agents.** ACL 2024. https://aclanthology.org/2024.acl-long.850/
10. Wang, Y. et al. (2024). **MMLU-Pro: A More Robust and Challenging Multi-Task Language Understanding Benchmark.** NeurIPS 2024 Datasets and Benchmarks. https://proceedings.neurips.cc/paper_files/paper/2024/hash/ad236edc564f3e3156e1b2feafb99a24-Abstract.html
11. Poon, M., Zeng, Q., Dai, X., & Zuo, J. (2026). **WEREWOLF: Reputation-Aware Red-Teaming for Self-Organizing LLM Multi-Agent Systems.** Findings of EMNLP 2026. Monitor for public paper/preprint.
