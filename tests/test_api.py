from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from portiq.api import create_app
from portiq.config import Settings


@pytest.fixture
def client(database: Path, source: Path):
    with TestClient(create_app(Settings(database=database, source=source))) as client:
        yield client


def test_browsing_without_api_key(client: TestClient) -> None:
    assert client.get("/api/health").json()["status"] == "ok"
    portfolios = client.get("/api/portfolios").json()
    assert portfolios["total"] == 13
    for path in [
        "/api/overview",
        "/api/portfolios/2",
        "/api/portfolios/2/holdings",
        "/api/portfolios/2/reconciliation",
        "/api/portfolios/2/performance",
        "/api/portfolios/2/risk",
        "/api/evaluation/summary",
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
    assert client.get("/api/evaluation/summary?path=.env").status_code == 200
    assert "GEMINI_API_KEY" not in client.get("/api/about").text


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
    assert client.post("/api/cache/clear", json={}).json()["status"] == "cleared"
    assert client.get("/api/cache").json()["size"] == 0


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
        assert c.post("/api/ask", headers=headers, content="x" * 17000).status_code in {413, 415}
        c.get("/api/cache", headers=headers)
        assert (
            c.get(
                "/api/cache", headers={**headers, "X-Forwarded-For": "fake-other-client"}
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
    assert answer.status_code == 503 and "Set GEMINI_API_KEY" in answer.text
    assert client.get("/api/../../.env").status_code != 200
