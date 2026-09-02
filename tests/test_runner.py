"""Tests for the single-agent evaluation runner."""

from __future__ import annotations

from pathlib import Path

from repguard.config import RepGuardConfig
from repguard.data.mmlu_pro import create_synthetic_tasks
from repguard.harness.runner import SingleAgentRunner


class TestSingleAgentRunner:
    """Tests for the SingleAgentRunner."""

    def test_run_with_mock_provider(self, tmp_config: RepGuardConfig) -> None:
        """Runner should complete successfully with mock provider."""
        tasks = create_synthetic_tasks(n=50, seed=42)
        runner = SingleAgentRunner(tmp_config)
        result = runner.run(tasks=tasks, split_name="dev", max_tasks=5)

        assert result.num_tasks > 0
        assert 0.0 <= result.accuracy <= 1.0
        assert len(result.responses) == result.num_tasks
        assert len(result.scores) == result.num_tasks

    def test_run_produces_per_domain_accuracy(self, tmp_config: RepGuardConfig) -> None:
        """Runner should compute per-domain accuracy breakdown."""
        tasks = create_synthetic_tasks(n=50, seed=42)
        runner = SingleAgentRunner(tmp_config)
        result = runner.run(tasks=tasks, split_name="dev")

        assert len(result.per_domain_accuracy) > 0
        for domain, stats in result.per_domain_accuracy.items():
            assert "accuracy" in stats
            assert "correct" in stats
            assert "total" in stats

    def test_run_creates_log_file(self, tmp_config: RepGuardConfig) -> None:
        """Runner should create a structured log file."""
        tasks = create_synthetic_tasks(n=50, seed=42)
        runner = SingleAgentRunner(tmp_config)
        runner.run(tasks=tasks, split_name="dev")

        log_dir = Path(tmp_config.logging.log_dir)
        log_files = list(log_dir.glob("experiment_*.jsonl"))
        assert len(log_files) >= 1

    def test_run_with_cache(self, tmp_config: RepGuardConfig) -> None:
        """Second run should hit cache for previously evaluated tasks."""
        tasks = create_synthetic_tasks(n=50, seed=42)

        # First run
        runner1 = SingleAgentRunner(tmp_config)
        result1 = runner1.run(tasks=tasks, split_name="dev")

        # Second run with same config (should hit cache)
        runner2 = SingleAgentRunner(tmp_config)
        result2 = runner2.run(tasks=tasks, split_name="dev")

        # Results should be identical
        assert result1.accuracy == result2.accuracy
        # Second run should have cache hits
        assert result2.cache_stats["hits"] > 0
