#!/usr/bin/env python3
"""Paired, resumable real Qwen3 thinking screen on unused MMLU-Pro train items.

The frozen manifest contains only task IDs and protocol metadata. Ground truth
is loaded for analysis later; it is never passed to the model or written here.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from repguard.config import ProviderConfig, ProviderParams
from repguard.providers.ollama_ import OllamaProvider
from repguard.harness.prompts import format_prompt
from run_real_week3 import load_dataset_and_splits, utc_now


MODEL_ID = "qwen3:8b"
PROMPT_VERSION = "week3_direct_json_enum_v1"
DEFAULT_OUTPUT = Path("results/real_week4_thinking_pilot_v3")


def variants_for(thinking_max_tokens: int) -> dict:
    return {"direct64": {"think": False, "max_tokens": 64},
            f"thinking{thinking_max_tokens}": {"think": True,
                                              "max_tokens": thinking_max_tokens}}


def canonical_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode()).hexdigest()


def select_unused(splits, old_manifest: dict, per_subject: int, seed: int) -> dict[str, list[str]]:
    by_subject = defaultdict(list)
    old_ids = {task_id for ids in old_manifest["selected"]["train_calibration"].values()
               for task_id in ids}
    for task in splits["train_calibration"].records:
        if task.task_id not in old_ids:
            by_subject[task.metadata.subject].append(task.task_id)
    selected = {}
    for subject in sorted(by_subject):
        ids = sorted(by_subject[subject])
        random.Random(f"{seed}:week4:{subject}").shuffle(ids)
        if len(ids) < per_subject:
            raise RuntimeError(f"Only {len(ids)} unused train items in {subject}")
        selected[subject] = ids[:per_subject]
    return selected


def frozen_manifest(splits, old_manifest: dict, model_digest: str,
                    server_version: str, per_subject: int, seed: int,
                    thinking_max_tokens: int) -> dict:
    selected = select_unused(splits, old_manifest, per_subject, seed)
    protocol = {
        "name": "week4_qwen3_paired_thinking_v3",
        "dataset_id": old_manifest["dataset_id"],
        "dataset_task_id_sha256": old_manifest["dataset_task_id_sha256"],
        "split_seed": old_manifest["split_seed"],
        "selection_seed": seed,
        "model_id": MODEL_ID,
        "model_digest": model_digest,
        "ollama_version": server_version,
        "prompt_version": PROMPT_VERSION,
        "temperature": 0.0,
        "top_p": 1.0,
        "json_schema": "answer_enum_available_letters_v1",
        "variants": variants_for(thinking_max_tokens),
        "selected_train_ids": selected,
    }
    return {"created_at": utc_now(), "protocol_hash": canonical_hash(protocol), **protocol}


def load_completed(path: Path, protocol_hash: str) -> set[tuple[str, str]]:
    completed = set()
    if path.exists():
        for line in path.read_text().splitlines():
            if not line:
                continue
            row = json.loads(line)
            if row["protocol_hash"] != protocol_hash:
                raise RuntimeError("Ledger contains a different protocol")
            key = (row["variant"], row["task_id"])
            if key in completed:
                raise RuntimeError(f"Duplicate ledger key {key}")
            completed.add(key)
    return completed


def append_jsonl(path: Path, row: dict) -> None:
    with path.open("a") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        fh.flush()
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def run(args: argparse.Namespace) -> None:
    load_dotenv(".env")
    old_manifest = json.loads(Path(args.week3_manifest).read_text())
    tasks, splits = load_dataset_and_splits(old_manifest["split_seed"])
    task_map = {task.task_id: task for task in tasks}
    split_ids = [task.task_id for split in splits.values() for task in split.records]
    if sorted(task_map) != sorted(split_ids):
        raise RuntimeError("Dataset split does not cover all task IDs")
    dataset_hash = hashlib.sha256("\n".join(sorted(task_map)).encode()).hexdigest()
    if dataset_hash != old_manifest["dataset_task_id_sha256"]:
        raise RuntimeError("Dataset differs from Week 3")

    provider = OllamaProvider(ProviderConfig(name="ollama", model_id=MODEL_ID,
        parameters=ProviderParams(temperature=0.0, max_tokens=1024, top_p=1.0)),
        timeout_seconds=args.timeout_seconds, max_retries=2)
    base = provider._base_url
    client = provider._client
    version_response = client.get(base + "/api/version")
    version_response.raise_for_status()
    version = version_response.json()["version"]
    tags_response = client.get(base + "/api/tags")
    tags_response.raise_for_status()
    matches = [m for m in tags_response.json()["models"] if m["name"] == MODEL_ID]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {MODEL_ID} in Ollama /api/tags")
    digest = matches[0]["digest"]
    show_response = client.post(base + "/api/show", json={"model": MODEL_ID})
    show_response.raise_for_status()
    if "thinking" not in show_response.json().get("capabilities", []):
        raise RuntimeError(f"{MODEL_ID} does not report thinking capability")

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "manifest.json"
    expected = frozen_manifest(splits, old_manifest, digest, version,
                               args.per_subject, args.seed, args.thinking_max_tokens)
    if len(expected["selected_train_ids"]) != 14:
        raise RuntimeError("Expected all 14 MMLU-Pro subjects")
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        if manifest["protocol_hash"] != expected["protocol_hash"]:
            raise RuntimeError("Manifest protocol changed; use a fresh output directory")
    else:
        manifest = expected
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    ledger = output / "predictions.jsonl"
    errors = output / "errors.jsonl"
    completed = load_completed(ledger, manifest["protocol_hash"])
    print(f"manifest={manifest_path} protocol={manifest['protocol_hash'][:16]} "
          f"model_digest={digest[:16]} subjects={len(manifest['selected_train_ids'])} "
          f"existing={len(completed)}", flush=True)
    new_count = 0
    for item_index in range(args.limit_per_subject):
        for subject, ids in manifest["selected_train_ids"].items():
            task_id = ids[item_index]
            task = task_map[task_id]
            prompt = format_prompt(task.to_online_view(), mode="direct")
            prompt_text = prompt.text + "\nRespond as JSON with only one key: answer."
            letters = [chr(ord("A") + i) for i in range(len(task.options))]
            response_format = {"type": "object", "properties": {
                "answer": {"type": "string", "enum": letters}}, "required": ["answer"]}
            for variant, settings in manifest["variants"].items():
                key = (variant, task_id)
                if key in completed:
                    continue
                try:
                    response = provider.complete(prompt_text, temperature=0.0,
                        max_tokens=settings["max_tokens"], top_p=1.0,
                        response_format=response_format, think=settings["think"])
                    try:
                        parsed = json.loads(response.content)
                        answer = parsed.get("answer")
                    except (json.JSONDecodeError, AttributeError):
                        answer = None
                    if answer not in letters:
                        answer = None
                    row = {"timestamp": utc_now(), "protocol_hash": manifest["protocol_hash"],
                           "variant": variant, "think": settings["think"],
                           "max_tokens": settings["max_tokens"], "model_id": MODEL_ID,
                           "model_digest": digest, "task_id": task_id,
                           "split": "train_calibration", "subject": subject,
                           "num_options": len(letters),
                           "prompt_hash": hashlib.sha256(prompt_text.encode()).hexdigest(),
                           "answer": answer, "valid_answer": answer is not None,
                           "raw_response": response.content,
                           "input_tokens": response.input_tokens,
                           "output_tokens": response.output_tokens,
                           "latency_ms": response.latency_ms,
                           **response.raw_response}
                    append_jsonl(ledger, row)
                    completed.add(key)
                    new_count += 1
                    print(f"progress {new_count} total={len(completed)} "
                          f"subject={subject} variant={variant} valid={answer is not None} "
                          f"tokens={response.output_tokens} latency_s={response.latency_ms/1000:.1f} "
                          f"done_reason={row['done_reason']} thinking={row['thinking_present']}",
                          flush=True)
                except Exception as exc:
                    append_jsonl(errors, {"timestamp": utc_now(), "protocol_hash": manifest["protocol_hash"],
                        "variant": variant, "task_id": task_id,
                        "error_type": type(exc).__name__, "error": str(exc)[:500]})
                    raise
                if args.max_new and new_count >= args.max_new:
                    print(f"paused_at_max_new={new_count}", flush=True)
                    return
    print(f"complete total={len(completed)}", flush=True)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output", default=str(DEFAULT_OUTPUT))
    p.add_argument("--week3-manifest", default="results/real_week3_json_v1/manifest.json")
    p.add_argument("--seed", type=int, default=314159)
    p.add_argument("--per-subject", type=int, default=30)
    p.add_argument("--limit-per-subject", type=int, default=5)
    p.add_argument("--thinking-max-tokens", type=int, default=8192)
    p.add_argument("--max-new", type=int, default=0)
    p.add_argument("--timeout-seconds", type=float, default=300.0)
    args = p.parse_args()
    if not 1 <= args.limit_per_subject <= args.per_subject:
        p.error("--limit-per-subject must be from 1 to --per-subject")
    run(args)


if __name__ == "__main__":
    main()
