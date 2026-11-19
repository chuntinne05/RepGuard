#!/usr/bin/env python3
"""Collect real, per-question MMLU-Pro answers for the RepGuard study.

The manifest selects questions without looking at labels. Predictions contain no
ground truth; scoring and reputation experiments consume the manifest and the
benchmark separately. The JSONL ledger is append-only and resumable.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import random
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from repguard.audit.capability_audit import CapabilityAuditConfig
from repguard.data.mmlu_pro import load_mmlu_pro
from repguard.data.splits import create_splits
from repguard.harness.prompts import format_prompt
from repguard.seed import SeedManager
from repguard.providers.base import create_provider

DEFAULT_COUNTS = {"train_calibration": 100, "dev": 50, "test": 70}
DEFAULT_OUTPUT = Path("results/real_week3_json_v1")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_dataset_and_splits(seed: int):
    tasks = load_mmlu_pro(data_dir="data", dataset_id="TIGER-Lab/MMLU-Pro")
    splits = create_splits(tasks, SeedManager(seed))
    return tasks, dict(zip(("train_calibration", "dev", "test"), splits))


def make_manifest(tasks, splits, counts: dict[str, int], seed: int) -> dict:
    selected: dict[str, dict[str, list[str]]] = {}
    for split_name, split in splits.items():
        by_subject = defaultdict(list)
        for task in split.records:
            by_subject[task.metadata.subject].append(task.task_id)
        selected[split_name] = {}
        for subject in sorted(by_subject):
            ids = sorted(by_subject[subject])
            random.Random(f"{seed}:{split_name}:{subject}").shuffle(ids)
            selected[split_name][subject] = ids[: counts[split_name]]
    dataset_digest = hashlib.sha256(
        "\n".join(sorted(t.task_id for t in tasks)).encode()
    ).hexdigest()
    return {
        "created_at": utc_now(),
        "protocol": "ollama_json_enum_v1_temperature0_max_tokens64_think_false",
        "dataset_id": "TIGER-Lab/MMLU-Pro",
        "dataset_n": len(tasks),
        "dataset_task_id_sha256": dataset_digest,
        "split_seed": seed,
        "selection_seed": seed,
        "counts_requested_per_subject": counts,
        "selected": selected,
    }


def prepare_manifest(output: Path, counts: dict[str, int], seed: int):
    tasks, splits = load_dataset_and_splits(seed)
    manifest_path = output / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        expected = make_manifest(tasks, splits, counts, seed)
        for key in ("protocol", "dataset_id", "dataset_n", "dataset_task_id_sha256", "split_seed", "selected"):
            if manifest[key] != expected[key]:
                raise RuntimeError(f"Existing manifest differs in {key}; choose a fresh output directory")
    else:
        output.mkdir(parents=True, exist_ok=True)
        manifest = make_manifest(tasks, splits, counts, seed)
        manifest_path.write_text(json.dumps(manifest, indent=2))
    return manifest, {t.task_id: t for t in tasks}


def apply_test_extension(output: Path, manifest: dict, seed: int, create: bool) -> dict:
    extension_path = output / "test_extension.json"
    if create and not extension_path.exists():
        _, splits = load_dataset_and_splits(seed)
        extras = {}
        for subject, initial_ids in manifest["selected"]["test"].items():
            all_ids = sorted(t.task_id for t in splits["test"].records if t.metadata.subject == subject)
            initial = set(initial_ids)
            extras[subject] = [tid for tid in all_ids if tid not in initial]
        extension = {
            "created_at": utc_now(),
            "reason": "Confirm small provisional subject winner gaps and increase real-data precision after 70-per-subject pilot",
            "initial_manifest_sha256": hashlib.sha256((output / "manifest.json").read_bytes()).hexdigest(),
            "selected_extra_test_ids": extras,
        }
        extension_path.write_text(json.dumps(extension, indent=2))
    if extension_path.exists():
        extension = json.loads(extension_path.read_text())
        actual_sha = hashlib.sha256((output / "manifest.json").read_bytes()).hexdigest()
        if extension["initial_manifest_sha256"] != actual_sha:
            raise RuntimeError("Base manifest changed after test extension was created")
        for subject, ids in extension["selected_extra_test_ids"].items():
            if set(ids) & set(manifest["selected"]["test"][subject]):
                raise RuntimeError(f"Test extension overlaps initial test sample: {subject}")
            manifest["selected"]["test"][subject].extend(ids)
        print(f"test_extension_loaded extra_questions={sum(map(len, extension['selected_extra_test_ids'].values()))}", flush=True)
    return manifest


def existing_keys(path: Path) -> set[tuple[str, str]]:
    if not path.exists():
        return set()
    keys = set()
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        keys.add((row["agent"], row["task_id"]))
    return keys


def collect(args) -> None:
    load_dotenv(".env")
    output = Path(args.output)
    counts = {
        "train_calibration": args.n_history,
        "dev": args.n_calibration,
        "test": args.n_test,
    }
    manifest, task_map = prepare_manifest(output, counts, args.seed)
    manifest = apply_test_extension(output, manifest, args.seed, args.extend_test_all)
    cfg = CapabilityAuditConfig.from_yaml("configs/capability_audit.yaml")
    agents = [a for a in cfg.agents if not args.agents or a.name in args.agents]
    if not agents:
        raise RuntimeError("No configured agents matched --agents")
    ledger = output / "predictions.jsonl"
    errors = output / "errors.jsonl"
    completed = existing_keys(ledger)
    print(f"manifest={output / 'manifest.json'} subjects={len(manifest['selected']['test'])}", flush=True)
    print(f"existing_predictions={len(completed)} agents={[a.name for a in agents]}", flush=True)
    new_count = 0
    for agent in agents:
        provider = create_provider(agent.to_provider_config())
        pending = []
        for split_name in args.splits:
            by_subject = manifest["selected"][split_name]
            for item_index in range(max(map(len, by_subject.values()))):
                for subject, ids in by_subject.items():
                    if item_index >= len(ids):
                        continue
                    task_id = ids[item_index]
                    if (agent.name, task_id) not in completed:
                        pending.append((split_name, subject, task_id))
        print(f"agent={agent.name} model={agent.model_id} pending={len(pending)}", flush=True)
        for i, (split_name, subject, task_id) in enumerate(pending, 1):
            task = task_map[task_id]
            prompt = format_prompt(task.to_online_view(), mode="direct")
            prompt_text = prompt.text + "\nRespond as JSON with only one key: answer."
            prompt_hash = hashlib.sha256(prompt_text.encode()).hexdigest()[:16]
            letters = [chr(ord("A") + j) for j in range(len(task.options))]
            response_format = {
                "type": "object",
                "properties": {"answer": {"type": "string", "enum": letters}},
                "required": ["answer"],
            }
            start = time.monotonic()
            try:
                response = provider.complete(
                    prompt_text,
                    temperature=0.0,
                    max_tokens=64,
                    top_p=1.0,
                    response_format=response_format,
                )
                structured = json.loads(response.content)
                answer = structured.get("answer")
                if answer not in letters:
                    raise ValueError(f"Model returned invalid choice: {answer!r}")
                row = {
                    "timestamp": utc_now(),
                    "agent": agent.name,
                    "model_id": agent.model_id,
                    "task_id": task_id,
                    "split": split_name,
                    "subject": subject,
                    "num_options": len(task.options),
                    "prompt_hash": prompt_hash,
                    "answer": answer,
                    "parse_method": "json_schema_enum",
                    "parse_confidence": 1.0,
                    "raw_response": response.content,
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "latency_ms": response.latency_ms,
                }
                with ledger.open("a") as fh:
                    fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                    fh.flush()
                    fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
                completed.add((agent.name, task_id))
                new_count += 1
            except Exception as exc:
                with errors.open("a") as fh:
                    fh.write(json.dumps({
                        "timestamp": utc_now(), "agent": agent.name,
                        "task_id": task_id, "error_type": type(exc).__name__,
                        "error": str(exc)[:500],
                    }) + "\n")
                print(f"ERROR agent={agent.name} task={task_id}: {type(exc).__name__}: {str(exc)[:120]}", flush=True)
                if args.stop_on_error:
                    raise
            if i == 1 or i % args.report_every == 0:
                print(
                    f"progress agent={agent.name} {i}/{len(pending)} "
                    f"split={split_name} subject={subject} elapsed={time.monotonic()-start:.2f}s "
                    f"total_ledger={len(completed)}",
                    flush=True,
                )
            if args.max_new and new_count >= args.max_new:
                print(f"stopped_at_max_new={new_count}; resume with same command", flush=True)
                return
    print(f"complete ledger={ledger} predictions={len(completed)}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n-history", type=int, default=100)
    parser.add_argument("--n-calibration", type=int, default=50)
    parser.add_argument("--n-test", type=int, default=70)
    parser.add_argument("--agents", nargs="*", default=[])
    parser.add_argument(
        "--splits", nargs="+", choices=("train_calibration", "dev", "test"),
        default=["test", "train_calibration", "dev"],
    )
    parser.add_argument("--report-every", type=int, default=25)
    parser.add_argument("--max-new", type=int, default=0)
    parser.add_argument("--extend-test-all", action="store_true")
    parser.add_argument("--stop-on-error", action="store_true")
    args = parser.parse_args()
    collect(args)


if __name__ == "__main__":
    main()
