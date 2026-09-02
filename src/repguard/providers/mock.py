"""Deterministic mock LLM provider for dry-run testing.

Returns deterministic responses based on a seeded hash of the prompt,
enabling full pipeline validation without API keys or network access.
Simulates realistic token counts and latency for cost estimation testing.
"""

from __future__ import annotations

import hashlib
import time

from repguard.config import ProviderConfig
from repguard.providers.base import LLMProvider, LLMResponse


# Answer letters used for simulated MC responses
_ANSWER_LETTERS = "ABCDEFGHIJ"


class MockProvider(LLMProvider):
    """Deterministic mock provider for dry-run testing.

    Generates responses by hashing the prompt with a seed to select
    a deterministic answer letter. The same prompt always produces the
    same response, enabling reproducible testing of the full pipeline
    without any API calls.

    The mock responses simulate:
    - A selected answer letter (deterministic per prompt)
    - Realistic token count estimates
    - Simulated latency (configurable)
    - Zero cost

    Example:
        >>> from repguard.config import ProviderConfig, ProviderParams
        >>> config = ProviderConfig(name="mock", model_id="mock-v1")
        >>> provider = MockProvider(config)
        >>> response = provider.complete("What is 2+2?")
        >>> response.content  # deterministic, always same for this prompt
        'The answer is A.'
    """

    def __init__(
        self,
        config: ProviderConfig,
        *,
        seed: int = 42,
        simulate_latency_ms: float = 10.0,
    ) -> None:
        """Initialize the mock provider.

        Args:
            config: Provider configuration.
            seed: Seed for deterministic response generation.
            simulate_latency_ms: Simulated latency per call in milliseconds.
        """
        super().__init__(config)
        self._seed = seed
        self._simulate_latency_ms = simulate_latency_ms

    def complete(
        self,
        prompt: str,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        top_p: float | None = None,
        stop: list[str] | None = None,
    ) -> LLMResponse:
        """Generate a deterministic mock response.

        The response is determined by SHA-256(seed || prompt), making it
        fully reproducible. The selected answer letter depends on the
        hash value modulo the number of available answer options.

        Args:
            prompt: The input prompt text.
            temperature: Ignored (deterministic).
            max_tokens: Ignored.
            top_p: Ignored.
            stop: Ignored.

        Returns:
            Deterministic LLMResponse with simulated metadata.
        """
        start = time.monotonic()

        # Deterministic answer selection based on prompt hash
        key = f"{self._seed}:{prompt}"
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        answer_idx = int(digest[:8], 16) % len(_ANSWER_LETTERS)
        answer_letter = _ANSWER_LETTERS[answer_idx]

        # Generate a simple reasoning trace for CoT-style prompts
        has_cot = "step by step" in prompt.lower() or "think" in prompt.lower()
        if has_cot:
            content = (
                f"Let me analyze this question carefully.\n\n"
                f"After considering the options, I believe the correct answer is "
                f"option {answer_letter}. This is because the key concept aligns "
                f"with the fundamental principles involved.\n\n"
                f"The answer is {answer_letter}."
            )
        else:
            content = f"The answer is {answer_letter}."

        # Simulate realistic token counts
        input_tokens = len(prompt.split()) + 10  # rough approximation
        output_tokens = len(content.split()) + 5

        # Simulate latency
        elapsed_ms = (time.monotonic() - start) * 1000 + self._simulate_latency_ms

        response = LLMResponse(
            content=content,
            model_id=self._model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost_usd=0.0,  # Mock calls are free
            latency_ms=round(elapsed_ms, 2),
            raw_response={"mock": True, "seed": self._seed, "digest_prefix": digest[:16]},
            cached=False,
        )

        self._track_cost(response)
        return response

    def __repr__(self) -> str:
        """Return a human-readable representation."""
        return f"MockProvider(model_id='{self._model_id}', seed={self._seed})"
