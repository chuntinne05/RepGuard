# Paper Claims Tracker

## Purpose
Track which paper claims are supported by experimental evidence.
A claim must NOT appear in the paper unless it has a corresponding
experiment entry with supporting data.

---

## Contribution Claims

### C1 — Empirical characterization of feedback reliability × task transferability
- **Status:** NOT YET TESTED
- **Supporting experiments:** (pending Week 3 Q×T grid)
- **Required evidence:** Heatmap, effect sizes, CIs

### C2 — ECRT method improves reputation calibration
- **Status:** NOT YET TESTED
- **Supporting experiments:** (pending Week 4)
- **Required evidence:** Main results table, ablation

### C3 — HistRepEval evaluation protocol
- **Status:** SUPPORTED (Week 2 HistRepEval v0.1 protocol completed & validated)
- **Supporting experiments:** Step 1.1 Capability Audit (4 real models, 8 domains), Week 2 Baselines Benchmark (5 methods), Feedback Corruption Q-Sweep (8 regimes), Task-Mismatch Demonstration.
- **Required evidence:** Protocol code (src/repguard/reputation/), reproducible runner (run_week2.py), 40 passing unit tests, and empirical logs in research_ops/experiment_registry.csv.

### C4 — Strategic stress-test analysis
- **Status:** NOT YET TESTED
- **Supporting experiments:** (pending Week 5)
- **Required evidence:** Attack-capital curves

---

## DO NOT CLAIM as novel
(See research proposal Section 4 and 6-week plan Section 2)

- Historical credibility/reputation (Ebrahimi et al. 2025)
- Skill-conditioned reputation (Xia & Wang 2026)
- Cross-skill laundering attacks (Xia & Wang 2026)
- Dynamic trust / time decay (CogTrust 2026)
- Malicious-agent detection (SentinelNet 2026)
- Reputation-aware red-teaming (WEREWOLF 2026)
- Untrusted tool feedback (Trust No Tool 2026)
- Historical experience recalibration (DREvo 2026)
