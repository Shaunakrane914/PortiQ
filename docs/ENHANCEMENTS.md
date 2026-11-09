# Optional assignment enhancements

Eleven of the twelve optional bullets have active implementations. Metadata RAG was
evaluated and deliberately excluded based on measured tradeoffs. The core CLI continues
to work without Streamlit, FastAPI, Node or a browser.

| Enhancement | Implementation and evidence |
|---|---|
| Parameterized SQL | CSV inserts, portfolio lookups and fixed analytical filters bind values. Model-generated SQL is parsed, authorized and executed read-only; it is not universally parameterized. |
| Query validation | SQLGlot, a SQLite authorizer, function allowlist, read-only connections, row/byte/time limits. See `tests/test_sql.py`. |
| Database error handling | Expected errors become safe CLI/API failures; invalid or ambiguous portfolios do not become guessed results. |
| Logging | Request IDs, status, tool names, SDK counts and durations; no questions, credentials or SDK payloads in operational logs. Use CLI `--verbose`; the API module enables INFO logs. |
| Input validation | Strict typed tool and API schemas, question/body limits and explicit errors. |
| Caching | Bounded TTL/LRU exact answers, isolated by session, model/configuration, runtime source and database version. Failures are not cached. CLI/UI opt-in; evaluator disabled. |
| Streamlit GUI | `uv sync --extra gui`, then `uv run --extra gui portfolio-agent gui`. Matches the existing four-view workspace using the shared dashboard stylesheet plus a native-widget adapter. Genuine model analysis is the default; local/cache/context controls are explicit. |
| Metadata RAG | Evaluated and excluded from the active submission. BM25 added 12.02% reported tokens without demonstrated accuracy/latency benefit; graph retrieval scored 9/10 versus 10/10. Full-schema prompting remains. See the [decision and archives](ENGINEERING_NOTES.md#metadata-retrieval-evaluated-and-excluded). |
| Production REST API | Explicit production profile, bounded input/concurrency, safe errors, request logs, readiness/liveness, existing bearer authentication, strict production origins/hosts, retained quota storage and a hardened Compose deployment. Deployment verification and limits are described below. |
| Concurrent users | A bounded reusable model-client pool, per-conversation turn locks and shared atomic daily/RPM guards permit independent conversations to overlap. Default capacity four. Tests synchronize two simultaneous fake provider calls and verify separate results, sessions and per-request metrics. |
| Performance-aware evaluation | VM-work scoring and query plans remain available. Optional `--profile-io` uses the performance extra to measure actual SQLite pager hits + misses on matched fresh-cache queries; incorrect answers receive zero. Engine/cache policy and limits are recorded. See [operations](OPERATIONS.md#performance-aware-evaluation). |
| Hybrid questions | Both tools execute within one request; evaluator v4 separates sector-percentage claims from SQL scalars and supports value-before-sector phrasing. Historical replays plus wrong/missing/negated claim tests cover the regression. |

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

The [operations guide](OPERATIONS.md) documents the supported single-process topology,
readiness dependencies, overload/recovery, shutdown, backups and actual-HTTP verification.

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

`GET /api/live` reports process liveness. `GET`/`HEAD /api/ready` checks all nine analytical
tables and quota storage; `/api/health` checks the portfolio table. Dependency failures
return 503 without revealing model/key configuration. Four
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

The [new-key retest](../reports/retest-2026-11-09/README.md) records 282 local tests, fresh
supplied v4 CLI 10/10, a completed nine-answer real three-user hybrid protocol, a 60-second
HTTP/stub soak and all 16 production Docker checks. Browser verification includes actual
dashboard and Streamlit servers. Earlier failed/quota-interrupted runs remain in the
[previous evidence](../reports/assurance-2026-11-09/README.md). This is verified single-process
behavior, not distributed/SLA proof.

The fresh extended v4 run scored 48/50, with all three hybrid cases passing. Two requests
failed on provider HTTP 504s; both passed in a separate 2/2 recovery check. Six SDK errors
had unreported usage. Neither the retries nor the old offline replay are combined into a
claimed clean fresh 50/50 run.

`tests/test_enhancements.py` checks query work, rate reservations, simultaneous
requests, overload recovery, production settings and an actual Streamlit AppTest session.
The platform CI job installs the GUI extra and runs these checks before browser/container
verification. No fake provider test is reported as a live Gemini accuracy run.
Three additional Playwright cases exercise the actual Streamlit server, including mobile
sidebar navigation, portfolio selection, local chat, export and injected-markup handling.

Final-answer verification and current live evidence are documented in
[evaluation methodology](EVALUATION.md). Historical reports retain their original evaluator
version and score; they are not retroactively certified under the stricter contract.

## Measured retrieval value

The [archived paired live comparison](https://github.com/Shaunakrane914/PortiQ/blob/d65927b2e59e07c76ff3795e1395c0724a439241/reports/rag-ablation-2026-11-08/README.md) kept the complete
schema and every generation/tool/evaluation setting fixed while removing only the retrieved
block in the control condition. Its complete, error-free supplied pass scored 10/10 with
21 SDK calls in both modes. Reported tokens increased from 48,271 to 54,074 (+12.02%). Mean
SDK service was 4.961 versus 5.348 seconds, but the uncertainty interval crossed zero.
No accuracy, call-count, SQL-work-score or reliable latency improvement was demonstrated.

The repeat was interrupted by provider 504s and circuit blocking, including a failed minimal
recovery probe. Those rows are preserved and are not reported as complete model comparisons.
The archived runner stops on an open circuit and rejects zero-call rows as completed
comparisons. Both retrieval implementations, their controls and experiment-specific tests
were subsequently removed from the active codebase. The agent now always receives the full
schema without RAG. No embeddings or larger-corpus benefits were measured. See the
[engineering decision](ENGINEERING_NOTES.md#metadata-retrieval-evaluated-and-excluded) for
both experiments and their archive branches.

Implementation references: [SQLite progress callbacks](https://www.sqlite.org/c3ref/progress_handler.html),
[Streamlit chat](https://docs.streamlit.io/develop/api-reference/chat) and
[FastAPI deployment concepts](https://fastapi.tiangolo.com/deployment/concepts/).
