"""Parse, authorize, bound, and execute one read-only analytical query."""

import sqlite3
import time
from pathlib import Path
from typing import Any

import sqlglot
from pydantic import BaseModel, ConfigDict, Field
from sqlglot import exp
from sqlglot.errors import ParseError

from portiq.database import connect_readonly
from portiq.errors import QueryError

SAFE_FUNCTIONS = frozenset(
    [
        "abs",
        "avg",
        "cast",
        "ceil",
        "ceiling",
        "coalesce",
        "concat",
        "count",
        "date",
        "datetime",
        "floor",
        "format",
        "glob",
        "group_concat",
        "ifnull",
        "iif",
        "instr",
        "julianday",
        "lag",
        "lead",
        "length",
        "like",
        "lower",
        "ltrim",
        "max",
        "min",
        "nullif",
        "pow",
        "power",
        "printf",
        "rank",
        "dense_rank",
        "replace",
        "round",
        "row_number",
        "rtrim",
        "sign",
        "strftime",
        "substr",
        "substring",
        "sum",
        "total",
        "trim",
        "typeof",
        "unixepoch",
        "upper",
    ]
)


class QueryResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    columns: list[str]
    rows: list[list[Any]]
    sql: str
    duration_ms: float
    truncated: bool = False
    attempts: int = 1


class SQLPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sql: str = Field(
        min_length=1,
        max_length=20000,
        description=(
            "One read-only SQLite query. For aggregate comparisons without a requested order, "
            "include ORDER BY the last requested numeric metric DESC. Use an inner join for "
            "sector-specific value aggregates unless zero-sector portfolios are explicitly requested."
        ),
    )
    explanation: str = Field(max_length=1000)


def requires_dedicated_planning(sql: str) -> bool:
    """Give structurally complex analytics a focused planner context before execution."""
    try:
        tree = sqlglot.parse_one(sql, read="sqlite")
    except (ParseError, RecursionError):
        return False  # The ordinary validation/repair loop handles malformed drafts.
    return (
        sum(1 for _ in tree.find_all(exp.Join)) >= 5 or sum(1 for _ in tree.find_all(exp.CTE)) >= 2
    )


def validate_sql(sql: str) -> None:
    if not sql.strip() or len(sql) > 20000:
        raise QueryError("SQL must contain one query of at most 20000 characters.")
    try:
        statements = sqlglot.parse(sql, read="sqlite")
    except (ParseError, RecursionError) as exc:
        raise QueryError("SQL could not be parsed as SQLite.") from exc
    if len(statements) != 1 or not isinstance(statements[0], exp.Query):
        raise QueryError("Only one read-only SELECT query is allowed.")
    tree = statements[0]
    for node in tree.walk():
        if isinstance(node, (exp.DDL, exp.DML, exp.Command, exp.Into)):
            raise QueryError("SQL modification and administrative commands are forbidden.")
        if isinstance(node, exp.With) and node.args.get("recursive"):
            raise QueryError("Recursive queries are forbidden.")
        if isinstance(node, exp.Table) and (
            node.catalog or node.db or node.name.lower().startswith(("sqlite_", "pragma_"))
        ):
            raise QueryError("Only application tables in the main database may be queried.")


def execute(
    path: Path,
    sql: str,
    parameters: tuple[Any, ...] = (),
    *,
    max_rows: int = 1000,
    seconds: float = 2.0,
) -> QueryResult:
    validate_sql(sql)
    start = time.perf_counter()
    with connect_readonly(path) as conn:
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        }

        def authorize(
            action: int,
            arg1: str | None,
            arg2: str | None,
            database: str | None,
            trigger: str | None,
        ) -> int:
            if action == sqlite3.SQLITE_SELECT:
                return sqlite3.SQLITE_OK
            if (
                action == sqlite3.SQLITE_READ
                and arg1 in tables
                and (database == "main" or (database is None and arg2 == ""))
            ):
                return sqlite3.SQLITE_OK
            if action == sqlite3.SQLITE_FUNCTION and (arg2 or "").lower() in SAFE_FUNCTIONS:
                return sqlite3.SQLITE_OK
            return sqlite3.SQLITE_DENY

        conn.set_authorizer(authorize)
        conn.set_progress_handler(lambda: int(time.perf_counter() - start > seconds), 1000)
        conn.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, 1_000_000)
        conn.setlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH, 20000)
        conn.setlimit(sqlite3.SQLITE_LIMIT_EXPR_DEPTH, 100)
        conn.setlimit(sqlite3.SQLITE_LIMIT_COMPOUND_SELECT, 20)
        try:
            cursor = conn.execute(sql, parameters)
            columns = [c[0] for c in cursor.description or []]
            rows = []
            result_bytes = 0
            for _ in range(max_rows + 1):
                row = cursor.fetchone()
                if row is None:
                    break
                result_bytes += sum(len(str(value).encode("utf-8")) for value in row)
                if result_bytes > 1_000_000:
                    raise QueryError("Query result exceeds 1 MB; narrow the request.")
                rows.append(list(row))
            if any(isinstance(value, bytes) for row in rows for value in row):
                raise QueryError("Binary query results are not supported.")
        except sqlite3.Error as exc:
            # SQLite messages contain identifiers but not credentials or filesystem paths.
            raise QueryError(f"Query rejected or failed: {str(exc)[:240]}") from exc
    return QueryResult(
        columns=columns,
        rows=rows[:max_rows],
        sql=sql,
        truncated=len(rows) > max_rows,
        duration_ms=round((time.perf_counter() - start) * 1000, 3),
    )
