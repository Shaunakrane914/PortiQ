import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from google.genai import types
from test_agent import FakeBackend, call

from portiq.agent import PortfolioAgent
from portiq.api import create_app
from portiq.config import Settings
from portiq.service import AnalysisService


def count_tool() -> types.GenerateContentResponse:
    return call(
        "sql_query",
        question="Count portfolios",
        sql="SELECT COUNT(*) FROM portfolios",
        explanation="Count the supplied records",
        complete=True,
    )


def test_synthesis_mode_blocks_both_direct_and_explicit_scalar_shortcuts(database: Path) -> None:
    backend = FakeBackend(
        [count_tool(), call("respond", status="answer", answer="There are 13 portfolios.")]
    )
    answer = PortfolioAgent(
        Settings(database=database, direct_results=True, force_synthesis=True), backend
    ).answer("Count all portfolios. Return just the count.")
    assert answer.api_calls == 2 and answer.answer == "There are 13 portfolios."
    assert answer.rendering == "model synthesis with authoritative tool evidence"
    system = backend.requests[0][1].system_instruction
    assert "Review the actual tool results" in system and "set complete=true" not in system


@pytest.mark.parametrize("endpoint", ["/api/ask", "/api/conversation"])
def test_smarter_api_bypasses_local_and_cache_without_replacing_fast_cached_answer(
    database: Path, endpoint: str
) -> None:
    backend = FakeBackend(
        [count_tool(), call("respond", status="answer", answer="There are 13 portfolios.")]
    )
    settings = Settings(database=database)
    service = AnalysisService(settings, backend)
    with TestClient(create_app(settings, service)) as client:
        fast = client.post(endpoint, json={"question": "Count all portfolios"}).json()
        assert fast["response"]["api_calls"] == 0
        payload = {"question": "Count all portfolios", "session_id": fast["session_id"]}
        smart = client.post(
            endpoint, json=payload | {"smarter": True, "local": True, "cache": True}
        ).json()["response"]
        assert smart["status"] == "answer" and smart["api_calls"] == 2
        assert smart["cache"] == "disabled" and smart["answer"] == "There are 13 portfolios."
        again = client.post(endpoint, json=payload).json()["response"]
        assert again["api_calls"] == 0 and again["cache"] == "hit"
        assert not settings.force_synthesis and settings.direct_results
        assert len(backend.requests) == 2


def test_api_requires_boolean_smarter_flag(database: Path) -> None:
    with TestClient(create_app(Settings(database=database))) as client:
        response = client.post("/api/ask", json={"question": "Count portfolios", "smarter": "yes"})
        assert response.status_code == 422


def test_simultaneous_modes_have_independent_prompts_and_do_not_mutate_service(
    database: Path,
) -> None:
    barrier = threading.Barrier(2)

    class Backend:
        def generate(self, contents, config):
            if len(contents) == 1:
                barrier.wait(timeout=5)
                return count_tool()
            assert "Review the actual tool results" in config.system_instruction
            return call("respond", status="answer", answer="There are 13 portfolios.")

    settings = Settings(database=database)
    service = AnalysisService(settings, Backend())
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            fast = pool.submit(service.ask, "Count portfolios", local=False, cached=False)
            smart = pool.submit(service.ask, "Count portfolios", smarter=True)
            fast_answer, fast_id = fast.result()
            smart_answer, smart_id = smart.result()
        assert fast_answer.api_calls == 1 and smart_answer.api_calls == 2
        assert fast_id != smart_id
        assert settings.direct_results and not settings.force_synthesis
    finally:
        service.close()
