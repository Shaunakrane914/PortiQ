import json
from pathlib import Path

import pytest
from test_agent import FakeBackend, call

from portiq.agent import AgentResponse, PortfolioAgent
from portiq.config import Settings
from portiq.evaluation import (
    compare_rows,
    evaluate,
    evaluate_case,
    reference_exposure,
    score_answer,
)


@pytest.mark.parametrize(
    "expected,actual,ordered,passes",
    [
        ([[1], [2]], [[2], [1]], False, True),
        ([[1], [2]], [[2], [1]], True, False),
        ([[1], [1]], [[1], [2]], False, False),
        ([[1]], [[1], [2]], False, False),
        ([[None]], [[0]], False, False),
        ([[1.0]], [[1.00000001]], False, True),
        ([[1.0]], [[float("nan")]], False, False),
        ([[1]], [["1"]], False, False),
        ([[1, 2]], [[1]], False, False),
        ([], [], False, True),
    ],
)
def test_comparison(expected: list, actual: list, ordered: bool, passes: bool) -> None:
    assert (compare_rows(expected, actual, ordered=ordered) is None) == passes


def test_supplied_references_are_executable(database: Path, source: Path) -> None:
    from portiq.sql import execute

    cases = json.loads((source / "ground_truth_dataset.json").read_text())["questions"]
    for case in cases:
        reference = case["ground_truth"]
        if "sql_query" in reference:
            execute(database, reference["sql_query"])
        else:
            assert reference_exposure(source, reference["parameters"]["portfolio_name"])


def test_all_frozen_extended_references(database: Path, source: Path) -> None:
    from portiq.sql import execute

    cases = json.loads((source / "evaluation/extended.json").read_text())["questions"]
    assert len(cases) == 50
    assert len({c["id"] for c in cases}) == 50
    assert {c["split"] for c in cases} == {"development", "validation", "heldout"}
    for case in cases:
        if case.get("expected_status"):
            assert case["expected_status"] in {"clarification", "unsupported"}
            continue
        for reference in case.get("references", [case.get("ground_truth", {})]):
            if "sql_query" in reference:
                assert not execute(database, reference["sql_query"]).truncated
            else:
                assert reference_exposure(source, reference["parameters"]["portfolio_name"])


def test_evaluator_rejects_incorrect_sql_even_plausible_prose(database: Path, source: Path) -> None:
    case = {
        "id": 1,
        "question": "Count portfolios",
        "ground_truth": {"sql_query": "SELECT COUNT(*) FROM portfolios"},
    }
    backend = FakeBackend(
        [
            call("sql_query", question="Count", sql="SELECT 12", explanation="wrong count"),
            call("respond", status="answer", answer="There are 13 portfolios."),
        ]
    )
    result = evaluate_case(
        PortfolioAgent(Settings(database=database, source=source), backend), case
    )
    assert not result["passed"] and "mismatched" in result["failure"]
    assert result["routing_correct"] and not result["result_correct"]


def test_evaluator_extra_columns_fail(database: Path, source: Path) -> None:
    case = {
        "id": 1,
        "question": "Count portfolios",
        "ground_truth": {"sql_query": "SELECT COUNT(*) FROM portfolios"},
    }
    backend = FakeBackend(
        [
            call(
                "sql_query",
                question="Count",
                sql="SELECT COUNT(*), 42 FROM portfolios",
                explanation="extra column",
            ),
            call("respond", status="answer", answer="13"),
        ]
    )
    result = evaluate_case(
        PortfolioAgent(Settings(database=database, source=source), backend), case
    )
    assert not result["passed"] and "Projection width" in result["failure"]


def test_report_artifacts(database: Path, source: Path, tmp_path: Path) -> None:
    suite = tmp_path / "suite.json"
    suite.write_text(
        json.dumps(
            {
                "questions": [
                    {
                        "id": "e",
                        "question": "Exposure",
                        "ground_truth": {"parameters": {"portfolio_name": "Tech Innovation Fund"}},
                    }
                ]
            }
        )
    )
    backend = FakeBackend(
        [
            call("exposure_calculator", portfolio="3"),
            call("respond", status="answer", answer="Technology 100%"),
        ]
    )
    output = tmp_path / "report.json"
    report = evaluate(
        PortfolioAgent(Settings(database=database, source=source), backend), suite, output
    )
    assert report["passed"] == report["total"] == 1
    assert report["answer_correct"] == report["routing_correct"] == 1
    assert report["evaluator_version"] == 3
    assert report["narrative_checked"] == 1
    assert output.exists() and output.with_suffix(".md").exists()


def test_historical_passive_failure_scores_semantics_and_routing(
    database: Path,
    source: Path,
) -> None:
    passive_sql = (
        "SELECT portfolio_name FROM portfolios WHERE strategy_type = 'Passive' "
        "ORDER BY portfolio_name ASC;"
    )
    actual = {
        "request_id": "test-ext-02",
        "status": "answer",
        "answer": "There are no passive portfolios.",
        "tools": [
            {
                "tool": "sql_query",
                "arguments": {
                    "sql": passive_sql,
                    "question": "List the names of Passive portfolios, alphabetically.",
                    "explanation": "Retrieve names where strategy_type is Passive",
                },
                "result": {
                    "columns": ["portfolio_name"],
                    "rows": [],
                    "sql": passive_sql,
                    "duration_ms": 1.5,
                    "truncated": False,
                },
                "duration_ms": 2.0,
            },
            {
                "tool": "sql_query",
                "arguments": {
                    "sql": "SELECT DISTINCT strategy_type FROM portfolios;",
                    "question": "Distinct strategy types",
                    "explanation": "Check distinct values",
                },
                "result": {
                    "columns": ["strategy_type"],
                    "rows": [["Growth"], ["Income"], ["Index"]],
                    "sql": "SELECT DISTINCT strategy_type FROM portfolios;",
                    "duration_ms": 1.5,
                    "truncated": False,
                },
                "duration_ms": 2.0,
            },
        ],
        "model": "gemini-3.1-flash-lite",
        "model_versions": [],
        "duration_ms": 10.0,
        "model_duration_ms": 8.0,
        "api_calls": 2,
        "tokens": 100,
    }
    suite = json.loads((source / "evaluation/extended.json").read_text())["questions"]
    case = next(c for c in suite if c["id"] == "ext-02")
    result = score_answer(
        Settings(database=database, source=source),
        case,
        AgentResponse.model_validate(actual),
        narrative_rules=["portfolio_names"],
    )
    assert result["sql_valid"] is True
    assert not result["routing_correct"] and not result["result_correct"]
    assert not result["answer_correct"] and not result["passed"]
    assert result["faithfulness"]["status"] == "failed"
    assert len(result["expected"][0]["rows"]) == 3
    assert {f["dimension"] for f in result["failures"]} == {"routing", "result", "faithfulness"}
    assert "Row count" in result["failure"]


def test_extra_discovery_does_not_hide_correct_evidence(database: Path, source: Path) -> None:
    case = {
        "id": "count",
        "question": "Count portfolios",
        "ground_truth": {"sql_query": "SELECT COUNT(*) FROM portfolios"},
    }
    backend = FakeBackend(
        [
            call(
                "sql_query",
                question="Discover statuses",
                sql="SELECT DISTINCT status FROM portfolios",
                explanation="Discovery",
            ),
            call(
                "sql_query",
                question="Count portfolios",
                sql="SELECT COUNT(*) FROM portfolios",
                explanation="Count",
            ),
            call("respond", status="answer", answer="There are 13 portfolios."),
        ]
    )
    result = evaluate_case(
        PortfolioAgent(Settings(database=database, source=source), backend),
        case,
        narrative_rules=["portfolio_count"],
    )
    assert result["answer_correct"] and result["result_correct"]
    assert not result["routing_correct"] and not result["passed"]
    assert [f["dimension"] for f in result["failures"]] == ["routing"]


@pytest.mark.parametrize(
    "answer", ["There are 14 portfolios.", "There are no portfolios; old count 13."]
)
def test_correct_sql_cannot_mask_a_false_narrative(
    database: Path, source: Path, answer: str
) -> None:
    case = {
        "id": "count",
        "question": "Count portfolios",
        "ground_truth": {"sql_query": "SELECT COUNT(*) FROM portfolios"},
    }
    backend = FakeBackend(
        [
            call(
                "sql_query",
                question="Count",
                sql="SELECT COUNT(*) FROM portfolios",
                explanation="Count",
            ),
            call("respond", status="answer", answer=answer),
        ]
    )
    result = evaluate_case(
        PortfolioAgent(Settings(database=database, source=source), backend),
        case,
        narrative_rules=["portfolio_count"],
    )
    assert result["routing_correct"] and result["result_correct"]
    assert not result["answer_correct"] and not result["passed"]
    assert [f["dimension"] for f in result["failures"]] == ["faithfulness"]


def test_truncated_evidence_and_duplicate_reference_assignment(
    database: Path, source: Path
) -> None:
    reference = {"sql_query": "SELECT portfolio_name FROM portfolios"}
    case = {"id": "names", "question": "List names", "ground_truth": reference}
    backend = FakeBackend(
        [
            call("sql_query", question="List", sql=reference["sql_query"], explanation="List"),
            call("respond", status="answer", answer="Here are the names."),
        ]
    )
    agent = PortfolioAgent(Settings(database=database, source=source, max_rows=1), backend)
    result = evaluate_case(agent, case)
    assert not result["result_correct"] and "Truncated" in result["failure"]
    stored = AgentResponse.model_validate(result["actual"])
    # Even two identical references require two distinct tool results.
    from portiq.sql import execute

    stored.tools[0].result = execute(database, reference["sql_query"]).model_dump(mode="json")
    duplicate = score_answer(agent.settings, {**case, "references": [reference, reference]}, stored)
    assert not duplicate["passed"]
    assert "distinct matching" in duplicate["failure"]


def test_nonfinite_exposure_fails_reference_scoring(database: Path, source: Path) -> None:
    backend = FakeBackend(
        [
            call("exposure_calculator", portfolio="3"),
            call("respond", status="answer", answer="Technology 100%."),
        ]
    )
    agent = PortfolioAgent(Settings(database=database, source=source), backend)
    answer = agent.answer("Tech exposure")
    answer.tools[0].result["sectors"]["Technology"] = "NaN"
    result = score_answer(
        agent.settings,
        {
            "id": "exposure",
            "question": "Tech exposure",
            "ground_truth": {"parameters": {"portfolio_name": "Tech Innovation Fund"}},
        },
        answer,
    )
    assert not result["result_correct"] and "percentage mismatch" in result["failure"]


def test_provider_error_is_not_a_numerical_narrative_claim(database: Path, source: Path) -> None:
    result = score_answer(
        Settings(database=database, source=source),
        {
            "id": "price",
            "question": "What is the price?",
            "ground_truth": {"sql_query": "SELECT 185.5"},
        },
        AgentResponse(
            request_id="provider-error",
            status="error",
            answer="Gemini request failed (status=429).",
            tools=[],
            model="test",
            model_versions=[],
            duration_ms=0,
            model_duration_ms=0,
            api_calls=1,
            tokens=0,
        ),
        narrative_rules=["scalar"],
    )
    assert not result["passed"] and not result["answer_correct"]
    assert result["faithfulness"]["status"] == "not_checked"
    assert result["faithfulness"]["configured_rules"] == ["scalar"]
    assert {f["dimension"] for f in result["failures"]} == {"status", "routing", "result"}
