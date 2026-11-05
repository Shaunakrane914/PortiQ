"""Independent command-line interface; no web server or UI dependencies."""

import argparse
import json
import logging
import sys
from pathlib import Path

from pydantic import ValidationError

from portiq.agent import PortfolioAgent, render_response
from portiq.config import Settings
from portiq.database import connect_readonly, initialize
from portiq.errors import PortiqError
from portiq.exposure import calculate_exposure
from portiq.model import GeminiBackend
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
    backend: GeminiBackend | None = None
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
        if args.command == "exposure":
            print(calculate_exposure(settings.database, args.portfolio).model_dump_json(indent=2))
            return 0
        if args.command == "sql":
            print(execute(settings.database, args.query).model_dump_json(indent=2))
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
                model = backend.client.models.get(model=settings.model)
                info["live"] = f"model accessible: {model.name}"
                info["supported_actions"] = ", ".join(model.supported_actions or [])
            print(json.dumps(info, indent=2))
            return 0 if integrity == "ok" and not foreign_keys else 1
        backend = GeminiBackend(settings)
        agent = PortfolioAgent(settings, backend)
        if args.command == "evaluate":
            from portiq.evaluation import evaluate

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
                "Static demonstration data. Type help or exit. Each question is independent."
            )
        while True:
            question = args.question if args.command == "ask" else input("\nYou: ").strip()
            if args.command == "chat" and question.lower() in {"exit", "quit"}:
                return 0
            if args.command == "chat" and question.lower() == "help":
                print(
                    "Ask about portfolio metadata, holdings, market values or sector exposures. "
                    "Use a portfolio name. Each question starts fresh. Type exit to leave."
                )
                continue
            if not question:
                if args.command == "chat":
                    continue
                raise PortiqError("Question cannot be empty.")
            response = agent.answer(question)
            print(
                response.model_dump_json(indent=2)
                if args.json
                else render_response(response, trace=args.trace, sql=args.show_sql)
            )
            if args.command == "ask":
                return 1 if response.status in {"error", "partial"} else 0
    except (PortiqError, ValidationError) as exc:
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


if __name__ == "__main__":
    raise SystemExit(main())
