# PortiQ — CLI-first portfolio analytics

[![CI](https://github.com/Shaunakrane914/PortiQ/actions/workflows/ci.yml/badge.svg)](https://github.com/Shaunakrane914/PortiQ/actions)
[Hosted demo](https://portiq-b9u7.onrender.com) · [Assignment checklist](docs/SUBMISSION.md) · [Evaluation evidence](docs/EVALUATION.md)

PortiQ implements the four [assignment deliverables](docs/assignment/README.md): a
Gemini-powered command-line agent, a ground-truth evaluator, run instructions and typed
Python code with bounded errors. Gemini chooses read-only SQL or a deterministic equity
exposure calculator. The supplied dataset is static demonstration data, not live market
data or investment advice.

## Run the CLI

Use Python 3.11+ and [uv](https://docs.astral.sh/uv/getting-started/installation/).

```powershell
uv sync --frozen
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
# Configure GEMINI_API_KEY privately in .env; never commit it.
uv run portfolio-agent init-db
uv run portfolio-agent chat
```

Type a question directly, then `exit` to finish. Try:

- How many portfolios do we have in total?
- What are the names of all active portfolios?
- Calculate sector exposure for Balanced Portfolio.

Initialize once; replacing an existing database requires `init-db --rebuild`. On macOS/Linux,
use `test -f .env || cp .env.example .env`. A pip alternative is `python -m pip install -e .`.
`uv run python main.py` is a shortcut that initializes a missing database and opens chat.
The base CLI needs no server, browser, FastAPI, Streamlit or Node.

```powershell
uv run portfolio-agent ask "List the names of Passive portfolios, alphabetically." --show-sql
uv run portfolio-agent exposure "Balanced Portfolio"
uv run portfolio-agent sql "SELECT COUNT(*) FROM portfolios"
```

`ask` and ordinary `chat` use genuine Gemini. Local answers, caching and conversation context
require explicit `--local`, `--cache` and `--context` flags. `sql` executes explicit SQL;
`exposure` performs the calculation without a model call. Global flags go before commands,
for example `portfolio-agent --db portfolio_database.db chat`.

## Evaluate the answers

```powershell
uv run portfolio-agent evaluate --output reports/local/supplied-new.json
uv run portfolio-agent evaluate --suite extended --output reports/local/extended-new.json
# Optional SQLite logical page-access scoring:
uv sync --frozen --extra performance
uv run portfolio-agent evaluate --profile-io --output reports/local/supplied-io.json
```

The required suite has ten questions; the author-created regression has fifty, including
three hybrid questions using both tools. Evaluation spends real Gemini quota, disables
local/cache answers, independently checks SQL/CSV results and verifies explicit final-answer
content. Any failed case returns exit code 1. Use fresh output names. Evaluator v4 fixes
hybrid percentage/scalar interference; historical captures retain their original version.
[Evidence and limits](docs/EVALUATION.md) distinguish live runs, offline replays and load tests.

[Current verification](reports/completion-2026-11-09/README.md): **50/50 extended passed
after retries**, including all three hybrids; supplied CLI 10/10; concurrent conversations
9/9. The extended evaluation and both retry captures total 102 SDK attempts, 217,421
reported tokens and 865.927 seconds of summed capture time across 54 question executions.
Six SDK attempts have unreported usage. Local tests, live dashboard/Streamlit, browser,
HTTP/stub soak and all 16 production Docker checks passed. Full timing, usage and provenance
are recorded in the linked report; original captures remain intact.

The agent uses the complete nine-table schema, actual categorical values, catalogue and
financial conventions. SQL is parsed, authorized, bounded and read-only. Exposure normalizes
Stock weights and excludes bonds; total quote values include bonds. Both RAG strategies were
[evaluated and excluded](docs/ENGINEERING_NOTES.md#metadata-retrieval-evaluated-and-excluded).

## Optional interfaces and deployment

```powershell
uv sync --frozen --extra web
uv run portfolio-agent serve
# Optional native Streamlit interface:
uv sync --frozen --extra gui
uv run --extra gui portfolio-agent gui
```

The existing dashboard opens at http://127.0.0.1:8000; Streamlit uses port 8501. Both open
AI Analyst first. Local/cache controls default off in the interfaces. API clients must send
`"local":false,"cache":false` explicitly for genuine analysis. The hosted anonymous demo
is separate from the token-protected production profile.

[Operations](docs/OPERATIONS.md) covers production Compose, readiness, graceful shutdown,
backup/recovery, concurrent HTTP verification and measured service limits. The supported
topology is one process with four concurrent analyses; distributed replicas are not claimed.

## Verify without spending Gemini quota

```powershell
uv sync --frozen --extra dev --extra gui --extra performance
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run --extra gui --extra performance pytest
```

See [architecture](docs/ARCHITECTURE.md), [data conventions](docs/DATA_ASSUMPTIONS.md),
[optional enhancements](docs/ENHANCEMENTS.md) and [known limitations](docs/KNOWN_LIMITATIONS.md).
The original data, assignment and frozen evaluation suites remain unchanged.
