"""Tests for prompt formatting."""

from __future__ import annotations

from repguard.data.models import TaskMetadata, TaskRecord
from repguard.harness.prompts import format_prompt


class TestFormatPrompt:
    """Tests for MC prompt formatting."""

    def test_direct_prompt_contains_question(self, sample_task: TaskRecord) -> None:
        """Direct prompt should include the question text."""
        result = format_prompt(sample_task, mode="direct")
        assert sample_task.question in result.text

    def test_direct_prompt_contains_options(self, sample_task: TaskRecord) -> None:
        """Direct prompt should include all answer options."""
        result = format_prompt(sample_task, mode="direct")
        for option in sample_task.options:
            assert option in result.text

    def test_cot_prompt_mentions_step_by_step(self, sample_task: TaskRecord) -> None:
        """CoT prompt should instruct step-by-step reasoning."""
        result = format_prompt(sample_task, mode="cot")
        assert "step by step" in result.text.lower()

    def test_prompt_hash_is_deterministic(self, sample_task: TaskRecord) -> None:
        """Same task should always produce the same prompt hash."""
        r1 = format_prompt(sample_task, mode="direct")
        r2 = format_prompt(sample_task, mode="direct")
        assert r1.prompt_hash == r2.prompt_hash

    def test_prompt_hash_differs_between_modes(self, sample_task: TaskRecord) -> None:
        """Direct and CoT modes should produce different hashes."""
        direct = format_prompt(sample_task, mode="direct")
        cot = format_prompt(sample_task, mode="cot")
        assert direct.prompt_hash != cot.prompt_hash

    def test_prompt_does_not_contain_gt(self, sample_task: TaskRecord) -> None:
        """Prompt text must NOT contain the ground truth answer explicitly."""
        result = format_prompt(sample_task, mode="direct")
        # The prompt should not say "the correct answer is A"
        assert "correct answer is A" not in result.text.lower()

    def test_online_view_produces_same_prompt(self, sample_task: TaskRecord) -> None:
        """OnlineTaskView should produce the same prompt as TaskRecord."""
        view = sample_task.to_online_view()
        r1 = format_prompt(sample_task, mode="direct")
        r2 = format_prompt(view, mode="direct")
        assert r1.text == r2.text
        assert r1.prompt_hash == r2.prompt_hash

    def test_metadata_is_captured(self, sample_task: TaskRecord) -> None:
        """FormattedPrompt should capture task_id and mode."""
        result = format_prompt(sample_task, mode="direct")
        assert result.task_id == sample_task.task_id
        assert result.mode == "direct"
        assert result.num_options == len(sample_task.options)
