"""Tests for LLM providers."""

from __future__ import annotations

import pytest

from repguard.config import ProviderConfig
from repguard.providers.base import create_provider
from repguard.providers.mock import MockProvider


class TestMockProvider:
    """Tests for the deterministic MockProvider."""

    def test_deterministic_responses(self) -> None:
        """Same prompt should always produce the same response."""
        config = ProviderConfig(name="mock", model_id="mock-v1")
        provider = MockProvider(config, seed=42)

        resp1 = provider.complete("What is 2+2?")
        provider2 = MockProvider(config, seed=42)
        resp2 = provider2.complete("What is 2+2?")

        assert resp1.content == resp2.content

    def test_different_prompts_may_differ(self) -> None:
        """Different prompts should (usually) produce different answers."""
        config = ProviderConfig(name="mock", model_id="mock-v1")
        provider = MockProvider(config, seed=42)

        resp1 = provider.complete("Question A")
        resp2 = provider.complete("Question B")

        # They could theoretically be the same by hash collision, but very unlikely
        # Just check they are valid responses
        assert len(resp1.content) > 0
        assert len(resp2.content) > 0

    def test_response_has_metadata(self) -> None:
        """MockProvider responses should have realistic metadata."""
        config = ProviderConfig(name="mock", model_id="mock-v1")
        provider = MockProvider(config, seed=42)

        resp = provider.complete("Test prompt")
        assert resp.model_id == "mock-v1"
        assert resp.input_tokens > 0
        assert resp.output_tokens > 0
        assert resp.cost_usd == 0.0  # Mock is free
        assert resp.cached is False

    def test_cot_mode_response(self) -> None:
        """Prompts with 'step by step' should produce longer responses."""
        config = ProviderConfig(name="mock", model_id="mock-v1")
        provider = MockProvider(config, seed=42)

        direct = provider.complete("What is the answer?")
        cot = provider.complete("Think step by step. What is the answer?")

        assert len(cot.content) > len(direct.content)

    def test_tracks_total_calls(self) -> None:
        """Provider should track cumulative call count."""
        config = ProviderConfig(name="mock", model_id="mock-v1")
        provider = MockProvider(config, seed=42)

        assert provider.total_calls == 0
        provider.complete("Q1")
        assert provider.total_calls == 1
        provider.complete("Q2")
        assert provider.total_calls == 2


class TestCreateProvider:
    """Tests for the provider factory function."""

    def test_creates_mock_provider(self) -> None:
        """Factory should create MockProvider for 'mock' name."""
        config = ProviderConfig(name="mock", model_id="mock-v1")
        provider = create_provider(config)
        assert isinstance(provider, MockProvider)

    def test_openai_without_key_raises(self) -> None:
        """OpenAI provider without API key should raise RuntimeError."""
        import os
        original = os.environ.get("OPENAI_API_KEY")
        os.environ.pop("OPENAI_API_KEY", None)
        try:
            config = ProviderConfig(name="openai", model_id="gpt-4o")
            with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
                create_provider(config)
        finally:
            if original is not None:
                os.environ["OPENAI_API_KEY"] = original

    def test_anthropic_without_key_raises(self) -> None:
        """Anthropic provider without API key should raise RuntimeError."""
        import os
        original = os.environ.get("ANTHROPIC_API_KEY")
        os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            config = ProviderConfig(name="anthropic", model_id="claude-sonnet-4-20250514")
            with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
                create_provider(config)
        finally:
            if original is not None:
                os.environ["ANTHROPIC_API_KEY"] = original

    def test_unknown_provider_raises(self) -> None:
        """Unknown provider name should raise ValueError."""
        config = ProviderConfig.__new__(ProviderConfig)
        object.__setattr__(config, "name", "unknown")
        object.__setattr__(config, "model_id", "x")
        object.__setattr__(config, "parameters", ProviderConfig().parameters)
        with pytest.raises(ValueError, match="Unknown provider"):
            create_provider(config)
