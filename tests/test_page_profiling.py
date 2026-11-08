from pathlib import Path

import pytest

from portiq.agent import AgentResponse, ToolTrace
from portiq.config import Settings
from portiq.errors import QueryError
from portiq.evaluation import score_answer
from portiq.profiling import page_profile
from portiq.sql import execute

pytest.importorskip("apsw")


def test_pager_accesses_penalize_equivalent_wasteful_sql(database: Path, source: Path):
    reference = "SELECT COUNT(*) FROM portfolios"
    wasteful = (
        "SELECT COUNT(DISTINCT p.portfolio_id) FROM portfolios p CROSS JOIN historical_prices"
    )
    small, large = page_profile(database, reference), page_profile(database, wasteful)
    assert small["rows"] == large["rows"] == [[13]]
    assert 0 < small["logical_page_reads"] < large["logical_page_reads"]
    assert small["logical_page_reads"] == small["cache_hits"] + small["cache_misses"]
    assert page_profile(database, reference) == small  # Fresh cache, repeatable measurements.
    answer = AgentResponse(
        request_id="io-test",
        status="answer",
        answer="There are 13 portfolios.",
        tools=[
            ToolTrace(
                tool="sql_query",
                arguments={},
                result=execute(database, wasteful).model_dump(),
                duration_ms=0,
            )
        ],
        model="offline",
        model_versions=[],
        duration_ms=0,
        model_duration_ms=0,
        api_calls=0,
        tokens=0,
    )
    case = {"id": "io", "question": "Count portfolios", "ground_truth": {"sql_query": reference}}
    good = score_answer(Settings(database=database, source=source), case, answer, profile_io=True)
    assert good["passed"] and 0 < good["efficiency_score"] < 100
    assert good["sql_efficiency"][0]["logical_page_reads"] == large["logical_page_reads"]
    answer.answer = "There are 14 portfolios."
    bad = score_answer(Settings(database=database, source=source), case, answer, profile_io=True)
    assert bad["result_correct"] and not bad["passed"] and bad["efficiency_score"] == 0


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM portfolios",
        "SELECT load_extension('anything')",
        "SELECT * FROM sqlite_master",
        "SELECT randomblob(100000000)",
    ],
)
def test_optional_profiler_preserves_sql_safety(database: Path, sql: str):
    with pytest.raises(QueryError):
        page_profile(database, sql)


def test_failed_scoring_retains_already_consumed_provider_usage(database: Path, monkeypatch):
    from test_agent import FakeBackend, call

    from portiq.agent import PortfolioAgent
    from portiq.evaluation import evaluate_case

    def failed(*args, **kwargs):
        raise QueryError("Profiling failed after generation.")

    monkeypatch.setattr("portiq.evaluation.score_answer", failed)
    agent = PortfolioAgent(
        Settings(database=database),
        FakeBackend([call("respond", status="unsupported", answer="Cannot forecast.")]),
    )
    record = evaluate_case(agent, {"id": "failure", "question": "Forecast"}, profile_io=True)
    assert not record["passed"] and record["actual"]["api_calls"] == 1
    assert record["actual"]["tokens"] == 5
