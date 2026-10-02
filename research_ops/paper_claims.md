# Paper Claims Tracker

**Post-pipeline audit, 2026-09-30:** The Week 4/5 capability and judge pipeline
is complete; this is an experiment-stage status, not completion of the original
Week 4–6 research gates. See
`docs/analysis/repguard_final_pipeline_assessment_2026-09-30.md` for the full
evidence table and decision. The original ECRT team-outcome claim remains
unsupported.

**Pool Gate 0, 2026-09-30:** The additional three-model pool study completed
1,260/1,260 real responses over the same 420 questions. Qwen3 8B thinking
remains the strongest single policy (280/420); an oracle over five answers
is 344/420 but not implementable; a five-fold subject router is 274/420.
There is insufficient independent specialist structure for DART in this pool.
See `docs/analysis/repguard_pool_gate_assessment_2026-09-30.md`. The newly
frozen 420-question holdout has not been used for model or method outcomes.

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
- **Supporting experiment:** 14-subject MMLU-Pro split manifest, four verified Ollama model digests, 18,064 raw per-question answers, ledger SHA-256 in report, paired target design, capability/attack/ablation artefacts; 204/204 repository tests passed on 2026-10-01.
- **Required before a benchmark claim:** Second dataset/pool, release-ready documentation and independent rerun. Legacy `run_week2.py` simulation is excluded.

### C4 — Strategic stress-test analysis
- **Status:** EXPLORATORY A1/A2 CONTROLLED-INTERVENTION PILOT; robustness claim NOT SUPPORTED.
- **Supporting experiment:** Dev-selected A1/A2 scenarios with actual original model answers, forced-wrong test intervention and selective false-positive history feedback. In A2 at budget 100, attacker-poisoned ECRT loses 16.7 team-accuracy points versus FixedBorrow 11.1 points.
- **Required before an attack claim:** Multiple attackers/history samples, uncertainty intervals, actual malicious model-generated responses and unseen task pool.

### C5 — Qwen3 8B thinking policy improves MMLU-Pro answer accuracy
- **Status:** SUPPORTED WITHIN THIS MODEL/BENCHMARK/PROTOCOL; not a novel CoT finding or a validation of ECRT.
- **Supporting experiment:** Disjoint 14-subject paired screen, 280/420 thinking vs 200/420 direct (+19.05 pp, CI [14.29, 23.81]), followed by frozen unused-dev validation, 203/280 vs 137/280 (+23.57 pp, CI [17.86, 29.29]). The later 560-ID development pool gives 372/560 thinking vs 277/560 direct (+16.96 pp, stratified-question bootstrap CI [+12.86, +21.07]); all 40 invalid thinking outputs hit the 8,192-token length cap. Same model digest and task-level pairing. The two policies use different output caps, so the comparisons establish a policy/budget effect, not the isolated effect of one `think` flag. See `results/real_dev_pool_v1/capability_analysis.json` and `analyze_real_dev_capability.py`.
- **Required before a broader claim:** Other model families and benchmarks, compute-matched baselines, and an untouched evaluation set for any newly selected routing policy.

### C6 — Candidate-blind judge improves feedback quality
- **Status:** EXPLORATORY ONLY; blind prompt was chosen after observing candidate-conditioned errors on the same 280 questions.
- **Supporting experiment:** Qwen3 14B blind verdict 549/694 correct versus candidate-conditioned 514/694; paired question-cluster difference +5.04 pp, CI [1.57, 8.56]. Blind choice accuracy was 151/280. Improvement came from 35 fewer false positives; false negatives were unchanged.
- **Required before a paper claim:** Freeze the prompt, evaluate fresh questions and another judge family, and show improved team decisions at matched cost.

### C7 — New model pool supports DART method superiority
- **Status:** NOT SUPPORTED; prespecified pool gate failed.
- **Supporting experiment:** Three additional real-model direct outputs on 420 paired MMLU-Pro questions (1,260 new calls). Qwen3 8B thinking 280/420, Qwen3 14B direct 226/420, Gemma2 195/420, Llama3 158/420. Oracle any-of-five 344/420, but cross-fitted subject routing 274/420. The observed engineering crossover (18/30 versus 13/30) is only one weak candidate specialty. On 560 fresh development IDs, a selector requiring Qwen14 on every question reached 396/560 versus 388/560 for the simple invalid-output fallback (+8 questions; CI for accuracy difference [0, +2.86] pp), below its prespecified +12-question gate. A pre-call router reached the same 388/560 as fallback while making 172 Qwen14 calls versus 40 fallback calls. These are development outcomes, not sealed-holdout confirmation.
- **Required before a method claim:** Distinct environment/pool with reproducible complementary expertise, learned decision gain over always-thinking, simple invalid-output fallback, routing, voting, and cost-matched published methods on independent holdout plus external benchmark. Audit/reputation ablations must add realized value.

### C8 — Agent-specific gold audit protects against targeted feedback poisoning
- **Status:** SUPPORTED ONLY FOR THE TESTED DEVELOPMENT INTERVENTION; incremental decision benefit over AuditOnly and strongest single solver NOT SUPPORTED.
- **Supporting experiment:** On 520 fresh development questions under targeted feedback poisoning of Qwen3 0.6B, old ECRT fell from 46.25% clean to 39.78% attacked, while AuditedECRT stayed at 45.67%. Under attack AuditedECRT exceeded FixedPlusAudit by 2.61 percentage points (target-cluster CI [+0.44, +4.91]), but exceeded AuditOnly by only 0.64 points (CI [−0.32, +1.73]); Qwen3 14B direct scored 53.08% on the same questions. See `docs/analysis/repguard_method_repair_pilot_2026-09-30.md`.
- **Required before a strong method claim:** Demonstrate added final-decision value from historical feedback beyond equal-budget gold audit and a strong single solver on a new pool and external task environment.

### C9 — Doubling context fixes Qwen3 8B thinking truncation
- **Status:** NOT SUPPORTED on the 70-question paired development diagnostic.
- **Supporting experiment:** `num_ctx` 4096→8192 with the same Qwen3 8B digest, prompt and 8192 output-token cap gave 42→46 correct answers, but validity stayed 64/70 and length-cap cases stayed 6/70 (two invalid cases exchanged in each direction). Four accuracy rescues and zero harms give a two-sided exact discordance p=0.125; the 14-subject bootstrap CI is fragile with only four discordant outcomes. Summed request time increased by 396.96 seconds (+9.05%). See `docs/analysis/repguard_followup_results_2026-10-01.md`.
- **Required before a broader claim:** Larger prospectively frozen sample and repeated runs to separate context effect from generation variability; the invalid-output fallback remains necessary.

### C10 — Interactive AppWorld base-agent feasibility
- **Status:** ONE TRAIN TASK SUCCESS IN DIRECT V4; THINKING V5 COMPLEMENTARITY NOT SUPPORTED; method and benchmark claims NOT SUPPORTED.
- **Supporting experiment:** Custom Qwen3 14B direct scaffold v2 scored 0/3 train task success. A v3 scaffold repair on one paired train task still failed. Qwen3 32B direct v4 on Modal L4 scored 1/3 official state-check successes on the same three train IDs (checks 2/7, 2/8, 8/8). Qwen3 32B thinking with larger output/context budget v5 scored 0/3 (checks 2/7, 1/8, 3/8), with two shared failures and one direct-only success. V5 used 75,250 generated tokens versus 7,184 for v4 direct. Every final cell was re-evaluated in a fresh Python process; AppWorld can otherwise leak cached model state across experiment evaluations in one process. V5 task 3 was replayed from initial state after two transport interruptions, documented separately. These are real model/tool trajectories but tiny train-visible custom-harness pilots, not official AppWorld benchmark scores or an isolated think-flag ablation. See `docs/analysis/repguard_followup_results_2026-10-01.md`.
- **Required before an interactive method study:** Repair agent API/postcondition loop on fresh train IDs; establish at least two capable policies with reproducible complementary successes, independent feedback histories and equal-budget baselines; then frozen dev and sealed holdout.

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
