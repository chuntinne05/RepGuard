# Paper Claims Tracker

**Evidence audit, 2026-09-29:** The legacy Week 2/3 outcome tables and the
eight-subject, five-question capability pilot are exploratory. They do not
support publication claims because Week 3 model answers were simulated from
aggregate accuracies. The real-answer rerun now covers all 14 MMLU-Pro
subjects and is complete: 18,064 model answers, 19,656 Q×T rows, and A1/A2
controlled-intervention pilots. See `docs/analysis/repguard_week3_real_report.md`.

## Purpose
Track which paper claims are supported by experimental evidence.
A claim must NOT appear in the paper unless it has a corresponding
experiment entry with supporting data.

---

## Contribution Claims

### C1 — Empirical characterization of feedback reliability × task transferability
- **Status:** SUPPORTED FOR CALIBRATION ON THIS BENCHMARK; team-outcome interaction not established; external confirmation pending.
- **Supporting experiment:** Real Week 3 Q×T grid (four Q regimes × three T strata × three seeds × nine methods; 13 complete target subjects), with target-cluster bootstrap. GlobalBeta same-subject Brier rises by 0.0290 under 50% noise (95% CI [0.0200, 0.0385]); same vs related oracle Brier differs by 0.0265 (CI [0.0133, 0.0421]). Feedback×transfer interaction on Brier exists in selected contrasts, but transfer weights with `tau=0` cause a mechanical prior in unrelated cells.
- **Do not claim:** Robust team-accuracy Q×T interaction or externally validated skill transfer.

### C2 — ECRT method improves reputation calibration
- **Status:** CONDITIONAL CALIBRATION BENEFIT; team-accuracy superiority and targeted-attack robustness NOT SUPPORTED.
- **Supporting experiment:** Real Week 3 full/ablation grid. ECRT reduces Brier versus FixedBorrow by 0.0520 in same-subject directional false positives (CI [0.0408, 0.0617]), but in the prespecified related + 25% noise cell ECRT minus FixedBorrow team accuracy is +0.02 percentage points (CI [−0.04, +0.10]); Brier difference +0.0088 (CI [−0.0003, +0.0181], positive is worse).
- **Required before a strong method claim:** Independent pool/benchmark, improved attack model, gain versus FixedBorrow and single-best model on held-out decision metrics.

### C3 — HistRepEval evaluation protocol
- **Status:** WORKING REAL-DATA PROTOCOL; broader benchmark contribution still unvalidated.
- **Supporting experiment:** 14-subject MMLU-Pro split manifest, four verified Ollama model digests, 18,064 raw per-question answers, ledger SHA-256 in report, paired target design, capability/attack/ablation artefacts; 183/183 repository tests pass.
- **Required before a benchmark claim:** Second dataset/pool, release-ready documentation and independent rerun. Legacy `run_week2.py` simulation is excluded.

### C4 — Strategic stress-test analysis
- **Status:** EXPLORATORY A1/A2 CONTROLLED-INTERVENTION PILOT; robustness claim NOT SUPPORTED.
- **Supporting experiment:** Dev-selected A1/A2 scenarios with actual original model answers, forced-wrong test intervention and selective false-positive history feedback. In A2 at budget 100, attacker-poisoned ECRT loses 16.7 team-accuracy points versus FixedBorrow 11.1 points.
- **Required before an attack claim:** Multiple attackers/history samples, uncertainty intervals, actual malicious model-generated responses and unseen task pool.

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
