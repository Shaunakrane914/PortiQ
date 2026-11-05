"""Independent result evaluation. This module is never imported by runtime agent code."""

import csv
import json
import math
import statistics
import time
from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import sqlglot

from portiq.agent import PortfolioAgent
from portiq.database import connect_readonly
from portiq.errors import PortiqError
from portiq.sql import execute


def cells_equal(expected: Any, actual: Any) -> bool:
    if expected is None or actual is None:
        return expected is actual
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return math.isfinite(float(actual)) and math.isclose(
            expected,
            actual,
            rel_tol=1e-7,
            abs_tol=1e-6,
        )
    return type(expected) is type(actual) and expected == actual


def compare_rows(
    expected: list[list[Any]], actual: list[list[Any]], *, ordered: bool
) -> str | None:
    """Compare all cells and duplicate multiplicities, with numeric tolerance."""
    if len(expected) != len(actual):
        return f"Row count: expected {len(expected)}, actual {len(actual)}."

    def equal(left: list[Any], right: list[Any]) -> bool:
        return len(left) == len(right) and all(
            cells_equal(a, b) for a, b in zip(left, right, strict=True)
        )

    if ordered:
        for index, (left, right) in enumerate(zip(expected, actual, strict=True)):
            if not equal(left, right):
                return f"Ordered row {index}: expected {left}, actual {right}."
        return None
    # Maximum bipartite matching avoids a greedy tolerance match stealing another row's match.
    candidates = [[j for j, row in enumerate(actual) if equal(left, row)] for left in expected]
    matched: dict[int, int] = {}

    def augment(index: int, visited: set[int]) -> bool:
        for candidate in candidates[index]:
            if candidate in visited:
                continue
            visited.add(candidate)
            if candidate not in matched or augment(matched[candidate], visited):
                matched[candidate] = index
                return True
        return False

    for index in range(len(expected)):
        if not augment(index, set()):
            return f"Missing or mismatched row (including duplicate count): {expected[index]}."
    return None


def reference_exposure(source: Path, portfolio_name: str) -> dict[str, float]:
    """Read original CSVs directly; no production resolver, DB joins, or calculator."""

    def read(table: str) -> list[dict[str, str]]:
        with (source / "data" / f"{table}.csv").open(encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))

    portfolios = [p for p in read("portfolios") if p["portfolio_name"] == portfolio_name]
    if len(portfolios) != 1:
        raise ValueError("Reference portfolio must be an exact unique CSV name.")
    securities = {s["security_id"]: s for s in read("securities") if s["asset_type"] == "Stock"}
    sectors = {s["sector_id"]: s["sector_name"] for s in read("sectors")}
    amounts: dict[str, Decimal] = defaultdict(Decimal)
    for holding in read("holdings"):
        if holding["portfolio_id"] == portfolios[0]["portfolio_id"]:
            security = securities.get(holding["security_id"])
            if security:
                amounts[sectors[security["sector_id"]]] += Decimal(holding["current_weight"])
    total = sum(amounts.values(), Decimal(0))
    if total <= 0:
        raise ValueError("Reference has no equity weight.")
    return {sector: float(weight * 100 / total) for sector, weight in amounts.items()}


def _reference_sql(path: Path, sql: str) -> tuple[list[str], list[list[Any]]]:
    # Trusted reference SQL runs through an independent connection, not generated-SQL machinery.
    with connect_readonly(path) as conn:
        deadline = time.perf_counter() + 2
        conn.set_progress_handler(lambda: int(time.perf_counter() > deadline), 1000)
        cursor = conn.execute(sql)
        return [c[0] for c in cursor.description], [list(r) for r in cursor.fetchall()]


def evaluate_case(agent: PortfolioAgent, case: dict[str, Any]) -> dict[str, Any]:
    start = time.perf_counter()
    record: dict[str, Any] = {
        "id": case["id"],
        "question": case["question"],
        "category": case.get("category", case.get("type")),
        "split": case.get("split", "supplied"),
        "passed": False,
        "routing_correct": False,
        "sql_valid": None,
        "expected": [],
    }
    try:
        answer = agent.answer(case["question"])
        record["actual"] = answer.model_dump(mode="json")
        expected_status = case.get("expected_status", "answer")
        if answer.status != expected_status:
            record["failure"] = f"Expected status {expected_status}; actual {answer.status}."
            return record
        if expected_status != "answer":
            # Subjective handling has explicit status/no-mutation rules, not exact prose equality.
            record["routing_correct"] = True
            record["passed"] = True
            return record
        references = case.get("references", [case.get("ground_truth", {})])
        expected_tools = [
            "sql_query" if "sql_query" in ref else "exposure_calculator" for ref in references
        ]
        successful = [t for t in answer.tools if t.result is not None]
        record["routing_correct"] = sorted(t.tool for t in successful) == sorted(expected_tools)
        if not record["routing_correct"]:
            record["failure"] = (
                f"Expected tools {expected_tools}; got {[t.tool for t in successful]}."
            )
            return record
        remaining = list(successful)
        for reference in references:
            if "sql_query" in reference:
                columns, expected = _reference_sql(agent.settings.database, reference["sql_query"])
                record["expected"].append({"columns": columns, "rows": expected})
                candidate = next(t for t in remaining if t.tool == "sql_query")
                remaining.remove(candidate)
                actual = candidate.result
                assert actual is not None
                # Independent re-execution checks data returned by the agent, too.
                query = execute(agent.settings.database, actual["sql"], max_rows=5000)
                record["sql_valid"] = True
                if actual["truncated"] or query.truncated:
                    record["failure"] = "Truncated query results cannot pass evaluation."
                    return record
                if len(columns) != len(query.columns):
                    record["failure"] = (
                        f"Projection width: expected {columns}, got {query.columns}."
                    )
                    return record
                ordered = bool(
                    sqlglot.parse_one(reference["sql_query"], read="sqlite").args.get("order")
                )
                mismatch = compare_rows(query.rows, actual["rows"], ordered=True)
                mismatch = mismatch or compare_rows(expected, query.rows, ordered=ordered)
            else:
                name = reference["parameters"]["portfolio_name"]
                expected_exposure = reference_exposure(agent.settings.source, name)
                record["expected"].append({"portfolio_name": name, "sectors": expected_exposure})
                candidate = next(
                    t
                    for t in remaining
                    if t.tool == "exposure_calculator"
                    and t.result
                    and t.result["portfolio_name"] == name
                )
                remaining.remove(candidate)
                assert candidate.result is not None
                actual_exposure = candidate.result["sectors"]
                mismatch = None
                if set(expected_exposure) != set(actual_exposure):
                    mismatch = "Exposure sector sets differ."
                elif any(
                    abs(expected_exposure[k] - float(actual_exposure[k])) > 0.005001
                    for k in expected_exposure
                ):
                    mismatch = (
                        "Exposure percentage mismatch (tolerance 0.005001 percentage points)."
                    )
            if mismatch:
                record["failure"] = mismatch
                return record
        record["passed"] = True
    except (PortiqError, ValueError, KeyError, StopIteration) as exc:
        record["failure"] = f"Evaluation failed: {type(exc).__name__}: {exc}"
    finally:
        record["duration_ms"] = round((time.perf_counter() - start) * 1000, 3)
    return record


def evaluate(
    agent: PortfolioAgent,
    suite: Path,
    output: Path,
    *,
    trials: int = 1,
    split: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    cases = json.loads(suite.read_text(encoding="utf-8"))["questions"]
    if split:
        cases = [c for c in cases if c.get("split") == split]
    if limit:
        cases = cases[:limit]
    records = []
    for trial in range(1, trials + 1):
        for case in cases:
            record = evaluate_case(agent, case)
            record["trial"] = trial
            records.append(record)
            print(
                f"trial={trial} id={case['id']} {'PASS' if record['passed'] else 'FAIL'} "
                f"{record.get('failure', '')}",
                flush=True,
            )
    durations = sorted(r["duration_ms"] for r in records)
    report = {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "suite": suite.name,
        "model": agent.settings.model,
        "cache": "disabled",
        "trials": trials,
        "split": split or "all",
        "total": len(records),
        "passed": sum(r["passed"] for r in records),
        "routing_correct": sum(r["routing_correct"] for r in records),
        "mean_ms": statistics.mean(durations) if durations else None,
        "p95_ms": durations[max(0, math.ceil(len(durations) * 0.95) - 1)] if durations else None,
        "api_calls": sum(r.get("actual", {}).get("api_calls", 0) for r in records),
        "tokens": sum(r.get("actual", {}).get("tokens", 0) for r in records),
        "records": records,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    output.with_suffix(".md").write_text(
        f"# Evaluation: {suite.name}\n\n{report['passed']}/{report['total']} passed. "
        f"Routing: {report['routing_correct']}/{report['total']}. "
        f"Model: `{report['model']}`. Cache disabled. Trials: {trials}.\n\n"
        "| Trial | ID | Pass | Failure |\n|---|---|---|---|\n"
        + "\n".join(
            f"| {r['trial']} | {r['id']} | {r['passed']} | "
            f"{str(r.get('failure', '')).replace('|', '/')} |"
            for r in records
        )
        + "\n",
        encoding="utf-8",
    )
    return report
