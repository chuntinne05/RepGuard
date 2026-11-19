# AppWorld train feasibility pilot v2 — protocol before outcomes

**Frozen on:** 2026-10-01, after the v1 smoke and before any v2 model call. This is a development pilot, not an official AppWorld baseline or a paper result.

## Motivation from v1

The custom v1 ReAct harness completed three real Qwen3 14B direct train trajectories and the official state-check evaluator scored **0/3 task successes**. All three reached the local 16-step cap without calling `complete_task`. Two spent every step inspecting API documentation; one attempted application actions but had execution/login errors. Thus v1 does not establish whether the model, the scaffold, or the step budget caused failure. The original v1 ledger and evaluator remain unchanged.

## Frozen v2 changes

- Use the same installed `appworld==0.1.3.post1` data bundle and the same Qwen3 14B direct model digest checked at runtime. Temperature remains 0 and output cap remains 1,024 tokens per call.
- Select the **fourth through sixth** IDs from the already hash-ordered, one-per-generator train list: `692c77d_2`, `29caf6f_1`, `7d7fbf6_1`. They are disjoint from the three v1 smoke IDs. Do not use dev or test tasks.
- Raise the local step cap from 16 to **40**. The [official AppWorld ReAct baseline config](https://github.com/StonyBrookNLP/appworld/blob/v0.1.3.post1/experiments/configs/react_llama3_test_normal.jsonnet) allows up to 100 LLM calls, so 16 was a restrictive feasibility cap, not a standard benchmark budget. Our 40-step v2 is still a different custom scaffold and must be labeled accordingly.
- Present the initial instruction plus the latest three assistant/tool exchanges as chat roles, with a compact list of older code. Cache the result of exact duplicate code and return that result without re-executing the same tool call. Clarify credential lookup and completion requirements in the prompt. These are scaffold interventions selected from v1 train errors, not changes to the underlying AppWorld task.
- Model process uses `load_ground_truth=False`; official state-check is run only by a separate evaluator after each closed trajectory is saved. Record task success, passed checks, steps, repeat suppression, errors, calls, input/output tokens and any `complete_task` call.

## Decision rule

If v2 gets at least one state-check success in the three new train tasks, consider a larger **paired** train pilot between two frozen policies at the same scaffold and budget. If v2 remains 0/3, inspect the failure taxonomy and test a compatible official agent scaffold or a stronger solver on *train* before concluding AppWorld is unsuitable. Do not open dev/test for prompt selection. Three tasks are too few for a method claim either way.

The implementation is `run_appworld_train_pilot_v2.py`; the evaluator is `evaluate_appworld_train_pilot.py --output results/appworld_external_v1/train_pilot_v2`. The raw trajectories and task-derived content stay under Git-ignored `results/` in accordance with AppWorld's redistribution conditions.
