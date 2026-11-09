from pathlib import Path

import pytest
from google.genai import types
from test_agent import FakeBackend, call, plan

from portiq.agent import PortfolioAgent, ToolTrace, can_render_complete, tool_declarations
from portiq.config import Settings


def sql_call(sql: str, *, complete: object = True) -> types.GenerateContentResponse:
    return call(
        "sql_query",
        question="Read requested data",
        sql=sql,
        explanation="Read data",
        complete=complete,
    )


def test_complete_list_uses_one_model_call(database: Path) -> None:
    backend = FakeBackend(
        [sql_call("SELECT portfolio_name FROM portfolios ORDER BY portfolio_name")]
    )
    answer = PortfolioAgent(Settings(database=database), backend).answer("List all portfolio names")
    assert answer.status == "answer" and answer.api_calls == 1
    assert len(answer.tools[0].result["rows"]) == 13
    assert all(row[0] in answer.answer for row in answer.tools[0].result["rows"])
    assert answer.rendering == "validated tool results after Gemini complete plan"
    assert answer.cache == "disabled" and answer.model == "gemini-3.1-flash-lite"


def test_complete_exposure_uses_verified_arithmetic_without_synthesis(database: Path) -> None:
    backend = FakeBackend([call("exposure_calculator", portfolio="Balanced", complete=True)])
    answer = PortfolioAgent(Settings(database=database), backend).answer("Balanced sector exposure")
    assert answer.status == "answer" and answer.api_calls == 1
    assert all(text in answer.answer for text in ["61.11%", "22.22%", "16.67%", "bonds excluded"])


@pytest.mark.parametrize("second_complete,expected_calls", [(True, 1), (False, 2)])
def test_hybrid_finishes_only_when_every_part_of_batch_is_complete(
    database: Path, second_complete: bool, expected_calls: int
) -> None:
    response = call("exposure_calculator", portfolio="Balanced Portfolio", complete=True)
    response.candidates[0].content.parts.extend(
        sql_call(
            "SELECT current_price FROM securities WHERE symbol='AAPL'", complete=second_complete
        )
        .candidates[0]
        .content.parts
    )
    backend = FakeBackend(
        [response, call("respond", status="answer", answer="A grounded synthesized answer")]
    )
    answer = PortfolioAgent(Settings(database=database), backend).answer("Exposure and AAPL price")
    assert answer.api_calls == expected_calls and len(answer.tools) == 2
    if second_complete:
        assert "61.11%" in answer.answer and "185.5" in answer.answer
    else:
        assert answer.answer == "A grounded synthesized answer"


def test_complete_result_preserves_numeric_precision(database: Path) -> None:
    backend = FakeBackend([sql_call("SELECT 1.234567891234 AS current_price")])
    answer = PortfolioAgent(Settings(database=database), backend).answer("Read the precise price")
    assert answer.api_calls == 1 and "1.234567891234" in answer.answer


@pytest.mark.parametrize(
    "sql,max_rows",
    [
        ("SELECT portfolio_name FROM portfolios", 1),
        ("SELECT holding_id FROM holdings", 1000),
        ("SELECT portfolio_name FROM portfolios WHERE portfolio_id=-1", 1000),
        ("SELECT 'a|b' AS name", 1000),
        ("SELECT 'a\nb' AS name", 1000),
    ],
)
def test_incomplete_or_lossy_display_keeps_normal_loop(
    database: Path, sql: str, max_rows: int
) -> None:
    backend = FakeBackend(
        [sql_call(sql), call("respond", status="answer", answer="Model handles the result shape")]
    )
    answer = PortfolioAgent(Settings(database=database, max_rows=max_rows), backend).answer(
        "Read data"
    )
    assert answer.api_calls == 2 and answer.answer == "Model handles the result shape"


def test_nonfinite_evidence_cannot_finish_early() -> None:
    trace = ToolTrace(
        tool="sql_query",
        arguments={},
        result={"columns": ["value"], "rows": [[float("inf")]], "truncated": False},
        duration_ms=0,
    )
    assert not can_render_complete([trace])


@pytest.mark.parametrize("portfolio", ["equity", "missing fund"])
def test_complete_flag_cannot_turn_ambiguous_or_missing_portfolio_into_answer(
    database: Path, portfolio: str
) -> None:
    backend = FakeBackend(
        [
            call("exposure_calculator", portfolio=portfolio, complete=True),
            call("respond", status="clarification", answer="Please specify an existing fund"),
        ]
    )
    answer = PortfolioAgent(Settings(database=database), backend).answer("Show fund exposure")
    assert answer.status == "clarification" and answer.api_calls == 2
    assert answer.tools[0].error


def test_complete_flag_does_not_bypass_sql_safety(database: Path) -> None:
    before = database.read_bytes()
    backend = FakeBackend(
        [
            sql_call("DELETE FROM portfolios"),
            plan("DELETE FROM portfolios"),
            call("respond", status="unsupported", answer="Cannot modify data"),
        ]
    )
    answer = PortfolioAgent(Settings(database=database), backend).answer("Delete portfolios")
    assert answer.status == "error" and answer.tools[0].error
    assert database.read_bytes() == before


def test_complete_flag_is_strictly_typed(database: Path) -> None:
    backend = FakeBackend(
        [
            sql_call("SELECT COUNT(*) FROM portfolios", complete="yes"),
            call("respond", status="clarification", answer="Cannot use invalid arguments"),
        ]
    )
    answer = PortfolioAgent(Settings(database=database), backend).answer("Count portfolios")
    assert answer.status == "clarification" and answer.tools[0].error


def test_baseline_switch_keeps_original_contract_and_synthesis(database: Path) -> None:
    backend = FakeBackend(
        [
            sql_call("SELECT COUNT(*) FROM portfolios"),
            call("respond", status="answer", answer="There are 13 portfolios"),
        ]
    )
    agent = PortfolioAgent(Settings(database=database, direct_results=False), backend)
    answer = agent.answer("Count all portfolios")
    assert answer.api_calls == 2 and answer.answer == "There are 13 portfolios"
    assert "set complete=true" not in agent.system
    for declaration in tool_declarations(direct_results=False)[:2]:
        assert "complete" not in declaration.parameters_json_schema["properties"]
