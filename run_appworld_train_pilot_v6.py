#!/usr/bin/env python3
"""Paired train-only AppWorld scaffold diagnostic using real Modal/Ollama calls.

This compares two Qwen3 32B direct scaffolds on previously unused train IDs.
It is not an official AppWorld baseline, a DART test, or a benchmark score.
"""

from __future__ import annotations

import argparse
import inspect
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv

from run_appworld_train_pilot import (
    CODE, DATA_ROOT, ROOT, cached_modal_token, now, refresh_modal_token,
    select_train_ids, sha,
)
from run_appworld_train_pilot_v4 import initial_prompt as control_prompt
from run_appworld_train_pilot_v5 import make_messages

OUTPUT = ROOT / "results/appworld_external_v1/train_pilot_v6"
MODEL = "qwen3:32b"
DEFAULT_L4_URL = "https://chuntinne05--ollama-server-repguard-l4-ollamaserver.us-east.modal.direct"
POLICIES = ("qwen3_32b_direct_control", "qwen3_32b_direct_verified")
NUM_CTX = 8192
NUM_PREDICT = 1024
MAX_STEPS = 40
REPEAT_LIMIT = 8
NO_CODE_LIMIT = 3
TOOL_CHARS = 3000
VERIFICATION_SUFFIX = (
    "\n\nBefore declaring completion, check the requested outcome with read APIs. "
    "After the last mutation, use a separate REPL turn to read the relevant "
    "state back, including all requested items; only then call "
    "apis.supervisor.complete_task(). For answer tasks, derive the exact "
    "answer from returned API data and check the calculation. If a call fails, "
    "read that API's documentation and change approach. Do not call "
    "complete_task(status='success') or claim success based only on a write "
    "response, an assumption, or a partial result. If you cannot complete the "
    "task, use complete_task(status='fail')."
)


def make_manifest(train_ids: list[str], model_digest: str) -> dict:
    selected = select_train_ids(train_ids)
    if len(selected) != 12:
        raise RuntimeError("Expected 12 hash-selected train generator IDs")
    protocol = {
        "name": "appworld_train_pilot_v6",
        "appworld_version": "0.1.3.post1",
        "data_bundle_sha256": "fd9f9608c2ec71ed0ac25c3633a738b9129a318a129e31230425b9188e508250",
        "split": "train",
        "task_ids": selected[6:9],
        "selection": "positions 7-9 of frozen SHA-256 train generator list; unused in v1-v5",
        "model_id": MODEL,
        "model_digest": model_digest,
        "endpoint_app": "ollama-server-repguard-l4/OllamaServer",
        "policies": {name: {"model": MODEL, "think": False,
                            "num_predict": NUM_PREDICT, "num_ctx": NUM_CTX}
                     for name in POLICIES},
        "temperature": 0,
        "top_p": 1,
        "max_steps": MAX_STEPS,
        "recent_turns": 5,
        "tool_output_chars": TOOL_CHARS,
        "duplicate_code_suppression": True,
        "repeat_suppression_stop_count": REPEAT_LIMIT,
        "consecutive_no_code_stop_count": NO_CODE_LIMIT,
        "prompt_source_sha256": sha(inspect.getsource(control_prompt) + VERIFICATION_SUFFIX),
        "message_source_sha256": sha(inspect.getsource(make_messages)),
        "transport": "ollama_ndjson_stream_both_policies",
        "ground_truth_loaded_in_model_process": False,
    }
    return {"created_at": now(), "protocol_hash": sha(json.dumps(protocol, sort_keys=True)),
            **protocol}


def prompt_for(task, policy: str) -> str:
    prompt = control_prompt(task)
    return prompt + (VERIFICATION_SUFFIX if policy == POLICIES[1] else "")


def call_model(client, base_url: str, messages: list[dict]) -> dict:
    import httpx

    payload = {"model": MODEL, "messages": messages, "stream": True,
               "think": False, "options": {"temperature": 0, "top_p": 1,
               "num_predict": NUM_PREDICT, "num_ctx": NUM_CTX}}
    for attempt in range(4):
        try:
            with client.stream("POST", base_url + "/api/chat", json=payload) as response:
                if response.status_code == 401 and attempt < 3:
                    token = refresh_modal_token(base_url)
                    if token:
                        client.headers["Modal-Authorization"] = "Bearer " + token
                        continue
                if response.status_code in {429, 500, 502, 503, 504} and attempt < 3:
                    time.sleep(5 * (attempt + 1))
                    continue
                response.raise_for_status()
                parts: list[str] = []
                final: dict | None = None
                for line in response.iter_lines():
                    if not line:
                        continue
                    part = json.loads(line)
                    parts.append(part.get("message", {}).get("content") or "")
                    if part.get("done"):
                        final = part
                        break
                if final is None:
                    raise httpx.RemoteProtocolError("Ollama stream ended without done=true")
                final["message"] = {"content": "".join(parts)}
                return final
        except httpx.TransportError:
            if attempt >= 3:
                raise
            time.sleep(5 * (attempt + 1))
    raise httpx.HTTPError("AppWorld v6 model request retries exhausted")


def run_task(task_id: str, policy: str, client, base_url: str,
             protocol_hash: str) -> dict:
    from appworld import AppWorld

    experiment = "repguard_train_pilot_v6_" + policy
    history: list[dict] = []
    with AppWorld(task_id=task_id, experiment_name=experiment,
                  load_ground_truth=False, max_interactions=MAX_STEPS + 1) as world:
        if world.task.ground_truth is not None:
            raise RuntimeError("Ground truth entered model process")
        initial = prompt_for(world.task, policy)
        executed_outputs: dict[str, str] = {}
        repeat_count = 0
        no_code_streak = 0
        stopped_for_repeat_loop = False
        stopped_for_no_code = False
        for step in range(MAX_STEPS):
            response = call_model(client, base_url, make_messages(initial, history))
            content = response.get("message", {}).get("content") or ""
            match = CODE.search(content)
            code = match.group(1).strip() if match else ""
            no_code_streak = 0 if code else no_code_streak + 1
            repeated = bool(code and code in executed_outputs)
            repeat_count += int(repeated)
            if not code:
                output = "No Python code block was returned. Provide one executable block."
            elif repeated:
                output = ("This exact code already ran. Its previous output was:\n" +
                          executed_outputs[code][:TOOL_CHARS] +
                          "\nUse this result and take a different action.")
            else:
                output = world.execute(code)
                executed_outputs[code] = str(output)
            history.append({"step": step + 1, "model_content": content, "code": code,
                            "tool_output": str(output), "repeat_suppressed": repeated,
                            "input_tokens": response.get("prompt_eval_count"),
                            "output_tokens": response.get("eval_count"),
                            "done_reason": response.get("done_reason")})
            print(f"policy={policy} task={task_id} step={step+1} "
                  f"executed={bool(code and not repeated)} "
                  f"completed={world.task_completed()}", flush=True)
            if world.task_completed():
                break
            if repeat_count >= REPEAT_LIMIT:
                stopped_for_repeat_loop = True
                break
            if no_code_streak >= NO_CODE_LIMIT:
                stopped_for_no_code = True
                break
        completed = world.task_completed()
    return {"timestamp": now(), "protocol_hash": protocol_hash, "split": "train",
            "task_id": task_id, "policy": policy, "experiment": experiment,
            "completed_task_api": completed, "steps": len(history),
            "stopped_for_repeat_loop": stopped_for_repeat_loop,
            "stopped_for_no_code": stopped_for_no_code,
            "transport": "ollama_ndjson_stream", "trajectory": history}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--collect", action="store_true")
    parser.add_argument("--max-tasks", type=int, default=3)
    args = parser.parse_args()
    if not 1 <= args.max_tasks <= 3:
        parser.error("--max-tasks must be 1..3")
    os.environ["APPWORLD_ROOT"] = str(DATA_ROOT)
    from appworld import load_task_ids

    train_ids = load_task_ids("train")
    if not args.collect:
        print(json.dumps({"task_ids": make_manifest(train_ids, "preflight_only")["task_ids"],
                          "policies": POLICIES, "split": "train", "gold_loaded": False},
                         indent=2))
        return

    import httpx

    load_dotenv(ROOT / ".env")
    # The generic .env OLLAMA_URL points at the older recovery app; v6 uses L4.
    base_url = (os.environ.get("OLLAMA_L4_URL") or DEFAULT_L4_URL).rstrip("/")
    token = cached_modal_token(base_url) or refresh_modal_token(base_url)
    headers = {"Modal-Authorization": "Bearer " + token} if token else {}
    timeout = httpx.Timeout(connect=60, read=120, write=60, pool=60)
    with httpx.Client(headers=headers, timeout=timeout) as client:
        for attempt in range(4):
            response = client.get(base_url + "/api/tags")
            if response.status_code == 401:
                token = refresh_modal_token(base_url)
                if token:
                    client.headers["Modal-Authorization"] = "Bearer " + token
                    continue
            if response.status_code in {429, 500, 502, 503, 504} and attempt < 3:
                time.sleep(10 * (attempt + 1))
                continue
            break
        response.raise_for_status()
        digests = {row["name"]: row["digest"] for row in response.json()["models"]}
        manifest = make_manifest(train_ids, digests[MODEL])
        OUTPUT.mkdir(parents=True, exist_ok=True)
        path = OUTPUT / "manifest.json"
        if path.exists():
            previous = json.loads(path.read_text())
            if previous["protocol_hash"] != manifest["protocol_hash"]:
                raise RuntimeError("AppWorld v6 manifest changed")
            manifest = previous
        else:
            path.write_text(json.dumps(manifest, indent=2) + "\n")
        for task_id in manifest["task_ids"][:args.max_tasks]:
            for policy in POLICIES:
                result_path = OUTPUT / "runs" / policy / f"{task_id}.json"
                if result_path.exists():
                    if json.loads(result_path.read_text())["protocol_hash"] != manifest["protocol_hash"]:
                        raise RuntimeError("Incompatible existing AppWorld v6 result")
                    continue
                result = run_task(task_id, policy, client, base_url,
                                  manifest["protocol_hash"])
                result_path.parent.mkdir(parents=True, exist_ok=True)
                temp = result_path.with_suffix(".tmp")
                temp.write_text(json.dumps(result, ensure_ascii=False) + "\n")
                temp.replace(result_path)
                print(f"finished policy={policy} task={task_id} "
                      f"steps={result['steps']} completed_api={result['completed_task_api']}",
                      flush=True)


if __name__ == "__main__":
    main()
