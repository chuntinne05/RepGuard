# AppWorld v10: official simplified ReAct capability protocol (frozen before task calls)

**Date:** 03/10/2026. This is a separate AppWorld **0.2.0** experiment. AppWorld 0.1.3 v1–v9 scores cannot be pooled with it. Its purpose is to determine whether the official current simplified ReAct scaffold makes a viable interactive solver for a later paired complementarity test. It is not an ECRT/DART/HistRepEval result.

## Setup gate already completed

- Official AppWorld source commit `42b5bcf3cd334fee33f0c37c02070a9f5807add5`, package `0.2.0.dev0`; matching official 0.2.0 data bundle from `https://s3.us-west-2.amazonaws.com/appworld.dev/data-0.2.0.bundle`, 34,908,601 bytes, HTTP ETag `e879e1fcc5e16748694882d84378ec84-5`. The multipart ETag is an identifier, not a SHA-256 checksum. AppWorld CLI unpacked the bundle into a version-isolated, Git-ignored root.
- Official `appworld verify tasks --root results/appworld_external_v2 --num-processes 4` exited 0 and printed **Passed 147/147 tasks** across train and dev. This is a data/environment installation check using official solutions, not model performance. No protected data is committed.
- Official `appworld-agents` simplified ReAct code and its official `react_code_agent/instructions.txt` prompt are installed from the same checkout. A non-task Modal OpenAI-compatible completion returned a fenced `print('READY')` response. This checks transport only.

## Frozen model experiment

- **Train IDs:** `b7a9ee9_2`, `07b42fd_3`, `ce359b5_1`, `2a163ab_2`, `287e338_1`, `d0b1f43_3`. These are positions 25–30 of the pre-existing SHA-256 one-per-generator train ordering, selected from IDs without reading instructions, gold or outcomes. All are disjoint from earlier pilot IDs. No dev or test task will be run.
- **Agent:** official `SimplifiedReActCodeAgent` with unchanged official prompt and code parsing. Adapt only the LiteLLM transport for Modal bearer auth and force `load_ground_truth=False`; the agent asserts ground truth is absent at task initialization. One serial trajectory per ID, isolated output namespace; resume skips completed trajectories. No per-task prompt changes.
- **Model and budget:** `qwen3-coder:30b-ctx8192` on the existing Modal Ollama server. Parent digest `06c1097efce0431c2045fe7b2e5108366e43bee1b4603a7aded8f21689e90bca`, alias digest `b51abbfa75725b89e9bedf9f38a28b57c44a8f1a37c6429def3cc648e6c0d918`; runner checks both before tasks. Context 8192, temperature 0, top_p 1, seed 123, maximum 1024 output tokens and 40 ReAct steps per task, prompt/history caps 20,000 characters. Stop sequence matches official CI ReAct config: closing Python fence followed by newline. Model call counts and reported input/output tokens are recorded.
- **Evaluation:** separate official AppWorld 0.2 state-check evaluator process after each trajectory, with exact task success and passed/total checks. Runner starts the first task as a technical gate, then completes all six if integration works. Infrastructure failures are repaired/retried without scoring an incomplete task as model failure.

## Predeclared branch

If Coder solves **fewer than 2/6** exactly, stop this scaffold/model pool as a reputation test candidate. If it solves **at least 2/6**, run a paired Qwen3 32B control on these same six IDs with the same official scaffold and caps, but lock that control protocol before its first task call. Report both-success, Coder-only, Qwen32-only and both-failure cells. Expand to a larger train pool for history/routing only if rescues occur in **both** directions. A six-task train pilot is a feasibility gate, not an accuracy estimate or publication claim. Any method comparison later needs a cost-matched baseline and an untouched confirmation set.

**Runner:** `run_appworld_v10_simplified.py`. Frozen protocol hash: `e46c3e85e8807ce2f0d479b2d9768d10a516481f5a396999667291c69b74975f`.
