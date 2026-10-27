#!/usr/bin/env python3
"""Exploratory same-audit-budget replay on the inspected Week 3 answer ledger.

The original ECRT calibrates feedback on 50 gold-labeled development questions
per source subject, whereas FixedBorrow never uses those labels as competence
evidence. This replay gives simple baselines access to the same audited cases.
No model inference is generated and no sealed holdout is read.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

from analyze_real_week3 import (
    Q_LEVELS,
    SEEDS,
    StudyTransferEstimator,
    build_methods,
    cluster_bootstrap,
    corrupt,
    eval_cell,
    load_inputs,
    make_episodes,
    mean,
)
from repguard.reputation.baselines import BetaParams, ReputationScore
from repguard.reputation.audited import AuditedECRTReputation
from repguard.reputation.ecrt import FeedbackReliabilityEstimator

OUTPUT = Path("results/real_next_study_v1/audit_budget_replay.json")
SOURCE = Path("results/real_week3_json_v1")
AGENTS = ("qwen3-8b", "gemma2", "llama3-8b", "qwen3-0.6b")
METHODS = ("FixedBorrow", "ECRT", "AuditOnly", "FixedPlusAudit",
           "CalibratedPlusAudit", "GuardedCalibratedPlusAudit", "AuditedECRT")


class ScoreTable:
    def __init__(self, scores: dict[str, ReputationScore]):
        self.scores = scores

    def score(self, agent: str, target: str) -> ReputationScore:
        return self.scores[agent]


def wilson_lower(successes: int, total: int, z: float = 1.645) -> float:
    if total == 0:
        return 0.0
    p = successes / total
    z2 = z * z
    center = (p + z2 / (2 * total)) / (1 + z2 / total)
    radius = z * math.sqrt(p * (1 - p) / total + z2 / (4 * total * total)) / (
        1 + z2 / total)
    return max(0.0, center - radius)


def signal_lower(calibration) -> float:
    tp = tn = positives = negatives = 0
    for episode in calibration:
        if episode.observed_feedback is None:
            continue
        if episode.oracle_correct():
            positives += 1
            tp += episode.observed_feedback >= 0.5
        else:
            negatives += 1
            tn += episode.observed_feedback < 0.5
    return wilson_lower(tp, positives) + wilson_lower(tn, negatives) - 1.0


def beta_scores(target: str, source: str, transfer, history, audited, reliability,
                kind: str, guard_mass: float) -> ScoreTable:
    tau = transfer.estimate(source, target).tau
    scores = {}
    estimator = FeedbackReliabilityEstimator()
    for agent in AGENTS:
        beta = BetaParams()
        for ep in audited:
            if ep.agent_id == agent:
                beta.update(float(ep.oracle_correct()), tau)
        if kind != "AuditOnly":
            for ep in history:
                if ep.agent_id != agent or ep.observed_feedback is None:
                    continue
                if kind == "FixedPlusAudit":
                    p, mass = ep.observed_feedback, 1.0
                else:
                    p, mass = estimator.infer_p_correct(ep, reliability)
                    if kind == "GuardedCalibratedPlusAudit":
                        # Conservative channel-strength heuristic, fixed in advance
                        # of this replay. This is not a calibrated confidence bound
                        # on correctness or a formally derived likelihood weight.
                        mass *= max(0.0, guard_mass)
                beta.update(p, tau * mass)
        scores[agent] = ReputationScore(agent, target, beta.mean,
                                        beta.lower_credible_bound,
                                        beta.evidence_count, kind)
    return ScoreTable(scores)


def summarize(rows: list[dict]) -> dict:
    by_target = defaultdict(list)
    for row in rows:
        for metric in ("team_accuracy", "brier_binary"):
            by_target[row["target"], row["t"], row["q"], row["method"], metric].append(
                float(row[metric]))
    averages = {key: mean(values) for key, values in by_target.items()}
    targets = sorted({row["target"] for row in rows})
    cells = {}
    paired = {}
    for metric in ("team_accuracy", "brier_binary"):
        cells[metric] = {}
        paired[metric] = {}
        for relation in ("same", "related", "unrelated"):
            cells[metric][relation] = {}
            paired[metric][relation] = {}
            for regime in Q_LEVELS:
                cells[metric][relation][regime] = {}
                paired[metric][relation][regime] = {}
                for method in METHODS:
                    values = {target: averages[target, relation, regime, method, metric]
                              for target in targets if
                              (target, relation, regime, method, metric) in averages}
                    cells[metric][relation][regime][method] = cluster_bootstrap(
                        values, n_boot=2000)
                for a, b in (("AuditOnly", "ECRT"),
                             ("FixedPlusAudit", "ECRT"),
                             ("GuardedCalibratedPlusAudit", "FixedPlusAudit"),
                             ("GuardedCalibratedPlusAudit", "AuditOnly"),
                             ("AuditedECRT", "FixedPlusAudit"),
                             ("AuditedECRT", "AuditOnly")):
                    values = {target: averages[target, relation, regime, a, metric]
                              - averages[target, relation, regime, b, metric]
                              for target in targets if
                              (target, relation, regime, a, metric) in averages and
                              (target, relation, regime, b, metric) in averages}
                    paired[metric][relation][regime][f"{a}_minus_{b}"] = cluster_bootstrap(
                        values, n_boot=2000)
    return {"cells": cells, "paired_effects": paired, "n_targets": len(targets)}


def main() -> None:
    manifest, tasks, predictions, missing = load_inputs(SOURCE)
    if missing:
        raise RuntimeError(f"Incomplete Week 3 ledger: {len(missing)} missing")
    transfer = StudyTransferEstimator()
    subjects = sorted(manifest["selected"]["test"])
    rows = []
    signals = defaultdict(list)
    for target in subjects:
        target_ids = manifest["selected"]["test"][target]
        for source in subjects:
            relation = transfer.estimate(source, target).condition.value
            history_raw = make_episodes(manifest["selected"]["train_calibration"][source],
                                        source, tasks, predictions)
            audited = make_episodes(manifest["selected"]["dev"][source],
                                    source, tasks, predictions)
            for regime in Q_LEVELS:
                for seed in SEEDS:
                    history = corrupt(history_raw, regime, seed + 10_000)
                    calibration = corrupt(audited, regime, seed + 20_000)
                    old_methods, reliability = build_methods(history, calibration, transfer)
                    strength = signal_lower(calibration)
                    signals[regime].append(strength)
                    methods = {name: old_methods[name] for name in ("FixedBorrow", "ECRT")}
                    for name in METHODS[2:-1]:
                        methods[name] = beta_scores(target, source, transfer, history,
                                                    audited, reliability, name, strength)
                    methods["AuditedECRT"] = AuditedECRTReputation(transfer).fit(
                        history, calibration)
                    rows.extend(eval_cell(target_ids, target, tasks, predictions,
                                          methods, regime, relation, source, seed))
    report = {
        "status": "exploratory_reused_week3_test_not_confirmation",
        "audit_budget": "50 gold questions per source subject x 4 agents; disjoint from history and test",
        "guard": "max(0, Wilson90_lower_sensitivity + Wilson90_lower_specificity - 1)",
        "n_rows": len(rows),
        "guarded_channel_positive_fraction": {
            regime: sum(s > 0 for s in values) / len(values)
            for regime, values in signals.items()},
        **summarize(rows),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n")
    print(f"saved={OUTPUT} rows={len(rows)}", flush=True)
    for regime in Q_LEVELS:
        rel = report["cells"]["team_accuracy"]["related"][regime]
        print(regime, {name: round(rel[name]["estimate"], 5) for name in METHODS}, flush=True)


if __name__ == "__main__":
    main()
