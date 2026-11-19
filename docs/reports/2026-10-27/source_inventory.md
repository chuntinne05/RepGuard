# Danh mục mã nguồn đã rà soát - 27/10/2026

Full-file bytes/hash/UTF-8/AST inventory; targeted behavioral review of research-critical algorithms, collectors, evaluators and protocols. Not a line-by-line formal verification or security audit.

| Nhóm | File Python | Dòng |
|---|---:|---:|
| root_scripts | 97 | 13366 |
| docs | 22 | 1651 |
| infra | 44 | 4442 |
| src | 41 | 8280 |
| tests | 45 | 4101 |
| thesis_pilot | 42 | 3739 |

Mỗi file bên dưới đã được đọc để kiểm hash/cú pháp và lập bản đồ định nghĩa. Danh mục không đồng nghĩa mọi nhánh đã được kiểm thử. Chi tiết phân tích hành vi nằm trong báo cáo chính.

## [analyze_appworld_paired_pilots.py](../../../analyze_appworld_paired_pilots.py)

63 dòng; SHA256 `dfe387f752fe97a92760a14b94226190a067c637d46f380247b052bfb4d326b6`.

Compare two AppWorld train pilots on shared IDs after official state checks.

Định nghĩa: `load_pilot` (L11); `main` (L23).

## [analyze_appworld_scaffold_v6.py](../../../analyze_appworld_scaffold_v6.py)

53 dòng; SHA256 `aa90c9469bba4d0a8da9ea7aa012b1cabe8c32d5ad2597d0f4e099837e1b8c2d`.

Summarize paired, fresh-process state checks for the two v6 train policies.

Định nghĩa: `main` (L12).

## [analyze_audit_budget_replay.py](../../../analyze_audit_budget_replay.py)

194 dòng; SHA256 `d62d2319532e97cb7d9f037b03153bf45d497b31916a7ff0e89873fb32fae7f9`.

Exploratory same-audit-budget replay on the inspected Week 3 answer ledger.

Định nghĩa: `ScoreTable` (L40); `__init__` (L41); `score` (L44); `wilson_lower` (L48); `signal_lower` (L59); `beta_scores` (L73); `summarize` (L103); `main` (L144).

## [analyze_contextual_selector.py](../../../analyze_contextual_selector.py)

118 dòng; SHA256 `fc2f422bc5a2062877eea61b18f2d5dc4c2797ca767a1fc1af88b2b34ff0d0a9`.

Exploratory out-of-fold Qwen14-vs-thinking answer selector on real outputs.

Định nghĩa: `features` (L25); `fitted_predictor` (L39); `main` (L57).

## [analyze_dart_judge_errors.py](../../../analyze_dart_judge_errors.py)

70 dòng; SHA256 `8e1c7c49d11e6b86cee5ee41fa9ceb8aed12e0d4c5df4d028158ea795993dd1a`.

Post-run error evidence; never used by the collector or any learner.

Định nghĩa: `run` (L12).

## [analyze_dart_leaderboard.py](../../../analyze_dart_leaderboard.py)

144 dòng; SHA256 `55da463d269340ce69f8ea992a456bdc1bf5fdb6cd57120cc27cff1410df7677`.

Validate and analyze the preregistered AppWorld pool; never rerun agents.

Định nghĩa: `exact_mcnemar` (L18); `cluster_ci` (L23); `load_pool` (L32); `analyze` (L91); `main` (L123).

## [analyze_dart_modal_judge.py](../../../analyze_dart_modal_judge.py)

66 dòng; SHA256 `f51aee57f1b418e5bb6dab8ede0cf2dd779cfd701c3abf8aed546368b331a448`.

Separate post-collection quality gate; never imported by the collector.

Định nghĩa: `balanced_accuracy` (L13); `analyze` (L20).

## [analyze_dart_postrun.py](../../../analyze_dart_postrun.py)

218 dòng; SHA256 `cc113af5934eaad978157d44f153d89ce50be7251ed27f5b4125674c84ee0ada`.

Full-data, post-run diagnostics; never imported by collection or routing.

Định nghĩa: `confusion` (L21); `rates` (L26); `metrics` (L32); `paired_feedback` (L45); `routing_comparison` (L66); `selection_diagnostics` (L94); `analyze` (L151); `main` (L203).

## [analyze_failure_mechanisms.py](../../../analyze_failure_mechanisms.py)

116 dòng; SHA256 `f0a400ec87258e19fd2a792d3bee669fa08837a035bc288011851454f970ba12`.

Reproduce ECRT/DART failure diagnostics from validated real ledgers.

Định nghĩa: `grid_diagnostics` (L30); `reliability_diagnostics` (L67); `pool_disagreement` (L87); `main` (L106).

## [analyze_real_decision_guard_pilot.py](../../../analyze_real_decision_guard_pilot.py)

165 dòng; SHA256 `8d819a81362e58565df0bceb400e7ed890af2f31c8105a6d0c94d8e1f3e14205`.

Exploratory decision guard on real Week 3 answers and real judge feedback.

Định nghĩa: `vote_choice` (L28); `answers_for` (L58); `correct` (L65); `run` (L72).

## [analyze_real_decision_sensitivity.py](../../../analyze_real_decision_sensitivity.py)

80 dòng; SHA256 `eaeab6300686d1e6fccb39a427a544038409e45ff303b45b42157b43fd81b5e3`.

Count when improved reputation calibration actually changes real decisions.

Định nghĩa: `run` (L18).

## [analyze_real_dev_capability.py](../../../analyze_real_dev_capability.py)

73 dòng; SHA256 `f030ad94d7517e676e995ed5d77b3f8b95b563add6caad50d6bcd6d490dd153f`.

Paired capability and cost audit on the complete 560-question development pool.

Định nghĩa: `run` (L18).

## [analyze_real_dev_context_pilot.py](../../../analyze_real_dev_context_pilot.py)

103 dòng; SHA256 `176f05ce703db9f65c166d9e3f09b440e2a11c925fe96b8747c3b92258d0e904`.

Paired 4K-versus-8K context diagnostic on 70 frozen development IDs.

Định nghĩa: `cluster_ci` (L16); `run` (L28).

## [analyze_real_dev_pool.py](../../../analyze_real_dev_pool.py)

118 dòng; SHA256 `ecaafb6cb0465e22038a377670cb7f232420f3d7b97e81487d12d1a2ef6f1c93`.

Validate the frozen 560-question development ledger and score complete variants.

Định nghĩa: `load_validated` (L23); `analyze` (L90).

## [analyze_real_pool_gate.py](../../../analyze_real_pool_gate.py)

143 dòng; SHA256 `a1ff6fa031425262b92afaa20b521880a8f81d382ad3d7ccf4c9cf926ff1c286`.

Exploratory cross-fitted decision gate on the real 420-question model pool.

Định nghĩa: `load_answers` (L29); `fold` (L57); `choose_best` (L61); `paired_bootstrap` (L71); `run` (L82).

## [analyze_real_pool_overlap.py](../../../analyze_real_pool_overlap.py)

127 dòng; SHA256 `a221fbcd4c81c2dcc72e32196d4ea37b738ad16fc8bbea5cff33cd5776627257`.

Audit and score the real multi-model overlap ledger without test leakage.

Định nghĩa: `analyze` (L19).

## [analyze_real_routing_gate.py](../../../analyze_real_routing_gate.py)

161 dòng; SHA256 `2dca2669432a55eedd05c903c92b584f88c92bb74da0acbf6e85769aa11b9e4b`.

Exploratory routing gate using already collected real model responses.

Định nghĩa: `read_pairs` (L33); `features` (L46); `fit_ridge` (L69); `evaluate` (L75); `main` (L133).

## [analyze_real_week3.py](../../../analyze_real_week3.py)

564 dòng; SHA256 `e41d66c5bd7551887343679b11a6bc5fd1f62aef0b9b20358b8fd9648cd6bd49`.

Analyze real MMLU-Pro answer traces with a paired Q x T design.

Định nghĩa: `StudyTransferEstimator` (L48); `write_csv` (L68); `clean_json` (L78); `wilson` (L88); `load_inputs` (L98); `capability_audit` (L167); `make_episodes` (L276); `corrupt` (L292); `FixedBorrow` (L304); `__init__` (L307); `score` (L311); `build_methods` (L322); `choose_answer` (L337); `eval_cell` (L357); `grid` (L403); `mean` (L443); `cluster_bootstrap` (L447); `summarize_grid` (L461); `main` (L541).

## [analyze_real_week4_thinking.py](../../../analyze_real_week4_thinking.py)

164 dòng; SHA256 `cba228b251eca720b2436eb6f009d863a6320a862a4c41bc9cfce4b8e0375baf`.

Score completed paired Week 4 thinking calls offline, keeping labels out of the ledger.

Định nghĩa: `describe` (L20); `paired_bootstrap_ci` (L28); `analyze` (L44); `main` (L154).

## [analyze_real_week5_blind_judge.py](../../../analyze_real_week5_blind_judge.py)

163 dòng; SHA256 `5abe0bf73721481004dd18ebaad610f25b46f7766ced36c5c99e24196690d8aa`.

Compare candidate-blind Modal judgments with candidate-conditioned judgments.

Định nghĩa: `ratio` (L17); `paired_cluster_ci` (L21); `analyze` (L40); `main` (L153).

## [analyze_real_week5_feedback_impact.py](../../../analyze_real_week5_feedback_impact.py)

200 dòng; SHA256 `d2c520f0c093f1d0d80b2ba6b5180fac648592826b3058c63e042d8f334b9da8`.

Exploratory Week 5 impact of real Modal judge feedback on Week 3 routing.

Định nghĩa: `load_judgments` (L27); `episodes_for` (L49); `oracle_feedback` (L69); `write_cells` (L74); `summarize` (L81); `run` (L125); `main` (L186).

## [analyze_real_week5_modal_judge.py](../../../analyze_real_week5_modal_judge.py)

191 dòng; SHA256 `6cce5f60bf8d62e2583f4c1521e4b1aaccb93a7a9922be1d7ef108fdfcd3c572`.

Verify and score real Modal judge feedback without exposing gold online.

Định nghĩa: `ratio` (L17); `cluster_bootstrap_accuracy` (L21); `cluster_bootstrap_gain_over_reject` (L44); `analyze` (L68); `main` (L183).

## [analyze_targeted_attack_replay.py](../../../analyze_targeted_attack_replay.py)

174 dòng; SHA256 `63f4493be32f53ad890a63d04e8c3ad281fcf7b1ac0f6b67a7c84ad5f8d3826a`.

Exploratory targeted-feedback attack on real Week 3 model answers.

Định nghĩa: `targeted_corrupt` (L35); `summary` (L42); `paired_summary` (L66); `main` (L97).

## [attack_real_week3.py](../../../attack_real_week3.py)

128 dòng; SHA256 `ddcfade6781c4024e3f718fa55e676ca8ee387705a31788a58882f192b162880`.

A1/A2 attack pilots on real model-answer traces (with explicit interventions).

Định nghĩa: `accuracy` (L19); `choose_attack_scenarios` (L23); `feedback_poison` (L50); `eval_attack` (L60); `main` (L89).

## [docs/analysis/analyze_composition_mechanism.py](../../../docs/analysis/analyze_composition_mechanism.py)

79 dòng; SHA256 `9cc93072cd04d33e69d80bfd9b66df8ea9fc4601d131e89436862877a09e0bf3`.

Exploratory paired analysis after complete frozen collection. No inference.

Định nghĩa: `read` (L15); `main` (L17); `cell` (L71).

## [docs/analysis/analyze_modern_routing_headroom.py](../../../docs/analysis/analyze_modern_routing_headroom.py)

49 dòng; SHA256 `812b3ff205f9e25789f8f727a2b146e34eda80d74123ead8d906486181d7c06b`.

Exploratory replay on REAL paired model responses; never live-policy evidence.

Định nghĩa: `read` (L14); `main` (L16); `gpu_cost` (L22).

## [docs/analysis/build_cycle02_decision.py](../../../docs/analysis/build_cycle02_decision.py)

84 dòng; SHA256 `feff0c462e465e504c78232ad61e8c29cb9b43cfe32fffff5a2de8e5b3780919`.

Summarize completed verified experiments; never starts a model call.

Định nghĩa: `read` (L6); `main` (L8).

## [docs/analysis/build_research_cycle_01_report.py](../../../docs/analysis/build_research_cycle_01_report.py)

119 dòng; SHA256 `516e7cb2a44ee01e4037a2639c08080e61206cb66cfe32c675a09298156911b4`.

Build the report only after both real batches and independent verification.

Định nghĩa: `read` (L7); `main` (L9); `prose_spacing` (L107).

## [docs/analysis/diagnose_tatqa_count_contract.py](../../../docs/analysis/diagnose_tatqa_count_contract.py)

86 dòng; SHA256 `a2ffd43fde268bcc94662275bf64a6303b2ec76adcefa26fe390b765b22f108d`.

Post-hoc software diagnostic on REAL outputs; not another inference experiment.

Định nghĩa: `normalize` (L17); `expand` (L24); `terms` (L27); `Rewrite` (L34); `visit_BinOp` (L35); `run` (L50); `diag` (L55).

## [docs/analysis/diagnose_tatqa_plain_metadata.py](../../../docs/analysis/diagnose_tatqa_plain_metadata.py)

48 dòng; SHA256 `18c353c4dff4a772423d254abb7731f71b4c6dc63987aa678cf2982099d223b2`.

Common post-hoc normalization of inert unit metadata in actual terminal artifacts.

Định nghĩa: `normalize` (L11); `run` (L28).

## [docs/analysis/prepare_evalplus_source_inventory.py](../../../docs/analysis/prepare_evalplus_source_inventory.py)

61 dòng; SHA256 `54584b09734c5a4a089239716014d894b010650ca78a2b008120d9081aeb9422`.

Pin official EvalPlus sources and a metadata-selected coding pilot, zero inference.

Định nghĩa: `digest` (L14); `write` (L15); `main` (L19).

## [docs/analysis/prepare_tatqa_source_inventory.py](../../../docs/analysis/prepare_tatqa_source_inventory.py)

66 dòng; SHA256 `cee6f58d63ed8fed3aac86dc79f93bd5f7c1db03e2336c901dc0af3f6fcb71e0`.

Source/metric inventory, not a new inference experiment or result.

Định nghĩa: `read` (L14); `digest` (L15); `norm` (L16); `main` (L18).

## [docs/analysis/repguard_paired_history_probe.py](../../../docs/analysis/repguard_paired_history_probe.py)

125 dòng; SHA256 `4eaf96cfee5774edc43af853cbc1454521b6714e20dafc866a13c675c590f31e`.

Exploratory OOF action-history test on REAL counterfactual outputs.

Định nghĩa: `read` (L22); `register` (L24); `harm_upper` (L43); `main` (L52); `cost` (L60); `score` (L69).

## [docs/analysis/repguard_pot_format_control.py](../../../docs/analysis/repguard_pot_format_control.py)

82 dòng; SHA256 `b43556c12e1c8b479b152e9d776c54061627780bc18691a32955082f98617ad5`.

Uniform formatting-only secondary control on saved REAL PoT programs.

Định nghĩa: `read` (L18); `canonical` (L20); `main` (L33).

## [docs/analysis/repguard_pot_readout_control.py](../../../docs/analysis/repguard_pot_readout_control.py)

79 dòng; SHA256 `24c67b7d71e2e1cce6b51a55bac0839d0f4218403c1345f37830204dba6c8ad3`.

Secondary single-agent control: accept an explicit final variable expression.

Định nghĩa: `read` (L20); `canonical` (L22); `main` (L40).

## [docs/analysis/repguard_unit_failure_diagnostic.py](../../../docs/analysis/repguard_unit_failure_diagnostic.py)

68 dòng; SHA256 `381dcd983ffe35d6c2260295d2adbe48e33d91550542d621e787bb163c1ab474`.

Post-hoc public-output surgery, NOT a model call or confirmed repair method.

Định nghĩa: `surgery` (L17); `main` (L29).

## [docs/analysis/replay_tatqa_component_fallback.py](../../../docs/analysis/replay_tatqa_component_fallback.py)

28 dòng; SHA256 `f19dd860bde97e55feb801e5b9d71008c3979747acb0229d336abef33c4f008d`.

Post-hoc receiver adequacy replay over REAL patches, no new model outputs.

Định nghĩa: `run` (L9).

## [docs/analysis/reserve_research_report_splits.py](../../../docs/analysis/reserve_research_report_splits.py)

61 dòng; SHA256 `e2699399cf5d5056cf40c1dd155f22b1eb9f1f3e458992e5d577a33660a29b8f`.

Reserve future report-disjoint development/calibration/confirmation IDs.

Định nghĩa: `read` (L13); `sha` (L14); `norm` (L15); `main` (L17).

## [docs/analysis/verify_backbone_probe.py](../../../docs/analysis/verify_backbone_probe.py)

64 dòng; SHA256 `6fa982cb178f60af1c3ed0f5b035c8114f8334d64359f745e7c7c57222abda4d`.

Verify32 real responses and recompute paired backbone outcomes, no inference.

Định nghĩa: `read` (L14); `sha` (L15); `main` (L17).

## [docs/analysis/verify_composition_cycle02.py](../../../docs/analysis/verify_composition_cycle02.py)

95 dòng; SHA256 `44743c43e6710709655ecd4b7af0b759ce26f8dcb48e7e03607d0a109318a5ed`.

Independently recalculate frozen cycle2 from real receipts; no inference.

Định nghĩa: `read` (L15); `sha` (L16); `main` (L18); `cost` (L35).

## [docs/analysis/verify_modern_direct_control.py](../../../docs/analysis/verify_modern_direct_control.py)

56 dòng; SHA256 `4c76ae41fb90a11f8beafced1e52812d947bf68130ee0f93589fd4e5dccd3c53`.

Verify whole-cohort non-native-thinking control; no model calls.

Định nghĩa: `read` (L13); `sha` (L14); `main` (L16).

## [docs/analysis/verify_modern_probe.py](../../../docs/analysis/verify_modern_probe.py)

58 dòng; SHA256 `035a0daaf1f4835d3e7ccee9ed90740ec1f32370d999086e22b83e51badf5645`.

Verify the contemporary baseline from16 real receipts, without inference.

Định nghĩa: `read` (L14); `sha` (L15); `main` (L17).

## [docs/analysis/verify_research_cycle_01.py](../../../docs/analysis/verify_research_cycle_01.py)

178 dòng; SHA256 `f9b8bb25ef0fccda01046cead921bde8640821894e759cd4da29f670e8ee1851`.

Independent local verification of saved real responses. No network/inference.

Định nghĩa: `read` (L20); `main` (L22); `eval_seconds` (L100).

## [docs/analysis/verify_tatqa_crossfamily_cycle03.py](../../../docs/analysis/verify_tatqa_crossfamily_cycle03.py)

58 dòng; SHA256 `0f81e13f79c0697ad6868e554328abe243f7d95333924e5923c107f44fb2337c`.

Audit120 new real responses plus24 reused lineage; no API inference.

Định nghĩa: `read` (L13); `sha` (L14); `audit` (L16).

## [docs/analysis/verify_tatqa_cycle03_final.py](../../../docs/analysis/verify_tatqa_cycle03_final.py)

31 dòng; SHA256 `34dd4fb03ec9e2a75019334a56c5bdec81e8de82ab8b9bcb9dfbc3a022fb8f8c`.

Recompute registered scores from evaluator raw records, not summary metrics.

Định nghĩa: `main` (L12).

## [docs/analysis/verify_tatqa_scope_cycle03.py](../../../docs/analysis/verify_tatqa_scope_cycle03.py)

76 dòng; SHA256 `2fac239356686c66026096ba05efd3317d51f73c33175146e4232c0285bddaa0`.

Independent receipt, provenance, privacy and local-execution audit (no API calls).

Định nghĩa: `load` (L14); `sha` (L15); `audit` (L17).

## [evaluate_appworld_legacy_react_v7.py](../../../evaluate_appworld_legacy_react_v7.py)

64 dòng; SHA256 `3427a227711dff96fa9901caac32e07cae800c4cb4fa14fd166199031e520687`.

Score completed v7 AppWorld rollouts in isolated evaluator processes.

Định nghĩa: `evaluate` (L15); `main` (L31).

## [evaluate_appworld_train_pilot.py](../../../evaluate_appworld_train_pilot.py)

83 dòng; SHA256 `9e52fa0096bf3dc08b13b31508bea77bcd4d73ea325c18f48ed44ec12158e7cd`.

Offline AppWorld state-check scoring for the gold-blind train pilot.

Định nghĩa: `evaluate_isolated` (L18); `main` (L37).

## [evaluate_appworld_v10_simplified.py](../../../evaluate_appworld_v10_simplified.py)

61 dòng; SHA256 `39fa80f2f35d07d0073e135f4c38fc58ddac9815f1c1d2bd3237dbdd190ade4e`.

Score completed AppWorld 0.2 v10 trajectories in isolated official evaluators.

Định nghĩa: `evaluate` (L14); `main` (L34).

## [evaluate_fresh_dev_audit.py](../../../evaluate_fresh_dev_audit.py)

183 dòng; SHA256 `405d5b55239b831ffa13e18cb793ba515af22a41d3a3206b6a753d1f1a915906`.

Locked fresh-development replay of targeted feedback attack and audited trust.

Định nghĩa: `choose` (L41); `summarize` (L58); `run` (L96).

## [evaluate_fresh_dev_router.py](../../../evaluate_fresh_dev_router.py)

146 dòng; SHA256 `813ed613afd598cd4210b89055f0d43c6dc462f35c295f52a8dd14c86972a3a1`.

Gold-blind at decision time, selective Qwen14 fallback on fresh dev IDs.

Định nghĩa: `decisions` (L28); `old_crossfit` (L34); `run` (L78).

## [evaluate_fresh_dev_selector.py](../../../evaluate_fresh_dev_selector.py)

101 dòng; SHA256 `96bbc143a8d35880cced4409f0b1a8e6b1b3b66fbf6cb32f9039e15e17f5a59e`.

Frozen Qwen14-vs-thinking selector evaluation on 560 fresh development IDs.

Định nghĩa: `stratified_ci` (L24); `run` (L36).

## [fetch_dart_paired_volume.py](../../../fetch_dart_paired_volume.py)

53 dòng; SHA256 `a62562a05a5f9ad5d177ab602fd7126bbf68f63cf51793ea5dd55de58f05e734`.

Fetch a terminal paired run incrementally using the official Volume read API.

Định nghĩa: `main` (L15); `read` (L21).

## [fetch_routerbench_finqa_feedback.py](../../../fetch_routerbench_finqa_feedback.py)

51 dòng; SHA256 `da28fb772a4ee5da7b21f0453dccc139bf4f29c4cf49e78e90ff15bb1a1231f6`.

Incremental checksummed download of active FinQA pilot artifacts.

Định nghĩa: `main` (L10); `read` (L15); `fetch_case` (L33).

## [fetch_routerbench_pilot.py](../../../fetch_routerbench_pilot.py)

47 dòng; SHA256 `931fb586fb3e7d8daf908d83d26265eb84a829c07879cc25fbc0c5f6d853ce42`.

Incremental pilot download; safe for live progress, final report requires terminal state.

Định nghĩa: `main` (L10); `read` (L15); `fetch_case` (L31).

## [freeze_dart_leaderboard_pool.py](../../../freeze_dart_leaderboard_pool.py)

93 dòng; SHA256 `b0832bcb6def918b599ddc9f3b0cfe8962f26fa2f130b28c168ad4373108daf6`.

Freeze the historical AppWorld baseline pool without inspecting outcomes.

Định nghĩa: `git` (L34); `main` (L38).

## [freeze_real_next_study.py](../../../freeze_real_next_study.py)

142 dòng; SHA256 `37e24bb05d85d4e806cfde7d8fb74a76af2791209df0f0aa085d59cd657840bf`.

Freeze disjoint, label-free MMLU-Pro IDs for the post-Week-5 study.

Định nghĩa: `canonical_hash` (L30); `ids_in` (L35); `prior_ids` (L45); `freeze` (L66); `main` (L122).

## [infra/modal/gain_core.py](../../../infra/modal/gain_core.py)

188 dòng; SHA256 `f62f985ff49cc0b9cc918398275e97c1c435cb06870d7b7d86ca8767deac8459`.

Bounded routing baselines; learners see only revealed training outcomes.

Định nghĩa: `terms` (L12); `text_features` (L17); `transform` (L22); `center_features` (L32); `factor_design` (L37); `factor_scores` (L50); `ridge_predict` (L61); `corrected_utility` (L74); `direct_utility` (L84); `fit` (L112); `feature_bank` (L129); `build` (L132); `route_case` (L146); `synthetic_smoke` (L177).

## [infra/modal/gain_modal.py](../../../infra/modal/gain_modal.py)

36 dòng; SHA256 `a31b3a7e2e4e1a6375de6c7c90b9e69da47e5d20aaa1df69f930b7b8346566d3`.

Long-running deployed routing experiment, independent of local Codex session.

Định nghĩa: `worker` (L18); `inspect_run` (L24).

## [infra/modal/gain_pipeline.py](../../../infra/modal/gain_pipeline.py)

123 dòng; SHA256 `d009f212e363483904f371594e3a62c275e1c1f64f92b9bb4043e49caa3c43df`.

Detached, finite R0/R1 run; primary endpoint frozen in the linked protocol.

Định nghĩa: `verify` (L14); `analysis` (L23); `validate_case` (L58); `run` (L66); `status` (L77); `case` (L88).

## [infra/modal/halving_core.py](../../../infra/modal/halving_core.py)

55 dòng; SHA256 `499b3a1d43aa3aad78728a48e23b0616a8c32721c13ef69914e584b67977b9d1`.

Finite-archive, exact-budget Sequential Halving; gold access by callback only.

Định nghĩa: `select` (L8).

## [infra/modal/halving_modal.py](../../../infra/modal/halving_modal.py)

33 dòng; SHA256 `1c554ad82be1aca8604eca81369952d524d1ddc4f9445e816efb957e65b62176`.

Định nghĩa: `worker` (L15); `inspect_run` (L21).

## [infra/modal/halving_pipeline.py](../../../infra/modal/halving_pipeline.py)

109 dòng; SHA256 `e160cd36b6aee51964d94ec3b13ee6e124532b91b677c3586a38d6151dadfa90`.

Bounded detached baseline audit. Frozen candidate predictions are comparators only.

Định nghĩa: `verify` (L13); `validate` (L21); `summarize` (L26); `run` (L53); `status` (L69).

## [infra/modal/history_core.py](../../../infra/modal/history_core.py)

71 dòng; SHA256 `ff827d4107da8c1d10252f8059bfef9495d082af0e784579b314bff4d5297ee5`.

Cross-fitted historical feedback calibration and regularized rectification.

Định nghĩa: `design` (L9); `cross_proxy` (L23); `rectify` (L43); `choose` (L52); `routes` (L56).

## [infra/modal/history_modal.py](../../../infra/modal/history_modal.py)

33 dòng; SHA256 `865725811f6773ceea4bee6d50772593cfd4f7271dcfbf5e44d656f7a7dfcbe0`.

Định nghĩa: `worker` (L15); `inspect_run` (L21).

## [infra/modal/history_pipeline.py](../../../infra/modal/history_pipeline.py)

99 dòng; SHA256 `f8a6b7f5ad900aac1d0444e6e98ee4d4bc5640244e3702115dd053e912caea76`.

Định nghĩa: `verify` (L11); `validate` (L19); `summarize` (L24); `run` (L53); `status` (L65).

## [infra/modal/neural_core.py](../../../infra/modal/neural_core.py)

125 dòng; SHA256 `d0ea9758527012856403d5ef32d25645f9b6c35c43785edc9e18070d692690b1`.

Gold-isolated frozen-feature routing; no network or outcome-store access.

Định nghĩa: `observed_gold` (L10); `means` (L16); `inner_folds` (L20); `features` (L28); `transform` (L35); `fit_predict` (L40); `ht_score` (L78); `route_case` (L86); `cluster_ci` (L120).

## [infra/modal/neural_modal.py](../../../infra/modal/neural_modal.py)

39 dòng; SHA256 `9d7f0ab5e69b0f150ff1b99bff6269d4845f75cab0133019fe2499c0f2710ef7`.

Deployed asynchronous CPU experiment; no local runner lifetime dependency.

Định nghĩa: `worker` (L20); `inspect_run` (L26).

## [infra/modal/neural_pipeline.py](../../../infra/modal/neural_pipeline.py)

172 dòng; SHA256 `710dc6dc1e705dad323be403f2ed8f571be65de764fc21d037450ec0433aeea0`.

Resumable cloud pipeline. All artifacts live on a committed Modal Volume.

Định nghĩa: `digest` (L14); `atomic` (L18); `ensure_identity` (L24); `verify_packet` (L32); `embeddings` (L42); `summarize` (L71); `run` (L100); `status` (L107); `case` (L130); `progress` (L142).

## [infra/modal/neural_smoke.py](../../../infra/modal/neural_smoke.py)

20 dòng; SHA256 `ae8355e6abcb426ccb26b816ad379c3241e1e2d6a80217f4979936a83a77c6af`.

Tiny synthetic unit controls, never scientific experiment observations.

Định nghĩa: `smoke` (L6).

## [infra/modal/ollama_modal_l4.py](../../../infra/modal/ollama_modal_l4.py)

183 dòng; SHA256 `96b1238480c3846c96ec669723c0849a9f8e5a8055bb1b24c048d98a18ba5795`.

Định nghĩa: `wait_for_ollama` (L62); `pull_model` (L97); `OllamaServer` (L166); `start` (L169); `stop` (L179).

## [infra/modal/ollama_modal_recovery.py](../../../infra/modal/ollama_modal_recovery.py)

179 dòng; SHA256 `51d58962f96546ca155689edf7ce7957889d4973b1fd0d7040d09fb58384947d`.

Định nghĩa: `wait_for_ollama` (L60); `pull_model` (L95); `OllamaServer` (L162); `start` (L165); `stop` (L175).

## [infra/modal/paired_history_core.py](../../../infra/modal/paired_history_core.py)

11 dòng; SHA256 `77c907c08b04b755c5a63ff51f8121158672eced11d85669788873125303c948`.

Rename only the sampling-design control; estimation is unchanged.

Định nghĩa: `routes` (L7).

## [infra/modal/paired_history_modal.py](../../../infra/modal/paired_history_modal.py)

33 dòng; SHA256 `506abb930a21f45423c442a5318404f88c55e0c86345d11eae2e2cb76e4e03d1`.

Định nghĩa: `worker` (L15); `inspect_run` (L21).

## [infra/modal/paired_history_pipeline.py](../../../infra/modal/paired_history_pipeline.py)

101 dòng; SHA256 `6449e76234c9dc5afba0bd9f7e20bb1e4e5bc0b3e1dbb1b04712ea368ea848f0`.

Paired acquisition version; estimator math is imported unchanged.

Định nghĩa: `verify` (L12); `validate` (L20); `summarize` (L25); `run` (L55); `status` (L67).

## [infra/modal/routerbench_finqa_consensus_core.py](../../../infra/modal/routerbench_finqa_consensus_core.py)

74 dòng; SHA256 `d7a126990dd8513c28be6f5143436ad7153697e8b6adbd9390926addd38aff06`.

Frozen exact-answer agreement proxy for FinQA historical executions.

Định nghĩa: `select_queries` (L9); `canonical` (L19); `agreement_proxy` (L23); `pair_ratio` (L37); `analyze` (L45).

## [infra/modal/routerbench_finqa_consensus_modal.py](../../../infra/modal/routerbench_finqa_consensus_modal.py)

45 dòng; SHA256 `7f212626e369917b2976ff59f5a2a4e2272c3af3808f34462d6f1f6feb4407a5`.

Detached Modal CPU run for frozen FinQA exact-answer consensus replay.

Định nghĩa: `worker` (L21); `inspect_run` (L29).

## [infra/modal/routerbench_finqa_consensus_pipeline.py](../../../infra/modal/routerbench_finqa_consensus_pipeline.py)

200 dòng; SHA256 `8b6c208f2e38d7869336eb8f30e667121a476ba4ca57ceb1ffda81cc84f4d847`.

Detached gold-blind consensus extraction followed by selected-score analysis.

Định nghĩa: `digest` (L15); `atomic` (L19); `save` (L26); `validate` (L33); `file_sha` (L38); `verify` (L46); `status` (L68); `selected_predictions` (L77); `selected_gold` (L111); `run` (L147).

## [infra/modal/routerbench_finqa_feedback_core.py](../../../infra/modal/routerbench_finqa_feedback_core.py)

146 dòng; SHA256 `e84bbd096c4a011690ba400697738c4706df9d4802c0a605695f61299a4dd830`.

Gold-blind FinQA judge input and fixed 20-model feedback diagnostic.

Định nghĩa: `query_hash` (L20); `select_queries` (L24); `visible_records` (L30); `final_answer` (L45); `prompt_for` (L67); `probability` (L82); `crossfit` (L92); `analyze` (L112); `ratio` (L124).

## [infra/modal/routerbench_finqa_feedback_modal.py](../../../infra/modal/routerbench_finqa_feedback_modal.py)

112 dòng; SHA256 `3dd0720a2e6acd82911f1a493df95ebd08cdf8423682b1ecd04d3bb7dbb731ef`.

Detached CPU orchestrator and isolated real Qwen3-14B GPU judge.

Định nghĩa: `judge` (L25); `request` (L59); `worker` (L76); `inspect_run` (L96).

## [infra/modal/routerbench_finqa_feedback_pipeline.py](../../../infra/modal/routerbench_finqa_feedback_pipeline.py)

248 dòng; SHA256 `3761291eef058c635fc0066bd3c5cd247f4e5c5956e91fe8aa123c63de10f957`.

Detached, resumable gold-blind FinQA judge collection and evaluator-only analysis.

Định nghĩa: `digest` (L15); `atomic` (L19); `save` (L26); `validate` (L33); `file_sha` (L38); `verify` (L46); `status` (L67); `prepare_inputs` (L76); `collect` (L124); `selected_gold` (L187); `finish` (L212).

## [infra/modal/routerbench_finqa_field_audit_modal.py](../../../infra/modal/routerbench_finqa_field_audit_modal.py)

134 dòng; SHA256 `247aa0fbc23cc4d34183d6b187af3359a60dd52121bc9c33043234959d16459b`.

Gold-blind audit of selected FinQA solver-output fields after pilot failure.

Định nghĩa: `inspect` (L14); `collect_predictions` (L69); `main` (L108).

## [infra/modal/routerbench_finqa_preflight_modal.py](../../../infra/modal/routerbench_finqa_preflight_modal.py)

92 dòng; SHA256 `cb042a65976b294b9ffbdbbb380ac18f448014dec8df2a187d86e6fba5fc4b4a`.

Gold-blind schema preflight for the selected FinQA development questions.

Định nghĩa: `inspect` (L11); `inspect_many` (L47).

## [infra/modal/routerbench_headroom_core.py](../../../infra/modal/routerbench_headroom_core.py)

33 dòng; SHA256 `3909ccf7707c0b037fac5d4eaf06d97ffa95a80361864d8ad42c2eeb7d082857`.

Outcome-blind query selection and descriptive headroom statistics.

Định nghĩa: `select_queries` (L9); `analyze` (L15).

## [infra/modal/routerbench_headroom_modal.py](../../../infra/modal/routerbench_headroom_modal.py)

43 dòng; SHA256 `4420bc79b4d56768dba73fb1582946c7517ae0eeb676edeede27f4ecd54cd70d`.

Detached CPU worker for two fixed gold-only development diagnostics.

Định nghĩa: `worker` (L19); `inspect_run` (L27).

## [infra/modal/routerbench_headroom_pipeline.py](../../../infra/modal/routerbench_headroom_pipeline.py)

157 dòng; SHA256 `3a5b7877beb3bad64330c08bb3e0624bcef37d867a4d7479fedf677184aa8d30`.

Read only frozen positions of archived objective scores from a pinned tar.

Định nghĩa: `digest` (L12); `atomic` (L16); `save` (L23); `validate` (L30); `file_sha` (L35); `verify` (L43); `selected_scores` (L67); `run` (L88); `status` (L95).

## [infra/modal/routerbench_intake_core.py](../../../infra/modal/routerbench_intake_core.py)

85 dòng; SHA256 `e4c890b55a2317cf1ebae1328493f5f253a9406cad4e5de7a1d68c3a83d389c4`.

Outcome-blind metadata intake for a pinned public archive. Never extract paths.

Định nghĩa: `digest` (L8); `normalized_query` (L12); `classify` (L16); `metadata_from_events` (L32); `inspect_json` (L62); `summarize` (L67).

## [infra/modal/routerbench_intake_modal.py](../../../infra/modal/routerbench_intake_modal.py)

33 dòng; SHA256 `d8b3789676dc3598a2cbe56e182d2129a19277a9ee6c4fc979dbe37acbe37fdd`.

Định nghĩa: `worker` (L15); `inspect_run` (L21).

## [infra/modal/routerbench_intake_pipeline.py](../../../infra/modal/routerbench_intake_pipeline.py)

119 dòng; SHA256 `e75bf86b803be0e43fb387194676f547a5e67af248b92b4a4a9a75a9325de9de`.

Detached hash-verified archive download and resumable outcome-blind inventory.

Định nghĩa: `atomic` (L11); `file_sha` (L15); `verify` (L23); `run` (L31); `status` (L52).

## [infra/modal/routerbench_intake_v2_core.py](../../../infra/modal/routerbench_intake_v2_core.py)

19 dòng; SHA256 `b9db0af179651eaa22b65f1e2bf72333900bacc23fc1795e3e3734a52eb00ac6`.

Layout amendment based exclusively on verified archive member names.

Định nghĩa: `classify` (L6).

## [infra/modal/routerbench_intake_v2_modal.py](../../../infra/modal/routerbench_intake_v2_modal.py)

33 dòng; SHA256 `a3095de41231dbf475d8f3363310fc1938212d63af96b8e2a8e4873c67739789`.

Định nghĩa: `worker` (L15); `inspect_run` (L21).

## [infra/modal/routerbench_intake_v2_pipeline.py](../../../infra/modal/routerbench_intake_v2_pipeline.py)

121 dòng; SHA256 `8af2f3303db7a2fbacd1a7621d605725e08e1b8782284bc886b7834ec2151ff4`.

Detached hash-verified archive download and resumable outcome-blind inventory.

Định nghĩa: `atomic` (L11); `file_sha` (L15); `verify` (L23); `run` (L31); `status` (L52).

## [infra/modal/routerbench_pilot_core.py](../../../infra/modal/routerbench_pilot_core.py)

131 dòng; SHA256 `2d6629a3e279e8cbfba3db2635a64fa1fb8384ff9fd1d5f2e5faf33889492814`.

Gold-blind inputs and fixed model-only cross-fit diagnostic for the first pilot.

Định nghĩa: `query_hash` (L21); `dev_query` (L25); `select_queries` (L29); `visible_records` (L36); `prompt_for` (L55); `probability` (L66); `crossfit` (L76); `analyze` (L98); `differences` (L107); `ratio` (L110).

## [infra/modal/routerbench_pilot_modal.py](../../../infra/modal/routerbench_pilot_modal.py)

104 dòng; SHA256 `b8d625b3e827300f0958e99b665d6d7f8ea621bf35b296754c7c3ba5a72e7d91`.

Deployed CPU orchestrator plus isolated GPU collector, independent of Codex.

Định nghĩa: `judge` (L26); `request` (L57); `worker` (L73); `inspect_run` (L92).

## [infra/modal/routerbench_pilot_pipeline.py](../../../infra/modal/routerbench_pilot_pipeline.py)

184 dòng; SHA256 `7315e799df9c87ce6103206d379f709195a7e6db54c0c685df8aa53c4f579869`.

Separate archive access, gold-blind GPU collection and post-collection evaluation.

Định nghĩa: `verify` (L13); `validate` (L21); `save` (L26); `update` (L32); `prepare_inputs` (L39); `collect` (L81); `selected_gold` (L130); `finish` (L154).

## [infra/modal/routerbench_prompt_groups_core.py](../../../infra/modal/routerbench_prompt_groups_core.py)

89 dòng; SHA256 `c9d256fad3667a27e923423079a029259e4c3e261832a0768daf81942e5505d3`.

Prompt-only MATH500 near-template groups; no outcome fields accepted.

Định nghĩa: `canonical` (L7); `query_hash` (L11); `prompt_records` (L15); `grams` (L29); `word_grams` (L33); `jaccard` (L37); `group` (L41); `find` (L51); `union` (L56).

## [infra/modal/routerbench_prompt_groups_modal.py](../../../infra/modal/routerbench_prompt_groups_modal.py)

41 dòng; SHA256 `e71606c0c071a265bf6a565fc72fdcd87adb659437347de36d964a034bd406ee`.

Detached CPU worker for prompt-only grouping of pinned MATH500 archive.

Định nghĩa: `worker` (L17); `inspect_run` (L25).

## [infra/modal/routerbench_prompt_groups_pipeline.py](../../../infra/modal/routerbench_prompt_groups_pipeline.py)

111 dòng; SHA256 `d84f8bb105ac922998d5220fed91ae6b7a791834dbf2f9a536f0092ee7603cf2`.

Verify the pinned tar and extract only prompts from one preselected member.

Định nghĩa: `digest` (L11); `atomic` (L15); `save` (L22); `validate` (L29); `file_sha` (L34); `verify` (L42); `run` (L57); `status` (L65).

## [infra/modal/routerbench_sparse_core.py](../../../infra/modal/routerbench_sparse_core.py)

219 dòng; SHA256 `c8f1aabf672fa11f26c4113112a195499e982a76467f2e3d3c29499dbccd15d7`.

Fixed sparse-gold model selection. Learners receive audit callbacks, never full gold.

Định nghĩa: `Audit` (L17); `__init__` (L19); `query` (L29); `choose` (L42); `audit_order` (L50); `observed_from_query` (L58); `means` (L69); `design` (L73); `predict` (L87); `cross_proxy` (L104); `rectify` (L121); `halving` (L130); `select_case` (L180); `observed_from_log` (L211).

## [infra/modal/routerbench_sparse_modal.py](../../../infra/modal/routerbench_sparse_modal.py)

39 dòng; SHA256 `5edda24e20607c03eee1c32aa1141b1135cf5eaa707109aedf29852bbcdac02e`.

Detached CPU-only replay; no solver or judge service is started.

Định nghĩa: `worker` (L17); `inspect_run` (L23).

## [infra/modal/routerbench_sparse_pipeline.py](../../../infra/modal/routerbench_sparse_pipeline.py)

220 dòng; SHA256 `0be770098b609d80f368d3c37007aec991f1f3e78fabd11fa91033c39e94c32c`.

Checkpointed finite development replay, with evaluator-owned gold access.

Định nghĩa: `digest` (L11); `atomic` (L15); `save` (L22); `validate` (L29); `verify` (L34); `case` (L59); `factory` (L68); `summarize` (L92); `run` (L177); `status` (L187).

## [report_dart_followup.py](../../../report_dart_followup.py)

90 dòng; SHA256 `d6632d16002e8c4043c903cd75888f94095956f5464ea027ad92d1a8f51d0ba3`.

Aggregate-only synthesis of the completed feedback and paired-design studies.

Định nghĩa: `read` (L10); `main` (L14).

## [report_dart_gain.py](../../../report_dart_gain.py)

118 dòng; SHA256 `67e4c7a77f7a15ff2d53d5d551003cef6984f3a6b8315389c5c3e12bc10f5bbd`.

Verify downloaded checkpoints and write the complete aggregate result report.

Định nghĩa: `main` (L14).

## [report_dart_halving.py](../../../report_dart_halving.py)

130 dòng; SHA256 `4de009ec87e1dde8a4e1cb1d47ac7f996ccc609f40763d9c5c1a50995df91837`.

Verify cloud queries/decisions and recompute every result locally.

Định nghĩa: `main` (L13).

## [report_dart_history.py](../../../report_dart_history.py)

112 dòng; SHA256 `0d05ad88d4b4639ec8e7907a0f81478881808fffc31d6dfc47da8152b8116879`.

Recompute and verify every completed historical-feedback case before reporting.

Định nghĩa: `main` (L14).

## [report_dart_judge_pipeline.py](../../../report_dart_judge_pipeline.py)

77 dòng; SHA256 `9b69842e30d9b3df86bd83c33972823959a9e4537ca94b5cfedb5d636ec7f27b`.

Export aggregate-only research results after the fixed automated stages.

Định nghĩa: `report` (L15).

## [report_dart_paired_history.py](../../../report_dart_paired_history.py)

112 dòng; SHA256 `85495b19b39d0aaed032aa1ff41248a7a80c8acd9f0d26829d5bb407c481f497`.

Recompute and verify every completed historical-feedback case before reporting.

Định nghĩa: `main` (L14).

## [report_dart_same_audit.py](../../../report_dart_same_audit.py)

75 dòng; SHA256 `d57da37c2fe38489b0b696ffa68b002e4c2eb8a9d3c849746a181acbff6be21c`.

Publish aggregate tables only; private task outcomes remain in results/.

Định nghĩa: `main` (L9).

## [report_routerbench_finqa_consensus.py](../../../report_routerbench_finqa_consensus.py)

109 dòng; SHA256 `abd76e14430a8b11491d789bddd310ea36179f32ed9fdf45406f194d46a1d0b2`.

Verify frozen FinQA consensus replay and regenerate its public report.

Định nghĩa: `sha` (L13); `main` (L17).

## [report_routerbench_finqa_consensus_failure.py](../../../report_routerbench_finqa_consensus_failure.py)

80 dòng; SHA256 `94f3f48b312cf6f1889042c1b3ff692421cf5665972f0b86ee214effb1fe1f5d`.

Reproduce post-hoc, aggregate diagnostics after the frozen consensus gate failed.

Định nghĩa: `correlation` (L12); `decomposition` (L16); `main` (L30).

## [report_routerbench_finqa_failure.py](../../../report_routerbench_finqa_failure.py)

159 dòng; SHA256 `dc0039f988b598c8d0b47484e96e0a16b7a354e8e0fc56a60146f0c92740572a`.

Post-hoc, development-only diagnosis of the completed FinQA judge pilot.

Định nghĩa: `pair_decomposition` (L19); `subset_crossfit` (L33); `corr` (L51); `main` (L55).

## [report_routerbench_finqa_feedback.py](../../../report_routerbench_finqa_feedback.py)

140 dòng; SHA256 `0d05d1d58b895c9c03ca99e8710bae3e0872ffb628dc7f9836299af582f49bca`.

Verify all real FinQA judge responses and recompute fixed diagnostic locally.

Định nghĩa: `near_equal` (L10); `main` (L28).

## [report_routerbench_headroom.py](../../../report_routerbench_headroom.py)

84 dòng; SHA256 `14c9bae85eab1c2f2b183f914440ab266fb55296b1919b0dff98d1e93103e156`.

Verify 40 score-only checkpoints and independently recompute headroom.

Định nghĩa: `main` (L11).

## [report_routerbench_pilot.py](../../../report_routerbench_pilot.py)

148 dòng; SHA256 `de538fa49ebbfba855978b927f3ca1c1aad81d9d6c9a5f6880c7a9e11d322772`.

Independently validate cloud inference records and recompute pilot diagnostics.

Định nghĩa: `near_equal` (L11); `load_verified_pilot` (L26); `main` (L82).

## [report_routerbench_prompt_groups.py](../../../report_routerbench_prompt_groups.py)

74 dòng; SHA256 `d35f9939aa4c1f9bdf8448ce31c4d0001e412d8fb77f879476213d456084bc82`.

Independently recompute prompt-only grouping from verified cloud artifacts.

Định nghĩa: `main` (L10).

## [report_routerbench_sparse.py](../../../report_routerbench_sparse.py)

148 dòng; SHA256 `959b39e5a4de2490936316c80a08895239f3a300c8b00faece4dc737a1e4a26a`.

Verify every cloud case, rerun decisions, and report aggregate development evidence.

Định nghĩa: `main` (L12).

## [run_appworld_after_dev.py](../../../run_appworld_after_dev.py)

65 dòng; SHA256 `1b789fa16596e2af0fe5010a2151d5fb34f99a980e8f7c32f8652fa970f87f0d`.

Run a small real AppWorld capability pilot only after MMLU inference ends.

Định nghĩa: `write` (L20); `main` (L30).

## [run_appworld_coder_v8.py](../../../run_appworld_coder_v8.py)

75 dòng; SHA256 `2911aaad176224c410ca0ed706545dcc9a20670ad815dd7bbf91e598d9f78081`.

Run the frozen Qwen3-Coder v8 AppWorld train capability screen.

Định nghĩa: `protocol` (L27).

## [run_appworld_glm_v9.py](../../../run_appworld_glm_v9.py)

75 dòng; SHA256 `f50f60b9cf6e2e92799c5bc3bc8d1793a013eceaf226d3fef55499f8d2ab71e4`.

Run the frozen GLM-4.7-Flash AppWorld v9 train capability screen.

Định nghĩa: `protocol` (L27).

## [run_appworld_legacy_react_v7.py](../../../run_appworld_legacy_react_v7.py)

245 dòng; SHA256 `e03c6ce7b1f72febb0e167fbec6feaed16103503221f6fdadb490a2e89296459`.

Gold-blind, version-matched legacy AppWorld Recoma train pilot.

Định nghĩa: `digest` (L30); `modal_token` (L34); `protocol` (L59); `configure_cache` (L89); `redirected` (L94); `make_config` (L103); `main` (L120); `public_fields` (L159); `finish_without_gold` (L173); `modal_completion` (L187).

## [run_appworld_qwen32_v8_control.py](../../../run_appworld_qwen32_v8_control.py)

71 dòng; SHA256 `3dd59e9955076c002f57187660463dd486cba4b1eac27c1137da587e22997d06`.

Paired Qwen3 32B control for the frozen v8 AppWorld capability screen.

Định nghĩa: `protocol` (L27).

## [run_appworld_train_pilot.py](../../../run_appworld_train_pilot.py)

237 dòng; SHA256 `081ac04695a8586b953959aaaaf8307ef4b91439ac8190f53cf9caef0d43e1d5`.

Paired, gold-blind AppWorld train pilot with real Modal/Ollama calls.

Định nghĩa: `sha` (L37); `now` (L41); `select_train_ids` (L45); `make_manifest` (L55); `prompt_for` (L74); `cached_modal_token` (L96); `refresh_modal_token` (L108); `ollama_call` (L117); `run_task` (L138); `main` (L176).

## [run_appworld_train_pilot_v2.py](../../../run_appworld_train_pilot_v2.py)

222 dòng; SHA256 `6b932e8079a7e1f6a5bbc267ad9cc11666a00e2eb643aed41ab3163f6986f06d`.

Gold-blind AppWorld train feasibility pilot with compact chat history.

Định nghĩa: `make_manifest` (L38); `initial_prompt` (L65); `make_messages` (L83); `call_model` (L102); `run_task` (L123); `main` (L163).

## [run_appworld_train_pilot_v3.py](../../../run_appworld_train_pilot_v3.py)

245 dòng; SHA256 `5e2f6bd7c5d24894972c9efcc113f0e6950334e4f9fcbc2803f41d45a45840f0`.

Gold-blind AppWorld train scaffold-repair diagnostic on paired v2 tasks.

Định nghĩa: `make_manifest` (L39); `initial_prompt` (L67); `make_messages` (L94); `call_model` (L113); `run_task` (L134); `main` (L181).

## [run_appworld_train_pilot_v4.py](../../../run_appworld_train_pilot_v4.py)

248 dòng; SHA256 `e020e1e876bb3a1e249b6f4dacf3b2a1fecb1bbcd4931aa306a064d05ce4d18c`.

Gold-blind AppWorld train solver-capability diagnostic on paired v3 task.

Định nghĩa: `make_manifest` (L40); `initial_prompt` (L70); `make_messages` (L97); `call_model` (L116); `run_task` (L137); `main` (L184).

## [run_appworld_train_pilot_v5.py](../../../run_appworld_train_pilot_v5.py)

282 dòng; SHA256 `ca0dd2f6854b7431e2a0edb225d6aa8a33074de5f010967b050db61eb8bcbc07`.

Gold-blind AppWorld train thinking-policy complementarity diagnostic.

Định nghĩa: `make_manifest` (L41); `initial_prompt` (L72); `make_messages` (L99); `call_model` (L118); `run_task` (L160); `main` (L215).

## [run_appworld_train_pilot_v6.py](../../../run_appworld_train_pilot_v6.py)

253 dòng; SHA256 `0300af266145b251afbef0ee1cb2ab3e87209d774edd3538a6d8016223c7a329`.

Paired train-only AppWorld scaffold diagnostic using real Modal/Ollama calls.

Định nghĩa: `make_manifest` (L49); `prompt_for` (L83); `call_model` (L88); `run_task` (L127); `main` (L185).

## [run_appworld_v10_simplified.py](../../../run_appworld_v10_simplified.py)

175 dòng; SHA256 `7621aedcd7d60e951f1bfbe4082fdbf55bc141ef90d4785e6b670701112998a3`.

Gold-blind AppWorld 0.2 official simplified ReAct capability screen.

Định nghĩa: `protocol` (L25); `setup_env` (L48); `verify_model` (L55); `main` (L79); `modal_completion` (L118); `GoldBlindAgent` (L142); `initialize` (L143); `set_finished` (L150).

## [run_audit.py](../../../run_audit.py)

21 dòng; SHA256 `a867336be8e78e3125786d55c8d6f621e108d95525cee9ec059da06f214946c5`.

Convenience entrypoint for Capability Audit.

## [run_context_to_appworld.py](../../../run_context_to_appworld.py)

92 dòng; SHA256 `46c0e0ece36cd5b2e05878606742b01f8ac1b4a6f8b6f8832be75e86b2d881ff`.

Finish the frozen context diagnostic, then run the disjoint AppWorld v2 pilot.

Định nghĩa: `record` (L25); `row_count` (L35); `retry_command` (L42); `main` (L55).

## [run_dart_audit_pilot.py](../../../run_dart_audit_pilot.py)

282 dòng; SHA256 `294b6548ac900854496d59fc686f4290f9aa238d824ce1f4bb1de53a527a1b50`.

Exploratory DART replay on real AppWorld trajectories and observed self-reports.

Định nghĩa: `digest` (L30); `write_status` (L34); `observed_feedback` (L41); `prepare_inputs` (L57); `summarize` (L87); `run` (L123); `audit` (L213); `main` (L260).

## [run_dart_followup.py](../../../run_dart_followup.py)

69 dòng; SHA256 `7d113980423b1b5c04ea07089049e79ca745456a928ff876b1e0d93cb474b284`.

Wait for the existing frozen run, then execute the locked follow-up analyses.

Định nghĩa: `status` (L18); `command` (L22); `main` (L28).

## [run_dart_gain.py](../../../run_dart_gain.py)

86 dòng; SHA256 `ab70c9a79125bcd8aebe0f222cb39a4ac7ad42a1b827451b571528ad986e6168`.

Prepare, submit, inspect, and fetch the fixed gain/structure experiment.

Định nghĩa: `prepare` (L16); `main` (L40).

## [run_dart_halving.py](../../../run_dart_halving.py)

57 dòng; SHA256 `5bdda5e3c9b1ed0ce76074c6abf06819c852e717f3140b96e0f96f97a60f1e64`.

Prepare frozen-candidate comparison with budget-adaptive gold-only baselines.

Định nghĩa: `prepare` (L14).

## [run_dart_history.py](../../../run_dart_history.py)

61 dòng; SHA256 `2708b3507f4d1e75d6441f89f26fd7a5267c897a6e2caef5c67a534b164b7ff3`.

Real-judge historical rectifier; reuses detached submit/status/fetch transport.

Định nghĩa: `prepare` (L17).

## [run_dart_judge_pipeline.py](../../../run_dart_judge_pipeline.py)

81 dòng; SHA256 `e84b75cc3d139ca89cbbef01d3d29660ceb29f3bbbc2a26cc2bd5e85f459e007`.

Bounded real-inference -> fixed quality gate -> complete replay controller.

Định nghĩa: `status` (L19); `command` (L24); `collect` (L31); `run` (L41).

## [run_dart_modal_judge.py](../../../run_dart_modal_judge.py)

245 dòng; SHA256 `a94950a2691edfc1d75680f1906d1fd61eab0fa312a0f4fba346a2423961283a`.

Gold-blind, resumable Modal judgment of frozen real AppWorld trajectories.

Định nghĩa: `sha` (L37); `canonical` (L41); `now` (L45); `atomic_json` (L49); `append` (L55); `case_order` (L62); `prompt_for` (L70); `read_case` (L81); `parse_probability` (L89); `read_ledger` (L99); `request` (L114); `run` (L134); `collect` (L142); `status` (L171); `main` (L222).

## [run_dart_neural.py](../../../run_dart_neural.py)

118 dòng; SHA256 `223f781f1e02dd6b76eebea44757fdfb7e1ca0c11f54619eab80eceec6426957`.

Prepare public normal packet; submit detached cloud job; inspect or fetch.

Định nghĩa: `prepare` (L16); `main` (L67).

## [run_dart_paired_ablation.py](../../../run_dart_paired_ablation.py)

140 dòng; SHA256 `5a836d90650fa10a7334e135d58d226b3fddad0f13b233628fbfe141ff4a27d4`.

Single locked paired-audit ablation; real archived outcomes, no model calls.

Định nghĩa: `run` (L19).

## [run_dart_paired_history.py](../../../run_dart_paired_history.py)

64 dòng; SHA256 `5d217b267cb7dc1018ce5883f9246c271dbc1d602c6318d20b3299859818bb41`.

Use exact original paired masks with unchanged cross-fitted estimators.

Định nghĩa: `prepare` (L18).

## [run_dart_same_audit.py](../../../run_dart_same_audit.py)

196 dòng; SHA256 `a72d86fcfc6236fc49688d0ee4a85400b2d095504f889c14900ca23061960072`.

Frozen controlled forensics on real archived audits, not new inference.

Định nghĩa: `run` (L25); `audit` (L101); `contrast` (L186).

## [run_post_dev_analysis.py](../../../run_post_dev_analysis.py)

59 dòng; SHA256 `b85c85c25309d87de60868faaede8a1ff884f151702e4310f28e49f8873d3395`.

Wait for the real dev controller, then run all frozen follow-up analyses.

Định nghĩa: `write` (L19); `main` (L28).

## [run_real_dev_context_pilot.py](../../../run_real_dev_context_pilot.py)

175 dòng; SHA256 `1d845d700e1fce7632f9db37d7d56e6cbbfa4e4996b24e2efa054b73f283ed4f`.

Resumable real Qwen8 thinking diagnostic with an explicit 8K context window.

Định nghĩa: `selected_ids` (L35); `freeze` (L44); `run` (L70); `main` (L165).

## [run_real_dev_pipeline.py](../../../run_real_dev_pipeline.py)

137 dòng; SHA256 `9460a5e8de201375ea24fa8095fcc07e8f32de0ba262d8a4f570b992c48748c4`.

Watchdog for the long real thinking run after direct collection completes.

Định nghĩa: `now` (L31); `counts` (L35); `status` (L45); `run_thinking` (L55); `main` (L107).

## [run_real_dev_pool.py](../../../run_real_dev_pool.py)

222 dòng; SHA256 `35c7ca6ad9f1025f0fa0e3c8dc402a0c2082a53717761f965400e12c7e86e069`.

Resumable real Modal/Ollama inference on frozen development IDs only.

Định nghĩa: `preflight` (L38); `make_manifest` (L61); `completed_keys` (L87); `run` (L109); `main` (L207).

## [run_real_pool_overlap.py](../../../run_real_pool_overlap.py)

197 dòng; SHA256 `80f4aa8d97d36519393e064a9985bf62dc6eea73c4f7d49c119e50228d8475e3`.

Collect real direct answers on Week 4's paired questions for pool screening.

Định nghĩa: `preflight` (L33); `manifest_for` (L51); `load_completed` (L71); `run` (L87); `main` (L182).

## [run_real_week3.py](../../../run_real_week3.py)

256 dòng; SHA256 `0ba986a6164b870f907d8ffcf92ab49f076f0003b1bf56438e56fd20414d40f4`.

Collect real, per-question MMLU-Pro answers for the RepGuard study.

Định nghĩa: `utc_now` (L37); `load_dataset_and_splits` (L41); `make_manifest` (L47); `prepare_manifest` (L74); `apply_test_extension` (L90); `existing_keys` (L119); `collect` (L131); `main` (L235).

## [run_real_week4_thinking.py](../../../run_real_week4_thinking.py)

235 dòng; SHA256 `68786661e8d94b044085d443b9edcb7a9f90e73ca2daacae9a5489a030239944`.

Paired, resumable real Qwen3 thinking screen on unused MMLU-Pro train items.

Định nghĩa: `variants_for` (L34); `canonical_hash` (L40); `select_unused` (L45); `frozen_manifest` (L62); `load_completed` (L85); `append_jsonl` (L101); `run` (L109); `main` (L218).

## [run_real_week5_blind_judge.py](../../../run_real_week5_blind_judge.py)

220 dòng; SHA256 `e84ae4038b479966aec66622af61621e105a27334fc6ec7125f4dfbb448f6042`.

Freeze and collect a candidate-blind Modal judge on the same 280 questions.

Định nghĩa: `prompt_for` (L33); `response_schema` (L44); `build_manifest` (L51); `prepare` (L85); `completed_cases` (L105); `collect` (L119); `main` (L200).

## [run_real_week5_modal_judge.py](../../../run_real_week5_modal_judge.py)

291 dòng; SHA256 `7aabb90b63aa701473ca38dc0f4faa9a1e427d3606e8d724483d526aeee274e2`.

Collect real Modal-hosted Ollama judgments of Week 3 agent answers.

Định nghĩa: `prompt_for` (L38); `response_schema` (L52); `select_history` (L60); `build_manifest` (L73); `prepare` (L118); `fetch_metadata` (L158); `read_done` (L176); `call_judge` (L192); `collect` (L207); `main` (L263).

## [run_real_week5_pipeline.py](../../../run_real_week5_pipeline.py)

223 dòng; SHA256 `a77d3a4a5764db2d6cfbc3c27b92fd7a509aa92f18be8072699a10daf2c5f2ef`.

Resume the predeclared Modal experiments sequentially after Week 4 finishes.

Định nghĩa: `now` (L31); `status` (L35); `count_jsonl` (L42); `week4_runner_alive` (L49); `restart_week4_runner` (L54); `modal_container_active` (L62); `recover_week4_runner` (L69); `wait_for_week4` (L93); `run_stage` (L150); `main` (L168).

## [run_real_week5_validation.py](../../../run_real_week5_validation.py)

204 dòng; SHA256 `2c79e9fd2861e7c5154e79af1da06e6944e0f636f1e0f6a3e7c556f29f6faa2b`.

Freeze and collect an independent real MMLU-Pro dev validation set.

Định nghĩa: `select_unused_dev` (L32); `make_manifest` (L49); `prepare` (L76); `collect` (L96); `main` (L181).

## [run_routerbench_finqa_consensus.py](../../../run_routerbench_finqa_consensus.py)

64 dòng; SHA256 `1f0554d913211b10ff2c4f1caaf8f4224492cc3860735a892a2e6a0f950a9579`.

Freeze and control the detached FinQA exact-answer consensus replay.

Định nghĩa: `prepare` (L18).

## [run_routerbench_finqa_feedback.py](../../../run_routerbench_finqa_feedback.py)

56 dòng; SHA256 `9a1ec67bdc1523864d17f1d9022f2c554e636f985be23cc2b85f9fc7852cabf2`.

Freeze and run the bounded genuine FinQA judge pilot from verified development metadata.

Định nghĩa: `prepare` (L14).

## [run_routerbench_headroom.py](../../../run_routerbench_headroom.py)

94 dòng; SHA256 `0d1548aeb43cbd35ba0b2145f2d922350b93b1b64c2aad85feeaf8d4e9b1139a`.

Freeze metadata-selected development questions before any score access.

Định nghĩa: `prepare` (L14).

## [run_routerbench_intake.py](../../../run_routerbench_intake.py)

32 dòng; SHA256 `d0245e1bf36dd67300695e665350a2c22eb95b1b565f1d4d19f6e1d7221933ee`.

Prepare/submit/status/fetch the pinned external-data inventory on Modal.

Định nghĩa: `prepare` (L12).

## [run_routerbench_intake_v2.py](../../../run_routerbench_intake_v2.py)

32 dòng; SHA256 `7c643eb6018ac279181f9dc2eab044af2ec01fc51a382bb174033c6bd6f2513e`.

Prepare/submit/status/fetch the pinned external-data inventory on Modal.

Định nghĩa: `prepare` (L12).

## [run_routerbench_pilot.py](../../../run_routerbench_pilot.py)

57 dòng; SHA256 `e443cc1f0a0160b7f3c12d22e893f1c887e925d2d5c014c07d2e329334ddbedc`.

Prepare only from verified outcome-free metadata; run bounded real judge pilot.

Định nghĩa: `prepare` (L14).

## [run_routerbench_prompt_groups.py](../../../run_routerbench_prompt_groups.py)

63 dòng; SHA256 `ede9b2c6730ea9a7b8115b3fc3717a32f4b2209524b9badf062236cfba759059`.

Prepare a frozen prompt-only grouping packet from verified intake metadata.

Định nghĩa: `prepare` (L13).

## [run_routerbench_sparse.py](../../../run_routerbench_sparse.py)

48 dòng; SHA256 `8b60345f19769d5c8c5f06b0170f97836d9f72f416dd680a50729459a305d5fa`.

Verify the real pilot and freeze a sparse-gold replay before submitting it.

Định nghĩa: `prepare` (L15).

## [run_week2.py](../../../run_week2.py)

90 dòng; SHA256 `abefd02d30d49f6519b0159d4fd024f58d974ace98c0ca0732192e1c8b4eb9c2`.

Convenience entrypoint for RepGuard Week 2 Experiments (HistRepEval v0.1).

Định nghĩa: `main` (L27).

## [run_week3.py](../../../run_week3.py)

576 dòng; SHA256 `48f5d877edf7d793a448f8803594c7d56c0bba9c27ec29058ff390eaa4b34f41`.

run_week3.py - Week 3 Experimental Runner for RepGuard/ECRT.

Định nghĩa: `_make_corruptor` (L78); `Week3Experiments` (L95); `__init__` (L98); `run_qt_grid` (L117); `_run_single_cell` (L151); `_save_qt_results` (L227); `_print_qt_summary` (L239); `run_attack_pilot` (L264); `_run_a1` (L275); `_run_a2` (L319); `run_statistical_analysis` (L364); `make_go_no_go_decision` (L418); `_update_research_log` (L455); `_update_paper_claims` (L489); `main` (L522).

## [src/repguard/__init__.py](../../../src/repguard/__init__.py)

3 dòng; SHA256 `0c7ea10eaeb030be8e19f05ef1368959d9cd84b24cf23e8cb50b74ee3eeb7437`.

RepGuard: Evidence-Calibrated Reputation Transfer under Imperfect Feedback.

## [src/repguard/audit/__init__.py](../../../src/repguard/audit/__init__.py)

35 dòng; SHA256 `8e0f3093504c773bcd374ebc2afa24ceaa6bc27411c9292f7ce45e0e87a0e1ee`.

Audit sub-package for RepGuard capability analysis.

Định nghĩa: `__getattr__` (L27).

## [src/repguard/audit/capability_audit.py](../../../src/repguard/audit/capability_audit.py)

1055 dòng; SHA256 `50c293f4b91159f9f67bfffa3de8e8d52ce3d758e468cd98f33c5e6b25756a7d`.

Capability Audit module for RepGuard — Step 1.1 (Week 1 exit gate).

Định nghĩa: `AgentConfig` (L66); `to_provider_config` (L96); `CapabilityAuditConfig` (L110); `from_yaml` (L138); `AgentDomainResult` (L196); `CapabilityMatrix` (L223); `accuracy_for` (L248); `best_agent_per_domain` (L253); `print_report` (L271); `to_dict` (L348); `HeterogeneityGateResult` (L379); `CapabilityAudit` (L405); `__init__` (L419); `run` (L424); `save` (L500); `_load_tasks` (L570); `_stratified_sample` (L599); `_build_provider` (L634); `_evaluate_agent_on_domain` (L666); `_check_heterogeneity` (L777); `update_research_ops` (L892); `main` (L995).

## [src/repguard/audit/design.py](../../../src/repguard/audit/design.py)

147 dòng; SHA256 `88c4e6743204504cb57534e65361622af697fec3d58d4564a93d9879000f5d3a`.

Fixed-budget randomized auditing and design-unbiased policy contrasts.

Định nghĩa: `inclusion_probabilities` (L12); `pivotal_sample` (L38); `corrected_policy_values` (L67); `disagreement_weights` (L97); `contrast_allocation` (L111).

## [src/repguard/audit/feedback.py](../../../src/repguard/audit/feedback.py)

49 dòng; SHA256 `95eacdf1a7da0646121b72fdde41e0034cbc3ecc74098634e76266b8a15ccc66`.

Validated categorical feedback matrix from a completed real-judge ledger.

Định nghĩa: `judge_feedback` (L11).

## [src/repguard/audit/forensics.py](../../../src/repguard/audit/forensics.py)

59 dòng; SHA256 `a9bb265ff9de285931de2c45ad4517bedda877a38d14169418838b3f137aa4fd`.

Learners for the frozen same-audit ablation; no full-gold input allowed.

Định nghĩa: `ridge_proxy` (L7); `sampled_values` (L29); `choose` (L57).

## [src/repguard/audit/paired.py](../../../src/repguard/audit/paired.py)

71 dòng; SHA256 `b81e8fc5b496fc499f795b7c5db5c6ddb7b15088653d9eafe8eecc10c6d360e1`.

Uniform task-block audits with exact record budgets and known inclusion.

Định nghĩa: `paired_sample` (L13); `joint_inclusion` (L25); `exact_ht_total_variance` (L37); `select_paired` (L54).

## [src/repguard/audit/routing.py](../../../src/repguard/audit/routing.py)

163 dòng; SHA256 `185fe182da4c83948029eeb420b9c102f6d1c119e9286d0470d43aa58c436126`.

Small policy class and gold-isolated learner for the exploratory DART pilot.

Định nghĩa: `generator_id` (L17); `construction_selection_split` (L21); `TextFeatures` (L32); `terms` (L35); `__init__` (L39); `transform` (L45); `global_means` (L56); `knn_routes` (L60); `policy_bank` (L73); `uniform_audit_routes` (L81); `calibrated_proxy` (L102); `select_policy` (L117).

## [src/repguard/config.py](../../../src/repguard/config.py)

239 dòng; SHA256 `c7704fb67f1bb4b9549c8c0bb1082efcca1109bf1924ddc46bdfc77e6c8d32a6`.

Pydantic-based experiment configuration schema for RepGuard.

Định nghĩa: `ExperimentConfig` (L18); `SplitConfig` (L27); `ratios_must_sum_to_one` (L42); `DataConfig` (L52); `ProviderParams` (L63); `ProviderConfig` (L71); `validate_provider_name` (L83); `RateLimitConfig` (L92); `RetryConfig` (L99); `CacheConfig` (L107); `HarnessConfig` (L114); `validate_prompt_mode` (L128); `LoggingConfig` (L137); `FeedbackConfig` (L145); `TransferConfig` (L153); `AgentPoolConfig` (L159); `RepGuardConfig` (L165); `from_yaml` (L183); `config_hash` (L210); `get_git_commit` (L223).

## [src/repguard/data/__init__.py](../../../src/repguard/data/__init__.py)

1 dòng; SHA256 `2d8ee8f241de86bbb90ff18b25c5eb75b239111ad203a6b0521a2916812f1f7a`.

Data layer for RepGuard.

## [src/repguard/data/mmlu_pro.py](../../../src/repguard/data/mmlu_pro.py)

363 dòng; SHA256 `2232d2862c35f6bd4ccc9674c4b951225934273e3b2bc1700d2c5c9901a3c2ed`.

MMLU-Pro dataset download, parsing, and caching.

Định nghĩa: `load_mmlu_pro` (L63); `_download_and_parse` (L114); `_parse_item` (L151); `_load_from_cache` (L217); `_save_to_cache` (L239); `_task_record_to_dict` (L251); `_dict_to_task_record` (L276); `_count_subjects` (L304); `create_synthetic_tasks` (L309).

## [src/repguard/data/models.py](../../../src/repguard/data/models.py)

199 dòng; SHA256 `75dbee66d67be5343cb299c81191cb892f66902a57b8be9d1ea63615470e943f`.

Core data models for RepGuard.

Định nghĩa: `FeedbackSourceType` (L22); `TaskMetadata` (L38); `TaskRecord` (L61); `to_online_view` (L91); `check_answer` (L108); `OnlineTaskView` (L123); `FeedbackSignal` (L145); `AgentResponse` (L172).

## [src/repguard/data/splits.py](../../../src/repguard/data/splits.py)

308 dòng; SHA256 `f2cda43823c6bbe6e00151801f3cb6f52305c02d5af3d07ae4f624203e1413e1`.

Deterministic, leak-proof dataset splitting for RepGuard.

Định nghĩa: `DataSplit` (L30); `size` (L49); `subject_distribution` (L53); `SplitManifest` (L66); `save` (L84); `load` (L107); `create_splits` (L127); `_assign_bucket` (L193); `_make_data_split` (L223); `create_manifest` (L244); `verify_no_leakage` (L270).

## [src/repguard/evaluation/__init__.py](../../../src/repguard/evaluation/__init__.py)

1 dòng; SHA256 `fc05e024a4eb4a213d43aa56ae02db61d2fb561d6f0892d4df2f0bf23378ef59`.

Evaluation metrics for RepGuard.

## [src/repguard/evaluation/decision_value.py](../../../src/repguard/evaluation/decision_value.py)

82 dòng; SHA256 `892757d821859518bbba75724237ed8807edae8335c05c87b2cbc63006dc6d89`.

Paired, task-level decision-value measurements for HistRepEval.

Định nghĩa: `PairedDecisionValue` (L14); `realized_gain` (L26); `sensitivity` (L30); `rescue_opportunity` (L34); `to_dict` (L38); `paired_decision_value` (L44).

## [src/repguard/evaluation/metrics.py](../../../src/repguard/evaluation/metrics.py)

107 dòng; SHA256 `0f5c30ccab8794820050477f2901ea60ba96723caf5517baaf3338601a7461ea`.

Evaluation metrics for RepGuard.

Định nghĩa: `compute_accuracy` (L17); `compute_per_domain_accuracy` (L31); `bootstrap_confidence_interval` (L74).

## [src/repguard/harness/__init__.py](../../../src/repguard/harness/__init__.py)

1 dòng; SHA256 `c4344f2b8af624d4e69baa3ff31d8a893256fb2b090fa2e4d6827314e98ca960`.

Evaluation harness for RepGuard.

## [src/repguard/harness/cache.py](../../../src/repguard/harness/cache.py)

201 dòng; SHA256 `1d544fe37d0557067e4a58a46275dd2e845b102f5f641d3637a456886dce02ac`.

Content-addressable disk cache for LLM responses.

Định nghĩa: `DiskCache` (L25); `__init__` (L41); `enabled` (L57); `hits` (L62); `misses` (L67); `hit_rate` (L72); `make_key` (L78); `get` (L101); `put` (L142); `clear` (L170); `get_stats` (L189).

## [src/repguard/harness/parser.py](../../../src/repguard/harness/parser.py)

158 dòng; SHA256 `a22fea90494b357636fdafa89c73b8c2880c673b195b179270a88e7614a358a9`.

Response parsing for multiple-choice answer extraction.

Định nghĩa: `ParseResult` (L15); `is_valid` (L31); `parse_response` (L78).

## [src/repguard/harness/prompts.py](../../../src/repguard/harness/prompts.py)

139 dòng; SHA256 `1e81978ed1c772a39c0d4ff25d1a70cf74c74e09d1f3c461c9d25329a1323ba0`.

Prompt formatting for multiple-choice evaluation.

Định nghĩa: `FormattedPrompt` (L21); `format_prompt` (L39); `_format_options` (L80); `_build_direct_prompt` (L96); `_build_cot_prompt` (L119).

## [src/repguard/harness/rate_limiter.py](../../../src/repguard/harness/rate_limiter.py)

137 dòng; SHA256 `59068eaea68ee1c608dbcf74deb69e659b908e48710da0526a4240abf28bbef9`.

Token-bucket rate limiter with configurable RPM/TPM limits.

Định nghĩa: `RateLimiter` (L17); `__init__` (L30); `wait_if_needed` (L52); `record_request` (L84); `_prune_old_entries` (L96); `_compute_sleep_time` (L110); `get_stats` (L125).

## [src/repguard/harness/runner.py](../../../src/repguard/harness/runner.py)

437 dòng; SHA256 `f0d014e592e2390235e1b580ee37b13926aa40f7868dc7c11fe23ebb2728550c`.

Single-agent evaluation harness for RepGuard.

Định nghĩa: `SingleAgentRunner` (L44); `__init__` (L61); `run` (L88); `_load_data` (L208); `_evaluate_task` (L229); `_print_results` (L303); `RunResult` (L345); `__init__` (L359); `main` (L380).

## [src/repguard/logging_.py](../../../src/repguard/logging_.py)

284 dòng; SHA256 `632ab46dd2ea2473173720fbf73a1061be16550fade31335928c6541d6f418a0`.

Structured experiment logging for RepGuard.

Định nghĩa: `setup_console_logging` (L26); `ExperimentLogger` (L52); `__init__` (L65); `log_file` (L103); `log_event` (L107); `log_llm_call` (L159); `log_evaluation` (L202); `update_experiment_registry` (L236); `finalize` (L274).

## [src/repguard/providers/__init__.py](../../../src/repguard/providers/__init__.py)

1 dòng; SHA256 `9de4aa78e8e8288992e7ba590077de2bc5e495926f091e20ccdddb020be48ae8`.

LLM provider layer for RepGuard.

## [src/repguard/providers/anthropic_.py](../../../src/repguard/providers/anthropic_.py)

166 dòng; SHA256 `edea2b61a485b122d8a6b587c8a4daa05b08d56c325378781f1bb3577956372f`.

Anthropic LLM provider for RepGuard.

Định nghĩa: `AnthropicProvider` (L37); `__init__` (L46); `complete` (L75); `_estimate_cost` (L153).

## [src/repguard/providers/base.py](../../../src/repguard/providers/base.py)

195 dòng; SHA256 `e49ec18736f53e6097d95df10e1aef875b3f48c163b62035bbb69c0f413abfd4`.

Base LLM provider protocol and response models.

Định nghĩa: `LLMResponse` (L20); `LLMProvider` (L46); `__init__` (L54); `model_id` (L66); `total_cost` (L71); `total_calls` (L76); `complete` (L81); `_track_cost` (L107); `get_stats` (L116); `create_provider` (L130).

## [src/repguard/providers/gemini_.py](../../../src/repguard/providers/gemini_.py)

354 dòng; SHA256 `91cc01a0675d9a66d9742aa5e1edbd444552a93fda0368b4154f3de6be371f38`.

Google Gemini provider via REST API (no SDK required).

Định nghĩa: `GeminiProvider` (L43); `__init__` (L56); `complete` (L87); `__repr__` (L198); `_build_payload` (L205); `_extract_text` (L248); `_estimate_cost` (L288); `_parse_retry_delay` (L319).

## [src/repguard/providers/mock.py](../../../src/repguard/providers/mock.py)

132 dòng; SHA256 `b7cc21f87db17591cfe9a3ccf7539be91b2a6be1e760fc67ef713707276d93a4`.

Deterministic mock LLM provider for dry-run testing.

Định nghĩa: `MockProvider` (L21); `__init__` (L44); `complete` (L62); `__repr__` (L130).

## [src/repguard/providers/ollama_.py](../../../src/repguard/providers/ollama_.py)

358 dòng; SHA256 `4ef66d1eff4a89a60b1a509b91b621f81b6bd109c1b1c86408c1505af994b8a0`.

Ollama LLM provider supporting both local instances and Modal-hosted endpoints.

Định nghĩa: `_get_modal_auth_token` (L31); `_fetch` (L69); `OllamaProvider` (L83); `__init__` (L95); `complete` (L150); `__repr__` (L305); `_build_payload` (L312).

## [src/repguard/providers/openai_.py](../../../src/repguard/providers/openai_.py)

159 dòng; SHA256 `8a3c7155cd92cb7da1b84afbdcba2bb611bd666f58bf9e5860b6f212e0a3acbc`.

OpenAI-compatible LLM provider for RepGuard.

Định nghĩa: `OpenAIProvider` (L39); `__init__` (L48); `complete` (L74); `_estimate_cost` (L139); `_build_raw_response` (L154).

## [src/repguard/reputation/__init__.py](../../../src/repguard/reputation/__init__.py)

52 dòng; SHA256 `8e6265b09041f1895739b9370ea261349aa7e37f785598080193358f32bc7ed1`.

RepGuard Reputation module — Week 2–3.

## [src/repguard/reputation/aggregator.py](../../../src/repguard/reputation/aggregator.py)

170 dòng; SHA256 `435022e193e23e7ed1eec41e5d014d4f14e95c94ea73090b34923271b9d81ffd`.

ReputationAggregator — combine agent answers weighted by reputation scores.

Định nghĩa: `AggregationResult` (L23); `is_correct` (L40); `bind_ground_truth` (L46); `__repr__` (L51); `ReputationAggregator` (L58); `__init__` (L66); `majority_vote` (L69); `reputation_weighted_vote` (L107); `aggregate` (L159).

## [src/repguard/reputation/audited.py](../../../src/repguard/reputation/audited.py)

131 dòng; SHA256 `bac250a767a71d8b16c7d9c1a6710c153a0985067cd7500657a73ed5c8bcd998`.

Experimental audited reputation with agent-specific feedback channels.

Định nghĩa: `_wilson_lower` (L20); `AuditedChannel` (L32); `correctness_given` (L41); `AuditedECRTReputation` (L52); `__init__` (L61); `_estimate_channel` (L69); `fit` (L89); `channel` (L105); `score` (L110).

## [src/repguard/reputation/baselines.py](../../../src/repguard/reputation/baselines.py)

427 dòng; SHA256 `776bd7f8222053d9fdff3fbfc642bae48c5fe685b463a48adbabbb1e47fb4188`.

Reputation Baselines for RepGuard — HistRepEval v0.1 (Week 2).

Định nghĩa: `BetaParams` (L33); `mean` (L44); `lower_credible_bound` (L49); `evidence_count` (L61); `update` (L65); `__repr__` (L75); `ReputationScore` (L80); `confidence_adjusted` (L99); `__repr__` (L106); `BaseReputation` (L118); `fit` (L130); `score` (L141); `score_all` (L152); `name` (L162); `UniformReputation` (L170); `fit` (L177); `score` (L182); `name` (L193); `GlobalBetaReputation` (L201); `__init__` (L212); `fit` (L218); `score` (L227); `name` (L241); `SkillConditionedReputation` (L249); `__init__` (L260); `fit` (L266); `score` (L275); `domain_params` (L289); `name` (L298); `OracleReputation` (L306); `__init__` (L318); `fit` (L328); `score` (L337); `global_score` (L352); `name` (L367); `ZeroEvidenceGate` (L375); `__init__` (L385); `fit` (L399); `score` (L403); `name` (L426).

## [src/repguard/reputation/ecrt.py](../../../src/repguard/reputation/ecrt.py)

259 dòng; SHA256 `1a98f23cdf3039911016877cf15a80b58df05e800a492781f40e96ce2520ba8a`.

ECRT — Evidence-Calibrated Reputation Transfer (Week 3–4 Core Method).

Định nghĩa: `FeedbackReliabilityParams` (L43); `FeedbackReliabilityEstimator` (L56); `calibrate` (L59); `infer_p_correct` (L88); `oracle_p_correct` (L112); `ECRTReputation` (L121); `__init__` (L137); `fit` (L162); `score` (L168); `_compute_tau` (L194); `decision_weight` (L206); `_compute_p_correct` (L215); `name` (L225); `__repr__` (L228); `build_ecrt_variants` (L238).

## [src/repguard/reputation/episode.py](../../../src/repguard/reputation/episode.py)

104 dòng; SHA256 `8ab8b14f010159c15796008c47c468d88fbd11491a26ff81216b795259a74277`.

EpisodeRecord — the atomic unit of historical interaction data in HistRepEval.

Định nghĩa: `DomainTransferCondition` (L19); `EpisodeRecord` (L31); `oracle_correct` (L57); `has_feedback` (L69); `feedback_positive` (L74); `with_corrupted_feedback` (L81); `__repr__` (L98).

## [src/repguard/reputation/experiment.py](../../../src/repguard/reputation/experiment.py)

675 dòng; SHA256 `01c3891a8d9d94113cb23dec85748a5c4318f657d602157b18b413109b8349b9`.

HistRepEval v0.1 — Week 2 Experimental Suite for RepGuard.

Định nghĩa: `HistRepEvalGenerator` (L51); `__init__` (L69); `_load_matrix` (L80); `agents` (L117); `domains` (L121); `generate_episodes` (L127); `generate_target_tasks` (L182); `Week2Experiments` (L217); `__init__` (L220); `run_baselines_comparison` (L238); `run_feedback_corruption_sweep` (L308); `run_task_mismatch_failure_demo` (L384); `eval_team` (L435); `_print_baseline_summary` (L476); `_print_feedback_sweep_table` (L503); `_print_mismatch_table` (L525); `save_and_log` (L566).

## [src/repguard/reputation/feedback.py](../../../src/repguard/reputation/feedback.py)

152 dòng; SHA256 `eeacd121c1db9f6344b86f7318898f3133d4d67bdc1fa286a9cedac4da509683`.

FeedbackCorruptor — controlled feedback noise and sparsity injection.

Định nghĩa: `FeedbackRegime` (L25); `FeedbackCorruptor` (L42); `__init__` (L54); `oracle` (L67); `noisy` (L71); `sparse` (L75); `adversarial` (L80); `corrupt` (L83); `_corrupt_episode` (L100); `_apply_noise` (L136); `describe` (L142); `__repr__` (L151).

## [src/repguard/reputation/metrics.py](../../../src/repguard/reputation/metrics.py)

378 dòng; SHA256 `e7b8fb5b922d8a46aec1bdd28d9fe1078061a793b5ed31010e039e30112b87bf`.

Reputation evaluation metrics for HistRepEval v0.1–v0.2 (Week 2–3).

Định nghĩa: `MetricsResult` (L26); `summary` (L58); `as_dict` (L66); `__repr__` (L83); `ReputationMetrics` (L87); `evaluate` (L101); `_compute_ece` (L164); `_compute_expert_leverage` (L198); `_compute_brier_score` (L213); `_compute_neg_log_likelihood` (L231); `bootstrap_ci` (L252); `_spearman_correlation` (L285); `rank` (L298); `compare_baselines` (L328); `grid_summary` (L347).

## [src/repguard/reputation/transfer.py](../../../src/repguard/reputation/transfer.py)

206 dòng; SHA256 `8ed79d306b1ba4a1517900a0d7da39e51bde0a0d9d0f17f1c09bf6a83dcad306`.

TransferEstimator — task transferability strata (experimental variable T).

Định nghĩa: `TransferEstimate` (L28); `__repr__` (L42); `TransferEstimator` (L49); `__init__` (L98); `estimate` (L108); `_is_related` (L140); `filter_episodes_by_condition` (L155); `tau_weights` (L191).

## [src/repguard/seed.py](../../../src/repguard/seed.py)

122 dòng; SHA256 `eaa10a39c9f3134b1b4adfc184016791b2f83dfd5ecb09716b147008aba6b245`.

Deterministic seed management for reproducible experiments.

Định nghĩa: `SeedManager` (L17); `__init__` (L33); `master_seed` (L42); `derive` (L46); `get_rng` (L65); `get_numpy_rng` (L80); `seed_everything` (L94); `__repr__` (L112); `to_dict` (L116).

## [tests/__init__.py](../../../tests/__init__.py)

1 dòng; SHA256 `4ec99e32bf4d1fb99e5a1802290928cb9085d9eb62b49ed310546f4dfff79a03`.

Test package for RepGuard.

## [tests/conftest.py](../../../tests/conftest.py)

77 dòng; SHA256 `d79dbe6fbf7930c63139dc1d706e815e87b98454d9e8e386a6e714f06c61cb37`.

Shared test fixtures for RepGuard test suite.

Định nghĩa: `seed_manager` (L16); `sample_task` (L22); `sample_tasks` (L40); `default_config` (L46); `tmp_config` (L58).

## [tests/test_audit_design.py](../../../tests/test_audit_design.py)

58 dòng; SHA256 `7b7512684e03c0d9dc73c31a53195611b8162b37614b121ccb589da9329fb38a`.

Synthetic fixtures test statistics only; they are never research outcomes.

Định nghĩa: `test_exact_budget_and_empirical_inclusion_probabilities` (L10); `test_residual_correction_unbiased_with_wrong_proxy` (L22); `test_all_labels_revealed_recovers_exact_policy_success` (L37); `test_invalid_probabilities_and_route_indices_fail_closed` (L44); `test_fixed_seed_is_reproducible` (L54).

## [tests/test_audit_routing.py](../../../tests/test_audit_routing.py)

77 dòng; SHA256 `f39500e537a003e1684a7333f4557f8610cd1196214d4c1d94ef58a92dbb7c93`.

Định nghĩa: `test_generators_never_cross_inner_partition` (L8); `test_query_text_cannot_add_vocabulary` (L15); `test_channel_calibration_uses_only_revealed_anchors` (L23); `test_unqueried_gold_cannot_change_policy_or_sampling` (L31); `test_all_audit_arms_query_same_exact_budget` (L47); `audit` (L53); `test_uniform_controls_use_exact_budget_and_ignore_unqueried_gold` (L59); `audit` (L66).

## [tests/test_audited_ecrt.py](../../../tests/test_audited_ecrt.py)

54 dòng; SHA256 `0df73b6a1c157a077957bd4417f1a630427f49e7a7021f1a8f11650674e45eee`.

Tests for the experimental audited feedback channel.

Định nghĩa: `episode` (L9); `test_uninformative_feedback_falls_back_to_disjoint_audit` (L18); `test_channels_are_agent_specific_under_targeted_false_positives` (L29); `test_unrelated_history_and_audits_have_zero_transfer` (L42); `test_history_and_audit_cannot_share_agent_task_id` (L51).

## [tests/test_cache.py](../../../tests/test_cache.py)

89 dòng; SHA256 `4c8c5560587f21f22944859576b544061757bb1b720a362701ab756a1dedeec0`.

Tests for the disk cache.

Định nghĩa: `TestDiskCache` (L11); `test_make_key_is_deterministic` (L14); `test_different_params_produce_different_keys` (L20); `test_cache_miss` (L26); `test_put_and_get` (L32); `test_disabled_cache` (L54); `test_clear` (L62); `test_hit_rate` (L72); `test_get_stats` (L82).

## [tests/test_capability_audit.py](../../../tests/test_capability_audit.py)

532 dòng; SHA256 `f20517fe4188bbca1dfd458d5bbb5d17295eac00bd5c905baf2b4c4451b88989`.

Tests for the GeminiProvider and Capability Audit system.

Định nghĩa: `TestGeminiProvider` (L31); `_make_provider` (L34); `_make_api_response` (L42); `test_complete_returns_text` (L58); `test_complete_tracks_cost_across_calls` (L78); `test_http_error_raises_runtime_error` (L95); `test_empty_candidates_returns_empty_string` (L118); `test_repr` (L132); `TestExtractText` (L137); `test_normal_response` (L140); `test_missing_candidates` (L148); `test_empty_candidates_list` (L151); `test_missing_parts` (L154); `test_malformed_structure` (L158); `TestEstimateCost` (L162); `test_gemini_flash_cost` (L165); `test_gemini_pro_cost_higher_than_flash` (L173); `test_zero_tokens_is_zero_cost` (L178); `test_unknown_model_fallback` (L181); `TestCapabilityAuditConfig` (L190); `test_from_yaml` (L193); `test_missing_file_raises` (L226); `test_agent_to_provider_config` (L230); `TestHeterogeneityGate` (L250); `_make_result` (L253); `test_gate_passes_with_heterogeneous_agents` (L264); `test_gate_fails_when_one_agent_dominates` (L284); `test_gate_fails_with_single_agent` (L301); `test_gate_fails_when_spread_too_small` (L312); `TestCapabilityAuditSynthetic` (L336); `_make_synthetic_config` (L339); `test_audit_runs_end_to_end` (L362); `test_audit_save_creates_files` (L381); `test_matrix_to_dict_is_serialisable` (L398); `test_best_agent_per_domain_is_populated` (L406); `test_update_research_ops` (L416); `test_reproducibility` (L433); `TestOllamaProvider` (L454); `_make_provider` (L457); `test_complete_returns_response` (L467); `test_model_not_found_raises_pull_instructions` (L495); `test_connect_error_raises_serve_instructions` (L508); `test_provider_factory_creates_ollama` (L524).

## [tests/test_config.py](../../../tests/test_config.py)

78 dòng; SHA256 `c16486c9d8069a108a1822ee8f581a019adbe6d03cdc7e9567af2c0381b760d2`.

Tests for configuration schema.

Định nghĩa: `TestRepGuardConfig` (L13); `test_default_config_is_valid` (L16); `test_from_yaml` (L23); `test_from_yaml_file_not_found` (L38); `test_invalid_provider_name` (L43); `test_split_ratios_must_sum_to_one` (L50); `test_config_hash_is_deterministic` (L61); `test_config_hash_changes_with_seed` (L67); `test_get_git_commit_returns_string` (L74).

## [tests/test_contrast_allocation.py](../../../tests/test_contrast_allocation.py)

24 dòng; SHA256 `cd2600f2ed1b125cfafa40d73b5415daff38abf1ee5fbdf0f350ab69bb2cb04d`.

Định nghĩa: `test_contrast_design_keeps_uniform_as_objective_safeguard` (L7); `test_all_selectable_policies_receive_contrast_coverage` (L17).

## [tests/test_dart_feedback.py](../../../tests/test_dart_feedback.py)

38 dòng; SHA256 `64f529c063abbe46deae97aa51e71a2816a235d943ad7a2c003ef4031f64cdad`.

Định nghĩa: `test_abstention_calibration_is_finite_and_anchor_only` (L10); `test_completed_judge_matrix_rejects_missing_and_duplicate_rows` (L20); `write` (L28).

## [tests/test_dart_forensics.py](../../../tests/test_dart_forensics.py)

49 dòng; SHA256 `236c04af4667f443f6342261c355641a7d3d6f98a6d7a829a6fba4c76795342e`.

Định nghĩa: `test_finite_population_unbiasedness_and_census_normalization` (L10); `test_only_paid_labels_enter_calibration_and_estimation` (L28); `test_no_match_normalized_fallback_empty_calibration_and_invalid_input` (L42).

## [tests/test_dart_gain.py](../../../tests/test_dart_gain.py)

104 dòng; SHA256 `8b5e15162321e57ea392db42ed4ddb9cae9ac32b6bcec74e657c59c1334ef24c`.

Định nghĩa: `test_unpaid_label_injection_does_not_change_fits` (L14); `test_vocabulary_and_center_exclude_test_inputs` (L25); `test_anchor_subtraction_is_not_a_new_ridge_ranker` (L35); `test_signed_utility_preserves_policy_gradient_and_full_gold` (L46); `test_factor_metadata_and_missing_agent` (L59); `test_checkpoint_tampering_rejected` (L70); `test_full_cloud_state_machine_resumes_and_finishes_fixed_batch` (L79); `route` (L85).

## [tests/test_dart_modal_judge.py](../../../tests/test_dart_modal_judge.py)

51 dòng; SHA256 `f699762103c3a47a0c4e5bdae9bffecfe462a005cc8b836bedaa89acbc6bbeb5`.

Định nghĩa: `test_order_balances_agents_without_outcomes` (L9); `test_collector_reads_only_public_spec_and_trace` (L18); `test_invalid_judge_response_rejected` (L36); `test_resume_rejects_duplicate_or_changed_manifest` (L41).

## [tests/test_dart_postrun.py](../../../tests/test_dart_postrun.py)

37 dòng; SHA256 `d1264c67df33364098ca5a9d88817f63981b0fe83312359b25f549b916970bda`.

Định nghĩa: `test_feedback_metrics_and_paired_identity` (L9); `test_single_class_auc_and_balanced_accuracy_undefined` (L21); `test_gold_only_control_feedback_invariance_guard` (L26).

## [tests/test_data_models.py](../../../tests/test_data_models.py)

121 dòng; SHA256 `c69306e36adb3b8d7d0407e27cffa64783f6fa746f3bf80432c2bbb1bb77229e`.

Tests for core data models and GT isolation.

Định nghĩa: `TestTaskRecord` (L17); `test_to_online_view_strips_gt` (L20); `test_online_view_preserves_non_gt_fields` (L27); `test_check_answer_correct` (L35); `test_check_answer_incorrect` (L41); `test_task_record_is_frozen` (L47); `test_online_view_is_frozen` (L52); `TestOnlineTaskViewIsolation` (L59); `test_no_gt_attribute_access` (L62); `test_online_view_dir_has_no_gt` (L72); `TestFeedbackSignal` (L80); `test_feedback_signal_creation` (L83); `test_feedback_absent` (L96); `TestAgentResponse` (L107); `test_agent_response_creation` (L110).

## [tests/test_decision_value.py](../../../tests/test_decision_value.py)

30 dòng; SHA256 `3993e539b78ee3b8103c1aca0902423697045b4386ec5c147bead777541508a7`.

Định nghĩa: `test_paired_decision_value_keeps_rescue_ceiling_separate_from_realized_gain` (L8); `test_paired_decision_value_rejects_unpaired_or_empty_evaluations` (L26).

## [tests/test_ecrt.py](../../../tests/test_ecrt.py)

203 dòng; SHA256 `8e31d9d0cc8160f62c9854e293fdc969e1888aaf3007c2069dabc6d10acfebb3`.

Unit tests for repguard.reputation.ecrt (ECRT method & components).

Định nghĩa: `_make_episode` (L16); `TestFeedbackReliabilityEstimator` (L34); `test_default_params` (L35); `test_calibration_perfect_feedback` (L41); `test_calibration_skips_none_feedback` (L54); `test_infer_p_correct_positive_feedback` (L63); `test_infer_p_correct_negative_feedback` (L71); `test_infer_p_correct_missing_feedback` (L79); `test_oracle_p_correct` (L87); `TestECRTReputation` (L95); `test_uncertainty_ablation_selects_the_requested_weight` (L96); `test_oracle_transfer_must_be_supplied_explicitly` (L107); `test_invalid_uncertainty_mode_is_rejected` (L118); `test_unfitted_score_raises` (L122); `test_fit_returns_self` (L127); `test_score_same_domain` (L133); `test_score_unrelated_domain_filters_out` (L148); `test_score_no_transfer_mode_allows_cross_domain` (L160); `test_score_no_reliability_mode` (L172); `test_name_and_repr` (L183); `TestBuildECRTVariants` (L189); `test_build_all_variants` (L190).

## [tests/test_halving.py](../../../tests/test_halving.py)

83 dòng; SHA256 `396ec63dfdaaa4cc95d0d0736f3e4a471e62bf57b3c4e5e83358f4271a40abb7`.

Định nghĩa: `test_exact_budget_distinct_queries_round_scores_and_pairing` (L12); `query` (L16); `test_unqueried_labels_cannot_change_path` (L32); `test_known_best_and_tied_agents` (L40); `test_pipeline_resume_and_terminal_idempotence` (L50); `stub` (L55); `test_checkpoint_corruption_rejected` (L75).

## [tests/test_history_rectifier.py](../../../tests/test_history_rectifier.py)

99 dòng; SHA256 `86087275b8b4fc9d86d55e31066c6f1ba4d0f9eb6fa0aa81986bef0e067d8cf5`.

Định nghĩa: `data` (L11); `test_null_proxy_exact_original_global_including_ties` (L20); `test_prediction_excludes_own_generator_gold` (L26); `test_hidden_gold_changes_cannot_change_any_decision` (L36); `test_gold_only_predictor_does_not_consume_judge_information` (L44); `test_bad_or_empty_inputs_fail_closed` (L54); `test_history_pipeline_resume_and_excludes_test_feedback` (L63); `stub` (L69); `test_paired_wrapper_changes_only_control_name` (L92).

## [tests/test_mmlu_pro.py](../../../tests/test_mmlu_pro.py)

78 dòng; SHA256 `e58914fada4a4b15f41ab120462468f3317758a146494c5abae0c2d4d7441a85`.

Tests for MMLU-Pro data loading and synthetic task generation.

Định nghĩa: `TestCreateSyntheticTasks` (L13); `test_returns_correct_count` (L16); `test_returns_task_records` (L21); `test_tasks_have_valid_gt` (L27); `test_tasks_cover_multiple_subjects` (L34); `test_deterministic_generation` (L40); `test_different_seeds_produce_different_tasks` (L49); `test_metadata_has_valid_domain` (L60); `test_metadata_has_valid_skill_family` (L67); `test_unique_task_ids` (L74).

## [tests/test_neural_dart.py](../../../tests/test_neural_dart.py)

91 dòng; SHA256 `443c68a614de205dc430d5e9c1925c110c1dd7bb5ed35161f07340e0e7f68934`.

Định nghĩa: `test_mask_cannot_expose_unpaid_labels` (L12); `test_group_isolation_and_pca_train_only` (L21); `test_ht_only_observed_and_empty_fails` (L33); `test_identity_and_incomplete_evaluation` (L40); `test_global_exact_smoothed_tie_order` (L50); `test_remote_training_controls` (L57); `test_crash_resume_skips_committed_case_and_gate_stops` (L62); `crashing_route` (L73).

## [tests/test_ollama_thinking_protocol.py](../../../tests/test_ollama_thinking_protocol.py)

68 dòng; SHA256 `1ac3d478b04dc01414ed7dbca43788ab09de548ed564b369fcc3eecf327a1bf4`.

The paired thinking protocol must preserve arm separation and final answers.

Định nghĩa: `test_ollama_thinking_is_explicit_and_final_content_is_separate` (L11); `Response` (L16); `raise_for_status` (L19); `json` (L22); `test_select_unused_does_not_reuse_week3_history` (L39); `Task` (L40); `__init__` (L41); `Split` (L45); `test_ollama_context_override_is_explicit_and_default_is_unchanged` (L54); `test_resume_key_includes_variant_and_protocol` (L64).

## [tests/test_paired_audit.py](../../../tests/test_paired_audit.py)

64 dòng; SHA256 `0fba1987e0e0de7cf24dde1867cb36cd83769528e94cd8bfd4fd3ff54323b3cf`.

Định nghĩa: `enumerate_design` (L8); `test_exact_marginals_joint_probabilities_and_ht_variance_by_enumeration` (L20); `test_sampler_exact_budget_unique_and_balanced_agent_counts` (L37); `test_single_row_single_agent_edge_cases` (L45); `test_paired_selector_never_uses_unqueried_labels` (L52); `audit` (L57).

## [tests/test_parser.py](../../../tests/test_parser.py)

68 dòng; SHA256 `d43c9e0e8ff2679b7113283597248e129a45f73dabda76e52769b48854e9ff52`.

Tests for response parsing.

Định nghĩa: `TestParseResponse` (L10); `test_standard_formats` (L24); `test_cot_response` (L30); `test_empty_response` (L41); `test_no_answer_found` (L47); `test_invalid_letter_for_num_options` (L52); `test_confidence_levels` (L58); `test_raw_response_preserved` (L64).

## [tests/test_prompts.py](../../../tests/test_prompts.py)

59 dòng; SHA256 `1d3186ca1f4eafbeb65ecfceacabdcba363c5fbc5d9defe1da99be2ea77a1d24`.

Tests for prompt formatting.

Định nghĩa: `TestFormatPrompt` (L9); `test_direct_prompt_contains_question` (L12); `test_direct_prompt_contains_options` (L17); `test_cot_prompt_mentions_step_by_step` (L23); `test_prompt_hash_is_deterministic` (L28); `test_prompt_hash_differs_between_modes` (L34); `test_prompt_does_not_contain_gt` (L40); `test_online_view_produces_same_prompt` (L46); `test_metadata_is_captured` (L54).

## [tests/test_providers.py](../../../tests/test_providers.py)

115 dòng; SHA256 `15bacda3838a2af3f23e2984ef25104effc41610786057b0781091240aabbd68`.

Tests for LLM providers.

Định nghĩa: `TestMockProvider` (L12); `test_deterministic_responses` (L15); `test_different_prompts_may_differ` (L26); `test_response_has_metadata` (L39); `test_cot_mode_response` (L51); `test_tracks_total_calls` (L61); `TestCreateProvider` (L73); `test_creates_mock_provider` (L76); `test_openai_without_key_raises` (L82); `test_anthropic_without_key_raises` (L95); `test_unknown_provider_raises` (L108).

## [tests/test_real_dev_context_pilot_protocol.py](../../../tests/test_real_dev_context_pilot_protocol.py)

15 dòng; SHA256 `d2e23821c7effcfbc776813ba1bedfe2891a7b5b04e44949efdb3913cbec8231`.

The context diagnostic selection is fixed from IDs, without outcomes.

Định nghĩa: `test_context_pilot_selects_five_fixed_ids_per_subject` (L6).

## [tests/test_real_dev_pool_protocol.py](../../../tests/test_real_dev_pool_protocol.py)

31 dòng; SHA256 `358ba9ed11ecd8becf9cbd85ac78df03df090ea7f9056882d93691acc7f62745`.

Protocol checks for fresh development collection without holdout inference.

Định nghĩa: `fake_frozen` (L8); `test_development_manifest_excludes_holdout_ids` (L21); `test_development_manifest_rejects_holdout_overlap` (L29).

## [tests/test_real_week3_protocol.py](../../../tests/test_real_week3_protocol.py)

49 dòng; SHA256 `9322883864546b590db931a342c8b833d83a3f62be0f4bd7ee51b8c46e76394b`.

Checks for the real-data protocol that affect scientific validity.

Định nghĩa: `test_manifest_selection_is_label_free_and_disjoint` (L7); `Task` (L8); `__init__` (L9); `Split` (L13); `__init__` (L14); `test_unrelated_label_matches_real_study_transfer_weight` (L31); `test_wilson_interval_is_not_degenerate_for_five_of_five` (L38); `test_vote_tie_does_not_depend_on_agent_order` (L44).

## [tests/test_real_week5_blind_judge_protocol.py](../../../tests/test_real_week5_blind_judge_protocol.py)

33 dòng; SHA256 `ad0d0c0d5f8f53a444975491c070b198c7b8cbc5755496d64b35194cae809d01`.

Candidate-blind judge prompts cannot see candidate answers or gold labels.

Định nghĩa: `test_blind_judge_manifest_has_one_prompt_per_task_and_no_candidate` (L6); `Task` (L7); `__init__` (L8); `to_online_view` (L14).

## [tests/test_real_week5_manifest.py](../../../tests/test_real_week5_manifest.py)

23 dòng; SHA256 `6355076ea8e9c13c4426bf8ffeab9f93459fd772758cde474658b0676d7955ca`.

Independent dev validation must never reuse Week 3 calibration questions.

Định nghĩa: `test_dev_selection_is_deterministic_and_excludes_prior_calibration` (L6); `Task` (L7); `__init__` (L8); `Split` (L12).

## [tests/test_real_week5_modal_judge_protocol.py](../../../tests/test_real_week5_modal_judge_protocol.py)

55 dòng; SHA256 `94d234da1b8cbffe3e5821ca95df6c162d8ee19f4730994a4fa2b19ad596edec`.

Judge selection uses genuine agent answers and never sends benchmark gold.

Định nghĩa: `test_judge_cases_deduplicate_answers_without_gold` (L8); `Task` (L9); `__init__` (L10); `to_online_view` (L16); `test_modal_metadata_retries_transient_503` (L38); `Response` (L39); `__init__` (L40); `Client` (L43); `__init__` (L44); `request` (L47).

## [tests/test_real_week5_pipeline.py](../../../tests/test_real_week5_pipeline.py)

19 dòng; SHA256 `d9e3b1f19e740af6eb439e23eb7ee28081a860094a49e7f4a81d714244828002`.

The Modal pipeline must wait for all Week 4 calls before sharing its GPU.

Định nghĩa: `test_pipeline_does_not_advance_on_partial_week4` (L6).

## [tests/test_reputation.py](../../../tests/test_reputation.py)

466 dòng; SHA256 `90fbdcbac1e11d4b73533a903c5b299426907c1aa5b8fbc492a6c67b1cc85a24`.

Unit tests for RepGuard Week 2 — Reputation Module (HistRepEval v0.1).

Định nghĩa: `_make_episode` (L38); `_history_two_agents` (L59); `_make_episode` (L83); `TestEpisodeRecord` (L108); `test_oracle_correct_true` (L109); `test_oracle_correct_false` (L113); `test_case_insensitive` (L117); `test_has_feedback_true` (L121); `test_has_feedback_false` (L125); `test_with_corrupted_feedback_preserves_truth` (L129); `TestBetaParams` (L141); `test_uniform_prior_mean` (L142); `test_update_increases_alpha_on_correct` (L146); `test_update_increases_beta_on_incorrect` (L152); `test_mean_after_5_correct` (L158); `test_evidence_count` (L165); `TestFeedbackCorruptor` (L176); `test_oracle_regime_matches_ground_truth` (L177); `test_noisy_flips_with_eta_one` (L186); `test_sparse_masks_some_feedback` (L193); `test_adversarial_flips_incorrect_to_positive` (L201); `test_ground_truth_never_changes` (L208); `TestGlobalBetaReputation` (L221); `test_prior_before_fit` (L222); `test_all_correct_pushes_mean_high` (L228); `test_all_wrong_pushes_mean_low` (L235); `test_domain_agnostic` (L242); `test_sparse_feedback_skipped` (L252); `TestSkillConditionedReputation` (L264); `test_domain_isolation` (L265); `test_specialist_beats_generalist_in_domain` (L276); `TestOracleReputation` (L290); `test_oracle_uses_ground_truth_not_feedback` (L291); `test_oracle_exceeds_noisy_reputation` (L304); `TestZeroEvidenceGate` (L323); `test_gates_to_uniform_when_no_evidence` (L324); `test_passes_through_when_sufficient_evidence` (L330); `TestTransferEstimator` (L346); `test_same_domain_is_same` (L347); `test_same_cluster_is_related` (L353); `test_different_cluster_is_unrelated` (L359); `test_biology_to_health_is_related` (L365); `test_filter_episodes_same_only` (L370); `test_filter_episodes_related` (L383); `TestReputationAggregator` (L400); `test_majority_vote_simple` (L401); `test_majority_vote_tie_deterministic` (L407); `test_reputation_weighted_follows_high_rep` (L413); `test_empty_answers` (L425); `TestReputationMetrics` (L435); `test_perfect_calibration_has_low_ece` (L436); `test_rank_correlation_perfect` (L447); `test_team_accuracy_computed` (L459).

## [tests/test_routerbench_finqa_consensus.py](../../../tests/test_routerbench_finqa_consensus.py)

89 dòng; SHA256 `b2841aece845c6e1d893dcc62c41dc49b942c9e6b63cf33c7f2d375ec2f59ad2`.

Định nghĩa: `test_selection_excludes_pilot_and_is_order_invariant` (L17); `test_agreement_self_exclusion_unicode_and_missing` (L28); `test_archive_prediction_pass_ignores_score_and_selected_gold_checks_identity` (L41); `make_archive` (L49); `test_crossfit_analysis_does_not_use_heldout_gold` (L78).

## [tests/test_routerbench_finqa_feedback.py](../../../tests/test_routerbench_finqa_feedback.py)

114 dòng; SHA256 `cc56377c6d29a8f0f9ea58ae4a820edb990f8d09b0a7f1af437bc31c45d62fcd`.

Định nghĩa: `test_final_box_extraction_and_full_context_without_gold` (L15); `test_visible_reader_changes_only_when_selected_visible_fields_change` (L33); `test_query_selection_and_crossfit_heldout_labels` (L46); `test_selected_gold_ignores_unselected_score_and_requires_binary` (L59); `test_collector_bounded_recovery_and_no_duplicate_after_persisted_response` (L76); `request` (L84); `test_deployed_module_imports_only_mounted_files` (L106).

## [tests/test_routerbench_headroom.py](../../../tests/test_routerbench_headroom.py)

67 dòng; SHA256 `cf0daf1d21c2273b9ce398eb7be76987aaa7f20eaffa5d648243ae9f54533011`.

Định nghĩa: `test_hash_selection_does_not_depend_on_scores_or_input_order` (L14); `test_selected_score_parser_ignores_unselected_gold_and_other_fields` (L24); `extract` (L27); `test_oracle_bound_and_fractional_scores` (L44); `test_modal_module_imports_with_only_declared_files` (L61).

## [tests/test_routerbench_intake.py](../../../tests/test_routerbench_intake.py)

82 dòng; SHA256 `cb0a9a3242a0521235e0798b3968435b28944b1128f7da438f93464d641f9ae4`.

Định nghĩa: `test_metadata_invariant_to_scores_references_outputs` (L12); `test_excluded_and_unsafe_paths` (L26); `test_verified_release_layout` (L35); `test_coverage_and_unsupported_queries` (L42); `test_real_tar_exclusion_integrity_resume` (L51); `crash` (L63).

## [tests/test_routerbench_pilot.py](../../../tests/test_routerbench_pilot.py)

113 dòng; SHA256 `d60204d72a86bd48d7d83ab7c72be31f8bf485ff7f67aacc767154f934cf8f76`.

Định nghĩa: `test_gold_does_not_enter_prompt_or_change_selection` (L12); `test_crossfit_excludes_all_labels_of_heldout_questions` (L26); `test_clipping_and_strict_probability` (L35); `test_diagnostic_is_finite_and_operational_failure_stops_expansion` (L44); `test_collector_recovers_interrupted_attempt_without_repeating_completed_case` (L51); `request` (L58); `test_failed_judge_bounded_and_explicit_invalid` (L76); `request` (L81); `test_evaluator_retains_only_preselected_record_positions` (L89); `test_deployment_imports_with_only_declared_cloud_files` (L103).

## [tests/test_routerbench_prompt_groups.py](../../../tests/test_routerbench_prompt_groups.py)

76 dòng; SHA256 `22f2bbed8743005089649134cd6f41fb65646476b360aabb1e69933ee19b0d8e`.

Định nghĩa: `test_parser_retains_only_prompts_when_outcomes_change` (L14); `synthetic` (L26); `test_grouping_is_deterministic_and_marks_pilot_components` (L33); `test_grouping_rejects_wrong_coverage_and_prompt_hash` (L45); `test_pipeline_rejects_changed_archive_and_does_not_read_gold` (L54).

## [tests/test_routerbench_sparse.py](../../../tests/test_routerbench_sparse.py)

206 dòng; SHA256 `998c4133c2c0119fd087c9004f5dd6067ee7ea21719f1bab18b4f5e763933164`.

Định nghĩa: `data` (L13); `select` (L20); `factory` (L22); `test_audit_enforces_history_unique_cells_and_budget` (L29); `test_all_acquisition_paths_exact_budget_and_nested_fixed_masks` (L42); `test_low_budget_halving_and_unqueried_gold_invariance` (L69); `test_unaudited_gold_cannot_change_any_choice_or_adaptive_path` (L85); `test_crossfit_excludes_own_question_labels_and_handles_empty_fold` (L96); `test_gold_only_predictor_feedback_invariant_and_fixed_design` (L116); `packet` (L128); `test_evaluation_gold_and_feedback_changes_leave_choices_identical` (L135); `test_checkpoint_resume_does_not_repeat_finished_case_and_rejects_corruption` (L150); `stub` (L155); `test_summarizer_gate_and_question_seed_averaging` (L175); `test_modal_module_imports_with_only_declared_cloud_files` (L200).

## [tests/test_runner.py](../../../tests/test_runner.py)

63 dòng; SHA256 `f8d02a0becea0ccb416ca404fcb75d74c27147326132a5eac7d79f7dd4da10f0`.

Tests for the single-agent evaluation runner.

Định nghĩa: `TestSingleAgentRunner` (L12); `test_run_with_mock_provider` (L15); `test_run_produces_per_domain_accuracy` (L26); `test_run_creates_log_file` (L38); `test_run_with_cache` (L48).

## [tests/test_seed.py](../../../tests/test_seed.py)

61 dòng; SHA256 `af2c1b597692d2bd5b83c4c1130cda8b642442e7f8a972761adc31d3851d045e`.

Tests for deterministic seed management.

Định nghĩa: `TestSeedManager` (L8); `test_derive_is_deterministic` (L11); `test_different_namespaces_produce_different_seeds` (L17); `test_different_master_seeds_produce_different_children` (L22); `test_derived_seed_is_positive` (L28); `test_get_rng_is_deterministic` (L36); `test_get_numpy_rng_is_deterministic` (L43); `test_to_dict` (L52); `test_repr` (L58).

## [tests/test_smoke.py](../../../tests/test_smoke.py)

99 dòng; SHA256 `808df772641fdb7a3699e4d1a916c89bdb8061ab8e144212798f6089e0622316`.

End-to-end smoke test for the RepGuard pipeline.

Định nghĩa: `TestSmokeEndToEnd` (L23); `test_full_pipeline_smoke` (L26); `test_runner_smoke` (L65); `test_reproducibility` (L76); `test_metrics_computation` (L90).

## [tests/test_splits.py](../../../tests/test_splits.py)

92 dòng; SHA256 `f94d4b1ef246b598aaa202003b5b1e770bd135744feb825bdf925a5fe3c68beb`.

Tests for deterministic data splitting and leakage verification.

Định nghĩa: `TestCreateSplits` (L12); `test_splits_are_exhaustive` (L15); `test_splits_are_disjoint` (L22); `test_splits_are_deterministic` (L29); `test_different_seeds_produce_different_splits` (L39); `test_approximate_ratios` (L50); `test_online_views_have_no_gt` (L65); `test_empty_records_raises` (L73); `test_invalid_ratios_raise` (L79); `test_subject_distribution` (L85).

## [thesis_pilot/__init__.py](../../../thesis_pilot/__init__.py)

1 dòng; SHA256 `9881d03ad187ac1bb372f86bed2e9b8647661a29275251058e9157aac7f6841f`.

Real, isolated RepGuard graduation-project development pilot.

## [thesis_pilot/analysis.py](../../../thesis_pilot/analysis.py)

217 dòng; SHA256 `24acab637c227fa6ad5011a5ee0137e3d67dadf8eefcbd0ffc43da2c9cf3c739`.

Evaluator-only supervised reputation and controlled real-output policy replay.

Định nghĩa: `reputation` (L10); `terms` (L18); `vector` (L24); `fit_model` (L36); `loss` (L45); `predict` (L66); `question_bootstrap` (L72); `analyze` (L80); `features` (L106); `choose` (L141).

## [thesis_pilot/audit.py](../../../thesis_pilot/audit.py)

83 dòng; SHA256 `5e62e72ab94b2d6f8f3000b225af95b256dda9d715e153c81be728518b7e9813`.

Additional correctness audits after frozen real-model evaluation.

Định nghĩa: `main` (L15).

## [thesis_pilot/backbone_probe.py](../../../thesis_pilot/backbone_probe.py)

96 dòng; SHA256 `01ad0bdb662ca77ce563a3575bc7f0497e9f6400aa95c55dfc8bef866fb5cd6b`.

Two natural backbones on16 reserved DEVELOPMENT reports, no final holdout.

Định nghĩa: `prepare` (L18); `collect` (L53); `analyze` (L73).

## [thesis_pilot/backbone_probe_app.py](../../../thesis_pilot/backbone_probe_app.py)

50 dòng; SHA256 `8b01c910f79674334e3dd4576ad91ddf381751b815b128ae130d416ac36302f8`.

A second isolated research app; reuse pinned weights read-only, no old app.

Định nghĩa: `BackboneProbeOllama` (L9); `start` (L11); `stop` (L27); `solve` (L30).

## [thesis_pilot/causal_study.py](../../../thesis_pilot/causal_study.py)

185 dòng; SHA256 `9a11ddc01044d20cbd14d324c3bb3d8772c4c06c5bbc5d666c324553605bb0f9`.

Preregister, collect real causal probes, then a bounded fresh repair study.

Định nghĩa: `prepare` (L17); `collect` (L77); `request` (L83); `report` (L115); `key` (L160); `choose` (L169).

## [thesis_pilot/causal_tools.py](../../../thesis_pilot/causal_tools.py)

104 dòng; SHA256 `35a1f243aafb9b090a553d85c836acf646c27df7f052a155059ffdf4c7183e27`.

Gold-free multi-step reference DSL and constrained repair interventions.

Định nghĩa: `messages` (L33); `refs` (L55); `edit_allowed` (L58); `verify` (L71).

## [thesis_pilot/cli.py](../../../thesis_pilot/cli.py)

137 dòng; SHA256 `dfe207b85d980ca06cdb5520b0723ecc2ae4d1f57b02ef6f6def079137263d6d`.

Prepare, submit, inspect, fetch and independently verify the REAL pilot.

Định nghĩa: `read` (L20); `prepare` (L23); `near` (L68); `report` (L80); `main` (L114).

## [thesis_pilot/competence_probe.py](../../../thesis_pilot/competence_probe.py)

61 dòng; SHA256 `59c76d61173688761f063154281cec42bfadc9227d01a29345a0156f647a2b19`.

Native-thinking competence check on eight already-seen HISTORY items only.

Định nghĩa: `main` (L15).

## [thesis_pilot/competence_tools.py](../../../thesis_pilot/competence_tools.py)

43 dòng; SHA256 `292b13d8f141124b8880cb0e3f6abdc3f3e3d2975f79785c04fddd442350104d`.

Gold-free competence control: same public input, native thinking, two contracts.

Định nghĩa: `messages` (L11); `verify` (L32).

## [thesis_pilot/composition_app.py](../../../thesis_pilot/composition_app.py)

51 dòng; SHA256 `db8d62b2ff2873d37540404487a7c7e18991cc5663c6a3f6e3b1f2526776c75d`.

Add a bounded class to the authorized NEW research app; preserve old class.

Định nghĩa: `CompositionOllama` (L8); `start` (L10); `stop` (L29); `refine` (L32).

## [thesis_pilot/composition_study.py](../../../thesis_pilot/composition_study.py)

145 dòng; SHA256 `8a4b7451f3f7c4067c40e367467d0871b54abc78728fe439c2f7824ba1e3b679`.

Frozen exploratory comparison: all24 existing reports,72 new real responses.

Định nghĩa: `parents` (L22); `prepare` (L38); `collect` (L67); `analyze` (L97); `cost` (L101).

## [thesis_pilot/composition_tools.py](../../../thesis_pilot/composition_tools.py)

58 dòng; SHA256 `9fe65805d8b6c2daa69788044a10fe2aa598737eae063f1cdac78b94c7a252ab`.

Cycle 2: source-grounded reconciliation versus iterative single-agent review.

Định nghĩa: `canonical` (L24); `candidate` (L45); `messages` (L50).

## [thesis_pilot/contract_repair.py](../../../thesis_pilot/contract_repair.py)

64 dòng; SHA256 `f3ed7241fd2e3e6eb12a52f6c432fdd201ee1229f16ad2ab5b23abdfcd57a03c`.

Real, bounded history-only validation of explicit output-contract repair.

Định nghĩa: `main` (L14).

## [thesis_pilot/core.py](../../../thesis_pilot/core.py)

215 dòng; SHA256 `f72180eb8284e1bd232f593fbc2ef85d5606c5661b27300ce275469f5d8c8b99`.

Gold-free, source-bound arithmetic contract shared by collection and serving.

Định nghĩa: `digest` (L55); `normalized` (L60); `visible_record` (L64); `source_map` (L71); `prompt` (L82); `number` (L95); `skill` (L112); `verify` (L123); `base_features` (L196); `correct` (L208).

## [thesis_pilot/diagnostic.py](../../../thesis_pilot/diagnostic.py)

69 dòng; SHA256 `20e5fe6061000a20f67172e0185e2f8be2360772007ad93ce25311c37c52b491`.

Bounded HISTORY-only real diagnostic; never alters the completed v2 pilot.

Định nghĩa: `main` (L14).

## [thesis_pilot/live_app.py](../../../thesis_pilot/live_app.py)

166 dòng; SHA256 `e71724c400a08534f5dfb35746fedbe826ed7a79ba642101af6f809fdb53c968`.

Private live-inference backend on the NEW app, deployed after the pilot finishes.

Định nghĩa: `LiveOllama` (L8); `pot_solve` (L10); `competence_solve` (L31); `causal_solve` (L52); `start` (L76); `stop` (L96); `solve` (L100); `typed_solve` (L145).

## [thesis_pilot/live_cli.py](../../../thesis_pilot/live_cli.py)

85 dòng; SHA256 `f4a49a0942a3d586a46bb07f4d3c23b5e56a67f413e0daff7320dfe9ef88e706`.

A real prototype: source-grounded answers with history-aware delegation.

Định nghĩa: `run` (L22); `probability` (L44); `invoke` (L50).

## [thesis_pilot/modal_app.py](../../../thesis_pilot/modal_app.py)

184 dòng; SHA256 `cc8ad9bc4268bcc2e54c14887d43c3362a6f3a42bd5f0a6a27c36b44c6488d4c`.

An isolated Modal application; never imports or calls the existing Ollama apps.

Định nghĩa: `download_models` (L21); `inspect_models` (L64); `collect_inference` (L81); `request` (L110); `worker` (L134); `inspect_run` (L169).

## [thesis_pilot/modern_direct_app.py](../../../thesis_pilot/modern_direct_app.py)

50 dòng; SHA256 `34ceabbf25c505b1fecfcb5b3b74c678edfdfd783f339f615e13551a314a36d3`.

Post-hoc whole-cohort reasoning-mode adequacy control. Preserve native API.

Định nghĩa: `ModernDirectOllama` (L7); `start` (L9); `stop` (L25); `solve` (L28).

## [thesis_pilot/modern_direct_control.py](../../../thesis_pilot/modern_direct_control.py)

78 dòng; SHA256 `6e2202df2bb67a723323e648c50ec9940328364ebb3aacb363583bb0f7381c1a`.

ALL16case no-native-thinking control, triggered by native4096truncations.

Định nghĩa: `prepare` (L21); `collect` (L41); `analyze` (L59).

## [thesis_pilot/modern_probe.py](../../../thesis_pilot/modern_probe.py)

95 dòng; SHA256 `bdafccb3f358858e0ac7a561bfe67d0d4b1b8593a1d36487b07cce1e6463ec9d`.

One contemporary baseline on ALL16 frozen backbone-development cases.

Định nghĩa: `download` (L21); `prepare` (L29); `collect` (L51); `analyze` (L68).

## [thesis_pilot/modern_probe_app.py](../../../thesis_pilot/modern_probe_app.py)

76 dòng; SHA256 `52c76b89c2b02523c97ec9804a10aeb910b0598cd3553adfe5ae0e60fda0ed2a`.

One modern backbone control on a third isolated research app/volume.

Định nghĩa: `ModernBackboneOllama` (L10); `start` (L12); `stop` (L28); `solve` (L31); `download_modern_model` (L55).

## [thesis_pilot/pipeline.py](../../../thesis_pilot/pipeline.py)

135 dòng; SHA256 `43457c9c9ecc83728b2130f57d7dd637d4c166a59bf03694cc717c7c83a1a669`.

Real Ollama collection with durable per-request receipts and no gold access.

Định nghĩa: `atomic` (L8); `save` (L15); `validate` (L20); `verify_visible` (L25); `jobs` (L42); `collect` (L48); `load_responses` (L124).

## [thesis_pilot/pot_probe.py](../../../thesis_pilot/pot_probe.py)

61 dòng; SHA256 `bfac225cd03db46c136a946e39b093834d84942514b35b61c4dbff45d3d37434`.

A standard-form arithmetic-program control on all24 existing development cases.

Định nghĩa: `main` (L15).

## [thesis_pilot/pot_tools.py](../../../thesis_pilot/pot_tools.py)

107 dòng; SHA256 `bff6a606df267ecec0aad26b750df8a0ba9e13589122df9ef4d473dc7e55744d`.

Straight-line arithmetic Python control, inspired by standard PoT/PAL.

Định nghĩa: `messages` (L31); `execute` (L36); `safe` (L43); `ev` (L47); `e` (L49); `verify` (L99).

## [thesis_pilot/program_integrity_v2.py](../../../thesis_pilot/program_integrity_v2.py)

38 dòng; SHA256 `cb5748e9e3daac9e1593ab37dff485fbf16f94f9b374566ad72fb610b36e67ca`.

Source-dependency checks for future versions, independent of target labels.

Định nghĩa: `inspect_program` (L7); `visit_arg` (L15); `visit_step` (L23).

## [thesis_pilot/quantity_parser_v2.py](../../../thesis_pilot/quantity_parser_v2.py)

26 dòng; SHA256 `8b78e34f3db683c2cbec72ffd56ff87d00e583ae82cd4ef89814558c39fb4bd3`.

Accounting percent-token fix for FUTURE studies, never retroactive v1 scoring.

Định nghĩa: `parse_quantity` (L11); `numeric_tokens` (L25).

## [thesis_pilot/serving_checks.py](../../../thesis_pilot/serving_checks.py)

17 dòng; SHA256 `a459cd5aa9c000967794c2d5bb35011789538781c41cd98a6a5a6b1f1af4f16b`.

Conservative live unit review; never changes frozen scientific scores.

Định nghĩa: `review_units` (L5).

## [thesis_pilot/source_checks.py](../../../thesis_pilot/source_checks.py)

37 dòng; SHA256 `81c7c92134fd1ffff7e0745ef3191480fa1a117c76c70137621c46c64c297b06`.

Additional mechanical token-boundary audit, separate from the frozen pilot.

Định nghĩa: `numeric_binding_errors` (L13); `strict_verify` (L31).

## [thesis_pilot/tatqa_crossfamily_app.py](../../../thesis_pilot/tatqa_crossfamily_app.py)

45 dòng; SHA256 `6c7ed103ae44649399ac0f00d8244632fe7cf742630f4bbf08aac13738262b49`.

Fourth isolated research app and weights volume; never user's original app.

Định nghĩa: `TatqaGemmaOllama` (L11); `start` (L13); `stop` (L17); `solve` (L19); `download_gemma` (L24).

## [thesis_pilot/tatqa_crossfamily_study.py](../../../thesis_pilot/tatqa_crossfamily_study.py)

138 dòng; SHA256 `f05e690712a9dcd69815350e43f192eb8648f9326a0a85f7ba24e90f65fd6d5e`.

Post-hoc capability and cross-family control; scopes' primary results preserved.

Định nghĩa: `read` (L20); `sha` (L21); `prepare` (L22); `path` (L55); `parent` (L56); `collect` (L57); `replay` (L91); `analyze` (L104).

## [thesis_pilot/tatqa_plain_review_app.py](../../../thesis_pilot/tatqa_plain_review_app.py)

17 dòng; SHA256 `08ebbd00479e964727c1f8b7bcb845f236f8ef45e7f312894d28aeca6448b3f6`.

Deploy only AFTER the frozen scoped study has completed.

Định nghĩa: `TatqaPlainReviewOllama` (L7); `start` (L9); `stop` (L13); `solve` (L15).

## [thesis_pilot/tatqa_plain_tools.py](../../../thesis_pilot/tatqa_plain_tools.py)

51 dòng; SHA256 `9eb3a49d8acd541a63bdbb9e1131d6802c13daee3c8c514a24c7ffbb15e06b39`.

Unrestricted PoT review capability control shared across model families.

Định nghĩa: `messages` (L12); `start_server` (L20); `solve_request` (L35).

## [thesis_pilot/tatqa_scope_app.py](../../../thesis_pilot/tatqa_scope_app.py)

47 dòng; SHA256 `8271dca51d3387bd19159a5f7cb2aac3e35c7dc476046d117b5ad8610116d330`.

New API on the isolated modern research app; previous modules stay frozen.

Định nghĩa: `TatqaScopeOllama` (L7); `start` (L9); `stop` (L25); `solve` (L28).

## [thesis_pilot/tatqa_scope_study.py](../../../thesis_pilot/tatqa_scope_study.py)

156 dòng; SHA256 `bbce814ffa021a984f5bdbbdba9b15a5157df2061bcd0ecdbc0fde7d8c6b934e`.

Frozen 24-context real-inference mechanism pilot; not a reputation result.

Định nghĩa: `read` (L21); `sha` (L22); `prepare` (L23); `path` (L56); `collect` (L57); `replay` (L96); `analyze` (L105).

## [thesis_pilot/tatqa_scope_tools.py](../../../thesis_pilot/tatqa_scope_tools.py)

158 dòng; SHA256 `93e0045c7897ef050db5782f1577351a5d4cc33db2b66ea3a65a298262665072`.

Source/operation interventions. No annotations or semantic-oracle acceptance.

Định nghĩa: `catalogue` (L64); `add` (L67); `messages` (L84); `verify` (L99); `incumbent` (L133); `scope_ok` (L136); `bs` (L139); `accept` (L150); `combined` (L153).

## [thesis_pilot/thinking_probe.py](../../../thesis_pilot/thinking_probe.py)

60 dòng; SHA256 `417dd2488b28a74cd4bfa0ea50d10bf29eb4bba10021e6d5e3e1c020da0a71c6`.

Eight real HISTORY calls for typed-tool feasibility, not confirmation.

Định nghĩa: `main` (L15).

## [thesis_pilot/typed_probe.py](../../../thesis_pilot/typed_probe.py)

59 dòng; SHA256 `17e56f4dda3b2a1fddae709a559a32d316c8316bcf92b3682d01dbb59cb32543`.

Eight real HISTORY calls for typed-tool feasibility, not confirmation.

Định nghĩa: `main` (L15).

## [thesis_pilot/typed_tools.py](../../../thesis_pilot/typed_tools.py)

108 dòng; SHA256 `fa0e4c79f84d181d2c2db8b270a2bfda8a2f5a80206f099e2a84efd750131872`.

Source-catalogue selection + typed financial operations. No evaluator/gold.

Định nghĩa: `catalogue` (L37); `messages` (L60); `verify` (L70).

## [thesis_pilot/verify_delivery.py](../../../thesis_pilot/verify_delivery.py)

82 dòng; SHA256 `83dad9340e563da8e9c5782a7f5efc1633bb50253b3d16520c4e6dba53e0b7a8`.

Independent artifact verification, no model calls or generated solver outputs.

Định nghĩa: `read` (L11).

## [thesis_pilot/web_demo.py](../../../thesis_pilot/web_demo.py)

84 dòng; SHA256 `a94fcc09bb1105f1e938311bfc2dd8fadc118e335e41b6086485d9854c7031a6`.

Local browser prototype. Every submitted question invokes live Modal models.

Định nghĩa: `Handler` (L17); `log_message` (L18); `send` (L22); `do_GET` (L31); `do_POST` (L42); `execute` (L69).

## [verify_dart_factor.py](../../../verify_dart_factor.py)

54 dòng; SHA256 `66f6c15ffe7de8ace80b7d3633894214309c006f611226ba52d0d69aad92e2de`.

Fast independent recomputation of the predeclared structured baseline only.

Định nghĩa: `main` (L18).
