from types import SimpleNamespace

import httpx
import pytest
from google.genai import types
from pydantic import SecretStr

from portiq.config import Settings
from portiq.errors import ModelError
from portiq.model import GeminiBackend


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
