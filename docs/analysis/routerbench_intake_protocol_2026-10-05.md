# External benchmark intake protocol

Locked before downloading the archive. Purpose: discover compatible datasets,
model coverage and metadata without selecting on outcome scores. No learned
method or judge is run by this job. Earlier scientific gates stay unchanged.

- Source: NPULH/LLMRouterBench, HF revision
  `0e5af1b84bf73437a01a1849c0f1d2468baa93fc`, 1,283,503,080 bytes, SHA256
  `b79f8cde1a6f029c2efa663a3a3b6f7748defb22341fe59f328cebef6648c8f1`.
- Official repository checked at `c77cb0506949d8f959e97967d2fefca0e8ff1b05`.
  GitHub root license and HF card license are not declared in the checked metadata.
  Keep downloaded material private; do not redistribute it or apply this project's
  MIT license to it. Underlying dataset/evaluator provenance still needs review.
- Download archive on detached Modal CPU worker, verify exact size and SHA256.
  Checkpoint resumable download. 24h maximum, two retries, one worker.
- Stream tar contents without extracting untrusted paths; reject absolute/traversal
  names, bound expanded size to64GiB. Files with `mmlu` anywhere in path are skipped
  before JSON parsing. Archive bytes contain these files, but payloads are not parsed.
- Parse only JSON beneath `bench/<dataset>/<partition>/<model>/<file>.json`.
  Retain record field names, index, normalized query SHA256, length, query source.
  Normalization: Unicode NFKC, casefold and whitespace collapse. Prefer origin_query,
  otherwise prompt. Unsupported query structures are counted explicitly.
- JSON tokenization necessarily traverses other values. Score, reference, prediction,
  reasoning and aggregate performance values are ignored and never retained in
  metadata artifacts or exposed to a learner/research selection decision.
- Report unique and common query hashes across models, partitions, duplicate counts
  and missingness; no accuracy/ranking. Multiple files per model are counted and
  flagged; a later pilot must lock a unique run per model before reading scores.
- Atomic per-file checkpoints with hashes; Volume commit every25 files and on error.
  Resume verifies identity and hashes. Final status `completed_inventory` is a data
  inventory result, not completed DART validation.
- Subsequent dataset selection must use task type, evaluator provenance and coverage,
  not outcomes. Pilot judgment requires a separate locked manifest and gold-blind
  input adapter. No automatic opening of the existing sealed holdouts.

Sources: [official repository](https://github.com/ynulihao/LLMRouterBench),
[public data archive](https://huggingface.co/datasets/NPULH/LLMRouterBench).
