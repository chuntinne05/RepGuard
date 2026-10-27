# Prompt-only grouping of the 500 common MATH500 questions

This frozen preprocessing step uses the pinned LLMRouterBench archive
`b79f8cde1a6f029c2efa663a3a3b6f7748defb22341fe59f328cebef6648c8f1`.
Read only `origin_query` or `prompt` from the single archived Qwen3-8B MATH500/test
member already selected in the pilot inventory. Verify all 500 query hashes and
the archive digest before grouping. Do not retain or use prediction, output,
reference, score, evaluator fields, or MMLU files. The worker is CPU-only.

Query identity is the pilot's NFKC/casefold/whitespace SHA256. Fail on missing,
duplicate, extra, or mismatched query hashes. Exact duplicates are thus already
collapsed in the 500-hash inventory. Prompt strings remain private on the
Modal Volume and under ignored local `results/`; public reports contain only
counts and hashes. The source archive is never extracted to filesystem paths.

Pairwise near-template rule (chosen before reading all 500 prompts):

1. Normalize with NFKC, casefold and whitespace collapse. Replace every
   contiguous digit sequence with `0` for template comparison; do not remove
   mathematical operators or alphabetic variables.
2. Form sets of character 5-grams of the raw normalized prompt and word 3-grams
   of the number-masked prompt. For short strings, use the whole string as one
   gram. Pair similarity is Jaccard intersection/union.
3. Link two prompts when length ratio >= 0.70 and either raw 5-gram Jaccard
   >= 0.82, or masked word 3-gram Jaccard >= 0.80 AND raw Jaccard >= 0.45.
   Connected components define conservative near-template groups. Record every
   linked edge and similarity in the private artifact for manual inspection.
4. Also count review candidates with length ratio >= 0.70 and raw Jaccard >=
   0.65, or masked word Jaccard >= 0.70 and raw >= 0.35. These are **not**
   automatically grouped. Grouping is heuristic, not certified independence.

The 48 pilot query hashes contaminate their entire detected components.
Report number of total groups, linked edges, candidate edges, contaminated
groups and remaining questions/groups. Do not assign final study folds or
inspect gold from the remaining questions in this step. Sensitivity analysis
and review of candidate/template families are required before declaring an
independent final evaluation set. The result can reveal inadequate sample size;
it cannot guarantee enough power for a paper.

The detached worker stores a packet, status, private prompt artifact and
checksum-protected analysis. It stops after grouping. Its source/protocol hashes
are recorded before submission; no adaptive threshold tuning on gold.
