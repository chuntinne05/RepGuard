"""Offline labels are opened only after collection stops; no inference here."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .collection import WORKFLOWS
from .prepare import OUT, digest, write


def metrics(pred, gold):
    correct = np.asarray([p == y for p, y in zip(pred, gold)], dtype=float)
    sufficient = [i for i, p in enumerate(pred) if p in (2, 3)]
    false = sum(pred[i] != gold[i] for i in sufficient)
    f1 = []
    for c in range(4):
        tp = sum(p == c and y == c for p, y in zip(pred, gold))
        fp = sum(p == c and y != c for p, y in zip(pred, gold))
        fn = sum(p != c and y == c for p, y in zip(pred, gold))
        f1.append(2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.)
    return {"correct": int(correct.sum()), "n": len(gold), "accuracy": float(correct.mean()),
            "macro_f1": float(np.mean(f1)), "sufficient_decisions": len(sufficient),
            "sufficient_coverage": len(sufficient) / len(gold),
            "false_sufficient_decisions": false,
            "false_sufficient_risk": false / len(sufficient) if sufficient else None,
            "false_support_approvals": sum(p == 2 and y != 2 for p, y in zip(pred, gold)),
            "predicted_counts": {str(c): pred.count(c) for c in (None, 0, 1, 2, 3)}}


def analyze(directory):
    directory = Path(directory)
    plan = json.loads((directory / "plan.json").read_text())
    public = json.loads((directory / "public_pilot.json").read_text())
    gold_packet = json.loads((OUT / "private_pilot_gold.json").read_text())
    if digest(gold_packet) != plan["gold_sha256"] or digest(public) != plan["public_sha256"]:
        raise ValueError("Evaluation input hashes changed")
    rows = public["items"]
    gold = [gold_packet["labels"][r["id"]] for r in rows]
    records = {}
    for p in (directory / "responses").glob("*.json"):
        record = json.loads(p.read_text())
        claimed = record.pop("record_sha256")
        if digest(record) != claimed:
            raise ValueError("Response checksum failed")
        record["record_sha256"] = claimed
        key = record["item_id"], record["workflow"]
        if key in records:
            raise ValueError("Duplicate terminal record")
        records[key] = record
    expected = {(r["id"], w) for r in rows for w in WORKFLOWS}
    if set(records) != expected:
        raise ValueError("Incomplete collection; cannot report full-pilot scores")
    predictions = {w: [records[(r["id"], w)]["parsed"].get("label") for r in rows] for w in WORKFLOWS}
    correct = {w: np.asarray([p == y for p, y in zip(predictions[w], gold)], dtype=float) for w in WORKFLOWS}
    delta = .5 * (correct["AB"] + correct["BA"] - correct["AA"] - correct["BB"])
    groups = list(dict.fromkeys(r["group"] for r in rows))
    group_delta = np.asarray([np.mean([delta[i] for i, r in enumerate(rows) if r["group"] == g]) for g in groups])
    rng = np.random.default_rng(20261109)
    samples = rng.choice(group_delta, size=(5000, len(groups)), replace=True).mean(axis=1)
    interactions = {}
    rescue_groups = set()
    total_rescues = 0
    for candidate, control in (("AB", "AA"), ("BA", "BB")):
        rescues = [i for i in range(len(rows)) if correct[candidate][i] and not correct[control][i]]
        harms = [i for i in range(len(rows)) if correct[control][i] and not correct[candidate][i]]
        total_rescues += len(rescues)
        rescue_groups.update(rows[i]["group"] for i in rescues)
        interactions[f"{candidate}_vs_{control}"] = {"rescues": len(rescues), "harms": len(harms),
                                                      "delta_pp": 100 * float((correct[candidate] - correct[control]).mean())}
    primary = float(group_delta.mean())
    operational = all(r.get("transport_ok") for r in records.values()) and np.mean(
        [r["parsed"]["valid"] for r in records.values()]) >= .95
    go = bool(operational and primary >= .03 and primary > 0 and total_rescues >= 6 and len(rescue_groups) >= 4)
    summary = {"plan_id": plan["plan_id"], "scope": "Development screen of standalone passage sufficiency; no method novelty or report-level claim.",
               "real_responses": len(records), "pairs": len(rows), "claim_groups": len(groups),
               "metrics": {w: metrics(predictions[w], gold) for w in WORKFLOWS},
               "primary_cross_minus_self_pp": 100 * primary,
               "claim_cluster_bootstrap95_pp": (100 * np.quantile(samples, [.025, .975])).tolist(),
               "interactions": interactions, "rescue_groups": len(rescue_groups),
               "operational_pass": bool(operational), "interaction_screen_pass": go,
               "oracle_all_workflows": int(np.max(np.stack(list(correct.values())), axis=0).sum()),
               "oracle_is_deployable": False, "history_learner_fitted": False,
               "per_call_totals": {
                   "input_tokens": sum(r.get("response", {}).get("prompt_eval_count", 0) for r in records.values()),
                   "output_tokens": sum(r.get("response", {}).get("eval_count", 0) for r in records.values()),
                   "summed_request_wall_seconds": sum(r["wall_seconds"] for r in records.values())},
               "billing_usd": None, "human_adjudications_added": 0}
    write(directory / "analysis.json", summary)
    diagnostics = []
    for i, row in enumerate(rows):
        diagnostics.append({"item_id": row["id"], "group": row["group"], "gold": gold[i],
                            "predictions": {w: predictions[w][i] for w in WORKFLOWS}})
    write(directory / "paired_diagnostics_private.json", diagnostics)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("directory")
    analyze(parser.parse_args().directory)
