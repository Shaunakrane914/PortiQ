"""Independent regression probes for final-answer verification and terminal entry points."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from portiq.agent import AgentResponse, ToolTrace
from portiq.config import Settings
from portiq.evaluation import score_answer
from portiq.exposure import calculate_exposure
from portiq.faithfulness import verify_answer
from portiq.sql import execute


def response_for(database: Path, case: dict) -> AgentResponse:
    reference = case["ground_truth"]
    if "sql_query" in reference:
        result = execute(database, reference["sql_query"]).model_dump()
        text = (
            " | ".join(result["columns"])
            + "\n"
            + "\n".join(" | ".join(str(value) for value in row) for row in result["rows"])
        )
        tool = "sql_query"
    else:
        result = calculate_exposure(
            database, reference["parameters"]["portfolio_name"]
        ).model_dump()
        text = (
            result["portfolio_name"]
            + "\n"
            + "\n".join(f"{sector}: {value}%" for sector, value in result["sectors"].items())
        )
        tool = "exposure_calculator"
    return AgentResponse(
        request_id="verification-probe",
        status="answer",
        answer=text,
        tools=[ToolTrace(tool=tool, arguments={}, result=result, duration_ms=0)],
        model="offline",
        model_versions=[],
        duration_ms=0,
        model_duration_ms=0,
        api_calls=0,
        tokens=0,
    )


@pytest.mark.parametrize("identifier", range(1, 11))
def test_every_supplied_format_accepts_complete_answer_and_rejects_false_prose(
    database: Path, source: Path, identifier: int
) -> None:
    cases = json.loads((source / "ground_truth_dataset.json").read_text())["questions"]
    case = next(case for case in cases if case["id"] == identifier)
    answer = response_for(database, case)
    settings = Settings(database=database, source=source)
    good = score_answer(settings, case, answer)
    assert good["passed"] and good["answer_verification"]["status"] == "passed"
    answer.answer = (
        "There are no active portfolios." if identifier == 2 else "Unrelated false answer."
    )
    bad = score_answer(settings, case, answer)
    assert bad["result_correct"] and bad["routing_correct"]
    assert not bad["passed"] and not bad["answer_correct"]
    assert bad["answer_verification"]["status"] == "failed"
    assert bad["efficiency_score"] in {0.0, None}


def test_prose_cannot_swap_metrics_omit_sectors_or_include_conflicting_counts() -> None:
    expected = [{"columns": ["name", "tech_value", "total_value"], "rows": [["Fund A", 100, 200]]}]
    assert verify_answer("| Fund A | 100 | 200 |", expected, [])["status"] == "passed"
    assert verify_answer("| Fund A | 200 | 100 |", expected, [])["status"] == "failed"
    exposure = [{"portfolio_name": "Fund A", "sectors": {"Technology": 60.0, "Energy": 40.0}}]
    assert verify_answer("Technology 60%", exposure, ["Fund A"])["status"] == "failed"
    assert (
        verify_answer(
            "Technology 60%; Energy 40%. No bond holdings are included.", exposure, ["Fund A"]
        )["status"]
        == "passed"
    )
    names = [{"columns": ["portfolio_name"], "rows": [["Fund A"], ["Fund B"]]}]
    assert verify_answer("3 active portfolios: Fund A, Fund B.", names, [])["status"] == "failed"
    assert (
        verify_answer(
            "The value is 12, although the reference says 13.",
            [{"columns": ["count"], "rows": [[13]]}],
            [],
        )["status"]
        == "failed"
    )


def test_shortcuts_preserve_global_options_and_require_explicit_local_mode(
    database: Path, source: Path, tmp_path: Path
) -> None:
    env = os.environ | {"GEMINI_API_KEY": "", "PORTIQ_DB": str(tmp_path / "untouched.db")}

    def run(*arguments):
        return subprocess.run(
            [sys.executable, str(source / "main.py"), *arguments],
            cwd=source,
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
        )

    help_result = run("--help")
    assert help_result.returncode == 0 and "evaluate" in help_result.stdout
    assert not (tmp_path / "untouched.db").exists()
    result = run("--db", str(database), "exposure", "Balanced Portfolio")
    assert result.returncode == 0 and "61.11" in result.stdout
    local = run("--db=" + str(database), "Count all portfolios", "--local", "--json")
    assert local.returncode == 0 and json.loads(local.stdout)["api_calls"] == 0
    genuine = run("--db", str(database), "Count all portfolios")
    assert genuine.returncode == 1 and "GEMINI_API_KEY" in genuine.stderr
