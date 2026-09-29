#!/usr/bin/env python3
"""Freeze and collect an independent real MMLU-Pro dev validation set.

Run without --collect to freeze 20 unused dev task IDs per subject before
examining Week 4's full screen. --collect performs real Ollama calls and writes
an append-only answer ledger with the same protocol as Week 4 thinking v3.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv

from repguard.config import ProviderConfig, ProviderParams
from repguard.harness.prompts import format_prompt
from repguard.providers.ollama_ import OllamaProvider
from run_real_week3 import load_dataset_and_splits, utc_now
from run_real_week4_thinking import append_jsonl, canonical_hash, load_completed


DEFAULT_OUTPUT = Path("results/real_week5_validation_v1")
WEEK3_MANIFEST = Path("results/real_week3_json_v1/manifest.json")
WEEK4_MANIFEST = Path("results/real_week4_thinking_pilot_v3/manifest.json")


def select_unused_dev(splits, old_manifest: dict, *, per_subject: int,
                      seed: int) -> dict[str, list[str]]:
    old_ids = {tid for ids in old_manifest["selected"]["dev"].values() for tid in ids}
    by_subject = defaultdict(list)
    for task in splits["dev"].records:
        if task.task_id not in old_ids:
            by_subject[task.metadata.subject].append(task.task_id)
    selected = {}
    for subject in sorted(by_subject):
        ids = sorted(by_subject[subject])
        random.Random(f"{seed}:week5:dev:{subject}").shuffle(ids)
        if len(ids) < per_subject:
            raise RuntimeError(f"Only {len(ids)} unused dev questions in {subject}")
        selected[subject] = ids[:per_subject]
    return selected


def make_manifest(old_manifest: dict, week4_manifest: dict, splits,
                  *, per_subject: int, seed: int) -> dict:
    selected = select_unused_dev(splits, old_manifest,
                                 per_subject=per_subject, seed=seed)
    if len(selected) != 14 or any(len(ids) != per_subject for ids in selected.values()):
        raise RuntimeError("Expected equal-size selection in all 14 subjects")
    protocol = {
        "name": "week5_qwen3_paired_thinking_dev_v1",
        "dataset_id": old_manifest["dataset_id"],
        "dataset_task_id_sha256": old_manifest["dataset_task_id_sha256"],
        "split_seed": old_manifest["split_seed"],
        "selection_seed": seed,
        "selection_split": "dev",
        "source_week4_protocol_hash": week4_manifest["protocol_hash"],
        "model_id": week4_manifest["model_id"],
        "model_digest": week4_manifest["model_digest"],
        "ollama_version": week4_manifest["ollama_version"],
        "prompt_version": week4_manifest["prompt_version"],
        "temperature": week4_manifest["temperature"],
        "top_p": week4_manifest["top_p"],
        "json_schema": week4_manifest["json_schema"],
        "variants": week4_manifest["variants"],
        "selected_dev_ids": selected,
    }
    return {"created_at": utc_now(), "protocol_hash": canonical_hash(protocol), **protocol}


def prepare(output: Path, *, per_subject: int, seed: int):
    old = json.loads(WEEK3_MANIFEST.read_text())
    week4 = json.loads(WEEK4_MANIFEST.read_text())
    tasks, splits = load_dataset_and_splits(old["split_seed"])
    actual_digest = hashlib.sha256("\n".join(sorted(t.task_id for t in tasks)).encode()).hexdigest()
    if actual_digest != old["dataset_task_id_sha256"]:
        raise RuntimeError("Local MMLU-Pro task IDs differ from Week 3")
    expected = make_manifest(old, week4, splits, per_subject=per_subject, seed=seed)
    output.mkdir(parents=True, exist_ok=True)
    path = output / "manifest.json"
    if path.exists():
        manifest = json.loads(path.read_text())
        if manifest["protocol_hash"] != expected["protocol_hash"]:
            raise RuntimeError("Frozen validation manifest differs; use a fresh directory")
    else:
        manifest = expected
        path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return manifest, {task.task_id: task for task in tasks}


def collect(args, manifest: dict, task_map: dict) -> None:
    load_dotenv(".env")
    provider = OllamaProvider(ProviderConfig(
        name="ollama", model_id=manifest["model_id"],
        parameters=ProviderParams(temperature=0.0, max_tokens=8192, top_p=1.0)),
        timeout_seconds=args.timeout_seconds, max_retries=2)
    base = provider._base_url
    client = provider._client
    version = client.get(base + "/api/version")
    version.raise_for_status()
    if version.json()["version"] != manifest["ollama_version"]:
        raise RuntimeError("Ollama server version changed from frozen protocol")
    tags = client.get(base + "/api/tags")
    tags.raise_for_status()
    digests = [m["digest"] for m in tags.json()["models"]
               if m["name"] == manifest["model_id"]]
    if digests != [manifest["model_digest"]]:
        raise RuntimeError("Qwen3 model digest changed from frozen protocol")
    show = client.post(base + "/api/show", json={"model": manifest["model_id"]})
    show.raise_for_status()
    if "thinking" not in show.json().get("capabilities", []):
        raise RuntimeError("Model no longer reports thinking capability")

    output = Path(args.output)
    ledger = output / "predictions.jsonl"
    errors = output / "errors.jsonl"
    done = load_completed(ledger, manifest["protocol_hash"])
    print(f"manifest={output/'manifest.json'} protocol={manifest['protocol_hash'][:16]} "
          f"existing={len(done)}", flush=True)
    new_count = 0
    for i in range(args.limit_per_subject):
        for subject, ids in manifest["selected_dev_ids"].items():
            task_id = ids[i]
            task = task_map[task_id]
            prompt_text = (format_prompt(task.to_online_view(), mode="direct").text +
                           "\nRespond as JSON with only one key: answer.")
            letters = [chr(ord("A") + j) for j in range(len(task.options))]
            response_format = {"type": "object", "properties": {
                "answer": {"type": "string", "enum": letters}}, "required": ["answer"]}
            for variant, settings in manifest["variants"].items():
                key = (variant, task_id)
                if key in done:
                    continue
                try:
                    response = provider.complete(prompt_text, temperature=0.0,
                        max_tokens=settings["max_tokens"], top_p=1.0,
                        response_format=response_format, think=settings["think"])
                    try:
                        answer = json.loads(response.content).get("answer")
                    except (json.JSONDecodeError, AttributeError):
                        answer = None
                    if answer not in letters:
                        answer = None
                    row = {"timestamp": utc_now(), "protocol_hash": manifest["protocol_hash"],
                           "variant": variant, "think": settings["think"],
                           "max_tokens": settings["max_tokens"],
                           "model_id": manifest["model_id"],
                           "model_digest": manifest["model_digest"],
                           "task_id": task_id, "split": "dev", "subject": subject,
                           "num_options": len(letters),
                           "prompt_hash": hashlib.sha256(prompt_text.encode()).hexdigest(),
                           "answer": answer, "valid_answer": answer is not None,
                           "raw_response": response.content,
                           "input_tokens": response.input_tokens,
                           "output_tokens": response.output_tokens,
                           "latency_ms": response.latency_ms,
                           **response.raw_response}
                    append_jsonl(ledger, row)
                    done.add(key)
                    new_count += 1
                    print(f"progress {new_count} total={len(done)} subject={subject} "
                          f"variant={variant} valid={answer is not None} "
                          f"tokens={response.output_tokens} "
                          f"done_reason={row['done_reason']}", flush=True)
                except Exception as exc:
                    append_jsonl(errors, {"timestamp": utc_now(),
                        "protocol_hash": manifest["protocol_hash"],
                        "variant": variant, "task_id": task_id,
                        "error_type": type(exc).__name__, "error": str(exc)[:500]})
                    raise
                if args.max_new and new_count >= args.max_new:
                    return
    print(f"complete total={len(done)}", flush=True)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output", default=str(DEFAULT_OUTPUT))
    p.add_argument("--seed", type=int, default=271828)
    p.add_argument("--per-subject", type=int, default=20)
    p.add_argument("--limit-per-subject", type=int, default=20)
    p.add_argument("--timeout-seconds", type=float, default=600.0)
    p.add_argument("--max-new", type=int, default=0)
    p.add_argument("--collect", action="store_true",
                   help="Send real requests to Ollama; default only freezes dev IDs")
    args = p.parse_args()
    if not 1 <= args.limit_per_subject <= args.per_subject:
        p.error("--limit-per-subject must be from 1 to --per-subject")
    manifest, task_map = prepare(Path(args.output),
                                 per_subject=args.per_subject, seed=args.seed)
    print(f"frozen_validation_manifest={Path(args.output)/'manifest.json'} "
          f"questions={sum(map(len, manifest['selected_dev_ids'].values()))} "
          f"protocol={manifest['protocol_hash'][:16]}", flush=True)
    if args.collect:
        collect(args, manifest, task_map)


if __name__ == "__main__":
    main()
