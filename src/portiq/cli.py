"""Independent command-line interface; no web server or UI dependencies."""

import argparse
import importlib.util
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

from google.genai import types
from pydantic import ValidationError

from portiq.agent import AnswerAgent, PortfolioAgent, render_response
from portiq.analytics import PortfolioService
from portiq.config import Settings
from portiq.database import connect_readonly, initialize
from portiq.errors import PortiqError
from portiq.exposure import calculate_exposure
from portiq.model import GeminiBackend
from portiq.service import AnalysisService, FallbackBackend
from portiq.sql import execute


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="PortiQ — PL Capital Portfolio Intelligence Agent")
    root.add_argument("--db", type=Path, help="SQLite path (default PORTIQ_DB)")
    root.add_argument("--source", type=Path, help="Assessment directory (default PORTIQ_SOURCE)")
    root.add_argument("--model", help="Gemini model ID (default GEMINI_MODEL)")
    root.add_argument(
        "--verbose", action="store_true", help="Operational logs, never hidden reasoning"
    )
    commands = root.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init-db", help="Validate and atomically load all supplied CSVs")
    init.add_argument("--rebuild", action="store_true")
    for command in ("ask", "chat"):
        sub = commands.add_parser(command, help="Ask Gemini using portfolio tools")
        if command == "ask":
            sub.add_argument("question")
        sub.add_argument(
            "--json", action="store_true", help="Structured result with trace metadata"
        )
        sub.add_argument("--trace", action="store_true")
        sub.add_argument("--show-sql", action="store_true")
        sub.add_argument(
            "--local", action="store_true", help="Enable the explicit local capability registry"
        )
        sub.add_argument("--cache", action="store_true", help="Enable session-scoped exact caching")
        sub.add_argument(
            "--context", action="store_true", help="Opt in to bounded conversation context"
        )
    for name in ("snapshot", "reconcile"):
        analytic_command = commands.add_parser(
            name, help="Local recorded-data analytics; no API key"
        )
        analytic_command.add_argument("portfolio")
    serve = commands.add_parser("serve", help="Launch the optional FastAPI dashboard")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    gui = commands.add_parser("gui", help="Launch the optional Streamlit interface on loopback")
    gui.add_argument("--port", type=int, default=8501)
    exposure = commands.add_parser("exposure", help="Deterministic exposure; no API key required")
    exposure.add_argument("portfolio")
    sql = commands.add_parser("sql", help="Execute explicit read-only SQL; no API key required")
    sql.add_argument("query")
    doctor = commands.add_parser("doctor", help="Check data/config; optionally verify model access")
    doctor.add_argument("--live", action="store_true")
    evaluation = commands.add_parser(
        "evaluate", help="Live Gemini evaluation with independent oracles"
    )
    evaluation.add_argument("--suite", choices=["supplied", "extended"], default="supplied")
    evaluation.add_argument("--output", type=Path, default=Path("reports/local/evaluation.json"))
    evaluation.add_argument("--trials", type=int, choices=range(1, 6), default=1)
    evaluation.add_argument("--split", choices=["development", "validation", "heldout"])
    evaluation.add_argument("--limit", type=int)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s %(message)s",
    )
    # SDK/http transport loggers can include URLs; never enable them for --verbose.
    logging.getLogger("httpx").setLevel(logging.ERROR)
    logging.getLogger("google").setLevel(logging.ERROR)
    backend: GeminiBackend | FallbackBackend | None = None
    analysis: AnalysisService | None = None
    try:
        settings = Settings.from_env()
        overrides = {
            name: getattr(args, flag)
            for name, flag in [("database", "db"), ("source", "source"), ("model", "model")]
            if getattr(args, flag) is not None
        }
        settings = Settings.model_validate(
            settings.model_dump() | overrides | {"api_key": settings.api_key}
        )
        if args.command == "init-db":
            print(
                json.dumps(
                    initialize(settings.source, settings.database, rebuild=args.rebuild), indent=2
                )
            )
            return 0
        if args.command == "gui":
            if importlib.util.find_spec("streamlit") is None:
                raise PortiqError("Install the GUI extra: uv sync --extra gui")
            if not 1 <= args.port <= 65535:
                raise PortiqError("Use a port between 1 and 65535.")
            return subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "streamlit",
                    "run",
                    str(Path(__file__).with_name("streamlit_app.py")),
                    "--server.address=127.0.0.1",
                    f"--server.port={args.port}",
                    "--browser.gatherUsageStats=false",
                    "--theme.primaryColor=#B69C6A",
                    "--theme.backgroundColor=#F4F1E8",
                    "--theme.secondaryBackgroundColor=#F4F1E8",
                    "--theme.textColor=#111C2E",
                ],
                check=False,
                env=os.environ
                | {
                    "PORTIQ_DB": str(settings.database.resolve()),
                    "PORTIQ_SOURCE": str(settings.source.resolve()),
                    "GEMINI_MODEL": settings.model,
                },
            ).returncode
        if args.command == "exposure":
            print(calculate_exposure(settings.database, args.portfolio).model_dump_json(indent=2))
            return 0
        if args.command == "sql":
            print(execute(settings.database, args.query).model_dump_json(indent=2))
            return 0
        if args.command in {"snapshot", "reconcile"}:
            from portiq.exposure import resolve_portfolio

            identity = resolve_portfolio(settings.database, args.portfolio)[0]
            snapshot = PortfolioService(settings.database).snapshot(identity)
            print(
                (
                    snapshot if args.command == "snapshot" else snapshot.reconciliation
                ).model_dump_json(indent=2)
            )
            return 0
        if args.command == "serve":
            try:
                import uvicorn

                from portiq.api import create_app
            except ImportError as exc:
                raise PortiqError("Install the web extra: uv sync --extra web") from exc
            if args.host not in {"127.0.0.1", "localhost"} and not os.getenv("PORTIQ_DEMO_TOKEN"):
                raise PortiqError("Set PORTIQ_DEMO_TOKEN before binding outside loopback.")
            uvicorn.run(create_app(settings), host=args.host, port=args.port, proxy_headers=False)
            return 0
        if args.command == "doctor":
            with connect_readonly(settings.database) as conn:
                integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
                foreign_keys = list(conn.execute("PRAGMA foreign_key_check"))
            info = {
                "database": str(settings.database),
                "integrity": integrity,
                "foreign_key_errors": len(foreign_keys),
                "model": settings.model,
                "key_configured": bool(settings.api_key.get_secret_value()),
                "live": "not requested",
            }
            if args.live:
                backend = GeminiBackend(settings)
                probe = backend.generate(
                    [types.Content(role="user", parts=[types.Part.from_text(text="Reply OK.")])],
                    types.GenerateContentConfig(temperature=0, max_output_tokens=32),
                )
                info["live"] = "generation succeeded"
                info["resolved_model"] = probe.model_version or "not provided by API"
            print(json.dumps(info, indent=2))
            return 0 if integrity == "ok" and not foreign_keys else 1
        agent: AnswerAgent | None = None
        if args.command in {"ask", "chat"} and (args.local or args.cache or args.context):
            analysis = AnalysisService(settings)
        else:
            backend = (
                FallbackBackend(settings) if settings.fallback_models else GeminiBackend(settings)
            )
            agent = PortfolioAgent(settings, backend)
        if args.command == "evaluate":
            from portiq.evaluation import evaluate

            assert agent is not None

            suite = settings.source / (
                "ground_truth_dataset.json"
                if args.suite == "supplied"
                else "evaluation/extended.json"
            )
            if args.limit is not None and args.limit <= 0:
                raise PortiqError("--limit must be positive.")
            report = evaluate(
                agent, suite, args.output, trials=args.trials, split=args.split, limit=args.limit
            )
            print(f"{report['passed']}/{report['total']} passed; report: {args.output}")
            return 0 if report["passed"] == report["total"] and report["total"] else 1
        if args.command == "chat":
            print(
                f"PortiQ | database: {settings.database} | model: {settings.model}\n"
                "Static demonstration data. Type help or exit. Each question is independent "
                "by default; --context enables bounded follow-ups."
            )
        session_id: str | None = None
        while True:
            question = args.question if args.command == "ask" else input("\nYou: ").strip()
            if args.command == "chat" and question.lower() in {"exit", "quit"}:
                return 0
            if args.command == "chat" and question.lower() == "help":
                print(
                    "Ask about portfolio metadata, holdings, market values or sector exposures. "
                    "Use a portfolio name; --context enables bounded follow-ups. "
                    "Type exit to leave."
                )
                continue
            if not question:
                if args.command == "chat":
                    continue
                raise PortiqError("Question cannot be empty.")
            if analysis is not None:
                response, session_id = analysis.ask(
                    question,
                    session_id=session_id,
                    conversation=args.context,
                    local=args.local,
                    cached=args.cache,
                )
            else:
                assert agent is not None
                response = agent.answer(question)
            print(
                response.model_dump_json(indent=2)
                if args.json
                else render_response(response, trace=args.trace, sql=args.show_sql)
            )
            if args.command == "ask":
                return 1 if response.status in {"error", "partial"} else 0
    except (PortiqError, ValidationError, ValueError) as exc:
        message = str(exc) if isinstance(exc, PortiqError) else "Invalid application configuration."
        print(f"Error: {message}", file=sys.stderr)
        return 1
    except (FileNotFoundError, PermissionError):
        print(
            "Error: a required file is missing or inaccessible; check paths and permissions.",
            file=sys.stderr,
        )
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye.")
        return 130 if isinstance(sys.exception(), KeyboardInterrupt) else 0
    finally:
        if backend is not None:
            backend.close()
        if analysis is not None:
            analysis.close()


if __name__ == "__main__":
    raise SystemExit(main())
