"""Small injectable boundary around the maintained Google GenAI SDK."""

import random
import threading
import time
from datetime import UTC, datetime
from typing import Any, Protocol

import httpx
from google import genai
from google.genai import errors, types

from portiq.config import Settings
from portiq.errors import ModelError
from portiq.quota import AdaptiveRateLimiter, RequestBudget, classify


class Backend(Protocol):
    def generate(
        self, contents: list[types.Content], config: types.GenerateContentConfig
    ) -> types.GenerateContentResponse: ...


class GeminiBackend:
    def __init__(
        self,
        settings: Settings,
        budget: RequestBudget | None = None,
        limiter: AdaptiveRateLimiter | None = None,
    ) -> None:
        key = settings.require_key()
        self.settings = settings
        self.model = settings.model
        self.request_interval = settings.request_interval
        self.last_request = 0.0
        self.budget = budget or RequestBudget(settings.daily_requests, settings.quota_path)
        self.limiter = limiter or AdaptiveRateLimiter(
            rpm_limit=settings.rpm_limit,
            window_seconds=settings.rpm_window,
            max_wait_seconds=settings.max_wait_seconds,
            cooldown_threshold=settings.rpm_cooldown_threshold,
            cooldown_seconds=settings.rpm_cooldown_seconds,
        )
        self.owns_budget = budget is None
        self.lock = threading.RLock()
        self.attempts: list[dict[str, Any]] = []
        self.attempt_sequence = 0
        self.suppressed_kind: str | None = None
        self.consecutive_failures = 0
        self.circuit_until = 0.0
        self.client = genai.Client(
            api_key=key,
            http_options=types.HttpOptions(
                timeout=30000, retry_options=types.HttpRetryOptions(attempts=1)
            ),
        )

    def generate(
        self, contents: list[types.Content], config: types.GenerateContentConfig
    ) -> types.GenerateContentResponse:
        with self.lock:
            return self._generate(contents, config)

    def _generate(
        self, contents: list[types.Content], config: types.GenerateContentConfig
    ) -> types.GenerateContentResponse:
        if self.circuit_until:
            remaining = self.circuit_until - time.monotonic()
            if remaining > 0:
                raise ModelError(
                    "Provider temporarily unavailable; retry after cooldown.",
                    kind="circuit_open",
                    retry_after=remaining,
                )
            self.client.close()
            self.client = genai.Client(
                api_key=self.settings.require_key(),
                http_options=types.HttpOptions(
                    timeout=30000, retry_options=types.HttpRetryOptions(attempts=1)
                ),
            )
            self.circuit_until = 0
        if self.suppressed_kind:
            raise ModelError(
                "Model disabled until backend restart after " + self.suppressed_kind + ".",
                kind=self.suppressed_kind,
            )
        now = time.monotonic()
        delay = self.limiter.acquire(
            request_interval=self.request_interval,
            last_request=self.last_request,
            now=now,
        )
        pacing_ms = 0.0
        if delay > 0:
            pacing_start = time.perf_counter()
            time.sleep(delay)
            pacing_ms = (time.perf_counter() - pacing_start) * 1000
        self.last_request = time.monotonic()
        if not self.budget.reserve():
            raise ModelError("Local daily request budget exhausted.", kind="local_budget")
        start = time.perf_counter()
        entry: dict[str, Any] = {
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "model": self.model,
            "service_ms": 0.0,
            "pacing_ms": pacing_ms,
            "input_tokens": None,
            "output_tokens": None,
            "thinking_tokens": None,
            "total_tokens": None,
            "error_kind": None,
        }
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )
            if response.usage_metadata:
                usage = response.usage_metadata
                entry.update(
                    input_tokens=usage.prompt_token_count,
                    output_tokens=usage.candidates_token_count,
                    thinking_tokens=usage.thoughts_token_count,
                    total_tokens=usage.total_token_count,
                )
            self.consecutive_failures = 0
            return response
        except (errors.APIError, httpx.HTTPError, ValueError) as exc:
            # Never interpolate SDK errors: request URLs or provider payloads may contain secrets.
            code = getattr(exc, "code", None)
            kind, retryable, delay = classify(exc)
            if kind in {"connection", "timeout", "provider_transient"}:
                self.consecutive_failures += 1
                if self.consecutive_failures >= self.settings.circuit_failures:
                    self.circuit_until = time.monotonic() + self.settings.circuit_seconds
            entry["error_kind"] = kind
            self.suppressed_kind = (
                kind if kind in {"daily_quota", "authentication", "unsupported_model"} else None
            )
            raise ModelError(
                f"Gemini request failed ({type(exc).__name__}, status={code}). "
                "Check model availability, credentials, network, and quota.",
                retryable=retryable,
                kind=kind,
                retry_after=delay,
            ) from exc
        finally:
            self.attempt_sequence += 1
            entry["sequence"] = self.attempt_sequence
            entry["service_ms"] = (time.perf_counter() - start) * 1000
            self.attempts.append(entry)
            if len(self.attempts) > 1000:
                del self.attempts[:-1000]

    def close(self) -> None:
        self.client.close()
        if self.owns_budget:
            self.budget.close()


class MeteredBackend:
    """Per-question metrics; token totals cover routing, SQL generation and summarization."""

    def __init__(self, backend: Backend) -> None:
        self.backend = backend
        self.calls = 0
        self.tokens = 0
        self.duration_ms = 0.0
        self.versions: set[str] = set()
        self.attempt_start = getattr(backend, "attempt_sequence", 0)
        self.backoff_ms = 0.0

    @property
    def metrics(self) -> list[dict[str, Any]]:
        return [
            a for a in getattr(self.backend, "attempts", []) if a["sequence"] > self.attempt_start
        ]

    def generate(
        self, contents: list[types.Content], config: types.GenerateContentConfig
    ) -> types.GenerateContentResponse:
        start = time.perf_counter()
        try:
            for attempt in range(2):
                self.calls += 1
                try:
                    response = self.backend.generate(contents, config)
                    break
                except ModelError as exc:
                    if not exc.retryable or attempt == 1:
                        raise
                    delay = (
                        exc.retry_after
                        if exc.retry_after is not None
                        else 2**attempt + random.uniform(0, 0.25)
                    )
                    if delay > 60:
                        raise
                    time.sleep(delay)
                    self.backoff_ms += delay * 1000
        finally:
            self.duration_ms += (time.perf_counter() - start) * 1000
        if response.model_version:
            self.versions.add(response.model_version)
        if response.usage_metadata:
            self.tokens += response.usage_metadata.total_token_count or 0
        return response
