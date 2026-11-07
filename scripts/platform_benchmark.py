"""Offline latency experiment with independent CSV references; no provider calls."""

import csv
import hashlib
import json
import statistics
import subprocess
import time
from collections import defaultdict
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from portiq.config import Settings
from portiq.service import AnalysisService


def main() -> None:
    def rows(name: str) -> list[dict[str, str]]:
        with Path("data", name + ".csv").open(encoding="utf-8", newline="") as handle:
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
    service = AnalysisService(Settings())
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
            "median_ms": statistics.median(values),
            "p95_ms": values[75],
            "mean_ms": statistics.mean(values),
        }
    output = Path("reports/v0.2.0/local-cache.json")
    if output.exists():
        raise RuntimeError("Refusing to overwrite existing evidence.")
    output.write_text(
        json.dumps(
            {
                "timestamp_utc": datetime.now(UTC).isoformat(),
                "revision": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], text=True
                ).strip(),
                "mode": "Local calculation and exact cache; no model or mocked backend",
                "conditions": "20 paired repeats of four explicit capabilities; warm filesystem; "
                "cache cleared before each pair; references from supplied CSVs; "
                "Python service timings, not browser/network latency",
                "source_sha256": {
                    str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in sorted(Path("data").glob("*.csv"))
                },
                "summaries": summaries,
                "records": records,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
