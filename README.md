# PortiQ - CLI-first Portfolio Analytics Agent

[![CI](https://github.com/Shaunakrane914/PortiQ/actions/workflows/ci.yml/badge.svg)](https://github.com/Shaunakrane914/PortiQ/actions)
[Hosted demo](https://portiq-b9u7.onrender.com) | [Assignment checklist](docs/SUBMISSION.md#assignment-requirements) | [Latest supplied CLI evidence](reports/supplied-no-rag-2026-11-09/README.md)

PortiQ implements the four deliverables in the original [PL Capital assignment](docs/assignment/README.md): a natural-language SQL tool, an equity-only sector exposure calculator, a command-line agent that chooses tools, and a command-line evaluator for the supplied ground truth. The optional API/dashboard uses the same backend. Data is a static demonstration, not live market data or investment advice.

## Run the assignment solution

Use Python 3.11+ from a clone of this repository. [uv](https://docs.astral.sh/uv/getting-started/installation/) is the recommended installer; `uv.lock` is the tested dependency resolution.

```powershell
uv sync --frozen
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
# Set GEMINI_API_KEY in .env locally. Never commit the key.
uv run portfolio-agent init-db
uv run portfolio-agent chat
# Shortcut after installing dependencies; initializes a missing database:
uv run python main.py
```

Run `init-db` once on a fresh checkout. It validates and loads all nine CSVs; it will not replace an existing database without `--rebuild`. On macOS/Linux, create the environment file with `test -f .env || cp .env.example .env`. A pip alternative is `python -m pip install -e .` in an activated virtual environment, then use `portfolio-agent` directly. The supplied `requirements.txt` is preserved reference material; current runtime dependencies are in `pyproject.toml`.

In `chat`, type a question directly, then type `exit` when finished. Example questions:

- How many portfolios do we have in total?
- What are the names of all active portfolios?
- Calculate sector exposure for Balanced Portfolio.

Bare `chat` and `main.py` treat questions independently and use genuine Gemini by default. `--context`, `--local` and `--cache` are explicit opt-ins. Global flags work before the command: `uv run python main.py --db portfolio_database.db exposure "Balanced Portfolio"`. Neither the base CLI nor its evaluator needs FastAPI, Node, a browser, or a running server.

```powershell
# Natural-language SQL: Gemini generates and locally validates the query.
uv run portfolio-agent ask "List the names of Passive portfolios, alphabetically." --show-sql
# Deterministic exposure: no Gemini key or calls needed.
uv run portfolio-agent exposure "Balanced Portfolio"
# Explicit SQL execution: this command does not translate natural language.
uv run portfolio-agent sql "SELECT COUNT(*) FROM portfolios"
# Configuration/database checks; --live additionally spends a Gemini request.
uv run portfolio-agent doctor
```

## Evaluate accuracy first

The **required supplied suite has 10 questions** in [ground_truth_dataset.json](ground_truth_dataset.json): eight SQL and two exposure questions. The separate, author-created [extended suite](evaluation/extended.json) has 50 previously observed regression questions.

```powershell
# Required supplied ground truth; uses genuine Gemini calls.
uv run portfolio-agent evaluate --output reports/local/supplied-new.json
# Optional extended regression; uses genuine Gemini calls.
uv run portfolio-agent evaluate --suite extended --output reports/local/extended-new.json
```

Choose fresh output names: the evaluator writes JSON, Markdown and a temporary progress report at the selected path. `evaluate` bypasses the local registry and answer cache, independently checks results and returns a nonzero exit code if any case fails. Check account quota and the local daily guard before a live run; [configuration and quota handling](docs/SUBMISSION.md#configuration) explain their separate scopes.

The [8 November 2026 CLI-only run](reports/cli-2026-11-08/README.md) on `4b49d95` passed **50/50**: 46 data-result cases and four handling cases, **92 actual SDK calls**, **201,404 reported tokens**, zero provider errors, and 593.976 seconds of CLI wall time. The archived original path passed the same suite with 266,304 tokens: 24.37% fewer tokens with no observed regression on those cases. Historical runs are not controlled speed comparisons or proof of unseen accuracy. Six cases have additional automated narrative assertions; all six passed.

The latest [full-schema CLI run without RAG](reports/supplied-no-rag-2026-11-09/README.md) on `0b3e94a` passed **10/10**, including all ten explicit final-answer checks: **21 SDK attempts, 48,293 reported tokens**, zero provider errors. Both retrieval strategies are removed; categorical values, relationships and financial conventions remain in context.

The earlier [graph-removal supplied CLI run](reports/supplied-after-graph-removal-2026-11-08/README.md) on `f14ea21` also passed 10/10 with 21 SDK attempts and 54,093 reported tokens. That historical capture still used BM25; it is not the current no-RAG architecture.

The earlier [supplied-ten CLI run](reports/supplied-v3-2026-11-08/README.md) on `b8db4a9` passed **10/10** under evaluator v3 with 21 SDK calls and 54,075 reported tokens. Its first complete 8/10 capture is retained; two correct exposure tables were rejected before percentage-header support was fixed. Runs are separate and never stitched. [Evaluation methodology](docs/EVALUATION.md) defines the bounded verification contract. Original inputs, frozen suites and captured reports are not rewritten.

## Implementation choices

- Gemini uses typed function calls to choose SQL, exposure or a final response. Python validates every tool invocation. No runtime planner imports benchmark answers.
- Sector exposure normalizes `Stock` holding weights within equities and excludes bonds. Balanced Portfolio computes Technology 61.11%, Financials 22.22%, Healthcare 16.67%; no-positive-equity exposure is undefined.
- SQLGlot validation, SQLite authorization, read-only connections and resource bounds enforce SQL safety. Valid SQL can still answer the wrong question; the evaluator checks its results separately.
- For explicit scalar-only wording such as "Return just the count", one successful, non-truncated, single-cell SQL result can be rendered after Gemini's query generation without another summary call. Other formats and guarded compound requests retain model synthesis. This is labeled in response metadata and is separate from local routing/cache.
- SQLite is file-backed for shared CLI/API access, atomic rebuilds and read-only connections. The brief mentions in-memory setup and also shows a file-backed example; this implementation provides the file-backed choice, not an in-memory mode.

See [architecture](docs/ARCHITECTURE.md), [data conventions](docs/DATA_ASSUMPTIONS.md) and [engineering decisions](docs/ENGINEERING_NOTES.md).

Optional enhancements include a Streamlit chat, concurrent model requests, SQL-efficiency
scoring and a separate production deployment profile alongside safety, logging, validation,
caching and hybrid support. Metadata RAG is deliberately excluded after evaluation.
See the [enhancement checklist and deployment guide](docs/ENHANCEMENTS.md).

Both retrieval strategies were evaluated and removed: BM25 added **12.02% reported tokens**
at equal observed accuracy; schema-graph retrieval scored **9/10 versus 10/10**. Neither
demonstrated a reliable latency benefit. The agent uses the complete nine-table schema,
database-derived categories, portfolio catalogue and financial conventions directly.
The [engineering decision](docs/ENGINEERING_NOTES.md#metadata-retrieval-evaluated-and-excluded)
links both preserved experiments and their limitations.

```powershell
uv sync --frozen --extra gui
uv run --extra gui portfolio-agent gui
```

Streamlit opens on http://127.0.0.1:8501 and matches the existing workspace: navy sidebar,
ivory/gold theme, serif headings, portfolio selector and the same four views. Its analyst
form includes SQL evidence, request metrics and explicit local/cache/context controls.
Full-schema context is shared with the core agent. Efficiency scoring measures SQLite
VM work, not disk reads. The production profile is separate from the anonymous Render demo.

## Optional dashboard and hosted demo

```powershell
uv sync --frozen --extra web
uv run portfolio-agent serve
```

Open **http://127.0.0.1:8000**. AI Analyst is the landing page; Overview, Portfolio Explorer and Reconciliation are the other three views. The static HTML/CSS/JavaScript frontend needs no build step. The hosted [Render demo](https://portiq-b9u7.onrender.com) and [health endpoint](https://portiq-b9u7.onrender.com/api/health) are optional review conveniences, not a production-readiness claim.

The UI starts with local fast-path and exact caching **unchecked**, so chat uses genuine Gemini analysis by default. Enable them explicitly to demonstrate local/cache behavior. The CLI also opts in with `--local` / `--cache`; `evaluate` never uses them. API clients should explicitly send `"local":false,"cache":false` for genuine analysis because the API request schema defaults differ from the UI. Local capabilities cover portfolio counts, unambiguous exposure, holdings and portfolio details. A Gemini-planned scalar answer still consumes a real SDK call.

The deployment explicitly permits anonymous demo access. An optional configured demo token remains supported; no new password wall is required. [Submission, API, Docker and configuration instructions](docs/SUBMISSION.md) document the exact behavior, including the stricter network-bind rule for CLI `serve`.

## Key-free verification

```powershell
uv sync --frozen --extra dev --extra gui
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run --extra gui pytest --cov=portiq
# Node 22 is used in browser CI; only needed for development verification.
npm ci
npx playwright install chromium
npm run check:web
npm run test:web
```

CI runs Python 3.11/3.13 on Ubuntu/Windows plus a separate real browser/container job. Live Gemini evaluations are opt-in and are not CI tests. See [submission](docs/SUBMISSION.md), [security](docs/SECURITY.md), [known limitations](docs/KNOWN_LIMITATIONS.md) and [change history](docs/CHANGELOG.md) for review scope.
