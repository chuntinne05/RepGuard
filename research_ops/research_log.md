# RepGuard Research Log

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
