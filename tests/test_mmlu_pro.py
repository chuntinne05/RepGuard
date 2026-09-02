"""Tests for MMLU-Pro data loading and synthetic task generation."""

from __future__ import annotations

from repguard.data.mmlu_pro import (
    SUBJECT_TO_DOMAIN,
    SUBJECT_TO_SKILL_FAMILY,
    create_synthetic_tasks,
)
from repguard.data.models import TaskRecord


class TestCreateSyntheticTasks:
    """Tests for the synthetic task generator."""

    def test_returns_correct_count(self) -> None:
        """Should return the requested number of tasks."""
        tasks = create_synthetic_tasks(n=30, seed=42)
        assert len(tasks) == 30

    def test_returns_task_records(self) -> None:
        """All items should be TaskRecord instances."""
        tasks = create_synthetic_tasks(n=10, seed=42)
        for task in tasks:
            assert isinstance(task, TaskRecord)

    def test_tasks_have_valid_gt(self) -> None:
        """Each task should have a valid ground truth answer."""
        tasks = create_synthetic_tasks(n=20, seed=42)
        for task in tasks:
            assert task.ground_truth_answer in "ABCDEFGHIJ"
            assert 0 <= task.ground_truth_index < len(task.options)

    def test_tasks_cover_multiple_subjects(self) -> None:
        """Synthetic tasks should span multiple subjects."""
        tasks = create_synthetic_tasks(n=50, seed=42)
        subjects = {t.metadata.subject for t in tasks}
        assert len(subjects) >= 5

    def test_deterministic_generation(self) -> None:
        """Same seed should produce identical tasks."""
        tasks1 = create_synthetic_tasks(n=20, seed=99)
        tasks2 = create_synthetic_tasks(n=20, seed=99)
        for t1, t2 in zip(tasks1, tasks2):
            assert t1.task_id == t2.task_id
            assert t1.question == t2.question
            assert t1.ground_truth_answer == t2.ground_truth_answer

    def test_different_seeds_produce_different_tasks(self) -> None:
        """Different seeds should produce different tasks."""
        tasks1 = create_synthetic_tasks(n=20, seed=1)
        tasks2 = create_synthetic_tasks(n=20, seed=2)
        # At least some tasks should differ
        differences = sum(
            t1.ground_truth_answer != t2.ground_truth_answer
            for t1, t2 in zip(tasks1, tasks2)
        )
        assert differences > 0

    def test_metadata_has_valid_domain(self) -> None:
        """All tasks should have domains from the mapping."""
        tasks = create_synthetic_tasks(n=50, seed=42)
        valid_domains = set(SUBJECT_TO_DOMAIN.values())
        for task in tasks:
            assert task.metadata.domain in valid_domains

    def test_metadata_has_valid_skill_family(self) -> None:
        """All tasks should have skill families from the mapping."""
        tasks = create_synthetic_tasks(n=50, seed=42)
        valid_families = set(SUBJECT_TO_SKILL_FAMILY.values())
        for task in tasks:
            assert task.metadata.skill_family in valid_families

    def test_unique_task_ids(self) -> None:
        """All task IDs should be unique."""
        tasks = create_synthetic_tasks(n=100, seed=42)
        ids = [t.task_id for t in tasks]
        assert len(ids) == len(set(ids))
