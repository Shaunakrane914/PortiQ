# Assignment checklist and reviewer runbook

The unchanged [original assignment](assignment/README.md) is the source of requirements. Its deliverables are a working command-line agent, a ground-truth evaluator, brief run documentation and clean code with error handling. The API/dashboard and other enhancements are optional.

## Assignment requirements

| Original requirement | Current implementation | Reviewer verification |
|---|---|---|
| SQL Query Tool: natural language to SQL | Typed `sql_query`, `run_sql_tool` in [agent.py](../src/portiq/agent.py), execution boundary in [sql.py](../src/portiq/sql.py) | `ask "What are the names of all active portfolios?" --show-sql` |
| Exposure Calculator: combine weights and sectors; ignore bonds | `calculate_exposure` in [exposure.py](../src/portiq/exposure.py); stock-only normalized weights and Decimal arithmetic | `exposure "Balanced Portfolio"` |
| CLI Portfolio Agent: select a tool | [cli.py](../src/portiq/cli.py) `chat` / `ask`; Gemini chooses SQL/exposure/respond | Start `chat` and type SQL-style and exposure questions |
| CLI Agent Evaluator: use supplied ground truth | [evaluation.py](../src/portiq/evaluation.py); supplied ten selected by default | `evaluate --output reports/local/supplied-new.json` |
| Brief run/design documentation | [README](../README.md), this guide, [architecture](ARCHITECTURE.md) | Fresh-clone quick start below |
| Clean code and error handling | Typed modules, input validation, SQL restrictions, bounded repairs/retries and safe errors | Key-free lint/type/tests; malformed-input and missing-data handling |

Commands in the table are subcommands of `uv run portfolio-agent`. The direct `sql` command executes user-written SQL; natural-language translation is demonstrated through `ask` / `chat`.

### Setup choices relative to the brief

All nine CSVs, schema, supplied ground truth, suggested `requirements.txt` and original assignment remain unchanged. Current install metadata is `pyproject.toml` / `uv.lock`. Suggested requirements include optional packages that the base CLI does not need. The runtime uses Google GenAI (`genai.Client`); the brief's illustrative `google.generativeai` snippet is not copied as the application API.

The setup hint mentions in-memory loading, while the sample opens `portfolio_database.db`. This implementation chooses file-backed SQLite for process reuse, atomic initialization and read-only query connections. An in-memory mode is not claimed.

### Optional enhancements

| Enhancement in the assignment | Status |
|---|---|
| SQL safety, parameterized queries, errors, logging, input validation | Implemented. Fixed queries bind parameters; generated SQL is parsed/authorized/read-only, rather than universally parameterized. |
| Caching | Explicit exact cache; disabled during live evaluation. |
| Graphical interface | Existing HTML/JS dashboard plus optional Streamlit chat (`gui`). |
| RAG / GraphRAG for metadata | Basic BM25 retrieval over live schema/foreign-key documents, with source IDs and the full schema retained. Graph retrieval was evaluated and removed; see the [engineering decision](ENGINEERING_NOTES.md#schema-graph-retrieval-archived). |
| REST API | Production configuration profile, liveness/readiness, bounded requests, safe logging and hardened retained-volume Compose recipe. |
| Concurrent multi-user execution | Default four analyses, separate reusable clients, shared quota guards and per-session turn locks. |
| Performance-aware evaluation | Correctness-gated relative SQLite VM-work scoring and query plans. Logical page I/O is not measured. |
| Hybrid questions using both tools | Implemented; three cases in the extended regression. |

See [enhancement implementation, verification and production scope](ENHANCEMENTS.md).

## Fresh-clone CLI demonstration

```powershell
uv sync --frozen
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
# Configure GEMINI_API_KEY privately in .env.
uv run portfolio-agent init-db
uv run portfolio-agent doctor
uv run portfolio-agent chat
```

Type questions directly, then `exit`. Add `--context` for bounded follow-ups; default questions are independent. Omit `--local` / `--cache` for a genuine-model assessment demonstration.

```powershell
uv run portfolio-agent ask "What are the names of all active portfolios?" --show-sql
uv run portfolio-agent exposure "Balanced Portfolio"
uv run portfolio-agent ask "How many securities are classified as Bond? Return just the count." --json
```

The last command demonstrates Gemini-generated SQL with direct scalar rendering; retries/repairs can still increase its call count. A bond-only portfolio returns an undefined-equity-exposure error. For a controlled failure demonstration, `sql "DELETE FROM portfolios"` is rejected by the read-only boundary.

## Required evaluation and evidence

```powershell
uv run portfolio-agent evaluate --output reports/local/supplied-new.json
# Optional author-created regression:
uv run portfolio-agent evaluate --suite extended --output reports/local/extended-new.json
```

Both spend genuine Gemini quota. Use fresh output names: reports are written at the selected path. JSON contains SQL/results/reference comparisons and provider metrics; Markdown contains strict pass/fail. Exit code 1 indicates at least one failure. Successful retries from separate runs are not stitched into a full score.

The fresh [supplied CLI evidence](../reports/supplied-v3-2026-11-08/README.md) captures `b8db4a9`: **10/10**, all ten final-answer checks, 21 SDK calls and 54,075 reported tokens. A separate earlier 8/10 run is retained with its two verifier-format false negatives. The [historical CLI-only extended evidence](../reports/cli-2026-11-08/README.md) captures `4b49d95`: 50/50 under evaluator v2, 92 SDK calls and 201,404 tokens. These are different suites and verification contracts; see [evaluation](EVALUATION.md).

## Configuration

A Gemini key is required only for genuine model questions. Deterministic SQL/exposure and read-only dashboard views need none. These are repository defaults, not the owner's current `.env` or Google's remaining quota.

| Variable | Default | Scope |
|---|---|---|
| `GEMINI_API_KEY` | empty | CLI/server credential; never a browser asset |
| `GEMINI_MODEL` | `gemini-3.1-flash-lite` | Primary model; availability verified only by a live request |
| `PORTIQ_DB`, `PORTIQ_SOURCE` | `portfolio_database.db`, `.` | SQLite file and input directory; global CLI flags can override |
| `PORTIQ_REQUEST_INTERVAL` | 0.0 s | Fixed minimum SDK-start spacing; 0.0 s allows adaptive limiter to govern pacing |
| `PORTIQ_RPM_LIMIT` | 12 | Adaptive limiter safety ceiling (under provider's 15 RPM limit) |
| `PORTIQ_RPM_WINDOW` | 60.0 s | Rolling window duration for SDK attempt tracking |
| `PORTIQ_RPM_COOLDOWN_THRESHOLD` | 8 | In-window attempt count that triggers question-level cooldown |
| `PORTIQ_RPM_COOLDOWN_SECONDS` | 1.5 s | Cooldown before starting a new question when approaching quota |
| `PORTIQ_MAX_WAIT_SECONDS` | 10.0 s | Recovery ceiling before returning immediate 429 Retry-After |
| `PORTIQ_DAILY_REQUESTS` | 200; Docker 100 | Actual-SDK-attempt local guard per UTC day |
| `PORTIQ_QUOTA_DB` | unset; Docker `/app/runtime/quota.sqlite` | Shared daily ledger; unset uses instance memory |
| `PORTIQ_FALLBACK_MODELS` | empty | Up to two explicit sequential alternatives |
| `PORTIQ_CIRCUIT_FAILURES`, `PORTIQ_CIRCUIT_SECONDS` | 3, 30 | Transient/transport circuit threshold and cooldown |
| `PORTIQ_DEMO_TOKEN` | unset | Optional bearer access; configured token is enforced even with anonymous opt-in |
| `PORTIQ_ALLOW_ANONYMOUS` | unset; Render `1` | Module/container opt-in for networked model access without a token |
| `PORTIQ_HOST` | module `127.0.0.1`; Docker `0.0.0.0` | Module entry point bind; CLI `serve` uses `--host` |
| `PORT` | module 8000 | Module entry point port; CLI `serve` uses `--port` |
| `PORTIQ_ALLOWED_HOSTS` | local hosts | Extra hosts; `*` supported. Anonymous module mode without an explicit list also allows any host. Render sets `*`. |
| `PORTIQ_CORS_ORIGINS` | empty | Explicit cross-origin allowlist; `*` is rejected |
| `PORTIQ_RATE_LIMIT` | 60/minute | Socket-client HTTP rate limit, separate from Gemini RPM/SDK pacing |
| `PORTIQ_MAX_CONCURRENT_ANALYSES` | 4 | Concurrent analyses/client pool bound, range 1–32 |
| `PORTIQ_ENV` | `demo` | Explicit `production` profile validates token/hosts/persistent ledger and uses exact origins |

The local ledger is not Google's quota meter. It counts SDK attempts, including delivery-unknown failures, only among processes sharing its file/settings. In-memory ledgers reset on backend restart. Container disk may be ephemeral; persistent counters require a writable retained volume. Conflicting process caps are unsupported. The local day resets at 00:00 UTC (05:30 IST). Google's quota/reset behavior is separate and must be checked in AI Studio. The local counter cannot reveal a remaining Google token balance.

The captured CLI run's approved 300-attempt exception was process-only; it did not change normal defaults or Google billing. It is historical metadata, not approval for future budget changes. Wait for reset or deliberately configure an approved cap if a guard is exhausted; do not delete the ledger to hide usage. Daily/authentication suppression can require a backend restart after the underlying issue is resolved.

## Optional local API / dashboard

```powershell
uv sync --frozen --extra web
uv run portfolio-agent serve
```

AI Analyst opens at http://127.0.0.1:8000; the other views are Overview, Portfolio Explorer and Reconciliation. Local/cache checkboxes default to unchecked for genuine Gemini analysis; enable them explicitly for those demonstrations. API clients must send false explicitly because omitted `local`/`cache` fields default to true in the request schema. Public OpenAPI/docs and internal evaluation/configuration/cache-management endpoints are disabled.

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
Invoke-RestMethod http://127.0.0.1:8000/api/portfolios/4/exposure
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/ask -ContentType application/json -Body '{"question":"Count all portfolios","local":false,"cache":false}'
```

`/api/ask` is independent; `/api/conversation` accepts a returned opaque session ID for bounded context. A configured token uses `Authorization: Bearer <token>`. The existing access-code dialog appears only when needed. CLI `serve --host` outside loopback requires `PORTIQ_DEMO_TOKEN`; anonymous module mode does not relax this CLI guard.

## Docker and hosted demonstration

```powershell
docker build -t portiq:0.2 .
docker run --rm --name portiq-demo -p 127.0.0.1:8000:8000 portiq:0.2
```

The credential-free non-root container initializes its database and serves deterministic views. Model questions fail cleanly without a key. For AI, supply a private runtime env file with `GEMINI_API_KEY` plus either `PORTIQ_DEMO_TOKEN` or explicit `PORTIQ_ALLOW_ANONYMOUS=1`. Never bake secrets into the image. UID 10001 needs write permission on a retained `/app/runtime` volume.

[render.yaml](../render.yaml) configures the public [Render demo](https://portiq-b9u7.onrender.com) with anonymous opt-in, wildcard accepted hosts and adaptive pacing. Health uses `/api/health` (GET/HEAD). Keys stay in runtime secrets; a configured token still applies. A single process supports bounded concurrent analyses. The separate [production profile](ENHANCEMENTS.md#production-deployment-profile) is an explicit operator choice, not a change to the anonymous demo. Hosting startup/redeploy behavior is outside the CLI assessment.

Reports, evaluation fixtures, `.env` and developer files are excluded from the image; run live evaluations from the repository, not the web-only image. Source CSVs/schema are bundled for initialization and are public on GitHub. Removing website pages does not make those repository copies private.

## Key-free validation

Use the checks in [README](../README.md#key-free-verification). CI covers Python 3.11/3.13 on Ubuntu/Windows plus real Playwright/container checks, using runner Python and pinned uv from PyPI. It does not spend Gemini quota. See [security](SECURITY.md), [data assumptions](DATA_ASSUMPTIONS.md), [limitations](KNOWN_LIMITATIONS.md) and [change history](CHANGELOG.md).
