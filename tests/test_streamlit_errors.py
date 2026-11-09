"""Deployed Streamlit errors stay actionable without exposing provider data."""

from pathlib import Path

import pytest
from pydantic import SecretStr

from portiq.agent import AgentResponse
from portiq.config import Settings
from portiq.errors import ModelError
from portiq.service import AnalysisService

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

from portiq import streamlit_app  # noqa: E402


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        ("authentication", "credentials or API permissions"),
        ("unsupported_model", "model is unavailable"),
        ("rate_limit", "rate limit"),
        ("daily_quota", "Google project quota"),
        ("local_budget", "daily request allowance"),
        ("timeout", "timed out"),
        ("connection", "could not connect"),
        ("provider_transient", "temporarily unavailable"),
        ("circuit_open", "repeated failures"),
        ("busy", "analysis slots"),
        ("secret-provider-message", "Analysis is temporarily unavailable"),
    ],
)
def test_fixed_error_messages(kind: str, expected: str) -> None:
    message = streamlit_app.analysis_error_message(
        Settings(api_key=SecretStr("secret-key-sentinel")), kind
    )
    assert expected in message
    assert "secret-key-sentinel" not in message
    assert "secret-provider-message" not in message


@pytest.mark.parametrize("failure", ["missing_key", "raised_authentication", "returned_rate_limit"])
def test_cloud_error_paths_do_not_render_private_exception_text(
    database: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    from google import genai

    def unexpected_provider_call(**kwargs: object) -> None:
        pytest.fail("These error-path checks must not call Gemini")

    monkeypatch.setattr(genai, "Client", unexpected_provider_call)
    monkeypatch.setenv("PORTIQ_DB", str(database))
    monkeypatch.setenv("PORTIQ_SOURCE", str(Path(__file__).parents[1]))
    monkeypatch.setenv("PORTIQ_QUOTA_DB", str(database.with_suffix(".quota.sqlite")))
    service = AnalysisService(
        Settings(
            database=database,
            api_key=SecretStr("" if failure == "missing_key" else "secret-key-sentinel"),
        )
    )
    if failure == "raised_authentication":

        def raise_auth(*args: object, **kwargs: object) -> None:
            raise ModelError("secret-provider-message", kind="authentication")

        monkeypatch.setattr(service, "ask", raise_auth)
    elif failure == "returned_rate_limit":
        result = AgentResponse(
            request_id="test-request",
            status="error",
            answer="secret-provider-message",
            tools=[],
            model="test-model",
            model_versions=[],
            duration_ms=0,
            model_duration_ms=0,
            api_calls=0,
            tokens=0,
            error_kind="rate_limit",
        )
        monkeypatch.setattr(service, "ask", lambda *args, **kwargs: (result, "test-session"))
    monkeypatch.setattr(streamlit_app, "analysis_service", lambda: service)
    try:
        script = Path(__file__).parents[1] / "deploy/streamlit/app.py"
        app = AppTest.from_file(str(script), default_timeout=20).run()
        assert not app.exception
        app.text_area[0].set_value("Count all portfolios")
        app.button(key="gui_analyze").click().run()
        assert not app.exception
        message = app.session_state["messages"][-1]["text"]
        expected = {
            "missing_key": "AI is not configured",
            "raised_authentication": "credentials or API permissions",
            "returned_rate_limit": "rate limit",
        }
        assert expected[failure] in message
        assert "secret-provider-message" not in message
        assert "secret-key-sentinel" not in message
    finally:
        service.close()
