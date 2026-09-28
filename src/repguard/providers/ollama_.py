"""Ollama LLM provider supporting both local instances and Modal-hosted endpoints.

Supports:
- Local Ollama: http://127.0.0.1:11434
- Modal-hosted Ollama: https://<user>--ollama-server-...modal.direct
  (Automatically handles Modal authentication via 'Modal-Authorization: Bearer <token>')

Configured for multiple-choice benchmarking:
- Uses /api/chat with think=False and stream=False.
- Uses num_predict=16 and temperature=0 for fast 1-token output.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

import httpx

from repguard.config import ProviderConfig
from repguard.providers.base import LLMProvider, LLMResponse

logger = logging.getLogger("repguard")

_DEFAULT_OLLAMA_HOST = "http://127.0.0.1:11434"


def _get_modal_auth_token(base_url: str) -> str | None:
    """Retrieve Modal flash authorization token for the endpoint if available.

    Checks:
    1. MODAL_AUTH_TOKEN environment variable.
    2. Cached token in ~/.cache/modal/curl-flash-auth-tokens.json (written by modal CLI).
    3. Programmatic token fetch via modal SDK if available.
    """
    # 1. Environment variable override
    env_token = os.environ.get("MODAL_AUTH_TOKEN")
    if env_token:
        return env_token

    # 2. Check cached token file from modal CLI
    cache_path = Path.home() / ".cache" / "modal" / "curl-flash-auth-tokens.json"
    if cache_path.exists():
        try:
            cache_data = json.loads(cache_path.read_text())
            now = time.time()
            # Clean hostname for matching
            from urllib.parse import urlparse

            hostname = urlparse(base_url).hostname or base_url

            for key, val in cache_data.items():
                if (key in hostname or hostname in key) and isinstance(val, dict):
                    if val.get("expires_at", 0) > now:
                        return val.get("token")
        except Exception as exc:
            logger.debug(f"Failed to read modal token cache: {exc}")

    # 3. Try modal client if installed
    try:
        from modal.client import _Client
        from modal_proto import api_pb2

        import asyncio

        async def _fetch() -> str:
            client = await _Client.from_env()
            resp = await client.stub.CurlGetAuthToken(api_pb2.CurlAuthTokenRequest(url=base_url))
            return resp.token

        return asyncio.run(_fetch())
    except Exception as exc:
        logger.debug(f"Failed to fetch modal auth token via SDK: {exc}")

    return None


class OllamaProvider(LLMProvider):
    """Ollama provider via /api/chat.

    Works with both local Ollama and Modal-hosted Ollama servers.

    Example:
        >>> config = ProviderConfig(name="ollama", model_id="qwen3:14b")
        >>> provider = OllamaProvider(config, base_url="https://...modal.direct")
        >>> response = provider.complete("What is 17 * 23?")
        >>> print(response.content)
    """

    def __init__(
        self,
        config: ProviderConfig,
        *,
        base_url: str | None = None,
        timeout_seconds: float = 180.0,
        max_retries: int = 3,
    ) -> None:
        """Initialise Ollama provider.

        Args:
            config: Provider configuration.
            base_url: Ollama base URL (reads from OLLAMA_URL or OLLAMA_HOST env if None).
            timeout_seconds: Timeout (default 180s to accommodate GPU cold starts).
            max_retries: Number of retries for transient errors.
        """
        super().__init__(config)

        # Resolve URL priority: explicit arg -> OLLAMA_URL -> OLLAMA_HOST -> default
        raw_url = (
            base_url
            or os.environ.get("OLLAMA_URL")
            or os.environ.get("OLLAMA_HOST")
            or _DEFAULT_OLLAMA_HOST
        )
        self._base_url = raw_url.rstrip("/")
        self._timeout = timeout_seconds
        self._max_retries = max_retries

        # Set up default headers
        headers: dict[str, str] = {
            "Content-Type": "application/json",
        }

        # If pointing to a Modal endpoint, add Modal authorization
        if "modal.direct" in self._base_url or "modal.run" in self._base_url:
            token = _get_modal_auth_token(self._base_url)
            if token:
                headers["Modal-Authorization"] = f"Bearer {token}"
            else:
                logger.warning(
                    f"Connecting to Modal endpoint {self._base_url} without a detected "
                    f"Modal auth token. If you get 401, run 'modal curl {self._base_url}' once "
                    f"or set MODAL_AUTH_TOKEN in .env."
                )

        self._client = httpx.Client(
            headers=headers,
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
        """Generate completion from Ollama /api/chat.

        Args:
            prompt: Formatted question prompt.
            temperature: Sampling temperature override (default 0).
            max_tokens: Max output tokens override (default 16 for single-letter answers).
            top_p: Top-p override.
            stop: Optional stop sequences.

        Returns:
            LLMResponse with generated text and token counts.

        Raises:
            RuntimeError: If server fails, model is missing, or connection drops.
        """
        url = f"{self._base_url}/api/chat"
        payload = self._build_payload(prompt, temperature, max_tokens, top_p, stop)

        retryable_codes = {429, 500, 502, 503, 504}

        for attempt in range(self._max_retries + 1):
            start = time.monotonic()
            try:
                http_response = self._client.post(url, json=payload)

                # Check if server is waking up / transient error
                if http_response.status_code in retryable_codes and attempt < self._max_retries:
                    wait_s = 5.0 * (attempt + 1)
                    logger.warning(
                        f"[Ollama {http_response.status_code}] Temporary server issue. "
                        f"Retrying in {wait_s:.1f}s ({attempt + 1}/{self._max_retries})..."
                    )
                    time.sleep(wait_s)
                    continue

                if http_response.status_code == 404:
                    err = http_response.json().get("error", "")
                    raise RuntimeError(
                        f"Ollama model '{self._model_id}' not found. "
                        f"Please pull it first: ollama pull {self._model_id} (Detail: {err})"
                    )

                if http_response.status_code == 401:
                    raise RuntimeError(
                        f"Modal proxy authentication failed (401) for {self._base_url}. "
                        f"Run 'modal curl {self._base_url}' in terminal to refresh the token, "
                        f"or set MODAL_AUTH_TOKEN in .env."
                    )

                http_response.raise_for_status()
                break

            except httpx.ConnectError as exc:
                if attempt < self._max_retries:
                    wait_s = 5.0 * (attempt + 1)
                    logger.warning(
                        f"Cannot connect to Ollama at {self._base_url}. "
                        f"Retrying in {wait_s:.1f}s ({attempt + 1}/{self._max_retries})..."
                    )
                    time.sleep(wait_s)
                    continue
                raise RuntimeError(
                    f"Cannot connect to Ollama at {self._base_url}. "
                    f"Ensure server is running ('ollama serve') or Modal container is deployed."
                ) from exc

            except httpx.ReadTimeout as exc:
                if attempt < self._max_retries:
                    logger.warning(
                        f"Ollama request timed out (cold start loading model). "
                        f"Retrying ({attempt + 1}/{self._max_retries})..."
                    )
                    time.sleep(5.0)
                    continue
                raise RuntimeError(
                    f"Ollama request timed out after {self._timeout}s. "
                    f"Model may still be loading or GPU instance is unavailable."
                ) from exc

            except httpx.HTTPStatusError as exc:
                if exc.response.status_code in retryable_codes and attempt < self._max_retries:
                    time.sleep(5.0 * (attempt + 1))
                    continue
                raise RuntimeError(
                    f"Ollama returned HTTP {exc.response.status_code}: {exc.response.text}"
                ) from exc

            except httpx.RequestError as exc:
                if attempt < self._max_retries:
                    time.sleep(3.0 * (attempt + 1))
                    continue
                raise RuntimeError(f"Ollama request failed: {exc}") from exc

        elapsed_ms = (time.monotonic() - start) * 1000.0
        data: dict[str, Any] = http_response.json()

        # Extract answer text from /api/chat ("message.content") or fallback to "response"
        message = data.get("message", {})
        if isinstance(message, dict):
            content = message.get("content", "").strip()
        else:
            content = ""
        if not content:
            content = data.get("response", "").strip()

        input_tokens = int(data.get("prompt_eval_count", 0))
        output_tokens = int(data.get("eval_count", 0))

        llm_response = LLMResponse(
            content=content,
            model_id=self._model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost_usd=0.0,
            latency_ms=round(elapsed_ms, 2),
            raw_response={"done": data.get("done", True)},
            cached=False,
        )

        self._track_cost(llm_response)
        return llm_response

    def __repr__(self) -> str:
        return f"OllamaProvider(model_id='{self._model_id}', base_url='{self._base_url}')"

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
        """Construct the exact /api/chat payload for direct answer extraction.

        Uses think=False to skip reasoning chain, saving tokens and Modal credit.
        """
        options: dict[str, Any] = {
            "temperature": (
                temperature
                if temperature is not None
                else self._config.parameters.temperature
            ),
            "num_predict": (
                max_tokens
                if max_tokens is not None
                else (self._config.parameters.max_tokens or 16)
            ),
            "top_p": (
                top_p if top_p is not None else self._config.parameters.top_p
            ),
        }
        if stop:
            options["stop"] = stop

        return {
            "model": self._model_id,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "think": False,
            "stream": False,
            "options": options,
        }
