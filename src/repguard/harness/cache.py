"""Content-addressable disk cache for LLM responses.

Caches LLM responses to disk using a content-addressable key derived from
(model_id, prompt_hash, generation_params). This prevents redundant API
calls across runs and enables exact reproduction of previous results.

Cache entries are stored as JSON files in a flat directory structure
keyed by SHA-256 hash.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any

from repguard.providers.base import LLMResponse

logger = logging.getLogger("repguard")


class DiskCache:
    """Content-addressable disk cache for LLM responses.

    Each cache entry is a JSON file named by the SHA-256 hash of
    (model_id, prompt_hash, temperature, max_tokens, top_p). This
    ensures that different generation parameters produce different
    cache keys, while identical requests always hit the same cache entry.

    Example:
        >>> cache = DiskCache("./.llm_cache")
        >>> key = cache.make_key("gpt-4o", "abc123", temperature=0.0)
        >>> cache.get(key)  # None if not cached
        >>> cache.put(key, response)
        >>> cache.get(key)  # Returns cached LLMResponse
    """

    def __init__(self, cache_dir: str | Path, *, enabled: bool = True) -> None:
        """Initialize the disk cache.

        Args:
            cache_dir: Directory to store cache files.
            enabled: Whether caching is active. If False, all operations are no-ops.
        """
        self._cache_dir = Path(cache_dir)
        self._enabled = enabled
        self._hits = 0
        self._misses = 0

        if self._enabled:
            self._cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def enabled(self) -> bool:
        """Whether caching is active."""
        return self._enabled

    @property
    def hits(self) -> int:
        """Number of cache hits."""
        return self._hits

    @property
    def misses(self) -> int:
        """Number of cache misses."""
        return self._misses

    @property
    def hit_rate(self) -> float:
        """Cache hit rate as a fraction [0, 1]."""
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    @staticmethod
    def make_key(
        model_id: str,
        prompt_hash: str,
        *,
        temperature: float = 0.0,
        max_tokens: int = 512,
        top_p: float = 1.0,
    ) -> str:
        """Create a deterministic cache key from call parameters.

        Args:
            model_id: The LLM model identifier.
            prompt_hash: SHA-256 hash of the prompt text.
            temperature: Generation temperature.
            max_tokens: Maximum tokens to generate.
            top_p: Top-p sampling parameter.

        Returns:
            SHA-256 hex string (first 32 chars) as cache key.
        """
        key_str = f"{model_id}|{prompt_hash}|{temperature}|{max_tokens}|{top_p}"
        return hashlib.sha256(key_str.encode("utf-8")).hexdigest()[:32]

    def get(self, key: str) -> LLMResponse | None:
        """Retrieve a cached response by key.

        Args:
            key: Cache key from make_key().

        Returns:
            Cached LLMResponse with cached=True, or None if not found.
        """
        if not self._enabled:
            self._misses += 1
            return None

        cache_file = self._cache_dir / f"{key}.json"

        if not cache_file.exists():
            self._misses += 1
            return None

        try:
            with open(cache_file) as f:
                data = json.load(f)

            self._hits += 1
            return LLMResponse(
                content=data["content"],
                model_id=data["model_id"],
                input_tokens=data.get("input_tokens", 0),
                output_tokens=data.get("output_tokens", 0),
                total_tokens=data.get("total_tokens", 0),
                cost_usd=0.0,  # No cost for cached responses
                latency_ms=0.0,  # No latency for cached responses
                raw_response=data.get("raw_response", {}),
                cached=True,
            )

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Corrupted cache entry {key}: {e}")
            self._misses += 1
            return None

    def put(self, key: str, response: LLMResponse) -> None:
        """Store a response in the cache.

        Args:
            key: Cache key from make_key().
            response: LLMResponse to cache.
        """
        if not self._enabled:
            return

        cache_file = self._cache_dir / f"{key}.json"

        data: dict[str, Any] = {
            "content": response.content,
            "model_id": response.model_id,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "total_tokens": response.total_tokens,
            "cost_usd": response.cost_usd,
            "raw_response": response.raw_response,
        }

        try:
            with open(cache_file, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except OSError as e:
            logger.warning(f"Failed to write cache entry {key}: {e}")

    def clear(self) -> int:
        """Clear all cache entries.

        Returns:
            Number of entries removed.
        """
        if not self._enabled:
            return 0

        count = 0
        for f in self._cache_dir.glob("*.json"):
            f.unlink()
            count += 1

        self._hits = 0
        self._misses = 0
        logger.info(f"Cache cleared: {count} entries removed")
        return count

    def get_stats(self) -> dict[str, Any]:
        """Get cache usage statistics.

        Returns:
            Dictionary with hit/miss counts and hit rate.
        """
        return {
            "enabled": self._enabled,
            "cache_dir": str(self._cache_dir),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self.hit_rate, 4),
        }
