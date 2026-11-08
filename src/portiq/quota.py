"""Atomic request budget, adaptive sliding-window limiter, and sanitized error classification."""

import json
import math
import re
import sqlite3
import threading
import time
import weakref
from collections import deque
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

import httpx

from portiq.errors import ModelError


class AdaptiveRateLimiter:
    """Sliding-window quota controller tracking actual Gemini SDK attempts.

    Maintains a rolling window of request timestamps over `window_seconds` (default 60s).
    Enforces an application safety cap (default 12 RPM under the 15 RPM provider limit).
    - Default artificial delay is 0s: requests execute immediately while under the safety cap.
    - As usage approaches the quota (>= cooldown_threshold), introduces a temporary gentle
      cooldown (1.5s) before starting a new question (never between tool calls in a question).
    - When the application safety cap is reached:
        - Calculates the exact recovery time until the oldest attempt exits the rolling window.
        - If recovery time <= max_wait_seconds, permits waiting for the slot to free.
        - If recovery time > max_wait_seconds, immediately raises ModelError with retry_after
          to return a clean retry/cooldown error message without freezing the web worker or UI.
    - Automatically recovers to 0s artificial delay as past attempts expire past 60s.
    """

    def __init__(
        self,
        rpm_limit: int = 12,
        window_seconds: float = 60.0,
        max_wait_seconds: float = 10.0,
        cooldown_threshold: int = 8,
        cooldown_seconds: float = 1.5,
        clock: Any = None,
    ) -> None:
        self.rpm_limit = rpm_limit
        self.window_seconds = window_seconds
        self.max_wait_seconds = max_wait_seconds
        self.cooldown_threshold = cooldown_threshold
        self.cooldown_seconds = cooldown_seconds
        self.clock = clock or time.monotonic
        self.lock = threading.RLock()
        self.timestamps: deque[float] = deque()

    def _evict_expired(self, now: float) -> None:
        cutoff = now - self.window_seconds
        while self.timestamps and self.timestamps[0] <= cutoff:
            self.timestamps.popleft()

    def prepare_question(self, now: float | None = None) -> float:
        """Called before starting a new question.

        Returns required cooldown delay (0.0 if sufficient quota headroom remains).
        Raises ModelError if quota is saturated and recovery wait exceeds max_wait_seconds.
        """
        with self.lock:
            current = self.clock() if now is None else now
            self._evict_expired(current)
            if len(self.timestamps) >= self.rpm_limit:
                recovery = self.window_seconds - (current - self.timestamps[0])
                if recovery > self.max_wait_seconds:
                    wait_s = math.ceil(recovery)
                    raise ModelError(
                        f"Gemini rate limit capacity full; retry after {wait_s} seconds.",
                        kind="rate_limit",
                        retryable=True,
                        retry_after=math.ceil(recovery),
                    )
                return max(0.0, recovery)
            if len(self.timestamps) >= self.cooldown_threshold:
                return self.cooldown_seconds
            return 0.0

    def acquire(
        self,
        request_interval: float = 0.0,
        last_request: float = 0.0,
        now: float | None = None,
    ) -> float:
        """Called before an SDK call. Computes required delay and records the attempt.

        Returns delay in seconds (0.0 for immediate processing).
        Raises ModelError if capacity is saturated and wait exceeds max_wait_seconds.
        """
        with self.lock:
            current = self.clock() if now is None else now
            self._evict_expired(current)

            interval_delay = 0.0
            if request_interval > 0 and last_request > 0:
                elapsed = current - last_request
                if elapsed < request_interval:
                    interval_delay = request_interval - elapsed

            window_delay = 0.0
            if len(self.timestamps) >= self.rpm_limit:
                recovery = self.window_seconds - (current - self.timestamps[0])
                if recovery > self.max_wait_seconds:
                    wait_s = math.ceil(recovery)
                    raise ModelError(
                        f"Gemini rate limit capacity full; retry after {wait_s} seconds.",
                        kind="rate_limit",
                        retryable=True,
                        retry_after=math.ceil(recovery),
                    )
                window_delay = max(0.0, recovery)

            delay = max(interval_delay, window_delay)
            self.timestamps.append(current + delay)
            return delay

    def current_usage(self, now: float | None = None) -> int:
        with self.lock:
            current = self.clock() if now is None else now
            self._evict_expired(current)
            return len(self.timestamps)

    def clear(self) -> None:
        with self.lock:
            self.timestamps.clear()


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
