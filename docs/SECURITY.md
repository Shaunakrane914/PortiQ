# Security boundary

Threats covered locally include generated SQL mutation, multiple statements, administrative
operations, arbitrary function calls, schema/file reads, recursive queries, untrusted names,
oversized inputs, slow joins, malformed model output and credential disclosure in transport errors.

Layers:

1. Typed tool arguments reject extra keys, wrong types and oversized values.
2. SQLGlot requires one SQLite query; DDL, DML, INTO, administrative statements, recursive
   CTEs, attached databases and SQLite internal/pragma tables are rejected.
3. SQLite's prepare-time authorizer independently allows application-table reads and an
   explicit set of analytical functions. Unknown functions are denied, including extension,
   file, randomblob and zeroblob functions.
4. Every application query runs with a read-only URI, `query_only=ON`, and extensions disabled.
5. SQL size, expression depth, compound query count, value length, result rows and SQLite
   execution time are bounded. Results are fetched incrementally with a 1 MB value budget.
   Truncation is explicit and cannot pass evaluation. Initialization rejects destinations
   that would overwrite original assessment inputs, including through resolved paths.
6. Exposure resolution uses parameterized IDs and whole-token matching; names never become SQL.

Generated analytical SQL may contain correctly escaped literals; the model has no write
capability even if it misquotes a user input. Deterministic queries use bound parameters.
This makes the SQLite boundary, rather than instruction obedience, responsible for preventing
mutation. Prompt injection tests deliberately force malicious model SQL and verify file bytes
remain unchanged.

API keys are environment-only `SecretStr` values, excluded from serialized settings and repr.
SDK error text is never returned directly because URLs/payloads can carry credentials.
Verbose logging leaves transport loggers disabled. `.env` and database/log artifacts are ignored.
The model receives schema, questions and tool results, never application credentials.

Limits: this is a local analyst tool, not a hostile multi-tenant SQL sandbox. The SQLite
progress callback bounds VM execution, not every possible native allocation or parser step.
Deployments serving untrusted users should add process isolation, memory/CPU limits,
authentication, per-user budgets and audit retention. A generated narrative can still
misstate a valid result; displayed structured evidence is authoritative, and narrative
faithfulness is not automatically established by SQL result scoring.


## Optional platform boundary

FastAPI accepts bounded typed JSON and rejects extra fields, oversized or chunked bodies above 16 KiB and unsafe origins. Explicit CORS and trusted-host configuration is required outside local use. A configured bearer token is checked with constant-time comparison. Request IDs accompany responses; raw validation input, provider payloads, keys and exception strings are not logged or returned.

The application ignores forwarded-client headers and rate-limits actual socket clients with bounded limiter state. A semaphore admits one analytical request at a time; use one server worker. Rate limiting and the circuit are not distributed security controls. Daily request reservations can be shared atomically through a configured SQLite ledger; conflicting process settings are unsupported.

The dashboard constructs data with `textContent` and explicit DOM/SVG nodes. CSP restricts application assets to the same origin; no inline script or external chart CDN is needed. Browser tests inject malicious database labels and verify they remain literal text. Downloaded CSV values neutralize spreadsheet formula prefixes. Internal evaluation, configuration and cache-management routes are not exposed by the web app.

Cached successes are deep-copied and keyed by data/code/model/strategy/context identity; no failures are retained. Opaque random session IDs separate bounded in-memory conversations. Anyone holding such a capability can use that session; a demo token does not create per-user identity. A public multi-user service requires real authentication/authorization and per-user quotas.

Docker runs as UID 10001 and excludes `.env`, development environments and local artifacts. Credentials belong only in runtime environment or a managed secret store. Neither the Gemini key nor conversations are embedded in reports. No public production deployment is represented by the container smoke check.


## Public frontend review

The public UI has four views: Overview, Portfolio Explorer, AI Analyst and Reconciliation. Assessment branding, Evaluation Lab, System Status, report provenance, local machine paths and runtime configuration are removed. `/api/about`, `/api/evaluation/summary`, cache-management routes and `/openapi.json` return 404. Static serving is restricted to `web/`; assessment documents, reports, `.env` and project files are not served. Browser errors redact provider/configuration/filesystem details; CLI diagnostics remain actionable locally.

A scan of the supplied CSVs found no email addresses, local-user paths or API-key patterns. This is a bounded check, not a certification of every future dataset. The demo intentionally displays portfolio records. Questions and necessary tool results for AI analysis go to Google Gemini; the UI discloses that data flow. Avoid submitting personal/confidential questions to a public demo.

The owner chose to keep GitHub public and avoid adding a password wall to ordinary browsing. Existing optional demo-token and networked-model controls are retained. Public GitHub data/history remains accessible independently of website routes; frontend changes do not make those copies private. Reports and evaluation fixtures are excluded from the web Docker image. Keep container images private if their embedded source data must not be redistributed. No public hosting has been performed by this change.
