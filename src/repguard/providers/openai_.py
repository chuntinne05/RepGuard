"""OpenAI-compatible LLM provider for RepGuard.

Implements the LLMProvider interface for OpenAI's chat completions API.
API keys are read from environment variables and never logged or stored.
Includes retry logic via tenacity for transient failures.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from repguard.config import ProviderConfig
from repguard.providers.base import LLMProvider, LLMResponse

logger = logging.getLogger("repguard")

# Approximate cost per 1M tokens for common OpenAI models (USD)
# Updated as of August 2026. These are estimates for cost tracking.
_OPENAI_COSTS: dict[str, tuple[float, float]] = {
    # (input_cost_per_1M, output_cost_per_1M)
    "gpt-4o-2024-08-06": (2.50, 10.00),
    "gpt-4o-mini-2024-07-18": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4-turbo": (10.00, 30.00),
    "gpt-3.5-turbo": (0.50, 1.50),
}


class OpenAIProvider(LLMProvider):
    """OpenAI chat completions provider.

    Reads OPENAI_API_KEY from environment variables. Implements retry
    with exponential backoff for rate-limit and transient errors.

    Requires the 'openai' extra: pip install repguard[openai]
    """

    def __init__(self, config: ProviderConfig, *, api_key: str) -> None:
        """Initialize the OpenAI provider.

        Args:
            config: Provider configuration.
            api_key: OpenAI API key (from environment variable).

        Raises:
            RuntimeError: If the openai package is not installed.
        """
        super().__init__(config)
        self._api_key = api_key

        try:
            import openai
            self._client = openai.OpenAI(api_key=api_key)
        except ImportError as e:
            msg = "The 'openai' package is required. Install with: pip install repguard[openai]"
            raise RuntimeError(msg) from e

    @retry(
        retry=retry_if_exception_type((Exception,)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        reraise=True,
    )
    def complete(
        self,
        prompt: str,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        top_p: float | None = None,
        stop: list[str] | None = None,
    ) -> LLMResponse:
        """Generate a completion using OpenAI's chat completions API.

        Args:
            prompt: The input prompt text.
            temperature: Override default temperature.
            max_tokens: Override default max tokens.
            top_p: Override default top_p.
            stop: Optional stop sequences.

        Returns:
            LLMResponse with generated content and usage metadata.

        Raises:
            RuntimeError: If the API call fails after retries.
        """
        params = self._config.parameters

        start = time.monotonic()

        try:
            response = self._client.chat.completions.create(
                model=self._model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature if temperature is not None else params.temperature,
                max_tokens=max_tokens if max_tokens is not None else params.max_tokens,
                top_p=top_p if top_p is not None else params.top_p,
                stop=stop,
            )
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

        elapsed_ms = (time.monotonic() - start) * 1000

        content = response.choices[0].message.content or ""
        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        total_tokens = usage.total_tokens if usage else 0

        cost = self._estimate_cost(input_tokens, output_tokens)

        result = LLMResponse(
            content=content,
            model_id=self._model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_usd=cost,
            latency_ms=round(elapsed_ms, 2),
            raw_response={"id": response.id, "model": response.model},
        )

        self._track_cost(result)
        return result

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate the cost of an API call based on token counts.

        Args:
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.

        Returns:
            Estimated cost in USD.
        """
        costs = _OPENAI_COSTS.get(self._model_id, (5.0, 15.0))
        input_cost = (input_tokens / 1_000_000) * costs[0]
        output_cost = (output_tokens / 1_000_000) * costs[1]
        return round(input_cost + output_cost, 8)

    def _build_raw_response(self, response: Any) -> dict[str, Any]:
        """Extract raw response metadata for logging."""
        return {
            "id": getattr(response, "id", "unknown"),
            "model": getattr(response, "model", self._model_id),
        }
