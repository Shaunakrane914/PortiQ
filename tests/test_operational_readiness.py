import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from portiq.api import create_app
from portiq.config import Settings


def test_readiness_detects_missing_analytical_tables_but_liveness_survives(database: Path):
    with TestClient(create_app(Settings(database=database))) as client:
        assert client.get("/api/ready").status_code == 200
        with sqlite3.connect(database) as conn:
            conn.execute("DROP TABLE transactions")
        assert client.get("/api/health").status_code == 200
        assert client.get("/api/ready").status_code == 503
        assert client.get("/api/live").status_code == 200


def test_readiness_detects_closed_quota_store(database: Path):
    app = create_app(Settings(database=database))
    with TestClient(app) as client:
        app.state.analysis.budget.close()
        assert client.get("/api/ready").status_code == 503
        assert client.get("/api/live").status_code == 200


@pytest.mark.parametrize("variable", ["WEB_CONCURRENCY", "UVICORN_WORKERS"])
def test_production_rejects_unsupported_worker_topology(
    database: Path, tmp_path: Path, monkeypatch, variable: str
):
    monkeypatch.setenv("PORTIQ_ALLOWED_HOSTS", "testserver")
    monkeypatch.setenv(variable, "2")
    with pytest.raises(ValueError, match="one worker"):
        create_app(
            Settings(database=database, environment="production", quota_path=tmp_path / "quota.db"),
            token="x" * 32,
        )
