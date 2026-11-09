# PortiQ ? CLI-first portfolio analytics

PortiQ uses Gemini to choose validated, read-only SQL or a deterministic equity-sector
exposure calculator. It includes a CLI evaluator for the original PL Capital questions.
The supplied data is static demonstration data, not live prices or investment advice.

## Run

Use Python 3.11+ and uv. From this directory:

```powershell
uv sync --frozen
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
# Set GEMINI_API_KEY privately in .env. Never commit it.
uv run portfolio-agent init-db
uv run portfolio-agent chat
```

Type a question, then `exit` to finish. For a single question:

```powershell
uv run portfolio-agent ask "How many portfolios do we have in total?" --show-sql
```

`uv run python main.py` initializes a missing database and opens chat. The core CLI needs
no browser, web server, FastAPI, Streamlit or Node. A pip alternative is `pip install -e .`.
Ordinary `ask`/`chat` use Gemini; local answers, cache and context require explicit flags.

## Evaluate

```powershell
uv run portfolio-agent evaluate --output reports/local/supplied-new.json
uv run portfolio-agent evaluate --suite extended --output reports/local/extended-new.json
```

Evaluation uses real Gemini quota, disables local/cache answers and exits 1 on failure.
Keep fresh output names. [Versioned evidence](reports/README.md) distinguishes observed
failures, full runs, interrupted runs and historical results. Scores belong to their
captured runtime; they are not automatically recertified by a refactor.

## Optional interfaces

```powershell
uv run --extra gui portfolio-agent gui
uv run --extra web portfolio-agent serve
```

Streamlit uses localhost:8501; the HTML dashboard uses localhost:8000. Both share the
agent and financial tools. [Deploy Streamlit](docs/STREAMLIT_DEPLOYMENT.md) or read the
[API/deployment guide](docs/OPERATIONS.md). These dependencies are optional for the CLI.

## Reviewer links

- [Original assignment](docs/assignment/README.md) and [requirement checklist](docs/SUBMISSION.md)
- [Architecture](docs/ARCHITECTURE.md), [financial conventions](docs/DATA_ASSUMPTIONS.md)
  and [engineering decisions/refactor verification](docs/ENGINEERING_NOTES.md)
- [Evaluation methodology](docs/EVALUATION.md), [security](docs/SECURITY.md),
  [optional enhancements](docs/ENHANCEMENTS.md) and [known limitations](docs/KNOWN_LIMITATIONS.md)

Key-free checks: `uv sync --frozen --extra dev --extra gui --extra performance`, then
`uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .` and `uv run mypy`.
Browser checks use `npm ci`, `npx playwright install chromium` and `npm run test:web`.
