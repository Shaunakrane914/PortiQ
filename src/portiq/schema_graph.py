"""Question-linked schema graph retrieval with FK paths and conservative full-schema fallback.

This is schema-graph RAG over structured metadata, not Microsoft's document/community pipeline.
No evaluation files, reference SQL, embeddings or extra model calls enter retrieval.
"""

import re
from collections import Counter, deque
from pathlib import Path

import sqlglot
from pydantic import BaseModel, Field

from portiq.database import connect_readonly, quote_identifier

ALIASES = {
    "portfolios": (
        "portfolio",
        "portfolios",
        "fund",
        "funds",
        "mandate",
        "aum",
        "assets under management",
        "target risk",
        "strategy",
        "active",
        "passive",
    ),
    "holdings": ("holding", "holdings", "position", "positions", "cost basis", "weight", "weights"),
    "securities": (
        "security",
        "securities",
        "stock",
        "stocks",
        "bond",
        "bonds",
        "ticker",
        "symbol",
        "company",
        "price",
        "prices",
        "currency",
        "currencies",
    ),
    "sectors": ("sector", "sectors", "industry"),
    "transactions": ("transaction", "transactions", "trade", "trades", "buy", "sell", "fees"),
    "historical_prices": (
        "historical price",
        "historical prices",
        "price history",
        "closing price",
        "close price",
        "volume",
        "adjusted close",
    ),
    "portfolio_performance": (
        "performance",
        "return",
        "returns",
        "nav",
        "sharpe",
        "volatility",
        "drawdown",
    ),
    "risk_metrics": (
        "risk metric",
        "value at risk",
        "conditional value",
        "var",
        "cvar",
        "sortino",
        "beta",
        "correlation",
        "tracking error",
        "information ratio",
    ),
    "benchmarks": ("benchmark", "benchmarks", "reference index"),
}
RULES = {
    "equity_exposure": (("exposure",), ("portfolios", "holdings", "securities", "sectors")),
    "holdings_projection": (
        ("holding", "holdings", "position", "positions", "cost basis"),
        ("holdings", "securities"),
    ),
    "quote_value": (
        ("market value", "portfolio value", "total value"),
        ("portfolios", "holdings", "securities"),
    ),
    "diversification": (
        ("diversification", "diversified"),
        ("portfolios", "holdings", "securities", "sectors"),
    ),
}


def normalized(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.casefold()))


def mentions(question: str, phrase: str) -> bool:
    return f" {normalized(phrase)} " in f" {question} "


class GraphContext(BaseModel):
    tables: list[str]
    ddl: str
    sources: list[str]
    seed_reasons: dict[str, list[str]] = Field(default_factory=dict)
    join_paths: list[list[str]] = Field(default_factory=list)
    fallback: bool = False
    reason: str | None = None


class SchemaGraph:
    def __init__(self, database: Path) -> None:
        self.ddl: dict[str, str] = {}
        self.nodes: dict[str, dict[str, str]] = {}
        self.edges: list[tuple[str, str, str]] = []
        self.adjacent: dict[str, set[str]] = {}
        self.columns: dict[str, list[str]] = {}
        self.values: dict[str, list[str]] = {}
        with connect_readonly(database) as conn:
            for name, ddl in conn.execute(
                "SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ):
                self.ddl[name] = sqlglot.parse_one(ddl, read="sqlite").sql(
                    dialect="sqlite", comments=False
                )
                self.nodes[f"table:{name}"] = {"kind": "table", "name": name}
                self.adjacent[name] = set()
                self.columns[name] = []
                for column in conn.execute(f"PRAGMA table_info({quote_identifier(name)})"):
                    self.columns[name].append(column[1])
                    key = f"column:{name}.{column[1]}"
                    self.nodes[key] = {"kind": "column", "name": column[1], "type": column[2]}
                    self.edges.append((f"table:{name}", key, "has_column"))
            for table in self.ddl:
                for fk in conn.execute(f"PRAGMA foreign_key_list({quote_identifier(table)})"):
                    if fk[2] in self.ddl:
                        self.adjacent[table].add(fk[2])
                        self.adjacent[fk[2]].add(table)
                        self.edges.append(
                            (f"column:{table}.{fk[3]}", f"column:{fk[2]}.{fk[4]}", "foreign_key")
                        )
            for table, column in (
                ("sectors", "sector_name"),
                ("securities", "symbol"),
                ("portfolios", "portfolio_name"),
            ):
                if column in self.columns.get(table, []):
                    self.values[table] = [
                        str(row[0])
                        for row in conn.execute(
                            f"SELECT DISTINCT {quote_identifier(column)} "
                            f"FROM {quote_identifier(table)} "
                            "LIMIT 200"
                        )
                        if row[0] and len(str(row[0])) <= 100
                    ]
        for rule, (_, tables) in RULES.items():
            self.nodes[f"rule:{rule}"] = {"kind": "metadata_rule", "name": rule}
            for table in tables:
                if table in self.ddl:
                    self.edges.append((f"rule:{rule}", f"table:{table}", "requires_metadata"))
        self.column_frequency = Counter(
            normalized(c) for cols in self.columns.values() for c in cols
        )

    def _path(self, start: str, targets: set[str]) -> list[str] | None:
        queue: deque[list[str]] = deque([[start]])
        seen = {start}
        while queue:
            path = queue.popleft()
            if path[-1] in targets:
                return path
            for neighbor in sorted(self.adjacent[path[-1]]):
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append([*path, neighbor])
        return None

    def retrieve(self, question: str) -> GraphContext:
        query = normalized(question)
        reasons: dict[str, list[str]] = {}
        rules = []

        def seed(table: str, reason: str) -> None:
            if table in self.ddl:
                reasons.setdefault(table, []).append(reason)

        for table in self.ddl:
            for alias in ALIASES.get(table, (table.replace("_", " "),)):
                if mentions(query, alias):
                    seed(table, "alias:" + alias)
            for column in self.columns[table]:
                term = normalized(column)
                if (
                    (" " in term or self.column_frequency[term] == 1)
                    and term not in {"id", "date", "price", "name", "value", "quantity"}
                    and mentions(query, term)
                ):
                    seed(table, f"column:{table}.{column}")
            for value in self.values.get(table, []):
                if mentions(query, value):
                    seed(table, "value:" + table)
        for rule, (terms, tables) in RULES.items():
            if any(mentions(query, term) for term in terms):
                rules.append("rule:" + rule)
                for table in tables:
                    seed(table, "rule:" + rule)
        selected: set[str] = set()
        paths = []
        failure = "No metadata seed matched; full-schema fallback." if not reasons else None
        # Connect strong semantic seeds first; intermediate tables preserve actual join paths.
        for table in sorted(reasons, key=lambda t: (-len(reasons[t]), t)):
            if not selected:
                selected.add(table)
            elif table not in selected:
                path = self._path(table, selected)
                if path is None:
                    failure = "Seeds are disconnected; full-schema fallback."
                    break
                selected.update(path)
                paths.append(path)
        if failure:
            selected = set(self.ddl)
        ordered = [table for table in self.ddl if table in selected]
        return GraphContext(
            tables=ordered,
            ddl="\n".join(self.ddl[t] for t in ordered),
            sources=[*(f"schema-graph:table:{t}" for t in ordered), *rules],
            seed_reasons=reasons,
            join_paths=paths,
            fallback=failure is not None,
            reason=failure,
        )
