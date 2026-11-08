"""Behavioral checks for the optional assignment enhancements."""

import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from test_agent import call

from portiq.agent import PortfolioAgent
from portiq.api import create_app
from portiq.config import Settings
from portiq.errors import QueryError
from portiq.quota import AdaptiveRateLimiter
from portiq.retrieval import MetadataIndex
from portiq.service import AnalysisService
from portiq.sql import execute


def test_metadata_retrieval_is_query_specific_and_sent_to_model(database: Path) -> None:
    from test_agent import FakeBackend

    index = MetadataIndex(database)
    price = index.retrieve("historical closing prices volume")
    risk = index.retrieve("sharpe risk drawdown volatility")
    assert price[0].source == "sqlite-schema:historical_prices"
    assert risk[0].source == "sqlite-schema:risk_metrics"
    assert "Foreign keys:" in price[0].text
    assert index.retrieve("xyzzy") == []
    backend = FakeBackend([call("respond", status="unsupported", answer="No predictions.")])
    result = PortfolioAgent(Settings(database=database), backend).answer(
        "Predict future sharpe volatility"
    )
    assert "sqlite-schema:risk_metrics" in result.metadata_sources
    assert "RETRIEVED METADATA" in backend.requests[0][1].system_instruction


def test_sql_work_profile_distinguishes_equivalent_work_and_enforces_safety(database: Path) -> None:
    simple = execute(database, "SELECT COUNT(*) FROM portfolios", profile=True)
    wasteful = execute(
        database,
        "SELECT COUNT(DISTINCT p.portfolio_id) FROM portfolios p CROSS JOIN historical_prices",
        profile=True,
    )
    assert simple.rows == wasteful.rows == [[13]]
    assert simple.vm_steps < wasteful.vm_steps
    assert simple.query_plan and wasteful.query_plan
    with pytest.raises(QueryError):
        execute(database, "DELETE FROM portfolios", profile=True)


def test_future_rate_reservations_do_not_overbook_recovery_slots() -> None:
    limiter = AdaptiveRateLimiter(rpm_limit=2, max_wait_seconds=10, clock=lambda: 100)
    limiter.acquire()
    limiter.acquire()
    assert limiter.acquire(now=155) == 5
    assert limiter.acquire(now=155) == 5
    with pytest.raises(Exception, match="capacity full"):
        limiter.acquire(now=155)


def test_api_executes_independent_model_requests_concurrently_with_shared_budget(
    database: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rendezvous = threading.Barrier(2)
    closed = []

    def generate(**kwargs):
        if len(kwargs["contents"]) == 1:
            rendezvous.wait(timeout=5)
            return call("exposure_calculator", portfolio=kwargs["contents"][0].parts[0].text)
        return call("respond", status="answer", answer="See the verified exposure figures.")

    monkeypatch.setattr(
        "portiq.model.genai.Client",
        lambda **kw: SimpleNamespace(
            models=SimpleNamespace(generate_content=generate), close=lambda: closed.append(True)
        ),
    )
    settings = Settings(database=database, api_key=SecretStr("test"), max_concurrent_analyses=2)
    analysis = AnalysisService(settings)
    with TestClient(create_app(settings, analysis, rate_limit=100)) as client:

        def ask(name):
            return client.post(
                "/api/conversation", json={"question": name, "local": False, "cache": False}
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(ask, ["Balanced Portfolio", "Tech Innovation Fund"]))
        assert [r.status_code for r in results] == [200, 200]
        envelopes = [r.json() for r in results]
        assert len({r["session_id"] for r in envelopes}) == 2
        assert [r["response"]["tools"][0]["result"]["portfolio_id"] for r in envelopes] == [4, 3]
        assert [r["response"]["api_calls"] for r in envelopes] == [2, 2]
        assert analysis.budget.used() == 4
        assert analysis.limiter.current_usage() == 4
    assert len(closed) == 2


def test_api_overload_is_bounded_and_recovers(database: Path, monkeypatch) -> None:
    started, release = threading.Event(), threading.Event()
    analysis = AnalysisService(Settings(database=database, max_concurrent_analyses=1))
    original = analysis.ask

    def delayed(*args, **kwargs):
        started.set()
        assert release.wait(timeout=5)
        return original(*args, **kwargs)

    monkeypatch.setattr(analysis, "ask", delayed)
    with TestClient(create_app(analysis.settings, analysis)) as client:
        with ThreadPoolExecutor(max_workers=1) as pool:
            first = pool.submit(client.post, "/api/ask", json={"question": "Count all portfolios"})
            assert started.wait(timeout=5)
            try:
                busy = client.post("/api/ask", json={"question": "Count all portfolios"})
                assert busy.status_code == 503 and busy.headers["retry-after"] == "1"
            finally:
                release.set()
            assert first.result().status_code == 200
        assert client.post("/api/ask", json={"question": "Count all portfolios"}).status_code == 200


def test_production_profile_and_readiness(database: Path, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PORTIQ_ALLOWED_HOSTS", "testserver")
    settings = Settings(database=database, environment="production", quota_path=tmp_path / "q.db")
    with pytest.raises(ValueError, match="token"):
        create_app(settings, token="short")
    with TestClient(create_app(settings, token="x" * 32)) as client:
        assert client.get("/api/live").json() == {"status": "alive"}
        assert client.get("/api/ready").status_code == 200
        assert client.get("/api/portfolios").status_code == 401
        headers = {"Authorization": "Bearer " + "x" * 32}
        assert client.get("/api/portfolios", headers=headers).status_code == 200
        assert (
            client.post(
                "/api/ask",
                headers={**headers, "Origin": "https://testserver"},
                json={"question": "Count all portfolios"},
            ).status_code
            == 403
        )  # Strict scheme/port matching in production.
    monkeypatch.setenv("PORTIQ_ALLOWED_HOSTS", "*")
    with pytest.raises(ValueError, match="hosts"):
        create_app(settings, token="x" * 32)


def test_streamlit_chat_uses_shared_local_tools(database: Path, monkeypatch) -> None:
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    monkeypatch.setenv("PORTIQ_DB", str(database))
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("PORTIQ_QUOTA_DB", str(database.with_suffix(".quota.db")))
    script = Path(__file__).parents[1] / "src/portiq/streamlit_app.py"
    app = AppTest.from_file(str(script)).run()
    assert not app.exception
    assert not app.sidebar.checkbox[0].value
    app.sidebar.checkbox[0].check().run()
    app.chat_input[0].set_value("Count all portfolios").run()
    assert not app.exception
    assert any("13" in text.value for text in app.text)
    app.sidebar.button[0].click().run()
    assert not app.session_state["messages"]


def test_gui_launcher_preserves_global_configuration(
    database: Path, source: Path, monkeypatch
) -> None:
    from portiq.cli import main

    calls = []
    monkeypatch.setattr("portiq.cli.importlib.util.find_spec", lambda name: object())

    def launch(arguments, **kwargs):
        calls.append((arguments, kwargs["env"]))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("portiq.cli.subprocess.run", launch)
    assert (
        main(
            [
                "--db",
                str(database),
                "--source",
                str(source),
                "--model",
                "test-model",
                "gui",
                "--port",
                "8502",
            ]
        )
        == 0
    )
    arguments, env = calls[0]
    assert "--server.port=8502" in arguments
    assert env["PORTIQ_DB"] == str(database.resolve())
    assert env["PORTIQ_SOURCE"] == str(source.resolve())
    assert env["GEMINI_MODEL"] == "test-model"
