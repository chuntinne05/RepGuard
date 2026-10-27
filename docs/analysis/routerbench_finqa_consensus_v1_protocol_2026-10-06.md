# FinQA exact-answer consensus proxy: frozen development replay v1

## Status and parentage

This is a **new, exploratory development diagnostic** designed after the
negative Qwen3-14B judge pilot `0fad63edd346eb0591fd99e1`. That pilot and
its FAIL gate remain unchanged. A post-hoc check on its 48 questions suggested
that exact answer agreement might carry within-question model information;
the old 48 questions are excluded here. This study is **not** an independent
confirmation or a contextual router experiment.

Use the fixed FinQA 20-model pool and 200 development question IDs from the
verified gold-only headroom run `58bcf5179974f10ebe94c405`. Remove all 48
judge-pilot IDs. Rank the remaining 152 IDs by
SHA256(`repguard-finqa-consensus-v1:` + ID) and take first 48. Do not rank by
score, model answer, agreement or pilot outcome. Freeze exact archive member
and record positions per model in an input packet before Modal execution.
These 48 were not used in the judge-pilot diagnosis, though their scores were
part of the earlier 200-question headroom aggregate. The 938 eligible unique
FinQA questions outside that 200-question development selection remain
untouched by this worker.

## Proxy and access boundary

CPU worker verifies the pinned archive SHA256. In its first archive pass it
reads **only** `origin_query` and `prediction` at the 48×20 selected record
positions. It validates the normalized query hash, saves the 960 prediction
strings privately and commits a `proxy_complete` checkpoint before opening any
score field. It never reads `raw_output`, ground truth or score during proxy
construction. No new solver or judge calls. The cost of the **archived** 20
model executions is not zero in any practical cost comparison.

Canonical answer = NFKC Unicode normalization, casefold, and whitespace
collapse. No numeric tolerance, unit conversion, percentage conversion or
semantic equivalence is allowed in this version. A missing/blank `prediction`
gets proxy 0 and a missing flag. For a nonempty answer from model `a` on
question `i`, proxy is the number of the **other 19 models** with the same
canonical answer, divided by 19. Self-votes are excluded. All 20 historical
outputs are available for this historical proxy, but none is available for a
new deployment question unless that model is actually run; report only global
historical model selection potential.

Only after `proxy_complete`, CPU evaluator scans the archive again, retaining
binary `score` at the same 960 preselected positions. No other scores are
stored or analyzed. It aligns score to frozen question/model order, recomputes
the proxy and fails closed on missing or changed artifacts. Raw predictions,
prompt and gold stay in ignored `results/` and Modal Volume.

## Fixed analysis and gate

Use the same 4 question folds (`index % 4`), intercept, 20 model indicators,
`p-.5`, `I(p>=.9)-.5`, per-question mean `p-.5`, and missing indicator as in
the judge pilot. Ridge penalties are 0 for intercept, 4 for model indicators,
and 1 for each proxy feature; target is `y-.5`, predictions clipped to [0,1].
Every held-out question is predicted from the other 36 questions' complete
gold **for this diagnostic only**. Gold-only control removes proxy features.
Report raw proxy and cross-fit Brier, gold-only Brier, 190-pair residual
variance ratio and the question-bootstrap CI (2,000 resamples, seed 1404,
fixed fitted predictions), answer coverage, and descriptive ranking/oracle
references. No sparse-gold or cost-saving claim follows from this full-gold
cross-fit diagnostic.

Operational criterion: >=90% nonempty parsed predictions. Expansion screen:
operational criterion AND pair residual variance ratio <=0.90 AND upper 95%
question-bootstrap bound <1. This is a development screen, not confirmatory
inference. Stop after this 48×20 matrix whether PASS or FAIL. If PASS, lock a
separate equal-gold-budget replay including gold-only, judge-only, consensus,
adaptive audit and strong proxy-aware controls. If FAIL, report the negative
result; do not tune normalization or select a favorable model subset on these
48 questions and relabel that result as preregistered.

This exact-string proxy is relevant only when model outputs contain a
comparable final answer. Extending it to code, free text or agent trajectories
would require a different verifier and new evaluation. It does not by itself
establish DART superiority or A* publication potential.
