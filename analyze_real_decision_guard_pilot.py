#!/usr/bin/env python3
"""Exploratory decision guard on real Week 3 answers and real judge feedback.

Judge audit/history folds are disjoint, thresholds are fit on Week 3 dev, and
the already inspected Week 3 test is replayed only as a diagnostic. This is
not an independent DART result and must not support a confirmatory claim.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

from analyze_real_week3 import AGENTS, FixedBorrow, StudyTransferEstimator, load_inputs
from analyze_real_week5_feedback_impact import episodes_for, load_judgments
from repguard.reputation.ecrt import ECRTReputation, FeedbackReliabilityEstimator


WEEK3 = Path("results/real_week3_json_v1")
JUDGE = Path("results/real_week5_modal_judge_v1")
OUTPUT = Path("results/real_next_study_v1/decision_guard_pilot.json")
BASELINE_AGENT = "qwen3-8b"
THRESHOLDS = (0.0, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2, 0.3, 0.4, 0.6, 0.8)


def vote_choice(task_id: str, subject: str, predictions: dict, scores: dict,
                *, use_lower: bool, aggregator: str) -> tuple[str, str, float]:
    from hashlib import sha256

    baseline = predictions[BASELINE_AGENT, task_id]["answer"]
    n_options = predictions[BASELINE_AGENT, task_id]["num_options"]
    votes: dict[str, float] = {chr(ord("A") + i): 0.0 for i in range(n_options)}
    for agent in AGENTS:
        answer = predictions[agent, task_id]["answer"]
        p = scores[agent].lower_bound if use_lower else scores[agent].mean
        if aggregator == "weighted_vote":
            votes[answer] += max(p, 1e-6)
        elif aggregator == "naive_bayes_answer":
            p = min(max(p, 1e-4), 1 - 1e-4)
            votes[answer] += math.log((n_options - 1) * p / (1 - p))
        else:
            raise ValueError(f"Unknown aggregator {aggregator}")
    high = max(votes.values())
    tied = [answer for answer, weight in votes.items() if abs(weight - high) < 1e-12]
    chosen = min(tied, key=lambda answer: sha256(f"{task_id}:{answer}".encode()).hexdigest())
    if aggregator == "weighted_vote":
        margin = (votes[chosen] - votes[baseline]) / sum(votes.values())
    else:
        maximum = max(votes.values())
        posterior = {answer: math.exp(value - maximum) for answer, value in votes.items()}
        normalizer = sum(posterior.values())
        margin = (posterior[chosen] - posterior[baseline]) / normalizer
    return baseline, chosen, margin


def answers_for(ids: list[str], subject: str, predictions: dict, scores: dict,
                *, use_lower: bool, aggregator: str) -> list[tuple[str, str, str, float]]:
    return [(tid, *vote_choice(tid, subject, predictions, scores,
                               use_lower=use_lower, aggregator=aggregator))
            for tid in ids]


def correct(records: list[tuple[str, str, str, float]], tasks: dict,
            threshold: float) -> int:
    return sum((candidate if margin > threshold else baseline)
               == tasks[tid].ground_truth_answer
               for tid, baseline, candidate, margin in records)


def run() -> dict:
    manifest, tasks, predictions, missing = load_inputs(WEEK3)
    if missing:
        raise RuntimeError(f"Week 3 ledger has {len(missing)} missing rows")
    judge_manifest, judgments = load_judgments(JUDGE)
    if judge_manifest["dataset_task_id_sha256"] != manifest["dataset_task_id_sha256"]:
        raise RuntimeError("Judge and Week 3 dataset mismatch")
    selected = judge_manifest["selected_history_ids"]
    transfer = StudyTransferEstimator()
    result = {"status": "exploratory_reused_week3_test_not_independent",
              "judge_protocol_hash": judge_manifest["protocol_hash"],
              "baseline_agent": BASELINE_AGENT,
              "folds": []}
    for fold in (0, 1):
        audit = [ep for subject, ids in sorted(selected.items())
                 for ep in episodes_for(ids[:10] if fold == 0 else ids[10:],
                                        subject, tasks, predictions, judgments)]
        reliability = FeedbackReliabilityEstimator().calibrate(audit)
        dev_by_method: dict[str, list] = defaultdict(list)
        test_by_method: dict[str, list] = defaultdict(list)
        subject_test: dict[str, dict[str, list]] = defaultdict(dict)
        for subject, ids in sorted(selected.items()):
            history = episodes_for(ids[10:] if fold == 0 else ids[:10],
                                   subject, tasks, predictions, judgments)
            methods = {
                "FixedBorrow": (FixedBorrow(history, transfer), False),
                "ECRT": (ECRTReputation(transfer, reliability).fit(history), True),
            }
            for name, (method, use_lower) in methods.items():
                scores = {agent: method.score(agent, subject) for agent in AGENTS}
                dev_ids = manifest["selected"]["dev"][subject]
                test_ids = manifest["selected"]["test"][subject]
                for aggregator in ("weighted_vote", "naive_bayes_answer"):
                    key = f"{name}:{aggregator}"
                    dev_by_method[key].extend(answers_for(
                        dev_ids, subject, predictions, scores, use_lower=use_lower,
                        aggregator=aggregator))
                    rows = answers_for(test_ids, subject, predictions, scores,
                                       use_lower=use_lower, aggregator=aggregator)
                    test_by_method[key].extend(rows)
                    subject_test[subject][key] = rows
                if name == "ECRT":
                    key = "ECRT_mean:naive_bayes_answer"
                    dev_by_method[key].extend(answers_for(
                        dev_ids, subject, predictions, scores, use_lower=False,
                        aggregator="naive_bayes_answer"))
                    rows = answers_for(test_ids, subject, predictions, scores,
                                       use_lower=False, aggregator="naive_bayes_answer")
                    test_by_method[key].extend(rows)
                    subject_test[subject][key] = rows
        fold_result = {"fold": fold, "audit_agent_cases": len(audit),
                       "history_agent_cases": 14 * 10 * len(AGENTS),
                       "judge_sensitivity": reliability.sensitivity,
                       "judge_specificity": reliability.specificity,
                       "methods": {}}
        for name in ("FixedBorrow:weighted_vote", "ECRT:weighted_vote",
                     "FixedBorrow:naive_bayes_answer", "ECRT:naive_bayes_answer",
                     "ECRT_mean:naive_bayes_answer"):
            dev = dev_by_method[name]
            test = test_by_method[name]
            ranked = sorted(((correct(dev, tasks, threshold), threshold)
                             for threshold in THRESHOLDS), reverse=True)
            best_dev, threshold = ranked[0]
            fold_result["methods"][name] = {
                "selected_threshold": threshold,
                "dev_correct": best_dev, "dev_n": len(dev),
                "test_correct": correct(test, tasks, threshold),
                "test_n": len(test),
                "test_unguarded_correct": correct(test, tasks, -1.0),
                "test_switched": sum(candidate != baseline and margin > threshold
                                     for _, baseline, candidate, margin in test),
                "test_by_subject": {subject: {
                    "n": len(subject_test[subject][name]),
                    "correct": correct(subject_test[subject][name], tasks, threshold)}
                    for subject in sorted(subject_test)},
            }
        result["folds"].append(fold_result)
    result["baseline_test_correct"] = sum(
        predictions[BASELINE_AGENT, tid]["answer"] == tasks[tid].ground_truth_answer
        for ids in manifest["selected"]["test"].values() for tid in ids)
    result["baseline_test_n"] = sum(map(len, manifest["selected"]["test"].values()))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    data = run()
    print(json.dumps({"status": data["status"], "baseline":
        [data["baseline_test_correct"], data["baseline_test_n"]],
        "folds": [{"fold": fold["fold"], "methods": {
            name: {k: value for k, value in method.items() if k != "test_by_subject"}
            for name, method in fold["methods"].items()}}
            for fold in data["folds"]]}, indent=2))
