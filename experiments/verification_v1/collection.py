"""Checkpointed bounded collection shared by local API and isolated cloud runs.

The invoker only receives prompts and a model configuration, never gold.
"""
from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from .core import build_prompt, parse_answer, request_id, text_from_response
from .prepare import digest, write

WORKFLOWS = ("A", "B", "AA", "BB", "AB", "BA")


def verify_packet(plan, public):
    if digest(public) != plan["public_sha256"]:
        raise ValueError("Public input hash changed")
    ids = [r["id"] for r in public["items"]]
    if len(ids) != len(set(ids)) or len(ids) != plan["items"]:
        raise ValueError("Case membership mismatch")
    if plan["max_corpus_calls"] != len(ids) * len(WORKFLOWS):
        raise ValueError("Call cap mismatch")
    for row in public["items"]:
        build_prompt(row["case"])


def collect(plan, public, directory, invoke, commit=lambda: None):
    verify_packet(plan, public)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    write(directory / "plan.json", plan)
    write(directory / "public_pilot.json", public)
    records = {}
    for p in (directory / "responses").glob("*.json"):
        r = json.loads(p.read_text())
        records[(r["item_id"], r["workflow"])] = r
    total = plan["max_corpus_calls"]
    first_groups = list(dict.fromkeys(r["group"] for r in public["items"]))[:2]
    first = [r for r in public["items"] if r["group"] in first_groups]
    rest = [r for r in public["items"] if r["group"] not in first_groups]

    def status(state):
        value = {"state": state, "completed": len(records), "cap": total,
                 "http_errors": sum(not r.get("transport_ok", False) for r in records.values()),
                 "plan_id": plan["plan_id"], "utc": datetime.now(timezone.utc).isoformat()}
        write(directory / "status.json", value)
        commit()
        print(json.dumps(value), flush=True)
        return value

    def one(row, workflow):
        key = (row["id"], workflow)
        if key in records:
            return records[key]
        prior = None
        if len(workflow) == 2:
            initial_record = records[(row["id"], workflow[0])]
            if not initial_record.get("transport_ok"):
                raise RuntimeError("Cannot review an initial answer with unknown transport outcome")
            prior = {"raw_text": initial_record["raw_text"]}
        prompt = build_prompt(row["case"], prior)
        rid = request_id(plan["plan_id"], row["id"], workflow)
        started = directory / "attempts" / (rid + ".json")
        if started.exists():
            raise RuntimeError("Unresolved started request; do not blindly retry generation")
        record = {"request_id": rid, "item_id": row["id"], "group": row["group"],
                  "workflow": workflow, "model_role": workflow[-1], "plan_id": plan["plan_id"],
                  "prompt": prompt, "prompt_sha256": digest(prompt),
                  "parent_request_id": request_id(plan["plan_id"], row["id"], workflow[0])
                  if len(workflow) == 2 else None,
                  "created_utc": datetime.now(timezone.utc).isoformat(), "generation_attempts": 1}
        write(started, {"request_id": rid, "state": "started", "prompt_sha256": digest(prompt)})
        commit()
        begin = time.monotonic()
        try:
            result = invoke(workflow[-1], prompt)
            record.update(result)
            record["transport_ok"] = True
            record["raw_text"] = text_from_response(result["response"], result["provider"])
            record["parsed"] = parse_answer(record["raw_text"], row["case"])
        except Exception as error:
            record.update(transport_ok=False, error_type=type(error).__name__,
                          error=str(error)[:1000], parsed={"valid": False, "label": None})
        record["wall_seconds"] = time.monotonic() - begin
        record["record_sha256"] = digest(record)
        write(directory / "responses" / (rid + ".json"), record)
        records[key] = record
        commit()
        return record

    status("collecting")
    with ThreadPoolExecutor(max_workers=plan["concurrency"]) as pool:
        for stage, items in (("operational_screen", first), ("pilot_remainder", rest)):
            for workflows in (("A", "B"), ("AA", "BB", "AB", "BA")):
                jobs = [(r, w) for r in items for w in workflows]
                # Bounded chunks avoid queuing the entire study after an error.
                for offset in range(0, len(jobs), plan["concurrency"]):
                    chunk = jobs[offset:offset + plan["concurrency"]]
                    futures = [pool.submit(one, r, w) for r, w in chunk]
                    for f in futures:
                        f.result()
                    current = status(stage)
                    if current["http_errors"]:
                        return status("STOP_transport_error_review_required")
            if stage == "operational_screen":
                observed = [records[(r["id"], w)] for r in first for w in WORKFLOWS]
                validity = sum(x["parsed"]["valid"] for x in observed) / len(observed)
                write(directory / "operational_gate.json", {"validity": validity,
                                                            "passed": validity >= .95,
                                                            "gold_accessed": False})
                commit()
                if validity < .95:
                    return status("STOP_operational_validity")
    return status("completed_ready_for_offline_evaluation")
