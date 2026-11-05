"""Atomic schema-aware CSV ingestion and constrained read-only SQLite access."""

import csv
import hashlib
import math
import os
import sqlite3
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Any

from portiq.errors import DataError


def quote_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


@contextmanager
def connect_readonly(path: Path) -> Iterator[sqlite3.Connection]:
    if not path.is_file():
        raise DataError("Database unavailable. Run portfolio-agent init-db first.")
    try:
        conn = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=1)
        conn.execute("PRAGMA query_only=ON")
        conn.enable_load_extension(False)
    except sqlite3.Error as exc:
        raise DataError("Cannot open the database read-only.") from exc
    try:
        yield conn
    finally:
        conn.close()


def _convert(value: str, kind: str, column: str) -> str | int | float | None:
    if value == "":
        return None
    if kind == "INTEGER":
        return int(value)
    if kind == "REAL":
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("non-finite numeric value")
        return number
    if kind == "DATE":
        date.fromisoformat(value)
    return value


def initialize(source: Path, destination: Path, *, rebuild: bool = False) -> dict[str, Any]:
    """Build in a sibling temporary file; replace only after full validation succeeds."""
    if destination.exists() and not rebuild:
        raise DataError("Database already exists. Use --rebuild to replace it atomically.")
    schema = source / "database_schema.sql"
    if not schema.is_file():
        raise DataError("Missing input: database_schema.sql")
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix="portiq-", suffix=".db", dir=destination.parent)
    os.close(descriptor)
    temp = Path(temporary)
    conn = sqlite3.connect(temp)
    counts: dict[str, int] = {}
    hashes = {"database_schema.sql": hashlib.sha256(schema.read_bytes()).hexdigest()}
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.executescript(schema.read_text(encoding="utf-8"))
        tables = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        ]
        with conn:
            for table in tables:
                file = source / "data" / f"{table}.csv"
                if not file.is_file():
                    raise DataError(f"Missing input: data/{table}.csv")
                hashes[f"data/{file.name}"] = hashlib.sha256(file.read_bytes()).hexdigest()
                columns = list(conn.execute(f"PRAGMA table_info({quote_identifier(table)})"))
                names = [r[1] for r in columns]
                with file.open(encoding="utf-8-sig", newline="") as handle:
                    reader = csv.DictReader(handle)
                    if reader.fieldnames != names:
                        raise DataError(f"Column mismatch in {file.name}; expected {names}.")
                    count = 0
                    for line, row in enumerate(reader, start=2):
                        if None in row or any(v is None for v in row.values()):
                            raise DataError(f"Malformed CSV in {file.name}, line {line}.")
                        try:
                            values = [_convert(row[c[1]], c[2], c[1]) for c in columns]
                            conn.execute(
                                f"INSERT INTO {quote_identifier(table)} VALUES "
                                f"({','.join('?' for _ in values)})",
                                values,
                            )
                        except (ValueError, sqlite3.Error) as exc:
                            raise DataError(
                                f"Invalid record in {file.name}, line {line}: {exc}"
                            ) from exc
                        count += 1
                    counts[table] = count
            if list(conn.execute("PRAGMA foreign_key_check")):
                raise DataError("Foreign-key validation failed.")
            if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise DataError("SQLite integrity check failed.")
            invalid = conn.execute(
                "SELECT COUNT(*) FROM holdings WHERE current_weight IS NULL "
                "OR current_weight < 0 OR current_weight > 1 OR quantity < 0"
            ).fetchone()[0]
            missing = conn.execute(
                "SELECT COUNT(*) FROM securities WHERE asset_type='Stock' AND sector_id IS NULL"
            ).fetchone()[0]
            if invalid or missing:
                raise DataError("Invalid holding weights/quantities or stock sector mappings.")
        conn.close()
        os.replace(temp, destination)
    except (OSError, sqlite3.Error) as exc:
        raise DataError(f"Database initialization failed: {type(exc).__name__}.") from exc
    finally:
        conn.close()
        temp.unlink(missing_ok=True)
    return {"rows": counts, "source_sha256": hashes, "foreign_keys": "ok", "integrity": "ok"}


def schema_context(path: Path) -> str:
    """Read schema from the database, never from evaluation answers."""
    with connect_readonly(path) as conn:
        return "\n".join(
            r[0]
            for r in conn.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        )
