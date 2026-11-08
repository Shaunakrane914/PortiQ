from pathlib import Path

from test_agent import FakeBackend, call

from portiq.config import Settings
from portiq.service import AnalysisService


def test_selected_portfolio_reference_resolves_each_sessions_own_identity(database: Path):
    backend = FakeBackend(
        [call("respond", status="unsupported", answer="Test capture.") for _ in range(4)]
    )
    service = AnalysisService(Settings(database=database), backend)
    try:
        _, balanced = service.ask("Hello", selected=4, conversation=True, local=False, cached=False)
        _, growth = service.ask("Hello", selected=1, conversation=True, local=False, cached=False)
        question = "Use both tools: exposure for the selected portfolio and AAPL price."
        service.ask(question, session_id=balanced, conversation=True, local=False, cached=False)
        service.ask(question, session_id=growth, conversation=True, local=False, cached=False)
        assert "exposure for Balanced Portfolio and AAPL" in backend.requests[2][0][0].parts[0].text
        assert "exposure for Growth Equity Fund and AAPL" in backend.requests[3][0][0].parts[0].text
        assert "selected portfolio" not in backend.requests[2][0][0].parts[0].text
    finally:
        service.close()


def test_missing_selected_identity_clarifies_without_any_model_guess(database: Path):
    backend = FakeBackend([])
    service = AnalysisService(Settings(database=database), backend)
    try:
        answer, _ = service.ask(
            "Exposure for the selected portfolio", conversation=True, local=False, cached=False
        )
        assert answer.status == "clarification" and answer.api_calls == 0 and not backend.requests
    finally:
        service.close()
