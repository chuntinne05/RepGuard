"""Response parsing for multiple-choice answer extraction.

Extracts the answer choice letter from LLM responses using a sequence
of regex patterns, handling various response formats: direct answers,
chain-of-thought conclusions, and edge cases (refusals, multi-answer).
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ParseResult:
    """Result of parsing an LLM response for an answer choice.

    Attributes:
        answer: Extracted answer letter (e.g., "A", "B") or "UNKNOWN" if parsing fails.
        confidence: Parser confidence in the extraction (1.0 = high, 0.0 = fallback).
        method: Which parsing strategy succeeded.
        raw_response: The original response text.
    """

    answer: str
    confidence: float
    method: str
    raw_response: str

    @property
    def is_valid(self) -> bool:
        """Whether a valid answer was extracted."""
        return self.answer != "UNKNOWN"


# Ordered list of extraction patterns, from most to least specific.
# Each pattern is (name, compiled_regex, group_index).
_PATTERNS: list[tuple[str, re.Pattern[str], int]] = [
    # "The answer is X" / "The answer is (X)"
    (
        "the_answer_is",
        re.compile(r"[Tt]he\s+answer\s+is\s*[:\s]*\(?([A-Ja-j])\)?", re.IGNORECASE),
        1,
    ),
    # "Answer: X" at end of response
    (
        "answer_colon",
        re.compile(r"[Aa]nswer\s*:\s*\(?([A-Ja-j])\)?", re.IGNORECASE),
        1,
    ),
    # Standalone letter with optional parentheses/period at end of text
    (
        "trailing_letter",
        re.compile(r"[\n\s]\(?([A-Ja-j])\)?\.?\s*$"),
        1,
    ),
    # "Option X" or "choice X"
    (
        "option_mention",
        re.compile(r"(?:option|choice)\s+\(?([A-Ja-j])\)?", re.IGNORECASE),
        1,
    ),
    # "is X." or "is (X)"
    (
        "is_letter",
        re.compile(r"\bis\s+\(?([A-Ja-j])\)?[.\s]", re.IGNORECASE),
        1,
    ),
    # Single letter response (entire response is just a letter)
    (
        "single_letter",
        re.compile(r"^\s*\(?([A-Ja-j])\)?\s*\.?\s*$"),
        1,
    ),
]


def parse_response(
    response_text: str,
    num_options: int = 10,
) -> ParseResult:
    """Extract the answer choice letter from an LLM response.

    Tries multiple regex patterns in order of specificity. If no pattern
    matches, returns "UNKNOWN" with zero confidence.

    Args:
        response_text: The raw LLM response text.
        num_options: Number of valid answer options (limits valid letters).

    Returns:
        ParseResult with the extracted answer and metadata.
    """
    if not response_text or not response_text.strip():
        return ParseResult(
            answer="UNKNOWN",
            confidence=0.0,
            method="empty_response",
            raw_response=response_text,
        )

    # Determine valid answer letters based on num_options
    valid_letters = {chr(ord("A") + i) for i in range(min(num_options, 10))}

    # Try each pattern in order
    for name, pattern, group_idx in _PATTERNS:
        match = pattern.search(response_text)
        if match:
            letter = match.group(group_idx).upper()
            if letter in valid_letters:
                # Higher confidence for more specific patterns
                confidence = 1.0 if name in ("the_answer_is", "answer_colon") else 0.8
                return ParseResult(
                    answer=letter,
                    confidence=confidence,
                    method=name,
                    raw_response=response_text,
                )

    # Last resort: find ANY valid letter in the response (lowest confidence)
    all_letters = re.findall(r"\b([A-Ja-j])\b", response_text)
    valid_found = [l.upper() for l in all_letters if l.upper() in valid_letters]

    if valid_found:
        # Take the last mentioned letter (usually the conclusion)
        return ParseResult(
            answer=valid_found[-1],
            confidence=0.3,
            method="last_letter_fallback",
            raw_response=response_text,
        )

    return ParseResult(
        answer="UNKNOWN",
        confidence=0.0,
        method="no_match",
        raw_response=response_text,
    )
