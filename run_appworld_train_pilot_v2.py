#!/usr/bin/env python3
"""Gold-blind AppWorld train feasibility pilot with compact chat history.

This is a new development protocol after the v1 three-task smoke showed API-doc
loops. It uses three *different* hash-selected train tasks and never opens dev
or test task outcomes. It is a custom scaffold, not an official AppWorld score.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

from run_appworld_train_pilot import (
    CODE,
    DATA_ROOT,
    ROOT,
    cached_modal_token,
    now,
    refresh_modal_token,
    select_train_ids,
    sha,
)

OUTPUT = ROOT / "results/appworld_external_v1/train_pilot_v2"
POLICY = {"model": "qwen3:14b", "think": False, "num_predict": 1024}
MAX_STEPS = 40
RECENT_TURNS = 3
TOOL_CHARS = 3000


def make_manifest(train_ids: list[str], model_digest: str) -> dict:
    selected = select_train_ids(train_ids)
    if len(selected) != 12:
        raise RuntimeError("Expected 12 hash-selected train generator IDs")
    protocol = {
        "name": "appworld_train_pilot_v2",
        "appworld_version": "0.1.3.post1",
        "data_bundle_sha256": "fd9f9608c2ec71ed0ac25c3633a738b9129a318a129e31230425b9188e508250",
        "split": "train",
        "task_ids": selected[3:6],
        "selection": "positions 4-6 in the frozen SHA-256 ordered one-per-generator train list",
        "model_id": POLICY["model"],
        "model_digest": model_digest,
        "think": POLICY["think"],
        "num_predict": POLICY["num_predict"],
        "temperature": 0,
        "max_steps": MAX_STEPS,
        "recent_turns": RECENT_TURNS,
        "tool_output_chars": TOOL_CHARS,
        "prompt_version": "appworld_compact_chat_v2",
        "duplicate_code_suppression": True,
        "ground_truth_loaded_in_model_process": False,
    }
    return {"created_at": now(), "protocol_hash": sha(json.dumps(protocol, sort_keys=True)),
            **protocol}


def initial_prompt(task) -> str:
    user = task.supervisor
    return (
        "Solve the user's task through the AppWorld Python REPL. Reply with one "
        "```python code block per turn; the environment executes it and keeps "
        "Python variables between turns. Use only the `apis` object. Start by "
        "finding the relevant app and API documentation. After reading a doc, "
        "advance to an action instead of requesting the same doc again. "
        "Read the exact API signature before calling it. For login, obtain the "
        "password with `apis.supervisor.show_account_passwords()` and select "
        "the entry matching the app; do not invent credentials. Handle pages "
        "of results. When done, call `apis.supervisor.complete_task(...)`. "
        "You have at most 40 turns.\n\n"
        f"Supervisor: {user.first_name} {user.last_name}; email: {user.email}; "
        f"phone: {user.phone_number}.\nTask: {task.instruction}"
    )


def make_messages(initial: str, history: list[dict]) -> list[dict]:
    messages = [
        {"role": "system", "content": "Act through one Python code block each turn. Use the REPL output to make progress. Never repeat an identical code block."},
        {"role": "user", "content": initial},
    ]
    if len(history) > RECENT_TURNS:
        prior = history[:-RECENT_TURNS]
        code_list = [f"{i+1}. {entry['code'][:180]}" for i, entry in enumerate(prior[-20:])]
        messages.append({"role": "user", "content":
                         "Earlier code already attempted (do not repeat it):\n" +
                         "\n".join(code_list)})
    for entry in history[-RECENT_TURNS:]:
        messages.append({"role": "assistant", "content": entry["model_content"]})
        messages.append({"role": "user", "content":
                         "REPL output:\n" + entry["tool_output"][:TOOL_CHARS] +
                         "\nNext: write one NEW Python code block that advances the task."})
    return messages


def call_model(client, base_url: str, messages: list[dict]) -> dict:
    import httpx

    payload = {"model": POLICY["model"], "messages": messages, "stream": False,
               "think": POLICY["think"], "options": {"temperature": 0, "top_p": 1,
               "num_predict": POLICY["num_predict"]}}
    for attempt in range(4):
        response = client.post(base_url + "/api/chat", json=payload)
        if response.status_code == 401 and attempt < 3:
            token = refresh_modal_token(base_url)
            if token:
                client.headers["Modal-Authorization"] = "Bearer " + token
                continue
        if response.status_code in {429, 500, 502, 503, 504} and attempt < 3:
            time.sleep(5 * (attempt + 1))
            continue
        response.raise_for_status()
        return response.json()
    raise httpx.HTTPError("AppWorld v2 model request retries exhausted")


def run_task(task_id: str, client, base_url: str, protocol_hash: str) -> dict:
    from appworld import AppWorld

    experiment = "repguard_train_pilot_v2_qwen3_14b_direct"
    history: list[dict] = []
    with AppWorld(task_id=task_id, experiment_name=experiment,
                  load_ground_truth=False, max_interactions=MAX_STEPS + 1) as world:
        if world.task.ground_truth is not None:
            raise RuntimeError("Ground truth entered model process")
        initial = initial_prompt(world.task)
        executed_outputs: dict[str, str] = {}
        for step in range(MAX_STEPS):
            response = call_model(client, base_url, make_messages(initial, history))
            content = response.get("message", {}).get("content") or ""
            match = CODE.search(content)
            code = match.group(1).strip() if match else ""
            repeated = bool(code and code in executed_outputs)
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
            if world.task_completed():
                break
        completed = world.task_completed()
    return {"timestamp": now(), "protocol_hash": protocol_hash, "split": "train",
            "task_id": task_id, "policy": "qwen3_14b_direct",
            "experiment": experiment, "completed_task_api": completed,
            "steps": len(history), "trajectory": history}


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
                          "split": "train", "gold_loaded": False}, indent=2))
        return

    import httpx

    load_dotenv(ROOT / ".env")
    base_url = (os.environ.get("OLLAMA_URL") or os.environ.get("OLLAMA_HOST") or "").rstrip("/")
    if not base_url:
        raise RuntimeError("OLLAMA_URL/OLLAMA_HOST missing")
    token = cached_modal_token(base_url) or refresh_modal_token(base_url)
    headers = {"Modal-Authorization": "Bearer " + token} if token else {}
    with httpx.Client(headers=headers, timeout=330) as client:
        response = client.get(base_url + "/api/tags")
        if response.status_code == 401:
            token = refresh_modal_token(base_url)
            if token:
                client.headers["Modal-Authorization"] = "Bearer " + token
                response = client.get(base_url + "/api/tags")
        response.raise_for_status()
        digests = {row["name"]: row["digest"] for row in response.json()["models"]}
        manifest = make_manifest(train_ids, digests[POLICY["model"]])
        OUTPUT.mkdir(parents=True, exist_ok=True)
        path = OUTPUT / "manifest.json"
        if path.exists():
            previous = json.loads(path.read_text())
            if previous["protocol_hash"] != manifest["protocol_hash"]:
                raise RuntimeError("AppWorld v2 manifest changed")
            manifest = previous
        else:
            path.write_text(json.dumps(manifest, indent=2) + "\n")
        for task_id in manifest["task_ids"][:args.max_tasks]:
            result_path = OUTPUT / "runs" / "qwen3_14b_direct" / f"{task_id}.json"
            if result_path.exists():
                if json.loads(result_path.read_text())["protocol_hash"] != manifest["protocol_hash"]:
                    raise RuntimeError("Incompatible existing AppWorld v2 result")
                continue
            result = run_task(task_id, client, base_url, manifest["protocol_hash"])
            result_path.parent.mkdir(parents=True, exist_ok=True)
            temp = result_path.with_suffix(".tmp")
            temp.write_text(json.dumps(result, ensure_ascii=False) + "\n")
            temp.replace(result_path)
            print(f"task={task_id} steps={result['steps']} "
                  f"completed_api={result['completed_task_api']}", flush=True)


if __name__ == "__main__":
    main()
