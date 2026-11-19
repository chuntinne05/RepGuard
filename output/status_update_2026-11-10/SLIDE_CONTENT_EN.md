## Slide 01 — Agenda

### Update Since the 27–28 October Report

From experimental results to the research question and next validation steps.

1. **Completed Work**  
   Four evaluation settings; a new verification layer.
2. **Results and Lessons Learned**  
   Cross-model review, data errors, and grading limitations.
3. **Research Direction**  
   Existing foundations and evidence still needed.
4. **Next Steps**  
   Task allocation for Tín and Trung; conditions for proceeding.

Reporting period: from the late-October update through 10 November 2026.

*Tín & Trung · RepGuard · Progress Update · 10 November 2026 · 1 / 10*

---

## Slide 02 — Progress Since the Previous Report

**1,265 new model responses · 4 evaluation settings**

| Model responses | Evaluation setting | Scope |
|---|---|---|
| **720** | Evidence Sufficiency | 120 pairs · 24 groups |
| **288** | Financial Report QA | 24 questions · 2 prompt profiles |
| **113** | Data Workspace | 6 tasks · 36 trajectories |
| **144** | SQL with Specified Interpretations | 12 tasks · 24 cases |

### Parallel Development

Constraint and source verification + evidence for agent handoffs

**New focus: explicitly verify requirements, data, and evidence status.**

Response counts do not represent independent task counts. The previous 18,064 MMLU-Pro responses and 560 repair responses are excluded.

*Tín & Trung · RepGuard · Progress Update · 10 November 2026 · 2 / 10*

---

## Slide 03 — First Two Studies: No Clear Advantage from Cross-Model Review

### Cross-Model Review − Self-Review

Equal-weight average across both directions · percentage points · 95% CI

| Evaluation setting | Scope | Difference | 95% confidence interval |
|---|---|---|---|
| Evidence Sufficiency | 120 pairs / 24 groups | **+2.08** | [−0.42; +4.59] |
| Financial Report QA | 24 questions / 24 groups | **+2.08** | [−4.17; +8.33] |

← Self-review performs better

Cross-model review performs better →

**Both confidence intervals include zero; reputation learning remains on hold.**

Sources: cycle01 and ARQA cycle02, 9 November. These are separate studies; their results are not pooled to estimate a common effect.

*Tín & Trung · RepGuard · Progress Update · 10 November 2026 · 3 / 10*

---

## Slide 04 — Real Data Workspaces: Task Completion Must Also Be Measured

**113 model responses**

6 tasks · 36 trajectories · CSV / JSON / SQLite / PDF

### Output Outcomes Across All 36 Trajectories

| Count | Outcome | Interpretation |
|---|---|---|
| **9** | Match the reference | Correct under strict relation matching. |
| **14** | Table produced, but no match | Requires distinguishing content, interpretation, and output-shape errors. |
| **13** | No final table | Source discovery, budget, or output-length constraints remain unresolved. |

**Distinguish “unfinished” from “output produced but requirements not met.”**

Adapted DataSpace tasks; diagnostic results combined from two collection blocks affected by interruptions. This is not an official confirmatory score.

*Tín & Trung · RepGuard · Progress Update · 10 November 2026 · 4 / 10*

---

## Slide 05 — Three Error Types to Distinguish

### 1. Wrong Attribute

**Fund manager nationality**

Person name / fund name

Used as a proxy for nationality

↓

`Nationality` + correct join

Verify both the field and the join.

### 2. Unresolved Interpretation

**“Fund abbreviation”**

`SecuAbbr`

or

`ChiNameAbbr`

The intended interpretation requires adjudication.

### 3. Extra Output Column

**Correct name sequence, extra ID column**

Procedure name | ID

Strict relation matching: no match

Keep the original score unchanged.

**Verifying correctness requires clear requirements and evidence tied to the correct sources.**

Tasks 380 / 371 / 44; development analysis without independent semantic adjudication. Gold references are not revised to fit model outputs.

*Tín & Trung · RepGuard · Progress Update · 10 November 2026 · 5 / 10*

---

## Slide 06 — Verification and Handoff Layer Implemented

### Host-Managed Constraints + Source Catalog

The verification layer is implemented; the diagram below shows its integration flow with agents.

**SQL-Generating Agent**  
Actual draft

→ **Verification Layer**  
Query + source

→ **Reviewer Agent**  
Receives evidence

→ **Re-execution**  
Output artifact

**Met · Violated · Unresolved**

| Result | Validation |
|---|---|
| **29** | New tests |
| **87** | Scoped tests passed |
| **20/20** | SQL re-executions reproduced output bytes |

**A reproducible component is in place; its effect on error correction still requires a separate experiment.**

V5 supports a subset of SQL; development contracts require independent review. Reproducing 20/20 outputs does not mean 20/20 answers are correct.

*Tín & Trung · RepGuard · Progress Update · 10 November 2026 · 6 / 10*

---

## Slide 07 — Evaluation Setup for New Databases

**204 tasks · 12 databases**

Pinned SpecBridge revision · split by database

| Split | Tasks | Status |
|---|---|---|
| Development | **45** | Opened for development |
| Validation | **67** | Not yet evaluated |
| Reserved | **92** | Not yet evaluated |

### 90/90 Reference SQL Queries Passed Grader Qualification

Controls: wrong-interpretation, extra-row, and missing-output cases were all rejected.

**Pin both the grader and the execution engine: one task’s grading outcome changed between SQLite 3.42 and 3.51.**

Qualification checks the grader. Of the 90 reference queries, 74 contain CTEs or multiple query scopes and are not fully covered by the current V5 checker.

*Tín & Trung · RepGuard · Progress Update · 10 November 2026 · 7 / 10*

---

## Slide 08 — Latest SQL Pilot: Self-Review Scored Higher

**12 tasks × 2 specified interpretations = 24 cases**

3 development databases · 144 model responses · audit PASS

| Workflow | Correct cases |
|---|---|
| A — Direct generation | **18/24** |
| B — Direct generation | **19/24** |
| AA — Self-review | **21/24** |
| BB — Self-review | **21/24** |
| AB — Cross-model review | **19/24** |
| BA — Cross-model review | **20/24** |

### −6.25 Percentage Points

Cross-model review − self-review  
Average across both directions

**Development-set results; no confirmation on held-out sources and no V5 checker intervention tested yet.**

A = Qwen; B = Gemma. The 24 variants are dependent within 12 tasks. The same two-call ceiling does not imply equal actual cost.

*Tín & Trung · RepGuard · Progress Update · 10 November 2026 · 8 / 10*

---

## Slide 09 — Research Question for Further Validation

**Do verified handoffs improve correction accuracy when sources, tools, and budgets are held constant?**

### Existing Foundations

- An error bank traceable to source data
- A verification layer and reproducible execution logs

### Isolating the Added Benefit

- Self-review / neutral recheck
- Correct / shuffled diagnostic feedback
- The same checker; validation on new sources

### Outcomes to Measure

Correct task completion · rescues / harms · false stops · coverage · total cost

**Target contributions: an adjudicated error bank + tooling + evidence from controlled comparisons.**

Contracts and handoffs have close prior work. Novelty has not been established; strong baselines, independent adjudication, and user evaluation are still missing.

*Tín & Trung · RepGuard · Progress Update · 10 November 2026 · 9 / 10*

---

## Slide 10 — Next Steps and Task Allocation

Proposed task allocation · priorities depend on readiness

### Tín

1. Measure / extend SQL coverage
2. Strong baselines with the same tools and checker
3. Experimental harness and token / timing logs

**Deliverables: coverage report + reproducible baseline results**

### Trung

1. Source-only review + rubric
2. Compare proposed contributions with prior work
3. Identify a workflow and recruit pilot users

**Deliverables: review forms + pilot workflow**

### Joint Work

Peer review → freeze the protocol → test the mechanism → evaluate on held-out sources

**Before scaling up, the next phase needs an unambiguous evaluation setup and sufficiently strong controls.**

No users have participated yet. Evaluation on held-out sources will begin after the mechanism is frozen and readiness checks are complete.

*Tín & Trung · RepGuard · Progress Update · 10 November 2026 · 10 / 10*
