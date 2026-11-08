"""Offline tool/cache benchmarks with raw samples and no Gemini requests."""

import argparse
import csv
import hashlib
import json
import math
import statistics
import subprocess
import time
import tracemalloc
from collections import defaultdict
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

from portiq.config import Settings
from portiq.exposure import calculate_exposure
from portiq.service import AnalysisService
from portiq.sql import execute


def stats(values: list[float]) -> dict[str, float]:
    return {
        "mean_ms": statistics.mean(values),
        "median_ms": statistics.median(values),
        "p95_ms": sorted(values)[math.ceil(len(values) * 0.95) - 1],
    }


def tool_report(settings: Settings) -> dict[str, Any]:
    path = settings.database
    measurements: dict[str, list[float]] = {"exposure_ms": [], "sql_ms": []}
    tracemalloc.start()
    for _ in range(200):
        start = time.perf_counter()
        result = calculate_exposure(path, "Balanced Portfolio")
        assert result.equity_weight == "0.36"
        measurements["exposure_ms"].append((time.perf_counter() - start) * 1000)
        start = time.perf_counter()
        query = execute(path, "SELECT COUNT(*) FROM portfolios")
        assert query.rows == [[13]]
        measurements["sql_ms"].append((time.perf_counter() - start) * 1000)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "iterations": 200,
        "cache": "disabled; OS filesystem cache uncontrolled",
        "peak_tracemalloc_bytes": peak,
        "summary": {name: stats(values) for name, values in measurements.items()},
        "samples": measurements,
    }


def cache_report(settings: Settings) -> dict[str, Any]:
    def rows(name: str) -> list[dict[str, str]]:
        with (settings.source / "data" / (name + ".csv")).open(
            encoding="utf-8", newline=""
        ) as handle:
            return list(csv.DictReader(handle))

    portfolios, holdings, securities = rows("portfolios"), rows("holdings"), rows("securities")
    security = {s["security_id"]: s for s in securities}
    sectors = {s["sector_id"]: s["sector_name"] for s in rows("sectors")}
    balanced = next(p for p in portfolios if p["portfolio_name"] == "Balanced Portfolio")
    positions = [h for h in holdings if h["portfolio_id"] == balanced["portfolio_id"]]
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for h in positions:
        s = security[h["security_id"]]
        if s["asset_type"] == "Stock":
            totals[sectors[s["sector_id"]]] += Decimal(h["current_weight"])
    equity = sum(totals.values())
    expected_sectors = {
        sector: str((weight / equity * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        for sector, weight in totals.items()
    }
    expected_holdings = [
        [
            int(h["holding_id"]),
            security[h["security_id"]]["symbol"],
            security[h["security_id"]]["company_name"],
            float(h["quantity"]),
            float(h["cost_basis"]),
        ]
        for h in sorted(positions, key=lambda h: int(h["holding_id"]))
    ]
    questions = [
        "Count all portfolios",
        "Calculate sector exposure for Balanced Portfolio",
        "Show holdings for Balanced Portfolio",
        "Show metadata for Balanced Portfolio",
    ]
    service = AnalysisService(settings)
    records = []
    sid = None
    for trial in range(20):
        for index, question in enumerate(questions):
            service.cache.clear()
            for mode in ("local_uncached", "exact_cache_hit"):
                started = time.perf_counter()
                response, sid = service.ask(question, session_id=sid, local=True, cached=True)
                wall = (time.perf_counter() - started) * 1000
                result = response.tools[0].result
                assert result is not None
                if index == 0:
                    assert result["rows"] == [[len(portfolios)]]
                elif index == 1:
                    assert result["sectors"] == expected_sectors
                elif index == 2:
                    assert result["rows"] == expected_holdings
                else:
                    assert result["rows"][0][1] == balanced["portfolio_name"]
                    assert result["rows"][0][4] == float(balanced["total_aum"])
                assert response.api_calls == response.tokens == 0
                assert response.cache == ("hit" if mode == "exact_cache_hit" else "miss")
                records.append(
                    {
                        "trial": trial + 1,
                        "question": question,
                        "mode": mode,
                        "passed": True,
                        "wall_ms": wall,
                        "source": response.execution_source,
                        "api_calls": 0,
                        "tokens": 0,
                        "stages_ms": response.stages_ms,
                    }
                )
    summaries = {}
    for mode in ("local_uncached", "exact_cache_hit"):
        values = sorted(r["wall_ms"] for r in records if r["mode"] == mode)
        summaries[mode] = {
            "passed": len(values),
            "total": len(values),
            **stats(values),
        }
    service.close()
    return {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "mode": "Local calculation and exact cache; no model or mocked backend",
        "conditions": "20 paired repeats of four capabilities; warm filesystem; cache cleared "
        "before each pair; CSV references; Python service time, not HTTP latency",
        "source_sha256": {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((settings.source / "data").glob("*.csv"))
        },
        "summaries": summaries,
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["tools", "cache"], default="tools")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--db", type=Path, default=Path("portfolio_database.db"))
    parser.add_argument("--source", type=Path, default=Path("."))
    args = parser.parse_args()
    output = args.output or Path("reports/local") / (args.mode + "-benchmark.json")
    if output.exists():
        parser.error("Output already exists; choose a new --output path.")
    # Construct key-free settings: benchmarks must never spend provider quota.
    settings = Settings(database=args.db, source=args.source)
    result = cache_report(settings) if args.mode == "cache" else tool_report(settings)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result.get("summaries", result.get("summary")), indent=2))


if __name__ == "__main__":
    main()
