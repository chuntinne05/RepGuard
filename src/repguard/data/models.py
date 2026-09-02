"""Core data models for RepGuard.

Implements the architectural separation between offline ground-truth data
and online views. This is the primary mechanism preventing GT leakage:

- TaskRecord: Full record including ground truth. Used ONLY by the offline
  evaluator and feedback simulation setup.
- OnlineTaskView: GT-stripped projection. The online reputation mechanism
  operates exclusively on this type and physically cannot access GT.
- TaskMetadata: Domain, subject, difficulty, and skill metadata.
- FeedbackSignal: Noisy observation with source type (never contains raw GT).
- AgentResponse: Agent answer with metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class FeedbackSourceType(Enum):
    """Type of feedback source that generated an observation.

    Used to track the provenance and expected reliability of feedback signals.
    """

    ORACLE = "oracle"                 # Ground truth (only under explicit oracle condition)
    NOISY_OBJECTIVE = "noisy_objective"  # Objective label with controlled noise
    SPARSE = "sparse"                  # Feedback revealed with probability rho
    LLM_JUDGE = "llm_judge"           # LLM-as-a-Judge evaluation
    PEER_AGREEMENT = "peer_agreement"  # Agreement among agents
    MIXED = "mixed"                    # Combination of sources
    ABSENT = "absent"                  # No feedback available


@dataclass(frozen=True)
class TaskMetadata:
    """Metadata describing a task's domain, subject, and attributes.

    Used for task-transfer estimation and stratified analysis. This metadata
    is available to the online reputation system (it describes the task, not
    the correctness of any answer).

    Attributes:
        domain: High-level domain (e.g., "STEM", "Humanities").
        subject: Specific subject (e.g., "physics", "history").
        difficulty: Difficulty indicator if available.
        skill_family: Grouping for transfer estimation.
        extra: Additional metadata key-value pairs.
    """

    domain: str
    subject: str
    difficulty: str = "unknown"
    skill_family: str = "general"
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TaskRecord:
    """Complete task record including ground truth.

    ⚠️ RESTRICTED ACCESS: This class contains ground truth and must be used
    ONLY by:
    - The offline evaluator (for scoring predictions)
    - Feedback simulation setup (for generating noisy signals)
    - Oracle baseline conditions

    The online reputation mechanism must NEVER receive TaskRecord objects.
    Use to_online_view() to create a GT-stripped projection.

    Attributes:
        task_id: Unique identifier for this task.
        question: The task question text.
        options: List of answer options (for multiple-choice).
        ground_truth_answer: The correct answer (OFFLINE ONLY).
        ground_truth_index: Index of the correct answer in options (OFFLINE ONLY).
        metadata: Task domain/subject/difficulty metadata.
        raw_data: Original data from the source benchmark.
    """

    task_id: str
    question: str
    options: tuple[str, ...]
    ground_truth_answer: str
    ground_truth_index: int
    metadata: TaskMetadata
    raw_data: dict[str, Any] = field(default_factory=dict)

    def to_online_view(self) -> OnlineTaskView:
        """Create a GT-stripped projection of this task.

        The returned OnlineTaskView physically lacks the ground_truth_answer
        and ground_truth_index fields. Code operating on OnlineTaskView
        cannot access GT even accidentally.

        Returns:
            An OnlineTaskView with no ground truth information.
        """
        return OnlineTaskView(
            task_id=self.task_id,
            question=self.question,
            options=self.options,
            metadata=self.metadata,
        )

    def check_answer(self, predicted: str) -> bool:
        """Check whether a predicted answer matches ground truth.

        ⚠️ This method should only be called by the offline evaluator.

        Args:
            predicted: The predicted answer string.

        Returns:
            True if the prediction matches the ground truth answer.
        """
        return predicted.strip().upper() == self.ground_truth_answer.strip().upper()


@dataclass(frozen=True)
class OnlineTaskView:
    """GT-stripped view of a task for the online reputation system.

    This dataclass physically does NOT contain ground truth. It is the
    only task representation that the online reputation mechanism should
    ever receive. This architectural constraint prevents accidental GT
    leakage into the reputation computation.

    Attributes:
        task_id: Unique identifier for this task.
        question: The task question text.
        options: List of answer options (for multiple-choice).
        metadata: Task domain/subject/difficulty metadata.
    """

    task_id: str
    question: str
    options: tuple[str, ...]
    metadata: TaskMetadata


@dataclass(frozen=True)
class FeedbackSignal:
    """A noisy observation about a historical interaction's outcome.

    This is what the online reputation system receives as evidence.
    It contains the feedback source's noisy assessment, NOT the raw
    ground-truth label.

    Attributes:
        task_id: The task this feedback pertains to.
        agent_id: The agent whose performance is assessed.
        observed_correct: The feedback source's (possibly noisy) assessment.
        confidence: The source's confidence in its assessment [0, 1].
        source_type: What kind of feedback produced this signal.
        source_id: Identifier for the specific feedback source.
        metadata: Additional feedback metadata.
    """

    task_id: str
    agent_id: str
    observed_correct: bool | None  # None = absent/unobserved
    confidence: float = 1.0
    source_type: FeedbackSourceType = FeedbackSourceType.ORACLE
    source_id: str = "default"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentResponse:
    """An agent's response to a task.

    Attributes:
        agent_id: Identifier for the agent.
        task_id: The task being answered.
        raw_response: The full text response from the LLM.
        parsed_answer: The extracted answer choice (e.g., "A", "B").
        model_id: The LLM model used.
        prompt_hash: SHA-256 hash of the prompt sent to the model.
        input_tokens: Number of input tokens.
        output_tokens: Number of output tokens.
        latency_ms: Response latency in milliseconds.
        cost_usd: Estimated cost of this call.
        cached: Whether the response was served from cache.
    """

    agent_id: str
    task_id: str
    raw_response: str
    parsed_answer: str
    model_id: str
    prompt_hash: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    cached: bool = False
