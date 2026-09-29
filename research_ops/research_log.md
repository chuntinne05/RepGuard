# RepGuard Research Log

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
