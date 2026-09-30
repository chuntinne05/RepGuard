#!/usr/bin/env python3
"""Exploratory targeted-feedback attack on real Week 3 model answers.

Only feedback is synthetically corrupted, never model answers. Gold audit cases
are disjoint from history and target test cases. Test outcomes were inspected in
prior research, so this is a development stress test, not confirmation.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from analyze_audit_budget_replay import beta_scores
from analyze_real_week3 import (
    SEEDS,
    StudyTransferEstimator,
    build_methods,
    cluster_bootstrap,
    eval_cell,
    load_inputs,
    make_episodes,
    mean,
)
from repguard.reputation.audited import AuditedECRTReputation
from repguard.reputation.feedback import FeedbackCorruptor

SOURCE = Path("results/real_week3_json_v1")
OUTPUT = Path("results/real_next_study_v1/targeted_attack_replay.json")
ATTACKERS = ("qwen3-0.6b", "qwen3-8b")
METHODS = ("FixedBorrow", "ECRT", "AuditOnly", "FixedPlusAudit", "AuditedECRT")


def targeted_corrupt(episodes, attacker: str, seed: int):
    target = [episode for episode in episodes if episode.agent_id == attacker]
    changed = FeedbackCorruptor.adversarial(bias_rate=0.4, seed=seed).corrupt(target)
    by_id = {episode.episode_id: episode for episode in changed}
    return [by_id.get(episode.episode_id, episode) for episode in episodes]


def summary(rows):
    grouped = defaultdict(list)
    for row in rows:
        key = (row["attacker"], row["target"], row["t"], row["condition"],
               row["method"])
        grouped[key].append(row["team_accuracy"])
    avg = {key: mean(values) for key, values in grouped.items()}
    targets = sorted({row["target"] for row in rows})
    result = {}
    for attacker in ATTACKERS:
        result[attacker] = {}
        for relation in ("same", "related"):
            result[attacker][relation] = {}
            for condition in ("clean", "targeted_false_positive_040"):
                result[attacker][relation][condition] = {}
                for method in METHODS:
                    values = {target: avg[attacker, target, relation, condition, method]
                              for target in targets if
                              (attacker, target, relation, condition, method) in avg}
                    result[attacker][relation][condition][method] = cluster_bootstrap(
                        values, n_boot=2000)
    return result


def paired_summary(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["attacker"], row["target"], row["t"], row["condition"],
                row["method"]].append(row["team_accuracy"])
    avg = {key: mean(values) for key, values in grouped.items()}
    targets = sorted({row["target"] for row in rows})
    effects = {}
    for attacker in ATTACKERS:
        effects[attacker] = {}
        for relation in ("same", "related"):
            effects[attacker][relation] = {}
            comparisons = [(method, "targeted_false_positive_040", method, "clean")
                           for method in METHODS]
            comparisons += [("AuditedECRT", "targeted_false_positive_040",
                             "ECRT", "targeted_false_positive_040"),
                            ("AuditedECRT", "targeted_false_positive_040",
                             "FixedPlusAudit", "targeted_false_positive_040"),
                            ("AuditedECRT", "targeted_false_positive_040",
                             "AuditOnly", "targeted_false_positive_040")]
            for a, ac, b, bc in comparisons:
                values = {target: avg[attacker, target, relation, ac, a]
                          - avg[attacker, target, relation, bc, b]
                          for target in targets if
                          (attacker, target, relation, ac, a) in avg and
                          (attacker, target, relation, bc, b) in avg}
                effects[attacker][relation][f"{a}_{ac}_minus_{b}_{bc}"] = (
                    cluster_bootstrap(values, n_boot=2000))
    return effects


def main() -> None:
    manifest, tasks, predictions, missing = load_inputs(SOURCE)
    if missing:
        raise RuntimeError(f"Week 3 ledger incomplete: {len(missing)}")
    transfer = StudyTransferEstimator()
    subjects = sorted(manifest["selected"]["test"])
    # Match the Week 3 factorial grid, which excludes a target without both
    # related and unrelated source strata (the isolated "other" subject).
    target_subjects = [target for target in subjects if
                       any(transfer.estimate(source, target).condition.value == "related"
                           for source in subjects) and
                       any(transfer.estimate(source, target).condition.value == "unrelated"
                           for source in subjects)]
    rows = []
    attack_counts = defaultdict(lambda: {"wrong": 0, "flipped": 0})
    for attacker in ATTACKERS:
        for target in target_subjects:
            target_ids = manifest["selected"]["test"][target]
            for source in subjects:
                relation = transfer.estimate(source, target).condition.value
                if relation == "unrelated":
                    continue
                history_raw = make_episodes(manifest["selected"]["train_calibration"][source],
                                            source, tasks, predictions)
                audit_raw = make_episodes(manifest["selected"]["dev"][source],
                                          source, tasks, predictions)
                for seed in SEEDS:
                    for condition in ("clean", "targeted_false_positive_040"):
                        if condition == "clean":
                            history, calibration = history_raw, audit_raw
                        else:
                            history = targeted_corrupt(history_raw, attacker, seed + 10_000)
                            calibration = targeted_corrupt(audit_raw, attacker, seed + 20_000)
                            key = (attacker, source, seed)
                            # Count each source history once, even if paired with
                            # several target subjects.
                            if target == source:
                                for before, after in zip(history_raw, history):
                                    if before.agent_id == attacker and not before.oracle_correct():
                                        attack_counts[key]["wrong"] += 1
                                        attack_counts[key]["flipped"] += (
                                            after.observed_feedback == 1.0)
                        old, reliability = build_methods(history, calibration, transfer)
                        methods = {name: old[name] for name in ("FixedBorrow", "ECRT")}
                        for name in ("AuditOnly", "FixedPlusAudit"):
                            methods[name] = beta_scores(target, source, transfer, history,
                                                        audit_raw, reliability, name, 0.0)
                        methods["AuditedECRT"] = AuditedECRTReputation(transfer).fit(
                            history, calibration)
                        cell_rows = eval_cell(target_ids, target, tasks, predictions,
                                              methods, condition, relation, source, seed)
                        for row in cell_rows:
                            row["attacker"] = attacker
                            row["condition"] = condition
                        rows.extend(cell_rows)
    result = {
        "status": "exploratory_reused_week3_test_synthetic_feedback_only",
        "attack": "40% false-positive feedback on wrong answers of one chosen agent",
        "attackers": list(ATTACKERS),
        "n_rows": len(rows),
        "history_attack_counts": {"|".join(map(str, key)): counts
                                  for key, counts in sorted(attack_counts.items())},
        "team_accuracy": summary(rows),
        "paired_effects": paired_summary(rows),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    for attacker in ATTACKERS:
        for relation in ("same", "related"):
            print(attacker, relation, {
                condition: {method: round(result["team_accuracy"][attacker][relation]
                                          [condition][method]["estimate"], 5)
                            for method in METHODS}
                for condition in ("clean", "targeted_false_positive_040")}, flush=True)


if __name__ == "__main__":
    main()
