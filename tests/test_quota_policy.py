import http.client
import importlib.util
import io
import time
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
from portiq.quota import AdaptiveRateLimiter, classify
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


def test_auth_suppression_retains_reason_without_trying_backup(
    database: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    actual = []

    def generate(**kwargs):
        actual.append(kwargs["model"])
        raise errors.ClientError(403, {"message": "secret-credential"})

    monkeypatch.setattr(
        "portiq.model.genai.Client",
        lambda **kw: SimpleNamespace(
            models=SimpleNamespace(generate_content=generate), close=lambda: None
        ),
    )
    settings = Settings(
        database=database,
        api_key=SecretStr("test"),
        model="primary",
        fallback_models=("backup",),
        request_interval=0,
    )
    backend = FallbackBackend(settings)
    try:
        for _ in range(2):
            result = PortfolioAgent(settings, backend).answer("Count portfolios")
            assert result.error_kind == "authentication"
        assert actual == ["primary"] and backend.budget.used() == 1
    finally:
        backend.close()


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


def test_circuit_limits_attempts_and_refreshes_after_cooldown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = [100.0]
    calls = []
    clients = []
    closed = []
    monkeypatch.setattr("portiq.model.time.monotonic", lambda: clock[0])

    def generate(**kwargs):
        calls.append(1)
        if len(calls) <= 3:
            raise httpx.ConnectError("secret-in-provider-url")
        return types.GenerateContentResponse()

    def factory(**kwargs):
        clients.append(1)
        return SimpleNamespace(
            models=SimpleNamespace(generate_content=generate), close=lambda: closed.append(1)
        )

    monkeypatch.setattr("portiq.model.genai.Client", factory)
    backend = GeminiBackend(Settings(api_key=SecretStr("test"), request_interval=0))
    try:
        for _ in range(3):
            with pytest.raises(ModelError):
                backend.generate([], types.GenerateContentConfig())
        with pytest.raises(ModelError) as error:
            backend.generate([], types.GenerateContentConfig())
        assert error.value.kind == "circuit_open" and backend.budget.used() == 3
        assert len(calls) == 3
        clock[0] += 31
        backend.generate([], types.GenerateContentConfig())
        assert (
            len(clients) == 2 and backend.budget.used() == 4 and backend.consecutive_failures == 0
        )
    finally:
        backend.close()
    assert len(closed) == 2


def test_adaptive_rate_limiter_immediate_processing() -> None:
    clock = [100.0]
    limiter = AdaptiveRateLimiter(
        rpm_limit=12,
        window_seconds=60.0,
        max_wait_seconds=10.0,
        cooldown_threshold=8,
        cooldown_seconds=1.5,
        clock=lambda: clock[0],
    )
    # First 7 requests process immediately with 0s delay
    for i in range(7):
        assert limiter.prepare_question() == 0.0
        delay = limiter.acquire()
        assert delay == 0.0
        assert limiter.current_usage() == i + 1


def test_adaptive_rate_limiter_question_cooldown_approaching_quota() -> None:
    clock = [100.0]
    limiter = AdaptiveRateLimiter(
        rpm_limit=12,
        window_seconds=60.0,
        max_wait_seconds=10.0,
        cooldown_threshold=8,
        cooldown_seconds=1.5,
        clock=lambda: clock[0],
    )
    # Fill 8 slots (e.g. 4 questions consuming 2 calls each)
    for _ in range(8):
        limiter.acquire()
    assert limiter.current_usage() == 8

    # 5th question approaching quota triggers question-level cooldown
    assert limiter.prepare_question() == 1.5

    # However, internal tool calls within that question execute with 0s delay
    assert limiter.acquire() == 0.0
    assert limiter.acquire() == 0.0


def test_adaptive_rate_limiter_quota_saturated_fail_fast() -> None:
    clock = [100.0]
    limiter = AdaptiveRateLimiter(
        rpm_limit=12,
        window_seconds=60.0,
        max_wait_seconds=10.0,
        cooldown_threshold=8,
        clock=lambda: clock[0],
    )
    # Fill all 12 slots at t=100
    for _ in range(12):
        limiter.acquire()
    assert limiter.current_usage() == 12

    # At t=110, oldest slot is at t=100. Recovery requires 60 - 10 = 50s.
    clock[0] = 110.0
    with pytest.raises(ModelError) as exc_info:
        limiter.prepare_question()
    assert exc_info.value.kind == "rate_limit"
    assert exc_info.value.retryable is True
    assert exc_info.value.retry_after == 50.0

    # acquire() also fails fast without freezing the thread
    with pytest.raises(ModelError) as exc_info2:
        limiter.acquire()
    assert exc_info2.value.kind == "rate_limit"
    assert exc_info2.value.retry_after == 50.0
    # No extra slot was added when rejected
    assert limiter.current_usage() == 12


def test_adaptive_rate_limiter_quota_saturated_short_wait() -> None:
    clock = [100.0]
    limiter = AdaptiveRateLimiter(
        rpm_limit=12,
        window_seconds=60.0,
        max_wait_seconds=10.0,
        cooldown_threshold=8,
        clock=lambda: clock[0],
    )
    for _ in range(12):
        limiter.acquire()

    # At t=155, oldest slot at t=100 will expire in 60 - 55 = 5s
    clock[0] = 155.0
    # 5s <= max_wait_seconds (10s), so it permits waiting
    assert limiter.prepare_question() == 5.0
    assert limiter.acquire() == 5.0


def test_adaptive_rate_limiter_automatic_recovery() -> None:
    clock = [100.0]
    limiter = AdaptiveRateLimiter(
        rpm_limit=12,
        window_seconds=60.0,
        max_wait_seconds=10.0,
        cooldown_threshold=8,
        clock=lambda: clock[0],
    )
    for _ in range(12):
        limiter.acquire()

    # Advance time past 60s window
    clock[0] = 165.0
    # All 12 requests have aged out; usage drops to 0 and delays reset to 0.0s
    assert limiter.prepare_question() == 0.0
    assert limiter.acquire() == 0.0
    assert limiter.current_usage() == 1


def test_adaptive_rate_limiter_thread_safety() -> None:
    import threading

    limiter = AdaptiveRateLimiter(rpm_limit=50, window_seconds=60.0)
    errors_encountered = []

    def worker():
        try:
            for _ in range(5):
                limiter.acquire()
        except Exception as e:
            errors_encountered.append(e)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors_encountered
    assert limiter.current_usage() == 50


def test_agent_integration_with_adaptive_limiter(
    database: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = Settings(
        database=database,
        api_key=SecretStr("test"),
        rpm_limit=12,
        rpm_cooldown_threshold=8,
    )
    backend = GeminiBackend(settings)
    # Saturate the limiter
    for _ in range(12):
        backend.limiter.timestamps.append(time.monotonic())

    agent = PortfolioAgent(settings, backend)
    # The agent should fail fast with status="error" and error_kind="rate_limit"
    response = agent.answer("How many portfolios do we have?")
    assert response.status == "error"
    assert response.error_kind == "rate_limit"
    assert response.error_retry_after is not None
    assert response.api_calls == 0


def test_transport_errors_never_expose_provider_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    def generate(**kwargs: object) -> None:
        raise httpx.ConnectError("secret-key-in-request-url")

    closed = []
    monkeypatch.setattr(
        "portiq.model.genai.Client",
        lambda **kw: SimpleNamespace(
            models=SimpleNamespace(generate_content=generate),
            close=lambda: closed.append(True),
        ),
    )
    backend = GeminiBackend(
        Settings(api_key=SecretStr("secret-key-in-request-url"), request_interval=0)
    )
    try:
        with pytest.raises(ModelError) as error:
            backend.generate([], types.GenerateContentConfig())
        assert "secret-key" not in str(error.value)
        assert "ConnectError" in str(error.value)
    finally:
        backend.close()
    assert closed == [True]


def test_request_pacing(monkeypatch: pytest.MonkeyPatch) -> None:
    clock = iter([100, 100, 102, 113])
    sleeps = []
    monkeypatch.setattr("portiq.model.time.monotonic", lambda: next(clock))
    monkeypatch.setattr("portiq.model.time.sleep", sleeps.append)
    monkeypatch.setattr(
        "portiq.model.genai.Client",
        lambda **kw: SimpleNamespace(
            models=SimpleNamespace(generate_content=lambda **kw: types.GenerateContentResponse()),
            close=lambda: None,
        ),
    )
    backend = GeminiBackend(Settings(api_key=SecretStr("test"), request_interval=13))
    backend.generate([], types.GenerateContentConfig())
    backend.generate([], types.GenerateContentConfig())
    assert sleeps == [11]
