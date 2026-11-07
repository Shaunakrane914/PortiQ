"""Counterbalanced paired live experiment using the original independent scorer."""

import argparse
import hashlib
import json
import math
import statistics
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from portiq.agent import PortfolioAgent
from portiq.config import Settings
from portiq.evaluation import score_answer
from portiq.model import GeminiBackend
from portiq.planning import OneCallAgent
from portiq.quota import attempt_summary


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stats(values: list[float]) -> dict[str, float | None]:
    values = sorted(values)
    return {
        "mean": statistics.mean(values) if values else None,
        "median": statistics.median(values) if values else None,
        "p95": values[max(0, math.ceil(len(values) * 0.95) - 1)] if values else None,
    }


def report(
    records: list[dict[str, Any]], *, suite: str, strategy: str, metadata: dict[str, Any]
) -> dict[str, Any]:
    attempts = [a for r in records for a in r["actual"]["provider_metrics"]]
    return {
        **metadata,
        "suite": suite,
        "strategy": strategy,
        "cache": "disabled; local fast path disabled",
        "trials": 1,
        "total": len(records),
        "passed": sum(r["passed"] for r in records),
        "answer_correct": sum(r["answer_correct"] for r in records),
        "result_correct": sum(r["result_correct"] is True for r in records),
        "routing_correct": sum(r["routing_correct"] for r in records),
        "narrative_checked": sum(
            r["faithfulness"]["status"] in {"passed", "failed"} for r in records
        ),
        "narrative_failed": sum(r["faithfulness"]["status"] == "failed" for r in records),
        "api_calls": sum(r["actual"]["api_calls"] for r in records),
        "tokens": sum(r["actual"]["tokens"] for r in records),
        "mean_ms": statistics.mean([r["analysis_e2e_ms"] for r in records]) if records else None,
        "p95_ms": stats([r["analysis_e2e_ms"] for r in records])["p95"],
        "latency_ms": {
            k: stats([r[k] for r in records])
            for k in [
                "analysis_e2e_ms",
                "service_ms",
                "pacing_ms",
                "backoff_ms",
                "sql_validation_ms",
                "sql_execution_ms",
                "financial_ms",
            ]
        },
        "provider_attempt_summary": attempt_summary(attempts),
        "provider_failed_attempts": sum(a["error_kind"] is not None for a in attempts),
        "repair_questions": sum(
            any(t["result"] and t["result"].get("attempts", 1) > 1 for t in r["actual"]["tools"])
            for r in records
        ),
        "invalid_sql_attempts": sum(
            bool(t["error"]) and t["tool"] == "sql_query"
            for r in records
            for t in r["actual"]["tools"]
        ),
        "fallback_questions": sum("fallback" in r["actual"]["strategy"] for r in records),
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fresh paired experiment; never uses cache/local routing"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports/local/paired-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")),
    )
    parser.add_argument(
        "--sets",
        nargs="+",
        choices=["supplied", "extended", "platform"],
        default=["supplied", "extended", "platform"],
    )
    parser.add_argument("--limit", type=int)
    parser.add_argument("--request-budget", type=int, default=250)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    settings = Settings.from_env().model_copy(
        update={
            "request_interval": 6.5,
            "daily_requests": args.request_budget,
            "fallback_models": (),
        }
    )
    backend = GeminiBackend(settings)
    agents = {
        "existing": PortfolioAgent(settings, backend),
        "one-call": OneCallAgent(settings, backend),
    }
    paths = {
        "supplied": Path("ground_truth_dataset.json"),
        "extended": Path("evaluation/extended.json"),
        "platform": Path("evaluation/platform.json"),
    }
    rules = json.loads(Path("evaluation/faithfulness.json").read_text(encoding="utf-8"))
    platform_rules = json.loads(
        Path("evaluation/platform_faithfulness.json").read_text(encoding="utf-8")
    )
    source_hashes = {str(p): digest(p) for p in sorted(Path("data").glob("*.csv"))}
    runtime_hashes = {p.name: digest(p) for p in sorted(Path("src/portiq").glob("*.py"))}
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    metadata = {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "runtime_revision": revision,
        "model": settings.model,
        "prompt_sha256": digest(Path("src/portiq/prompts.py")),
        "source_sha256": source_hashes,
        "runtime_sha256": runtime_hashes,
        "request_interval_seconds": 6.5,
        "request_budget": args.request_budget,
        "evaluator_version": 2,
        "conditions": "Alternating strategy order per paired question; one shared paced backend. "
        "CLI steady-state analysis latency excludes oracle execution. SDK service time includes "
        "transport; it is not isolated model inference time. No controlled speedup claim across "
        "historical releases.",
    }
    all_records = []
    try:
        for name in args.sets:
            path = paths[name]
            cases = json.loads(path.read_text(encoding="utf-8"))["questions"]
            if args.limit:
                cases = cases[: args.limit]
            for case in cases:
                ordering = (
                    ["existing", "one-call"]
                    if len(all_records) // 2 % 2 == 0
                    else ["one-call", "existing"]
                )
                for strategy in ordering:
                    started = time.perf_counter()
                    answer = agents[strategy].answer(case["question"])
                    end_to_end = (time.perf_counter() - started) * 1000
                    contract = platform_rules if name == "platform" else rules.get(path.name, {})
                    row = score_answer(
                        settings, case, answer, narrative_rules=contract.get(str(case["id"]), [])
                    )
                    traces = answer.tools
                    row.update(
                        suite_name=name,
                        strategy=strategy,
                        trial=1,
                        analysis_e2e_ms=end_to_end,
                        service_ms=sum(a["service_ms"] for a in answer.provider_metrics),
                        pacing_ms=sum(a["pacing_ms"] for a in answer.provider_metrics),
                        backoff_ms=answer.backoff_ms,
                        sql_validation_ms=sum(
                            t.result.get("validation_ms", 0)
                            for t in traces
                            if t.result and t.tool == "sql_query"
                        ),
                        sql_execution_ms=sum(
                            t.result["duration_ms"]
                            for t in traces
                            if t.result and t.tool == "sql_query"
                        ),
                        financial_ms=sum(
                            t.duration_ms for t in traces if t.tool == "exposure_calculator"
                        ),
                    )
                    all_records.append(row)
                    (args.output_dir / "progress.json").write_text(
                        json.dumps(
                            {**metadata, "complete": False, "records": all_records}, indent=2
                        )
                        + "\n",
                        encoding="utf-8",
                    )
                    print(
                        f"{name} {case['id']} {strategy} {'PASS' if row['passed'] else 'FAIL'} "
                        f"calls={answer.api_calls} {row.get('failure', '')}",
                        flush=True,
                    )
                    if answer.error_kind in {
                        "daily_quota",
                        "local_budget",
                        "authentication",
                        "unsupported_model",
                        "suppressed",
                    }:
                        print(
                            "Stopped on exhausted quota/budget; partial evidence retained. "
                            "A later run must use a new directory.",
                            flush=True,
                        )
                        return 2
        assert runtime_hashes == {
            p.name: digest(p) for p in sorted(Path("src/portiq").glob("*.py"))
        }, "Runtime changed during experiment."
        for name in args.sets:
            for strategy in agents:
                rows = [
                    r for r in all_records if r["suite_name"] == name and r["strategy"] == strategy
                ]
                result = report(
                    rows,
                    suite=name,
                    strategy=strategy,
                    metadata={**metadata, "suite_sha256": digest(paths[name]), "complete": True},
                )
                (args.output_dir / f"{name}-{strategy}.json").write_text(
                    json.dumps(result, indent=2) + "\n", encoding="utf-8"
                )
        (args.output_dir / "progress.json").rename(args.output_dir / "paired-records.json")
        return int(any(not r["passed"] for r in all_records))
    finally:
        backend.close()


if __name__ == "__main__":
    raise SystemExit(main())
