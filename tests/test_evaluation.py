import json
from pathlib import Path

import pytest
from test_agent import FakeBackend, call

from portiq.agent import PortfolioAgent
from portiq.config import Settings
from portiq.evaluation import compare_rows, evaluate, evaluate_case, reference_exposure


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
    assert output.exists() and output.with_suffix(".md").exists()
