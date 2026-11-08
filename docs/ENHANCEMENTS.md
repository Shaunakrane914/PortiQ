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
| Streamlit GUI | `uv sync --extra gui`, then `uv run --extra gui portfolio-agent gui`. Matches the existing four-view workspace using the shared dashboard stylesheet plus a native-widget adapter. Genuine model analysis is the default; local/cache/context controls are explicit. |
| Metadata RAG | Default BM25 retrieves three live schema documents and appends them to the full context. An experimental schema graph selects tables through real FK paths and prunes initial DDL, with full-schema fallback. This is not Microsoft's document/community GraphRAG pipeline. See [graph retrieval](GRAPH_RETRIEVAL.md) for the method and comparison commands. No embeddings, external corpus or benchmark answers enter runtime retrieval. |
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
uses the navy/ivory/gold palette and honors global CLI database/source/model options,
but each browser conversation has its own opaque session identifier. It is a local optional
interface; the production recipe serves the existing static dashboard and REST API.
AI Analyst, Overview, Portfolio Explorer and Reconciliation share the same portfolio
selector and backend calculations. SQL evidence, SDK/token/timing metrics and reconciliation
CSV export are available in Streamlit. Questions render as escaped plain text; the launcher
hides framework deployment controls and client error traces.

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
Three additional Playwright cases exercise the actual Streamlit server, including mobile
sidebar navigation, portfolio selection, local chat, export and injected-markup handling.

Final-answer verification and current live evidence are documented in
[evaluation methodology](EVALUATION.md). Historical reports retain their original evaluator
version and score; they are not retroactively certified under the stricter contract.

## Measured retrieval value

The [paired live comparison](../reports/rag-ablation-2026-11-08/README.md) keeps the complete
schema and every generation/tool/evaluation setting fixed while removing only the retrieved
block in the control condition. Its complete, error-free supplied pass scored 10/10 with
21 SDK calls in both modes. Reported tokens increased from 48,271 to 54,074 (+12.02%). Mean
SDK service was 4.961 versus 5.348 seconds, but the uncertainty interval crossed zero.
No accuracy, call-count, SQL-work-score or reliable latency improvement was demonstrated.

The repeat was interrupted by provider 504s and circuit blocking, including a failed minimal
recovery probe. Those rows are preserved and are not reported as complete model comparisons.
The runner now stops on an open circuit and rejects zero-call rows as completed comparisons.
`PortfolioAgent(..., use_retrieval=False)` supports the experimental control; application
defaults remain unchanged. For this nine-table dataset, metadata retrieval is functional but
adds redundant context; useful retrieval gains would need evidence from missing knowledge
or larger schemas. No embeddings or larger-corpus benefits were measured here. The separate
[schema-graph experiment](GRAPH_RETRIEVAL.md) tests replacing redundant full-schema context
with connected metadata selection; its results must not be inferred from this basic-RAG run.
Its [fresh live comparison](../reports/graph-rag-2026-11-08/README.md) reduced reported tokens
by 26.80%, but scored 9/10 against the full-schema control's 10/10. Required table coverage
was complete; a financial denominator error remained. No reliable latency gain was shown,
so graph retrieval remains experimental and application defaults remain unchanged.

Implementation references: [SQLite progress callbacks](https://www.sqlite.org/c3ref/progress_handler.html),
[Streamlit chat](https://docs.streamlit.io/develop/api-reference/chat) and
[FastAPI deployment concepts](https://fastapi.tiangolo.com/deployment/concepts/).
