#!/usr/bin/env python3
"""Paired Qwen3 32B control for the frozen v8 AppWorld capability screen."""

from __future__ import annotations

import json
import sys
import time

import run_appworld_legacy_react_v7 as legacy

TASK_IDS = (
    "cf6abd2_2", "771d8fc_2", "6104387_3",
    "e7a10f8_3", "82e2fac_2", "aa8502b_2",
)
PARENT_DIGEST = "030ee887880fc378860c2dd35101da424377520441ae4bfe7be6deff8ade7840"
ALIAS_DIGEST = "09629261f4ec92b3ffd142c8a45c0b9104423ad62bb9d9d43ce095197524cf27"

legacy.OUTPUT = legacy.DATA_ROOT / "train_pilot_v8_qwen32_control"
legacy.MODEL = "qwen3:32b-ctx8192"
legacy.EXPERIMENT_NAME = "repguard_train_pilot_v8_qwen32_control"
legacy.TASK_IDS = TASK_IDS
legacy.MAX_TASKS = len(TASK_IDS)
original_protocol = legacy.protocol


def protocol() -> dict:
    body = original_protocol()
    body.pop("protocol_hash")
    body.update(
        name="appworld_v8_qwen32_paired_control",
        task_ids=TASK_IDS,
        task_selection="same positions 13-18 as frozen v8 coder capability screen",
        model=legacy.MODEL,
        parent_model_digest=PARENT_DIGEST,
        alias_model_digest=ALIAS_DIGEST,
        paired_with="appworld_coder_v8_capability_screen",
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
                headers={"Modal-Authorization": "Bearer " + token}, timeout=60,
            )
            if response.status_code == 401:
                token = refresh_modal_token(legacy.URL)
            elif response.status_code in {429, 500, 502, 503, 504}:
                time.sleep(5 * (attempt + 1))
            else:
                response.raise_for_status()
                digests = {item["name"]: item["digest"]
                           for item in response.json()["models"]}
                if digests.get("qwen3:32b") != PARENT_DIGEST:
                    raise RuntimeError("v8 control parent digest changed")
                if digests.get(legacy.MODEL) != ALIAS_DIGEST:
                    raise RuntimeError("v8 control alias digest changed")
                break
        else:
            raise RuntimeError("Could not verify v8 control digests")
    legacy.main()
