"""End-to-end smoke test for the RepGuard pipeline.

This test validates the complete pipeline from data loading through
evaluation without requiring any API keys (uses MockProvider).
"""

from __future__ import annotations

import pytest

from repguard.config import RepGuardConfig
from repguard.data.mmlu_pro import create_synthetic_tasks
from repguard.data.splits import create_splits, verify_no_leakage
from repguard.evaluation.metrics import bootstrap_confidence_interval, compute_accuracy
from repguard.harness.prompts import format_prompt
from repguard.harness.parser import parse_response
from repguard.harness.runner import SingleAgentRunner
from repguard.providers.base import create_provider
from repguard.seed import SeedManager


@pytest.mark.smoke
class TestSmokeEndToEnd:
    """Complete end-to-end smoke tests."""

    def test_full_pipeline_smoke(self, tmp_config: RepGuardConfig) -> None:
        """Full pipeline: load → split → prompt → query → parse → score.

        This test validates every component in sequence without API keys.
        """
        # 1. Generate synthetic data
        tasks = create_synthetic_tasks(n=50, seed=42)
        assert len(tasks) == 50

        # 2. Create splits
        sm = SeedManager(42)
        train, dev, test = create_splits(tasks, sm)
        assert verify_no_leakage(train, dev, test) is True
        assert train.size + dev.size + test.size == 50

        # 3. Verify GT isolation
        for view in dev.online_views:
            assert not hasattr(view, "ground_truth_answer")

        # 4. Format a prompt
        sample = dev.records[0] if dev.size > 0 else train.records[0]
        prompt = format_prompt(sample, mode="direct")
        assert len(prompt.text) > 0
        assert len(prompt.prompt_hash) == 16

        # 5. Query mock provider
        provider = create_provider(tmp_config.provider)
        response = provider.complete(prompt.text)
        assert len(response.content) > 0
        assert response.cost_usd == 0.0  # Mock is free

        # 6. Parse response
        parsed = parse_response(response.content, num_options=prompt.num_options)
        assert parsed.answer in ("UNKNOWN", *[chr(ord("A") + i) for i in range(10)])

        # 7. Score (offline evaluator)
        is_correct = sample.check_answer(parsed.answer)
        assert isinstance(is_correct, bool)

    def test_runner_smoke(self, tmp_config: RepGuardConfig) -> None:
        """SingleAgentRunner should complete a full evaluation run."""
        tasks = create_synthetic_tasks(n=20, seed=42)
        runner = SingleAgentRunner(tmp_config)
        result = runner.run(tasks=tasks, split_name="dev")

        assert result.num_tasks > 0
        assert 0.0 <= result.accuracy <= 1.0
        assert len(result.responses) == result.num_tasks
        assert len(result.per_domain_accuracy) > 0

    def test_reproducibility(self, tmp_config: RepGuardConfig) -> None:
        """Two runs with the same config should produce identical results."""
        tasks = create_synthetic_tasks(n=15, seed=42)

        runner1 = SingleAgentRunner(tmp_config)
        result1 = runner1.run(tasks=tasks, split_name="dev")

        runner2 = SingleAgentRunner(tmp_config)
        result2 = runner2.run(tasks=tasks, split_name="dev")

        assert result1.accuracy == result2.accuracy
        for r1, r2 in zip(result1.responses, result2.responses):
            assert r1.parsed_answer == r2.parsed_answer

    def test_metrics_computation(self) -> None:
        """Metrics functions should work with boolean score lists."""
        scores = [True, True, False, True, False]
        accuracy = compute_accuracy(scores)
        assert accuracy == 0.6

        mean, lower, upper = bootstrap_confidence_interval(scores, seed=42)
        assert lower <= mean <= upper
        assert 0.0 <= lower
        assert upper <= 1.0
