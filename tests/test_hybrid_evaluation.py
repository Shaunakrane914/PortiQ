"""Replay historical hybrids and mutate their prose; no provider or judge calls."""

import json
from pathlib import Path

import pytest

from portiq.agent import AgentResponse
from portiq.config import Settings
from portiq.evaluation import score_answer


@pytest.fixture(params=["ext-44", "ext-45", "ext-46"])
def hybrid(request, source: Path):
    cases = json.loads((source / "evaluation/extended.json").read_text())["questions"]
    archive = json.loads((source / "reports/cli-2026-11-08/extended.json").read_text())
    case = next(c for c in cases if c["id"] == request.param)
    row = next(r for r in archive["records"] if r["id"] == request.param)
    return case, AgentResponse.model_validate(row["actual"])


def test_historical_hybrids_pass_complete_evidence_and_prose(database: Path, source: Path, hybrid):
    case, answer = hybrid
    record = score_answer(Settings(database=database, source=source), case, answer)
    assert record["passed"] and record["result_correct"] and record["routing_correct"]
    assert record["narrative_status"] == "passed"


@pytest.mark.parametrize(
    "mutation", ["wrong_price", "missing_price", "wrong_exposure", "negated_price", "conflict"]
)
def test_hybrid_rejects_wrong_or_missing_claim_without_weakening_evidence(
    database: Path, source: Path, hybrid, mutation: str
):
    case, answer = hybrid
    price = {"ext-44": "185.50", "ext-45": "415.26", "ext-46": "875.30"}[case["id"]]
    percentage = {"ext-44": "61.11", "ext-45": "93.00", "ext-46": "38.00"}[case["id"]]
    if mutation == "wrong_price":
        answer.answer = answer.answer.replace(price, "999.99")
    elif mutation == "missing_price":
        answer.answer = answer.answer.replace(price, "unavailable")
    elif mutation == "wrong_exposure":
        answer.answer = answer.answer.replace(percentage + "%", "99.99%")
    elif mutation == "negated_price":
        answer.answer = answer.answer.replace(price, "not " + price)
    else:
        answer.answer += " The current price is actually 999.99."
    record = score_answer(Settings(database=database, source=source), case, answer)
    assert record["result_correct"] and record["routing_correct"]
    assert not record["passed"] and record["narrative_status"] == "failed"
    assert record["efficiency_score"] == 0


def test_hybrid_requires_both_distinct_tools(database: Path, source: Path, hybrid):
    case, answer = hybrid
    answer.tools = [t for t in answer.tools if t.tool == "exposure_calculator"]
    record = score_answer(Settings(database=database, source=source), case, answer)
    assert not record["passed"] and not record["routing_correct"] and not record["result_correct"]
