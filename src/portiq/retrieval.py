"""Local lexical retrieval over live schema metadata; no benchmark or answer corpus."""

import math
import re
from collections import Counter
from pathlib import Path

from pydantic import BaseModel

from portiq.database import connect_readonly, quote_identifier

DESCRIPTIONS = {
    "portfolios": "fund names status strategy risk level assets under management AUM",
    "holdings": "portfolio positions equity stock bond quantity cost basis current weight exposure",
    "securities": "stock bond symbol company current price currency classification",
    "sectors": "sector industry classification technology healthcare financials",
    "transactions": "trade buy sell transaction date quantity execution price fees",
    "historical_prices": "historical security prices closing date volume latest snapshot",
    "portfolio_performance": "portfolio historical returns performance benchmark date",
    "risk_metrics": "portfolio volatility sharpe ratio risk drawdown beta date",
    "benchmarks": "benchmark reference index comparison",
}


def tokens(text: str) -> list[str]:
    return [word.rstrip("s") for word in re.findall(r"[a-z0-9]+", text.lower())]


class MetadataHit(BaseModel):
    source: str
    text: str
    score: float


class MetadataIndex:
    """BM25-ranked table documents with actual foreign-key paths for join grounding."""

    def __init__(self, database: Path) -> None:
        self.documents: dict[str, str] = {}
        with connect_readonly(database) as conn:
            for (table,) in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ):
                columns = ", ".join(
                    f"{row[1]} {row[2]}"
                    for row in conn.execute(f"PRAGMA table_info({quote_identifier(table)})")
                )
                links = "; ".join(
                    f"{table}.{row[3]} -> {row[2]}.{row[4]}"
                    for row in conn.execute(f"PRAGMA foreign_key_list({quote_identifier(table)})")
                )
                self.documents[table] = (
                    f"{table}: {DESCRIPTIONS.get(table, '')}. Columns: {columns}. "
                    f"Foreign keys: {links or 'none'}."
                )
        self.counts = {name: Counter(tokens(text)) for name, text in self.documents.items()}

    def retrieve(self, question: str, *, limit: int = 3) -> list[MetadataHit]:
        if not 1 <= limit <= 9:
            raise ValueError("Metadata retrieval limit must be between 1 and 9.")
        terms = set(tokens(question))
        count = len(self.counts)
        average = sum(sum(c.values()) for c in self.counts.values()) / max(count, 1)
        hits = []
        for table, frequencies in self.counts.items():
            score = 0.0
            length = sum(frequencies.values())
            for term in terms:
                frequency = frequencies[term]
                if frequency:
                    matches = sum(term in c for c in self.counts.values())
                    inverse = math.log(1 + (count - matches + 0.5) / (matches + 0.5))
                    score += (
                        inverse
                        * frequency
                        * 2.2
                        / (frequency + 1.2 * (0.25 + 0.75 * length / average))
                    )
            if score > 0:
                hits.append(
                    MetadataHit(
                        source=f"sqlite-schema:{table}",
                        text=self.documents[table],
                        score=round(score, 6),
                    )
                )
        return sorted(hits, key=lambda hit: (-hit.score, hit.source))[:limit]
