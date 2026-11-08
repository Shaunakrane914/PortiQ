# Operating the supported deployment

PortiQ supports **one application process**, with up to four concurrent analyses by default.
Each active request borrows a separate model client; they share the process's atomic RPM
reservations and persistent daily ledger. Conversation turns serialize within their own
session. Multiple workers/replicas need external session, rate and capacity coordination;
the production profile rejects `WEB_CONCURRENCY` or `UVICORN_WORKERS` values other than one.
This avoids presenting untested distributed behavior as a supported deployment mode.

## Deploy and verify

Configure a private Gemini key, a random bearer token of at least 32 characters, explicit
allowed hostnames and exact browser origins. Use the existing production Compose recipe:

```powershell
docker compose -f compose.production.yaml config --quiet
docker compose -f compose.production.yaml up --build -d
```

Keep the published port on loopback behind an HTTPS reverse proxy. TLS certificates,
public routing and monitoring are operator responsibilities. The anonymous Render demo
is a separate profile and is not changed by the production settings.

- `/api/live`: process liveness; no provider call.
- `/api/ready`: all nine analytical tables and the quota store are accessible; no provider call.
- `/api/health`: lightweight database health for the dashboard/container.
- Verify missing/invalid tokens receive 401, an allowed authenticated analytical request
  succeeds, and cross-origin requests from unlisted origins receive 403.
- Verify Docker runs as UID 10001, uses a read-only root, drops capabilities and retains
  `/app/runtime` in the named volume. Keep quota storage across restarts.

The server bounds socket concurrency at 128 and model analyses at four. Overload returns
503 with `Retry-After: 1`; provider/local quota exhaustion returns 429 with recovery metadata.
An accepted request can still fail during a later tool-loop call if quota is exhausted.
Provider timeouts/retries remain bounded; never treat a rejected request as a financial answer.
The server allows 45 seconds for graceful shutdown; Compose gives the process 60 seconds.

## Observe, recover and back up

Logs include request ID, route/status, duration and failure type. They omit questions,
credentials and raw SDK payloads. Correlate a browser failure with its request ID. Alert on
readiness failures, sustained 5xx, quota exhaustion and restart loops. Liveness does not
certify model availability; readiness intentionally does not spend Gemini quota.

Before restoring or replacing runtime data, stop incoming analyses and take consistent
SQLite backups with `sqlite3.Connection.backup()` for both portfolio and quota databases.
Store backups privately outside the container, restore into the retained volume while the
service is stopped, then verify readiness and recorded daily usage before accepting traffic.
Do not delete/reset the quota ledger to recover from a quota error. Rotate the bearer token
through private deployment configuration and restart; never publish it in a report.

Reproduce service verification from a clean checkout:

```powershell
uv sync --frozen --extra dev --extra performance
# Real HTTP, explicit deterministic SDK stub, zero provider calls:
uv run python scripts/verify_service.py --seconds 60 --output reports/local/soak.json
# Three real hybrid conversations, three concurrent users, three turns each:
uv run python scripts/verify_service.py --live --output reports/local/live-service.json
```

The live mode spends genuine Gemini quota, keeps the configured daily guard/ledger, disables
local/cache/fallback answers, and uses 6.5-second batch pacing. The nine accepted answers are
checked against independent SQL/CSV references, including follow-ups using session context.
The stub soak measures API capacity, rejection/recovery, readiness and isolation; its times
are not Gemini inference measurements. Output files must be fresh. Neither test establishes
a production SLA, unlimited throughput or distributed availability.

[Measured verification](../reports/assurance-2026-11-09/README.md) records the current soak,
Docker checks and quota-interrupted real-provider attempt with their exact source versions.

## Performance-aware evaluation

```powershell
uv sync --frozen --extra performance
uv run portfolio-agent evaluate --profile-io --output reports/local/supplied-io.json
```

The optional APSW adapter measures SQLite pager cache hits plus misses for each generated
and reference query on separate fresh private connections with the schema preloaded. Query
preparation and execution are counted; result rows must independently agree before scoring.
Both arms use the same APSW/SQLite build, whose version is recorded. Lower page-access work
receives a higher relative score; wrong results or prose receive zero. The original VM-work
counts and query plans remain available. Without `--profile-io`, VM work remains the default.

This is a logical page-access metric, not physical device I/O or SQL Server's exact I/O
accounting. SQLite's [pager counters](https://sqlite.org/c3ref/c_dbstatus_options.html) define
cache hits/misses; [APSW](https://rogerbinns.github.io/apsw/connection.html#apsw.Connection.status)
exposes them. Engine versions, cache policy and the small dataset limit generalization.
