"""Experimental one-call function planner; the original orchestrator remains the default."""

import time
from typing import Literal
from uuid import uuid4

from google.genai import types
from pydantic import BaseModel, ConfigDict, Field, model_validator

from portiq.agent import AgentResponse, PortfolioAgent, ToolTrace, user_content
from portiq.config import Settings
from portiq.errors import ModelError, PortfolioError, PortiqError
from portiq.exposure import calculate_exposure
from portiq.model import Backend, MeteredBackend
from portiq.renderer import render_tools
from portiq.sql import execute, validate_sql


class Step(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    tool: Literal["sql_query", "exposure_calculator"]
    sql: str | None = Field(default=None, max_length=20000)
    portfolio: str | None = Field(default=None, max_length=200)
    from_step: int | None = Field(default=None, ge=0, le=5)

    @model_validator(mode="after")
    def contract(self) -> "Step":
        if self.tool == "sql_query":
            if not self.sql or self.portfolio is not None or self.from_step is not None:
                raise ValueError("SQL steps require only sql.")
            validate_sql(self.sql)
        elif self.sql is not None or (self.portfolio is None) == (self.from_step is None):
            raise ValueError("Exposure requires either original portfolio reference or from_step.")
        return self


class Plan(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    status: Literal["answer", "clarification", "unsupported", "fallback"]
    message: str = Field(default="", max_length=2000)
    steps: list[Step] = Field(default_factory=list, max_length=6)

    @model_validator(mode="after")
    def contract(self) -> "Plan":
        if (self.status == "answer") != bool(self.steps):
            raise ValueError("Only answers require analytical steps.")
        for index, step in enumerate(self.steps):
            if step.from_step is not None and (
                step.from_step >= index or self.steps[step.from_step].tool != "sql_query"
            ):
                raise ValueError("Dependencies must reference an earlier SQL step.")
        return self


class OneCallAgent:
    def __init__(self, settings: Settings, backend: Backend, *, fallback: bool = True) -> None:
        self.settings = settings
        self.backend = backend
        self.original = PortfolioAgent(settings, backend)
        self.fallback = fallback

    def answer(self, question: str) -> AgentResponse:
        if not question.strip() or len(question) > 4000:
            raise PortiqError("Question must contain 1 to 4000 characters.")
        start = time.perf_counter()
        meter = MeteredBackend(self.backend)
        traces: list[ToolTrace] = []

        def response(
            status: Literal["answer", "clarification", "unsupported", "error"], text: str
        ) -> AgentResponse:
            return AgentResponse(
                request_id=str(uuid4()),
                status=status,
                answer=text,
                tools=traces,
                model=self.settings.model,
                model_versions=sorted(meter.versions),
                duration_ms=(time.perf_counter() - start) * 1000,
                model_duration_ms=meter.duration_ms,
                api_calls=len(meter.metrics) if hasattr(self.backend, "attempts") else meter.calls,
                tokens=meter.tokens,
                strategy="one-call",
                rendering="deterministic tool rendering",
                provider_metrics=meter.metrics,
                backoff_ms=meter.backoff_ms,
            )

        def recover(reason: str = "invalid_or_insufficient_plan") -> AgentResponse:
            if not self.fallback:
                return response(
                    "error", "One-call plan was unusable; original strategy is available."
                )
            result = self.original.answer(question)
            result.tools = traces + result.tools
            result.api_calls += meter.calls
            result.tokens += meter.tokens
            result.provider_metrics = meter.metrics
            if hasattr(self.backend, "attempts"):
                result.api_calls = len(meter.metrics)
            result.backoff_ms += meter.backoff_ms
            result.duration_ms = (time.perf_counter() - start) * 1000
            result.model_duration_ms += meter.duration_ms
            result.strategy = "one-call → existing fallback"
            result.planning_events.append(reason)
            return result

        try:
            generated = meter.generate(
                [user_content(question)],
                types.GenerateContentConfig(
                    system_instruction=self.original.system
                    + "\nReturn one complete execute_plan call. "
                    "Python executes and renders it; no final synthesis call is needed. "
                    "Use from_step only when exposure depends on a preceding SQL result that "
                    "returns exactly one portfolio name or ID. Preserve original references. "
                    "If discovery cannot be planned safely, choose fallback. "
                    "Never invent result values.",
                    temperature=0,
                    max_output_tokens=4096,
                    tools=[
                        types.Tool(
                            function_declarations=[
                                types.FunctionDeclaration(
                                    name="execute_plan",
                                    description="Submit a typed, ordered analytical tool plan.",
                                    parameters_json_schema=Plan.model_json_schema(),
                                )
                            ]
                        )
                    ],
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                    tool_config=types.ToolConfig(
                        function_calling_config=types.FunctionCallingConfig(
                            mode=types.FunctionCallingConfigMode.ANY
                        )
                    ),
                ),
            )
            calls = generated.function_calls or []
            if len(calls) != 1 or calls[0].name != "execute_plan":
                return recover()
            plan = Plan.model_validate(calls[0].args)
            if plan.status == "fallback":
                return recover("planner_requested_fallback")
            if plan.status != "answer":
                return response(
                    plan.status,
                    plan.message or "Please specify the portfolio or supported analysis.",
                )
            for step in plan.steps:
                tool_start = time.perf_counter()
                args = step.model_dump(exclude_none=True)
                try:
                    if step.tool == "sql_query":
                        result = execute(
                            self.settings.database,
                            step.sql or "",
                            max_rows=self.settings.max_rows,
                            seconds=self.settings.query_seconds,
                        ).model_dump(mode="json")
                    else:
                        reference = step.portfolio
                        if step.from_step is not None:
                            prior = traces[step.from_step].result
                            if (
                                not prior
                                or prior.get("truncated")
                                or len(prior["rows"]) != 1
                                or len(prior["rows"][0]) != 1
                            ):
                                raise PortfolioError(
                                    "Dependent portfolio selection is not one unambiguous value."
                                )
                            reference = str(prior["rows"][0][0])
                        result = calculate_exposure(
                            self.settings.database, reference or ""
                        ).model_dump(mode="json")
                    traces.append(
                        ToolTrace(
                            tool=step.tool,
                            arguments=args,
                            result=result,
                            duration_ms=(time.perf_counter() - tool_start) * 1000,
                        )
                    )
                except PortfolioError as exc:
                    traces.append(
                        ToolTrace(tool=step.tool, arguments=args, error=str(exc), duration_ms=0)
                    )
                    return response("clarification", str(exc))
                except PortiqError as exc:
                    traces.append(
                        ToolTrace(tool=step.tool, arguments=args, error=str(exc), duration_ms=0)
                    )
                    return recover()
            render_start = time.perf_counter()
            text = render_tools(traces)
            render_ms = (time.perf_counter() - render_start) * 1000
            finished = response("answer", text)
            finished.rendering_ms = render_ms
            return finished
        except ModelError as exc:
            failed = response("error", str(exc))
            failed.error_kind = exc.kind
            failed.error_retry_after = exc.retry_after
            return failed
        except (ValueError, TypeError, PortiqError):
            return recover()
