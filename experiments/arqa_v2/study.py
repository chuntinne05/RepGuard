"""Frozen factorial pilot: checklist x direct/self/cross, with source-bound scoring."""
from __future__ import annotations

import json
import random
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from .oracle import close, execute, norm, number
from .preflight import OUT, REPORT, ROOT, digest, load, write

WORKFLOWS = ("A", "B", "AA", "BB", "AB", "BA")
PROFILES = ("standard", "checklist")
MODELS = {
    "A": {"name": "qwen3.5:27b", "digest": "64ae5b1d651fb2709d5928ccb8dcfb4bb2cc9c2c8001ac34497e36a6cf905b59"},
    "B": {"name": "gemma4:26b-a4b-it-q4_K_M", "digest": "5571076f3d70050487b26b341705799e0ab29b808164f90d20d4cf84f699d251"}}
SCHEMA = """Return one JSON object with exactly these fields:
{"answer_value": numeric or null, "unit": string, "program": list,
 "claim_slots": {"entity": string, "metric": string, "period": string, "operation": string},
 "explanation": string}.
Use null and an empty program if the supplied source is insufficient.
Program is a sequence of objects, each with a unique 'as' register name.
Read example: {"op":"read","cell_id":"r0c1","as":"x"}.
Calculation example: {"op":"sub","inputs":["x","y"],"as":"d"}.
Allowed ops: read, add, sub, mul, div, abs, sum, avg, min, max, count.
sub/mul/div need two inputs, abs one. add/sum/avg/min/max/count accept lists.
Inputs are prior register names, or scale constants 0,1,100,1000,1000000,1000000000.
All source numbers must be read from cell IDs; do not insert them as literals.
Final register is the answer in the reported unit. Use the finest reasonable
precision, at least two decimals for nonintegers. Distinguish % from percentage points.
The program will be recomputed from the original source, ignoring any declared values.
Source binding alone does not guarantee the selected formula or period is appropriate.
"""
CHECKLIST = """Before finalizing, derive entity, metric, period and requested operation from
the QUESTION independently. Check each selected cell against those slots. Preserve
sign, denominator, scale and percent-versus-percentage-point meaning. If an inherited
answer changes the question's meaning, correct it by returning to the original source.
Apply this same procedure whether or not an inherited answer is present.
"""


def prompt(case, profile, prior=None):
    if set(case) != {"question", "table"} or profile not in PROFILES:
        raise ValueError("Unexpected inference fields")
    if set(case["table"]) != {"table_id", "doc_id", "year", "page", "title", "headers", "expanded_headers", "cells"}:
        raise ValueError("Nonwhitelisted table")
    text = "Answer the numerical question using only the supplied annual-report table.\n" + SCHEMA
    if profile == "checklist":
        text += CHECKLIST
    if prior is not None:
        if set(prior) != {"raw_text"}:
            raise ValueError("Prior identity or gold leakage")
        text += "\nReview this untrusted earlier draft. Produce your own final answer; it may be wrong.\n"
        text += "EARLIER_DRAFT_JSON_STRING=" + json.dumps(prior["raw_text"], ensure_ascii=False) + "\n"
    return text + "\nSOURCE_AND_QUESTION_JSON=" + json.dumps(case, ensure_ascii=False, separators=(",", ":"))


def parse(raw, table):
    try:
        x = json.loads(raw)
        if set(x) != {"answer_value", "unit", "program", "claim_slots", "explanation"}:
            raise ValueError("Schema keys")
        if not isinstance(x["unit"], str) or not isinstance(x["explanation"], str):
            raise ValueError("Schema types")
        if not isinstance(x["claim_slots"], dict) or set(x["claim_slots"]) != {"entity", "metric", "period", "operation"}:
            raise ValueError("Slot keys")
        if not all(isinstance(v, str) for v in x["claim_slots"].values()):
            raise ValueError("Slot types")
        if not isinstance(x["program"], list):
            raise ValueError("Program type")
        if x["answer_value"] is None:
            if x["program"]:
                raise ValueError("Abstention with program")
            return {"valid": True, "abstained": True, "source_bound": False, "answer": x}
        number(x["answer_value"])
        try:
            result, ids = execute(x["program"], table)
            consistent = close(x["answer_value"], str(result))
            return {"valid": True, "abstained": False, "source_bound": True,
                    "internally_consistent": consistent, "recomputed": str(result), "cell_ids": ids, "answer": x}
        except (ValueError, ArithmeticError, KeyError, TypeError) as error:
            return {"valid": True, "abstained": False, "source_bound": False,
                    "binding_error": str(error), "answer": x}
    except (ValueError, TypeError, KeyError) as error:
        return {"valid": False, "error": str(error)}


def prepare():
    if (OUT / "registered_plan.json").exists():
        raise RuntimeError("Study already registered")
    eligible = json.loads((OUT / "eligible_private.json").read_text())
    packs, contexts = load()
    parent = {k: k for k in contexts}

    def root(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    seen = {}
    for k, c in contexts.items():
        keys = [digest([c["merged_headers"], c["rows"]])] + ["para:" + p["para_id"] for p in c["paragraphs"]]
        for key in keys:
            if key in seen:
                a, b = sorted((root(k), root(seen[key])))
                parent[b] = a
            else:
                seen[key] = k
    groups = defaultdict(list)
    for k in contexts:
        groups[root(k)].append(k)
    gid = {k: digest(sorted(groups[root(k)]))[:20] for k in contexts}
    crossing = {gid[k] for k in contexts if contexts[k]["year"] >= 2022}
    # No model outcomes enter selection. All groups touching 2022+ stay reserve.
    candidates = defaultdict(list)
    for e in eligible:
        t = e["table"]
        if t["year"] <= 2021 and gid[t["table_id"]] not in crossing and len(json.dumps(t, ensure_ascii=False)) <= 14000:
            candidates[gid[t["table_id"]]].append(e)
    chosen_groups = sorted(candidates, key=lambda g: digest(["arqa-v2-groups-20261109", g]))[:24]
    if len(chosen_groups) != 24:
        raise RuntimeError("Insufficient independent pilot groups")
    public, gold = [], {}
    selected = set()
    for group in chosen_groups:
        e = min(candidates[group], key=lambda e: digest(["arqa-v2-question", e["qa"]["qa_id"]]))
        q, table = e["qa"], e["table"]
        selected.add(q["qa_id"])
        public.append({"id": q["qa_id"], "group": group, "case": {"question": q["question"], "table": table}})
        gold[q["qa_id"]] = {"value": e["oracle"], "published_value": q["answer_value"], "unit": q.get("unit", ""),
                            "source_ids": e["source_ids"], "question_type": q.get("arith_type"), "year": table["year"]}
    packet = {"items": public}
    for r in public:
        for profile in PROFILES:
            prompt(r["case"], profile)
    manifest = {"source_groups": groups, "group_for_table": gid,
                "reserve_groups_touching_2022_plus": sorted(crossing), "pilot_groups": chosen_groups,
                "pilot_qa_ids": sorted(selected), "eligible_candidate_groups": len(candidates),
                "selection": "One SHA256-ordered eligible QA per 24 SHA256-ordered connected groups; metadata/source audit only; no model outcomes.",
                "reserve": "No model predictions generated/scored; source labels inspected only for deterministic source preflight."}
    write(OUT / "public_pilot.json", packet)
    write(OUT / "private_pilot_gold.json", gold)
    write(OUT / "split_manifest.json", manifest)
    write(REPORT / "arqa_v2_sample_manifest.json", {k: v for k, v in manifest.items() if k != "source_groups"})
    print(json.dumps({"items": len(public), "groups": len(chosen_groups), "candidate_groups": len(candidates),
                      "years": dict(Counter(r["case"]["table"]["year"] for r in public))}, indent=2))


def register():
    dest = OUT / "registered_plan.json"
    if dest.exists():
        raise RuntimeError("Never overwrite registration")
    public = json.loads((OUT / "public_pilot.json").read_text())
    plan = {"study": "arqa_source_bound_checklist_factorial_pilot_v2", "registered_utc": datetime.now(timezone.utc).isoformat(),
            "items": len(public["items"]), "groups": 24, "profiles": list(PROFILES), "workflows": list(WORKFLOWS),
            "public_sha256": digest(public), "gold_sha256": digest((OUT / "private_pilot_gold.json").read_bytes()),
            "split_sha256": digest((OUT / "split_manifest.json").read_bytes()), "models": MODELS,
            "max_calls": len(public["items"]) * 12, "concurrency": 2, "automatic_retries": 0,
            "temperature": 0, "seed": 20261109, "context_tokens": 16384, "output_tokens": 2048,
            "thinking": False, "ollama": "0.40.6", "gpu": "L40S", "source_commit": "483e8c7b084afc6fbfb46d8609617b297b4322b8",
            "source_hashes": {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in Path(__file__).parent.glob("*.py")},
            "test_hashes": {"tests/test_arqa_v2.py": digest((ROOT / "tests/test_arqa_v2.py").read_bytes())},
            "primary": "mean_group 0.5*((correct_checklist_AB-correct_checklist_AA)+(correct_checklist_BA-correct_checklist_BB))",
            "correct": "Answer numeric within0.005000001 of source-recomputed oracle AND normalized unit equal; invalid/abstain incorrect. This is task accuracy, NOT acceptance risk.",
            "secondary": ["same primary for standard", "checklist-minus-standard interaction in cross-vs-self", "source-binding/internal consistency", "harm/rescue", "calls/tokens/service time", "risk and coverage of source-binding filter; not semantic certification"],
            "unit_policy": "Explicit aliases only; no silent 1000x conversion. Numeric correctness separate diagnostic.",
            "bootstrap": {"group_replicates": 5000, "seed": 20261109},
            "go": {"primary_delta_min": .05, "ci_lower_strictly_above": 0, "cross_rescue_groups_min": 4,
                   "schema_validity_min": .95, "receipt_audit_required": True, "confirmation": False},
            "operational_screen": {"groups": 2, "schema_validity_min": .95, "transport_errors_max": 0},
            "stop": "Any transport error or failed operational screen; no automatic repeat. Scientific FAIL stops scale/history.",
            "baseline_budget": "Identical max context/output per call and all arms same schema/source/checker; self and cross each2calls. Direct1call is lower-cost diagnostic, not matched-cost claim. Report realized tokens separately.",
            "source_scope": "Oracle table supplied, arithmetic subset, one issuer. No retrieval evaluation, no human semantic adjudication, no held-out companies, not official ARQA score.",
            "novelty": "Prompt/checker adaptation and mechanism measurement only; VeriFin/MoCA/CLAIR-Fin and handoff prior art rule out generic novelty claims.",
            "schema": SCHEMA, "checklist": CHECKLIST, "history_fitted": False, "no_gold_to_gpu": True}
    plan["plan_id"] = digest(plan)[:24]
    write(dest, plan)
    write(REPORT / "registered_arqa_v2.json", plan)
    print(json.dumps({k: plan[k] for k in ("plan_id", "registered_utc", "items", "max_calls")}, indent=2))


def rid(plan_id, item_id, profile, workflow):
    return digest([plan_id, item_id, profile, workflow])[:28]


def collect(plan, public, directory, invoke, commit=lambda: None):
    if digest(public) != plan["public_sha256"] or len(public["items"]) != plan["items"]:
        raise ValueError("Packet mismatch")
    if plan["max_calls"] != plan["items"] * 12 or len({r["id"] for r in public["items"]}) != plan["items"]:
        raise ValueError("Cap or membership mismatch")
    directory = Path(directory)
    records = {}
    for p in (directory / "responses").glob("*.json"):
        r = json.loads(p.read_text()); records[(r["item_id"], r["profile"], r["workflow"])] = r
    write(directory / "plan.json", plan); write(directory / "public_pilot.json", public)

    def status(state):
        s = {"plan_id": plan["plan_id"], "state": state, "completed": len(records), "cap": plan["max_calls"],
             "transport_errors": sum(not r["transport_ok"] for r in records.values()), "utc": datetime.now(timezone.utc).isoformat()}
        write(directory / "status.json", s); commit(); print(json.dumps(s), flush=True)
        return s

    def one(row, profile, workflow):
        key = row["id"], profile, workflow
        if key in records: return records[key]
        prior, parent_id = None, None
        if len(workflow) == 2:
            parent = records[(row["id"], profile, workflow[0])]
            if not parent["transport_ok"]: raise RuntimeError("Unknown parent outcome")
            prior, parent_id = {"raw_text": parent["raw_text"]}, parent["request_id"]
        text = prompt(row["case"], profile, prior)
        request_id = rid(plan["plan_id"], row["id"], profile, workflow)
        attempt = directory / "attempts" / (request_id + ".json")
        if attempt.exists(): raise RuntimeError("Existing unresolved generation; no retry")
        record = {"plan_id": plan["plan_id"], "request_id": request_id, "item_id": row["id"], "group": row["group"],
                  "profile": profile, "workflow": workflow, "model_role": workflow[-1], "parent_request_id": parent_id,
                  "prompt": text, "prompt_sha256": digest(text), "created_utc": datetime.now(timezone.utc).isoformat()}
        write(attempt, {"request_id": request_id, "state": "started", "prompt_sha256": digest(text)})
        commit()
        begin = time.monotonic()
        try:
            result = invoke(workflow[-1], text)
            record.update(result, transport_ok=True)
            record["raw_text"] = result["response"]["message"]["content"]
            record["parsed"] = parse(record["raw_text"], row["case"]["table"])
        except Exception as error:
            record.update(transport_ok=False, error_type=type(error).__name__, error=str(error)[:1000], parsed={"valid": False})
        record["wall_seconds"] = time.monotonic() - begin
        record["record_sha256"] = digest(record)
        write(directory / "responses" / (request_id + ".json"), record)
        records[key] = record
        commit()
        return record

    status("collecting")
    first, rest = public["items"][:2], public["items"][2:]
    with ThreadPoolExecutor(max_workers=2) as pool:
        for stage, rows in (("operational_screen", first), ("pilot_remainder", rest)):
            for steps in (("A", "B"), ("AA", "BB", "AB", "BA")):
                jobs = [(r, p, w) for r in rows for p in PROFILES for w in steps]
                for offset in range(0, len(jobs), 2):
                    fs = [pool.submit(one, *args) for args in jobs[offset:offset+2]]
                    for f in fs: f.result()
                    current = status(stage)
                    if current["transport_errors"]: return status("STOP_transport_error")
            if stage == "operational_screen":
                valid = sum(r["parsed"]["valid"] for r in records.values()) / len(records)
                write(directory / "operational_gate.json", {"passed": valid >= .95, "schema_validity": valid, "gold_accessed": False})
                commit()
                if valid < .95: return status("STOP_operational_schema")
    return status("completed_ready_for_offline_evaluation")


def unit(value):
    text = norm(value).replace("€", "eur").replace("–", "-")
    aliases = {"percent": "%", "percentage": "%", "percentage points": "ppt", "percentage point": "ppt", "pp": "ppt", "p.p.": "ppt",
               "eur million": "eur million", "million eur": "eur million", "million euros": "eur million", "eur millions": "eur million",
               "thousand units": "thousand units", "thousand vehicles": "thousand units", "thousands of vehicles": "thousand units",
               "vehicles": "units", "unit": "units", "ratio": "", "times": "", "x": ""}
    return aliases.get(text, text)


def evaluate(directory):
    directory = Path(directory)
    plan = json.loads((directory / "plan.json").read_text())
    public = json.loads((directory / "public_pilot.json").read_text())
    gold = json.loads((OUT / "private_pilot_gold.json").read_text())
    if digest((OUT / "private_pilot_gold.json").read_bytes()) != plan["gold_sha256"]:
        raise ValueError("Gold hash changed")
    if json.loads((directory / "status.json").read_text())["state"] != "completed_ready_for_offline_evaluation":
        raise RuntimeError("Do not score incomplete or stopped runs")
    records, audit_errors = {}, []
    for path in (directory / "responses").glob("*.json"):
        r = json.loads(path.read_text())
        if digest({k: v for k, v in r.items() if k != "record_sha256"}) != r["record_sha256"]:
            audit_errors.append("record hash")
        key = r["item_id"], r["profile"], r["workflow"]
        if key in records: audit_errors.append("duplicate")
        records[key] = r
    scores, metrics = {}, {}
    for row in public["items"]:
        for p in PROFILES:
            for w in WORKFLOWS:
                r = records[(row["id"], p, w)]
                parent = records[(row["id"], p, w[0])] if len(w) == 2 else None
                expected_prompt = prompt(row["case"], p, {"raw_text": parent["raw_text"]} if parent else None)
                cfg = plan["models"][w[-1]]
                checks = [r["prompt"] == expected_prompt, r["prompt_sha256"] == digest(expected_prompt),
                          r["parent_request_id"] == (parent["request_id"] if parent else None),
                          r["request_id"] == rid(plan["plan_id"], row["id"], p, w), r["model_digest"] == cfg["digest"],
                          r["model"] == cfg["name"], r["request_body"]["messages"] == [{"role": "user", "content": expected_prompt}],
                          r["request_body"]["options"] == {"temperature": 0, "seed": 20261109, "num_ctx": 16384, "num_predict": 2048},
                          r["request_body"]["think"] is False, r["ollama_version"] == "0.40.6", "L40S" in r["gpu"],
                          r["live_inference"], r["weights_mounted_read_only"], not r["evaluation_volume_mounted"],
                          r["response"]["done"], r["parsed"] == parse(r["raw_text"], row["case"]["table"])]
                if not all(checks): audit_errors.append([row["id"], p, w, "receipt/lineage"])
                parsed, g = r["parsed"], gold[row["id"]]
                numeric, correct = False, False
                if parsed["valid"] and not parsed.get("abstained"):
                    a = parsed["answer"]
                    numeric = close(a["answer_value"], g["value"])
                    correct = numeric and unit(a["unit"]) == unit(g["unit"])
                scores[(row["id"], p, w)] = {"correct": int(correct), "numeric": int(numeric),
                    "accepted_by_binding_filter": bool(parsed.get("source_bound") and parsed.get("internally_consistent"))}
    if len(records) != plan["max_calls"]: audit_errors.append("count")
    if audit_errors:
        write(directory / "audit_failures.json", audit_errors)
        raise RuntimeError("Receipt audit failed")
    for p in PROFILES:
        for w in WORKFLOWS:
            rs = [records[(r["id"], p, w)] for r in public["items"]]
            ss = [scores[(r["id"], p, w)] for r in public["items"]]
            accepted = [s for s in ss if s["accepted_by_binding_filter"]]
            input_tokens = sum(r["response"].get("prompt_eval_count", 0) for r in rs)
            output_tokens = sum(r["response"].get("eval_count", 0) for r in rs)
            metrics[p + "/" + w] = {"correct": sum(s["correct"] for s in ss), "n": len(ss), "numeric_correct": sum(s["numeric"] for s in ss),
                "valid": sum(r["parsed"]["valid"] for r in rs), "binding_filter_accepted": len(accepted),
                "wrong_among_binding_accepted": sum(not s["correct"] for s in accepted),
                "binding_filter_risk": sum(not s["correct"] for s in accepted) / len(accepted) if accepted else None,
                "terminal_input_tokens": input_tokens, "terminal_output_tokens": output_tokens,
                "mean_terminal_serving_seconds": sum(r["response"]["total_duration"] / 1e9 for r in rs) / len(rs)}
            policy_records = rs + ([records[(r["id"], p, w[0])] for r in public["items"]] if len(w) == 2 else [])
            metrics[p + "/" + w].update(
                workflow_calls_per_item=len(w),
                workflow_input_tokens=sum(r["response"].get("prompt_eval_count", 0) for r in policy_records),
                workflow_output_tokens=sum(r["response"].get("eval_count", 0) for r in policy_records),
                mean_workflow_serving_seconds=sum(r["response"]["total_duration"] / 1e9 for r in policy_records) / len(rs))
    values = {p: [0.5 * ((scores[(r["id"], p, "AB")]["correct"] - scores[(r["id"], p, "AA")]["correct"]) +
                         (scores[(r["id"], p, "BA")]["correct"] - scores[(r["id"], p, "BB")]["correct"])) for r in public["items"]] for p in PROFILES}
    rng = random.Random(20261109)
    samples = [[rng.randrange(len(public["items"])) for _ in public["items"]] for _ in range(5000)]

    def estimate(xs):
        bs = sorted(sum(xs[i] for i in sample) / len(sample) for sample in samples)
        return {"delta": sum(xs) / len(xs), "ci95": [bs[124], bs[4874]]}

    estimates = {p: estimate(values[p]) for p in PROFILES}
    estimates["interaction"] = estimate([a-b for a,b in zip(values["checklist"],values["standard"])])
    rescues, harms, rescue_groups = 0, 0, set()
    for r in public["items"]:
        for cross, self_ in (("AB", "AA"), ("BA", "BB")):
            a,b=scores[(r["id"],"checklist",cross)]["correct"],scores[(r["id"],"checklist",self_)]["correct"]
            rescues += a > b; harms += a < b
            if a>b: rescue_groups.add(r["group"])
    schema_validity = sum(r["parsed"]["valid"] for r in records.values()) / len(records)
    primary = estimates["checklist"]
    passed = primary["delta"] >= .05 and primary["ci95"][0] > 0 and len(rescue_groups) >= 4 and schema_validity >= .95
    result = {"plan_id": plan["plan_id"], "receipt_audit": "PASS", "calls": len(records), "metrics": metrics,
        "contrasts": estimates, "checklist_cross_rescues": rescues, "checklist_cross_harms": harms,
        "checklist_rescue_groups": len(rescue_groups), "schema_validity": schema_validity,
        "scientific_gate": "GO_exploratory_only" if passed else "FAIL_stop_scale_and_history",
        "length_stops": sum(r["response"].get("done_reason") == "length" for r in records.values()),
        "tokens_actual_terminal_total": {"input": sum(m["terminal_input_tokens"] for m in metrics.values()),
                                        "output": sum(m["terminal_output_tokens"] for m in metrics.values())},
        "limits": ["24 connected source groups, one QA each; not powered confirmation", "source/table oracle supplied; no retrieval", "one issuer, two quantized families", "no human semantic adjudication", "binding filter is not semantic verification", "terminal tokens differ; same caps are not equal realized cost"]}
    write(directory / "analysis.json", result)
    write(directory / "scores_private.json", [{"item_id": k[0], "profile": k[1], "workflow": k[2], **v} for k,v in scores.items()])
    write(REPORT / "arqa_v2_results.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(); p.add_argument("action", choices=("prepare", "register", "evaluate")); p.add_argument("directory", nargs="?")
    args=p.parse_args()
    if args.action == "prepare": prepare()
    elif args.action == "register": register()
    else: evaluate(args.directory)
