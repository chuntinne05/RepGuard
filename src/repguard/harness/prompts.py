"""Prompt formatting for multiple-choice evaluation.

Formats MMLU-Pro tasks into structured prompts for LLM evaluation.
Supports both direct-answer and chain-of-thought (CoT) modes.
All prompts are SHA-256 hashed for deterministic caching and logging.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from repguard.data.models import OnlineTaskView, TaskRecord


# Answer index to letter mapping
INDEX_TO_LETTER = {i: chr(ord("A") + i) for i in range(26)}


@dataclass(frozen=True)
class FormattedPrompt:
    """A formatted prompt ready for LLM evaluation.

    Attributes:
        text: The full prompt text to send to the LLM.
        prompt_hash: SHA-256 hash of the prompt text (first 16 hex chars).
        task_id: The task this prompt was generated for.
        mode: Prompt mode ("direct" or "cot").
        num_options: Number of answer options.
    """

    text: str
    prompt_hash: str
    task_id: str
    mode: str
    num_options: int


def format_prompt(
    task: TaskRecord | OnlineTaskView,
    mode: str = "direct",
) -> FormattedPrompt:
    """Format a task into a structured multiple-choice prompt.

    Accepts both TaskRecord and OnlineTaskView — the prompt is generated
    from the question and options only, never from ground truth.

    Args:
        task: The task to format (either full record or online view).
        mode: Prompt mode — "direct" for answer-only, "cot" for chain-of-thought.

    Returns:
        FormattedPrompt with the text, hash, and metadata.

    Raises:
        ValueError: If mode is not "direct" or "cot".
    """
    if mode not in ("direct", "cot"):
        msg = f"Invalid prompt mode: '{mode}'. Use 'direct' or 'cot'."
        raise ValueError(msg)

    options_text = _format_options(task.options)

    if mode == "direct":
        prompt_text = _build_direct_prompt(task.question, options_text, len(task.options))
    else:
        prompt_text = _build_cot_prompt(task.question, options_text, len(task.options))

    prompt_hash = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()[:16]

    return FormattedPrompt(
        text=prompt_text,
        prompt_hash=prompt_hash,
        task_id=task.task_id,
        mode=mode,
        num_options=len(task.options),
    )


def _format_options(options: tuple[str, ...]) -> str:
    """Format answer options as labeled lines.

    Args:
        options: Tuple of option texts.

    Returns:
        Formatted string with labeled options (A, B, C, ...).
    """
    lines = []
    for i, option in enumerate(options):
        letter = INDEX_TO_LETTER.get(i, str(i))
        lines.append(f"({letter}) {option}")
    return "\n".join(lines)


def _build_direct_prompt(question: str, options_text: str, num_options: int) -> str:
    """Build a direct-answer prompt (answer only, no reasoning).

    Args:
        question: The question text.
        options_text: Formatted options string.
        num_options: Number of options.

    Returns:
        Complete prompt text.
    """
    max_letter = INDEX_TO_LETTER.get(num_options - 1, "J")

    return (
        f"The following is a multiple choice question. "
        f"Select the correct answer from the options below.\n\n"
        f"Question: {question}\n\n"
        f"{options_text}\n\n"
        f"Answer with ONLY the letter of the correct option (A-{max_letter}). "
        f"Do not include any explanation.\n\n"
        f"Answer:"
    )


def _build_cot_prompt(question: str, options_text: str, num_options: int) -> str:
    """Build a chain-of-thought prompt (reasoning then answer).

    Args:
        question: The question text.
        options_text: Formatted options string.
        num_options: Number of options.

    Returns:
        Complete prompt text.
    """
    max_letter = INDEX_TO_LETTER.get(num_options - 1, "J")

    return (
        f"The following is a multiple choice question. Think through it step by step, "
        f"then select the correct answer.\n\n"
        f"Question: {question}\n\n"
        f"{options_text}\n\n"
        f"Think step by step, then conclude with your answer on the last line "
        f"in the format: 'The answer is X.' where X is the letter (A-{max_letter})."
    )
