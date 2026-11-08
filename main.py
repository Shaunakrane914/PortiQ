"""Terminal shortcut: python main.py, python main.py "question", or any CLI subcommand."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from portiq.cli import main as cli_main  # noqa: E402
from portiq.cli import parser  # noqa: E402
from portiq.config import Settings  # noqa: E402
from portiq.database import initialize  # noqa: E402
from portiq.errors import PortiqError  # noqa: E402

COMMANDS = {
    "ask",
    "chat",
    "exposure",
    "sql",
    "snapshot",
    "reconcile",
    "init-db",
    "doctor",
    "serve",
    "gui",
    "evaluate",
}


def dispatch(arguments: list[str]) -> list[str]:
    """Preserve global options before selecting a subcommand; never enable hidden modes."""
    prefix: list[str] = []
    rest = arguments.copy()
    while rest:
        option = rest[0].split("=", 1)[0]
        if option == "--verbose":
            prefix.append(rest.pop(0))
        elif option in {"--db", "--source", "--model"}:
            flag = rest.pop(0)
            prefix.append(flag)
            if "=" not in flag:
                if not rest:
                    return prefix
                prefix.append(rest.pop(0))
        else:
            break
    if rest and rest[0] in COMMANDS | {"-h", "--help"}:
        return prefix + rest
    if not rest or rest[0].startswith("-"):
        return prefix + ["chat"] + rest
    return prefix + ["ask"] + rest


def bootstrap() -> int:
    arguments = dispatch(sys.argv[1:])
    args = parser().parse_args(arguments)
    try:
        if args.command in {"ask", "chat"}:
            settings = Settings.from_env()
            database = args.db if args.db is not None else settings.database
            source = args.source if args.source is not None else settings.source
            if not database.exists():
                initialize(source, database)
        return cli_main(arguments)
    except (PortiqError, OSError, ValueError) as exc:
        message = (
            str(exc) if isinstance(exc, PortiqError) else "Check configuration and input paths."
        )
        print(f"Error: {message}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(bootstrap())
