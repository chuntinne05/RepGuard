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
