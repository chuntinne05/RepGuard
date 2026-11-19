# AppWorld v6: paired direct-agent scaffold diagnostic — frozen before model calls

**Date:** 02/10/2026 (Asia/Ho_Chi_Minh). V4 Qwen3 32B direct solved 1/3 train tasks; v5 thinking with a larger generation/context budget solved 0/3 on those same IDs. V5 failed in API selection and postcondition verification while generating 10.47× as many output tokens. The next question is whether a generic verification instruction helps the *direct* agent on fresh train tasks. This is a capability pilot, not a HistRepEval/DART method test or an official AppWorld baseline score.

## Fixed comparison

- **Tasks:** `34d9492_2`, `b0a8eae_2`, `76f2c72_1`, positions 7–9 of the previously frozen SHA-256 one-per-generator train list. None was run in v1–v5. No task instruction, solution, evaluator test or task state was inspected to choose them.
- **Control:** The v4 explicit API-discovery prompt, Qwen3 32B direct, with the v5 five-turn short-history rule.
- **Treatment:** The exact control plus a generic instruction to read back requested state after the last mutation, verify answers from returned API data, and avoid claiming success from a write response or assumption. It does not hardcode a task-specific API sequence.
- **Equal inference budget:** Same model digest, `think=false`, `temperature=0`, `top_p=1`, `num_ctx=8192`, `num_predict=1024`, 40 model turns, five recent turns, 3,000-character tool outputs, exact-code repeat suppression at eight, and three consecutive no-code turns as a stop. Both use Ollama NDJSON streaming and the same `ollama-server-repguard-l4/OllamaServer` Modal deployment; the runner targets its explicit L4 URL because the generic `.env` URL points to an older recovery app. The two policies differ in prompt text only. The change from v4's 4K context and nonstreaming transport means the v6 control is **not** the old v4 cell.
- **Order:** Control then treatment for each task; task IDs in frozen order. This is not randomized. Model/server nondeterminism and GPU warm state remain possible limitations.
- **Ground truth:** The runner opens AppWorld with `load_ground_truth=False`. Raw trajectories and experiment outputs stay in Git-ignored `results/appworld_external_v1/train_pilot_v6/`. Score each completed cell with AppWorld's official state-check in a fresh Python process. Do not infer success from `complete_task` alone.

Implementation is `run_appworld_train_pilot_v6.py`; the manifest hashes the protocol and prompt/message source before collection. `--max-tasks` only stages the fixed three-task run and does not alter selection. If interrupted, resume by skipping compatible completed JSON cells; preserve aborted partial logs separately.

## Decision rules

Finish and report all three paired train IDs if service remains available. If deployment or transport repeatedly fails, report incomplete cells separately and do not count them as task failures. For each cell report official success/checks, turns, generated/input tokens, execution errors and `complete_task`. Compare paired success and cost, not raw check totals across tasks with different denominators. A gain on this tiny train-visible set is a feasibility signal only. Zero successes or no treatment-only rescue closes this scaffold avenue for now; any promising pattern requires more prospectively selected train tasks and a stronger official-compatible ReAct reference before dev testing. Do not open sealed holdout or claim DART superiority from v6.

The [official AppWorld repository](https://github.com/StonyBrookNLP/appworld) describes the benchmark's state-based evaluator and separate simplified ReAct agents; its [ReAct prompt](https://github.com/StonyBrookNLP/appworld/blob/main/experiments/prompts/react_code_agent/instructions.txt) emphasizes API documentation, paging and correct completion. V6 borrows that general verification principle but uses our custom harness, so the resulting numbers are not official-agent baseline scores.
