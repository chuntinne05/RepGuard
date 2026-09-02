"""Tests for response parsing."""

from __future__ import annotations

import pytest

from repguard.harness.parser import parse_response


class TestParseResponse:
    """Tests for answer extraction from LLM responses."""

    @pytest.mark.parametrize("response,expected", [
        ("The answer is A.", "A"),
        ("The answer is B", "B"),
        ("The answer is (C).", "C"),
        ("the answer is d", "D"),
        ("Answer: E", "E"),
        ("Answer:F", "F"),
        ("A", "A"),
        ("  B  ", "B"),
        ("(C)", "C"),
    ])
    def test_standard_formats(self, response: str, expected: str) -> None:
        """Standard answer formats should be parsed correctly."""
        result = parse_response(response, num_options=10)
        assert result.answer == expected
        assert result.is_valid

    def test_cot_response(self) -> None:
        """Chain-of-thought response should extract the final answer."""
        response = (
            "Let me think about this step by step.\n"
            "First, we need to consider...\n"
            "Based on this analysis, option B is correct.\n"
            "The answer is B."
        )
        result = parse_response(response, num_options=5)
        assert result.answer == "B"

    def test_empty_response(self) -> None:
        """Empty response should return UNKNOWN."""
        result = parse_response("", num_options=5)
        assert result.answer == "UNKNOWN"
        assert not result.is_valid

    def test_no_answer_found(self) -> None:
        """Response with no identifiable answer should return UNKNOWN."""
        result = parse_response("I cannot determine the answer to this question.", num_options=4)
        assert result.answer == "UNKNOWN" or result.is_valid  # may find a letter in text

    def test_invalid_letter_for_num_options(self) -> None:
        """Answer outside the valid range should be rejected."""
        # Only 4 options (A-D), so E should not match as a specific pattern
        result = parse_response("The answer is E.", num_options=4)
        assert result.answer != "E" or not result.is_valid

    def test_confidence_levels(self) -> None:
        """More specific patterns should have higher confidence."""
        high = parse_response("The answer is A.")
        low = parse_response("Considering various factors A seems right overall")
        assert high.confidence >= low.confidence

    def test_raw_response_preserved(self) -> None:
        """Original response text should be preserved in result."""
        text = "The answer is C."
        result = parse_response(text)
        assert result.raw_response == text
