"""PortiQ interactive CLI entry point.

Run directly to start asking questions in the terminal:
    python main.py
    python run_cli.py

Or ask a single question immediately:
    python main.py "Show holdings for Conservative Income Fund"

Or run any sub-command:
    python main.py exposure "Balanced Portfolio"
    python main.py doctor
"""

import sys
from pathlib import Path

# Ensure src/ is on sys.path for direct execution without prior installation
ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from portiq.cli import main as cli_main  # noqa: E402
from portiq.config import Settings  # noqa: E402
from portiq.database import initialize  # noqa: E402
from portiq.errors import PortiqError  # noqa: E402

KNOWN_COMMANDS = {
    "ask",
    "chat",
    "exposure",
    "sql",
    "snapshot",
    "reconcile",
    "init-db",
    "doctor",
    "serve",
    "evaluate",
}


def bootstrap() -> None:
    """Ensure database exists and dispatch to the interactive CLI chat."""
    settings = Settings.from_env()

    # Automatically initialize the database from CSVs if not present
    if not settings.database.exists():
        print(f"Initializing portfolio database at {settings.database} from CSV inputs...")
        initialize(settings.source, settings.database)
        print("Database initialized successfully.\n")

    args = sys.argv[1:]

    # Default: launch interactive chat session
    if not args:
        sys.exit(cli_main(["chat", "--local", "--context"]))

    first = args[0]
    if first in KNOWN_COMMANDS:
        sys.exit(cli_main(args))

    # Flags without a subcommand: default to chat with those flags
    if first.startswith("-") and first not in {"-h", "--help"}:
        sys.exit(cli_main(["chat", "--local", "--context", *args]))

    # Raw question passed directly: python main.py "What is Balanced Portfolio exposure?"
    sys.exit(cli_main(["ask", *args, "--local", "--context"]))


if __name__ == "__main__":
    try:
        bootstrap()
    except KeyboardInterrupt:
        print("\nSession ended.")
        sys.exit(0)
    except PortiqError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
