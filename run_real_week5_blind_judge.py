#!/usr/bin/env python3
"""Freeze and collect a candidate-blind Modal judge on the same 280 questions.

The judge receives each MCQ once, without any submitted agent answer. Its
chosen letter is compared to agent answers only offline after collection.
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
from repguard.providers.ollama_ import OllamaProvider
from run_real_week3 import load_dataset_and_splits, utc_now
from run_real_week4_thinking import append_jsonl, canonical_hash
from run_real_week5_modal_judge import fetch_metadata


OUTPUT = Path("results/real_week5_blind_judge_v1")
SOURCE = Path("results/real_week5_modal_judge_v1/manifest.json")
MODEL_ID = "qwen3:14b"
PROMPT_VERSION = "candidate_blind_mcq_choice_v1"


def prompt_for(task) -> str:
    view = task.to_online_view()
    choices = "\n".join(f"{chr(65+i)}. {option}" for i, option in enumerate(view.options))
    return (
        "Solve this multiple-choice question independently. Choose exactly one "
        "best option. Return JSON only with chosen_letter and confidence from "
        "0 to 1.\n\n"
        f"Question: {view.question}\nOptions:\n{choices}"
    )


def response_schema(n_options: int) -> dict:
    return {"type": "object", "properties": {
        "chosen_letter": {"type": "string", "enum": [chr(65+i) for i in range(n_options)]},
        "confidence": {"type": "number"}},
        "required": ["chosen_letter", "confidence"]}


def build_manifest(source: dict, task_map: dict) -> dict:
    selected = source["selected_history_ids"]
    if len(selected) != 14 or any(len(ids) != 20 for ids in selected.values()):
        raise RuntimeError("Expected 20 questions in each of 14 subjects")
    cases = []
    seen = set()
    for subject, ids in selected.items():
        for task_id in ids:
            if task_id in seen or task_map[task_id].metadata.subject != subject:
                raise RuntimeError("Duplicate or mismatched selected task")
            seen.add(task_id)
            cases.append({"task_id": task_id, "subject": subject,
                          "prompt_hash": hashlib.sha256(
                              prompt_for(task_map[task_id]).encode()).hexdigest()})
    protocol = {
        "name": "week5_modal_candidate_blind_judge_v1",
        "dataset_id": source["dataset_id"],
        "dataset_task_id_sha256": source["dataset_task_id_sha256"],
        "split_seed": source["split_seed"],
        "source_judge_protocol_hash": source["protocol_hash"],
        "judge_model_id": MODEL_ID,
        "judge_model_digest": source["judge_model_digest"],
        "ollama_version": source["ollama_version"],
        "think": False,
        "temperature": 0.0,
        "top_p": 1.0,
        "max_output_tokens": 256,
        "prompt_version": PROMPT_VERSION,
        "selected_history_ids": selected,
        "candidate_blind_cases": cases,
    }
    return {"created_at": utc_now(), "protocol_hash": canonical_hash(protocol), **protocol}


def prepare(output: Path, source_path: Path) -> tuple[dict, dict]:
    source = json.loads(source_path.read_text())
    tasks, _ = load_dataset_and_splits(source["split_seed"])
    task_map = {task.task_id: task for task in tasks}
    digest = hashlib.sha256("\n".join(sorted(task_map)).encode()).hexdigest()
    if digest != source["dataset_task_id_sha256"]:
        raise RuntimeError("Local MMLU-Pro dataset differs from frozen source")
    expected = build_manifest(source, task_map)
    output.mkdir(parents=True, exist_ok=True)
    path = output / "manifest.json"
    if path.exists():
        manifest = json.loads(path.read_text())
        if manifest["protocol_hash"] != expected["protocol_hash"]:
            raise RuntimeError("Frozen blind judge manifest differs")
    else:
        manifest = expected
        path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return manifest, task_map


def completed_cases(path: Path, protocol_hash: str) -> set[str]:
    completed = set()
    if path.exists():
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            task_id = row["task_id"]
            if row["protocol_hash"] != protocol_hash or task_id in completed:
                raise RuntimeError("Blind judge ledger mismatch or duplicate")
            completed.add(task_id)
    return completed


def collect(args, manifest: dict, task_map: dict) -> None:
    load_dotenv(".env")
    provider = OllamaProvider(ProviderConfig(name="ollama", model_id=MODEL_ID,
        parameters=ProviderParams(temperature=0.0, max_tokens=256, top_p=1.0)),
        timeout_seconds=args.timeout_seconds, max_retries=2)
    base = provider._base_url
    if "modal.direct" not in base and "modal.run" not in base:
        raise RuntimeError("Blind judge must use Modal endpoint")
    client = provider._client
    version = fetch_metadata(client, "GET", base + "/api/version")
    version.raise_for_status()
    if version.json()["version"] != manifest["ollama_version"]:
        raise RuntimeError("Ollama version changed from frozen protocol")
    tags = fetch_metadata(client, "GET", base + "/api/tags")
    tags.raise_for_status()
    digests = [m["digest"] for m in tags.json()["models"]
               if m["name"] == MODEL_ID]
    if digests != [manifest["judge_model_digest"]]:
        raise RuntimeError("Model digest changed from frozen protocol")

    output = Path(args.output)
    ledger = output / "judgments.jsonl"
    errors = output / "errors.jsonl"
    done = completed_cases(ledger, manifest["protocol_hash"])
    selected = {tid for ids in manifest["selected_history_ids"].values()
                for tid in ids[:args.limit_per_subject]}
    cases = [case for case in manifest["candidate_blind_cases"]
             if case["task_id"] in selected]
    print(f"protocol={manifest['protocol_hash'][:16]} planned={len(cases)} "
          f"existing={len(done)}", flush=True)
    new_count = 0
    for case in cases:
        task_id = case["task_id"]
        if task_id in done:
            continue
        task = task_map[task_id]
        prompt = prompt_for(task)
        if hashlib.sha256(prompt.encode()).hexdigest() != case["prompt_hash"]:
            raise RuntimeError("Blind judge prompt changed")
        try:
            response = provider.complete(prompt, temperature=0.0, top_p=1.0,
                max_tokens=manifest["max_output_tokens"],
                response_format=response_schema(len(task.options)), think=False)
            try:
                parsed = json.loads(response.content)
            except json.JSONDecodeError:
                parsed = {}
            chosen = parsed.get("chosen_letter")
            confidence = parsed.get("confidence")
            letters = {chr(65+i) for i in range(len(task.options))}
            valid = (isinstance(chosen, str) and chosen in letters and
                     type(confidence) in (int, float)
                     and 0 <= confidence <= 1)
            row = {"timestamp": utc_now(), "protocol_hash": manifest["protocol_hash"],
                   **case, "judge_model_id": MODEL_ID,
                   "model_digest": manifest["judge_model_digest"],
                   "chosen_letter": chosen if valid else None,
                   "confidence": confidence if valid else None,
                   "valid_judgment": valid,
                   "raw_response": response.content,
                   "input_tokens": response.input_tokens,
                   "output_tokens": response.output_tokens,
                   "latency_ms": response.latency_ms,
                   **response.raw_response}
            append_jsonl(ledger, row)
            done.add(task_id)
            new_count += 1
            print(f"progress {new_count} total={len(done)} "
                  f"subject={case['subject']} valid={valid} "
                  f"latency_s={response.latency_ms/1000:.1f}", flush=True)
        except Exception as exc:
            append_jsonl(errors, {"timestamp": utc_now(),
                "protocol_hash": manifest["protocol_hash"],
                "task_id": task_id, "error_type": type(exc).__name__,
                "error": str(exc)[:500]})
            raise
        if args.max_new and new_count >= args.max_new:
            return
    print(f"complete total={len(done)}", flush=True)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output", default=str(OUTPUT))
    p.add_argument("--source", type=Path, default=SOURCE)
    p.add_argument("--limit-per-subject", type=int, default=1)
    p.add_argument("--timeout-seconds", type=float, default=180.0)
    p.add_argument("--max-new", type=int, default=0)
    p.add_argument("--collect", action="store_true")
    args = p.parse_args()
    if not 1 <= args.limit_per_subject <= 20:
        p.error("--limit-per-subject must be from 1 to 20")
    manifest, task_map = prepare(Path(args.output), args.source)
    print(f"frozen_blind_manifest={Path(args.output)/'manifest.json'} "
          f"questions={len(manifest['candidate_blind_cases'])} "
          f"protocol={manifest['protocol_hash'][:16]}", flush=True)
    if args.collect:
        collect(args, manifest, task_map)


if __name__ == "__main__":
    main()
