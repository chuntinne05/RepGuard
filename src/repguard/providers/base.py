"""Base LLM provider protocol and response models.

Defines the abstract interface that all LLM providers must implement,
plus the LLMResponse dataclass for standardized return values. The
provider factory function creates the appropriate provider based on
configuration.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from repguard.config import ProviderConfig


@dataclass(frozen=True)
class LLMResponse:
    """Standardized response from any LLM provider.

    Attributes:
        content: The generated text content.
        model_id: Model identifier that produced this response.
        input_tokens: Number of input/prompt tokens.
        output_tokens: Number of output/completion tokens.
        total_tokens: Total tokens (input + output).
        cost_usd: Estimated cost of this API call in USD.
        latency_ms: Round-trip latency in milliseconds.
        raw_response: Raw provider-specific response data.
        cached: Whether this was served from disk cache.
    """

    content: str
    model_id: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    raw_response: dict[str, Any] = field(default_factory=dict)
    cached: bool = False


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    All providers must implement the complete() method with a standardized
    interface. Providers read API keys from environment variables and never
    store them in configuration files or logs.
    """

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize the provider with configuration.

        Args:
            config: Provider configuration including model ID and parameters.
        """
        self._config = config
        self._model_id = config.model_id
        self._total_cost = 0.0
        self._total_calls = 0

    @property
    def model_id(self) -> str:
        """The model identifier for this provider."""
        return self._model_id

    @property
    def total_cost(self) -> float:
        """Cumulative cost of all calls through this provider (USD)."""
        return self._total_cost

    @property
    def total_calls(self) -> int:
        """Total number of API calls made through this provider."""
        return self._total_calls

    @abstractmethod
    def complete(
        self,
        prompt: str,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        top_p: float | None = None,
        stop: list[str] | None = None,
    ) -> LLMResponse:
        """Generate a completion for the given prompt.

        Args:
            prompt: The input prompt text.
            temperature: Override default temperature.
            max_tokens: Override default max tokens.
            top_p: Override default top_p.
            stop: Optional stop sequences.

        Returns:
            LLMResponse with the generated content and metadata.

        Raises:
            RuntimeError: If the API call fails after retries.
        """
        ...

    def _track_cost(self, response: LLMResponse) -> None:
        """Update cumulative cost and call tracking.

        Args:
            response: The LLM response to track.
        """
        self._total_cost += response.cost_usd
        self._total_calls += 1

    def get_stats(self) -> dict[str, Any]:
        """Get provider usage statistics.

        Returns:
            Dictionary with call count and cost information.
        """
        return {
            "provider": self._config.name,
            "model_id": self._model_id,
            "total_calls": self._total_calls,
            "total_cost_usd": round(self._total_cost, 6),
        }


def create_provider(config: ProviderConfig) -> LLMProvider:
    """Factory function to create the appropriate LLM provider.

    Args:
        config: Provider configuration.

    Returns:
        An initialized LLMProvider instance.

    Raises:
        ValueError: If the provider name is not recognized.
        RuntimeError: If required API keys are not set.
    """
    if config.name == "mock":
        from repguard.providers.mock import MockProvider
        return MockProvider(config)

    elif config.name == "openai":
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            msg = (
                "OPENAI_API_KEY environment variable is not set. "
                "Set it in your .env file or use provider='mock' for dry-run."
            )
            raise RuntimeError(msg)
        from repguard.providers.openai_ import OpenAIProvider
        return OpenAIProvider(config, api_key=api_key)

    elif config.name == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            msg = (
                "ANTHROPIC_API_KEY environment variable is not set. "
                "Set it in your .env file or use provider='mock' for dry-run."
            )
            raise RuntimeError(msg)
        from repguard.providers.anthropic_ import AnthropicProvider
        return AnthropicProvider(config, api_key=api_key)

    else:
        msg = f"Unknown provider: '{config.name}'. Use 'mock', 'openai', or 'anthropic'."
        raise ValueError(msg)
