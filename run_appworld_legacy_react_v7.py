#!/usr/bin/env python3
"""Gold-blind, version-matched legacy AppWorld Recoma train pilot.

Use the separate 0.1.3 environment and official source checkout documented in
docs/analysis/appworld_legacy_react_v7_protocol_2026-10-02.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_ROOT = ROOT / "results/appworld_external_v1"
OUTPUT = DATA_ROOT / "train_pilot_v7_legacy_react"
SOURCE = Path("/private/tmp/repguard_appworld_official_013_src")
MODEL = "qwen3:32b-ctx8192"
EXPERIMENT_NAME = "repguard_train_pilot_v7_legacy_react"
URL = "https://chuntinne05--ollama-server-repguard-l4-ollamaserver.us-east.modal.direct"
TASK_IDS = ("afc0fce_2", "27e1026_2", "6ea6792_2")
MAX_TASKS = 3


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def protocol() -> dict:
    body = {
        "name": "appworld_legacy_react_v7",
        "split": "train",
        "task_ids": TASK_IDS,
        "task_selection": "positions 10-12 of frozen SHA-256 one-per-generator train list",
        "appworld_version": "0.1.3.post1",
        "data_bundle_sha256": "fd9f9608c2ec71ed0ac25c3633a738b9129a318a129e31230425b9188e508250",
        "official_source_commit": "66ad8099e12188ece0d3fe45e661dbc01880813b",
        "recoma_version": "0.0.4",
        "litellm_version": "1.37.19",
        "model": MODEL,
        "parent_model_digest": "030ee887880fc378860c2dd35101da424377520441ae4bfe7be6deff8ade7840",
        "num_ctx": 8192,
        "reasoning_effort": "none",
        "max_llm_calls": 40,
        "max_tokens_per_call": 1024,
        "temperature": 0,
        "top_p": 1,
        "seed": 123,
        "max_prompt_length_chars": 20000,
        "max_output_length_chars": 20000,
        "gold_loaded_in_agent": False,
        "evaluation": "AppWorld 0.1.3 state-check in fresh process after rollout",
        "adapters": ["Modal bearer auth + OpenAI compatible transport",
                     "gold-blind prompt fields", "answerer skips in-process evaluation"],
    }
    return {"protocol_hash": digest(json.dumps(body, sort_keys=True)), **body}


def configure_cache() -> None:
    cache_root = Path("/private/tmp/repguard_legacy_cache")
    cache_root.mkdir(parents=True, exist_ok=True)
    original_expand = os.path.expanduser

    def redirected(path):
        if isinstance(path, str) and path.startswith("~/.cache/"):
            return str(cache_root / path[len("~/.cache/"):])
        return original_expand(path)

    os.path.expanduser = redirected
    os.environ["MPLCONFIGDIR"] = str(cache_root / "matplotlib")


def make_config() -> dict:
    import _jsonnet

    path = SOURCE / "experiments/configs/react_gpt4o_test_normal.jsonnet"
    cfg = json.loads(_jsonnet.evaluate_file(str(path)))['config']
    cfg["reader"].update(dataset_name="train", tasks_per_gen=1)
    action = cfg["models"]["action"]
    action["max_prompt_length"] = 20000
    params = action["generator_params"]
    params.update(model=MODEL, max_tokens=1024, use_cache=False)
    cfg["search"]["stopping_conditions"] = [
        {"type": "max_env_calls", "max_env_calls": 40},
        {"type": "max_llm_calls", "max_llm_calls": 40},
    ]
    return cfg


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--collect", action="store_true")
    parser.add_argument("--max-tasks", type=int, default=MAX_TASKS)
    args = parser.parse_args()
    if not 1 <= args.max_tasks <= MAX_TASKS:
        parser.error(f"--max-tasks must be 1..{MAX_TASKS}")
    os.environ["APPWORLD_ROOT"] = str(DATA_ROOT)
    configure_cache()
    sys.path.insert(0, str(SOURCE))
    os.chdir(SOURCE)

    from appworld import AppWorld, load_task_ids
    from recoma.run_inference import build_configurable_systems_from_json
    from recoma.models.core.prompted_lm_model import PromptedLMModel
    from experiments.code.recoma import (  # noqa: F401
        AppworldAnswerer, AppworldPromptedLMModel,
    )
    from experiments.code.recoma.singleton_appworld import SingletonAppWorld

    selected = TASK_IDS[:args.max_tasks]
    train_ids = set(load_task_ids("train"))
    if any(task_id not in train_ids for task_id in selected):
        raise RuntimeError("One or more frozen IDs are not in train")
    cfg = make_config()
    plan = protocol()
    if not args.collect:
        # Resolve the official Recoma registries and config without opening a task.
        build_configurable_systems_from_json(cfg, str(OUTPUT / "preflight_recoma"))
        print(json.dumps({"protocol": plan, "selected": selected,
                          "config_build": "passed"}, indent=2))
        return

    from run_appworld_train_pilot import cached_modal_token, refresh_modal_token
    import litellm
    import recoma.models.impl.lite_llm_generator as litellm_module

    # The original prompt model computes a required-API field from ground truth.
    # Its ReAct template does not use that field, but remove the access entirely.
    def public_fields(self, input_str, state):
        params = PromptedLMModel.populate_template_dictionary(self, input_str, state)
        world = SingletonAppWorld().world
        if world.task.ground_truth is not None:
            raise RuntimeError("Ground truth loaded into agent process")
        params["main_user"] = world.task.supervisor
        params["app_descriptions"] = json.dumps(
            [{"name": k, "description": v}
             for k, v in world.task.app_descriptions.items()], indent=1)
        params["relevant_apis"] = "[]"
        return params

    AppworldPromptedLMModel.populate_template_dictionary = public_fields

    def finish_without_gold(self, state):
        world = SingletonAppWorld().world
        state.data["num_steps"] = len(world.environment_io)
        prediction = [io["input"] for io in world.environment_io]
        world.close()
        return json.dumps(prediction)

    AppworldAnswerer.generate_answer = finish_without_gold
    AppWorld.init_defaults.update(
        load_ground_truth=False, timeout_seconds=60, random_seed=123,
        max_interactions=41,
        experiment_name=EXPERIMENT_NAME)

    calls_path = OUTPUT / "model_calls.jsonl"
    def modal_completion(**kwargs):
        for auth_attempt in range(3):
            token = cached_modal_token(URL) or refresh_modal_token(URL)
            if not token:
                raise RuntimeError("Modal authorization token unavailable")
            kwargs["model"] = "openai/" + MODEL
            try:
                response = litellm.completion(
                    **kwargs, api_base=URL + "/v1", api_key="unused",
                    extra_headers={"Modal-Authorization": "Bearer " + token},
                    extra_body={"reasoning_effort": "none"}, timeout=180,
                )
                break
            except litellm.AuthenticationError:
                if auth_attempt == 2:
                    raise
                # Modal flash-auth tokens are short-lived. Refresh via its CLI
                # and retry transport only; no environment action occurred.
                refresh_modal_token(URL)
                time.sleep(2)
        usage = response.usage
        with calls_path.open("a") as fh:
            fh.write(json.dumps({"task_id": current_task[0],
                                 "prompt_tokens": getattr(usage, "prompt_tokens", None),
                                 "completion_tokens": getattr(usage, "completion_tokens", None),
                                 "content_chars": len(response.choices[0].message.content or "")}) + "\n")
        return response

    litellm_module.completion = modal_completion
    OUTPUT.mkdir(parents=True, exist_ok=True)
    manifest_path = OUTPUT / "manifest.json"
    if manifest_path.exists():
        old = json.loads(manifest_path.read_text())
        if old["protocol_hash"] != plan["protocol_hash"]:
            raise RuntimeError("Existing v7 manifest has a different protocol")
    else:
        manifest_path.write_text(json.dumps(plan, indent=2) + "\n")

    config_sys = build_configurable_systems_from_json(cfg, str(OUTPUT / "recoma"))
    config_sys.reader.task_ids = list(selected)
    current_task = [None]
    for example in config_sys.reader.get_examples():
        current_task[0] = example.task_id
        destination = OUTPUT / "runs" / (example.task_id + ".json")
        if destination.exists():
            print("skip_completed", example.task_id, flush=True)
            continue
        print("start", example.task_id, flush=True)
        prediction = config_sys.search.predict(example)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps({
            "protocol_hash": plan["protocol_hash"], "task_id": example.task_id,
            "prediction": json.loads(prediction.prediction),
            "steps": prediction.final_state.data.get("num_steps"),
            "experiment": AppWorld.init_defaults.experiment_name,
        }, indent=2) + "\n")
        print("done", example.task_id, "steps", prediction.final_state.data.get("num_steps"), flush=True)


if __name__ == "__main__":
    main()
