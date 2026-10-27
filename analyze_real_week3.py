#!/usr/bin/env python3
"""Analyze real MMLU-Pro answer traces with a paired Q x T design.

No model answer is generated here. Q changes only the observed historical
feedback. For each target subject, the same held-out questions and model
answers are reused across same, related, and unrelated source subjects.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from repguard.data.mmlu_pro import load_mmlu_pro
from repguard.harness.prompts import format_prompt
from repguard.reputation.baselines import (
    BetaParams, GlobalBetaReputation, ReputationScore,
    SkillConditionedReputation, UniformReputation, ZeroEvidenceGate,
)
from repguard.reputation.ecrt import ECRTReputation, FeedbackReliabilityEstimator
from repguard.reputation.episode import EpisodeRecord
from repguard.reputation.feedback import FeedbackCorruptor
from repguard.reputation.transfer import TransferEstimator

AGENTS = ("qwen3-8b", "gemma2", "llama3-8b", "qwen3-0.6b")
AGENT_MODEL_IDS = {
    "qwen3-8b": "qwen3:8b", "gemma2": "gemma2",
    "llama3-8b": "llama3:8b", "qwen3-0.6b": "qwen3:0.6b",
}
Q_LEVELS = ("oracle", "noisy_025", "noisy_050", "adversarial_040")
SEEDS = (42, 123, 456)
METHODS = (
    "Uniform", "GlobalBeta", "SkillConditioned", "ZeroEvidenceGate",
    "FixedBorrow", "ECRT", "ECRT-noReliability", "ECRT-noTransfer",
    "ECRT-noUncertainty",
)


class StudyTransferEstimator(TransferEstimator):
    """Predeclared, coarse subject taxonomy for the real-data study.

    Unlike the earlier pilot taxonomy, biology and math are unrelated. These
    labels describe metadata proximity; they are not claimed to be oracle
    estimates of actual cross-subject skill transfer.
    """

    _CLUSTERS = {
        "biology": "life_science", "chemistry": "life_science", "health": "life_science",
        "computer science": "physical_technical", "engineering": "physical_technical",
        "math": "physical_technical", "physics": "physical_technical",
        "business": "social_behavioral", "economics": "social_behavioral",
        "psychology": "social_behavioral",
        "history": "humanities", "law": "humanities", "philosophy": "humanities",
        "other": "general",
    }
    _RELATED_CROSS_CLUSTER = set()


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def clean_json(value):
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {k: clean_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [clean_json(v) for v in value]
    return value


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (math.nan, math.nan)
    p = k / n
    den = 1 + z*z/n
    center = (p + z*z/(2*n)) / den
    half = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / den
    return (max(0.0, center-half), min(1.0, center+half))


def load_inputs(output: Path):
    manifest = json.loads((output / "manifest.json").read_text())
    extension_path = output / "test_extension.json"
    if extension_path.exists():
        extension = json.loads(extension_path.read_text())
        actual_sha = hashlib.sha256((output / "manifest.json").read_bytes()).hexdigest()
        if extension["initial_manifest_sha256"] != actual_sha:
            raise RuntimeError("Base manifest changed after test extension was created")
        for subject, ids in extension["selected_extra_test_ids"].items():
            if set(ids) & set(manifest["selected"]["test"][subject]):
                raise RuntimeError(f"Test extension overlaps initial sample: {subject}")
            manifest["selected"]["test"][subject].extend(ids)
    tasks = {t.task_id: t for t in load_mmlu_pro(data_dir="data")}
    dataset_digest = hashlib.sha256("\n".join(sorted(tasks)).encode()).hexdigest()
    if len(tasks) != manifest["dataset_n"] or dataset_digest != manifest["dataset_task_id_sha256"]:
        raise RuntimeError("Local dataset does not match the run manifest")
    prediction_path = output / "predictions.jsonl"
    if not prediction_path.exists():
        raise RuntimeError("Prediction ledger is missing")
    predictions = {}
    duplicates = []
    selected_location = {
        tid: (split_name, subject)
        for split_name, by_subject in manifest["selected"].items()
        for subject, ids in by_subject.items()
        for tid in ids
    }
    n_selected = sum(len(ids) for by_subject in manifest["selected"].values() for ids in by_subject.values())
    if len(selected_location) != n_selected:
        raise RuntimeError("Selected task IDs overlap across splits or subjects")
    for task_id, (_, subject) in selected_location.items():
        if task_id not in tasks or tasks[task_id].metadata.subject != subject:
            raise RuntimeError(f"Selected task metadata mismatch: {task_id}")
    for line in prediction_path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        key = (row["agent"], row["task_id"])
        if row["agent"] not in AGENT_MODEL_IDS or row["model_id"] != AGENT_MODEL_IDS[row["agent"]]:
            raise RuntimeError(f"Model identity mismatch: {key}")
        if selected_location.get(row["task_id"]) != (row["split"], row["subject"]):
            raise RuntimeError(f"Task manifest mismatch: {key}")
        task = tasks[row["task_id"]]
        if row["num_options"] != len(task.options):
            raise RuntimeError(f"Option count mismatch: {key}")
        expected_prompt = format_prompt(task.to_online_view(), mode="direct").text + "\nRespond as JSON with only one key: answer."
        expected_hash = hashlib.sha256(expected_prompt.encode()).hexdigest()[:16]
        if row["prompt_hash"] != expected_hash:
            raise RuntimeError(f"Prompt hash mismatch: {key}")
        if json.loads(row["raw_response"]).get("answer") != row["answer"]:
            raise RuntimeError(f"Raw answer mismatch: {key}")
        valid_answers = {chr(ord("A") + i) for i in range(len(task.options))}
        if row["answer"] not in valid_answers:
            raise RuntimeError(f"Invalid answer letter: {key}")
        if key in predictions:
            duplicates.append(key)
        predictions[key] = row
    if duplicates:
        raise RuntimeError(f"Duplicate prediction keys: {duplicates[:5]}")
    missing = []
    for split_name, by_subject in manifest["selected"].items():
        for subject, ids in by_subject.items():
            for task_id in ids:
                for agent in AGENTS:
                    if (agent, task_id) not in predictions:
                        missing.append((agent, split_name, subject, task_id))
    return manifest, tasks, predictions, missing


def capability_audit(manifest, tasks, predictions, out: Path) -> dict:
    rows = []
    for split_name, by_subject in manifest["selected"].items():
        for subject, ids in sorted(by_subject.items()):
            for agent in AGENTS:
                available = [task_id for task_id in ids if (agent, task_id) in predictions]
                k = sum(tasks[tid].check_answer(predictions[(agent, tid)]["answer"]) for tid in available)
                lo, hi = wilson(k, len(available))
                unknown = sum(predictions[(agent, tid)]["answer"] == "UNKNOWN" for tid in available)
                rows.append({
                    "split": split_name, "subject": subject, "agent": agent,
                    "n": len(available), "n_requested": len(ids), "n_correct": k,
                    "accuracy": k/len(available) if available else math.nan,
                    "ci_lo": lo, "ci_hi": hi, "unknown": unknown,
                })
    write_csv(out / "capability_matrix.csv", rows)
    test_rows = [r for r in rows if r["split"] == "test"]
    history_rows = [r for r in rows if r["split"] == "train_calibration"]
    winners = {}
    winner_ties = {}
    winner_evidence = {}
    for subject in sorted(manifest["selected"]["test"]):
        group = [r for r in test_rows if r["subject"] == subject]
        if all(r["n"] == r["n_requested"] for r in group):
            group.sort(key=lambda r: r["accuracy"], reverse=True)
            winners[subject] = group[0]["agent"]
            winner_ties[subject] = [r["agent"] for r in group if r["n_correct"] == group[0]["n_correct"]]
            history_group = [r for r in history_rows if r["subject"] == subject]
            if all(r["n"] == r["n_requested"] for r in history_group):
                candidate = max(history_group, key=lambda r: r["accuracy"])["agent"]
                ids = manifest["selected"]["test"][subject]
                comparisons = {}
                for rival in (a for a in AGENTS if a != candidate):
                    paired = [
                        int(tasks[tid].check_answer(predictions[(candidate, tid)]["answer"]))
                        - int(tasks[tid].check_answer(predictions[(rival, tid)]["answer"]))
                        for tid in ids
                    ]
                    rng = random.Random(f"winner:{subject}:{rival}")
                    boot = sorted(mean([paired[rng.randrange(len(paired))] for _ in paired]) for _ in range(5000))
                    comparisons[rival] = {
                        "gap": mean(paired), "gap_ci_lo": boot[125], "gap_ci_hi": boot[4875],
                    }
                winner_evidence[subject] = {
                    "history_selected_candidate": candidate,
                    "test_comparisons": comparisons,
                    "confirmed": all(v["gap_ci_lo"] > 0 for v in comparisons.values()),
                }
    confirmed_winners = sorted({v["history_selected_candidate"] for v in winner_evidence.values() if v["confirmed"]})
    overall = {}
    for agent in AGENTS:
        agent_rows = [r for r in test_rows if r["agent"] == agent]
        n = sum(r["n"] for r in agent_rows)
        k = sum(r["n_correct"] for r in agent_rows)
        lo, hi = wilson(k, n)
        complete_subjects = [r for r in agent_rows if r["n"] == r["n_requested"]]
        macro = cluster_bootstrap({r["subject"]: r["accuracy"] for r in complete_subjects})
        overall[agent] = {
            "n": n, "n_correct": k, "micro_accuracy": k/n if n else math.nan,
            "micro_wilson_ci_lo": lo, "micro_wilson_ci_hi": hi,
            "macro_subject_accuracy": macro["estimate"],
            "macro_subject_ci_lo": macro["ci_lo"],
            "macro_subject_ci_hi": macro["ci_hi"],
            "n_complete_subjects": len(complete_subjects),
        }
    routing_diagnostic = None
    if len(winner_evidence) == len(manifest["selected"]["test"]):
        selected = {subject: v["history_selected_candidate"] for subject, v in winner_evidence.items()}
        history_totals = {
            agent: sum(r["n_correct"] for r in history_rows if r["agent"] == agent)
            for agent in AGENTS
        }
        global_agent = max(history_totals, key=history_totals.get)
        routed_correct = 0
        global_correct = 0
        oracle_subject_correct = 0
        n_total = 0
        for subject, ids in manifest["selected"]["test"].items():
            n_total += len(ids)
            routed_correct += sum(tasks[tid].check_answer(predictions[(selected[subject], tid)]["answer"]) for tid in ids)
            global_correct += sum(tasks[tid].check_answer(predictions[(global_agent, tid)]["answer"]) for tid in ids)
            oracle_subject_correct += max(
                sum(tasks[tid].check_answer(predictions[(agent, tid)]["answer"]) for tid in ids)
                for agent in AGENTS
            )
        routing_diagnostic = {
            "selection_split": "train_calibration",
            "selected_by_subject": selected,
            "global_model_selected_on_history": global_agent,
            "n_test_tasks": n_total,
            "routed_test_accuracy": routed_correct/n_total,
            "global_test_accuracy": global_correct/n_total,
            "test_oracle_subject_best_optimistic_accuracy": oracle_subject_correct/n_total,
        }
    result = {
        "test_winners": winners,
        "test_winner_ties": winner_ties,
        "test_unique_winners": sorted(set(winners.values())),
        "test_overall": overall,
        "winner_evidence": winner_evidence,
        "confirmed_unique_winners": confirmed_winners,
        "heterogeneity_gate_provisional": len(confirmed_winners) >= 2,
        "routing_diagnostic": routing_diagnostic,
        "rows": rows,
    }
    (out / "capability_matrix.json").write_text(json.dumps(clean_json(result), indent=2, allow_nan=False))
    return result


def make_episodes(ids: list[str], source: str, tasks, predictions) -> list[EpisodeRecord]:
    episodes = []
    for tid in ids:
        task = tasks[tid]
        for agent in AGENTS:
            answer = predictions[(agent, tid)]["answer"]
            episodes.append(EpisodeRecord(
                episode_id=f"{agent}:{tid}", agent_id=agent, task_id=tid,
                domain=source, agent_answer=answer,
                _ground_truth=task.ground_truth_answer,
                observed_feedback=1.0 if task.check_answer(answer) else 0.0,
                feedback_regime="oracle",
            ))
    return episodes


def corrupt(episodes, q: str, seed: int):
    if q == "oracle":
        return list(episodes)
    if q == "noisy_025":
        return FeedbackCorruptor.noisy(noise_rate=0.25, seed=seed).corrupt(episodes)
    if q == "noisy_050":
        return FeedbackCorruptor.noisy(noise_rate=0.50, seed=seed).corrupt(episodes)
    if q == "adversarial_040":
        return FeedbackCorruptor.adversarial(bias_rate=0.40, seed=seed).corrupt(episodes)
    raise ValueError(q)


class FixedBorrow:
    """Raw-feedback Beta baseline with the same metadata transfer weights as ECRT."""

    def __init__(self, episodes, transfer: TransferEstimator):
        self.episodes = episodes
        self.transfer = transfer

    def score(self, agent: str, target: str) -> ReputationScore:
        beta = BetaParams()
        for ep in self.episodes:
            if ep.agent_id != agent or ep.observed_feedback is None:
                continue
            tau = self.transfer.estimate(ep.domain, target).tau
            if tau:
                beta.update(ep.observed_feedback, tau)
        return ReputationScore(agent, target, beta.mean, beta.lower_credible_bound, beta.evidence_count, "fixed_borrow")


def build_methods(history, calibration, transfer):
    reliability = FeedbackReliabilityEstimator().calibrate(calibration)
    return {
        "Uniform": UniformReputation().fit(history),
        "GlobalBeta": GlobalBetaReputation().fit(history),
        "SkillConditioned": SkillConditionedReputation().fit(history),
        "ZeroEvidenceGate": ZeroEvidenceGate(SkillConditionedReputation(), min_evidence=5).fit(history),
        "FixedBorrow": FixedBorrow(history, transfer),
        "ECRT": ECRTReputation(transfer, reliability, mode="ecrt").fit(history),
        "ECRT-noReliability": ECRTReputation(transfer, reliability, mode="no_reliability").fit(history),
        "ECRT-noTransfer": ECRTReputation(transfer, reliability, mode="no_transfer").fit(history),
        "ECRT-noUncertainty": ECRTReputation(transfer, reliability, mode="ecrt").fit(history),
    }, reliability


def choose_answer(answers: dict[str, str], scores, method: str, task_id: str) -> str:
    votes = defaultdict(float)
    for agent in AGENTS:
        answer = answers[agent]
        if answer == "UNKNOWN":
            continue
        if method == "Uniform":
            weight = 1.0
        elif method.startswith("ECRT") and method != "ECRT-noUncertainty":
            weight = max(scores[agent].lower_bound, 1e-6)
        else:
            weight = max(scores[agent].mean, 1e-6)
        votes[answer] += weight
    if not votes:
        return "UNKNOWN"
    highest = max(votes.values())
    tied = [answer for answer, weight in votes.items() if abs(weight-highest) < 1e-12]
    return min(tied, key=lambda answer: hashlib.sha256(f"{task_id}:{answer}".encode()).hexdigest())


def eval_cell(target_ids, target: str, tasks, predictions, methods, q: str, t: str, source: str, seed: int):
    rows = []
    answers_by_task = {
        tid: {agent: predictions[(agent, tid)]["answer"] for agent in AGENTS}
        for tid in target_ids
    }
    for method_name, method in methods.items():
        scores = {agent: method.score(agent, target) for agent in AGENTS}
        true_target_accuracy = {
            agent: mean([
                float(tasks[tid].check_answer(answers_by_task[tid][agent]))
                for tid in target_ids
            ]) for agent in AGENTS
        }
        competence_mae = mean([
            abs(scores[agent].mean - true_target_accuracy[agent])
            for agent in AGENTS
        ])
        correct_flags = []
        only_one_flags = []
        brier_terms = []
        for tid in target_ids:
            task = tasks[tid]
            answers = answers_by_task[tid]
            chosen = choose_answer(answers, scores, method_name, tid)
            team_correct = task.check_answer(chosen)
            correct_flags.append(team_correct)
            agent_correct = {a: task.check_answer(ans) for a, ans in answers.items()}
            if sum(agent_correct.values()) == 1:
                only_one_flags.append(team_correct)
            for agent in AGENTS:
                brier_terms.append((scores[agent].mean - float(agent_correct[agent])) ** 2)
        rows.append({
            "target": target, "source": source, "t": t, "q": q, "seed": seed,
            "method": method_name, "n_tasks": len(target_ids),
            "n_correct": sum(correct_flags),
            "team_accuracy": sum(correct_flags)/len(correct_flags),
            "brier_binary": sum(brier_terms)/len(brier_terms),
            "competence_mae": competence_mae,
            "n_unique_expert_tasks": len(only_one_flags),
            "unique_expert_success": sum(only_one_flags)/len(only_one_flags) if only_one_flags else math.nan,
            "scores": json.dumps({a: round(scores[a].mean, 6) for a in AGENTS}),
        })
    return rows


def grid(manifest, tasks, predictions, out: Path) -> list[dict]:
    transfer = StudyTransferEstimator()
    subjects = sorted(manifest["selected"]["test"])
    pairs = []
    for target in subjects:
        groups = defaultdict(list)
        for source in subjects:
            condition = transfer.estimate(source, target).condition.value
            groups[condition].append(source)
        if not all(groups.get(t) for t in ("same", "related", "unrelated")):
            continue
        for t in ("same", "related", "unrelated"):
            for source in groups[t]:
                pairs.append((target, source, t))
    target_subjects = sorted(set(p[0] for p in pairs))
    print(f"factorial_targets={len(target_subjects)} source_target_pairs={len(pairs)}", flush=True)
    (out / "domain_pairs.json").write_text(json.dumps([
        {"target": target, "source": source, "t": t, "tau": transfer.estimate(source, target).tau}
        for target, source, t in pairs
    ], indent=2))
    rows = []
    for i, (target, source, t) in enumerate(pairs, 1):
        history_ids = manifest["selected"]["train_calibration"][source]
        calibration_ids = manifest["selected"]["dev"][source]
        target_ids = manifest["selected"]["test"][target]
        raw_history = make_episodes(history_ids, source, tasks, predictions)
        raw_calibration = make_episodes(calibration_ids, source, tasks, predictions)
        for q in Q_LEVELS:
            for seed in SEEDS:
                # Independent corruption streams on disjoint task splits.
                history = corrupt(raw_history, q, seed + 10_000)
                calibration = corrupt(raw_calibration, q, seed + 20_000)
                methods, _ = build_methods(history, calibration, transfer)
                rows.extend(eval_cell(target_ids, target, tasks, predictions, methods, q, t, source, seed))
        if i % 10 == 0 or i == len(pairs):
            print(f"grid_progress={i}/{len(pairs)}", flush=True)
    write_csv(out / "qt_grid_results.csv", rows)
    return rows


def mean(values):
    return sum(values)/len(values) if values else math.nan


def cluster_bootstrap(values_by_target: dict[str, float], n_boot: int = 5000, seed: int = 42):
    targets = sorted(values_by_target)
    vals = [values_by_target[t] for t in targets]
    if not vals:
        return {"estimate": math.nan, "ci_lo": math.nan, "ci_hi": math.nan, "n_targets": 0}
    estimate = mean(vals)
    rng = random.Random(seed)
    reps = []
    for _ in range(n_boot):
        reps.append(mean([vals[rng.randrange(len(vals))] for _ in vals]))
    reps.sort()
    return {"estimate": estimate, "ci_lo": reps[int(.025*n_boot)], "ci_hi": reps[int(.975*n_boot)], "n_targets": len(vals)}


def summarize_grid(rows, out: Path) -> dict:
    # Each target contributes equally. Source pairs and corruption seeds are
    # averaged within target before inference to avoid pseudoreplication.
    grouped = defaultdict(list)
    for row in rows:
        for metric in ("team_accuracy", "brier_binary", "competence_mae", "unique_expert_success"):
            value = float(row[metric])
            if not math.isnan(value):
                grouped[(row["target"], row["t"], row["q"], row["method"], metric)].append(value)
    cell = {key: mean(vals) for key, vals in grouped.items()}
    targets = sorted(set(key[0] for key in cell))
    metrics = ("team_accuracy", "brier_binary", "competence_mae", "unique_expert_success")
    summary = {"design": {
        "inference_unit": "target subject",
        "n_target_subjects": len(targets),
        "source_pairs_and_noise_seeds": "averaged within target before cluster bootstrap",
        "bootstrap_replicates": 5000,
        "warning": "metadata-relatedness is not an oracle measurement of skill transfer",
    }, "cells": {}, "paired_effects": {}, "method_differences": {}}
    for metric in metrics:
        summary["cells"][metric] = {}
        for method in METHODS:
            summary["cells"][metric][method] = {}
            for t in ("same", "related", "unrelated"):
                summary["cells"][metric][method][t] = {}
                for q in Q_LEVELS:
                    by_target = {target: cell[(target,t,q,method,metric)] for target in targets if (target,t,q,method,metric) in cell}
                    summary["cells"][metric][method][t][q] = cluster_bootstrap(by_target)
    # Effects are computed within target for identical held-out target answers.
    for metric in metrics:
        summary["paired_effects"][metric] = {}
        for method in METHODS:
            effects = {}
            for t in ("related", "unrelated"):
                by_target = {}
                for target in targets:
                    a = cell.get((target,"same","oracle",method,metric))
                    b = cell.get((target,t,"oracle",method,metric))
                    if a is not None and b is not None:
                        by_target[target] = a-b
                effects[f"same_minus_{t}_oracle"] = cluster_bootstrap(by_target)
            for q in ("noisy_025", "noisy_050", "adversarial_040"):
                for t in ("same", "related", "unrelated"):
                    by_target = {}
                    for target in targets:
                        a = cell.get((target,t,q,method,metric))
                        b = cell.get((target,t,"oracle",method,metric))
                        if a is not None and b is not None:
                            by_target[target] = a-b
                    effects[f"{q}_minus_oracle_{t}"] = cluster_bootstrap(by_target)
                by_target = {}
                for target in targets:
                    a = cell.get((target,"unrelated",q,method,metric))
                    b = cell.get((target,"unrelated","oracle",method,metric))
                    c = cell.get((target,"same",q,method,metric))
                    d = cell.get((target,"same","oracle",method,metric))
                    if None not in (a,b,c,d):
                        by_target[target] = (a-b)-(c-d)
                effects[f"interaction_{q}_unrelated_vs_same"] = cluster_bootstrap(by_target)
            summary["paired_effects"][metric][method] = effects
    for metric in metrics:
        summary["method_differences"][metric] = {}
        for baseline in ("Uniform", "GlobalBeta", "SkillConditioned", "ZeroEvidenceGate", "FixedBorrow",
                         "ECRT-noReliability", "ECRT-noTransfer", "ECRT-noUncertainty"):
            comparison = {}
            for t in ("same", "related", "unrelated"):
                comparison[t] = {}
                for q in Q_LEVELS:
                    by_target = {}
                    for target in targets:
                        a = cell.get((target,t,q,"ECRT",metric))
                        b = cell.get((target,t,q,baseline,metric))
                        if a is not None and b is not None:
                            by_target[target] = a-b
                    comparison[t][q] = cluster_bootstrap(by_target)
            summary["method_differences"][metric][f"ECRT_minus_{baseline}"] = comparison
    (out / "statistical_analysis.json").write_text(json.dumps(clean_json(summary), indent=2, allow_nan=False))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/real_week3_json_v1")
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    output = Path(args.output)
    manifest, tasks, predictions, missing = load_inputs(output)
    print(f"predictions={len(predictions)} missing={len(missing)}", flush=True)
    if missing and not args.allow_partial:
        raise RuntimeError("Ledger is incomplete; run run_real_week3.py until missing=0")
    analysis_dir = output / "analysis"
    analysis_dir.mkdir(exist_ok=True)
    audit = capability_audit(manifest, tasks, predictions, analysis_dir)
    print(f"test_winners={audit['test_winners']}", flush=True)
    if missing:
        print("Partial capability audit saved. Factorial grid requires complete ledger.", flush=True)
        return
    rows = grid(manifest, tasks, predictions, analysis_dir)
    summary = summarize_grid(rows, analysis_dir)
    print(f"grid_rows={len(rows)} target_subjects={summary['design']['n_target_subjects']}", flush=True)


if __name__ == "__main__":
    main()
