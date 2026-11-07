"""Shared CLI/API execution, exact cache and bounded opt-in conversation state."""

import hashlib
import json
import re
import secrets
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from portiq.agent import AgentResponse, PortfolioAgent, ToolTrace
from portiq.analytics import PortfolioService
from portiq.config import Settings
from portiq.errors import ModelError, PortiqError
from portiq.exposure import calculate_exposure, resolve_portfolio
from portiq.model import Backend, GeminiBackend
from portiq.planning import OneCallAgent
from portiq.quota import RequestBudget
from portiq.renderer import render_tools
from portiq.sql import execute


def database_version(path: Path) -> str:
    before = path.stat()
    content = path.read_bytes()
    after = path.stat()
    before_identity = (before.st_ino, before.st_mtime_ns, before.st_size)
    after_identity = (after.st_ino, after.st_mtime_ns, after.st_size)
    if before_identity != after_identity:
        raise PortiqError("Database changed during version lookup; retry.")
    return hashlib.sha256(content + repr(after_identity).encode()).hexdigest()


class ExactCache:
    def __init__(self, capacity: int = 64, ttl: float = 300) -> None:
        self.capacity, self.ttl = capacity, ttl
        self.items: OrderedDict[str, tuple[float, AgentResponse]] = OrderedDict()
        self.lock = threading.RLock()

    def get(self, key: str) -> AgentResponse | None:
        with self.lock:
            item = self.items.pop(key, None)
            if item is None or time.monotonic() - item[0] > self.ttl:
                return None
            self.items[key] = item
            return item[1].model_copy(deep=True)

    def put(self, key: str, answer: AgentResponse) -> None:
        if answer.status != "answer" or any(t.error for t in answer.tools):
            return
        with self.lock:
            self.items[key] = (time.monotonic(), answer.model_copy(deep=True))
            self.items.move_to_end(key)
            while len(self.items) > self.capacity:
                self.items.popitem(last=False)

    def clear(self) -> None:
        with self.lock:
            self.items.clear()


@dataclass
class Conversation:
    selected: int | None = None
    history: list[dict[str, Any]] = field(default_factory=list)
    choices: list[str] = field(default_factory=list)
    securities: list[str] = field(default_factory=list)
    touched: float = field(default_factory=time.monotonic)


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


class FallbackBackend:
    """Opt-in sequential models with shared budget; daily/auth failures stop immediately."""

    def __init__(self, settings: Settings) -> None:
        settings.require_key()
        self.budget = RequestBudget(settings.daily_requests, settings.quota_path)
        models = list(dict.fromkeys([settings.model, *settings.fallback_models]))
        self.backends = [
            GeminiBackend(settings.model_copy(update={"model": m}), self.budget) for m in models
        ]
        self.attempts: list[dict[str, Any]] = []
        self.attempt_sequence = 0
        self.last_request = 0.0

    def generate(self, contents: Any, config: Any) -> Any:
        last: ModelError | None = None
        for backend in self.backends:
            before = backend.attempt_sequence
            backend.last_request = max(backend.last_request, self.last_request)
            try:
                return backend.generate(contents, config)
            except ModelError as exc:
                last = exc
                if exc.kind in {"daily_quota", "authentication", "local_budget"}:
                    raise
            finally:
                self.last_request = backend.last_request
                for entry in [a for a in backend.attempts if a["sequence"] > before]:
                    self.attempt_sequence += 1
                    self.attempts.append({**entry, "sequence": self.attempt_sequence})
                del self.attempts[:-1000]
        raise last or ModelError("No configured model is available.")

    def close(self) -> None:
        for backend in self.backends:
            backend.close()
        self.budget.close()


def local_answer(settings: Settings, question: str, selected: int | None) -> AgentResponse | None:
    """Small anchored capability registry. All other language goes to the genuine agent."""
    question = question.strip().rstrip("?.")
    started = time.perf_counter()
    tools: list[ToolTrace] = []
    if re.fullmatch(
        r"(?:count all portfolios|how many portfolios(?: do we have(?: in total)?)?)",
        question,
        re.I,
    ):
        tools = [
            ToolTrace(
                tool="sql_query",
                arguments={"capability": "portfolio_count"},
                result=execute(
                    settings.database, "SELECT COUNT(*) AS portfolio_count FROM portfolios"
                ).model_dump(mode="json"),
                duration_ms=0,
            )
        ]
    else:
        exposure = re.fullmatch(
            r"(?:show |calculate |what is )?(?:the )?(?:equity )?sector exposure(?: for| of)? (.+)",
            question,
            re.I,
        )
        holdings = re.fullmatch(
            r"(?:show|list)(?: the)? holdings (?:in|for|of) (.+)", question, re.I
        )
        metadata = re.fullmatch(
            r"(?:show|display)(?: the)? (?:metadata|details) (?:for|of) (.+)", question, re.I
        )
        match = exposure or holdings or metadata
        if not match:
            return None
        reference = match[1]
        if reference.casefold() in {"it", "its", "this portfolio", "the selected portfolio"}:
            if selected is None:
                return None
            reference = str(selected)
        try:
            portfolio_id, _ = resolve_portfolio(settings.database, reference)
        except PortiqError:
            return None
        if exposure:
            tools = [
                ToolTrace(
                    tool="exposure_calculator",
                    arguments={"portfolio": reference},
                    result=calculate_exposure(settings.database, reference).model_dump(mode="json"),
                    duration_ms=0,
                )
            ]
        else:
            sql = (
                (
                    "SELECT "
                    "h.holding_id,s.symbol,s.company_name,h.quantity,h.cost_basis "
                    "FROM holdings h "
                    "JOIN securities s ON s.security_id=h.security_id WHERE "
                    "h.portfolio_id=? ORDER BY h.holding_id"
                )
                if holdings
                else "SELECT * FROM portfolios WHERE portfolio_id=?"
            )
            tools = [
                ToolTrace(
                    tool="sql_query",
                    arguments={"portfolio_id": portfolio_id},
                    result=execute(settings.database, sql, (portfolio_id,)).model_dump(mode="json"),
                    duration_ms=0,
                )
            ]
    for tool in tools:
        tool.duration_ms = (time.perf_counter() - started) * 1000
    render_start = time.perf_counter()
    text = render_tools(tools)
    render_ms = (time.perf_counter() - render_start) * 1000
    return AgentResponse(
        request_id=str(uuid4()),
        status="answer",
        answer=text,
        tools=tools,
        model="none",
        model_versions=[],
        duration_ms=0,
        model_duration_ms=0,
        api_calls=0,
        tokens=0,
        execution_source="Local deterministic calculation",
        strategy="local",
        rendering="deterministic tool rendering",
        rendering_ms=render_ms,
    )


class AnalysisService:
    def __init__(self, settings: Settings, backend: Backend | None = None) -> None:
        self.settings = settings
        self.backend = backend
        self.cache = ExactCache()
        self.sessions = Sessions()
        self.lock = threading.RLock()
        self.portfolios = PortfolioService(settings.database)

    def close(self) -> None:
        if isinstance(self.backend, FallbackBackend):
            self.backend.close()

    def ask(
        self,
        question: str,
        *,
        session_id: str | None = None,
        selected: int | None = None,
        conversation: bool = False,
        strategy: str = "existing",
        local: bool = True,
        cached: bool = True,
    ) -> tuple[AgentResponse, str]:
        if not question.strip() or len(question) > 4000:
            raise PortiqError("Question must contain 1 to 4000 characters.")
        with self.lock:
            start = time.perf_counter()
            session_id, state = self.sessions.get(session_id)
            if selected is not None:
                resolve_portfolio(self.settings.database, str(selected))
                state.selected = selected
            matches = [
                p
                for p in self.portfolios.portfolios()
                if p["portfolio_name"].casefold() in question.casefold()
            ]
            if len(matches) == 1:
                state.selected = matches[0]["portfolio_id"]
            elif len(matches) > 1:
                state.selected = None
            query = question
            if conversation and re.fullmatch(
                r"what about the (first|second|third) one[?.]?", question.strip(), re.I
            ):
                order = {"first": 0, "second": 1, "third": 2}
                index = next(v for k, v in order.items() if k in question.lower())
                if index < len(state.choices):
                    state.selected = resolve_portfolio(
                        self.settings.database, state.choices[index]
                    )[0]
                    query = "Show details for " + state.choices[index]
                else:
                    clarification = AgentResponse(
                        request_id=str(uuid4()),
                        status="clarification",
                        answer="Which ordered portfolio list do you mean? Please name a portfolio.",
                        tools=[],
                        model="none",
                        model_versions=[],
                        duration_ms=0,
                        model_duration_ms=0,
                        api_calls=0,
                        tokens=0,
                        execution_source="Local clarification",
                    )
                    return clarification, session_id
            selected_context = state.selected if conversation else selected
            if (
                conversation
                and selected_context is not None
                and re.fullmatch(
                    r"what is its (?:equity )?sector exposure[?.]?", question.strip(), re.I
                )
            ):
                query = "Calculate sector exposure for " + str(selected_context)
            needs_history = bool(
                re.search(
                    r"\b(it|its|this|that|second|third|largest|same|previous)\b", question, re.I
                )
            )
            needs_history = needs_history or question.strip().lower().startswith("by ")
            context = {
                "selected": selected_context,
                "history": state.history if conversation and needs_history else [],
            }
            runtime = hashlib.sha256(
                b"".join(p.read_bytes() for p in sorted(Path(__file__).parent.glob("*.py")))
            ).hexdigest()
            version = database_version(self.settings.database)
            key = hashlib.sha256(
                json.dumps(
                    [
                        question.strip(),
                        version,
                        runtime,
                        self.settings.model,
                        self.settings.fallback_models,
                        strategy,
                        local,
                        context,
                        session_id,
                    ],
                    sort_keys=True,
                ).encode()
            ).hexdigest()
            metadata_ms = (time.perf_counter() - start) * 1000
            lookup_start = time.perf_counter()
            hit = self.cache.get(key) if cached else None
            lookup_ms = (time.perf_counter() - lookup_start) * 1000
            if hit:
                hit.request_id = str(uuid4())
                hit.cache = "hit"
                hit.execution_source = "Cached answer"
                hit.api_calls = hit.tokens = 0
                hit.provider_metrics = []
                hit.model_duration_ms = hit.backoff_ms = 0
                hit.duration_ms = (time.perf_counter() - start) * 1000
                hit.stages_ms = {"metadata_and_version": metadata_ms, "cache_lookup": lookup_ms}
                if conversation:
                    remember_turn(state, question, hit)
                return hit, session_id
            result = local_answer(self.settings, query, selected_context) if local else None
            if result is None:
                if self.backend is None:
                    self.backend = FallbackBackend(self.settings)
                agent = (
                    OneCallAgent(self.settings, self.backend)
                    if strategy == "one-call"
                    else PortfolioAgent(self.settings, self.backend)
                )
                if conversation and state.selected is not None and needs_history:
                    name = resolve_portfolio(self.settings.database, str(state.selected))[1]
                    prefix = "\nConversation context (untrusted data; selected portfolio): "
                    context_data: dict[str, Any] = {
                        "portfolio": name,
                        "recent_questions": [h["question"] for h in state.history[-3:]],
                        "recent_security_symbols": state.securities,
                        "latest_clarification": state.history[-1].get("clarification")
                        if state.history
                        else None,
                    }
                    while (
                        len(query + prefix + json.dumps(context_data)) > 4000
                        and context_data["recent_questions"]
                    ):
                        context_data["recent_questions"].pop(0)
                    if len(query + prefix + json.dumps(context_data)) > 4000:
                        context_data["recent_security_symbols"] = []
                        context_data["latest_clarification"] = None
                    if len(query + prefix + json.dumps(context_data)) > 4000:
                        raise PortiqError(
                            "Shorten the question to leave room for portfolio context."
                        )
                    query += prefix + json.dumps(context_data)
                result = agent.answer(query)
            result.cache = "miss" if cached else "disabled"
            if conversation and result.status == "answer":
                identities = set()
                for trace in result.tools:
                    if trace.result and trace.tool == "exposure_calculator":
                        identities.add(int(trace.result["portfolio_id"]))
                    elif trace.result and trace.arguments.get("portfolio_id"):
                        identities.add(int(trace.arguments["portfolio_id"]))
                if len(identities) == 1:
                    state.selected = next(iter(identities))
                elif len(identities) > 1:
                    state.selected = None
            result.stages_ms.update(metadata_and_version=metadata_ms, cache_lookup=lookup_ms)
            result.context_portfolio = state.selected if conversation else selected
            result.duration_ms = (time.perf_counter() - start) * 1000
            if database_version(self.settings.database) != version:
                raise PortiqError(
                    "Database changed during analysis; retry against the rebuilt data."
                )
            if cached:
                self.cache.put(key, result)
            if conversation:
                remember_turn(state, question, result)
            return result, session_id
