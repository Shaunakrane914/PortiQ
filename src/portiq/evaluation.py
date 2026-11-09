"""Independent result evaluation. This module is never imported by runtime agent code."""

import csv
import hashlib
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

from portiq.agent import AgentResponse, AnswerAgent
from portiq.config import Settings
from portiq.database import connect_readonly
from portiq.errors import PortiqError
from portiq.exposure import ExposureResult
from portiq.faithfulness import check_faithfulness, verify_answer
from portiq.model import GeminiBackend
from portiq.service import FallbackBackend
from portiq.sql import QueryResult, execute


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


def _record(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": case["id"],
        "question": case["question"],
        "category": case.get("category", case.get("type")),
        "split": case.get("split", "supplied"),
        "passed": False,
        "routing_correct": False,
        "answer_correct": False,
        "result_correct": None,
        "data_correct": None,
        "projection_exact": None,
        "status_correct": False,
        "sql_valid": None,
        "narrative_status": "not_checked",
        "expected": [],
        "failures": [],
    }


def _expectations(settings: Settings, case: dict[str, Any]) -> list[dict[str, Any]]:
    if case.get("expected_status", "answer") != "answer":
        return []
    expected = []
    for reference in case.get("references", [case.get("ground_truth", {})]):
        if "sql_query" in reference:
            sql = reference["sql_query"]
            columns, rows = _reference_sql(settings.database, sql)
            expected.append(
                {
                    "tool": "sql_query",
                    "columns": columns,
                    "rows": rows,
                    "ordered": bool(sqlglot.parse_one(sql, read="sqlite").args.get("order")),
                    "sql": sql,
                }
            )
        else:
            name = reference["parameters"]["portfolio_name"]
            expected.append(
                {
                    "tool": "exposure_calculator",
                    "portfolio_name": name,
                    "sectors": reference_exposure(settings.source, name),
                }
            )
    return expected


def _compare_evidence(reference: dict[str, Any], candidate: dict[str, Any]) -> str | None:
    if reference["tool"] != candidate["tool"]:
        return "Different tool type."
    if candidate.get("error"):
        return str(candidate["error"])
    actual = candidate["result"]
    if reference["tool"] == "sql_query":
        ref_cols = [c.lower() for c in reference["columns"]]
        actual_cols = [c.lower() for c in actual["columns"]]
        candidate["projection_exact"] = (len(reference["columns"]) == len(actual["columns"]))
        has_all_cols = len(ref_cols) <= len(actual_cols) and all(c in actual_cols for c in ref_cols)
        if has_all_cols and not candidate["projection_exact"]:
            indices = [actual_cols.index(c) for c in ref_cols]
            projected = [[row[i] for i in indices] for row in actual["rows"]]
            candidate["data_correct"] = (
                compare_rows(reference["rows"], projected, ordered=reference["ordered"]) is None
            )
        else:
            candidate["data_correct"] = candidate["projection_exact"]

        if len(reference["columns"]) != len(actual["columns"]):
            return f"Projection width: expected {reference['columns']}, got {actual['columns']}."
        return compare_rows(reference["rows"], actual["rows"], ordered=reference["ordered"])
    if reference["portfolio_name"] != actual["portfolio_name"]:
        return (
            f"Portfolio identity: expected {reference['portfolio_name']}, "
            f"got {actual['portfolio_name']}."
        )
    if set(reference["sectors"]) != set(actual["sectors"]):
        return "Exposure sector sets differ."
    if any(
        not math.isfinite(float(actual["sectors"][k]))
        or abs(value - float(actual["sectors"][k])) > 0.005001
        for k, value in reference["sectors"].items()
    ):
        return "Exposure percentage mismatch (tolerance 0.005001 percentage points)."
    return None


def score_answer(
    settings: Settings,
    case: dict[str, Any],
    answer: AgentResponse,
    *,
    narrative_rules: list[str] | None = None,
    profile_io: bool = False,
) -> dict[str, Any]:
    """Score evidence, routing and limited prose claims independently; never stop at routing."""
    record = _record(case)
    record["actual"] = answer.model_dump(mode="json")
    record["expected"] = expected = _expectations(settings, case)

    def fail(dimension: str, message: str) -> None:
        record["failures"].append({"dimension": dimension, "message": message})

    expected_status = case.get("expected_status", "answer")
    record["status_correct"] = answer.status == expected_status
    if not record["status_correct"]:
        fail("status", f"Expected {expected_status}; actual {answer.status}: {answer.answer[:240]}")
    successful = [t for t in answer.tools if t.result is not None]
    expected_tools = [e["tool"] for e in expected]
    record["routing_correct"] = (
        sorted(t.tool for t in successful) == sorted(expected_tools)
        if expected_status == "answer"
        else record["status_correct"]
    )
    record["analytical_calls"] = len(successful)
    if not record["routing_correct"]:
        fail("routing", f"Expected tools {expected_tools}; got {[t.tool for t in successful]}.")

    candidates = []
    sql_validity = []
    for index, tool in enumerate(successful):
        candidate: dict[str, Any] = {"tool_index": index, "tool": tool.tool, "result": tool.result}
        try:
            if tool.tool == "sql_query":
                actual = QueryResult.model_validate(tool.result)
                query = execute(settings.database, actual.sql, max_rows=5000, profile=True)
                sql_validity.append(True)
                candidate["result"] = query.model_dump(mode="json")
                if actual.truncated or query.truncated:
                    candidate["error"] = "Truncated query results cannot pass evaluation."
                elif actual.columns != query.columns:
                    candidate["error"] = "Tool columns differ from independently re-executed SQL."
                else:
                    candidate["error"] = compare_rows(query.rows, actual.rows, ordered=True)
            elif tool.tool == "exposure_calculator":
                candidate["result"] = ExposureResult.model_validate(tool.result).model_dump()
        except (PortiqError, ValueError, KeyError, TypeError) as exc:
            candidate["error"] = f"Evidence execution/validation failed: {exc}"
            if tool.tool == "sql_query":
                sql_validity.append(False)
        candidates.append(candidate)
    record["sql_valid"] = all(sql_validity) if sql_validity else None
    comparisons = [[_compare_evidence(ref, c) for c in candidates] for ref in expected]
    matches = [[i for i, error in enumerate(row) if error is None] for row in comparisons]

    def assign(index: int, used: set[int]) -> list[int] | None:
        if index == len(matches):
            return []
        for candidate in matches[index]:
            if candidate not in used:
                rest = assign(index + 1, used | {candidate})
                if rest is not None:
                    return [candidate, *rest]
        return None

    assignment = assign(0, set())
    record["reference_checks"] = [
        {
            "reference_index": i,
            "matched_tool_index": assignment[i] if assignment else None,
            "candidates": [
                {"tool_index": j, "matched": error is None, "error": error}
                for j, error in enumerate(row)
            ],
        }
        for i, row in enumerate(comparisons)
    ]
    if expected_status == "answer":
        record["result_correct"] = assignment is not None
        if assignment is not None:
            matched_candidates = [candidates[assignment[i]] for i in range(len(expected))]
            record["projection_exact"] = all(
                c.get("projection_exact", True)
                for c in matched_candidates
                if c.get("tool") == "sql_query"
            )
            record["data_correct"] = all(
                c.get("data_correct", True)
                for c in matched_candidates
                if c.get("tool") == "sql_query"
            )
        else:
            record["projection_exact"] = False
            record["data_correct"] = any(
                c.get("data_correct") is True
                for c in candidates
                if c.get("tool") == "sql_query"
            )
        if assignment is None:
            details = [
                f"Reference {i}: "
                + ("; ".join(str(e) for e in row if e) if row else "No successful tool evidence.")
                for i, row in enumerate(comparisons)
                if not matches[i]
            ]
            fail(
                "result",
                " | ".join(details) or "References require distinct matching tool results.",
            )
    with (settings.source / "data/portfolios.csv").open(encoding="utf-8-sig", newline="") as handle:
        names = [row["portfolio_name"] for row in csv.DictReader(handle)]
    with (settings.source / "data/sectors.csv").open(encoding="utf-8-sig", newline="") as handle:
        sectors = [row["sector_name"] for row in csv.DictReader(handle)]
    record["faithfulness"] = faithfulness = check_faithfulness(
        answer.answer,
        expected,
        (narrative_rules or []) if answer.status == "answer" else [],
        names,
        sectors,
    )
    faithfulness["configured_rules"] = narrative_rules or []
    if answer.status != "answer":
        faithfulness["reason"] = (
            "No factual answer was produced; narrative assertions not applicable."
        )
    record["answer_verification"] = verification = verify_answer(
        answer.answer, expected if answer.status == "answer" else [], names, sectors
    )
    prose_failures = faithfulness["failures"] + verification["failures"]
    record["narrative_status"] = (
        "failed"
        if prose_failures
        else "passed"
        if "passed" in {verification["status"], faithfulness["status"]}
        else "not_checked"
    )
    if prose_failures:
        fail("faithfulness", "; ".join(prose_failures))
    record["answer_correct"] = (
        record["status_correct"]
        and record["result_correct"] is not False
        and faithfulness["status"] != "failed"
        and verification["status"] != "failed"
    )
    record["passed"] = record["answer_correct"] and record["routing_correct"]
    record["sql_efficiency"] = []
    if assignment is not None:
        for index, reference in enumerate(expected):
            if reference["tool"] != "sql_query":
                continue
            baseline = execute(settings.database, reference["sql"], max_rows=5000, profile=True)
            generated = candidates[assignment[index]]["result"]
            reference_steps = baseline.vm_steps or 0
            actual_steps = generated["vm_steps"] or 0
            measurement = {
                "reference_vm_steps": reference_steps,
                "generated_vm_steps": actual_steps,
                "reference_query_plan": baseline.query_plan,
                "generated_query_plan": generated["query_plan"],
                "score": round(100 * min(1, reference_steps / max(actual_steps, 1)), 2)
                if record["passed"]
                else 0.0,
                "metric": "SQLite VM progress callbacks at interval 1; lower work is preferred",
                "logical_page_reads": None,
            }
            if profile_io:
                from portiq.profiling import page_profile

                reference_io = page_profile(settings.database, reference["sql"])
                actual_io = page_profile(settings.database, generated["sql"])
                for profile, expected_rows in (
                    (reference_io, reference["rows"]),
                    (actual_io, generated["rows"]),
                ):
                    error = compare_rows(expected_rows, profile.pop("rows"), ordered=False)
                    if error:
                        raise PortiqError(
                            "Page profiler result disagrees with validated SQL: " + error
                        )
                measurement.update(
                    vm_score=measurement["score"],
                    reference_page_io=reference_io,
                    generated_page_io=actual_io,
                    logical_page_reads=actual_io["logical_page_reads"],
                    score=round(
                        100
                        * min(
                            1,
                            reference_io["logical_page_reads"]
                            / max(actual_io["logical_page_reads"], 1),
                        ),
                        2,
                    )
                    if record["passed"]
                    else 0.0,
                    metric="Correctness-gated relative SQLite logical page accesses",
                )
            record["sql_efficiency"].append(measurement)
    record["efficiency_score"] = (
        statistics.mean(item["score"] for item in record["sql_efficiency"])
        if record["sql_efficiency"]
        else 0.0
        if any(e["tool"] == "sql_query" for e in expected)
        else None
    )
    if record["failures"]:
        record["failure"] = " | ".join(
            f"{f['dimension']}: {f['message']}" for f in record["failures"]
        )
    return record


def evaluate_case(
    agent: AnswerAgent,
    case: dict[str, Any],
    *,
    narrative_rules: list[str] | None = None,
    profile_io: bool = False,
) -> dict[str, Any]:
    start = time.perf_counter()
    answer = None
    try:
        answer = agent.answer(case["question"])
        record = score_answer(
            agent.settings,
            case,
            answer,
            narrative_rules=narrative_rules,
            profile_io=profile_io,
        )
    except (PortiqError, ValueError, KeyError, TypeError) as exc:
        record = _record(case)
        if answer is not None:
            record["actual"] = answer.model_dump(mode="json")
        record["failure"] = f"Evaluation failed: {type(exc).__name__}: {exc}"
        record["failures"] = [{"dimension": "execution", "message": str(exc)}]
    record["duration_ms"] = round((time.perf_counter() - start) * 1000, 3)
    return record


def evaluate(
    agent: AnswerAgent,
    suite: Path,
    output: Path,
    *,
    trials: int = 1,
    split: str | None = None,
    limit: int | None = None,
    profile_io: bool = False,
) -> dict[str, Any]:
    cases = json.loads(suite.read_text(encoding="utf-8"))["questions"]
    if split:
        cases = [c for c in cases if c.get("split") == split]
    if limit:
        cases = cases[:limit]
    rules_path = agent.settings.source / "evaluation/faithfulness.json"
    rules = json.loads(rules_path.read_text(encoding="utf-8")) if rules_path.is_file() else {}
    suite_rules = rules.get(suite.name, {})
    records = []
    output.parent.mkdir(parents=True, exist_ok=True)
    for trial in range(1, trials + 1):
        for case in cases:
            record = evaluate_case(
                agent,
                case,
                narrative_rules=suite_rules.get(str(case["id"]), []),
                profile_io=profile_io,
            )
            record["trial"] = trial
            records.append(record)
            output.with_suffix(".progress.json").write_text(
                json.dumps({"complete": False, "records": records}, indent=2) + "\n",
                encoding="utf-8",
            )
            print(
                f"trial={trial} id={case['id']} {'PASS' if record['passed'] else 'FAIL'} "
                f"{record.get('failure', '')}",
                flush=True,
            )
    durations = sorted(r["duration_ms"] for r in records)
    report = {
        "evaluator_version": 4,
        "sql_performance_metric": "logical_page_reads" if profile_io else "vm_steps",
        "execution_strategy": "orchestrated",
        "fallback_models": list(agent.settings.fallback_models),
        "generation_mode": (
            "Live Gemini; local routing and answer caching disabled"
            if isinstance(getattr(agent, "backend", None), (GeminiBackend, FallbackBackend))
            else "Injected backend; not a live Gemini evaluation"
        ),
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "suite": suite.name,
        "model": agent.settings.model,
        "request_interval_seconds": agent.settings.request_interval,
        "sql_attempts": agent.settings.sql_attempts,
        "max_tool_calls": agent.settings.max_tool_calls,
        "source_sha256": {
            str(path.relative_to(agent.settings.source)): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in sorted(agent.settings.source.glob("data/*.csv"))
        },
        "suite_sha256": hashlib.sha256(suite.read_bytes()).hexdigest(),
        "narrative_rules_sha256": (
            hashlib.sha256(rules_path.read_bytes()).hexdigest() if rules_path.is_file() else None
        ),
        "runtime_sha256": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(Path(__file__).parent.glob("*.py"))
        },
        "cache": "disabled",
        "trials": trials,
        "split": split or "all",
        "total": len(records),
        "passed": sum(r["passed"] for r in records),
        "answer_correct": sum(r["answer_correct"] for r in records),
        "result_correct": sum(r["result_correct"] is True for r in records),
        "result_checked": sum(r["result_correct"] is not None for r in records),
        "projection_exact": sum(r.get("projection_exact") is True for r in records),
        "routing_correct": sum(r["routing_correct"] for r in records),
        "narrative_checked": sum(
            r.get("answer_verification", {}).get("status") in {"passed", "failed"}
            or r.get("faithfulness", {}).get("status") in {"passed", "failed"}
            for r in records
        ),
        "narrative_failed": sum(
            r.get("answer_verification", {}).get("status") == "failed"
            or r.get("faithfulness", {}).get("status") == "failed"
            for r in records
        ),
        "sql_efficiency_mean": statistics.mean(
            r["efficiency_score"] for r in records if r.get("efficiency_score") is not None
        )
        if any(r.get("efficiency_score") is not None for r in records)
        else None,
        "sql_efficiency_scope": (
            "Correctness-gated relative pager hits + misses; same APSW engine/fresh private "
            "cache for both queries; no physical device I/O claim."
            if profile_io
            else "Correctness-gated work score relative to reference; SQLite VM callbacks, not "
            "logical disk/page I/O. Scores do not change answer correctness."
        ),
        "mean_ms": statistics.mean(durations) if durations else None,
        "p95_ms": durations[max(0, math.ceil(len(durations) * 0.95) - 1)] if durations else None,
        "api_calls": sum(r.get("actual", {}).get("api_calls", 0) for r in records),
        "tokens": sum(r.get("actual", {}).get("tokens", 0) for r in records),
        "records": records,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    output.with_suffix(".progress.json").unlink(missing_ok=True)
    output.with_suffix(".md").write_text(
        f"# Evaluation: {suite.name}\n\n{report['passed']}/{report['total']} passed. "
        f"Answer correctness: {report['answer_correct']}/{report['total']}. "
        f"Routing: {report['routing_correct']}/{report['total']}. "
        f"Deterministic answer checks: {report['narrative_checked']} cases, "
        f"{report['narrative_failed']} failures. Unchecked prose is not certified. "
        f"Model: `{report['model']}`. Cache disabled. Trials: {trials}.\n\n"
        "| Trial | ID | Strict pass | Answer | Routing | Narrative | Failure |\n"
        "|---|---|---|---|---|---|---|\n"
        + "\n".join(
            f"| {r['trial']} | {r['id']} | {r['passed']} | "
            f"{r['answer_correct']} | {r['routing_correct']} | "
            f"{r['narrative_status']} | "
            f"{str(r.get('failure', '')).replace('|', '/')} |"
            for r in records
        )
        + "\n",
        encoding="utf-8",
    )
    return report
