# Open Research Questions

## Purpose
Track unresolved research questions that need answers before
the paper can be finalized. Questions are closed with a decision
and supporting evidence.

---

## Active Questions

### OQ-1: Model pool composition
- **Question:** Which 4-6 LLM backbones should form the agent pool?
- **Constraints:** Need genuine heterogeneity (best agent must change across domains)
- **Candidates:** GPT-4o, GPT-4o-mini, Claude 3.5 Sonnet, Claude 3 Haiku, Llama 3.1, Gemini
- **Decision criteria:** Per-domain capability audit (Week 1 exit criterion)
- **Status:** OPEN — pending API key availability

### OQ-2: MMLU-Pro split sizes
- **Question:** Are the 60/20/20 split ratios appropriate?
- **Considerations:** Need enough calibration data for feedback-source estimation
- **Status:** OPEN — validate after initial data loading

### OQ-3: Task transfer estimation method
- **Question:** Should transfer use metadata hierarchy or held-out correlation?
- **Dependencies:** Needs per-domain capability audit first
- **Status:** OPEN — defer to Week 2

### OQ-4: Judge model selection
- **Question:** Which model(s) to use as LLM-as-a-Judge?
- **Constraints:** Should be different from agent models to reduce correlation
- **Status:** OPEN — defer to Week 2

### OQ-5: WEREWOLF paper status
- **Question:** Has WEREWOLF been publicly released?
- **Action:** Check arXiv and EMNLP 2026 proceedings at end of Week 1
- **Status:** OPEN — monitoring

---

## Closed Questions

(None yet)
