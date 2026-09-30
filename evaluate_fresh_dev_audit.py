#!/usr/bin/env python3
"""Locked fresh-development replay of targeted feedback attack and audited trust.

Historical responses and disjoint gold audits come from the inspected Week 3
train/dev splits. New target answers come only from all 560 frozen development
IDs. The attack changes historical feedback of qwen3-0.6b, never model answers.
This script is written before scoring the new development outcomes.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

from analyze_audit_budget_replay import beta_scores
from analyze_real_dev_pool import load_validated
from analyze_real_week3 import (
    SEEDS,
    StudyTransferEstimator,
    build_methods,
    cluster_bootstrap,
    load_inputs,
    make_episodes,
    mean,
)
from analyze_targeted_attack_replay import targeted_corrupt
from repguard.reputation.audited import AuditedECRTReputation

OUTPUT = Path("results/real_dev_pool_v1/audit_evaluation.json")
OLD = Path("results/real_week3_json_v1")
AGENTS = ("qwen3-8b", "gemma2", "qwen3-0.6b")
NEW_VARIANTS = {"qwen3-8b": "qwen3_8b_direct", "gemma2": "gemma2_direct",
                "qwen3-0.6b": "qwen3_06b_direct"}
METHODS = ("FixedBorrow", "ECRT", "AuditOnly", "FixedPlusAudit", "AuditedECRT")
CONDITIONS = ("clean", "targeted_false_positive_040")


def choose(task_id: str, answers: dict[str, str | None], scores, method: str) -> str | None:
    votes = defaultdict(float)
    for agent in AGENTS:
        answer = answers[agent]
        if answer is None:
            continue
        score = scores[agent]
        weight = score.lower_bound if method == "ECRT" else score.mean
        votes[answer] += max(weight, 1e-6)
    if not votes:
        return None
    high = max(votes.values())
    tied = [answer for answer, total in votes.items() if abs(total - high) < 1e-12]
    return min(tied, key=lambda answer: hashlib.sha256(
        f"{task_id}:{answer}".encode()).hexdigest())


def summarize(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["target"], row["relation"], row["condition"],
                row["method"]].append(row["accuracy"])
    avg = {key: mean(values) for key, values in grouped.items()}
    targets = sorted({row["target"] for row in rows})
    cells = {}
    effects = {}
    for relation in ("same", "related"):
        cells[relation] = {}
        effects[relation] = {}
        for condition in CONDITIONS:
            cells[relation][condition] = {}
            for method in METHODS:
                values = {target: avg[target, relation, condition, method]
                          for target in targets if
                          (target, relation, condition, method) in avg}
                cells[relation][condition][method] = cluster_bootstrap(values, n_boot=5000)
        for method in METHODS:
            values = {target: avg[target, relation, CONDITIONS[1], method]
                      - avg[target, relation, CONDITIONS[0], method]
                      for target in targets if
                      (target, relation, CONDITIONS[1], method) in avg and
                      (target, relation, CONDITIONS[0], method) in avg}
            effects[relation][f"{method}_attack_minus_clean"] = cluster_bootstrap(
                values, n_boot=5000)
        for baseline in ("ECRT", "FixedPlusAudit", "AuditOnly"):
            values = {target: avg[target, relation, CONDITIONS[1], "AuditedECRT"]
                      - avg[target, relation, CONDITIONS[1], baseline]
                      for target in targets if
                      (target, relation, CONDITIONS[1], "AuditedECRT") in avg and
                      (target, relation, CONDITIONS[1], baseline) in avg}
            effects[relation][f"AuditedECRT_minus_{baseline}_under_attack"] = (
                cluster_bootstrap(values, n_boot=5000))
    return cells, effects


def run() -> dict:
    old_manifest, tasks, old_predictions, old_missing = load_inputs(OLD)
    if old_missing:
        raise RuntimeError("Old Week 3 history/audit ledger incomplete")
    new_manifest, new_tasks, new_rows = load_validated()
    selected = new_manifest["selected_development_ids"]
    for variant in NEW_VARIANTS.values():
        if sum(name == variant for name, _ in new_rows) != 560:
            raise RuntimeError(f"Need all 560 real development answers for {variant}")
    if set(tasks) != set(new_tasks):
        raise RuntimeError("Dataset changed between studies")

    transfer = StudyTransferEstimator()
    subjects = sorted(selected)
    targets = [target for target in subjects if
               any(transfer.estimate(source, target).condition.value == "related"
                   for source in subjects) and
               any(transfer.estimate(source, target).condition.value == "unrelated"
                   for source in subjects)]
    rows = []
    for target in targets:
        ids = selected[target]
        gold = {tid: new_tasks[tid].ground_truth_answer for tid in ids}
        answers = {tid: {agent: new_rows[variant, tid]["answer"]
                         for agent, variant in NEW_VARIANTS.items()} for tid in ids}
        for source in subjects:
            relation = transfer.estimate(source, target).condition.value
            if relation == "unrelated":
                continue
            history_raw = [ep for ep in make_episodes(
                old_manifest["selected"]["train_calibration"][source], source,
                tasks, old_predictions) if ep.agent_id in AGENTS]
            audits_raw = [ep for ep in make_episodes(
                old_manifest["selected"]["dev"][source], source,
                tasks, old_predictions) if ep.agent_id in AGENTS]
            for seed in SEEDS:
                for condition in CONDITIONS:
                    if condition == "clean":
                        history, calibration = history_raw, audits_raw
                    else:
                        history = targeted_corrupt(history_raw, "qwen3-0.6b",
                                                   seed + 10_000)
                        calibration = targeted_corrupt(audits_raw, "qwen3-0.6b",
                                                       seed + 20_000)
                    old_methods, reliability = build_methods(history, calibration,
                                                             transfer)
                    methods = {name: old_methods[name]
                               for name in ("FixedBorrow", "ECRT")}
                    for name in ("AuditOnly", "FixedPlusAudit"):
                        methods[name] = beta_scores(target, source, transfer,
                                                    history, audits_raw,
                                                    reliability, name, 0.0)
                    methods["AuditedECRT"] = AuditedECRTReputation(transfer).fit(
                        history, calibration)
                    for method in METHODS:
                        scores = {agent: methods[method].score(agent, target)
                                  for agent in AGENTS}
                        correct = sum(choose(tid, answers[tid], scores, method) == gold[tid]
                                      for tid in ids)
                        rows.append({"target": target, "source": source,
                                     "relation": relation, "seed": seed,
                                     "condition": condition, "method": method,
                                     "n": len(ids), "correct": correct,
                                     "accuracy": correct / len(ids)})
    cells, effects = summarize(rows)
    result = {
        "status": "fresh_development_not_sealed_holdout",
        "new_protocol_hash": new_manifest["protocol_hash"],
        "attack": "40% false-positive feedback only on qwen3-0.6b wrong history and audit cases",
        "historical_gold_audit": "50 disjoint Week 3 dev questions per source subject and agent",
        "team_agents": list(AGENTS), "n_rows": len(rows),
        "target_subjects": len(targets),
        "cells": cells, "paired_effects": effects,
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    result = run()
    print(json.dumps({relation: {
        condition: {method: round(result["cells"][relation][condition]
                                  [method]["estimate"], 5) for method in METHODS}
        for condition in CONDITIONS} for relation in ("same", "related")}, indent=2))
