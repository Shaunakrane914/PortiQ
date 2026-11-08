"""Atomic request budget and sanitized provider error classification. No prompts are stored."""

import json
import re
import sqlite3
import threading
import weakref
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

import httpx


class RequestBudget:
    """SQLite transactions serialize workers sharing this file; memory mode is instance-local."""

    def __init__(self, limit: int = 200, path: Path | None = None) -> None:
        self.limit = limit
        self.lock = threading.RLock()
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path) if path else ":memory:", check_same_thread=False)
        self.finalize = weakref.finalize(self, self.conn.close)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS usage(day TEXT PRIMARY KEY, attempts INTEGER NOT NULL)"
        )
        self.conn.commit()

    def reserve(self) -> bool:
        day = datetime.now(UTC).date().isoformat()
        with self.lock:
            self.conn.execute("BEGIN IMMEDIATE")
            try:
                self.conn.execute("INSERT OR IGNORE INTO usage VALUES(?,0)", (day,))
                count = self.conn.execute(
                    "SELECT attempts FROM usage WHERE day=?", (day,)
                ).fetchone()[0]
                if count >= self.limit:
                    self.conn.rollback()
                    return False
                self.conn.execute("UPDATE usage SET attempts=attempts+1 WHERE day=?", (day,))
                self.conn.commit()
                return True
            except BaseException:
                self.conn.rollback()
                raise

    def used(self) -> int:
        with self.lock:
            row = self.conn.execute(
                "SELECT attempts FROM usage WHERE day=?", (datetime.now(UTC).date().isoformat(),)
            ).fetchone()
            return int(row[0]) if row else 0

    def close(self) -> None:
        self.finalize()


def classify(exc: Exception) -> tuple[str, bool, float | None]:
    code = getattr(exc, "code", None)
    details = getattr(exc, "details", {})
    # Inspect only in memory; never expose provider text, URLs or arbitrary details.
    encoded = json.dumps(details, default=lambda _: "").casefold()
    delay = None
    match = re.search(r'"retrydelay"\s*:\s*"(\d+(?:\.\d+)?)s"', encoded)
    if match:
        delay = float(match[1])
    response = getattr(exc, "response", None)
    if response is not None:
        header = response.headers.get("Retry-After", "")
        if header.replace(".", "", 1).isdigit():
            delay = float(header)
        elif header:
            try:
                retry_at = parsedate_to_datetime(header)
                if retry_at.tzinfo:
                    delay = max(0.0, (retry_at - datetime.now(UTC)).total_seconds())
            except (TypeError, ValueError, OverflowError):
                pass
    if code == 429:
        if any(term in encoded for term in ("perday", "per_day", "daily")):
            return "daily_quota", False, delay
        return "rate_limit", delay is None or delay <= 60, delay
    if code in {401, 403}:
        return "authentication", False, None
    if code == 404:
        return "unsupported_model", False, None
    if code in {408, 500, 502, 503, 504}:
        return "provider_transient", delay is None or delay <= 60, delay
    if isinstance(exc, httpx.TimeoutException):
        return "timeout", True, None
    if isinstance(exc, httpx.TransportError):
        return "connection", True, None
    return "invalid_response" if isinstance(exc, ValueError) else "provider_error", False, None
