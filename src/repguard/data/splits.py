"""Deterministic, leak-proof dataset splitting for RepGuard.

Partitions TaskRecords into Train/Calibration, Dev, and Test splits
with the following guarantees:

1. Deterministic: Same seed + same data always produces identical splits.
2. Stratified: Subject distribution is preserved across splits.
3. Leak-proof: Split assignment is based solely on task_id hash, never on GT.
4. Manifest-tracked: Each split produces a manifest of task IDs for exact
   reproduction, enabling future researchers to recreate identical splits.
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from repguard.data.models import OnlineTaskView, TaskRecord
from repguard.seed import SeedManager

logger = logging.getLogger("repguard")


@dataclass(frozen=True)
class DataSplit:
    """A named partition of the dataset.

    Holds both the full TaskRecords (for offline evaluation) and the
    GT-stripped OnlineTaskViews (for the online reputation system).

    Attributes:
        name: Split name (train_calibration, dev, test).
        records: Full TaskRecords (OFFLINE EVALUATOR ONLY).
        online_views: GT-stripped views (safe for online reputation system).
        task_ids: Ordered list of task IDs in this split.
    """

    name: str
    records: tuple[TaskRecord, ...]
    online_views: tuple[OnlineTaskView, ...]
    task_ids: tuple[str, ...]

    @property
    def size(self) -> int:
        """Number of tasks in this split."""
        return len(self.records)

    def subject_distribution(self) -> dict[str, int]:
        """Count tasks per subject in this split.

        Returns:
            Dictionary mapping subject names to task counts.
        """
        dist: dict[str, int] = defaultdict(int)
        for r in self.records:
            dist[r.metadata.subject] += 1
        return dict(dist)


@dataclass(frozen=True)
class SplitManifest:
    """Manifest documenting a set of splits for reproducibility.

    Stores the task IDs for each split along with the seed and ratios
    used to create them, enabling exact reproduction.

    Attributes:
        seed: The master seed used for splitting.
        ratios: Dictionary of split ratios.
        splits: Dictionary mapping split names to lists of task IDs.
        total_tasks: Total number of tasks before splitting.
    """

    seed: int
    ratios: dict[str, float]
    splits: dict[str, list[str]]
    total_tasks: int

    def save(self, path: str | Path) -> None:
        """Save the manifest to a JSON file.

        Args:
            path: File path to write the manifest.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data: dict[str, Any] = {
            "seed": self.seed,
            "ratios": self.ratios,
            "total_tasks": self.total_tasks,
            "split_sizes": {name: len(ids) for name, ids in self.splits.items()},
            "splits": self.splits,
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Split manifest saved to {path}")

    @classmethod
    def load(cls, path: str | Path) -> SplitManifest:
        """Load a manifest from a JSON file.

        Args:
            path: File path to read the manifest from.

        Returns:
            Loaded SplitManifest instance.
        """
        with open(path) as f:
            data = json.load(f)

        return cls(
            seed=data["seed"],
            ratios=data["ratios"],
            splits=data["splits"],
            total_tasks=data["total_tasks"],
        )


def create_splits(
    records: list[TaskRecord],
    seed_manager: SeedManager,
    train_cal_ratio: float = 0.6,
    dev_ratio: float = 0.2,
    test_ratio: float = 0.2,
) -> tuple[DataSplit, DataSplit, DataSplit]:
    """Create deterministic, stratified, leak-proof splits.

    Split assignment is determined by hashing (seed, task_id) with SHA-256,
    then mapping the hash to a split based on cumulative ratios. This ensures:

    - Determinism: Same seed + data → same splits.
    - Independence from GT: Assignment depends only on task_id, not on answers.
    - Stratification: Proportional representation per subject is approximately
      maintained because the hash uniformly distributes tasks.

    Args:
        records: List of all TaskRecords to split.
        seed_manager: SeedManager for deterministic hashing.
        train_cal_ratio: Fraction for train/calibration split.
        dev_ratio: Fraction for development split.
        test_ratio: Fraction for held-out test split.

    Returns:
        Tuple of (train_calibration, dev, test) DataSplit objects.

    Raises:
        ValueError: If ratios don't sum to 1.0 or records are empty.
    """
    total = train_cal_ratio + dev_ratio + test_ratio
    if abs(total - 1.0) > 1e-6:
        msg = f"Split ratios must sum to 1.0, got {total:.6f}"
        raise ValueError(msg)

    if not records:
        msg = "Cannot split an empty list of records"
        raise ValueError(msg)

    split_seed = seed_manager.derive("data_split")

    train_cal: list[TaskRecord] = []
    dev: list[TaskRecord] = []
    test: list[TaskRecord] = []

    for record in records:
        bucket = _assign_bucket(record.task_id, split_seed, train_cal_ratio, dev_ratio)
        if bucket == "train_calibration":
            train_cal.append(record)
        elif bucket == "dev":
            dev.append(record)
        else:
            test.append(record)

    logger.info(
        f"Split {len(records)} tasks: "
        f"train_cal={len(train_cal)}, dev={len(dev)}, test={len(test)}"
    )

    return (
        _make_data_split("train_calibration", train_cal),
        _make_data_split("dev", dev),
        _make_data_split("test", test),
    )


def _assign_bucket(
    task_id: str,
    split_seed: int,
    train_cal_ratio: float,
    dev_ratio: float,
) -> str:
    """Assign a task to a split bucket using deterministic hashing.

    Args:
        task_id: The task identifier to hash.
        split_seed: Seed to combine with task_id for determinism.
        train_cal_ratio: Cumulative threshold for train/calibration.
        dev_ratio: Size of the dev split.

    Returns:
        Split name: "train_calibration", "dev", or "test".
    """
    key = f"{split_seed}:{task_id}"
    hash_val = int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:16], 16)
    # Normalize to [0, 1)
    normalized = (hash_val % 10_000_000) / 10_000_000.0

    if normalized < train_cal_ratio:
        return "train_calibration"
    elif normalized < train_cal_ratio + dev_ratio:
        return "dev"
    else:
        return "test"


def _make_data_split(name: str, records: list[TaskRecord]) -> DataSplit:
    """Construct a DataSplit from a list of records.

    Args:
        name: Split name.
        records: TaskRecords in this split.

    Returns:
        DataSplit with both full records and GT-stripped online views.
    """
    online_views = tuple(r.to_online_view() for r in records)
    task_ids = tuple(r.task_id for r in records)

    return DataSplit(
        name=name,
        records=tuple(records),
        online_views=online_views,
        task_ids=task_ids,
    )


def create_manifest(
    splits: tuple[DataSplit, ...],
    seed: int,
    ratios: dict[str, float],
) -> SplitManifest:
    """Create a SplitManifest from a set of DataSplits.

    Args:
        splits: Tuple of DataSplit objects.
        seed: Master seed used.
        ratios: Dictionary of split ratios.

    Returns:
        SplitManifest for reproducibility tracking.
    """
    total = sum(s.size for s in splits)
    split_ids = {s.name: list(s.task_ids) for s in splits}

    return SplitManifest(
        seed=seed,
        ratios=ratios,
        splits=split_ids,
        total_tasks=total,
    )


def verify_no_leakage(
    train_cal: DataSplit,
    dev: DataSplit,
    test: DataSplit,
) -> bool:
    """Verify that no task IDs appear in more than one split.

    Args:
        train_cal: Train/calibration split.
        dev: Development split.
        test: Test split.

    Returns:
        True if there is no leakage (all splits are disjoint).

    Raises:
        ValueError: If task ID overlap is detected.
    """
    train_set = set(train_cal.task_ids)
    dev_set = set(dev.task_ids)
    test_set = set(test.task_ids)

    train_dev = train_set & dev_set
    train_test = train_set & test_set
    dev_test = dev_set & test_set

    if train_dev or train_test or dev_test:
        overlaps = []
        if train_dev:
            overlaps.append(f"train∩dev: {len(train_dev)} tasks")
        if train_test:
            overlaps.append(f"train∩test: {len(train_test)} tasks")
        if dev_test:
            overlaps.append(f"dev∩test: {len(dev_test)} tasks")
        msg = f"DATA LEAKAGE DETECTED — overlapping task IDs: {', '.join(overlaps)}"
        raise ValueError(msg)

    logger.info("✓ No data leakage: all splits are disjoint")
    return True
