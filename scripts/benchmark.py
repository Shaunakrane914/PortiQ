"""Offline microbenchmark with raw samples; no invented before/after improvements."""

import argparse
import json
import statistics
import time
import tracemalloc
from datetime import UTC, datetime
from pathlib import Path

from portiq.exposure import calculate_exposure
from portiq.sql import execute


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline financial-tool microbenchmark")
    parser.add_argument("--output", type=Path, default=Path("reports/local/performance.json"))
    args = parser.parse_args()
    path = Path("portfolio_database.db")
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
    report = {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "iterations": 200,
        "cache": "disabled; OS filesystem cache uncontrolled",
        "peak_tracemalloc_bytes": peak,
        "summary": {
            name: {
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "p95": sorted(values)[189],
            }
            for name, values in measurements.items()
        },
        "samples": measurements,
    }
    output = args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
