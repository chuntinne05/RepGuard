#!/usr/bin/env python3
"""Collect real Modal-hosted Ollama judgments of Week 3 agent answers.

The judge sees an MCQ and one submitted answer, never its gold label or the
agent identity. Identical submitted answers on one task share one judge call.
The manifest is frozen before calls; the ledger is append-only and resumable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv
import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from repguard.config import ProviderConfig, ProviderParams
from repguard.providers.ollama_ import OllamaProvider
from run_real_week3 import load_dataset_and_splits, utc_now
from run_real_week4_thinking import append_jsonl, canonical_hash


OUTPUT = Path("results/real_week5_modal_judge_v1")
WEEK3 = Path("results/real_week3_json_v1")
MODEL_ID = "qwen3:14b"
AGENTS = ("qwen3-8b", "gemma2", "llama3-8b", "qwen3-0.6b")
SCHEMA_VERSION = "candidate_correct_boolean_confidence_chosen_letter_v1"
PROMPT_VERSION = "independent_mcq_candidate_judge_v1"


def prompt_for(task, candidate: str) -> str:
    view = task.to_online_view()
    choices = "\n".join(f"{chr(65+i)}. {option}" for i, option in enumerate(view.options))
    return (
        "You are an independent evaluator of a multiple-choice answer. "
        "Solve the question independently before judging the submitted answer. "
        "Do not assume the submitted answer is correct. Choose exactly one best option. "
        "Then return whether the submitted answer is correct, your own chosen option, "
        "and confidence from 0 to 1. Return JSON only.\n\n"
        f"Question: {view.question}\nOptions:\n{choices}\n"
        f"Submitted answer: {candidate}"
    )


def response_schema(n_options: int) -> dict:
    return {"type": "object", "properties": {
        "verdict": {"type": "boolean"},
        "chosen_letter": {"type": "string", "enum": [chr(65+i) for i in range(n_options)]},
        "confidence": {"type": "number"}},
        "required": ["verdict", "chosen_letter", "confidence"]}


def select_history(old: dict, *, per_subject: int, seed: int) -> dict[str, list[str]]:
    selected = {}
    for subject, ids in sorted(old["selected"]["train_calibration"].items()):
        candidates = sorted(ids)
        random.Random(f"{seed}:week5:judge:{subject}").shuffle(candidates)
        if len(candidates) < per_subject:
            raise RuntimeError(f"Only {len(candidates)} history questions in {subject}")
        selected[subject] = candidates[:per_subject]
    if len(selected) != 14:
        raise RuntimeError("Expected all 14 MMLU-Pro subjects")
    return selected


def build_manifest(old: dict, week3_rows: list[dict], task_map: dict,
                   *, per_subject: int, seed: int,
                   model_digest: str, server_version: str) -> dict:
    selected = select_history(old, per_subject=per_subject, seed=seed)
    predictions = {(row["task_id"], row["agent"]): row["answer"]
                   for row in week3_rows if row["split"] == "train_calibration"}
    cases = []
    for subject, ids in selected.items():
        for task_id in ids:
            answer_agents = defaultdict(list)
            for agent in AGENTS:
                key = (task_id, agent)
                if key not in predictions:
                    raise RuntimeError(f"Missing real Week 3 answer: {key}")
                answer = predictions[key]
                if answer not in {chr(65+i) for i in range(len(task_map[task_id].options))}:
                    raise RuntimeError(f"Invalid historical answer: {key}")
                answer_agents[answer].append(agent)
            for answer in sorted(answer_agents):
                cases.append({"task_id": task_id, "subject": subject,
                              "candidate_answer": answer,
                              "agents": answer_agents[answer],
                              "prompt_hash": hashlib.sha256(
                                  prompt_for(task_map[task_id], answer).encode()).hexdigest()})
    protocol = {
        "name": "week5_real_modal_ollama_judge_v1",
        "dataset_id": old["dataset_id"],
        "dataset_task_id_sha256": old["dataset_task_id_sha256"],
        "split_seed": old["split_seed"],
        "selection_seed": seed,
        "selected_history_ids": selected,
        "judge_model_id": MODEL_ID,
        "judge_model_digest": model_digest,
        "ollama_version": server_version,
        "think": False,
        "temperature": 0.0,
        "top_p": 1.0,
        "max_output_tokens": 256,
        "prompt_version": PROMPT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "candidate_cases": cases,
    }
    return {"created_at": utc_now(), "protocol_hash": canonical_hash(protocol), **protocol}


def prepare(output: Path, *, per_subject: int, seed: int,
            provider: OllamaProvider):
    if "modal.direct" not in provider._base_url and "modal.run" not in provider._base_url:
        raise RuntimeError("Judge must run on the configured Modal endpoint")
    client = provider._client
    base = provider._base_url
    version_response = fetch_metadata(client, "GET", base + "/api/version")
    version_response.raise_for_status()
    server_version = version_response.json()["version"]
    tags_response = fetch_metadata(client, "GET", base + "/api/tags")
    tags_response.raise_for_status()
    matches = [item for item in tags_response.json()["models"]
               if item["name"] == MODEL_ID]
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one {MODEL_ID} on Modal")
    model_digest = matches[0]["digest"]
    old = json.loads((WEEK3 / "manifest.json").read_text())
    tasks, _ = load_dataset_and_splits(old["split_seed"])
    task_map = {task.task_id: task for task in tasks}
    digest = hashlib.sha256("\n".join(sorted(task_map)).encode()).hexdigest()
    if digest != old["dataset_task_id_sha256"]:
        raise RuntimeError("Local MMLU-Pro dataset differs from Week 3")
    week3_rows = [json.loads(line) for line in (WEEK3 / "predictions.jsonl").read_text().splitlines()
                  if line.strip()]
    expected = build_manifest(old, week3_rows, task_map,
                              per_subject=per_subject, seed=seed,
                              model_digest=model_digest,
                              server_version=server_version)
    output.mkdir(parents=True, exist_ok=True)
    path = output / "manifest.json"
    if path.exists():
        manifest = json.loads(path.read_text())
        if manifest["protocol_hash"] != expected["protocol_hash"]:
            raise RuntimeError("Frozen judge manifest differs; choose a new output directory")
    else:
        manifest = expected
        path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return manifest, task_map


def fetch_metadata(client: httpx.Client, method: str, url: str) -> httpx.Response:
    """Wait through transient Modal startup errors before checking frozen metadata."""
    for attempt in range(6):
        try:
            response = client.request(method, url)
            if response.status_code not in {429, 500, 502, 503, 504}:
                return response
            if attempt == 5:
                response.raise_for_status()
        except httpx.RequestError:
            if attempt == 5:
                raise
        delay = min(30, 5 * (attempt + 1))
        print(f"modal_metadata_retry attempt={attempt+1} delay_s={delay}", flush=True)
        time.sleep(delay)
    raise RuntimeError("Modal metadata retry exhausted")


def read_done(path: Path, protocol_hash: str) -> set[tuple[str, str]]:
    done = set()
    if path.exists():
        for line in path.read_text().splitlines():
            if not line:
                continue
            row = json.loads(line)
            if row["protocol_hash"] != protocol_hash:
                raise RuntimeError("Judge ledger contains a different protocol")
            key = (row["task_id"], row["candidate_answer"])
            if key in done:
                raise RuntimeError(f"Duplicate judge case: {key}")
            done.add(key)
    return done


def call_judge(provider: OllamaProvider, *, prompt: str, n_options: int,
               manifest: dict) -> dict:
    response = provider.complete(prompt,
        temperature=manifest["temperature"],
        top_p=manifest["top_p"],
        max_tokens=manifest["max_output_tokens"],
        response_format=response_schema(n_options), think=manifest["think"])
    return {"raw_response": response.content,
            "model_digest": manifest["judge_model_digest"],
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "latency_ms": response.latency_ms,
            **response.raw_response}


def collect(args, manifest: dict, task_map: dict, provider: OllamaProvider) -> None:
    output = Path(args.output)
    ledger = output / "judgments.jsonl"
    errors = output / "errors.jsonl"
    done = read_done(ledger, manifest["protocol_hash"])
    selected = {tid for ids in manifest["selected_history_ids"].values()
                for tid in ids[:args.limit_per_subject]}
    cases = [case for case in manifest["candidate_cases"] if case["task_id"] in selected]
    print(f"protocol={manifest['protocol_hash'][:16]} cases={len(cases)} "
          f"existing={len(done)}", flush=True)
    new_count = 0
    for case in cases:
        key = (case["task_id"], case["candidate_answer"])
        if key in done:
            continue
        task = task_map[case["task_id"]]
        prompt = prompt_for(task, case["candidate_answer"])
        if hashlib.sha256(prompt.encode()).hexdigest() != case["prompt_hash"]:
            raise RuntimeError("Judge prompt hash changed")
        try:
            response = call_judge(provider, prompt=prompt,
                                  n_options=len(task.options), manifest=manifest)
            try:
                parsed = json.loads(response["raw_response"])
            except json.JSONDecodeError:
                parsed = {}
            verdict = parsed.get("verdict")
            chosen = parsed.get("chosen_letter")
            confidence = parsed.get("confidence")
            letters = {chr(65+i) for i in range(len(task.options))}
            valid = (isinstance(verdict, bool) and chosen in letters and
                     type(confidence) in (int, float) and 0 <= confidence <= 1)
            row = {"timestamp": utc_now(), "protocol_hash": manifest["protocol_hash"],
                   **case, "judge_model_id": manifest["judge_model_id"],
                   "verdict": verdict if valid else None,
                   "chosen_letter": chosen if valid else None,
                   "confidence": confidence if valid else None,
                   "valid_judgment": valid, **response}
            append_jsonl(ledger, row)
            done.add(key)
            new_count += 1
            print(f"progress {new_count} total={len(done)} subject={case['subject']} "
                  f"valid={valid} tokens={response['output_tokens']} "
                  f"latency_s={response['latency_ms']/1000:.1f}", flush=True)
        except Exception as exc:
            append_jsonl(errors, {"timestamp": utc_now(),
                "protocol_hash": manifest["protocol_hash"],
                "task_id": case["task_id"],
                "candidate_answer": case["candidate_answer"],
                "error_type": type(exc).__name__, "error": str(exc)[:500]})
            raise
        if args.max_new and new_count >= args.max_new:
            return
    print(f"complete total={len(done)}", flush=True)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output", default=str(OUTPUT))
    p.add_argument("--seed", type=int, default=1618033)
    p.add_argument("--per-subject", type=int, default=20)
    p.add_argument("--limit-per-subject", type=int, default=1)
    p.add_argument("--timeout-seconds", type=float, default=120.0)
    p.add_argument("--max-new", type=int, default=0)
    p.add_argument("--collect", action="store_true")
    args = p.parse_args()
    if not 1 <= args.limit_per_subject <= args.per_subject:
        p.error("--limit-per-subject must be from 1 to --per-subject")
    load_dotenv(".env")
    provider = OllamaProvider(ProviderConfig(name="ollama", model_id=MODEL_ID,
        parameters=ProviderParams(temperature=0.0, max_tokens=256, top_p=1.0)),
        timeout_seconds=args.timeout_seconds, max_retries=2)
    manifest, task_map = prepare(Path(args.output),
                                 per_subject=args.per_subject, seed=args.seed,
                                 provider=provider)
    print(f"frozen_judge_manifest={Path(args.output)/'manifest.json'} "
          f"questions={sum(map(len,manifest['selected_history_ids'].values()))} "
          f"unique_cases={len(manifest['candidate_cases'])} "
          f"protocol={manifest['protocol_hash'][:16]}", flush=True)
    if args.collect:
        collect(args, manifest, task_map, provider)


if __name__ == "__main__":
    main()
