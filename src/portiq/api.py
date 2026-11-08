"""Thin single-worker FastAPI demo; all analytics and agent execution use shared services."""

import hmac
import math
import os
import threading
import time
from collections import OrderedDict, deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from portiq import __version__
from portiq.agent import AgentResponse
from portiq.analytics import Reconciliation, Snapshot
from portiq.config import Settings
from portiq.database import connect_readonly, initialize
from portiq.errors import DataError, ModelError, PortfolioError, PortiqError, QueryError
from portiq.exposure import ExposureResult, calculate_exposure
from portiq.service import AnalysisService


class BodyLimit:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] != "POST":
            await self.app(scope, receive, send)
            return
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > 16384:
                await JSONResponse({"detail": "Request exceeds 16 KiB."}, 413)(scope, receive, send)
                return
            if not message.get("more_body", False):
                break
        sent = False

        async def bounded_receive() -> Any:
            nonlocal sent
            if not sent:
                sent = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, bounded_receive, send)


class Ask(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    question: str = Field(min_length=1, max_length=4000)
    selected_portfolio: int | None = Field(default=None, gt=0)
    session_id: str | None = Field(default=None, min_length=30, max_length=100)
    strategy: Literal["existing"] = "existing"
    local: bool = True
    cache: bool = True


class AskResult(BaseModel):
    response: AgentResponse
    session_id: str


class TablePage(BaseModel):
    records: list[dict[str, Any]]
    total: int
    limit: int
    offset: int


def create_app(
    settings: Settings | None = None,
    service: AnalysisService | None = None,
    *,
    token: str | None = None,
    rate_limit: int | None = None,
) -> FastAPI:
    settings = settings or Settings.from_env()
    rate_limit = rate_limit if rate_limit is not None else int(os.getenv("PORTIQ_RATE_LIMIT", "60"))
    if not 1 <= rate_limit <= 10000:
        raise ValueError("API rate limit must be 1–10000.")
    analysis = service or AnalysisService(settings)
    demo_token = token if token is not None else os.getenv("PORTIQ_DEMO_TOKEN", "")
    origins = [o.strip() for o in os.getenv("PORTIQ_CORS_ORIGINS", "").split(",") if o.strip()]
    if "*" in origins:
        raise ValueError("Explicit CORS origins are required.")
    clients: OrderedDict[str, deque[float]] = OrderedDict()
    rate_lock = threading.Lock()
    model_slot = threading.BoundedSemaphore(1)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> Any:
        yield
        analysis.close()

    app = FastAPI(
        title="PortiQ",
        version=__version__,
        lifespan=lifespan,
        openapi_url=None,
        docs_url=None,
        redoc_url=None,
    )
    app.state.analysis = analysis
    app.add_middleware(BodyLimit)
    extra_hosts = [h.strip() for h in os.getenv("PORTIQ_ALLOWED_HOSTS", "").split(",") if h.strip()]
    if "*" in extra_hosts or (not extra_hosts and os.getenv("PORTIQ_ALLOW_ANONYMOUS") == "1"):
        allowed_hosts = ["*"]
    else:
        allowed_hosts = ["localhost", "127.0.0.1", "testserver", *extra_hosts]
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=allowed_hosts,
    )
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_methods=["GET", "POST"],
            allow_headers=["Authorization", "Content-Type"],
        )

    @app.middleware("http")
    async def security(request: Request, call_next: Any) -> Any:
        request_id = str(uuid4())
        request.state.request_id = request_id
        response = None
        if request.url.path.startswith("/api/") and request.url.path != "/api/health":
            authorization = request.headers.get("authorization", "")
            if demo_token and not hmac.compare_digest(authorization, "Bearer " + demo_token):
                response = JSONResponse({"detail": "Demo access token required."}, 401)
            origin = request.headers.get("origin")
            own_origin = str(request.base_url).rstrip("/")
            is_same_origin = False
            if origin:
                if origin == own_origin or origin in origins:
                    is_same_origin = True
                else:
                    parsed_origin = urlparse(origin)
                    parsed_base = urlparse(own_origin)
                    host_header = request.headers.get("host", "").split(":")[0]
                    origin_hostname = parsed_origin.hostname or ""
                    # Behind TLS-terminating proxies (e.g. Render/Cloudflare),
                    # compare hostname with base URL or Host header.
                    if origin_hostname and (
                        origin_hostname == parsed_base.hostname or origin_hostname == host_header
                    ):
                        is_same_origin = True
            if request.method == "POST" and origin and not is_same_origin:
                response = JSONResponse({"detail": "Origin not allowed."}, 403)
            if request.method == "POST" and not request.headers.get("content-type", "").startswith(
                "application/json"
            ):
                response = JSONResponse({"detail": "Use application/json."}, 415)
            ip = request.client.host if request.client else "unknown"
            with rate_lock:
                now = time.monotonic()
                queue = clients.setdefault(ip, deque())
                while queue and now - queue[0] > 60:
                    queue.popleft()
                if len(queue) >= rate_limit:
                    response = JSONResponse(
                        {"detail": "Local API rate limit reached."},
                        429,
                        headers={"Retry-After": "60"},
                    )
                else:
                    queue.append(now)
                clients.move_to_end(ip)
                while len(clients) > 1024:
                    clients.popitem(last=False)
        if response is None:
            response = await call_next(request)
        response.headers.update(
            {
                "X-Request-ID": request_id,
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "no-referrer",
                "Cache-Control": "no-store",
                "Content-Security-Policy": "default-src 'self'; script-src 'self'; "
                "style-src 'self'; img-src"
                " 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-"
                "uri 'none'; form-action 'self'",
            }
        )
        return response

    @app.exception_handler(PortiqError)
    async def expected_error(request: Request, exc: PortiqError) -> JSONResponse:
        status = (
            404 if isinstance(exc, PortfolioError) else 503 if isinstance(exc, ModelError) else 400
        )
        # Keep filesystem/configuration/provider details in the CLI, never in browser errors.
        message = (
            "Analysis is temporarily unavailable. Please try again later."
            if isinstance(exc, ModelError)
            else "The dataset is temporarily unavailable."
            if isinstance(exc, DataError)
            else "The requested query could not be completed."
            if isinstance(exc, QueryError)
            else str(exc)
        )
        return JSONResponse({"detail": message}, status)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            {
                "detail": [
                    {"loc": e["loc"], "type": e["type"], "message": "Invalid request value."}
                    for e in exc.errors()
                ]
            },
            422,
        )

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            {"detail": "Internal request failure; consult the request ID."},
            500,
            headers={
                "X-Request-ID": getattr(request.state, "request_id", str(uuid4())),
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
            },
        )

    @app.api_route("/api/health", methods=["GET", "HEAD"])
    def health() -> JSONResponse:
        try:
            with connect_readonly(settings.database) as conn:
                conn.execute("SELECT 1").fetchone()
            return JSONResponse({"status": "ok"})
        except PortiqError:
            return JSONResponse({"status": "database unavailable"}, 503)

    @app.get("/api/overview")
    def overview() -> dict[str, Any]:
        return analysis.portfolios.overview()

    @app.get("/api/portfolios", response_model=TablePage)
    def portfolios(limit: int = 100, offset: int = 0) -> TablePage:
        if not 1 <= limit <= 100 or offset < 0:
            raise PortiqError("Use limit 1–100 and nonnegative offset.")
        values = analysis.portfolios.portfolios()
        return TablePage(
            records=values[offset : offset + limit], total=len(values), limit=limit, offset=offset
        )

    @app.get("/api/portfolios/{portfolio_id}", response_model=Snapshot)
    def snapshot(portfolio_id: int) -> Snapshot:
        result = analysis.portfolios.snapshot(portfolio_id)
        if (
            max(len(result.holdings), len(result.prices), len(result.performance), len(result.risk))
            > settings.max_rows
        ):
            raise PortiqError(
                "Snapshot exceeds the configured response bound; use paged holdings or the CLI."
            )
        return result

    @app.get("/api/portfolios/{portfolio_id}/holdings", response_model=TablePage)
    def holdings(portfolio_id: int, limit: int = 100, offset: int = 0) -> TablePage:
        if not 1 <= limit <= min(settings.max_rows, 200) or offset < 0:
            raise PortiqError("Use a positive limit within the configured response bound.")
        rows = analysis.portfolios.holdings(portfolio_id)
        return TablePage(
            records=[h.model_dump() for h in rows[offset : offset + limit]],
            total=len(rows),
            limit=limit,
            offset=offset,
        )

    @app.get("/api/portfolios/{portfolio_id}/exposure", response_model=ExposureResult)
    def exposure(portfolio_id: int) -> ExposureResult:
        return calculate_exposure(settings.database, str(portfolio_id))

    @app.get("/api/portfolios/{portfolio_id}/reconciliation", response_model=Reconciliation)
    def reconciliation(portfolio_id: int) -> Reconciliation:
        return snapshot(portfolio_id).reconciliation

    @app.get("/api/portfolios/{portfolio_id}/performance")
    def performance(portfolio_id: int) -> list[dict[str, Any]]:
        return snapshot(portfolio_id).performance

    @app.get("/api/portfolios/{portfolio_id}/risk")
    def risk(portfolio_id: int) -> list[dict[str, Any]]:
        return snapshot(portfolio_id).risk

    def answer(body: Ask, conversational: bool) -> AskResult | JSONResponse:
        if not model_slot.acquire(blocking=False):
            raise ModelError("Another analysis is running; retry shortly.", kind="busy")
        try:
            result, session_id = analysis.ask(
                body.question,
                session_id=body.session_id,
                selected=body.selected_portfolio,
                conversation=conversational,
                strategy=body.strategy,
                local=body.local,
                cached=body.cache,
            )
            if result.status == "error":
                result.answer = "Analysis is temporarily unavailable. Please try again later."
                for trace in result.tools:
                    if trace.error:
                        trace.error = "This analysis step could not be completed."
            envelope = AskResult(response=result, session_id=session_id)
            if result.status == "error":
                status = (
                    429
                    if result.error_kind in {"rate_limit", "daily_quota", "local_budget"}
                    else 503
                )
                headers = (
                    {"Retry-After": str(math.ceil(result.error_retry_after))}
                    if result.error_retry_after is not None
                    and math.isfinite(result.error_retry_after)
                    else None
                )
                return JSONResponse(envelope.model_dump(mode="json"), status, headers=headers)
            return envelope
        finally:
            model_slot.release()

    @app.post("/api/ask", response_model=AskResult)
    def ask(body: Ask) -> AskResult | JSONResponse:
        return answer(body, False)

    @app.post("/api/conversation", response_model=AskResult)
    def conversation(body: Ask) -> AskResult | JSONResponse:
        return answer(body, True)

    app.mount(
        "/", StaticFiles(directory=Path(__file__).parent / "web", html=True), name="dashboard"
    )
    return app


def main() -> None:
    """Container entry point; optional web dependencies stay outside the base CLI."""
    import uvicorn

    settings = Settings.from_env()
    host = os.getenv("PORTIQ_HOST", "127.0.0.1")
    if (
        host not in {"127.0.0.1", "localhost"}
        and settings.api_key.get_secret_value()
        and not os.getenv("PORTIQ_DEMO_TOKEN")
        and os.getenv("PORTIQ_ALLOW_ANONYMOUS") != "1"
    ):
        raise PortiqError(
            "Set PORTIQ_DEMO_TOKEN for networked Gemini access, or PORTIQ_ALLOW_ANONYMOUS=1."
        )
    if not settings.database.exists():
        initialize(settings.source, settings.database)
    uvicorn.run(
        create_app(settings), host=host, port=int(os.getenv("PORT", "8000")), proxy_headers=False
    )


if __name__ == "__main__":
    main()
