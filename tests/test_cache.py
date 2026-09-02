"""Tests for the disk cache."""

from __future__ import annotations

from pathlib import Path

from repguard.harness.cache import DiskCache
from repguard.providers.base import LLMResponse


class TestDiskCache:
    """Tests for the content-addressable disk cache."""

    def test_make_key_is_deterministic(self) -> None:
        """Same parameters should produce the same cache key."""
        key1 = DiskCache.make_key("gpt-4o", "abc123", temperature=0.0)
        key2 = DiskCache.make_key("gpt-4o", "abc123", temperature=0.0)
        assert key1 == key2

    def test_different_params_produce_different_keys(self) -> None:
        """Different parameters should produce different cache keys."""
        key1 = DiskCache.make_key("gpt-4o", "abc123", temperature=0.0)
        key2 = DiskCache.make_key("gpt-4o", "abc123", temperature=0.5)
        assert key1 != key2

    def test_cache_miss(self, tmp_path: Path) -> None:
        """Absent key should return None."""
        cache = DiskCache(tmp_path / "cache")
        assert cache.get("nonexistent_key") is None
        assert cache.misses == 1

    def test_put_and_get(self, tmp_path: Path) -> None:
        """Cached response should be retrievable."""
        cache = DiskCache(tmp_path / "cache")
        response = LLMResponse(
            content="The answer is B.",
            model_id="gpt-4o",
            input_tokens=100,
            output_tokens=10,
            total_tokens=110,
            cost_usd=0.001,
        )
        key = DiskCache.make_key("gpt-4o", "test_hash")
        cache.put(key, response)

        cached = cache.get(key)
        assert cached is not None
        assert cached.content == "The answer is B."
        assert cached.model_id == "gpt-4o"
        assert cached.cached is True
        assert cached.cost_usd == 0.0  # Cached responses have zero cost
        assert cache.hits == 1

    def test_disabled_cache(self, tmp_path: Path) -> None:
        """Disabled cache should always miss and never write."""
        cache = DiskCache(tmp_path / "cache", enabled=False)
        response = LLMResponse(content="test", model_id="m")
        cache.put("key", response)
        assert cache.get("key") is None
        assert cache.misses == 1  # Only the get() counts as a miss

    def test_clear(self, tmp_path: Path) -> None:
        """Clear should remove all cached entries."""
        cache = DiskCache(tmp_path / "cache")
        response = LLMResponse(content="test", model_id="m")
        cache.put("k1", response)
        cache.put("k2", response)
        count = cache.clear()
        assert count == 2
        assert cache.get("k1") is None

    def test_hit_rate(self, tmp_path: Path) -> None:
        """Hit rate should be computed correctly."""
        cache = DiskCache(tmp_path / "cache")
        response = LLMResponse(content="test", model_id="m")
        cache.put("k1", response)

        cache.get("k1")  # hit
        cache.get("k2")  # miss
        assert cache.hit_rate == 0.5

    def test_get_stats(self, tmp_path: Path) -> None:
        """Stats should contain expected fields."""
        cache = DiskCache(tmp_path / "cache")
        stats = cache.get_stats()
        assert "enabled" in stats
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats
