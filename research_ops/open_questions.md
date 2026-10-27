# Open Research Questions

## Purpose
Track unresolved research questions that need answers before
the paper can be finalized. Questions are closed with a decision
and supporting evidence.

---

## Active Questions

### OQ-1: Model pool composition
- **Question:** Which agent policies have reproducible complementary strengths that a deployable selector can predict before seeing the answer?
- **Evidence:** The 18,064-answer real Week 3 rerun found only one confirmed domain specialist, and subject routing scored 47.19% versus 47.76% for the best single direct model. In the later 420-question thinking pool, the strongest policy scored 280/420, while cross-fitted subject routing scored 274/420. See `docs/analysis/repguard_week3_real_report.md` and `docs/analysis/repguard_pool_gate_assessment_2026-09-30.md`.
- **Status:** OPEN / GATE 0 STOP for the current MMLU-Pro generalist pool. The 2026-09-28 small-pilot PASS was superseded by these real-answer analyses. A different pool or interactive environment must pass a new complementarity gate before a DART method claim.

### OQ-3: Task transfer estimation method
- **Question:** Should transfer use metadata hierarchy or held-out correlation?
- **Evidence:** ECRT currently uses fixed subject-cluster transfer weights (same 1, related 0.5, unrelated 0). The Week 3 taxonomy was not independently validated as a skill measure; zero transfer also forces a prior mechanically.
- **Status:** OPEN — learn or validate task/skill similarity on training data and test its decision value on new IDs before replacing the fixed taxonomy.

### OQ-4: Judge model selection
- **Question:** Which model(s) to use as LLM-as-a-Judge?
- **Constraints:** Should be different from agent models to reduce correlation
- **Evidence:** Qwen3 14B supplied real candidate-conditioned feedback and an exploratory blind-judge comparison on the same 280 history questions. The blind prompt was selected after inspecting candidate-conditioned errors; Qwen3 14B is also a solver in the later pool.
- **Status:** OPEN — freeze the blind prompt, evaluate fresh task IDs and a judge from another model family, then measure downstream decision value at matched cost.

### OQ-5: WEREWOLF paper status
- **Question:** Has WEREWOLF been publicly released?
- **Action:** Check arXiv and EMNLP 2026 proceedings at end of Week 1
- **Status:** OPEN — monitoring

---

## Closed Questions

### OQ-2: MMLU-Pro split sizes
- **Question:** Are the 60/20/20 split ratios implemented reproducibly?
- **Decision:** The deterministic seed-42 split has 7,241 train/calibration, 2,375 dev, and 2,416 test questions across all 14 subjects.
- **Limit:** This closes the partitioning question, not transfer-taxonomy validity or external generalization.
