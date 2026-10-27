#!/usr/bin/env python3
"""Count when improved reputation calibration actually changes real decisions.

Uses candidate-conditioned judge feedback from the existing two-fold Week 5
analysis and replays the already examined Week 3 test. This is exploratory.
"""

from __future__ import annotations

import json
from pathlib import Path

from analyze_real_week3 import AGENTS, FixedBorrow, StudyTransferEstimator, choose_answer, load_inputs
from analyze_real_week5_feedback_impact import episodes_for, load_judgments
from repguard.reputation.ecrt import ECRTReputation, FeedbackReliabilityEstimator


def run() -> dict:
    week3 = Path("results/real_week3_json_v1")
    judge = Path("results/real_week5_modal_judge_v1")
    manifest, tasks, predictions, missing = load_inputs(week3)
    if missing:
        raise RuntimeError("Week 3 ledger incomplete")
    judge_manifest, judgments = load_judgments(judge)
    selected = judge_manifest["selected_history_ids"]
    transfer = StudyTransferEstimator()
    folds = []
    for fold in (0, 1):
        audit = [ep for subject, ids in sorted(selected.items())
                 for ep in episodes_for(ids[:10] if fold == 0 else ids[10:],
                                        subject, tasks, predictions, judgments)]
        reliability = FeedbackReliabilityEstimator().calibrate(audit)
        totals = {"questions": 0, "different_final_answers": 0,
                  "ecrt_only_correct": 0, "fixed_only_correct": 0,
                  "mean_absolute_reputation_shift_sum": 0.0,
                  "subject_breakdown": {}}
        for subject, ids in sorted(selected.items()):
            history = episodes_for(ids[10:] if fold == 0 else ids[:10],
                                   subject, tasks, predictions, judgments)
            fixed = FixedBorrow(history, transfer)
            ecrt = ECRTReputation(transfer, reliability).fit(history)
            fixed_scores = {a: fixed.score(a, subject) for a in AGENTS}
            ecrt_scores = {a: ecrt.score(a, subject) for a in AGENTS}
            shift = sum(abs(ecrt_scores[a].mean - fixed_scores[a].mean) for a in AGENTS) / len(AGENTS)
            subject_counts = {"n": 0, "different": 0, "ecrt_only": 0,
                              "fixed_only": 0, "mean_absolute_reputation_shift": round(shift, 6)}
            for tid in manifest["selected"]["test"][subject]:
                answers = {a: predictions[a, tid]["answer"] for a in AGENTS}
                f_answer = choose_answer(answers, fixed_scores, "FixedBorrow", tid)
                e_answer = choose_answer(answers, ecrt_scores, "ECRT", tid)
                f_correct = f_answer == tasks[tid].ground_truth_answer
                e_correct = e_answer == tasks[tid].ground_truth_answer
                subject_counts["n"] += 1
                subject_counts["different"] += int(f_answer != e_answer)
                subject_counts["ecrt_only"] += int(e_correct and not f_correct)
                subject_counts["fixed_only"] += int(f_correct and not e_correct)
            totals["questions"] += subject_counts["n"]
            totals["different_final_answers"] += subject_counts["different"]
            totals["ecrt_only_correct"] += subject_counts["ecrt_only"]
            totals["fixed_only_correct"] += subject_counts["fixed_only"]
            totals["mean_absolute_reputation_shift_sum"] += shift * subject_counts["n"]
            totals["subject_breakdown"][subject] = subject_counts
        totals["fold"] = fold
        totals["mean_absolute_reputation_shift"] = round(
            totals.pop("mean_absolute_reputation_shift_sum") / totals["questions"], 6)
        folds.append(totals)
    result = {"status": "exploratory_reused_week3_test",
              "judge_protocol_hash": judge_manifest["protocol_hash"],
              "condition": "same_subject_real_candidate_judge_feedback",
              "folds": folds}
    out = Path("results/real_next_study_v1/decision_sensitivity.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    data = run()
    print(json.dumps([{k: v for k, v in fold.items() if k != "subject_breakdown"}
                      for fold in data["folds"]], indent=2))
