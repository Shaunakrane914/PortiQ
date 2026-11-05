import os

import pytest

from portiq.agent import PortfolioAgent
from portiq.config import Settings
from portiq.model import GeminiBackend


@pytest.mark.live
@pytest.mark.skipif(
    os.getenv("PORTIQ_LIVE") != "1", reason="Set PORTIQ_LIVE=1 for real Gemini calls"
)
def test_live_agent() -> None:
    settings = Settings.from_env()
    backend = GeminiBackend(settings)
    try:
        response = PortfolioAgent(settings, backend).answer("Count all portfolios in the database")
        assert response.status == "answer"
        assert any(t.result and t.result.get("rows") == [[13]] for t in response.tools)
    finally:
        backend.close()
