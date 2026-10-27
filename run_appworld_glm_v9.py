#!/usr/bin/env python3
"""Run the frozen GLM-4.7-Flash AppWorld v9 train capability screen."""

from __future__ import annotations

import json
import sys
import time

import run_appworld_legacy_react_v7 as legacy

TASK_IDS = (
    "60d0b5b_2", "3c13f5a_1", "ccb4494_2",
    "e3d6c94_3", "e85d92a_2", "229360a_1",
)
PARENT_DIGEST = "4475827791a269b02c8ec49b1c3bc1abb5846bacf3fae015b75d33986322d8f6"
ALIAS_DIGEST = "724a495ee5055ed5ed9d396c12d1c0bc0eedaf03a4746829bfba59f0946500a5"

legacy.OUTPUT = legacy.DATA_ROOT / "train_pilot_v9_glm"
legacy.MODEL = "glm-4.7-flash-ctx8192:latest"
legacy.EXPERIMENT_NAME = "repguard_train_pilot_v9_glm"
legacy.TASK_IDS = TASK_IDS
legacy.MAX_TASKS = len(TASK_IDS)
original_protocol = legacy.protocol


def protocol() -> dict:
    if "PENDING" in PARENT_DIGEST or "PENDING" in ALIAS_DIGEST:
        raise RuntimeError("Pin v9 model digests before any task run")
    body = original_protocol()
    body.pop("protocol_hash")
    body.update(
        name="appworld_glm_v9_capability_screen",
        task_ids=TASK_IDS,
        task_selection="positions 19-24 of frozen SHA-256 one-per-generator train list",
        model=legacy.MODEL,
        parent_model_digest=PARENT_DIGEST,
        alias_model_digest=ALIAS_DIGEST,
        candidate_source="https://registry.ollama.com/library/glm-4.7-flash",
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
                if digests.get("glm-4.7-flash:latest") != PARENT_DIGEST:
                    raise RuntimeError("v9 parent model digest changed")
                if digests.get(legacy.MODEL) != ALIAS_DIGEST:
                    raise RuntimeError("v9 alias model digest changed")
                break
        else:
            raise RuntimeError("Could not verify v9 Modal model digests")
    legacy.main()
