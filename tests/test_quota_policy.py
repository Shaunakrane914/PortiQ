import http.client
import importlib.util
import io
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from google.genai import errors, types
from pydantic import SecretStr
from test_agent import call

from portiq.agent import PortfolioAgent
from portiq.config import Settings
from portiq.errors import ModelError
from portiq.model import GeminiBackend, MeteredBackend
from portiq.quota import classify
from portiq.service import FallbackBackend


def test_actual_fallback_attempts_and_budget(
    database: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = []

    def generate(**kwargs):
        calls.append(kwargs["model"])
        if kwargs["model"] == "primary":
            raise errors.ClientError(404, {"message": "do-not-expose-this-secret"})
        return call("respond", status="unsupported", answer="Predictions are unavailable.")

    monkeypatch.setattr(
        "portiq.model.genai.Client",
        lambda **kw: SimpleNamespace(
            models=SimpleNamespace(generate_content=generate), close=lambda: None
        ),
    )
    settings = Settings(
        database=database,
        api_key=SecretStr("private-key"),
        model="primary",
        fallback_models=("backup",),
        request_interval=0,
        daily_requests=3,
    )
    backend = FallbackBackend(settings)
    try:
        a = PortfolioAgent(settings, backend).answer("Predict future return")
        b = PortfolioAgent(settings, backend).answer("Predict next year")
        c = PortfolioAgent(settings, backend).answer("Predict next month")
        assert (a.api_calls, b.api_calls, c.api_calls) == (2, 1, 0)
        assert calls == ["primary", "backup", "backup"] and backend.budget.used() == 3
        assert a.provider_metrics[0]["error_kind"] == "unsupported_model"
        assert c.error_kind == "local_budget" and c.status == "error"
        assert "secret" not in a.model_dump_json() and "private-key" not in a.model_dump_json()
    finally:
        backend.close()


def test_rate_retry_delay_and_daily_suppression(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts = [
        errors.ClientError(429, {"details": [{"retryDelay": "2.5s"}]}),
        call("respond", status="unsupported", answer="No prediction."),
    ]

    def generate(**kwargs):
        result = attempts.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(
        "portiq.model.genai.Client",
        lambda **kw: SimpleNamespace(
            models=SimpleNamespace(generate_content=generate), close=lambda: None
        ),
    )
    sleeps = []
    monkeypatch.setattr("portiq.model.time.sleep", sleeps.append)
    backend = GeminiBackend(Settings(api_key=SecretStr("test"), request_interval=0))
    try:
        meter = MeteredBackend(backend)
        meter.generate([], types.GenerateContentConfig())
        assert sleeps == [2.5] and meter.backoff_ms == 2500
        assert len(meter.metrics) == 2 and meter.metrics[0]["error_kind"] == "rate_limit"
        attempts.append(errors.ClientError(429, {"quotaId": "RequestsPerDay"}))
        with pytest.raises(ModelError) as error:
            backend.generate([], types.GenerateContentConfig())
        assert error.value.kind == "daily_quota"
        count = backend.budget.used()
        with pytest.raises(ModelError):
            backend.generate([], types.GenerateContentConfig())
        assert backend.budget.used() == count
    finally:
        backend.close()


@pytest.mark.parametrize(
    "error,expected",
    [
        (httpx.ReadTimeout("secret"), "timeout"),
        (httpx.ConnectError("secret"), "connection"),
        (ValueError("secret"), "invalid_response"),
    ],
)
def test_safe_classification(error: Exception, expected: str) -> None:
    assert classify(error)[0] == expected


def test_http_retry_after() -> None:
    response = httpx.Response(503, headers={"Retry-After": "3"})
    assert classify(errors.ServerError(503, {}, response=response)) == (
        "provider_transient",
        True,
        3.0,
    )


def test_container_probe_handles_startup_disconnect(monkeypatch: pytest.MonkeyPatch) -> None:
    spec = importlib.util.spec_from_file_location(
        "smoke", Path(__file__).parents[1] / "scripts/container_smoke.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    calls = []

    def open_url(*args, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise http.client.RemoteDisconnected("not ready")
        return io.BytesIO(b'{"status":"ok"}')

    monkeypatch.setattr(module.urllib.request, "urlopen", open_url)
    monkeypatch.setattr(module.time, "sleep", lambda _: None)
    module.wait_for_health("http://localhost:8000")
    assert len(calls) == 2
