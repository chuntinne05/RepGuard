# RepGuard real thesis pilot

The deployed application is `repguard-thesis-real-pilot-20261018`. It uses only
new volumes: `repguard-thesis-models-20261018`,
`repguard-thesis-runs-20261018`, and `repguard-thesis-evals-20261018`.
No function connects to the existing Ollama endpoints or model volume.

This package is a real, bounded development experiment. All solver outputs must
be recorded responses from Ollama on a Modal L4. There is no mock provider.
The arithmetic executor and policy replay are deterministic software, not
additional model executions. Gold is evaluator-only. The GPU never mounts the
evaluation volume. See `protocol.md` for the frozen design and limitations.

Run from the repository root with its existing Python environment:

```bash
./.venv/bin/python -m thesis_pilot.cli status
./.venv/bin/python -m thesis_pilot.cli fetch
./.venv/bin/python -m thesis_pilot.cli report
```

Raw inputs, frozen source, receipts and real responses are private under
`results/thesis_real_pilot_v2/` (Git-ignored). Aborted v1 is preserved separately.
The public report is generated
under `docs/analysis/repguard_thesis_pilot_assessment_2026-10-18.md` only after
all 200 real responses pass checksum checks and local recomputation matches
the cloud fit/evaluation. Report does not submit inference.

`submit` is guarded by the receipt; never delete it to start a duplicate or
repeat an unfavorable outcome. `prepare` verifies a preexisting packet and
rejects changed source. A new method or prompt needs a NEW protocol/run
identity and preserved prior artifacts. A scientific STOP is not a retryable
infrastructure failure.

Model downloads are CPU-only; collection uses one L4, no idle GPU, a 6600-second
collection wall limit and a 7200-second function timeout. A request may have at
most two initiated attempts after transport failure. Completed invalid answers
are not retried. Token and request-time records do not equal total USD billing.

The split is 60 history, 10 probability calibration, 10 policy validation and
20 development screen questions from 100 distinct company/year reports.
This is not final evaluation, a 10%-gold audit result, or evidence that the
method has already improved accuracy. Full history gold is available equally
to supervised methods and gold-only controls. Model×skill, current mechanical
evidence, and optional out-of-fold history competence features are compared.

Serving-cost comparisons replay only permitted responses; an A→B decision
costs both calls. The 200-counterfactual-call data acquisition cost must also
be reported. No test gold, unseen solver output, or future feedback is allowed
when a policy decides. Source consistency does not establish semantic truth.

## Real browser prototype

After completing and verifying the pilot, deploy the live class on the same NEW
app (do not deploy while the collector is running):

```bash
./.venv/bin/modal deploy thesis_pilot/live_app.py
./.venv/bin/python -m thesis_pilot.web_demo
```

Open `http://127.0.0.1:8765`. Each click invokes actual Modal Ollama inference;
there is no cached-answer fallback. The page displays the model, input/output
tokens, source references, arithmetic program and complete response traces.
It supports the frozen RepGuard policy and either single-agent control. Live
artifacts are saved under `results/thesis_live_prototype/`.

A repeat on a pilot document is an integration demonstration, not independent
scientific evaluation. You can edit its question. For a separate document,
provide a gold-free JSON with keys `id/report/question/table/pre_text/post_text`:

```bash
./.venv/bin/python -m thesis_pilot.live_cli --document /absolute/path/report.json
```

The policy's competence features use audited HISTORY only. The GPU live class
mounts only the new model volume, never the evaluation volume. Its additional
numeric sign/percent boundary checks are a disclosed serving refinement and are
audited separately; they do not rewrite frozen pilot results. Probability
estimates come from a small development pilot and do not guarantee correctness.

`python -m thesis_pilot.audit` adds a post-evaluation audit of official arithmetic,
numeric-source boundaries and the difference between candidate accuracy and
automatically approved resolution.

`python -m thesis_pilot.diagnostic` performs at most16 additional real calls,
on the first8 HISTORY questions only, to diagnose over-abstention. Its plan and
raw outputs are separate under `results/thesis_contract_diagnostic_v1/`; see
the corresponding protocol in `docs/analysis/`. It does not alter v2 or apply
the old calibrator to a new output contract.

The second, separate16-call history check is `python -m thesis_pilot.contract_repair`.
Its results preserve failed source selection/unit handling. A live percentage
double-scaling failure is retained and reviewed under `serving_checks.py`; the
new guard requests review instead of silently fixing a generated answer.

The next prototype branch uses `typed_tools.py`: the model selects numeric
catalogue references and one typed operation, while software controls arithmetic
and percent display. Its bounded8-call history probe is
`python -m thesis_pilot.typed_probe`. It is a single-B baseline, with no fitted
reputation/calibrator; it is not a reputation improvement claim. The browser
option is “B + công cụ tính có kiểu (chưa hiệu chỉnh)”. Or run:

```bash
./.venv/bin/python -m thesis_pilot.live_cli --mode always_b --contract typed_tools
```

This typed branch does not load history gold or a fitted v2 policy. With a custom
document it does not require the pilot input packet. Multi-stage questions
outside the fixed templates remain unsupported and count as failures in the
history probe. A fresh set of reports and fitting are required before claiming
generalization or a reputation benefit for a new contract.

The final small development diagnostic, `python -m thesis_pilot.thinking_probe`,
uses the same8 history cases with native thinking enabled and4096 output tokens.
This compares configurations with different output budgets. Its own plan,
snapshot and raw responses are under `results/thesis_typed_thinking_probe_v1/`;
it does not change the v2 pilot, fit a reputation model or claim a final result.

After all bounded runs complete, `python -m thesis_pilot.verify_delivery` verifies
the200 primary response checksums, every48 follow-up response against the actual
executor, frozen source ZIP hashes, native-thinking message parity, and the live
demo arithmetic. It makes NO inference/network calls. The public verification
record is `docs/analysis/repguard_delivery_verification_2026-10-18.json`.

## Method research cycle 1 (18 October 2026)

The next research cycle uses the same private NEW Modal app and pinned14B
weights; it never invokes an old Ollama deployment. Its separate artifacts are:

- `results/thesis_causal_repair_v1/`:112 real responses, including24 new reports
  with initial/self/evidence/plan programs. All four yield6/24; raw oracle union
  is6. Do not train an action selector to claim an accuracy gain on these outputs.
- `results/thesis_competence_probe_v1/`:24 native-thinking diagnostics on8
  repeatedly seen HISTORY questions, not an independent evaluation.
- `results/thesis_pot_control_v1/`:24 additional arithmetic-Python controls on
  all24 development cases, a familiar-program baseline rather than a new method.

Each has its own plan, raw outputs and frozen source ZIP. Updates to
`live_app.py` were deployed only after the preceding collector finished.
The seven original pilot source files remain unchanged. Prior snapshots, failed
answers and strict scores must remain available; do not rewrite them using a new
parser or unit convention. The total ceiling for these three inference batches
is160 calls. Corpus selection, model costs and validity limits are in the dated
protocols under `docs/analysis/`.

`quantity_parser_v2.py` and `program_integrity_v2.py` contain future-study fixes
for accounting percentages and evidence dependency. They are not retroactively
activated in the frozen studies and do not themselves prove a stronger solver.

After complete collection, the following are LOCAL analysis/verification calls,
not model requests (run from the repository root):

```bash
./.venv/bin/python docs/analysis/repguard_paired_history_probe.py analyze
./.venv/bin/python docs/analysis/repguard_pot_format_control.py
./.venv/bin/python docs/analysis/repguard_pot_readout_control.py
./.venv/bin/python docs/analysis/verify_research_cycle_01.py
./.venv/bin/python docs/analysis/build_research_cycle_01_report.py
```

The paired-history analysis uses real counterfactual responses and supervised
report-separated OOF fitting only when its gate passes. Its pre-analysis plan
was fixed before inspecting PoT outputs, after seeing cheap development outcomes;
it is exploratory, not an independent or10%-audit result. Serving cost replay is
separate from the160 collection calls. Measured Ollama evaluation seconds are a
compute proxy, not USD billing or an end-to-end deployed-policy benchmark.

The formatting control uniformly removes unnecessary leading whitespace from
straight-line Python, without changing numbers/operators. Its secondary scores
remain separate from the strict original PoT scores; compiler/formatting gains
must not be credited to reputation. A separate readout control accepts a final
bare variable expression when no `answer` assignment exists. It does not change
arithmetic. Strict14/24, whitespace16/24 and final-readout17/24 remain separate.
With the same controls, local history also reaches17/24 while using a measured
compute proxy13.6% higher than direct PoT on this development sample. No confirmed
reputation advantage has been established. The main report is
`docs/analysis/repguard_research_cycle_01_2026-10-18.md`.


## Research cycle2 (2026-10-19)

136 new REAL responses; no mock solver or quality retries.24previously seen
reports support72new self-review/composition calls;16new LIVE-cohort report
groups support32backbone calls plus16native27B and16post-hoc no-native-thinking
calls. Do not count136responses as136independent tasks.

- `thesis_composition_cycle_02`: direct/self1/self2=17/24; compose16/24,
  zero rescue/one harm, union17. GateFAIL; no new history learner.
- `thesis_backbone_diversity_probe_v1`:8B/14B=11/16with identical correctness;
  oracle union11. GateFAIL.
- `thesis_modern_backbone_control_v1`: Qwen3.5 27B native4096=11/16,
 4length stops. This does not establish a model-capacity limit.
- `thesis_modern_direct_control_v1`: SAME16cases/model/prompt/cap with
  `think=False`, a separate post-hoc adequacy control;13/16,15valid,0length
  stops,0native-thinking outputs, mean11.067 Ollama evaluation seconds.
  No native response or primary score was replaced. Not independent confirmation.

Original research app: `repguard-thesis-real-pilot-20261018` (L4).
Two additional isolated apps: `repguard-thesis-backbone-probe-20261019` (L4)
and `repguard-thesis-modern-backbone-20261019` (L40S). The last uses a NEW volume
`repguard-thesis-modern-models-20261019`; the original weights manifest remains
unchanged. All three were observed with zero containers after collection.

Modern pinned digest:
`64ae5b1d651fb2709d5928ccb8dcfb4bb2cc9c2c8001ac34497e36a6cf905b59`.
The added `ModernDirectOllama` class provides a real private Modal RPC solver;
it accepts only the same6public case fields and has no evaluation-volume mount.
Do not reuse historical calibration across model/prompt/contract changes.

Recompute from SAVED responses, without inference:

```bash
./.venv/bin/python -m thesis_pilot.composition_study analyze
./.venv/bin/python -m thesis_pilot.backbone_probe analyze
./.venv/bin/python -m thesis_pilot.modern_probe analyze
./.venv/bin/python -m thesis_pilot.modern_direct_control analyze
./.venv/bin/python docs/analysis/verify_composition_cycle02.py
./.venv/bin/python docs/analysis/verify_backbone_probe.py
./.venv/bin/python docs/analysis/verify_modern_probe.py
./.venv/bin/python docs/analysis/verify_modern_direct_control.py
```

Each run directory holds its frozen plan, registration, source ZIP and real
responses. Archived source files must remain unchanged for these verifiers.
The7primary pilot files are still unchanged. Paired bootstrap comparisons and
GPU-rate runtime proxies are exploratory; they do not prove non-inferiority,
production latency, billing savings, or true semantic correctness of targets.

Main report: `docs/analysis/repguard_research_decision_2026-10-19.md`.
Research gap/candidate status: `repguard_research_gap_2026-10-19.md` and
`repguard_method_candidate_2026-10-19.md` in the same directory.
Source-only blind-review packets cover40cases;0human reviews completed.
TAT-QA64TRAINcontexts and the original evaluator are prepared and software
checked, but no TAT-QA solver calls/score have been produced.


## Completed cycle3 (2026-10-20)

264 NEW real responses on24 TAT-QA TRAIN contexts: scoped144 and separate
plain-review/cross-family120. The latter reuses24 real Qwen direct outputs,
with their cost included in workflow comparisons. Both studies audit PASS;
zero mocks/unresolved/length stops in these runs. No reputation advantage or
new history learner. See docs/analysis/repguard_research_decision_2026-10-20.md.

Frozen modules: tatqa_scope_tools/app/study and tatqa_plain_tools,
tatqa_plain_review_app, tatqa_crossfamily_app/study. Preserve all registered
hashes. Results: results/thesis_tatqa_scoped_repair_v1 and
results/thesis_tatqa_crossfamily_v1. Prepare rejects source drift; analyze uses
the pinned ORIGINAL TAT-QA evaluator (SciPy isolated at
/tmp/repguard_tatqa_eval_deps). Gold/scale annotations never enter prompts.

New Gemma app: repguard-thesis-crossfamily-20261020, separate weights volume
repguard-thesis-gemma4-models-20261020. Full digest:
5571076f3d70050487b26b341705799e0ab29b808164f90d20d4cf84f699d251.
Ollama0.40.6, Q4_K_M, L40S, non-thinking, greedy0, seed20102026,4096 cap.
Previous model APIs and primary sources preserved. All four research apps
observed at zero containers after collection; original user app untouched.

Read-only audits, run from repository root:

```bash
.venv/bin/python docs/analysis/verify_tatqa_scope_cycle03.py
.venv/bin/python docs/analysis/verify_tatqa_crossfamily_cycle03.py
```

Count rewrite, inert-unit metadata pruning and component-fallback replay are
explicit POST-HOC diagnostics over real outputs; no new model calls, no rewrite
of primary scores, no simulated new review contexts. Do not call them method wins.

EvalPlus/MBPP+ source preparation is separate and has ZERO model calls/program
executions. Its32 development tasks are not a confirmed independent test split;
archive MBPP overlap remains unmapped. Use the public packet WITH input-domain
constraints and an isolated official checker before a new locked model study.
