#!/usr/bin/env python3
"""Resumable real Modal/Ollama inference on frozen development IDs only.

The sealed holdout is never included in this manifest or request loop. The
append-only ledger stores no gold labels. Model digests, prompts and inference
settings are frozen before collecting any responses.
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

OUTPUT = Path("results/real_dev_pool_v1")
FROZEN = Path("results/real_next_study_v1/frozen_splits.json")
VARIANTS = {
    "qwen3_8b_direct": {"model_id": "qwen3:8b", "think": False, "max_tokens": 64},
    "qwen3_14b_direct": {"model_id": "qwen3:14b", "think": False, "max_tokens": 64},
    "gemma2_direct": {"model_id": "gemma2:latest", "think": False, "max_tokens": 64},
    "qwen3_06b_direct": {"model_id": "qwen3:0.6b", "think": False, "max_tokens": 64},
    "qwen3_8b_thinking": {"model_id": "qwen3:8b", "think": True, "max_tokens": 8192},
}


def preflight(timeout: float):
    load_dotenv(".env")
    provider = OllamaProvider(ProviderConfig(
        name="ollama", model_id="qwen3:8b",
        parameters=ProviderParams(temperature=0.0, max_tokens=64, top_p=1.0)),
        timeout_seconds=timeout, max_retries=2)
    version_response = provider._client.get(provider._base_url + "/api/version")
    version_response.raise_for_status()
    tags_response = provider._client.get(provider._base_url + "/api/tags")
    tags_response.raise_for_status()
    inventory = {row["name"]: row["digest"] for row in tags_response.json()["models"]}
    needed = {settings["model_id"] for settings in VARIANTS.values()}
    if needed - inventory.keys():
        raise RuntimeError(f"Models missing on Ollama: {sorted(needed - inventory.keys())}")
    show = provider._client.post(provider._base_url + "/api/show",
                                 json={"model": "qwen3:8b"})
    show.raise_for_status()
    if "thinking" not in show.json().get("capabilities", []):
        raise RuntimeError("Qwen3 8B does not report thinking capability")
    return provider, version_response.json()["version"], {
        model: inventory[model] for model in sorted(needed)}


def make_manifest(frozen: dict, version: str, digests: dict[str, str]) -> dict:
    selected = frozen["selected"]["development"]
    ids = [task_id for subject_ids in selected.values() for task_id in subject_ids]
    if len(selected) != 14 or len(ids) != 560 or len(set(ids)) != 560:
        raise RuntimeError("Expected 560 unique development IDs across 14 subjects")
    if set(ids) & {task_id for subject_ids in frozen["selected"]["holdout"].values()
                   for task_id in subject_ids}:
        raise RuntimeError("Development overlaps sealed holdout")
    protocol = {
        "name": "real_dev_pool_v1",
        "source_protocol_hash": frozen["protocol_hash"],
        "dataset_id": frozen["dataset_id"],
        "dataset_task_id_sha256": frozen["dataset_task_id_sha256"],
        "ollama_version": version,
        "model_digests": digests,
        "variants": VARIANTS,
        "prompt_version": "week3_direct_json_enum_v1",
        "temperature": 0.0,
        "top_p": 1.0,
        "json_schema": "answer_enum_available_letters_v1",
        "selected_development_ids": selected,
        "holdout_read_for_inference": False,
    }
    return {"created_at": utc_now(), "protocol_hash": canonical_hash(protocol), **protocol}


def completed_keys(path: Path, manifest: dict) -> set[tuple[str, str]]:
    keys = set()
    if not path.exists():
        return keys
    selected = {task_id for ids in manifest["selected_development_ids"].values()
                for task_id in ids}
    for line in path.open():
        if not line.strip():
            continue
        row = json.loads(line)
        variant, task_id = row["variant"], row["task_id"]
        if (row["protocol_hash"] != manifest["protocol_hash"] or
            variant not in VARIANTS or task_id not in selected or
            row["model_digest"] != manifest["model_digests"][row["model_id"]]):
            raise RuntimeError("Existing development ledger has an incompatible row")
        key = variant, task_id
        if key in keys:
            raise RuntimeError(f"Duplicate development response: {key}")
        keys.add(key)
    return keys


def run(args: argparse.Namespace) -> None:
    frozen = json.loads(FROZEN.read_text())
    source_protocol = {key: value for key, value in frozen.items()
                       if key not in ("created_at", "protocol_hash")}
    if canonical_hash(source_protocol) != frozen["protocol_hash"]:
        raise RuntimeError("Frozen split protocol hash mismatch")
    provider, version, digests = preflight(args.timeout_seconds)
    expected = make_manifest(frozen, version, digests)
    args.output.mkdir(parents=True, exist_ok=True)
    manifest_path = args.output / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        if manifest["protocol_hash"] != expected["protocol_hash"]:
            raise RuntimeError("Development manifest differs from current protocol")
    else:
        manifest = expected
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"protocol={manifest['protocol_hash']} variants={list(VARIANTS)} ",
          "development_questions=560", flush=True)
    if not args.collect:
        return

    tasks, splits = load_dataset_and_splits(frozen["original_split_seed"])
    task_map = {task.task_id: task for task in tasks}
    digest = hashlib.sha256("\n".join(sorted(task_map)).encode()).hexdigest()
    if digest != manifest["dataset_task_id_sha256"]:
        raise RuntimeError("Local MMLU-Pro dataset differs from frozen split")
    train_ids = {task.task_id for task in splits["train_calibration"].records}
    if any(task_id not in train_ids for ids in manifest["selected_development_ids"].values()
           for task_id in ids):
        raise RuntimeError("Development task outside frozen train/calibration split")
    ledger = args.output / "predictions.jsonl"
    errors = args.output / "errors.jsonl"
    completed = completed_keys(ledger, manifest)
    new_count = 0
    for variant, settings in VARIANTS.items():
        if args.variants and variant not in args.variants:
            continue
        model = OllamaProvider(ProviderConfig(
            name="ollama", model_id=settings["model_id"],
            parameters=ProviderParams(temperature=0.0,
                                      max_tokens=settings["max_tokens"], top_p=1.0)),
            base_url=provider._base_url, timeout_seconds=args.timeout_seconds,
            max_retries=2)
        for index in range(args.limit_per_subject):
            for subject, ids in manifest["selected_development_ids"].items():
                task_id = ids[index]
                if (variant, task_id) in completed:
                    continue
                task = task_map[task_id]
                prompt = format_prompt(task.to_online_view(), mode="direct").text
                prompt += "\nRespond as JSON with only one key: answer."
                letters = [chr(ord("A") + i) for i in range(len(task.options))]
                schema = {"type": "object", "properties": {
                    "answer": {"type": "string", "enum": letters}}, "required": ["answer"]}
                try:
                    response = model.complete(prompt, temperature=0.0,
                                              max_tokens=settings["max_tokens"],
                                              top_p=1.0, response_format=schema,
                                              think=settings["think"])
                    try:
                        answer = json.loads(response.content).get("answer")
                    except (json.JSONDecodeError, AttributeError):
                        answer = None
                    if answer not in letters:
                        answer = None
                    row = {"timestamp": utc_now(), "protocol_hash": manifest["protocol_hash"],
                           "variant": variant, "model_id": settings["model_id"],
                           "model_digest": digests[settings["model_id"]],
                           "task_id": task_id, "split": "development", "subject": subject,
                           "think": settings["think"], "max_tokens": settings["max_tokens"],
                           "num_options": len(letters),
                           "prompt_hash": hashlib.sha256(prompt.encode()).hexdigest(),
                           "answer": answer, "valid_answer": answer is not None,
                           "raw_response": response.content,
                           "input_tokens": response.input_tokens,
                           "output_tokens": response.output_tokens,
                           "latency_ms": response.latency_ms, **response.raw_response}
                    append_jsonl(ledger, row)
                    completed.add((variant, task_id))
                    new_count += 1
                    print(f"progress variant={variant} new={new_count} "
                          f"total={len(completed)}/2800 subject={subject} "
                          f"valid={answer is not None} tokens={response.output_tokens}",
                          flush=True)
                except Exception as exc:
                    append_jsonl(errors, {"timestamp": utc_now(),
                                          "protocol_hash": manifest["protocol_hash"],
                                          "variant": variant, "task_id": task_id,
                                          "error_type": type(exc).__name__,
                                          "error": str(exc)[:500]})
                    raise
                if args.max_new and new_count >= args.max_new:
                    print(f"paused_at_max_new={new_count}", flush=True)
                    return
    print(f"complete total={len(completed)}/2800", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--collect", action="store_true")
    parser.add_argument("--variants", nargs="*", choices=VARIANTS, default=[])
    parser.add_argument("--limit-per-subject", type=int, default=1)
    parser.add_argument("--max-new", type=int, default=0)
    parser.add_argument("--timeout-seconds", type=float, default=300)
    args = parser.parse_args()
    if not 1 <= args.limit_per_subject <= 40:
        parser.error("--limit-per-subject must be 1..40")
    run(args)


if __name__ == "__main__":
    main()
