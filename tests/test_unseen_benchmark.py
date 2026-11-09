import json
from pathlib import Path

from portiq.agent import ToolTrace, render_tools
from portiq.config import Settings
from portiq.evaluation import _expectations
from portiq.faithfulness import verify_answer


def test_unseen_benchmark_expectations_and_rendering(database: Path, source: Path) -> None:
    settings = Settings(database=database, source=source)
    with (source / "evaluation/unseen_nlp.json").open(encoding="utf-8") as f:
        data = json.load(f)

    questions = data["questions"]
    assert len(questions) == 32

    for case in questions:
        expected = _expectations(settings, case)
        if case.get("expected_status", "answer") != "answer":
            assert not expected
            continue

        assert expected, f"Case {case['id']} should have expected analytical results"
        traces = []
        for exp in expected:
            if exp["tool"] == "sql_query":
                traces.append(
                    ToolTrace(
                        tool="sql_query",
                        arguments={"sql": exp["sql"], "question": case["question"]},
                        result={
                            "columns": exp["columns"],
                            "rows": exp["rows"],
                            "truncated": False,
                            "sql": exp["sql"],
                        },
                        duration_ms=1.0,
                    )
                )
            elif exp["tool"] == "exposure_calculator":
                traces.append(
                    ToolTrace(
                        tool="exposure_calculator",
                        arguments={"portfolio": exp["portfolio_name"]},
                        result={
                            "portfolio_name": exp["portfolio_name"],
                            "sectors": exp["sectors"],
                        },
                        duration_ms=1.0,
                    )
                )

        rendered = render_tools(traces, question=case["question"])
        assert rendered, f"Rendering failed for {case['id']}"
        verification = verify_answer(rendered, expected, [])
        assert verification["status"] == "passed", (
            f"Faithfulness verification failed for {case['id']}: {verification['failures']}"
        )
