"""Google Gemini provider via REST API (no SDK required).

Mirrors the curl command exactly:

    curl "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
      -H 'Content-Type: application/json'
      -H 'X-goog-api-key: {api_key}'
      -X POST
      -d '{"contents": [{"parts": [{"text": "..."}]}]}'

To swap providers later, implement a new LLMProvider subclass with the same
interface. The CapabilityAudit module is provider-agnostic.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from repguard.config import ProviderConfig
from repguard.providers.base import LLMProvider, LLMResponse

logger = logging.getLogger("repguard")

# Gemini REST API base URL
_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

# Approximate pricing per 1 million tokens (USD) as of 2026.
# Keys matched by substring in model_id (longest match wins).
_GEMINI_PRICING: dict[str, tuple[float, float]] = {
    "gemini-2.0-flash":   (0.10,  0.40),
    "gemini-flash-latest": (0.10,  0.40),
    "gemini-flash":       (0.075, 0.30),
    "gemini-1.5-flash":   (0.075, 0.30),
    "gemini-1.5-pro":     (1.25,  5.00),
    "gemini-pro":         (1.25,  5.00),
}


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider using the REST API.

    Authenticates with ``X-goog-api-key`` header (no OAuth). Supports any
    Gemini model available via ``v1beta/models/{model_id}:generateContent``.

    Example:
        >>> import os
        >>> config = ProviderConfig(name="gemini", model_id="gemini-flash-latest")
        >>> provider = GeminiProvider(config, api_key=os.environ["GEMINI_API_KEY"])
        >>> response = provider.complete("Explain AI in three words.")
    """

    def __init__(
        self,
        config: ProviderConfig,
        *,
        api_key: str,
        timeout_seconds: float = 60.0,
    ) -> None:
        """Initialise the Gemini provider.

        Args:
            config: Provider configuration (model_id, parameters).
            api_key: Gemini API key (``GEMINI_API_KEY`` env var recommended).
            timeout_seconds: HTTP request timeout in seconds.
        """
        super().__init__(config)
        self._api_key = api_key
        self._timeout = timeout_seconds

        # Reuse a single HTTP client across calls (connection pooling).
        self._client = httpx.Client(
            headers={
                "Content-Type": "application/json",
                "X-goog-api-key": api_key,
            },
            timeout=timeout_seconds,
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def complete(
        self,
        prompt: str,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        top_p: float | None = None,
        stop: list[str] | None = None,
    ) -> LLMResponse:
        """Generate a completion via Gemini generateContent REST endpoint.

        Args:
            prompt: The full prompt text to send.
            temperature: Override config temperature. Defaults to config value.
            max_tokens: Override config max output tokens.
            top_p: Override config top_p sampling parameter.
            stop: Optional list of stop sequences.

        Returns:
            LLMResponse with generated text and usage metadata.

        Raises:
            RuntimeError: On non-2xx HTTP responses or unrecoverable errors.
        """
        url = f"{_GEMINI_BASE_URL}/{self._model_id}:generateContent"
        payload = self._build_payload(prompt, temperature, max_tokens, top_p, stop)

        max_retries = getattr(self, "_max_retries", 3)
        base_backoff = 10.0
        retryable_codes = {429, 500, 502, 503, 504}

        for attempt in range(max_retries + 1):
            start = time.monotonic()
            try:
                http_response = self._client.post(url, json=payload)
                if http_response.status_code in retryable_codes and attempt < max_retries:
                    if http_response.status_code == 429:
                        wait_seconds = _parse_retry_delay(
                            http_response, fallback_seconds=base_backoff * (attempt + 1)
                        )
                        logger.warning(
                            f"[Gemini 429 Rate Limit] Quota exceeded. Sleeping "
                            f"{wait_seconds:.1f}s before retry ({attempt + 1}/{max_retries})..."
                        )
                    else:
                        wait_seconds = 5.0 * (attempt + 1)
                        logger.warning(
                            f"[Gemini {http_response.status_code} Server Busy] High demand. Sleeping "
                            f"{wait_seconds:.1f}s before retry ({attempt + 1}/{max_retries})..."
                        )
                    time.sleep(wait_seconds)
                    continue

                http_response.raise_for_status()
                break
            except httpx.HTTPStatusError as exc:
                code = exc.response.status_code
                if code in retryable_codes and attempt < max_retries:
                    if code == 429:
                        wait_seconds = _parse_retry_delay(
                            exc.response, fallback_seconds=base_backoff * (attempt + 1)
                        )
                        logger.warning(
                            f"[Gemini 429 Rate Limit] Quota exceeded. Sleeping "
                            f"{wait_seconds:.1f}s before retry ({attempt + 1}/{max_retries})..."
                        )
                    else:
                        wait_seconds = 5.0 * (attempt + 1)
                        logger.warning(
                            f"[Gemini {code} Server Busy] High demand. Sleeping "
                            f"{wait_seconds:.1f}s before retry ({attempt + 1}/{max_retries})..."
                        )
                    time.sleep(wait_seconds)
                    continue
                raise RuntimeError(
                    f"Gemini API returned {exc.response.status_code}: {exc.response.text}"
                ) from exc
            except httpx.RequestError as exc:
                if attempt < max_retries:
                    wait_seconds = 3.0 * (attempt + 1)
                    logger.warning(
                        f"Gemini connection failed: {exc}. Retrying in {wait_seconds:.1f}s..."
                    )
                    time.sleep(wait_seconds)
                    continue
                raise RuntimeError(f"Gemini API request failed: {exc}") from exc

        elapsed_ms = (time.monotonic() - start) * 1000.0
        raw: dict[str, Any] = http_response.json()

        content = _extract_text(raw)
        usage = raw.get("usageMetadata", {})
        input_tokens = int(usage.get("promptTokenCount", 0))
        output_tokens = int(usage.get("candidatesTokenCount", 0))
        cost = _estimate_cost(self._model_id, input_tokens, output_tokens)

        llm_response = LLMResponse(
            content=content,
            model_id=self._model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost_usd=cost,
            latency_ms=round(elapsed_ms, 2),
            raw_response={"candidates_count": len(raw.get("candidates", []))},
            cached=False,
        )

        self._track_cost(llm_response)
        return llm_response

    def __repr__(self) -> str:
        return f"GeminiProvider(model_id='{self._model_id}')"

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_payload(
        self,
        prompt: str,
        temperature: float | None,
        max_tokens: int | None,
        top_p: float | None,
        stop: list[str] | None,
    ) -> dict[str, Any]:
        """Build the Gemini REST API request payload.

        Args:
            prompt: The input text.
            temperature: Generation temperature (or None for config default).
            max_tokens: Max output tokens (or None for config default).
            top_p: Top-p parameter (or None for config default).
            stop: Optional stop sequences.

        Returns:
            JSON-serialisable payload dictionary.
        """
        generation_config: dict[str, Any] = {
            "temperature": temperature if temperature is not None
                           else self._config.parameters.temperature,
            "maxOutputTokens": max_tokens if max_tokens is not None
                               else self._config.parameters.max_tokens,
            "topP": top_p if top_p is not None
                    else self._config.parameters.top_p,
        }
        if stop:
            generation_config["stopSequences"] = stop

        return {
            "contents": [
                {"parts": [{"text": prompt}]}
            ],
            "generationConfig": generation_config,
        }


# ------------------------------------------------------------------
# Module-level utilities
# ------------------------------------------------------------------

def _extract_text(raw: dict[str, Any]) -> str:
    """Extract the first text part from a Gemini generateContent response.

    Gemini response structure:
        {
          "candidates": [
            {"content": {"parts": [{"text": "..."}]}}
          ]
        }

    Args:
        raw: Parsed JSON response dictionary.

    Returns:
        Extracted text, or empty string if no text is found.
    """
    try:
        candidates = raw.get("candidates", [])
        if not candidates or not isinstance(candidates[0], dict):
            logger.warning("Gemini response contains no valid candidates.")
            return ""
        content = candidates[0].get("content")
        if not isinstance(content, dict):
            logger.warning("Gemini candidate has no valid content object.")
            return ""
        parts = content.get("parts", [])
        if not parts or not isinstance(parts[0], dict):
            logger.warning("Gemini candidate has no valid parts.")
            return ""
        text = parts[0].get("text", "")
        if not text:
            # Some safety-filtered responses have empty text
            finish_reason = candidates[0].get("finishReason", "UNKNOWN")
            logger.warning(f"Gemini returned empty text. finishReason={finish_reason}")
        return text
    except (KeyError, IndexError, TypeError, AttributeError) as exc:
        logger.error(f"Failed to parse Gemini response: {exc}. Raw: {str(raw)[:200]}")
        return ""


def _estimate_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate USD cost for a Gemini API call.

    Matches ``model_id`` against the pricing table by substring search,
    preferring longer (more specific) matches.

    Args:
        model_id: Gemini model identifier string.
        input_tokens: Number of prompt tokens.
        output_tokens: Number of completion tokens.

    Returns:
        Estimated cost in USD.
    """
    # Select pricing by longest matching key (most specific match first)
    matched_key = max(
        (key for key in _GEMINI_PRICING if key in model_id.lower()),
        key=len,
        default=None,
    )
    if matched_key is None:
        # Unknown model — use a conservative default
        input_price_per_m, output_price_per_m = 1.0, 3.0
    else:
        input_price_per_m, output_price_per_m = _GEMINI_PRICING[matched_key]

    return (
        input_tokens * input_price_per_m + output_tokens * output_price_per_m
    ) / 1_000_000


def _parse_retry_delay(response: Any, fallback_seconds: float = 15.0) -> float:
    """Extract retry delay in seconds from a Gemini 429 error response or header.

    Checks:
    1. HTTP 'Retry-After' header.
    2. Google RPC 'RetryInfo.retryDelay' (e.g. '36s' or '36.327826445s').
    3. Fallback duration if neither is present.

    Args:
        response: httpx.Response object.
        fallback_seconds: Default seconds to wait if no delay found.

    Returns:
        Number of seconds to sleep before retrying (includes a 1s buffer).
    """
    # 1. Header
    retry_after = getattr(response, "headers", {}).get("Retry-After")
    if retry_after:
        try:
            return float(retry_after) + 1.0
        except ValueError:
            pass

    # 2. JSON details: error.details -> RetryInfo.retryDelay
    try:
        data = response.json()
        details = data.get("error", {}).get("details", [])
        for item in details:
            if isinstance(item, dict) and "RetryInfo" in item.get("@type", ""):
                delay_str = str(item.get("retryDelay", ""))
                if delay_str:
                    return float(delay_str.rstrip("s")) + 1.0
    except Exception:
        pass

    return fallback_seconds
