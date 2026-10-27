# AppWorld official-agent compatibility audit (02/10/2026)

**Purpose:** After v6 failed 0/3 in both custom-harness policies, the next capability reference should use AppWorld's own ReAct agent implementation. A source/version audit was performed **without any model calls** and without opening dev or sealed holdout.

## Verified source and environment facts

- The local completed pilots use `appworld==0.1.3.post1`, a local data bundle pinned by SHA-256 `fd9f9608c2ec71ed0ac25c3633a738b9129a318a129e31230425b9188e508250`, and Pydantic 1.10.26. Official state-checks for v1–v6 were run through this package. The local result data is Git-ignored.
- The current [official AppWorld repository](https://github.com/StonyBrookNLP/appworld), inspected at commit `42b5bcf3cd334fee33f0c37c02070a9f5807add5`, provides `experiments/code/simplified/react_code_agent.py` and a separate `appworld-agents` package. Its root AppWorld package is `0.2.0.dev0` and requires Pydantic 2; the current simplified agent also imports Pydantic 2 APIs. Its [experiment guidance](https://github.com/StonyBrookNLP/appworld/blob/main/README.md) treats these as the official simplified agents.
- The version-matched official tag `v0.1.3.post1` resolves to commit `66ad8099e12188ece0d3fe45e661dbc01880813b`. Its `experiments/` directory contains the earlier **Recoma/legacy ReAct** configuration (`react_gpt4o_test_normal.jsonnet`, prompt `react.txt`), not the later simplified agent. Thus “run simplified ReAct on the old 0.1.3 bundle” would mix code and evaluator/data versions.
- A trial editable install of the newer agents into the old temporary environment upgraded Pydantic to 2 and broke `import appworld`. It was immediately reversed: Pydantic 1.10.26 restored, `appworld-agents` and `litellm` removed, `pip check` reports no broken requirements, and a fresh sample state-check still returns the previously recorded **4/5, fail**. No task trajectory or evaluator result was altered by this package experiment.
- The newer repository's `src/appworld/.source/apps.bundle` uses Git LFS; this machine lacks `git-lfs`. A source checkout without LFS supplies a pointer rather than the protected bundle, so it is not yet a working 0.2 benchmark install. No 0.2 task data was downloaded or scored.

## Consequence for paper claims

V4–v6 remain **real custom-harness AppWorld 0.1.3 train pilots**, not an official ReAct baseline. There is currently **no official-agent score** in this project. The six v6 state-check scores remain valid under the restored 0.1.3 evaluator. The Modal L4 server is deployed, but no AppWorld runner remains active after v6.

## Next controlled options

1. **Comparable reference on existing 0.1.3 data:** run the official **legacy Recoma ReAct** code at tag `v0.1.3.post1` in a separate environment, with a transport adapter for Modal authentication and a predeclared step/token budget. Use the remaining fresh train-generator positions 10–12, then evaluate with the same 0.1.3 state-check. Call it a version-matched legacy reference, not simplified ReAct.
2. **Current simplified agent:** set up a fully isolated AppWorld 0.2 installation with its matching protected bundle/data and the pinned simplified-agent code, then run a new train-only protocol. Its scores cannot be paired with v4–v6 because the benchmark/data version changes. Verify installation, package compatibility and model transport before freezing task IDs or making model calls.

Option 1 has now reached a runnable preflight in an isolated AppWorld 0.1.3/Pydantic 1 environment with `recoma==0.0.4` and `litellm==1.37.19`; `pip check` and Recoma configuration construction pass. The Ollama Qwen3 32B context-8K alias was created on the existing Modal L4 deployment. The frozen v7 setup is recorded in [the protocol](appworld_legacy_react_v7_protocol_2026-10-02.md). No v7 AppWorld task result is claimed in this compatibility note.

The legacy prompted model reads `world.task.ground_truth.required_apis` while building template fields, but the actual `react.txt` prompt does not interpolate `relevant_apis`. Thus the audited source has a latent gold access, **not evidence of gold being shown in that prompt**. V7 removes the access entirely, disables gold loading, and moves scoring to a separate process. If the base agent cannot solve enough train tasks, stop AppWorld pool construction and focus HistRepEval on an environment with demonstrably capable complementary agents. Do not tune against sealed holdout.
