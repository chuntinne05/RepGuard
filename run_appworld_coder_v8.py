#!/usr/bin/env python3
"""Run the frozen Qwen3-Coder v8 AppWorld train capability screen."""

from __future__ import annotations

import json
import sys
import time

import run_appworld_legacy_react_v7 as legacy

TASK_IDS = (
    "cf6abd2_2", "771d8fc_2", "6104387_3",
    "e7a10f8_3", "82e2fac_2", "aa8502b_2",
)
PARENT_DIGEST = "06c1097efce0431c2045fe7b2e5108366e43bee1b4603a7aded8f21689e90bca"
ALIAS_DIGEST = "b51abbfa75725b89e9bedf9f38a28b57c44a8f1a37c6429def3cc648e6c0d918"

legacy.OUTPUT = legacy.DATA_ROOT / "train_pilot_v8_coder"
legacy.MODEL = "qwen3-coder:30b-ctx8192"
legacy.EXPERIMENT_NAME = "repguard_train_pilot_v8_coder"
legacy.TASK_IDS = TASK_IDS
legacy.MAX_TASKS = len(TASK_IDS)
original_protocol = legacy.protocol


def protocol() -> dict:
    if "PENDING" in PARENT_DIGEST or "PENDING" in ALIAS_DIGEST:
        raise RuntimeError("Pin v8 model digests before any task run")
    body = original_protocol()
    body.pop("protocol_hash")
    body.update(
        name="appworld_coder_v8_capability_screen",
        task_ids=TASK_IDS,
        task_selection="positions 13-18 of frozen SHA-256 one-per-generator train list",
        model=legacy.MODEL,
        parent_model_digest=PARENT_DIGEST,
        alias_model_digest=ALIAS_DIGEST,
        candidate_source="https://registry.ollama.com/library/qwen3-coder",
        screen_gate="at least 2/6 exact task successes to justify paired expansion",
    )
    return {"protocol_hash": legacy.digest(json.dumps(body, sort_keys=True)), **body}


legacy.protocol = protocol


if __name__ == "__main__":
    if "--collect" in sys.argv:
        import httpx
        from run_appworld_train_pilot import refresh_modal_token

        token = legacy.modal_token()
        for attempt in range(4):
            response = httpx.get(
                legacy.URL + "/api/tags",
                headers={"Modal-Authorization": "Bearer " + token},
                timeout=60,
            )
            if response.status_code == 401:
                token = refresh_modal_token(legacy.URL)
            elif response.status_code in {429, 500, 502, 503, 504}:
                time.sleep(5 * (attempt + 1))
            else:
                response.raise_for_status()
                digests = {item["name"]: item["digest"]
                           for item in response.json()["models"]}
                if digests.get("qwen3-coder:30b") != PARENT_DIGEST:
                    raise RuntimeError("v8 parent model digest changed")
                if digests.get(legacy.MODEL) != ALIAS_DIGEST:
                    raise RuntimeError("v8 alias model digest changed")
                break
        else:
            raise RuntimeError("Could not verify v8 Modal model digests")
    legacy.main()
