# AppWorld v9: GLM-4.7-Flash capability screen — frozen before task calls

**Date:** 03/10/2026. V8 produced three exact task successes for both Qwen3-Coder 30B and Qwen3 32B on the same six train IDs, with no single-model rescue. V9 tests a model from a different family on **new** train tasks before any history-based selection experiment. [Ollama's GLM-4.7-Flash card](https://registry.ollama.com/library/glm-4.7-flash) motivates a feasibility test but does not establish AppWorld performance. Ollama server version `0.34.4` has been verified; the card lists `0.14.3` as its minimum.

## Frozen task and evaluation design

- **Train IDs:** `60d0b5b_2`, `3c13f5a_1`, `ccb4494_2`, `e3d6c94_3`, `e85d92a_2`, `229360a_1` — positions 19–24 from the same SHA-256 one-per-generator rule. Selection was made from task IDs only, without opening instructions or gold. These IDs are disjoint from v1–v8. No dev/test access.
- **Environment and agent:** AppWorld `0.1.3.post1` protected bundle and the same version-matched legacy Recoma ReAct source/adapters as v7–v8. Gold disabled in agent; score each task using official state-check in a separate evaluator process after the trajectory. Separate output and AppWorld experiment namespace.
- **Model:** `glm-4.7-flash:latest` from the official Ollama library, on the existing Modal Ollama server (L4 or A10), with alias `glm-4.7-flash-ctx8192:latest`. The parent digest is `4475827791a269b02c8ec49b1c3bc1abb5846bacf3fae015b75d33986322d8f6`; alias digest is `724a495ee5055ed5ed9d396c12d1c0bc0eedaf03a4746829bfba59f0946500a5`. `/api/show` reports `num_ctx=8192`. Do not treat preflight transport/memory errors as task failures.
- **Inference budget:** temperature 0, top_p 1, `reasoning_effort=none`, at most 1,024 output tokens and 40 model/environment calls per task, controller history cap 20,000 characters; same as v8. A non-task OpenAI-compatible completion with this configuration returned a fenced one-line Python `print('READY')` in 9 output tokens and no separate reasoning field. This is technical compatibility, not AppWorld ability. No per-task prompt edits.
- **Execution:** run one task as a technical gate and, if the transport/model/agent work, finish all six. One completed trajectory per ID; no best-of selection. Report exact task success, check counts, realized model calls and input/output tokens, failure mode and any infrastructure retry. Raw task data stays Git-ignored.

## Predeclared decision branch

If GLM solves **fewer than two of six**, stop this candidate as an AppWorld reputation pool. If it solves **at least two**, run a paired Qwen3-Coder 30B control on the **same six new IDs**, same scaffold and caps, in a separate namespace. Report both-success, GLM-only, Coder-only and both-failure cells, along with realized tokens. Only meaningful rescue in **both** directions would justify expansion to a larger train pool for history/reputation. Even then, matching request caps is insufficient for a cost-matched method claim; that test must come later. Six selected train tasks are a feasibility gate, not a population accuracy estimate or an A* publication result.

## Reproducibility pin

`run_appworld_glm_v9.py` passed a no-task Recoma configuration preflight. Its protocol hash is `abe401ebd2a8df2291c9157ede5a6e5cb41486b034b4ebe6b093e6bf9dfce779`. Parent and alias digests, context, non-task completion, six IDs and gate were fixed before the first AppWorld task call. The first attempt to create the alias used an outdated `/api/create` body and returned HTTP 400; a request with the current `from` and `parameters` fields succeeded. Neither alias request was a task call.
