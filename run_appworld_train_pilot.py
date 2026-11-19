#!/usr/bin/env python3
"""Paired, gold-blind AppWorld train pilot with real Modal/Ollama calls.

This is a feasibility pilot with a small local ReAct harness, not an official
AppWorld agent score. The model process loads tasks with ground truth disabled;
evaluation belongs in a separate process after trajectories are saved.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "results/appworld_external_v1/train_pilot_v1"
DATA_ROOT = ROOT / "results/appworld_external_v1"
POLICIES = {
    "qwen3_8b_thinking": {"model": "qwen3:8b", "think": True, "num_predict": 8192},
    "qwen3_14b_direct": {"model": "qwen3:14b", "think": False, "num_predict": 1024},
}
MAX_STEPS = 16
PROMPT_VERSION = "appworld_local_react_v1"
CODE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


def sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def select_train_ids(ids: list[str], limit: int = 12) -> list[str]:
    """One task per generator, chosen without instruction or gold inspection."""
    by_generator: dict[str, list[str]] = {}
    for task_id in ids:
        by_generator.setdefault(task_id.rsplit("_", 1)[0], []).append(task_id)
    chosen = [min(group, key=lambda item: sha("member:" + item))
              for group in by_generator.values()]
    return sorted(chosen, key=lambda item: sha("group:" + item))[:limit]


def make_manifest(train_ids: list[str], digests: dict[str, str]) -> dict:
    protocol = {
        "name": "appworld_train_pilot_v1",
        "appworld_version": "0.1.3.post1",
        "data_bundle_sha256": "fd9f9608c2ec71ed0ac25c3633a738b9129a318a129e31230425b9188e508250",
        "split": "train",
        "task_ids": select_train_ids(train_ids),
        "selection": "sha256 ordered generator IDs; one member per generator",
        "policies": POLICIES,
        "max_steps": MAX_STEPS,
        "prompt_version": PROMPT_VERSION,
        "temperature": 0,
        "model_digests": digests,
        "ground_truth_loaded_in_model_process": False,
    }
    return {"created_at": now(), "protocol_hash": sha(json.dumps(protocol, sort_keys=True)),
            **protocol}


def prompt_for(task) -> str:
    user = task.supervisor
    return (
        "You are an AppWorld coding agent. Solve the task using only the provided "
        "Python REPL and `apis` object. In each reply write exactly one small "
        "```python code block; its code will be executed and the printed output "
        "shown to you. State persists between steps. Inspect an API before use: "
        "`print(apis.api_docs.show_app_descriptions())`, then "
        "`print(apis.api_docs.show_api_descriptions(app_name='...'))`, then "
        "`print(apis.api_docs.show_api_doc(app_name='...', api_name='...'))`. "
        "Use `apis.supervisor.show_account_passwords()` for app credentials. "
        "Do not invent IDs, credentials, or API arguments. Process all pages of "
        "paginated results. Use only AppWorld APIs; do not access OS files. "
        "After finishing call `apis.supervisor.complete_task(answer=...)` when "
        "an answer is needed, otherwise `apis.supervisor.complete_task()`. "
        "If impossible, call `apis.supervisor.complete_task(status='fail')`.\n\n"
        f"Supervisor: {user.first_name} {user.last_name}; "
        f"email: {user.email}; phone: {user.phone_number}.\n"
        f"Task: {task.instruction}\n"
    )


def cached_modal_token(url: str) -> str | None:
    path = Path.home() / ".cache/modal/curl-flash-auth-tokens.json"
    if not path.exists():
        return None
    host = urlparse(url).hostname or url
    for key, value in json.loads(path.read_text()).items():
        if isinstance(value, dict) and (key in host or host in key):
            if value.get("expires_at", 0) > time.time() + 60:
                return value.get("token")
    return None


def refresh_modal_token(url: str) -> str | None:
    modal = ROOT / ".venv/bin/modal"
    if modal.exists():
        subprocess.run([str(modal), "curl", url + "/api/version"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=90, check=False)
    return cached_modal_token(url)


def ollama_call(client, base_url: str, policy: dict, prompt: str) -> dict:
    import httpx

    payload = {"model": policy["model"], "messages": [{"role": "user", "content": prompt}],
               "stream": False, "think": policy["think"],
               "options": {"temperature": 0, "top_p": 1, "num_predict": policy["num_predict"]}}
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
    raise httpx.HTTPError("Ollama request retries exhausted")


def run_task(task_id: str, policy_name: str, policy: dict, client, base_url: str,
             protocol_hash: str) -> dict:
    from appworld import AppWorld

    experiment = "repguard_train_pilot_v1_" + policy_name
    trajectory: list[dict] = []
    with AppWorld(task_id=task_id, experiment_name=experiment,
                  load_ground_truth=False, max_interactions=MAX_STEPS + 1) as world:
        if world.task.ground_truth is not None:
            raise RuntimeError("Ground truth entered model process")
        initial = prompt_for(world.task)
        transcript = initial
        for step in range(MAX_STEPS):
            response = ollama_call(client, base_url, policy, transcript)
            content = response.get("message", {}).get("content") or ""
            match = CODE.search(content)
            code = match.group(1).strip() if match else ""
            if code:
                output = world.execute(code)
            else:
                output = "No executable Python code block returned."
            trajectory.append({"step": step + 1, "prompt_sha256": sha(transcript),
                               "model_content": content, "code": code,
                               "tool_output": output, "input_tokens": response.get("prompt_eval_count"),
                               "output_tokens": response.get("eval_count"),
                               "done_reason": response.get("done_reason")})
            if world.task_completed():
                break
            transcript += (f"\nAssistant:\n{content}\n\nEnvironment output:\n"
                           f"{output[:6000]}\n\nWrite the next single Python code block.\n")
            if len(transcript) > 100_000:
                transcript = initial + "\nEarlier steps omitted.\n" + transcript[-70_000:]
        completed = world.task_completed()
    return {"timestamp": now(), "protocol_hash": protocol_hash, "split": "train",
            "task_id": task_id, "policy": policy_name, "experiment": experiment,
            "completed_task_api": completed, "steps": len(trajectory), "trajectory": trajectory}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--collect", action="store_true")
    parser.add_argument("--max-tasks", type=int, default=12)
    parser.add_argument("--policies", nargs="*", choices=POLICIES, default=list(POLICIES))
    args = parser.parse_args()
    if not 1 <= args.max_tasks <= 12:
        parser.error("--max-tasks must be 1..12")
    os.environ["APPWORLD_ROOT"] = str(DATA_ROOT)
    from appworld import load_task_ids
    import httpx

    train_ids = load_task_ids("train")
    if not args.collect:
        manifest = make_manifest(train_ids, {policy["model"]: "preflight_only"
                                              for policy in POLICIES.values()})
        print(json.dumps({"candidate_task_ids": manifest["task_ids"],
                          "n_train": len(train_ids), "gold_loaded": False}, indent=2))
        return
    load_dotenv(ROOT / ".env")
    base_url = (os.environ.get("OLLAMA_URL") or os.environ.get("OLLAMA_HOST") or "").rstrip("/")
    if not base_url:
        raise RuntimeError("OLLAMA_URL/OLLAMA_HOST missing")
    headers = {}
    token = cached_modal_token(base_url) or refresh_modal_token(base_url)
    if token:
        headers["Modal-Authorization"] = "Bearer " + token
    with httpx.Client(headers=headers, timeout=330) as client:
        response = client.get(base_url + "/api/tags")
        response.raise_for_status()
        digests = {model["name"]: model["digest"] for model in response.json()["models"]}
        manifest = make_manifest(train_ids, digests)
        OUTPUT.mkdir(parents=True, exist_ok=True)
        path = OUTPUT / "manifest.json"
        if path.exists():
            previous = json.loads(path.read_text())
            if previous["protocol_hash"] != manifest["protocol_hash"]:
                raise RuntimeError("Pilot manifest changed")
            manifest = previous
        else:
            path.write_text(json.dumps(manifest, indent=2) + "\n")
        for policy_name in args.policies:
            for task_id in manifest["task_ids"][:args.max_tasks]:
                result_path = OUTPUT / "runs" / policy_name / f"{task_id}.json"
                if result_path.exists():
                    existing = json.loads(result_path.read_text())
                    if existing["protocol_hash"] != manifest["protocol_hash"]:
                        raise RuntimeError("Incompatible existing task result")
                    continue
                result = run_task(task_id, policy_name, POLICIES[policy_name],
                                  client, base_url, manifest["protocol_hash"])
                result_path.parent.mkdir(parents=True, exist_ok=True)
                tmp = result_path.with_suffix(".tmp")
                tmp.write_text(json.dumps(result, ensure_ascii=False) + "\n")
                tmp.replace(result_path)
                print(f"task={task_id} policy={policy_name} "
                      f"steps={result['steps']} completed_api={result['completed_task_api']}",
                      flush=True)


if __name__ == "__main__":
    main()
