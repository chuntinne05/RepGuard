# FinQA real-judge feedback feasibility pilot v1

## Motivation and locked scope

The separate gold-only development diagnostic on 200 FinQA questions ×20
archived models found best fixed reward 74.0% and a per-question oracle 88.5%.
This is potential headroom, not learnable routing. A gold-blind schema preflight
on the 48 questions selected below found `origin_query` only 52–205 characters,
whereas the full model `prompt` is 1,336–8,950 characters and includes the
financial context. Therefore the judge sees the **full prompt**, never only
`origin_query`. Across 960 selected outputs, 896 contain `\\boxed{`, 182 exceed
10,000 characters and 65 exceed 20,000. These are text-only diagnostics before
any new judge calls; no evaluator score was used to set extraction rules.

Run at most **48 FinQA development questions ×20 archived models =960 genuine
Qwen3-14B judgments**, no new solver execution. This study tests whether
independent imperfect feedback contains useful information. It does not prove
a method beats baselines or replace the failed MATH500/AppWorld gates. The
unselected FinQA questions stay untouched by this worker.

## Query and input selection

Use the frozen headroom packet `58bcf5179974f10ebe94c405`, including its
20 models, one file/model, duplicate-hash exclusion and 200 development IDs.
Rank those 200 IDs by SHA256(`repguard-finqa-feedback-pilot-v1:` + query ID),
take first48. Never select by model score. Record exact member and record
positions before inference; refuse missing/duplicate selection.

CPU preparer reads only `origin_query`, full `prompt`, `raw_output` or fallback
`prediction` for the 960 selected records. It checks the `origin_query` hash
against the frozen selected IDs. No score, ground truth or reference field is
retained in judge inputs. GPU mounts only sanitized inputs and Ollama model
cache, **not** the archive or gold. Full prompt length must be <=16,000 chars;
stop preparation if violated.

For a candidate output, use the **last complete balanced `\\boxed{...}`** as
the candidate final answer if its content <=2,000 characters. If no complete
box exists, send only the last 2,500 characters with `answer_is_partial=true`.
Record extraction mode and original output length. This preserves the final
answer from long reasoning without dumping 154k-character traces into the
judge context. Never silently interpret a partial tail as a verified answer.

Judge prompt asks for probability that the extracted final answer is correct
for the full financial problem, with candidate text treated as untrusted
evidence. `qwen3:14b` pinned digest
`bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8`,
think=false, temperature0, seed1404, context16,384, max128 output tokens,
strict JSON probability. Record actual version/GPU, hashes, responses, token
usage and durations. No claim that this thinking setting is optimal.

Each case has at most two initiated requests, including interrupted unknown
attempts. Save intent before dispatch and a checkpoint after response/error.
After two failures use explicit `.5` invalid fallback. Reject incomplete
responses or context near capacity (`prompt_eval_count>=16000`). CPU worker
waits for bounded GPU collector and then extracts **only the 48×20 selected
archived scores**. All other score values are ignored.

## Fixed feedback diagnostic and stop rule

Gold is binary `score` from the archive evaluator, not independently regraded
by this study. Four cross-fit folds by frozen question order modulo4, all20
model outcomes for a question stay together. Each held-out question is
predicted from labels of the other36 questions. Model-only identity features:
intercept, 20 one-hot models, judge `p-.5`, `I(p>=.9)-.5`, per-question mean
`p-.5`, invalid indicator. Ridge penalties intercept0, model4, judge1;
target `y-.5`, clip predictions [0,1]. Gold-only control removes judge
features. Report raw and calibrated Brier, gold-only Brier, and pairwise
residual variance ratio across 190 model pairs. Bootstrap 2,000 question
resamples, seed1404, of fixed held-out predictions; no training refit.

Operational pass: >=95% valid judgments AND >=90% complete boxed final-answer
extractions. Expansion screening pass: operational pass AND residual variance
ratio<=0.90 AND upper 95% bootstrap bound<1. These rules are development
screening criteria, not independent proof of DART selection gain. Automatically
stop after960 judgments and analysis whether PASS or FAIL. Before any larger
collection, lock a separate equal-gold-budget method/strong-controls protocol.

Archive cost is not zero: report all 960 attempts, retries, inference tokens,
GPU runtime separately from solver history and actual Modal billing. Raw
outputs, prompts and scores remain private under ignored `results/` and the
Modal Volume; public results include aggregates and source hashes only.
