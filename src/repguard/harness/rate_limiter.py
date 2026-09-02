"""Token-bucket rate limiter with configurable RPM/TPM limits.

Provides rate limiting for LLM API calls to stay within provider
quotas. Implements a simple token-bucket algorithm with sleep-based
throttling rather than rejecting requests.
"""

from __future__ import annotations

import logging
import time
from collections import deque

logger = logging.getLogger("repguard")


class RateLimiter:
    """Token-bucket rate limiter for LLM API calls.

    Tracks both requests-per-minute (RPM) and tokens-per-minute (TPM)
    and sleeps when either limit would be exceeded.

    Example:
        >>> limiter = RateLimiter(requests_per_minute=60, tokens_per_minute=100000)
        >>> limiter.wait_if_needed(estimated_tokens=500)
        >>> # Make API call...
        >>> limiter.record_request(actual_tokens=450)
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        tokens_per_minute: int = 100_000,
    ) -> None:
        """Initialize the rate limiter.

        Args:
            requests_per_minute: Maximum requests per 60-second window.
            tokens_per_minute: Maximum tokens per 60-second window.
        """
        self._rpm = requests_per_minute
        self._tpm = tokens_per_minute

        # Sliding window of (timestamp, token_count) for recent requests
        self._request_times: deque[float] = deque()
        self._token_counts: deque[tuple[float, int]] = deque()

        self._total_requests = 0
        self._total_tokens = 0
        self._total_wait_seconds = 0.0

    def wait_if_needed(self, estimated_tokens: int = 0) -> float:
        """Block until the request can proceed within rate limits.

        Args:
            estimated_tokens: Estimated tokens for the upcoming request.

        Returns:
            Number of seconds waited (0.0 if no wait was needed).
        """
        waited = 0.0

        while True:
            now = time.monotonic()
            self._prune_old_entries(now)

            rpm_ok = len(self._request_times) < self._rpm
            current_tokens = sum(tc for _, tc in self._token_counts)
            tpm_ok = (current_tokens + estimated_tokens) <= self._tpm

            if rpm_ok and tpm_ok:
                break

            # Sleep until the oldest entry expires from the window
            sleep_time = self._compute_sleep_time(now)
            if sleep_time > 0:
                logger.debug(f"Rate limit: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
                waited += sleep_time

        self._total_wait_seconds += waited
        return waited

    def record_request(self, actual_tokens: int = 0) -> None:
        """Record a completed request for rate tracking.

        Args:
            actual_tokens: Actual tokens consumed by the request.
        """
        now = time.monotonic()
        self._request_times.append(now)
        self._token_counts.append((now, actual_tokens))
        self._total_requests += 1
        self._total_tokens += actual_tokens

    def _prune_old_entries(self, now: float) -> None:
        """Remove entries older than 60 seconds from the sliding window.

        Args:
            now: Current monotonic time.
        """
        cutoff = now - 60.0

        while self._request_times and self._request_times[0] < cutoff:
            self._request_times.popleft()

        while self._token_counts and self._token_counts[0][0] < cutoff:
            self._token_counts.popleft()

    def _compute_sleep_time(self, now: float) -> float:
        """Compute how long to sleep until the oldest entry expires.

        Args:
            now: Current monotonic time.

        Returns:
            Sleep duration in seconds.
        """
        oldest_request = self._request_times[0] if self._request_times else now
        oldest_token = self._token_counts[0][0] if self._token_counts else now
        oldest = min(oldest_request, oldest_token)
        # Sleep until the oldest entry is 60s old, plus a small buffer
        return max(0.0, (oldest + 60.0) - now + 0.1)

    def get_stats(self) -> dict[str, float | int]:
        """Get rate limiter usage statistics.

        Returns:
            Dictionary with usage counts and wait time.
        """
        return {
            "total_requests": self._total_requests,
            "total_tokens": self._total_tokens,
            "total_wait_seconds": round(self._total_wait_seconds, 2),
            "rpm_limit": self._rpm,
            "tpm_limit": self._tpm,
        }
