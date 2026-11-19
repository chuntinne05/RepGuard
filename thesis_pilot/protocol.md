# RepGuard real thesis pilot v2 — arithmetic repair, frozen before v2 task inference

V1 run ca72380557dad9ef0769a382 was cancelled after real history-case calls,
before fitting or screen analysis. Its executor incorrectly rounded intermediate
steps. Preserve its source/packet/receipts/raw responses. V2 keeps the exact same
metadata-selected100questions, agents, caps, partitions, policy protocol and
controls, changes ONLY prompt/executor to round the FINAL result. V2 does not
reuse v1 solver responses. No screen target was inspected to select this fix.

This is a development feasibility experiment, not final confirmation. No mock
provider, synthetic solver answer, LLM-generated gold or substituted archived
solver outcome is permitted. Use a NEW Modal app and NEW model/response/evaluation
volumes, never the existing deployed Ollama app or its model volume.

FinQA official TRAIN at revision 0f16e2867befa6840783e58be38c9efb9229d742,
SHA256 49f237eb9779b569473b26b08048867d04635a7cc39ad6a7a5664c55bb428db6.
Choose one question per company/year report by SHA256, excluding duplicate
normalized questions and hashes in the previously exposed FinQA headroom200.
Selection uses ONLY ID/report/question metadata, no program, answer or score.
Freeze 100 reports: first60 history, next10 calibration, next10 validation,
last20 DEVELOPMENT SCREEN. No MMLU sealed or AppWorld challenge access.

GPU gets ONLY allowlisted table/pre_text/post_text/question plus identity and
protocol metadata. CPU evaluator gets qa.exe_ans separately; GPU does not mount
the evaluation volume. Do not pass gold retrieval or qa.model_input to a solver.

Two fixed agents: A=qwen3:8b, direct source-bound arithmetic program,896 output
tokens; B=qwen3:14b, careful source-bound arithmetic program,1536 output tokens.
Both think=false, temperature0, seed18102026, num_ctx16384, same JSON schema.
Freeze actual downloaded digests and Ollama0.40.6 before task calls. Use oneL4
container, one inference at a time, no provisioned idle GPU. Two attempts maximum
per request ONLY on transport/unknown failures; NEVER retry valid-but-wrong,
abstained, schema-invalid or length-capped completed answers to improve scores.
200 base task calls total; fixed8-call technical gate uses history cases only,
no gold: at least6 structured JSON and at least1 source-bound executable answer.
Record actual nvidia-smi and model VRAM evidence; stop if inference falls to CPU.
Collection wall cap6600seconds and GPU-function timeout7200seconds; no automatic
larger study or new-model search after finishing. Downloads run on CPU.

Use FinQA executor numerical convention: percentages as fractions, keep full
precision in intermediate operations, round final value to5decimals;
compare qa.exe_ans at5decimals, yes/no exactly.
No factor100 oracle matching. This is answer execution scoring, NOT symbolic
program accuracy. Source consistency is NOT semantic correctness; report both.
All100 selected questions retained, including unsupported/boolean tasks. Gold
disagreements/annotation ambiguity get a separate audit, not outcome replacement.

Train real L2 logistic risk models using history solver correctness, with/without
reputation features. History features are report-out-of-fold; current question
gold never enters its own features. Reputation includes global and skill Beta
means and TFIDF-neighbor history competence. Both learners share model×skill
interactions and current verifier features. Fit separate logistic calibration on
10calibration questions; threshold search ONLY10validation questions over
[.2,.35,.5,.65,.8], maximizing accuracy−.05×tokens/AlwaysBtokens. Freeze then
evaluate once on20screen questions. Full supervised history labels are counted;
this is NOT a10%audit experiment. No online update from screen labels.

Controls: AlwaysA, AlwaysB, full-history GlobalGold and SkillGold, raw mechanical
feedback Skill, hard-check FixedCascade, learned EvidenceOnly, learned RepGuard.
At serving time a cascade initially sees A only; calling B costs A+B. Cached
counterfactual responses may be replayed after real collection, but no uncalled
output is exposed to the policy. Report collection cost separately from serving
simulation. Do not call response replay additional live model execution.

Primary contrasts RepGuard vs AlwaysB, FixedCascade, EvidenceOnly, SkillGold:
all-question accuracy (abstentions fail), rescue/harm, token cost, model calls.
Secondary approved coverage/precision, wrong approvals, recorded request time.
2000paired question bootstrap draws, seed18102026; all reports unique. Intervals
exploratory and not adjusted for prior research. Small screen cannot establish
SOTA/safety/noninferiority or promise thesis grades. Descriptive pilot signal
requires accuracy>=both EvidenceOnly and FixedCascade and either strict accuracy
gain over both or >=10%token saving vs both. Report FAIL unchanged; no choice of
new threshold, subset, metric or model after screen outcomes.

Persist raw real responses, attempt intents, prompt/model/source hashes, usage,
grounded arithmetic traces, optimizer loss, choices, checkpoints and status.
Verify checksums and recompute policies locally after completion. Report output
tokens, latency and GPU wall metadata separately; absent billing is not USD0.
