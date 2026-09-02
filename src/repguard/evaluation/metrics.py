"""Evaluation metrics for RepGuard.

Provides accuracy computation, per-domain breakdown, and bootstrap
confidence intervals for the single-agent evaluation harness.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import numpy as np

from repguard.data.models import TaskRecord


def compute_accuracy(scores: list[bool]) -> float:
    """Compute overall accuracy from a list of boolean scores.

    Args:
        scores: List of boolean values (True = correct).

    Returns:
        Accuracy as a fraction in [0, 1]. Returns 0.0 if scores is empty.
    """
    if not scores:
        return 0.0
    return sum(scores) / len(scores)


def compute_per_domain_accuracy(
    tasks: list[TaskRecord],
    scores: list[bool],
) -> dict[str, dict[str, Any]]:
    """Compute accuracy broken down by domain/subject.

    Args:
        tasks: List of TaskRecords aligned with scores.
        scores: List of boolean scores aligned with tasks.

    Returns:
        Dictionary mapping subject names to accuracy statistics:
        {"subject": {"accuracy": float, "correct": int, "total": int}}.

    Raises:
        ValueError: If tasks and scores have different lengths.
    """
    if len(tasks) != len(scores):
        msg = f"tasks ({len(tasks)}) and scores ({len(scores)}) must have the same length"
        raise ValueError(msg)

    domain_correct: dict[str, int] = defaultdict(int)
    domain_total: dict[str, int] = defaultdict(int)

    for task, correct in zip(tasks, scores):
        subject = task.metadata.subject
        domain_total[subject] += 1
        if correct:
            domain_correct[subject] += 1

    result: dict[str, dict[str, Any]] = {}
    for subject in sorted(domain_total.keys()):
        total = domain_total[subject]
        correct = domain_correct[subject]
        result[subject] = {
            "accuracy": correct / total if total > 0 else 0.0,
            "correct": correct,
            "total": total,
        }

    return result


def bootstrap_confidence_interval(
    scores: list[bool],
    n_bootstrap: int = 1000,
    confidence: float = 0.95,
    seed: int = 42,
) -> tuple[float, float, float]:
    """Compute bootstrap confidence interval for accuracy.

    Args:
        scores: List of boolean scores.
        n_bootstrap: Number of bootstrap samples.
        confidence: Confidence level (e.g., 0.95 for 95% CI).
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (mean_accuracy, lower_bound, upper_bound).
    """
    if not scores:
        return (0.0, 0.0, 0.0)

    rng = np.random.default_rng(seed)
    arr = np.array(scores, dtype=np.float64)

    bootstrapped_means = np.empty(n_bootstrap)
    for i in range(n_bootstrap):
        sample = rng.choice(arr, size=len(arr), replace=True)
        bootstrapped_means[i] = sample.mean()

    alpha = 1 - confidence
    lower = float(np.percentile(bootstrapped_means, 100 * alpha / 2))
    upper = float(np.percentile(bootstrapped_means, 100 * (1 - alpha / 2)))
    mean = float(arr.mean())

    return (mean, lower, upper)
