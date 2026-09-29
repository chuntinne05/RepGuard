#!/usr/bin/env python3
"""A1/A2 attack pilots on real model-answer traces (with explicit interventions)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from analyze_real_week3 import (
    AGENTS, StudyTransferEstimator, build_methods, choose_answer, load_inputs,
    make_episodes, write_csv,
)

BUDGETS = (0, 5, 10, 20, 50, 100)
METHODS = ("Uniform", "GlobalBeta", "SkillConditioned", "ZeroEvidenceGate", "FixedBorrow", "ECRT")


def accuracy(agent, ids, tasks, predictions):
    return sum(tasks[tid].check_answer(predictions[(agent, tid)]["answer"]) for tid in ids) / len(ids)


def choose_attack_scenarios(manifest, tasks, predictions, transfer):
    subjects = sorted(manifest["selected"]["dev"])
    dev_accuracy = {
        (agent, subject): accuracy(agent, manifest["selected"]["dev"][subject], tasks, predictions)
        for agent in AGENTS for subject in subjects
    }
    # Select both scenarios using dev data only, never target-test outcomes.
    a1_agent, a1_domain = max(dev_accuracy, key=lambda key: dev_accuracy[key])
    related_candidates = []
    for agent in AGENTS:
        for source in subjects:
            for target in subjects:
                if transfer.estimate(source, target).condition.value != "related":
                    continue
                gap = dev_accuracy[(agent, source)] - dev_accuracy[(agent, target)]
                related_candidates.append((gap, agent, source, target))
    gap, a2_agent, a2_source, a2_target = max(related_candidates)
    return {
        "a1": {"attacker": a1_agent, "source": a1_domain, "target": a1_domain,
               "dev_source_accuracy": dev_accuracy[(a1_agent, a1_domain)]},
        "a2": {"attacker": a2_agent, "source": a2_source, "target": a2_target,
               "dev_source_accuracy": dev_accuracy[(a2_agent, a2_source)],
               "dev_target_accuracy": dev_accuracy[(a2_agent, a2_target)],
               "dev_transfer_gap": gap},
    }


def feedback_poison(episodes, attacker: str):
    # Attacker controls its own feedback reports: all wrong historical answers
    # receive false positive feedback. Other agents' feedback remains objective.
    return [
        ep.with_corrupted_feedback(1.0)
        if ep.agent_id == attacker and not ep.oracle_correct() else ep
        for ep in episodes
    ]


def eval_attack(method_name, method, target_ids, target, attacker, tasks, predictions):
    scores = {a: method.score(a, target) for a in AGENTS}
    weights = {
        a: (scores[a].lower_bound if method_name == "ECRT" else scores[a].mean)
        for a in AGENTS
    }
    total = sum(weights.values())
    influence = weights[attacker]/total if total else 0.25
    clean = attacked = 0
    for tid in target_ids:
        task = tasks[tid]
        answers = {a: predictions[(a, tid)]["answer"] for a in AGENTS}
        clean += task.check_answer(choose_answer(answers, scores, method_name, tid))
        attack_answers = dict(answers)
        attack_answers[attacker] = next(
            chr(ord("A") + i) for i in range(len(task.options))
            if chr(ord("A") + i) != task.ground_truth_answer
        )
        attacked += task.check_answer(choose_answer(attack_answers, scores, method_name, tid))
    n = len(target_ids)
    return {
        "n_target_tasks": n, "attacker_weight_share": influence,
        "clean_team_accuracy": clean/n,
        "attacked_team_accuracy": attacked/n,
        "attack_accuracy_loss": (clean-attacked)/n,
        "attacker_reputation_mean": scores[attacker].mean,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/real_week3_json_v1")
    args = parser.parse_args()
    output = Path(args.output)
    manifest, tasks, predictions, missing = load_inputs(output)
    if missing:
        raise RuntimeError(f"Prediction ledger incomplete: {len(missing)} model answers missing")
    transfer = StudyTransferEstimator()
    scenarios = choose_attack_scenarios(manifest, tasks, predictions, transfer)
    out = output / "analysis"
    out.mkdir(exist_ok=True)
    (out / "attack_scenarios.json").write_text(json.dumps(scenarios, indent=2))
    rows = []
    for scenario_name, cfg in scenarios.items():
        source, target, attacker = cfg["source"], cfg["target"], cfg["attacker"]
        cal = make_episodes(manifest["selected"]["dev"][source], source, tasks, predictions)
        target_ids = manifest["selected"]["test"][target]
        for budget in BUDGETS:
            history_ids = manifest["selected"]["train_calibration"][source][:budget]
            honest_history = make_episodes(history_ids, source, tasks, predictions)
            for feedback_condition in ("honest", "attacker_false_positive"):
                history = honest_history if feedback_condition == "honest" else feedback_poison(honest_history, attacker)
                methods, _ = build_methods(history, cal, transfer)
                for method_name in METHODS:
                    result = eval_attack(method_name, methods[method_name], target_ids, target, attacker, tasks, predictions)
                    rows.append({
                        "scenario": scenario_name, "attacker": attacker,
                        "source": source, "target": target,
                        "budget_history_tasks": budget,
                        "feedback_condition": feedback_condition,
                        "method": method_name, **result,
                    })
    write_csv(out / "attack_capital_curves.csv", rows)
    print(f"attack_scenarios={scenarios}")
    print(f"attack_curve_rows={len(rows)}")


if __name__ == "__main__":
    main()
