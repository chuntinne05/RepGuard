#!/usr/bin/env python3
"""Resumable real Qwen8 thinking diagnostic with an explicit 8K context window.

Five IDs per MMLU-Pro development subject are frozen by hash without reading
answers. This is a paired protocol diagnostic against the completed 4K-context
run; it does not touch the sealed holdout or replace the main 560-question run.
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
from run_real_dev_pool import FROZEN, preflight
from run_real_week3 import load_dataset_and_splits, utc_now
from run_real_week4_thinking import append_jsonl, canonical_hash

SELECTION = Path("configs/real_dev_context_pilot_v1.json")
OUTPUT = Path("results/real_dev_context_pilot_v1")
MODEL = "qwen3:8b"
NUM_CTX = 8192
MAX_TOKENS = 8192


def selected_ids(frozen: dict) -> dict[str, list[str]]:
    dev = frozen["selected"]["development"]
    if len(dev) != 14 or any(len(ids) != 40 for ids in dev.values()):
        raise RuntimeError("Expected 14 subjects with 40 frozen development IDs each")
    return {subject: sorted(ids, key=lambda task_id: hashlib.sha256(
        ("context_v1:" + task_id).encode()).hexdigest())[:5]
            for subject, ids in sorted(dev.items())}


def freeze() -> dict:
    frozen = json.loads(FROZEN.read_text())
    selected = selected_ids(frozen)
    all_ids = [task_id for ids in selected.values() for task_id in ids]
    holdout = {task_id for ids in frozen["selected"]["holdout"].values()
               for task_id in ids}
    if len(all_ids) != 70 or len(set(all_ids)) != 70 or set(all_ids) & holdout:
        raise RuntimeError("Pilot selection is not 70 unique non-holdout IDs")
    protocol = {"name": "real_dev_context_pilot_v1", "source_protocol_hash": frozen["protocol_hash"],
                "selection_rule": "sha256(context_v1:task_id), first 5 of each frozen dev subject",
                "selected_development_ids": selected, "n": 70,
                "model_id": MODEL, "think": True, "max_tokens": MAX_TOKENS,
                "num_ctx": NUM_CTX, "temperature": 0.0, "top_p": 1.0,
                "prompt_version": "week3_direct_json_enum_v1",
                "holdout_ids_used_only_for_disjointness_check": True,
                "holdout_inference": False}
    payload = {"created_at": utc_now(), "protocol_hash": canonical_hash(protocol), **protocol}
    if SELECTION.exists():
        old = json.loads(SELECTION.read_text())
        if old["protocol_hash"] != payload["protocol_hash"]:
            raise RuntimeError("Frozen context pilot selection changed")
        return old
    SELECTION.write_text(json.dumps(payload, indent=2) + "\n")
    return payload


def run(args: argparse.Namespace) -> None:
    selection = freeze()
    if not args.collect:
        print(json.dumps({"protocol_hash": selection["protocol_hash"],
                          "n": selection["n"], "subjects": len(selection["selected_development_ids"])},
                         indent=2))
        return
    load_dotenv(".env")
    provider, version, digests = preflight(args.timeout_seconds)
    manifest_protocol = {key: value for key, value in selection.items()
                         if key not in ("created_at", "protocol_hash")}
    manifest_protocol.update({"selection_protocol_hash": selection["protocol_hash"],
                              "ollama_version": version, "model_digest": digests[MODEL]})
    manifest = {"created_at": utc_now(), "protocol_hash": canonical_hash(manifest_protocol),
                **manifest_protocol}
    OUTPUT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT / "manifest.json"
    if path.exists():
        previous = json.loads(path.read_text())
        if previous["protocol_hash"] != manifest["protocol_hash"]:
            raise RuntimeError("Context pilot manifest changed")
        manifest = previous
    else:
        path.write_text(json.dumps(manifest, indent=2) + "\n")
    tasks, splits = load_dataset_and_splits(json.loads(FROZEN.read_text())["original_split_seed"])
    task_map = {task.task_id: task for task in tasks}
    train_ids = {task.task_id for task in splits["train_calibration"].records}
    selected = selection["selected_development_ids"]
    if any(task_id not in train_ids for ids in selected.values() for task_id in ids):
        raise RuntimeError("Context pilot task outside train/calibration split")
    model = OllamaProvider(ProviderConfig(name="ollama", model_id=MODEL,
        parameters=ProviderParams(temperature=0.0, max_tokens=MAX_TOKENS, top_p=1.0)),
        base_url=provider._base_url, timeout_seconds=args.timeout_seconds, max_retries=2)
    ledger = OUTPUT / "predictions.jsonl"
    completed: set[str] = set()
    if ledger.exists():
        for line in ledger.open():
            if not line.strip():
                continue
            row = json.loads(line)
            task_id = row["task_id"]
            if (row["protocol_hash"] != manifest["protocol_hash"] or
                row["model_digest"] != manifest["model_digest"] or
                task_id not in {item for ids in selected.values() for item in ids} or
                task_id in completed):
                raise RuntimeError("Incompatible or duplicate context pilot row")
            completed.add(task_id)
    new = 0
    for index in range(5):
        for subject, ids in selected.items():
            task_id = ids[index]
            if task_id in completed:
                continue
            task = task_map[task_id]
            prompt = format_prompt(task.to_online_view(), mode="direct").text
            prompt += "\nRespond as JSON with only one key: answer."
            letters = [chr(ord("A") + i) for i in range(len(task.options))]
            schema = {"type": "object", "properties": {"answer": {
                "type": "string", "enum": letters}}, "required": ["answer"]}
            try:
                response = model.complete(prompt, temperature=0.0, max_tokens=MAX_TOKENS,
                                          top_p=1.0, response_format=schema, think=True,
                                          num_ctx=NUM_CTX)
                try:
                    answer = json.loads(response.content).get("answer")
                except (json.JSONDecodeError, AttributeError):
                    answer = None
                if answer not in letters:
                    answer = None
                row = {"timestamp": utc_now(), "protocol_hash": manifest["protocol_hash"],
                       "selection_protocol_hash": selection["protocol_hash"],
                       "task_id": task_id, "subject": subject, "model_id": MODEL,
                       "model_digest": manifest["model_digest"], "think": True,
                       "num_ctx": NUM_CTX, "max_tokens": MAX_TOKENS,
                       "prompt_hash": hashlib.sha256(prompt.encode()).hexdigest(),
                       "answer": answer, "valid_answer": answer is not None,
                       "raw_response": response.content, "input_tokens": response.input_tokens,
                       "output_tokens": response.output_tokens,
                       "latency_ms": response.latency_ms, **response.raw_response}
                append_jsonl(ledger, row)
                completed.add(task_id)
                new += 1
                print(f"context_pilot progress={len(completed)}/70 new={new} "
                      f"subject={subject} valid={answer is not None} "
                      f"tokens={response.output_tokens}", flush=True)
            except Exception as exc:
                append_jsonl(OUTPUT / "errors.jsonl", {"timestamp": utc_now(),
                    "protocol_hash": manifest["protocol_hash"], "task_id": task_id,
                    "error_type": type(exc).__name__, "error": str(exc)[:500]})
                raise
            if args.max_new and new >= args.max_new:
                return
    print("context_pilot complete=70/70", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--collect", action="store_true")
    parser.add_argument("--max-new", type=int, default=0)
    parser.add_argument("--timeout-seconds", type=float, default=600)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
