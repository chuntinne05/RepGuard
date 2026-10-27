#!/usr/bin/env python3
"""Collect real direct answers on Week 4's paired questions for pool screening.

The existing Qwen3 8B direct/thinking ledger is reused by task ID. This runner
only collects new models. The manifest freezes model digests, task IDs and
prompt settings; the append-only ledger is resumable and contains no gold.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from repguard.config import ProviderConfig, ProviderParams
from repguard.harness.prompts import format_prompt
from repguard.providers.ollama_ import OllamaProvider
from run_real_week3 import load_dataset_and_splits, utc_now
from run_real_week4_thinking import append_jsonl, canonical_hash


OUTPUT = Path("results/real_pool_overlap_v1")
SOURCE = Path("results/real_week4_thinking_pilot_v3/manifest.json")
MODELS = ("gemma2:latest", "llama3:8b", "qwen3:14b")


def preflight(timeout_seconds: float) -> tuple[OllamaProvider, str, dict[str, str]]:
    load_dotenv(".env")
    provider = OllamaProvider(ProviderConfig(
        name="ollama", model_id=MODELS[0],
        parameters=ProviderParams(temperature=0.0, max_tokens=64, top_p=1.0)),
        timeout_seconds=timeout_seconds, max_retries=2)
    base = provider._base_url
    response = provider._client.get(base + "/api/version")
    response.raise_for_status()
    version = response.json()["version"]
    response = provider._client.get(base + "/api/tags")
    response.raise_for_status()
    inventory = {row["name"]: row["digest"] for row in response.json()["models"]}
    if any(model not in inventory for model in MODELS):
        raise RuntimeError("The frozen candidate pool is not available on Ollama")
    return provider, version, {model: inventory[model] for model in MODELS}


def manifest_for(source: dict, server_version: str, model_digests: dict[str, str]) -> dict:
    protocol = {
        "name": "real_pool_overlap_on_qwen3_thinking_screen_v1",
        "source_protocol_hash": source["protocol_hash"],
        "dataset_id": source["dataset_id"],
        "dataset_task_id_sha256": source["dataset_task_id_sha256"],
        "split_seed": source["split_seed"],
        "model_digests": model_digests,
        "ollama_version": server_version,
        "prompt_version": source["prompt_version"],
        "temperature": 0.0,
        "top_p": 1.0,
        "think": False,
        "max_tokens": 64,
        "json_schema": source["json_schema"],
        "selected_train_ids": source["selected_train_ids"],
    }
    return {"created_at": utc_now(), "protocol_hash": canonical_hash(protocol), **protocol}


def load_completed(path: Path, manifest: dict) -> set[tuple[str, str]]:
    completed = set()
    if path.exists():
        for line in path.open():
            if not line.strip():
                continue
            row = json.loads(line)
            if row["protocol_hash"] != manifest["protocol_hash"]:
                raise RuntimeError("Mixed protocols in pool ledger")
            key = row["model_id"], row["task_id"]
            if key in completed:
                raise RuntimeError(f"Duplicate pool answer {key}")
            completed.add(key)
    return completed


def run(args: argparse.Namespace) -> None:
    source = json.loads(SOURCE.read_text())
    if len(source["selected_train_ids"]) != 14 or any(
        len(ids) != 30 for ids in source["selected_train_ids"].values()
    ):
        raise RuntimeError("Source screen must contain 30 IDs in each of 14 subjects")
    preflight_provider, version, digests = preflight(args.timeout_seconds)
    if version != source["ollama_version"]:
        raise RuntimeError("Ollama server version differs from source study")
    frozen = manifest_for(source, version, digests)
    args.output.mkdir(parents=True, exist_ok=True)
    path = args.output / "manifest.json"
    if path.exists():
        manifest = json.loads(path.read_text())
        if manifest["protocol_hash"] != frozen["protocol_hash"]:
            raise RuntimeError("Existing pool manifest differs from current protocol")
    else:
        manifest = frozen
        path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(f"protocol={manifest['protocol_hash']} models={list(digests)} "
          f"questions={sum(map(len, manifest['selected_train_ids'].values()))}", flush=True)
    if not args.collect:
        return

    tasks, splits = load_dataset_and_splits(source["split_seed"])
    task_map = {task.task_id: task for task in tasks}
    digest = hashlib.sha256("\n".join(sorted(task_map)).encode()).hexdigest()
    if digest != source["dataset_task_id_sha256"]:
        raise RuntimeError("Local MMLU-Pro task IDs changed")
    train_ids = {task.task_id for task in splits["train_calibration"].records}
    if any(tid not in train_ids for ids in manifest["selected_train_ids"].values() for tid in ids):
        raise RuntimeError("Pool selection is not within original train/calibration split")
    ledger = args.output / "predictions.jsonl"
    errors = args.output / "errors.jsonl"
    completed = load_completed(ledger, manifest)
    new_count = 0
    for model in MODELS:
        if args.models and model not in args.models:
            continue
        provider = OllamaProvider(ProviderConfig(
            name="ollama", model_id=model,
            parameters=ProviderParams(temperature=0.0, max_tokens=64, top_p=1.0)),
            base_url=preflight_provider._base_url,
            timeout_seconds=args.timeout_seconds, max_retries=2)
        for index in range(args.limit_per_subject):
            for subject, ids in manifest["selected_train_ids"].items():
                task_id = ids[index]
                key = model, task_id
                if key in completed:
                    continue
                task = task_map[task_id]
                prompt = format_prompt(task.to_online_view(), mode="direct").text
                prompt += "\nRespond as JSON with only one key: answer."
                letters = [chr(ord("A") + i) for i in range(len(task.options))]
                schema = {"type": "object", "properties": {
                    "answer": {"type": "string", "enum": letters}}, "required": ["answer"]}
                try:
                    response = provider.complete(prompt, temperature=0.0,
                                                 max_tokens=64, top_p=1.0,
                                                 response_format=schema, think=False)
                    try:
                        answer = json.loads(response.content).get("answer")
                    except (json.JSONDecodeError, AttributeError):
                        answer = None
                    if answer not in letters:
                        answer = None
                    row = {"timestamp": utc_now(), "protocol_hash": manifest["protocol_hash"],
                           "model_id": model, "model_digest": digests[model],
                           "task_id": task_id, "split": "train_calibration",
                           "subject": subject, "think": False, "max_tokens": 64,
                           "num_options": len(letters),
                           "prompt_hash": hashlib.sha256(prompt.encode()).hexdigest(),
                           "answer": answer, "valid_answer": answer is not None,
                           "raw_response": response.content,
                           "input_tokens": response.input_tokens,
                           "output_tokens": response.output_tokens,
                           "latency_ms": response.latency_ms, **response.raw_response}
                    append_jsonl(ledger, row)
                    completed.add(key)
                    new_count += 1
                    print(f"progress model={model} new={new_count} total={len(completed)} "
                          f"subject={subject} valid={answer is not None} "
                          f"latency_s={response.latency_ms/1000:.2f}", flush=True)
                except Exception as exc:
                    append_jsonl(errors, {"timestamp": utc_now(),
                        "protocol_hash": manifest["protocol_hash"],
                        "model_id": model, "task_id": task_id,
                        "error_type": type(exc).__name__, "error": str(exc)[:500]})
                    raise
                if args.max_new and new_count >= args.max_new:
                    print(f"paused_at_max_new={new_count}", flush=True)
                    return
    print(f"complete total={len(completed)}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--collect", action="store_true")
    parser.add_argument("--models", nargs="*", choices=MODELS, default=[])
    parser.add_argument("--limit-per-subject", type=int, default=1)
    parser.add_argument("--max-new", type=int, default=0)
    parser.add_argument("--timeout-seconds", type=float, default=300)
    args = parser.parse_args()
    if not 1 <= args.limit_per_subject <= 30:
        parser.error("--limit-per-subject must be 1..30")
    run(args)


if __name__ == "__main__":
    main()
