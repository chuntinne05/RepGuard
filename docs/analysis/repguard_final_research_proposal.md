# RepGuard: Evidence-Calibrated Reputation Transfer under Imperfect Feedback in Multi-Agent LLM Systems

**Status:** Final research proposal / paper blueprint  
**Core method:** Evidence-Calibrated Reputation Transfer (ECRT)  
**Working evaluation-suite name:** HistRepEval  
**Literature status checked through:** 30 August 2026

---

# 1. One-Sentence Description

**RepGuard studies how a multi-agent LLM system should convert imperfect historical feedback into task-relevant teammate reputation, and proposes Evidence-Calibrated Reputation Transfer (ECRT) to distinguish whether historical evidence is trustworthy from whether it is relevant to the current task before that evidence is allowed to influence team decisions.**

---

# 2. Motivation

Multi-agent LLM systems are increasingly built from heterogeneous agents whose strengths differ across tasks, models, tools, and reasoning styles. In such systems, treating every agent as equally reliable is inefficient: the system should leverage the agent that is genuinely competent for the current task.

Recent evidence shows, however, that merely having an expert in the team is not sufficient. Multi-agent teams can fail to exploit expert knowledge even when the expert is identifiable. This makes **expert influence assignment** a central coordination problem.

Historical reputation is a natural solution. If an agent repeatedly performs well, the system can give it greater influence in future tasks.

But historical reputation creates a deeper question:

> **What historical evidence should be allowed to become reputation?**

A successful historical interaction is useful only if two conditions hold:

1. the system has reliable evidence that the historical interaction was actually successful; and
2. that historical success is relevant to competence on the current task.

These conditions are not equivalent.

An interaction can be:

- **reliably evaluated but irrelevant** to the current task;
- **highly relevant but poorly evaluated**;
- both reliable and relevant;
- neither.

A reputation mechanism that collapses these cases into a single historical success count may assign unjustified influence.

This problem becomes more important under strategic behavior: an agent may intentionally accumulate favorable history where feedback is cheap, noisy, or weakly transferable, then exploit the resulting reputation on a high-value target task.

---

# 3. Core Research Problem

Let a multi-agent system contain agents \(i\in\{1,\dots,n\}\).

Each historical interaction \(t\) generates:

\[
h_{it}=(q_t,y_{it},x_t,F_{it}),
\]

where:

- \(q_t\) is the historical task;
- \(y_{it}\) is agent \(i\)'s answer or action;
- \(x_t\) describes task attributes such as domain, skill, or difficulty;
- \(F_{it}\) is the feedback observed after the interaction.

The true correctness or quality:

\[
z_{it}\in\{0,1\}
\]

is generally not directly observable by the deployed reputation system.

When the system receives a new task \(q^\*\), it must decide how much influence to give agent \(i\).

The central problem is therefore:

> **How can the system infer trustworthy evidence of historical competence from imperfect feedback, determine whether that evidence transfers to the current task, and convert it into calibrated influence?**

---

# 4. Why This Is Not Just “Another Reputation Score”

This project deliberately avoids claiming novelty for components that already exist.

## Existing direction 1 — Historical credibility

Ebrahimi, Dehghankar, and Asudeh (IJCNLP-AACL 2025) learn credibility from agents' historical contributions and use credibility during aggregation.

Therefore:

> **Historical credibility itself is not new.**

---

## Existing direction 2 — Skill-conditioned reputation

Xia and Wang (2026) show that a single global reputation score is inadequate for heterogeneous agents. They study skill-conditional reputation, cross-skill evidence borrowing, and cross-skill reputation laundering.

Therefore:

> **Skill-conditioned reputation, cross-skill evidence borrowing, and laundering attacks are not new contributions of RepGuard.**

---

## Existing direction 3 — Dynamic trust

CogTrust (2026) includes dynamic trust evaluation and time-decayed memory.

Therefore:

> **Recency decay and dynamic trust are not the novelty.**

---

## Existing direction 4 — Malicious-agent detection

SentinelNet (WWW 2026) detects malicious communications and dynamically suppresses harmful agents.

Therefore:

> **Threat detection is not the novelty.**

---

## Existing direction 5 — Reputation-aware attacks

WEREWOLF is listed as accepted to Findings of EMNLP 2026 under the title *Reputation-Aware Red-Teaming for Self-Organizing LLM Multi-Agent Systems*.

Therefore:

> **Reputation red-teaming or reputation manipulation must not be presented as a newly discovered attack family without comparison to WEREWOLF.**

Attacks in RepGuard are stress tests.

---

## Existing direction 6 — Untrusted feedback

Recent work such as *Trust No Tool* studies trust formation when tool feedback is malicious, and other 2026 work shows that misleading tool observations can be worse than receiving no feedback.

Therefore:

> **The general observation that agent feedback may be unreliable is not new.**

---

## Existing direction 7 — Recalibrating historical experience

DREvo (2026) dynamically reassesses whether historical experience remains valid for current harness self-evolution.

Therefore:

> **Generic historical-experience recalibration is not a universal novelty claim.**

RepGuard must remain specifically about **teammate expertise reputation and influence** in multi-agent LLM systems.

---

# 5. Research Gap

The strongest defensible gap is at the intersection of recent research lines.

Existing multi-agent reputation work increasingly uses historical success to weight, select, or trust agents. Skill-conditioned work asks **where** reputation should apply across skills. Feedback-security research shows that observations and judges may themselves be unreliable. Expert-utilization research shows that deciding **how much influence** to give an expert matters.

However, as of the literature review conducted through 30 August 2026, the following problem remains insufficiently isolated as a first-class experimental object:

> **When historical teammate reputation is learned from imperfect feedback, how should a system separately account for confidence in the historical outcome and relevance of that outcome to the current task before converting history into influence?**

RepGuard therefore studies two distinct dimensions of historical evidence:

### Dimension 1 — Feedback reliability

\[
R_F(h_t)
\]

asks:

> How trustworthy is the evidence that the historical answer/action was good?

### Dimension 2 — Task transferability

\[
R_T(h_t,q^\*)
\]

asks:

> Assuming the historical outcome is known, how relevant is it as evidence of competence for the new task?

The paper does **not** assume these variables are statistically independent.

Instead, it tests whether experimentally manipulating the two dimensions exposes distinguishable failure modes.

---

# 6. Research Story

The intended paper story is:

## Step 1 — Expert leveraging is important

Heterogeneous multi-agent teams need to assign influence according to competence.

## Step 2 — Historical reputation appears useful

Historical outcomes provide evidence about which agent is competent.

## Step 3 — Raw history is not self-authenticating

Historical success may be inferred from noisy judges, sparse feedback, environmental signals, or corrupted observations.

## Step 4 — Correct history may still be irrelevant

A verified success in one domain may provide little evidence for competence in another.

## Step 5 — Current reputation mechanisms can conflate these issues

Global reputation may transfer too broadly; skill-conditioned systems improve specificity but can still depend on the quality of the evidence being conditioned or borrowed.

## Step 6 — Characterize the problem before proposing a defense

Run a controlled factorial study of:

\[
\text{feedback reliability} \times \text{task transferability}.
\]

## Step 7 — Introduce ECRT

Historical evidence contributes to current reputation only according to:

- estimated correctness/reliability;
- evidence strength;
- task transferability;
- posterior uncertainty.

## Step 8 — Stress-test strategically

Use delayed betrayal, cross-skill laundering, and feedback corruption to test whether reputation can be manipulated.

## Step 9 — Release a reproducible evaluation protocol

If successful, publish HistRepEval as an evaluation suite/benchmark protocol for future reputation mechanisms.

---

# 7. Research Questions

## RQ1

How do feedback sparsity, feedback noise, and evaluator error affect the calibration of learned reputation?

## RQ2

How does mismatch between historical tasks and current tasks affect the usefulness of historical reputation?

## RQ3

Do feedback reliability and task transferability correspond to distinguishable empirical failure modes when manipulated independently?

## RQ4

Does ECRT improve reputation calibration, expert leveraging, and team utility over global and skill-conditioned reputation under imperfect feedback?

## RQ5

How much historical evidence must a strategic agent accumulate to gain harmful influence under different reputation mechanisms?

## Optional RQ6

Can reputation uncertainty allocate a limited verification budget efficiently?

---

# 8. Hypotheses

## H1 — Feedback degradation

As feedback becomes noisier or sparser, naive historical reputation becomes less calibrated with true target competence.

## H2 — Task mismatch

Reliable historical success may still produce misleading reputation when evidence is transferred to weakly related tasks.

## H3 — Distinct evidence dimensions

Holding task relationship fixed while varying feedback reliability and holding feedback reliability fixed while varying task relationship will produce separable changes in reputation quality.

## H4 — Joint evidence calibration

A method that models both dimensions will perform better than methods that model only raw history or skill identity.

## H5 — Strategic robustness

ECRT will require a strategic attacker to accumulate more evidence or corrupt stronger feedback before acquiring the same harmful influence.

These hypotheses are falsifiable and should be revised if the controlled study rejects them.

---

# 9. Feedback: What It Means Operationally

Feedback is any signal observed after an agent interaction that provides evidence about whether the interaction was successful.

## 9.1 Objective feedback

Examples:

- answer key;
- unit test;
- exact execution result;
- state-based environment test;
- tool/API success condition.

This is the strongest controlled signal.

## 9.2 Evidence-grounded feedback

A claim can be checked against retrieved documents, citations, or structured evidence.

The verifier does not need a full ideal answer; it checks whether evidence supports the claim.

## 9.3 Delayed environmental outcome

The system may learn success later:

- deployment succeeds/fails;
- task is reopened;
- action is reverted;
- downstream workflow succeeds;
- user accepts/rejects a result.

## 9.4 Human audit

A small fraction of historical interactions can be manually assessed.

## 9.5 LLM-as-a-Judge

A judge model can estimate answer quality.

Its output is a noisy observation and must be calibrated rather than treated as ground truth.

## 9.6 Peer agreement

Agreement among agents is weak auxiliary evidence, not truth, because correlated models may agree on the same wrong answer.

---

# 10. Feedback Reliability Model

The true historical correctness:

\[
z_t\in\{0,1\}
\]

is latent in deployment.

Suppose feedback source \(j\) outputs \(f_{tj}\).

A simple first implementation estimates:

\[
P(f_j\mid z)
\]

using a held-out calibration subset where objective ground truth is available.

For a binary feedback source, estimate:

- sensitivity;
- specificity;
- false-positive rate;
- false-negative rate.

Then estimate:

\[
p_t=P(z_t=1\mid F_t).
\]

This can begin with a simple calibrated Bayesian combination.

### Why simple first?

The research question is about the structure of historical evidence, not about inventing a new noisy-label inference algorithm.

Optional extensions:

- EM;
- Dawid–Skene-style latent labels;
- hierarchical Bayes;
- dependency-aware feedback aggregation.

These should be attempted only if the simple model becomes a clear bottleneck.

---

# 11. Task Transferability

Task transferability describes how much historical evidence about an agent should inform competence on the current task.

\[
\tau(h_t,q^\*)\in[0,1].
\]

Examples:

- Python debugging → Python debugging: high transfer;
- Python algorithms → pandas debugging: moderate/high;
- Python coding → legal reasoning: low.

Transferability is not the same as semantic similarity.

Two tasks can share vocabulary while requiring different competencies.

## Proposed first implementation

Use transparent task metadata:

- same domain;
- same subject;
- shared skill family;
- difficulty compatibility.

Optionally estimate empirical cross-domain competence correlation on held-out data.

Do not train a new large transfer model during the core project.

---

# 12. Evidence-Calibrated Reputation Transfer (ECRT)

For each historical episode:

- \(p_t\) = probability the agent was correct given feedback;
- \(m_t\) = effective evidence mass / confidence in feedback;
- \(\tau_t\) = relevance of that evidence to current task.

Construct:

\[
\alpha_i(q^\*)=
\alpha_0+\sum_t \tau_t m_t p_t
\]

\[
\beta_i(q^\*)=
\beta_0+\sum_t \tau_t m_t(1-p_t).
\]

Posterior expected expertise:

\[
\mu_i(q^\*)=
\frac{\alpha_i(q^\*)}
{\alpha_i(q^\*)+\beta_i(q^\*)}.
\]

Uncertainty can be represented by posterior variance or a credible interval.

---

# 13. Why Uncertainty Matters

Two agents may have the same posterior mean but very different evidence.

Example:

- Agent A: 1 verified success;
- Agent B: 100 highly reliable successes.

A point score can hide this distinction.

Possible conservative influence rules:

### Option A — Lower credible bound

Weight according to a lower posterior quantile.

### Option B — Mean minus uncertainty penalty

\[
w_i=\mu_i-\lambda\sigma_i.
\]

### Option C — Prior reversion / abstention

If effective evidence is too small, do not grant strong historical influence.

This is especially important under cross-skill evidence transfer.

---

# 14. How Reputation Is Used

The primary paper should use a deliberately simple aggregation mechanism so that the scientific effect is interpretable.

For multiple-choice tasks:

1. each agent independently answers;
2. each agent receives weight \(w_i(q^\*)\);
3. answers are aggregated by weighted voting.

This isolates reputation quality from complicated debate dynamics.

A secondary condition may use one round of discussion or expert selection, but it is not necessary for the core study.

---

# 15. Evaluation Benchmark / Public Output

## Working name: HistRepEval

HistRepEval should be understood first as an **evaluation suite**, not necessarily a newly authored raw dataset.

It defines how to turn objectively scored public tasks into longitudinal reputation episodes.

## Unit of evaluation

A sample contains:

- agent identity/configuration;
- historical task ID;
- historical answer;
- true offline outcome;
- feedback observations visible to the online system;
- feedback-source type;
- task/domain metadata;
- source-target relationship;
- target task ID;
- target agent outputs;
- attack metadata;
- reputation score/posterior;
- final team output.

## Public release options

### Output level A — Protocol only

Release:

- scripts;
- configs;
- task IDs;
- generation rules;
- metrics.

### Output level B — Evaluation suite

Additionally release:

- generated histories;
- feedback masks;
- corruption masks;
- transfer metadata;
- attack configurations;
- cached model outputs where licensing/API policies permit.

### Output level C — Full benchmark package

Additionally release permitted derived records and a benchmark card.

The release must respect the licenses and test-set restrictions of every source benchmark.

---

# 16. Primary Benchmark

## MMLU-Pro

Recommended as primary because it has:

- 14 domains;
- objective answers;
- diverse reasoning;
- relatively low experimental complexity;
- enough structure to define historical/current task relations;
- strong discriminative difficulty.

Use ground truth only for:

- offline competence measurement;
- oracle baseline;
- feedback simulation;
- evaluator calibration.

The non-oracle online reputation mechanism must not access it directly.

---

# 17. Secondary Benchmark

## AppWorld — optional external validation

AppWorld provides:

- 750 interactive tasks;
- 9 apps;
- 457 APIs;
- state-based unit-test evaluation.

Its value is structurally different feedback: executable environmental outcomes.

However:

- setup cost is higher;
- recent skill-conditioned reputation work already uses a heterogeneous AppWorld agent pool.

Therefore, AppWorld should strengthen external validity rather than carry the novelty claim.

---

# 18. Agent Pool

Use genuinely heterogeneous agents.

Possible dimensions:

- different LLM backbones;
- different sizes;
- different scaffolds;
- different tool access;
- specialized system prompts.

Before main experiments, build an agent × domain capability matrix.

A valid experimental pool must show that the best agent changes across domains.

If the same agent dominates everywhere, the setup cannot meaningfully test expertise reputation.

---

# 19. Controlled Feedback Regimes

## Oracle

\[
F=z
\]

Upper bound.

## Synthetic corruption

Flip feedback with probability \(\eta\).

Recommended:

\[
\eta\in\{0,0.1,0.25,0.4\}.
\]

## Sparse feedback

Reveal feedback with probability \(\rho\).

Recommended:

\[
\rho\in\{0.1,0.25,0.5,1.0\}.
\]

## Judge feedback

Use one or more LLM judges and measure their calibration.

## Mixed feedback

Sample from objective, judge, and missing feedback channels.

Synthetic corruption is important even if judge feedback is more realistic, because controlled noise permits causal interpretation.

---

# 20. Controlled Transfer Conditions

## T1 — Same skill/domain

High expected transfer.

## T2 — Related skill

Intermediate transfer.

## T3 — Unrelated skill/domain

Low expected transfer.

The experiment should not assert arbitrary transfer coefficients as truth.

Instead, it creates controlled source-target strata and separately evaluates candidate \(\hat{\tau}\) estimators.

An oracle-transfer diagnostic can be derived from held-out empirical competence correlations.

---

# 21. The Central 2D Experiment

The most important experiment is a controlled grid:

\[
\text{Feedback Quality} \times \text{Transfer Condition}.
\]

Example:

| Feedback | Same task | Related task | Unrelated task |
|---|---:|---:|---:|
| Clean | condition | condition | condition |
| Mild noise | condition | condition | condition |
| Strong noise | condition | condition | condition |
| Adversarial | condition | condition | condition |

Run the same histories under multiple reputation mechanisms.

This experiment can answer:

- whether feedback reliability matters;
- whether transfer matters;
- whether one dominates;
- whether there is an interaction;
- which reputation system fails in each regime.

A mixed-effects or factorial model can be used:

\[
Y=\beta_0+\beta_1Q+\beta_2T+\beta_3(Q\times T)+u_{\text{agent}}+u_{\text{domain}}+\epsilon.
\]

The key scientific result may be the regime structure itself, even before ECRT.

---

# 22. Strategic Threat Model

Attacker goal:

> acquire enough historical reputation to influence or override a target-team decision.

Attacker capabilities may include:

- behaving correctly during warm-up;
- selecting cheap historical tasks;
- exploiting cross-skill evidence transfer;
- benefiting from noisy evaluators;
- intentionally failing at a target task.

Do not assume every attacker can alter ground truth or evaluator outputs.

Create explicit capability levels.

---

# 23. Attack Stress Tests

## Attack A — Delayed betrayal

Correct warm-up → harmful target behavior.

## Attack B — Cross-skill laundering

Accumulate evidence in a source skill → exploit it on target skill.

This is a known attack and must be cited as such.

## Attack C — Feedback poisoning

Historical evaluation is biased or corrupted.

## Attack D — Combined reputation manipulation

Warm-up + transfer mismatch + noisy feedback.

Measure the amount of history required to reach a harmful influence threshold.

---

# 24. Baselines

## B0 — Uniform majority

No reputation.

## B1 — Global reputation

One scalar per agent.

## B2 — Oracle global reputation

Same mechanism but correct historical labels.

Useful upper bound.

## B3 — Independent skill-conditioned reputation

One reputation per agent × skill.

## B4 — Skill-conditioned reputation with evidence borrowing

Reproduce a controlled version of cross-skill borrowing.

## B5 — Zero-evidence gate

Prevent unsupported target-skill trust.

## B6 — Credibility-scoring-style historical weighting

Adapt the historical contribution idea to the chosen controlled setup.

## B7 — ECRT

Full method.

## Optional

- time-decay reputation;
- dynamic trust variant.

SentinelNet should primarily be discussed in related work because malicious-message detection is a different task.

---

# 25. Oracle Component Decomposition

This is one of the most important analyses.

Evaluate:

| Feedback | Transfer | Purpose |
|---|---|---|
| Oracle | Oracle | attainable upper bound |
| Oracle | Estimated | isolate transfer error |
| Estimated | Oracle | isolate feedback error |
| Estimated | Estimated | deployable system |

This answers:

> Is the main bottleneck feedback inference or transfer estimation?

Without this decomposition, ECRT can fail without revealing why.

---

# 26. Main Metrics

## Reputation calibration

- Brier Score;
- negative log-likelihood;
- Expected Calibration Error.

## Reputation ranking

- Spearman correlation;
- Kendall correlation;
- expert identification.

## Team effectiveness

- final accuracy;
- best-agent gap;
- expert leverage rate;
- expert override rate;
- clean performance.

## Security

- attack success rate;
- attack capital;
- harmful influence probability;
- post-betrayal recovery.

## Evidence behavior

- effective evidence mass;
- posterior uncertainty;
- abstention/prior-reversion rate.

---

# 27. Definition of Expert Leverage

Let:

- \(A_{\text{best}}\): accuracy of the best individual agent for the relevant domain;
- \(A_{\text{team}}\): team accuracy.

Possible metric:

\[
\text{Best-Agent Gap}=A_{\text{best}}-A_{\text{team}}.
\]

A lower gap means the team is leveraging available expertise more effectively.

For task-level analysis, also track whether the correct/high-competence agent’s answer is overridden by lower-competence agents.

---

# 28. Calibration Target

A reputation score should not merely correlate with past correctness.

For current task class \(k\), if an agent receives reputation 0.8 repeatedly, it should succeed near 80% under comparable conditions.

This makes calibration a more meaningful target than raw score magnitude.

---

# 29. Main Ablation

## Full ECRT

Feedback reliability + transferability + uncertainty.

## – Feedback reliability

Treat observed feedback as equally trustworthy.

Tests whether noisy evaluators create the failure.

## – Transferability

Allow all historical evidence to transfer.

Tests whether task mismatch creates the failure.

## – Uncertainty

Use only posterior mean.

Tests whether evidence quantity/confidence matters.

## – Gate/abstention

Force the system to provide a reputation even with negligible relevant evidence.

Tests unsupported influence.

No large “module soup” ablation should be used.

---

# 30. Statistical Analysis

## Repetitions

At least 3 seeds, preferably 5 for key tables.

## Confidence intervals

Use bootstrap 95% confidence intervals for accuracy and attack metrics.

## Paired comparison

Evaluate methods on the same target tasks wherever possible.

## Factorial effects

For the Q×T study, report:

- Q main effect;
- T main effect;
- Q×T interaction;
- confidence intervals;
- standardized effect sizes where appropriate.

## Multiple comparisons

Correct when performing many simultaneous hypothesis tests.

Do not use “statistically independent” simply because both coefficients are significant.

---

# 31. Expected Findings

These are **possible**, not guaranteed.

## Possible finding A — Both dimensions matter

This is the strongest support for ECRT.

## Possible finding B — Feedback reliability dominates

The paper becomes more about reputation learning from unreliable evaluators.

## Possible finding C — Transfer dominates

The paper becomes more about evidence relevance / conditional reputation.

This would increase overlap risk with Xia & Wang and require a narrower novelty claim.

## Possible finding D — Interaction dominates

For example, noisy feedback may be especially harmful when transfer is high because the system has more confidence in the wrong evidence.

This could become the most interesting empirical finding.

## Possible finding E — Reputation hurts in low-evidence regimes

A useful conclusion may be that no reputation is safer than unsupported reputation.

## Possible finding F — Simple gates outperform sophisticated transfer

This is still scientifically valuable if reproduced robustly.

---

# 32. Possible Paper Contributions

The final contribution list must be selected from actual results.

## Contribution C1 — Empirical characterization

**Potential primary contribution**

A controlled study of how feedback reliability and historical-to-current task transfer jointly affect teammate reputation.

Output:

- regime heatmap;
- effect decomposition;
- calibrated metrics.

## Contribution C2 — ECRT method

A probabilistic evidence-calibrated reputation mechanism.

Output:

- equations;
- implementation;
- ablation;
- oracle decomposition.

## Contribution C3 — HistRepEval evaluation suite

A reproducible protocol for historical reputation under imperfect feedback and task shift.

Output:

- task-history generator;
- feedback corruption/missingness generator;
- transfer strata;
- attack scenarios;
- metrics;
- configurations.

## Contribution C4 — Strategic stress-test suite

Output:

- delayed betrayal;
- cross-skill laundering;
- feedback poisoning;
- attack-capital evaluation.

## Contribution C5 — Calibrated judge profiles

If judge experiments are large enough:

- judge sensitivity/specificity;
- calibration curves;
- influence on downstream reputation.

## Contribution C6 — External-validity evidence

If AppWorld or another interactive environment is completed:

- comparison between answer-key feedback and state-based execution feedback.

---

# 33. What a Public Benchmark Output Actually Means

A benchmark contribution does not require inventing all underlying tasks.

HistRepEval can be a **derived evaluation framework** built on public benchmarks.

The public artifact may contain:

```text
histrepeval/
  configs/
  task_splits/
  history_generator/
  feedback_generator/
  transfer_metadata/
  attacks/
  metrics/
  baselines/
  examples/
  benchmark_card.md
```

A user can run:

```text
existing benchmark tasks
        ↓
HistRepEval generator
        ↓
longitudinal agent histories
        ↓
imperfect feedback
        ↓
target task
        ↓
reputation method
        ↓
calibration / utility / attack metrics
```

This allows future researchers to test different reputation algorithms under the same evidence conditions.

---

# 34. Why a Benchmark Could Matter

Current papers often use different:

- agent pools;
- attack definitions;
- feedback assumptions;
- trust metrics;
- domains;
- histories.

This makes comparison difficult.

A public protocol could standardize:

1. how historical evidence is generated;
2. what the online algorithm is allowed to see;
3. how feedback noise is controlled;
4. how task shift is defined;
5. how attacker history is generated;
6. how reputation calibration is evaluated.

The benchmark is valuable only if it is reproducible and genuinely tests a missing evaluation dimension.

---

# 35. Practical Meaning for LLM / Multi-Agent Research

If successful, RepGuard would contribute to the broader question:

> **How should autonomous agent systems decide which agents deserve influence when historical evidence is incomplete and context-dependent?**

Potential relevance:

## Multi-agent coordination

Improves expertise-aware aggregation.

## Agent reliability

Separates “what happened” from “how confidently we know what happened.”

## Agent security

Makes reputation manipulation quantitatively testable.

## Agent marketplaces / ecosystems

Provides a model for reputation that does not automatically treat historical success as universally transferable.

## Feedback research

Connects feedback reliability to long-term inter-agent trust rather than only single-trajectory self-correction.

---

# 36. Scientific Value Beyond Accuracy

The paper should not be sold as “ECRT improves accuracy by X%.”

The stronger scientific message is:

> **Historical performance is not a single kind of evidence. Reliability of the evaluation signal and relevance to the current task are separate questions, and a multi-agent system should not convert either into influence without considering the other.**

A strong paper would quantify when this statement matters and when it does not.

---

# 37. Scope Controls

## In scope

- heterogeneous LLM agents;
- repeated interactions;
- historical reputation;
- imperfect feedback;
- task-conditioned transfer;
- uncertainty;
- strategic manipulation stress tests;
- calibration;
- expert influence.

## Out of scope for the core six-week paper

- training new foundation models;
- full Sybil-resistance;
- cryptographic reputation systems;
- decentralized blockchain reputation;
- universal malicious-agent detection;
- sophisticated neural transfer models;
- full online reinforcement learning;
- long-horizon economic mechanism design;
- personalized human trust;
- production deployment.

---

# 38. Failure Conditions

The paper should be reconsidered if:

1. agent pool has no real heterogeneity;
2. global/skill-conditioned baselines already solve all controlled regimes;
3. Q×T manipulation produces no stable effects;
4. transfer strata cannot be defined without leakage;
5. ECRT benefits arise only from oracle information;
6. judge calibration requires target-test ground truth;
7. results depend on one model or one seed;
8. attack effects are only prompt artifacts;
9. claims overlap substantially with a newly released WEREWOLF method.

These are research findings, not reasons to hide results.

---

# 39. Recommended Paper Title Options

## Conservative

**RepGuard: Evidence-Calibrated Reputation Transfer under Imperfect Feedback in Multi-Agent LLM Systems**

## Empirical-story title

**When Should Historical Agent Reputation Be Trusted? Feedback Reliability and Task Transfer in Multi-Agent LLMs**

## Benchmark-first title

**HistRepEval: Evaluating Historical Agent Reputation under Imperfect Feedback and Task Shift**

Use the final title only after Week 3 determines whether the main contribution is method, characterization, or benchmark.

---

# 40. Draft Abstract Template

> Multi-agent LLM systems increasingly rely on heterogeneous agents whose competence varies across tasks, motivating the use of historical reputation to allocate influence. Existing reputation mechanisms, however, may treat historical success as reliable evidence even when the outcome was weakly evaluated or poorly matched to the current task. We study historical teammate reputation under imperfect feedback and distinguish two dimensions of historical evidence: feedback reliability and task transferability. Through a controlled factorial evaluation, we characterize how these dimensions affect reputation calibration, expert leveraging, and vulnerability to strategic manipulation. We then introduce Evidence-Calibrated Reputation Transfer (ECRT), which infers probabilistic historical correctness from heterogeneous feedback, discounts evidence according to task transferability, and preserves posterior uncertainty when assigning influence. [RESULTS TO BE INSERTED ONLY AFTER EXPERIMENTS.] We release [ARTIFACT TO BE CONFIRMED] to support reproducible evaluation of reputation learning under noisy feedback, task shift, and reputation-manipulation stress tests.

Do not fill the results sentence until experiments are frozen.

---

# 41. Proposed Introduction Contribution Paragraph

If results support the method, a safe contribution paragraph is:

> **Our contributions are threefold. First, we formulate historical teammate reputation under imperfect feedback as an evidence-quality problem and experimentally separate feedback reliability from historical-to-current task transferability. Second, we propose Evidence-Calibrated Reputation Transfer (ECRT), a probabilistic mechanism that combines calibrated historical feedback with task-relevant evidence while preserving uncertainty. Third, we develop a reproducible evaluation protocol that measures reputation calibration, expert leveraging, clean utility, and strategic robustness across controlled feedback and task-shift regimes.**

Avoid “first” unless a final pre-submission literature search justifies it.

---

# 42. Related-Work Comparison Matrix

| Work | Historical reputation | Skill/task conditional | Imperfect feedback modeled | Cross-task transfer | Dynamic trust | Attack focus | Main distinction from RepGuard |
|---|---:|---:|---:|---:|---:|---:|---|
| Credibility Scoring (2025) | Yes | Limited | Judge/reward quality is a dependency | No central focus | Gradual history | Adversarial agents | Does not make feedback reliability × task transfer the main evidence model |
| CogTrust (2026) | Trust history | No core skill transfer | Different trust signals | No core focus | Yes | Dynamic security | Time/dynamic trust rather than historical evidence calibration |
| SentinelNet (2026) | Credit/ranking | No | Message detector | No | Yes | Malicious detection | Detects harmful communications |
| Xia & Wang (2026) | Yes | Yes | Evidence is conditioned/borrowed | Yes across skills | Not core | Cross-skill laundering | Closest transfer-related baseline; feedback-source reliability is not the main axis |
| Trust No Tool (2026) | Trajectory trust | Task-conditioned benchmark | Yes, malicious tool feedback | Not teammate expertise transfer | Trajectory | Cognitive poisoning | Trust in tool feedback/final action, not longitudinal teammate reputation |
| DREvo (2026) | Historical experience | State-dependent | Historical evidence validity | State/harness relevance | Iterative | No teammate reputation focus | Recalibrates harness-evolution experience rather than agent reputation |
| WEREWOLF (2026) | Reputation-aware | To be checked | To be checked | To be checked | To be checked | Reputation-aware red-teaming | Must be checked before final novelty claim |
| RepGuard / ECRT | Yes | Yes | Central axis | Central axis | Optional | Stress tests | Joint evidence calibration for teammate expertise and influence |

The table must be updated if WEREWOLF becomes publicly available.

---

# 43. Literature and Reference List

1. **Ebrahimi, S., Dehghankar, M., & Asudeh, A.** “An Adversary-Resistant Multi-Agent LLM System via Credibility Scoring.” IJCNLP-AACL 2025. https://aclanthology.org/2025.ijcnlp-long.90/
2. **Xia, Y., & Wang, T.** “When Should Agent Trust Be Conditional? Characterizing and Attacking Skill-Conditional Reputation in Agent Swarms.” 2026. https://arxiv.org/abs/2606.14200
3. **Wang, J. et al.** “CogTrust: Cognitive Logic-Based Framework for Dynamic Trust Evaluation in Multi-Agent Systems.” Expert Systems with Applications, 313:131535, 2026. https://doi.org/10.1016/j.eswa.2026.131535
4. **Feng, Y., & Pan, X.** “SentinelNet: Safeguarding Multi-Agent Collaboration Through Credit-Based Dynamic Threat Detection.” WWW 2026. https://doi.org/10.1145/3774904.3792462
5. **Pappu, A. et al.** “Multi-Agent Teams Hold Experts Back.” 2026. https://arxiv.org/abs/2602.01011
6. **Yan, L. et al.** “Trust No Tool: Evaluating and Defending LLM Agents under Untrusted Tool Feedback.” 2026. https://arxiv.org/abs/2605.17453
7. **Guo, H. et al.** “DREvo: Distilling Recalibrated Historical Experience for Harness Self-Evolution.” 2026. https://arxiv.org/abs/2607.26722
8. **Liu, Z. et al.** “A Survey on the Feedback Mechanism of LLM-based AI Agents.” IJCAI 2025. https://doi.org/10.24963/ijcai.2025/1175
9. **Trivedi, H. et al.** “AppWorld: A Controllable World of Apps and People for Benchmarking Interactive Coding Agents.” ACL 2024. https://aclanthology.org/2024.acl-long.850/
10. **Wang, Y. et al.** “MMLU-Pro: A More Robust and Challenging Multi-Task Language Understanding Benchmark.” NeurIPS 2024 Datasets and Benchmarks. https://proceedings.neurips.cc/paper_files/paper/2024/hash/ad236edc564f3e3156e1b2feafb99a24-Abstract.html
11. **Poon, M., Zeng, Q., Dai, X., & Zuo, J.** “WEREWOLF: Reputation-Aware Red-Teaming for Self-Organizing LLM Multi-Agent Systems.” Findings of EMNLP 2026. Public details should be monitored before submission.
12. **Kaal, W. A.** “Empirical Evaluation of the Agentic Reputation Substrate.” SSRN, August 2026. https://doi.org/10.2139/ssrn.7261018

---

# 44. Final Project Output Checklist

At the end of the project, a reader should be able to obtain:

## Scientific outputs

- validated research gap;
- controlled Q×T empirical study;
- ECRT method;
- ablation;
- attack robustness analysis;
- uncertainty analysis;
- limitations.

## Reproducibility outputs

- code;
- environment file;
- prompts;
- model versions;
- seeds;
- experiment configs;
- generated-history protocol;
- plotting scripts;
- raw metric tables.

## Possible public benchmark outputs

- HistRepEval protocol;
- task IDs/splits;
- feedback masks;
- corruption generator;
- transfer metadata;
- attack suite;
- benchmark card;
- example histories;
- allowed cached outputs.

## Publication output

- final paper;
- appendix;
- reproducibility checklist;
- artifact README;
- citation/BibTeX.

---

# 45. Final Meaning of the Project

If the project succeeds, its contribution to multi-agent LLM research is not merely:

> “We created a better reputation score.”

The stronger message is:

> **Long-term trust between AI agents should be treated as evidence inference. A historical success should influence a new decision only to the extent that the system has reliable evidence the success occurred and that the success is informative about the competence required now.**

RepGuard tests whether this distinction matters empirically, formalizes it through ECRT, and—if the results are sufficiently robust—provides a reusable protocol for evaluating future reputation mechanisms under imperfect feedback, task shift, and strategic behavior.
