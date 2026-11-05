import os

import pytest

from portiq.agent import PortfolioAgent
from portiq.config import Settings
from portiq.model import GeminiBackend


@pytest.mark.live
@pytest.mark.skipif(
    os.getenv("PORTIQ_LIVE") != "1", reason="Set PORTIQ_LIVE=1 for real Gemini calls"
)
def test_live_categorical_column_semantics() -> None:
    import json

    from portiq.evaluation import evaluate_case

    settings = Settings.from_env()
    cases = json.loads((settings.source / "evaluation/extended.json").read_text())["questions"]
    case = next(c for c in cases if c["id"] == "ext-02")
    backend = GeminiBackend(settings)
    try:
        result = evaluate_case(
            PortfolioAgent(settings, backend), case, narrative_rules=["portfolio_names"]
        )
        assert result["result_correct"] and result["routing_correct"] and result["answer_correct"]
        assert result["faithfulness"]["status"] == "passed"
    finally:
        backend.close()


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
