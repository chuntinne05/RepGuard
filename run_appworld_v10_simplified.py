#!/usr/bin/env python3
"""Gold-blind AppWorld 0.2 official simplified ReAct capability screen."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_ROOT = ROOT / "results/appworld_external_v2"
OUTPUT = DATA_ROOT / "train_pilot_v10_simplified_coder"
EXPERIMENT = "repguard_train_pilot_v10_simplified_coder"
URL = "https://chuntinne05--ollama-server-repguard-l4-ollamaserver.us-east.modal.direct"
MODEL = "qwen3-coder:30b-ctx8192"
PARENT_DIGEST = "06c1097efce0431c2045fe7b2e5108366e43bee1b4603a7aded8f21689e90bca"
ALIAS_DIGEST = "b51abbfa75725b89e9bedf9f38a28b57c44a8f1a37c6429def3cc648e6c0d918"
SOURCE_COMMIT = "42b5bcf3cd334fee33f0c37c02070a9f5807add5"
TASK_IDS = ("b7a9ee9_2", "07b42fd_3", "ce359b5_1", "2a163ab_2", "287e338_1", "d0b1f43_3")


def protocol() -> dict:
    body = {
        "name": "appworld_v10_official_simplified_coder_capability",
        "split": "train", "task_ids": TASK_IDS,
        "task_selection": "positions 25-30 of SHA-256 one-per-generator train list; IDs only",
        "appworld_source_commit": SOURCE_COMMIT,
        "appworld_package_version": "0.2.0.dev0", "data_version": "0.2.0",
        "data_url": "https://s3.us-west-2.amazonaws.com/appworld.dev/data-0.2.0.bundle",
        "data_etag": "e879e1fcc5e16748694882d84378ec84-5",
        "data_bundle_bytes": 34908601,
        "agent": "official appworld-agents simplified_react_code_agent; unchanged official prompt",
        "model": MODEL, "parent_digest": PARENT_DIGEST, "alias_digest": ALIAS_DIGEST,
        "num_ctx": 8192, "max_steps": 40, "max_tokens": 1024,
        "temperature": 0, "top_p": 1, "seed": 123,
        "stop": ["```\n"], "max_prompt_length_chars": 20000,
        "max_output_length_chars": 20000,
        "gold_loaded_in_agent": False,
        "evaluation": "AppWorld 0.2 official state-check in fresh process after trajectory",
        "gate": "at least 2/6 exact success to justify paired Qwen3 32B control on same IDs",
    }
    return {"protocol_hash": hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest(), **body}


def setup_env() -> None:
    os.environ["APPWORLD_ROOT"] = str(DATA_ROOT)
    os.environ["APPWORLD_CACHE"] = "/private/tmp/repguard_appworld_02_cache"
    os.environ["OPENAI_API_KEY"] = "unused"
    Path(os.environ["APPWORLD_CACHE"]).mkdir(parents=True, exist_ok=True)


def verify_model() -> None:
    import httpx
    from run_appworld_legacy_react_v7 import modal_token
    from run_appworld_train_pilot import refresh_modal_token

    for attempt in range(6):
        try:
            response = httpx.get(URL + "/api/tags", headers={
                "Modal-Authorization": "Bearer " + modal_token()}, timeout=90)
            if response.status_code == 401:
                refresh_modal_token(URL)
            elif response.status_code == 200:
                digests = {item["name"]: item["digest"] for item in response.json()["models"]}
                if digests.get("qwen3-coder:30b") != PARENT_DIGEST or digests.get(MODEL) != ALIAS_DIGEST:
                    raise RuntimeError("Modal model digest changed")
                return
            elif response.status_code not in {429, 500, 502, 503, 504}:
                response.raise_for_status()
        except httpx.TransportError:
            pass
        time.sleep(min(5 * (attempt + 1), 20))
    raise RuntimeError("Modal model preflight unavailable")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--collect", action="store_true")
    parser.add_argument("--max-tasks", type=int, default=len(TASK_IDS))
    args = parser.parse_args()
    if not 1 <= args.max_tasks <= len(TASK_IDS):
        parser.error("invalid max-tasks")
    setup_env()
    from appworld import load_task_ids, update_root
    from appworld.common.path_store import path_store
    from appworld_agents.code.simplified.react_code_agent import SimplifiedReActCodeAgent
    import appworld_agents.code.simplified.language_model as lm_module
    import litellm
    from run_appworld_legacy_react_v7 import modal_token
    from run_appworld_train_pilot import refresh_modal_token

    update_root(str(DATA_ROOT))
    selected = TASK_IDS[:args.max_tasks]
    if not set(selected).issubset(set(load_task_ids("train"))):
        raise RuntimeError("Frozen IDs not all in AppWorld 0.2 train")
    plan = protocol()
    prompt_path = Path(path_store.experiment_prompts) / "react_code_agent/instructions.txt"
    if not prompt_path.is_file():
        raise RuntimeError("Official simplified ReAct prompt missing")
    if not args.collect:
        print(json.dumps({"protocol": plan, "prompt_exists": True, "selected": selected}, indent=2))
        return

    verify_model()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    manifest_path = OUTPUT / "manifest.json"
    if manifest_path.exists():
        if json.loads(manifest_path.read_text())["protocol_hash"] != plan["protocol_hash"]:
            raise RuntimeError("Existing manifest has different protocol")
    else:
        manifest_path.write_text(json.dumps(plan, indent=2) + "\n")

    current_task = [None]
    calls_path = OUTPUT / "model_calls.jsonl"
    def modal_completion(**kwargs):
        kwargs.pop("api_key", None)
        for attempt in range(4):
            try:
                response = litellm.completion(
                    **kwargs, api_base=URL + "/v1", api_key="unused",
                    extra_headers={"Modal-Authorization": "Bearer " + modal_token()},
                    extra_body={"reasoning_effort": "none"}, timeout=180,
                )
                break
            except litellm.AuthenticationError:
                if attempt == 3:
                    raise
                refresh_modal_token(URL)
                time.sleep(2)
        usage = response.usage
        with calls_path.open("a") as fh:
            fh.write(json.dumps({"task_id": current_task[0],
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "content_chars": len(response.choices[0].message.content or "")}) + "\n")
        return response
    lm_module.get_raw_lm_caller = lambda **_kwargs: modal_completion

    class GoldBlindAgent(SimplifiedReActCodeAgent):
        def initialize(self, world):
            if world.task.ground_truth is not None:
                raise RuntimeError("Ground truth loaded into agent process")
            current_task[0] = world.task_id
            print("start", world.task_id, flush=True)
            super().initialize(world)

        def set_finished(self, experiment_name, task_id):
            super().set_finished(experiment_name, task_id)
            count = sum(1 for line in calls_path.read_text().splitlines()
                        if json.loads(line)["task_id"] == task_id) if calls_path.exists() else 0
            print("done", task_id, "model_calls", count, flush=True)

    agent = GoldBlindAgent(
        prompt_file_path=str(prompt_path),
        ignore_multiple_calls=True, max_prompt_length=20000, max_output_length=20000,
        model_config={"name": "openai/" + MODEL, "client_name": "litellm",
                      "api_type": "chat_completions", "api_key": "unused",
                      "max_tokens": 1024, "temperature": 0, "top_p": 1, "seed": 123,
                      "stop": ["```\n"], "use_cache": False, "max_retries": 3,
                      "retry_after_n_seconds": 10,
                      "cost_per_token": {"input_cache_miss": 0, "input_cache_hit": 0,
                                         "input_cache_write": 0, "output": 0}},
        appworld_config={"load_ground_truth": False, "random_seed": 123,
                         "timeout_seconds": 60, "max_interactions": 41},
        logger_config={"verbose": False, "color": False},
        max_steps=40, log_lm_calls=False, skip_if_finished=True,
    )
    agent.solve_tasks(list(selected), experiment_name=EXPERIMENT, num_processes=1)


if __name__ == "__main__":
    main()
