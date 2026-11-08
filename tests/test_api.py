from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from portiq.api import create_app
from portiq.config import Settings
from portiq.errors import DataError, ModelError, PortiqError, QueryError


@pytest.fixture
def client(database: Path, source: Path):
    with TestClient(create_app(Settings(database=database, source=source))) as client:
        yield client


def test_browsing_without_api_key(client: TestClient) -> None:
    assert client.get("/api/health").json()["status"] == "ok"
    assert client.head("/api/health").status_code == 200
    portfolios = client.get("/api/portfolios").json()
    assert portfolios["total"] == 13
    for path in [
        "/api/overview",
        "/api/portfolios/2",
        "/api/portfolios/2/holdings",
        "/api/portfolios/2/reconciliation",
        "/api/portfolios/2/performance",
        "/api/portfolios/2/risk",
    ]:
        response = client.get(path)
        assert response.status_code == 200, path
        assert response.headers["x-content-type-options"] == "nosniff"
    balanced = next(
        p["portfolio_id"]
        for p in portfolios["records"]
        if p["portfolio_name"] == "Balanced Portfolio"
    )
    assert (
        client.get(f"/api/portfolios/{balanced}/exposure").json()["sectors"]["Technology"]
        == "61.11"
    )
    assert client.get("/api/portfolios/999").status_code == 404
    assert client.get("/api/portfolios?limit=1000").status_code == 400
    assert client.get("/api/evaluation/summary?path=.env").status_code == 404
    assert client.get("/api/about").status_code == 404


def test_api_local_cache_and_context(client: TestClient) -> None:
    first = client.post("/api/conversation", json={"question": "Count all portfolios"}).json()
    assert first["response"]["api_calls"] == 0
    repeat = client.post(
        "/api/conversation",
        json={"question": "Count all portfolios", "session_id": first["session_id"]},
    ).json()
    assert repeat["response"]["cache"] == "hit"
    bad = client.post("/api/ask", json={"question": "hi", "unknown": True})
    assert bad.status_code == 422 and "input" not in bad.text
    client.app.state.analysis.cache.clear()
    assert len(client.app.state.analysis.cache.items) == 0


def test_auth_origin_body_limit_and_rate(database: Path) -> None:
    with TestClient(
        create_app(Settings(database=database), token="private-token", rate_limit=5)
    ) as c:
        assert c.get("/api/health").status_code == 200
        assert c.get("/api/portfolios").status_code == 401
        headers = {"Authorization": "Bearer private-token"}
        assert c.get("/api/portfolios", headers=headers).status_code == 200
        assert (
            c.post(
                "/api/ask",
                headers={**headers, "Origin": "https://attacker.test"},
                json={"question": "Count all portfolios"},
            ).status_code
            == 403
        )
        # Verify TLS-terminating reverse proxy forwards HTTPS origin to testserver without 403
        assert (
            c.post(
                "/api/ask",
                headers={**headers, "Origin": "https://testserver"},
                json={"question": "Count all portfolios"},
            ).status_code
            != 403
        )
        assert c.post("/api/ask", headers=headers, content="x" * 17000).status_code in {413, 415}
        c.get("/api/overview", headers=headers)
        assert (
            c.get(
                "/api/overview", headers={**headers, "X-Forwarded-For": "fake-other-client"}
            ).status_code
            == 429
        )
    with TestClient(create_app(Settings(database=database))) as c:
        assert (
            c.post(
                "/api/ask", content="x" * 17000, headers={"Content-Type": "application/json"}
            ).status_code
            == 413
        )


def test_frontend_assets_csp_and_missing_credentials(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200 and "Portfolio Explorer" in response.text
    assert "script-src 'self'" in response.headers["content-security-policy"]
    js = client.get("/app.js").text
    assert "textContent" in js and "innerHTML" not in js
    answer = client.post(
        "/api/ask", json={"question": "What is the latest AAPL quote?", "local": False}
    )
    assert answer.status_code == 503 and "temporarily unavailable" in answer.text
    assert "GEMINI_API_KEY" not in answer.text
    assert client.get("/api/../../.env").status_code != 200


def test_usage_status_and_response_bounds(database: Path) -> None:
    with TestClient(create_app(Settings(database=database, max_rows=2))) as client:
        response = client.get("/api/portfolios/4/holdings?limit=2")
        assert len(response.json()["records"]) == 2 and response.json()["total"] > 2
        assert client.get("/api/portfolios/4").status_code == 400


def test_unexpected_errors_are_redacted_with_request_id(
    database: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = create_app(Settings(database=database))

    def fail():
        raise RuntimeError("private-provider-payload")

    monkeypatch.setattr(app.state.analysis.portfolios, "overview", fail)
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/overview")
        assert response.status_code == 500 and response.headers["x-request-id"]
        assert "private-provider" not in response.text


def test_removed_planner_is_rejected_without_execution(client: TestClient) -> None:
    response = client.post(
        "/api/ask", json={"question": "Count all portfolios", "strategy": "one-call"}
    )
    assert response.status_code == 422
    assert len(client.app.state.analysis.cache.items) == 0
    service = client.app.state.analysis
    assert service.backend is None
    with pytest.raises(PortiqError, match="Only the existing orchestration"):
        service.ask("Count all portfolios", strategy="one-call")
    assert service.backend is None


def test_container_entrypoint_rejects_unprotected_model_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from portiq.api import main

    settings = Settings(database=tmp_path / "fresh.db", api_key=SecretStr("test-only"))
    monkeypatch.setattr(Settings, "from_env", lambda: settings)
    monkeypatch.setenv("PORTIQ_HOST", "0.0.0.0")
    monkeypatch.delenv("PORTIQ_DEMO_TOKEN", raising=False)
    with pytest.raises(PortiqError, match="PORTIQ_DEMO_TOKEN"):
        main()
    assert not settings.database.exists()


def test_internal_reports_and_configuration_are_not_public(client: TestClient) -> None:
    for path in [
        "/api/about",
        "/api/cache",
        "/api/evaluation/summary",
        "/openapi.json",
        "/reports/cli-2026-11-08/summary.json",
        "/.env",
        "/docs/assignment/README.md",
    ]:
        assert client.get(path).status_code == 404, path
    assert client.get("/api/health").json() == {"status": "ok"}
    for path in ["/", "/app.js", "/styles.css"]:
        text = client.get(path).text
        for private in [
            "Shaunak",
            "PL Capital",
            "GEMINI_API_KEY",
            "Evaluation Lab",
            "System Status",
        ]:
            assert private not in text


@pytest.mark.parametrize(
    "error",
    [
        DataError("C:/Users/private-owner/database.db"),
        ModelError("secret-provider-key"),
        QueryError("private-query-details"),
    ],
)
def test_expected_errors_hide_internal_details(client: TestClient, monkeypatch, error) -> None:
    def fail():
        raise error

    monkeypatch.setattr(client.app.state.analysis.portfolios, "overview", fail)
    response = client.get("/api/overview")
    assert response.status_code in {400, 503}
    assert str(error) not in response.text
