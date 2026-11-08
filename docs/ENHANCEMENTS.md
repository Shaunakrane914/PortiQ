# Optional assignment enhancements

All twelve optional bullets in the original brief have an implementation. The core CLI
continues to work without Streamlit, FastAPI, Node or a browser.

| Enhancement | Implementation and evidence |
|---|---|
| Parameterized SQL | CSV inserts, portfolio lookups and fixed analytical filters bind values. Model-generated SQL is parsed, authorized and executed read-only; it is not universally parameterized. |
| Query validation | SQLGlot, a SQLite authorizer, function allowlist, read-only connections, row/byte/time limits. See `tests/test_sql.py`. |
| Database error handling | Expected errors become safe CLI/API failures; invalid or ambiguous portfolios do not become guessed results. |
| Logging | Request IDs, status, tool names, SDK counts and durations; no questions, credentials or SDK payloads in operational logs. Use CLI `--verbose`; the API module enables INFO logs. |
| Input validation | Strict typed tool and API schemas, question/body limits and explicit errors. |
| Caching | Bounded TTL/LRU exact answers, isolated by session, model/configuration, runtime source and database version. Failures are not cached. CLI/UI opt-in; evaluator disabled. |
| Streamlit GUI | `uv sync --extra gui`, then `uv run --extra gui portfolio-agent gui`. Genuine model analysis is the default; local/cache/context controls are explicit. |
| Metadata RAG | `MetadataIndex` builds documents from live SQLite columns/foreign keys and descriptive metadata. BM25 retrieves three relevant documents for each question and appends them to model context with source IDs. Full schema remains available to preserve join coverage. No embeddings, GraphRAG, external corpus or benchmark answers are claimed. |
| Production REST API | Explicit production profile, bounded input/concurrency, safe errors, request logs, readiness/liveness, existing bearer authentication, strict production origins/hosts, retained quota storage and a hardened Compose deployment. Deployment verification and limits are described below. |
| Concurrent users | A bounded reusable model-client pool, per-conversation turn locks and shared atomic daily/RPM guards permit independent conversations to overlap. Default capacity four. Tests synchronize two simultaneous fake provider calls and verify separate results, sessions and per-request metrics. |
| Performance-aware evaluation | Each generated/reference SQL is separately profiled. A correctness-gated score is `100 * min(1, reference VM work / generated VM work)`; incorrect SQL/answers receive zero. The metric counts SQLite progress callbacks at interval one and records query plans. It is an engine-work proxy, not measured logical page reads. |
| Hybrid questions | Both tools can execute within one request; the extended suite includes three frozen hybrid cases. Existing agent tests cover combined tool execution. |

## Run the interfaces

```powershell
uv sync --frozen --extra dev --extra web --extra gui
uv run portfolio-agent init-db
uv run portfolio-agent chat
uv run --extra gui portfolio-agent gui
# Existing dashboard:
uv run portfolio-agent serve
```

Run `init-db` only for a missing database. Streamlit binds to 127.0.0.1:8501; the existing
dashboard binds to 127.0.0.1:8000. Streamlit shares server-side quota/cache/session services,
but each browser conversation has its own opaque session identifier. It is a local optional
interface; the production recipe serves the existing static dashboard and REST API.

## Production deployment profile

The public Render demo retains its anonymous behavior. Production settings are an explicit
separate choice. Configure private environment variables before running:

```powershell
# Set GEMINI_API_KEY and PORTIQ_DEMO_TOKEN privately; never put real values in documentation.
# The token must contain at least 32 characters.
$env:PORTIQ_ALLOWED_HOSTS = "portiq.example.com,localhost"
$env:PORTIQ_CORS_ORIGINS = "https://portiq.example.com"
docker compose -f compose.production.yaml up --build -d
```

The recipe binds loopback for an operator-managed HTTPS reverse proxy, runs as UID 10001,
uses a read-only root filesystem, drops Linux capabilities and retains `/app/runtime` in
a named volume. Production startup rejects missing/short bearer tokens, wildcard/missing
hosts and an absent persistent quota ledger. Its origin checks use exact origins; TLS
proxy deployments must explicitly allow their public HTTPS origin. The existing access-code
dialog supplies the bearer token when configured; anonymous demo mode is unchanged.

`GET /api/live` reports process liveness. `GET`/`HEAD /api/ready` and `/api/health` check the
portfolio table, return 503 if unavailable and reveal no model/key configuration. Four
analyses can run at once by default; excess requests get 503 with `Retry-After: 1`. Configure
`PORTIQ_MAX_CONCURRENT_ANALYSES=1..32` to change this bound. Provider quota may still reject
concurrent requests; local RPM reservations coordinate the pool and daily attempts share
the configured SQLite ledger.

This profile targets one application process with concurrent requests. Multiple processes
would have separate sessions, RPM reservations and capacity gates even if daily usage
shares a ledger; distributed deployment needs external coordination. HTTPS certificates,
proxy configuration, secret rotation, storage backups and service monitoring are operator
responsibilities. A passing smoke test is not a security certification or availability SLA.

## Validation

`tests/test_enhancements.py` checks retrieval, query work, rate reservations, simultaneous
requests, overload recovery, production settings and an actual Streamlit AppTest session.
The platform CI job installs the GUI extra and runs these checks before browser/container
verification. No fake provider test is reported as a live Gemini accuracy run.

Final-answer verification and current live evidence are documented in
[evaluation methodology](EVALUATION.md). Historical reports retain their original evaluator
version and score; they are not retroactively certified under the stricter contract.

Implementation references: [SQLite progress callbacks](https://www.sqlite.org/c3ref/progress_handler.html),
[Streamlit chat](https://docs.streamlit.io/develop/api-reference/chat) and
[FastAPI deployment concepts](https://fastapi.tiangolo.com/deployment/concepts/).
