# AppWorld v5: Qwen3 32B thinking complementarity pilot — frozen before calls

**Date:** 2026-10-02 Vietnam time. V4 Qwen3 32B direct on the custom scaffold succeeded on 1/3 train task IDs (`7d7fbf6_1`) and failed on `692c77d_2`, `29caf6f_1`. V5 first runs **only `692c77d_2`**, paired with its existing direct trajectory, to see whether a thinking policy can rescue a failure. This is train-visible capability research, not an independent method test or official AppWorld score.

Keep the same Qwen3 32B model digest, task IDs, prompt, recent-history rule, exact-code duplicate suppression, 40-step cap, temperature 0 and official post-trajectory state-check as v4. Set `think=true`, `num_predict=4096`, `num_ctx=8192`; thus v5 is a **different inference/budget policy**, not an isolated think-flag ablation. Stop after eight suppressed exact repeats or three consecutive turns without executable code to limit cost. The model process loads no ground truth. Manifest is frozen on first collection.

If the first task returns no executable code three times, stop v5 and do not spend on the other tasks. If it makes meaningful app actions, state-check it; only if it succeeds or reveals a distinct actionable failure pattern, consider running the remaining paired train tasks. Even one rescue would be a feasibility signal, not statistical evidence of complementarity: a later method study needs more train IDs, equal-budget baselines and untouched dev/test.

Implementation: `run_appworld_train_pilot_v5.py`; output under Git-ignored `results/appworld_external_v1/train_pilot_v5/`.
