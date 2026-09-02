"""Tests for deterministic data splitting and leakage verification."""

from __future__ import annotations

import pytest

from repguard.data.models import TaskRecord
from repguard.data.splits import create_splits, verify_no_leakage
from repguard.seed import SeedManager


class TestCreateSplits:
    """Tests for the split creation function."""

    def test_splits_are_exhaustive(self, sample_tasks: list[TaskRecord]) -> None:
        """All tasks must appear in exactly one split."""
        sm = SeedManager(42)
        train, dev, test = create_splits(sample_tasks, sm)
        total = train.size + dev.size + test.size
        assert total == len(sample_tasks)

    def test_splits_are_disjoint(self, sample_tasks: list[TaskRecord]) -> None:
        """No task should appear in more than one split."""
        sm = SeedManager(42)
        train, dev, test = create_splits(sample_tasks, sm)
        # verify_no_leakage raises ValueError on overlap
        assert verify_no_leakage(train, dev, test) is True

    def test_splits_are_deterministic(self, sample_tasks: list[TaskRecord]) -> None:
        """Same seed + data should produce identical splits."""
        sm1 = SeedManager(42)
        sm2 = SeedManager(42)
        train1, dev1, test1 = create_splits(sample_tasks, sm1)
        train2, dev2, test2 = create_splits(sample_tasks, sm2)
        assert train1.task_ids == train2.task_ids
        assert dev1.task_ids == dev2.task_ids
        assert test1.task_ids == test2.task_ids

    def test_different_seeds_produce_different_splits(
        self, sample_tasks: list[TaskRecord]
    ) -> None:
        """Different seeds should produce different splits."""
        sm1 = SeedManager(42)
        sm2 = SeedManager(99)
        train1, _, _ = create_splits(sample_tasks, sm1)
        train2, _, _ = create_splits(sample_tasks, sm2)
        # With high probability, the splits will differ
        assert train1.task_ids != train2.task_ids

    def test_approximate_ratios(self, sample_tasks: list[TaskRecord]) -> None:
        """Split sizes should approximately match requested ratios."""
        sm = SeedManager(42)
        # Use a larger sample for better ratio approximation
        from repguard.data.mmlu_pro import create_synthetic_tasks
        large_tasks = create_synthetic_tasks(n=500, seed=42)

        train, dev, test = create_splits(large_tasks, sm, 0.6, 0.2, 0.2)
        total = len(large_tasks)

        # Allow ±10% tolerance for hash-based splitting
        assert abs(train.size / total - 0.6) < 0.10
        assert abs(dev.size / total - 0.2) < 0.10
        assert abs(test.size / total - 0.2) < 0.10

    def test_online_views_have_no_gt(self, sample_tasks: list[TaskRecord]) -> None:
        """OnlineTaskViews in splits should lack GT fields."""
        sm = SeedManager(42)
        train, _, _ = create_splits(sample_tasks, sm)
        for view in train.online_views:
            assert not hasattr(view, "ground_truth_answer")
            assert not hasattr(view, "ground_truth_index")

    def test_empty_records_raises(self) -> None:
        """Splitting empty records should raise ValueError."""
        sm = SeedManager(42)
        with pytest.raises(ValueError, match="empty"):
            create_splits([], sm)

    def test_invalid_ratios_raise(self, sample_tasks: list[TaskRecord]) -> None:
        """Ratios not summing to 1.0 should raise ValueError."""
        sm = SeedManager(42)
        with pytest.raises(ValueError, match="sum to 1.0"):
            create_splits(sample_tasks, sm, 0.5, 0.3, 0.3)

    def test_subject_distribution(self, sample_tasks: list[TaskRecord]) -> None:
        """Each split should contain multiple subjects."""
        sm = SeedManager(42)
        train, dev, test = create_splits(sample_tasks, sm)
        # With 50 tasks across 14 subjects, each non-empty split should have ≥2
        for split in [train, dev, test]:
            if split.size > 5:
                assert len(split.subject_distribution()) >= 2
