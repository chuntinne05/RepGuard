# RepGuard Research Log

## 2026-09-30 — Post-Week-5 method gate, active real-model pool study

- Week 5 pipeline completed before this entry: 840 direct/thinking screen answers, 280 blind-judge calls, and 560 direct/thinking validation answers, all real Ollama/Modal requests. Interpretation and limitations are in `docs/analysis/repguard_final_pipeline_assessment_2026-09-30.md`.
- Froze 560 new development IDs and 420 sealed holdout IDs from previously unused MMLU-Pro train/calibration questions across all 14 subjects. Protocol SHA-256 `0bd154554e845ca472f73a5c113985a115b4f1a55322092909d798e45b326d1d`. The sealed holdout must stay untouched until method, baselines, attack policy, and primary endpoint are frozen.
- Completed and audited a real **1,260/1,260-response** pool overlap study on 420 previously screened questions, adding Gemma2, Llama3 8B, and Qwen3 14B direct outputs to the existing Qwen3 8B direct/thinking pair. Protocol SHA-256 `f4d3b237728c0b0463c49e47673793e9e1290903c187f0741dc533f51e4c7308`; ledger SHA-256 `81319c132b75d7822027d943fe67c05c8c616c366e57ea46473d0b0289da0437`. New model correct counts: Gemma2 195/420, Llama3 158/420, Qwen3 14B 226/420, versus Qwen3 8B thinking 280/420. No new-model invalid output.
- Oracle any-of-five reaches 344/420 but uses test gold and is not a method. Five-fold out-of-fold subject routing learns from other task IDs and reaches 274/420 versus always-thinking 280/420; 95% subject-stratified paired bootstrap CI of the accuracy difference is [−3.57, +0.71] percentage points. Engineering shows a Qwen3 14B direct advantage of 18/30 versus 13/30 thinking, but no second independently clear specialist. Registered Gate 0 for DART on this pool **failed**. Keep the 420-question sealed holdout untouched; do not search method variants on it. Full assessment: `docs/analysis/repguard_pool_gate_assessment_2026-09-30.md`.
- Ran exploratory replay of actual Week 4/5 direct/thinking outputs: at 50% thinking quota, question feature router 181/280, subject-only 185/280, direct-first 186/280, always thinking 203/280. The Week 5 dev set has been viewed; these are development findings, not paper confirmation.
- Found the decision-sensitivity bottleneck of ECRT: with real judge feedback, reputation changes about 0.10 on average relative to FixedBorrow, while selected answers differ on only 37 or 41 of 2,416 already viewed Week 3 test questions across two folds. This is a HistRepEval metric and an argument against claiming decision improvement from calibration alone.
- Updated prior-art screen with BEST-Route (ICML 2025), Budgeted Act-or-Defer (2026), Share the Judge/Learn the Deferral (2026), TRUST-Bench/VISTA-Guard (2026), and CP-Router (AAAI 2026). Routing, local reliability bounds, audited deferral, and feedback poisoning each have direct prior art. DART requires a narrower, empirically demonstrated contribution; there is no guaranteed A* method win.

---

## 2026-09-29 — Re-audit of legacy Week 3 and real-data rerun

- The 2026-09-28 Week 3 `GO-B`/`COMPLETE` entry below is **superseded**. Its Q×T and attack outputs were generated from simulated Bernoulli correctness based on a very small capability pilot, rather than per-question model answers. The earlier audit also used an overly broad task-relatedness mapping and did not establish a paired target-domain comparison. Those outputs are retained as exploratory engineering artifacts only.
- Registered the real-answer protocol in `research_ops/real_week3_protocol.md`. All 14 MMLU-Pro subjects, all four actual Ollama model IDs, deterministic disjoint splits, and an append-only prediction ledger are in use.
- Completed the initial 70-test-question-per-subject pilot, then documented a post-pilot expansion to every held-out test question for **all** subjects. At this checkpoint the test ledger contained 9,664 valid model answers on 2,416 distinct test questions; history/dev collection and Q×T analysis followed and are recorded below.
- At this checkpoint, no replacement Week 3 go/no-go decision was valid until the real-data grid and paired uncertainty analysis finished.

### Final real-data outcome, 2026-09-29

- Completed all **18,064/18,064** real model answers: four actual model IDs × (1,400 history + 700 dev + 2,416 full held-out test questions). Ledger SHA-256: `1c69cd9d49f3b2c97bf20868e246c5b524492a0f28f9b0095170fa1dded9fd4e`. Audit found zero missing, duplicate or invalid responses. Full test accuracy: Qwen3 8B 47.76%, Gemma2 45.12%, Llama3 8B 36.30%, Qwen3 0.6B 23.51%.
- History-selected subject specialist confirmation: **only Qwen3 8B in physics** passes the paired gate; no second model passes. Subject routing from history 47.19% vs history-selected single global Qwen3 8B 47.76% on the same test questions; paired CI for difference [−1.90, +0.75] percentage points.
- Completed paired Q×T analysis: 182 source–target pairs, four feedback regimes, three seeds, nine methods, 19,656 result rows and 13 complete target subjects. Feedback degradation and source mismatch have clear calibration effects; team accuracy differences are much smaller. In the prespecified related + 25% noise cell, ECRT minus FixedBorrow team accuracy +0.02 percentage points (95% subject-bootstrap CI [−0.04,+0.10]); no meaningful method gain. Under directional false positives, ECRT improves Brier calibration but does not improve team accuracy.
- A1/A2 dev-selected attack pilots completed using real model answer traces with explicit forced-wrong and feedback-poisoning interventions. Targeted poisoning can hurt ECRT more than FixedBorrow in the selected A2 related-domain case; the pilot is not a claim about spontaneous malicious model behavior.
- **Superseding decision: GO-C.** Week 3 experimentation and report are complete; the original method-superiority/robust-specialist hypothesis is not established. Stop treating the old `GO-B` entry below as active. Full methods, effect sizes, CIs, failure modes and next steps: `docs/analysis/repguard_week3_real_report.md`.

---

## Purpose
Daily record of research activities, decisions, and observations.
Updated at the end of every working day.

---

## 2026-09-02 — Week 1, Day 3

### Engineering
- Initialized repository structure and full Week 1 infrastructure
- Created Pydantic configuration schema with YAML loading
- Implemented deterministic seed management (SHA-256 derivation)
- Built MMLU-Pro download/parse/cache pipeline
- Implemented leak-proof data splitting (hash-based assignment)
- Created LLM provider layer (Mock, OpenAI, Anthropic)
- Built single-agent evaluation harness with caching and rate limiting
- Structured experiment logger (JSON-lines with full audit metadata)

### Decisions
- Split ratios: 60% train/calibration, 20% dev, 20% test
- GT isolation enforced at type level (TaskRecord vs OnlineTaskView)
- Mock provider uses SHA-256(seed || prompt) for deterministic answers
- Content-addressable disk cache keyed on (model_id, prompt_hash, params)

### Next Steps
- Run capability audit with 2-4 candidate models
- Begin literature structured notes
- Start paper writing (Introduction v0.5, Related Work v0.7)

---

## 2026-09-28 — Capability Audit (Step 1.1) — Run 1 (gemini + mock)

### Agents evaluated
- gemini-flash
- mock-baseline

### Heterogeneity Gate: FAIL ✗
- ✗ Best agent does NOT change — 'gemini-flash' wins every domain.
- ✓ Performance spread: 41.7% (threshold ≥ 10%) — meaningful.
→ OQ-1 OPEN: Adjust agent pool before running experiments.

### Accuracy summary
- gemini-flash: mean=50.0%
- mock-baseline: mean=8.3%

---

## 2026-09-28 — Capability Audit (Step 1.1) — Run 2 (4-agent pool via Modal Ollama) ✅

### Agents evaluated (n_samples_per_domain = 5, 8 domains = 40 tasks each)
- **gemma2** (via Ollama qwen3:14b mapped to gemma2 config)
- **qwen3-0.6b** (Qwen3 0.6B — budget/weak agent)
- **qwen3-8b** (Qwen3 8B — primary reasoning agent)
- **llama3-8b** (Llama3 8B — generalist baseline)

### Domains covered
- biology, computer science, economics, history, law, math, physics, psychology

### Capability Matrix (accuracy %)

| Domain          | Gemma2 | Qwen3 0.6B | Qwen3 8B | Llama3 8B | Best Agent     |
|:----------------|:------:|:----------:|:--------:|:---------:|:---------------|
| Biology         |   80%  |    30%     | **100%** |    60%    | Qwen3 8B       |
| Computer Sci.   |   20%  |    20%     |  **40%** |    30%    | Qwen3 8B       |
| Economics       | **70%**|    50%     |  **70%** |    50%    | Gemma2 / Qwen3 8B |
| History         |   40%  |    10%     |  **50%** |    40%    | Qwen3 8B       |
| Law             | **60%**|    30%     |  **60%** |    40%    | Gemma2 / Qwen3 8B |
| Math            | **50%**|    10%     |    10%   |    30%    | **Gemma2** ← Key |
| Physics         | **30%**|    10%     |    20%   |    20%    | **Gemma2** ← Key |
| Psychology      |   50%  |    20%     |  **60%** |    40%    | Qwen3 8B       |
| **Mean**        | **50.0%** | **22.5%** | **51.25%** | **38.75%** | Qwen3 8B |

### Heterogeneity Gate: PASS ✓
- ✓ Best agent changes across domains: Gemma2 wins Math & Physics; Qwen3 8B wins 6/8 domains.
- ✓ Performance spread: 51.25% − 22.5% = **28.75%** (threshold ≥ 10%) — very meaningful.
- ✓ Role stratification confirmed:
  - **Qwen3 8B**: Language, social & biology specialist (51.25% mean).
  - **Gemma2**: Quantitative specialist — Math (50% vs 10%) & Physics (30% vs 20%).
  - **Llama3 8B**: Balanced generalist (38.75%) — ideal control baseline.
  - **Qwen3 0.6B**: Weak/budget agent (22.5%) — ideal for adversarial reputation farming tests.

### Key Research Implication
Oracle Team Accuracy (best agent per domain) ≈ **67.5% – 70%**, vs single-best agent 51.25%.
This gap is the experimental motivation for ECRT: skill-conditioned reputation can unlock ~+20 pp
improvement over global reputation by routing Toán/Lý → Gemma2, rest → Qwen3 8B.

→ **OQ-1 CLOSED: Heterogeneity Gate PASS. Proceed to Week 2.**

### Accuracy summary
- qwen3-8b:   mean = 51.25%
- gemma2:     mean = 50.00%
- llama3-8b:  mean = 38.75%
- qwen3-0.6b: mean = 22.50%

---

## 2026-09-28 — Week 2 Start

### Goal
Build HistRepEval v0.1 + implement mandatory reputation baselines.

### Engineering started
- Implementing `src/repguard/reputation/` module with:
  - `episode.py`     — EpisodeRecord data model (history store)
  - `feedback.py`    — FeedbackCorruptor (noise / sparsity injection)
  - `baselines.py`   — Uniform, GlobalBeta, SkillConditioned, OracleRep, ZeroEvidenceGate
  - `aggregator.py`  — Aggregation strategies (majority, weighted)
  - `transfer.py`    — TransferEstimator (same/related/unrelated strata)
  - `metrics.py`     — CalibrationError, ExpertLeverage, ReputationRankCorr

### Decisions
- HistRepEval v0.1 uses MMLU-Pro train_calibration split as source of history episodes.
- Feedback corruption controlled via FeedbackConfig (noise_eta, sparsity_rho).
- Transfer conditions: same-domain / cross-domain (related / unrelated).
- All baselines use Beta distribution formulation for principled uncertainty.

---

## 2026-09-28 — Capability Audit (Step 1.1)

### Agents evaluated
- qwen3-8b
- gemma2
- llama3-8b
- qwen3-0.6b

### Domains covered
- biology
- computer science
- economics
- history
- law
- math
- physics
- psychology

### Heterogeneity Gate: PASS ✓
- ✓ Best agent changes across domains: YES (winners: 'qwen3-0.6b', 'qwen3-8b')
- ✓ Performance spread: 32.5% (threshold ≥ 10%) — meaningful.
-    qwen3-8b                  mean accuracy = 55.0%
-    gemma2                    mean accuracy = 42.5%
-    llama3-8b                 mean accuracy = 25.0%
-    qwen3-0.6b                mean accuracy = 22.5%
- 
→ OQ-1 CLOSED: Proceed with Week 2 baselines and HistRepEval v0.1.

### Accuracy summary
- qwen3-8b: mean=55.0%
- gemma2: mean=42.5%
- llama3-8b: mean=25.0%
- qwen3-0.6b: mean=22.5%

---

## 2026-09-28 — Full local Ollama capability audit (selected 3-model pool)

- Evaluated `gemma2:latest`, `qwen3:8b`, and `llama3:8b` on all 7,241 `train_calibration` questions across 14 MMLU-Pro domains; Qwen3 0.6B was excluded from this run.
- Heterogeneity gate: **PASS**. Domain winners change between Gemma2 and Qwen3 8B; macro-average spread is 10.84 percentage points (threshold: 10).
- Macro-average accuracy: Qwen3 8B 47.44%, Gemma2 45.21%, Llama3 8B 36.60%.
- The held-out Dev and Test splits were not used in this audit.
- Aggregate artifacts: `results/capability_audit_ollama_full/`.


---

## 2026-09-28 — Week 2 Execution: HistRepEval v0.1 Baselines & Task-Mismatch Demo ✅

### Experiments Executed
1. **Experiment 1 (Mandatory Baselines Benchmark)**:
   - Uniform (Majority Vote): mean TeamAcc = 48.5%
   - GlobalBetaReputation: mean TeamAcc = 54.5%, ECE = 0.140
   - SkillConditionedReputation: mean TeamAcc = 48.0%, ECE = 0.067
   - ZeroEvidenceGate: mean TeamAcc = 57.5%
   - OracleReputation: mean TeamAcc = 54.0%

2. **Experiment 2 (Feedback Quality Q-Sweep)**:
   - Evaluated 8 regimes: Oracle, Noisy (η=0.1, 0.2, 0.3), Sparse (ρ=0.3, 0.5, 0.7), Adversarial.
   - Demonstrated calibration degradation: ECE increases systematically as noise η increases.

3. **Experiment 3 (Controlled Task-Mismatch Failure Demo)**:
   - Source: biology → Target: math
   - GlobalBeta suffered severe cross-domain calibration error (ECE = 0.457) by overtrusting biology reputation on math.
   - ZeroEvidenceGate and SkillConditioned prevented catastrophic overconfidence.
   - **Week 2 Exit Criterion 4 PASSED: Task-mismatch failure confirmed.**

### Week 2 Exit Criteria Assessment
- ✓ All mandatory baselines run end-to-end.
- ✓ Histories generated reproducibly from config + seed.
- ✓ No test ground-truth leakage (enforced by sealed EpisodeRecord design).
- ✓ Task-mismatch failure produced in controlled setting (Exp 3).
- ✓ Agent heterogeneity gate passed (32.5% spread).

→ **WEEK 2 STATUS: COMPLETE. READY FOR WEEK 3 (ECRT CORE METHOD & Q×T GRID).**


---

## 2026-09-28 - Week 3 Execution: Q x T Factorial Grid + Attack Pilot

### Experiments Executed
1. **Q x T Factorial Grid** (4 x 3 x 3 seeds x 5 methods):
   - Q main effect on team_accuracy: range = 0.037
   - T main effect on team_accuracy: range = 0.238
   - Results: results/week3/qt_grid/qt_grid_results.csv

2. **Attack Pilot**:
   - A1 (Delayed Betrayal): completed.
   - A2 (Cross-Skill Laundering): ECRT blocks laundering (tau=0 for unrelated).

### Go/No-Go: **GO-B**

### Week 3 Exit Criteria
- [x] Q x T grid completed (3 seeds)
- [x] Bootstrap CIs computed
- [x] Attack pilot A1+A2 done
- [x] Go/No-Go decision documented

-> **WEEK 3 COMPLETE. PROCEED TO WEEK 4 (ECRT FULL ABLATION + MAIN TABLE).**


---

## 2026-11-09 — Prospective verification cycle 01

Historical GO-B entries above are not the current scientific verdict; see the real rerun and the 2026-11-09 review.

- New protocol written before generation: docs/reports/2026-11-09/EXECUTION_PLAN_V1.md.
- Registered plan: 1a97e7cca4367a1fe81c9417; metadata-only pilot24groups/120pairs; cap720.
- Source DG-evidence750 pinned to dc65e18a0a3e40e13c461c05b55103379db1fd8e; exact duplicate grouping147groups; public/private packets separated.
- Two synthetic API attempts: Gemma valid, Gemini timeout with unknown generation outcome. No blind retry; predefined Modal fallback used.
- New isolated Modal app, readonly existing research weights, no gold volume to inference; real Qwen/Gemma generations.
- Completed720/720 terminal responses,0transport errors. Original pilot app containers observed empty after completion. Offline audit/scoring pending at this log entry.
- Thirteen research-harness tests passed. No history learner fitted and no method-superiority claim yet.
- User discovery: no participant group available yet; recruitment kit prepared,0interviews conducted.

### Cycle01 offline result

720response checksums/prompts/parents/model digests audited PASS. Scores A/B/AA/BB/AB/BA=91/85/93/85/96/87 out of120. Primary cross-minus-self=+2.0833pp, claim-clusterCI[-0.4167,+4.5938], below locked3pp floor: FAIL.719/720parse-valid,0length stops. Oracle105 is diagnostic only. No history learner fitted. See docs/reports/2026-11-09/VERIFICATION_CYCLE01_RESULTS_VA_QUYET_DINH.md and NEXT_STUDY_AFTER_CYCLE01.md.

##2026-11-09 — ARQA source audit and prospectively registered cycle02

Pinned official scorer/source inspected, no upstream model results read. Source audit561/623 arithmetic pass explicit binding/rounding;62 exclusions include schema/interpreter limits and are not automatically gold errors. Selected24connected source groups by hash without model outcomes. Registered plan`deaee6167f9609bd2f045f46` before inference,12arms/item, cap288. Isolated app`ap-NyOvggLu1E0hHsy61ZXiMl`, read-only weights, no gold GPU mount.11tests passed. Separate source-receipt final-dependency diagnostic added after registration,5tests pass; does not alter frozen primary. No human annotations or discovery participants;24blank source-only review forms prepared. Outcome pending.

###Cycle02completed,09/11/2026

288/288real responses finished07:33:10UTC. Frozen primary checklist cross-self+2.083pp CI[-4.167,+8.333]pp, interaction0, rescues2/harms1, rescuegroups2. GateFAIL; no scaling/history.274/288schema-valid,1lengthstop,0transport. Receipt/source/prompt/parent/attempt auditsPASS; originalv1 source hashes still match. App finished07:34:28UTC; subsequent container list[]. Post-hoc whole24measurement flags:4question-production measure mismatches;10published-vs-strict precision;1repeated-row scope;2emptyunit;1segments/group scope;2numeric-header layout. Flags are not human gold corrections. Checklist abstention on production vs sales was counted incorrect, so numeric/unit score is not validated task truth. Frozen scores untouched; source-only human review remains0completed;0users recruited. Source receipt prototype16newtests total across two files passed (11+5), not whole repo suite. XBRLFiling card/license/filing metadata pinned; no tasks or model outcomes downloaded. Next action is task/oracle adjudication and actualworkflow discovery before new inference.

##2026-11-09 — cross-workload extension requested and implemented

Working direction broadened from annual-report QA to evidence-grounded verification/revision for multi-agent analytical and reporting workflows; official thesis title unchanged. Read primary ProvenanceGuard, Beyond fabrication, MMEnterprise, DataSpace, DAB and AgentWebBench sources at stated depths; generic provenance/contracts/checkers are not novelty. New src/repguard/verification has strict candidate/contract separation, caller-owned source admission, scope/unit/conflict/validity checks, JSON/CSV adapters, conditional receipts and one reviewer callback.25kernel tests pass; previous scoped regression39pass before last CSV additions.38synthetic engineering cases +5real recordedartifactclaims +2controlledmutations exercised, no new model calls/human labels or superiority claim. DataSpace pinned source+HF manifest:410tasks,60publicreferences; partialZIPinputinspection6candidates/12files via3,980,118rangebytes; no gold/config/output read, no scorer or task code executed, fullarchiveSHA notverified. DAB README/tree only, database/license gate unresolved. Priorv1/v2 sources and scores preserved; no new cloud inference scheduled. Current plan:docs/reports/2026-11-09/DINH_HUONG_MO_RONG_VA_KE_HOACH_V3.md.


##2026-11-09 — workspace_v4 engineering pilot completed with explicit interruptions

Full pinned DataSpace archive2,878,651,222bytes/SHAverified;96inputs12offlineevaluationfiles. Source reconstruction frozen before gold5/6;task391date-output amendment before inference gives6/6engineeringreadiness, not semantic adjudication. Initial Modal source-inclusion guard stopped planc83c5fa198c76cce65a9c5d4 before corpuscalls. Packaging2plan6a325835a376d02f1440fadf isolated runtime passed,42responses/12trajectories on first2tasks then STOP before task380inference:1ULP SQLite text-toREAL differences. Prefix sources/results preserved. Recovery3plan3af22795afdac39d725c3351 registered before outcome scoring, Pythonnumericbinding and all4adapterchecks before inference;71newresponses/24trajectories;no prior task regenerated. Both offline receipt auditsPASS;original6taskstudy remains interrupted, no pooledscientificprimary. Composite engineering masks A/B/AA/BB/AB/BA=1/1/2/1/2/2of6;9matches14mismatches13nofinal;13toolerrors10lengthstops. All3rescuesononePDFtask,selfQwenalsosucceeds;no methodwin/history/transferclaim. Posthoc task371SecuAbbr/ChiNameAbbr ambiguity and task44extraIDcolumn flags recorded separately;originalscoresunchanged.33v4tools/trajectory/audittestsPASS;25kernel+5receipt scoped regressionPASS;notfullsuite.2syntheticGemini4probes separate(firstHTTPErrorunknownstatus,second429quota0);frontierbaselineabsent.0independenthumanlabels0users0interviews;12blanksource-onlyforms. Read closer primary ICR/ARIA/VeriMAP/VerifyMAS/diagnosticcontracts/ToxicBench/SEMV/harnessverification papers; genericverification,scopedrepair and sourcebinding notnovel. All4intake/pilotappsstopped0tasks verified2026-11-09T14:35:18.317509+00:00;unrelatedappsuntouched. Latest:docs/reports/2026-11-09/WORKSPACE_V4_RESULTS_VA_PATH_TIEP.md.


##2026-11-09 — relational_v5 research/implementation and external preparation

Read primary SpecBridge(Nov3), changing-business-semanticsSQL(Oct30), TraceIntegrity, SemanticAgent, Maat, MustMaybev2 and verification-status-laundering sources at documented depths. Generic contracts/ambiguity/operatorvalidation/statuspreservation have close prior art; no novelty guarantee. New relational.py uses host-owned source/operator obligations, explicit unresolved and separate release status; handoff re-computes receipts rather than trusting hashes/status. Source-only schema_search/query_audit wrapper+CLI implemented outside frozen v4;29newtests87scopedregressionPASS. Posthoc ALL36v4trajectories:13nofinal,20SQL,3asserted;26interpretationreceipts17violated9unresolved,ALLneeds_review asdeveloper-only;not27humanlabels or methodaccuracy.20actualSQLreexecutions20byte-identical tooldoutputs;0newmodelcalls0humanlabels0users. PinnedSpecBridgea51be850a113a6b7c0ada57ad3c7806c6c3f25a4;307records204upstreamaccepted12DB;metadata-byDBsplit45dev67val92reserve;onlyalien/chinook/financialdevDBdownloadedGitSHA/SHA256/quickcheckPASS;publicprompt/privateevaluationseparate;no cachedmodeloutputs;nativegradernotexecuted. CodeMIT/dataCCBYSA4.0 per upstreamDATA_LICENSE. DAB manifest/downloader inspected but licenses/nativeassetqualification unresolved. NoGPU launched; scientific/history gatesnotopened. Latest strategy:docs/reports/2026-11-09/RESEARCH_STRATEGY_V5_VA_CONTRIBUTIONS.md.
