"""Optional evaluation-only SQLite pager measurements; never imported by the agent."""

import time
from pathlib import Path
from typing import Any

from portiq.errors import QueryError
from portiq.sql import SAFE_FUNCTIONS, validate_sql


def page_profile(path: Path, sql: str) -> dict[str, Any]:
    """Count pager hits + misses on a fresh private cache, including query preparation.

    This is SQLite logical page access, not physical device I/O. APSW can use a different
    SQLite build from Python's sqlite3, so both comparison arms use this same engine and
    independently verify their result rows before any I/O score is awarded.
    """
    try:
        import apsw
    except ImportError as exc:
        raise QueryError("Page profiling requires installation with --extra performance.") from exc
    validate_sql(sql)
    conn = apsw.Connection(
        str(path.resolve()),
        flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_PRIVATECACHE,
        statementcachesize=0,
    )
    try:
        tables = {
            row[0]
            for row in conn.execute(
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
            if action == apsw.SQLITE_SELECT:
                return apsw.SQLITE_OK
            if (
                action == apsw.SQLITE_READ
                and arg1 in tables
                and ((database or "").casefold() == "main" or (database is None and arg2 == ""))
            ):
                return apsw.SQLITE_OK
            if action == apsw.SQLITE_FUNCTION and (arg2 or "").lower() in SAFE_FUNCTIONS:
                return apsw.SQLITE_OK
            return apsw.SQLITE_DENY

        conn.set_authorizer(authorize)
        conn.limit(apsw.SQLITE_LIMIT_LENGTH, 1_000_000)
        conn.limit(apsw.SQLITE_LIMIT_SQL_LENGTH, 20000)
        conn.limit(apsw.SQLITE_LIMIT_EXPR_DEPTH, 100)
        start = time.perf_counter()
        conn.set_progress_handler(lambda: time.perf_counter() - start > 2, 1000)
        before_hits = conn.status(apsw.SQLITE_DBSTATUS_CACHE_HIT)[0]
        before_misses = conn.status(apsw.SQLITE_DBSTATUS_CACHE_MISS)[0]
        rows: list[list[Any]] = []
        size = 0
        for row in conn.execute(sql):
            size += sum(len(str(value).encode()) for value in row)
            if len(rows) >= 5000 or size > 1_000_000:
                raise QueryError("Page profile exceeded complete-result limits.")
            rows.append(list(row))
        hits = conn.status(apsw.SQLITE_DBSTATUS_CACHE_HIT)[0] - before_hits
        misses = conn.status(apsw.SQLITE_DBSTATUS_CACHE_MISS)[0] - before_misses
        return {
            "rows": rows,
            "cache_hits": hits,
            "cache_misses": misses,
            "logical_page_reads": hits + misses,
            "sqlite_version": apsw.sqlitelibversion(),
            "apsw_version": apsw.apswversion(),
            "cache_policy": "fresh private connection; schema preloaded; prepare + execute counted",
            "metric": "SQLite pager cache hits + misses; not physical storage reads",
        }
    except apsw.Error as exc:
        raise QueryError("SQLite page profile could not complete safely.") from exc
    finally:
        conn.close()
