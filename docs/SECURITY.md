# Security boundary and public demo

The assignment lists SQL safety, input validation, error handling and logging as optional enhancements. These are implemented, while the service remains an assessment/demo application. SQL safety does not certify semantic correctness or production multi-tenant isolation.

## SQL and tool boundaries

1. Typed tool arguments reject extra keys, wrong types and oversized values.
2. SQLGlot requires one SQLite read query and rejects mutations, administrative statements, recursive CTEs, attached/internal/pragma tables and other unsupported constructs.
3. SQLite's authorizer independently allows application-table reads and an explicit set of analytical functions. File/extension functions, arbitrary unknown functions and allocation-heavy blob functions are denied.
4. Query connections use a read-only URI, `query_only=ON` and disabled extensions.
5. SQL size/depth, compound queries, value length, row counts and VM execution time are bounded. Fetching has a 1 MB value budget; truncation is explicit and cannot pass evaluation.
6. Portfolio resolution and fixed queries use bound parameters. Generated SQL can contain escaped literals, but never gains write privileges because a model emitted it.

The model has no file/shell tools. Initialization checks resolved destination paths so an explicit rebuild cannot overwrite original assessment inputs. Tests deliberately supply malicious generated SQL and verify database bytes remain unchanged. The SQLite boundary enforces read access independently of prompt obedience.

The progress callback bounds VM work, not every native allocation or parser step; this is not an OS sandbox. The model can still choose a valid wrong-column query or misstate a valid result. Independent reference scoring and authoritative tool tables address a different boundary from SQL authorization.

## Credentials and model data flow

Keys come from process environment or a local `.env` and use `SecretStr`, excluded from settings serialization/repr. `.env`, local databases, logs and development environments are ignored. Transport exception text is not returned verbatim because URLs/payloads may contain credentials. Verbose operation logs keep SDK/HTTP transport loggers disabled and do not expose hidden reasoning.

Gemini receives schema/catalogue/domain context, user questions and necessary tool results. It does not receive the application key in its prompt. Evaluation reports intentionally contain frozen benchmark questions, model answers, SQL and results; they do not embed runtime credentials. Ordinary browser conversations are ephemeral and are not automatically written to those reports. Users should avoid entering personal/confidential information into the public demo; its UI discloses the Gemini data flow.

## Local API controls

FastAPI accepts strict typed JSON, rejects extra fields and bounds POST bodies to 16 KiB, including chunked bodies. POST requests require JSON. Demo-mode Origin validation accepts an exact base/allowlisted origin or a hostname match to the base URL/Host header to support TLS-terminating proxies. That demo hostname fallback does not strictly compare scheme and port. Production mode requires exact origins. Configured CORS origins must be explicit; wildcard CORS is rejected. A configured bearer token uses constant-time comparison. Browser-facing validation/provider/filesystem errors are sanitized; request IDs support troubleshooting.

The API rate limiter uses actual socket clients and ignores forwarded-client headers. Behind a proxy, clients can share a socket identity/limit. A bounded semaphore admits four analyses by default and returns 503/Retry-After when full. Separate reusable model clients share atomic daily accounting and RPM reservations; per-session locks isolate turns. One process is supported. Rate limiting, the circuit and in-memory cache/session state are not distributed controls. A shared SQLite file coordinates daily attempt counts only among compatible processes.

CLI `serve` requires a demo token for a bind address other than `127.0.0.1` or `localhost`. The module/container entry point alternatively permits explicit `PORTIQ_ALLOW_ANONYMOUS=1` for networked model access without a token. A token, if configured, is still checked; the anonymous flag does not disable it. Host wildcard and anonymous-host defaults are described in [configuration](SUBMISSION.md#configuration).

## Hosted frontend and deployment choices

The public [Render demo](https://portiq-b9u7.onrender.com) is configured through [render.yaml](../render.yaml) with anonymous opt-in, wildcard accepted hosts and adaptive pacing. It is a review demonstration, not individual user identity, per-user budgets, audit retention or an availability guarantee. No additional password wall is imposed on ordinary browsing.

The explicit `PORTIQ_ENV=production` profile requires a >=32-character existing bearer token,
explicit hostnames and a persistent quota ledger. It uses exact origin matching; public HTTPS
origins must be allowed explicitly behind TLS proxies. The separate hardened
[Compose recipe](../compose.production.yaml) retains runtime data, drops capabilities and
uses a read-only root filesystem. TLS, token rotation, backups and monitoring remain operator
responsibilities; see [deployment scope](ENHANCEMENTS.md#production-deployment-profile).

The four views are AI Analyst (landing page), Overview, Portfolio Explorer and Reconciliation. Assessment branding, Evaluation Lab, System Status and internal configuration/report pages are removed. `/api/about`, `/api/evaluation/summary`, cache-management and public OpenAPI/docs routes are unavailable. Static serving is restricted to `web/`; `.env`, assignment documents, reports and project files are not served by those routes.

The dashboard constructs data with `textContent` and DOM/SVG nodes. Same-origin CSP assets, no external chart CDN and tests with malicious labels reduce frontend injection risks. CSV downloads neutralize spreadsheet formula prefixes. Opaque session IDs are bearer capabilities, not user accounts; possession permits access to that in-memory session. A configured demo token is shared access, not per-user authorization.

The repository intentionally remains public. Source CSVs and historical reports are accessible there independently of website routes. Frontend cleanup does not make those copies private. A bounded scan found no email addresses, user-machine paths or API-key patterns in the supplied CSVs; this is not a guarantee for future data. New CLI evidence was also scanned before publication.

Docker runs as UID/GID 10001. The image excludes `.env`, local databases, reports, evaluation fixtures, Node modules and development files, but bundles source CSVs/schema for initialization. Keys belong in runtime environment/secret storage. Persisting the daily ledger requires writable retained storage; ephemeral redeploys can reset a container-local ledger. The local counter is not a project-wide provider quota or billing control.

See [limitations](KNOWN_LIMITATIONS.md), [evaluation scope](EVALUATION.md) and the [assignment checklist](SUBMISSION.md#assignment-requirements) for the claims that are deliberately not made.
