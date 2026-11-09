"""Bounded conversation storage and history; no model or cache ownership."""

import secrets
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any

from portiq.answers import AgentResponse
from portiq.errors import PortiqError


@dataclass
class Conversation:
    selected: int | None = None
    history: list[dict[str, Any]] = field(default_factory=list)
    choices: list[str] = field(default_factory=list)
    securities: list[str] = field(default_factory=list)
    touched: float = field(default_factory=time.monotonic)
    lock: Any = field(default_factory=threading.RLock, repr=False)


def remember_turn(state: Conversation, question: str, result: AgentResponse) -> None:
    state.history.append(
        {
            "question": question[:400],
            "status": result.status,
            "clarification": result.answer[:300] if result.status == "clarification" else None,
            "tools": [t.tool for t in result.tools],
            "result_summaries": [
                {
                    "tool": t.tool,
                    "rows": len(t.result.get("rows", [])),
                    "columns": t.result.get("columns", [])[:12],
                    "portfolio": t.result.get("portfolio_name"),
                }
                for t in result.tools
                if t.result
            ],
        }
    )
    state.history = state.history[-8:]
    if result.status != "answer":
        return
    state.choices = []
    state.securities = []
    for t in result.tools:
        if t.result and t.tool == "sql_query" and "symbol" in t.result["columns"]:
            col = t.result["columns"].index("symbol")
            state.securities.extend(str(row[col])[:30] for row in t.result["rows"][:10])
        if t.result and t.tool == "sql_query" and "portfolio_name" in t.result["columns"]:
            col = t.result["columns"].index("portfolio_name")
            state.choices.extend(str(row[col]) for row in t.result["rows"][:10])


class Sessions:
    def __init__(self, capacity: int = 100, ttl: float = 1800) -> None:
        self.capacity, self.ttl = capacity, ttl
        self.items: OrderedDict[str, Conversation] = OrderedDict()

    def get(self, key: str | None) -> tuple[str, Conversation]:
        now = time.monotonic()
        for old in [k for k, v in self.items.items() if now - v.touched > self.ttl]:
            del self.items[old]
        if key is None:
            key = secrets.token_urlsafe(32)
            self.items[key] = Conversation()
        if key not in self.items:
            raise PortiqError("Conversation expired or unavailable; start a new session.")
        state = self.items[key]
        state.touched = now
        self.items.move_to_end(key)
        while len(self.items) > self.capacity:
            self.items.popitem(last=False)
        return key, state
