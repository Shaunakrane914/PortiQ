"""Shared CLI/API execution, exact cache and bounded opt-in conversation state."""

import contextlib
import hashlib
import json
import re
import threading
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

from portiq.agent import PortfolioAgent
from portiq.analytics import PortfolioService
from portiq.answers import AgentResponse, ToolTrace, render_tools
from portiq.cache import ExactCache as ExactCache
from portiq.cache import database_version as database_version
from portiq.config import Settings
from portiq.errors import ModelError, PortiqError
from portiq.exposure import calculate_exposure, resolve_portfolio
from portiq.model import Backend
from portiq.model import FallbackBackend as FallbackBackend
from portiq.quota import AdaptiveRateLimiter, RequestBudget
from portiq.sessions import Conversation as Conversation
from portiq.sessions import Sessions as Sessions
from portiq.sessions import remember_turn as remember_turn
from portiq.sql import execute


def local_answer(settings: Settings, question: str, selected: int | None) -> AgentResponse | None:
    """Small anchored capability registry. All other language goes to the genuine agent."""
    question = question.strip().rstrip("?.")
    started = time.perf_counter()
    tools: list[ToolTrace] = []
    count_pattern = (
        r"(?:count all (?:portfolios|funds)|count (?:portfolios|funds)|"
        r"how many (?:portfolios|funds)(?: (?:do we have|are there|exist)(?: in total)?)?|"
        r"total (?:number of )?(?:portfolios|funds))"
    )
    if re.fullmatch(count_pattern, question, re.I):
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
        patterns = [
            (
                "exposure",
                (
                    r"(?:show |calculate |what is )?(?:the )?(?:equity[- ])?"
                    r"(?:sector )?(?:exposure|breakdown|allocation)(?: for| of)? (.+)"
                ),
            ),
            (
                "exposure",
                (
                    r"(?:show |calculate |what is )?(?:the )?"
                    r"(.+?)['’]s (?:equity[- ])?(?:sector )?(?:exposure|breakdown|allocation)"
                ),
            ),
            ("holdings", r"(?:show|list)(?: the)? holdings (?:in|for|of) (.+)"),
            ("holdings", r"(?:show |list )?(?:the )?(.+?)['’]s holdings"),
            ("metadata", r"(?:show|display)(?: the)? (?:metadata|details) (?:for|of) (.+)"),
            ("metadata", r"(?:show |display )?(?:the )?(.+?)['’]s (?:metadata|details)"),
        ]
        kind, reference = None, None
        for k, pat in patterns:
            if m := re.fullmatch(pat, question, re.I):
                kind, reference = k, m[1]
                break
        if not kind or not reference:
            return None
        if reference.casefold() in {"it", "its", "this portfolio", "the selected portfolio"}:
            if selected is None:
                return None
            reference = str(selected)
        try:
            portfolio_id, _ = resolve_portfolio(settings.database, reference)
        except PortiqError:
            return None
        if kind == "exposure":
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
                if kind == "holdings"
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
    text = render_tools(tools, question=question)
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
        self.budget = RequestBudget(settings.daily_requests, settings.quota_path)
        self.limiter = AdaptiveRateLimiter(
            rpm_limit=settings.rpm_limit,
            window_seconds=settings.rpm_window,
            max_wait_seconds=settings.max_wait_seconds,
            cooldown_threshold=settings.rpm_cooldown_threshold,
            cooldown_seconds=settings.rpm_cooldown_seconds,
        )
        self.backend_pool: list[FallbackBackend] = []
        self.available_backends: list[FallbackBackend] = []

    def close(self) -> None:
        if isinstance(self.backend, FallbackBackend):
            self.backend.close()
        for backend in self.backend_pool:
            backend.close()
        self.budget.close()

    def borrow_backend(self) -> Backend:
        if self.backend is not None:
            return self.backend
        with self.lock:
            if self.available_backends:
                return self.available_backends.pop()
            if len(self.backend_pool) >= self.settings.max_concurrent_analyses:
                raise ModelError("Analysis capacity is busy.", kind="busy", retry_after=1)
            backend = FallbackBackend(self.settings, budget=self.budget, limiter=self.limiter)
            self.backend_pool.append(backend)
            return backend

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
        smarter: bool = False,
    ) -> tuple[AgentResponse, str]:
        if not question.strip() or len(question) > 4000:
            raise PortiqError("Question must contain 1 to 4000 characters.")
        if strategy != "existing":
            raise PortiqError("Only the existing orchestration strategy is supported.")
        request_settings = self.settings
        if smarter:
            local = cached = False
            request_settings = self.settings.model_copy(
                update={"direct_results": False, "force_synthesis": True}
            )
        with self.lock:
            session_id, state = self.sessions.get(session_id)
        # Independent conversations execute concurrently; turns in one conversation serialize.
        with state.lock:
            start = time.perf_counter()
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
            selected_reference = re.compile(
                r"\b(?:the\s+)?(?:selected|current)\s+(?:portfolio|fund)\b", re.I
            )
            if conversation and selected_reference.search(query):
                if selected_context is None:
                    return AgentResponse(
                        request_id=str(uuid4()),
                        status="clarification",
                        answer="Which portfolio should I use? Please name or select one.",
                        tools=[],
                        model="none",
                        model_versions=[],
                        duration_ms=0,
                        model_duration_ms=0,
                        api_calls=0,
                        tokens=0,
                        execution_source="Local context clarification",
                    ), session_id
                # This is an explicit session selection, not a model-inferred identity.
                name = resolve_portfolio(self.settings.database, str(selected_context))[1]
                query = selected_reference.sub(lambda _: name, query)
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
                        request_settings.direct_results,
                        request_settings.force_synthesis,
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
                backend = self.borrow_backend()
                try:
                    result = PortfolioAgent(request_settings, backend).answer(query)
                finally:
                    if self.backend is None and isinstance(backend, FallbackBackend):
                        with self.lock:
                            self.available_backends.append(backend)
            result.cache = "miss" if cached else "disabled"
            if conversation and result.status == "answer":
                identities = set()
                for trace in result.tools:
                    if trace.result and trace.tool == "exposure_calculator":
                        pid = trace.result.get("portfolio_id")
                        if pid is not None:
                            with contextlib.suppress(ValueError, TypeError):
                                identities.add(int(pid))
                    elif trace.result and trace.arguments.get("portfolio_id"):
                        with contextlib.suppress(ValueError, TypeError):
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
