"""Small injectable boundary around the maintained Google GenAI SDK."""

import time
from typing import Protocol

import httpx
from google import genai
from google.genai import errors, types

from portiq.config import Settings
from portiq.errors import ModelError


class Backend(Protocol):
    def generate(
        self, contents: list[types.Content], config: types.GenerateContentConfig
    ) -> types.GenerateContentResponse: ...


class GeminiBackend:
    def __init__(self, settings: Settings) -> None:
        self.model = settings.model
        self.request_interval = settings.request_interval
        self.last_request = 0.0
        self.client = genai.Client(
            api_key=settings.require_key(),
            http_options=types.HttpOptions(
                timeout=30000, retry_options=types.HttpRetryOptions(attempts=1)
            ),
        )

    def generate(
        self, contents: list[types.Content], config: types.GenerateContentConfig
    ) -> types.GenerateContentResponse:
        try:
            remaining = self.request_interval - (time.monotonic() - self.last_request)
            if remaining > 0:
                time.sleep(remaining)
            self.last_request = time.monotonic()
            return self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )
        except (errors.APIError, httpx.HTTPError, ValueError) as exc:
            # Never interpolate SDK errors: request URLs or provider payloads may contain secrets.
            code = getattr(exc, "code", None)
            raise ModelError(
                f"Gemini request failed ({type(exc).__name__}, status={code}). "
                "Check model availability, credentials, network, and quota."
            ) from exc

    def close(self) -> None:
        self.client.close()


class MeteredBackend:
    """Per-question metrics; token totals cover routing, SQL generation and summarization."""

    def __init__(self, backend: Backend) -> None:
        self.backend = backend
        self.calls = 0
        self.tokens = 0
        self.duration_ms = 0.0
        self.versions: set[str] = set()

    def generate(
        self, contents: list[types.Content], config: types.GenerateContentConfig
    ) -> types.GenerateContentResponse:
        self.calls += 1
        start = time.perf_counter()
        try:
            response = self.backend.generate(contents, config)
        finally:
            self.duration_ms += (time.perf_counter() - start) * 1000
        if response.model_version:
            self.versions.add(response.model_version)
        if response.usage_metadata:
            self.tokens += response.usage_metadata.total_token_count or 0
        return response
