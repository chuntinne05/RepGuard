"""Anthropic LLM provider for RepGuard.

Implements the LLMProvider interface for Anthropic's messages API.
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

# Approximate cost per 1M tokens for common Anthropic models (USD)
_ANTHROPIC_COSTS: dict[str, tuple[float, float]] = {
    # (input_cost_per_1M, output_cost_per_1M)
    "claude-sonnet-4-20250514": (3.00, 15.00),
    "claude-opus-4-20250514": (15.00, 75.00),
    "claude-3-5-sonnet-20241022": (3.00, 15.00),
    "claude-3-5-haiku-20241022": (0.80, 4.00),
    "claude-3-haiku-20240307": (0.25, 1.25),
}


class AnthropicProvider(LLMProvider):
    """Anthropic messages API provider.

    Reads ANTHROPIC_API_KEY from environment variables. Implements retry
    with exponential backoff for rate-limit and transient errors.

    Requires the 'anthropic' extra: pip install repguard[anthropic]
    """

    def __init__(self, config: ProviderConfig, *, api_key: str) -> None:
        """Initialize the Anthropic provider.

        Args:
            config: Provider configuration.
            api_key: Anthropic API key (from environment variable).

        Raises:
            RuntimeError: If the anthropic package is not installed.
        """
        super().__init__(config)
        self._api_key = api_key

        try:
            import anthropic
            self._client = anthropic.Anthropic(api_key=api_key)
        except ImportError as e:
            msg = (
                "The 'anthropic' package is required. "
                "Install with: pip install repguard[anthropic]"
            )
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
        """Generate a completion using Anthropic's messages API.

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

        kwargs: dict[str, Any] = {
            "model": self._model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens if max_tokens is not None else params.max_tokens,
        }

        temp = temperature if temperature is not None else params.temperature
        if temp > 0:
            kwargs["temperature"] = temp

        p = top_p if top_p is not None else params.top_p
        if p < 1.0:
            kwargs["top_p"] = p

        if stop:
            kwargs["stop_sequences"] = stop

        try:
            response = self._client.messages.create(**kwargs)
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise

        elapsed_ms = (time.monotonic() - start) * 1000

        # Extract text from response content blocks
        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text

        input_tokens = response.usage.input_tokens if response.usage else 0
        output_tokens = response.usage.output_tokens if response.usage else 0

        cost = self._estimate_cost(input_tokens, output_tokens)

        result = LLMResponse(
            content=content,
            model_id=self._model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost_usd=cost,
            latency_ms=round(elapsed_ms, 2),
            raw_response={"id": response.id, "model": response.model},
        )

        self._track_cost(result)
        return result

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate the cost of an API call.

        Args:
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.

        Returns:
            Estimated cost in USD.
        """
        costs = _ANTHROPIC_COSTS.get(self._model_id, (3.0, 15.0))
        input_cost = (input_tokens / 1_000_000) * costs[0]
        output_cost = (output_tokens / 1_000_000) * costs[1]
        return round(input_cost + output_cost, 8)
