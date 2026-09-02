"""Tests for core data models and GT isolation."""

from __future__ import annotations

import pytest

from repguard.data.models import (
    AgentResponse,
    FeedbackSignal,
    FeedbackSourceType,
    OnlineTaskView,
    TaskMetadata,
    TaskRecord,
)


class TestTaskRecord:
    """Tests for TaskRecord and GT isolation."""

    def test_to_online_view_strips_gt(self, sample_task: TaskRecord) -> None:
        """OnlineTaskView must NOT contain ground truth fields."""
        view = sample_task.to_online_view()
        assert isinstance(view, OnlineTaskView)
        assert not hasattr(view, "ground_truth_answer")
        assert not hasattr(view, "ground_truth_index")

    def test_online_view_preserves_non_gt_fields(self, sample_task: TaskRecord) -> None:
        """OnlineTaskView should preserve question, options, metadata."""
        view = sample_task.to_online_view()
        assert view.task_id == sample_task.task_id
        assert view.question == sample_task.question
        assert view.options == sample_task.options
        assert view.metadata == sample_task.metadata

    def test_check_answer_correct(self, sample_task: TaskRecord) -> None:
        """check_answer should return True for correct answer."""
        assert sample_task.check_answer("A") is True
        assert sample_task.check_answer("a") is True
        assert sample_task.check_answer(" A ") is True

    def test_check_answer_incorrect(self, sample_task: TaskRecord) -> None:
        """check_answer should return False for wrong answer."""
        assert sample_task.check_answer("B") is False
        assert sample_task.check_answer("C") is False
        assert sample_task.check_answer("X") is False

    def test_task_record_is_frozen(self, sample_task: TaskRecord) -> None:
        """TaskRecord should be immutable (frozen dataclass)."""
        with pytest.raises(AttributeError):
            sample_task.task_id = "modified"  # type: ignore[misc]

    def test_online_view_is_frozen(self, sample_task: TaskRecord) -> None:
        """OnlineTaskView should be immutable."""
        view = sample_task.to_online_view()
        with pytest.raises(AttributeError):
            view.task_id = "modified"  # type: ignore[misc]


class TestOnlineTaskViewIsolation:
    """Tests ensuring OnlineTaskView cannot leak GT."""

    def test_no_gt_attribute_access(self, sample_task: TaskRecord) -> None:
        """Attempting to access GT on OnlineTaskView should fail."""
        view = sample_task.to_online_view()

        with pytest.raises(AttributeError):
            _ = view.ground_truth_answer  # type: ignore[attr-defined]

        with pytest.raises(AttributeError):
            _ = view.ground_truth_index  # type: ignore[attr-defined]

    def test_online_view_dir_has_no_gt(self, sample_task: TaskRecord) -> None:
        """dir() of OnlineTaskView should not list GT fields."""
        view = sample_task.to_online_view()
        attrs = dir(view)
        assert "ground_truth_answer" not in attrs
        assert "ground_truth_index" not in attrs


class TestFeedbackSignal:
    """Tests for FeedbackSignal."""

    def test_feedback_signal_creation(self) -> None:
        """FeedbackSignal should be creatable with expected fields."""
        signal = FeedbackSignal(
            task_id="task_001",
            agent_id="agent_1",
            observed_correct=True,
            confidence=0.8,
            source_type=FeedbackSourceType.LLM_JUDGE,
        )
        assert signal.observed_correct is True
        assert signal.confidence == 0.8
        assert signal.source_type == FeedbackSourceType.LLM_JUDGE

    def test_feedback_absent(self) -> None:
        """FeedbackSignal with None observed_correct represents absent feedback."""
        signal = FeedbackSignal(
            task_id="task_001",
            agent_id="agent_1",
            observed_correct=None,
            source_type=FeedbackSourceType.ABSENT,
        )
        assert signal.observed_correct is None


class TestAgentResponse:
    """Tests for AgentResponse."""

    def test_agent_response_creation(self) -> None:
        """AgentResponse should store all expected fields."""
        response = AgentResponse(
            agent_id="agent_gpt4",
            task_id="task_001",
            raw_response="The answer is B.",
            parsed_answer="B",
            model_id="gpt-4o",
            prompt_hash="abc123",
        )
        assert response.parsed_answer == "B"
        assert response.model_id == "gpt-4o"
