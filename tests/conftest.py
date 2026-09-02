"""Shared test fixtures for RepGuard test suite."""

from __future__ import annotations

from pathlib import Path

import pytest

from repguard.config import RepGuardConfig
from repguard.data.mmlu_pro import create_synthetic_tasks
from repguard.data.models import TaskMetadata, TaskRecord
from repguard.seed import SeedManager


@pytest.fixture
def seed_manager() -> SeedManager:
    """Provide a SeedManager with a fixed master seed."""
    return SeedManager(master_seed=42)


@pytest.fixture
def sample_task() -> TaskRecord:
    """Provide a single sample TaskRecord for testing."""
    return TaskRecord(
        task_id="test_001",
        question="What is the capital of France?",
        options=("Paris", "London", "Berlin", "Madrid"),
        ground_truth_answer="A",
        ground_truth_index=0,
        metadata=TaskMetadata(
            domain="Humanities",
            subject="history",
            difficulty="easy",
            skill_family="humanities_knowledge",
        ),
    )


@pytest.fixture
def sample_tasks() -> list[TaskRecord]:
    """Provide a list of synthetic tasks for testing."""
    return create_synthetic_tasks(n=50, seed=42)


@pytest.fixture
def default_config(tmp_path: Path) -> RepGuardConfig:
    """Provide a default config pointing to temporary directories."""
    return RepGuardConfig(
        experiment=RepGuardConfig.model_fields["experiment"].default_factory(),  # type: ignore[misc]
        data=RepGuardConfig.model_fields["data"].default_factory(),  # type: ignore[misc]
        provider=RepGuardConfig.model_fields["provider"].default_factory(),  # type: ignore[misc]
        harness=RepGuardConfig.model_fields["harness"].default_factory(),  # type: ignore[misc]
        logging=RepGuardConfig.model_fields["logging"].default_factory(),  # type: ignore[misc]
    )


@pytest.fixture
def tmp_config(tmp_path: Path) -> RepGuardConfig:
    """Provide a config with all paths pointing to tmp_path."""
    from repguard.config import (
        CacheConfig,
        DataConfig,
        ExperimentConfig,
        HarnessConfig,
        LoggingConfig,
        ProviderConfig,
    )

    return RepGuardConfig(
        experiment=ExperimentConfig(name="test_run", seed=42),
        data=DataConfig(data_dir=str(tmp_path / "data")),
        provider=ProviderConfig(name="mock", model_id="mock-test-v1"),
        harness=HarnessConfig(
            cache=CacheConfig(enabled=True, cache_dir=str(tmp_path / "cache")),
        ),
        logging=LoggingConfig(log_dir=str(tmp_path / "logs")),
    )
