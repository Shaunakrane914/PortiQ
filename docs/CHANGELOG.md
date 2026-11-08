# Change history

## Controlled retrieval comparison — 8 November 2026

- Added a native experimental RAG-off control and reproducible paired live-Gemini runner.
- The complete supplied pass tied at 10/10 and 21 calls, with 12.02% more reported tokens
  for RAG; timing and SQL-work scores showed no demonstrated gain.
- Preserved the provider-interrupted repeat and separate failed recovery probe. Corrected
  benchmark completion/timing logic so circuit-blocked, zero-SDK rows cannot masquerade as
  completed model comparisons. No application retrieval default or quota ledger was reset.

## Streamlit workspace alignment — 8 November 2026

- Matched the existing frontend with a shared stylesheet, navy sidebar, ivory/gold accents,
  serif headings, portfolio picker and the same four analytical views.
- Added persistent SQL evidence/metrics, native analyst form, safe text rendering and CSV
  export. Local/cache/context remain explicit choices; no new Gemini calls were needed.
- Added actual-server Playwright coverage for desktop chat, all views/selection/export,
  mobile navigation and injected markup. Streamlit's client error traces are hidden.

## Optional enhancements and evaluator v3 — 8 November 2026

- Added local BM25 metadata retrieval with schema provenance, an optional Streamlit chat,
  bounded concurrent model-client pooling, shared quota reservations and a production
  configuration/Compose profile with liveness/readiness.
- Added correctness-gated SQLite VM-work/query-plan scoring. This does not measure disk I/O.
- Final-answer verification now covers explicit scalar/list/table/exposure formats without
  per-case opt-in, including the false active-portfolio example. Historical scores stay tied
  to evaluator v2 and are not silently upgraded.
- Fixed shortcut CLI help/global flags and made local/context modes explicit. Corrected
  deleted-report links and removed instructions for deleted helper scripts.
- Preserved the first supplied CLI run's 8/10 verifier-format failure, added percentage-header
  support and recorded a separate complete 10/10 run with 21 SDK calls and 54,075 tokens.
  The optional GUI launcher forwards global configuration and uses the navy/ivory/gold palette.

Source tags, original assessment inputs, frozen suites and captured evaluation reports are not rewritten. The [pre-cleanup snapshot](https://github.com/Shaunakrane914/PortiQ/tree/ace58054c7a778817d68a7c1d81386b7dffd95e8) retains removed experiments and detailed development evidence.

## Adaptive sliding-window quota controller - 8 November 2026

- Replaced rigid, fixed-interval SDK sleeps (`PORTIQ_REQUEST_INTERVAL`) with an adaptive sliding-window quota controller (`AdaptiveRateLimiter`) tracking actual Gemini attempts in a 60-second rolling window.
- Set an application safety cap of 12 RPM under Google's 15 RPM free tier limit with a default 0.0s artificial delay, reducing live two-turn agent response latency on Render from ~11s down to ~1.8–2.6s.
- Eliminated artificial pacing between internal tool execution steps (SQL generation and response synthesis) within the same user question.
- Introduced a gentle 1.5-second cooldown before starting a new question when usage approaches the quota ceiling (>= 8 attempts in 60s).
- Implemented exact capacity recovery calculation and fail-fast behavior: returns an immediate HTTP 429 with `Retry-After` when recovery exceeds 10.0 seconds, preventing worker thread stalls and UI freezes.
- Updated `render.yaml` and `.env.example` defaults (`PORTIQ_REQUEST_INTERVAL=0`, `PORTIQ_RPM_LIMIT=12`).
- Added comprehensive unit and integration test coverage for all rate limiter state transitions in `tests/test_quota_policy.py`.

## Documentation alignment - 8 November 2026

- Reorganized the run guide and reviewer checklist around the assignment's four required CLI components.
- Separated the supplied ten questions from the optional author-created fifty; current and historical scores retain their actual capture revisions.
- Documented file-backed SQLite versus the brief's in-memory setup hint, current SDK/install metadata and implemented/deferred optional enhancements.
- Reconciled public Render demo, anonymous/token behavior, CLI/module network guards, container defaults and local versus provider quota accounting.
- Updated architecture for compact context/direct scalar rendering and clarified performance, narrative and production-readiness limits.
- Kept the original assignment and all raw captured evidence unchanged. This documentation pass is not a new Gemini evaluation.

## CI bootstrap - `84d296a`

Repeated GitHub Release HTTP 504 responses prevented `setup-uv` from reaching the tests on Windows and Linux. CI now selects runner Python with `actions/setup-python@v6` and installs pinned `uv==0.11.26` from PyPI. All four Python/OS matrix jobs and the browser/container job remain; matrix fail-fast is disabled. All five jobs passed on this commit. Failed Actions history was later removed at the owner's request, independently of model-evaluation reports.

## CLI evidence publication - `3fd4cab`, `6ae3355`

Published the complete [CLI-only 50-question capture](../reports/cli-2026-11-08/README.md): 50/50, 92 actual SDK invocations, 201,404 reported tokens and zero provider errors on source `4b49d95`. It includes complete answers, SQL, independent references, per-question metrics, transcript, immutable hashes and data audits. Scoped attributes preserve exact original CRLF/transcript bytes. Publishing the evidence did not run the model again.

## Model requests - `4b49d95`

Compacted schema formatting and repeated instructions while retaining the original orchestrator. Supported scalar-only requests can directly render one successful, non-truncated SQL cell after genuine Gemini generation. Multiple tools, guarded compound language and other shapes retain normal synthesis. Metadata discloses rendering and actual SDK/token use. No rolling-minute Gemini scheduler was retained. The later full CLI capture showed no regression on its frozen fifty, without establishing unseen accuracy or a general inference-time speedup.

## Frontend and hosted demonstration

Made AI Analyst the landing page and retained Overview, Portfolio Explorer and Reconciliation. Removed internal evaluation/configuration/status pages/routes, public schema discovery, assessment branding and the aggregate AUM card whose currency basis was unspecified. Browser errors are sanitized; local/cache/model modes stay visible. Applied navy, ivory and gold.

Added the optional Render blueprint and public review demo, explicit anonymous network opt-in, cloud health-check host handling and GET/HEAD health support. Later changes accept matching hostnames for TLS proxy origins and default the UI's local/cache checkboxes off; browser smoke tests enable those modes explicitly when testing them. This is not production multi-user identity or availability. The repository remains public by the owner's choice; website cleanup does not hide GitHub data/history.

## Consolidation after v0.2 experiments

Cleanup `122dee6` removed the unsuccessful experimental planner and selected development artifacts, and merged deterministic rendering into `agent.py`. Follow-ups reject its removed strategy rather than silently substituting another. Container startup lives in `api.py`; Docker uses `python -m portiq.api`. Tool/cache benchmarking is consolidated in `scripts/benchmark.py`; engineering/requirement notes are consolidated in the current documentation.

## Historical v0.2 platform work

Added shared analytics/reconciliation, explicit local capabilities, exact caching, bounded context, actual SDK accounting, local quota/retry/circuit/fallback controls, optional FastAPI/static UI and non-root Docker verification. Original-path captures passed 10/10 supplied, 50/50 extended and 8/8 platform. The experimental path passed 9/10, 50/50 and 7/8, including a Technology projection mismatch and an ambiguous portfolio guess; it was not promoted. Provider-outage failures and reporting caveats remain archived separately.

## v0.1.1

Corrected Passive/status semantics with database-derived categorical domains, strengthened result/routing/narrative scoring and preserved historical failures. Archived results: 10/10 supplied, 50/50 extended, 6/6 categorical and 3/3 ambiguity. Its 148 ordinary tests, 94.04% coverage and four CI jobs describe that release, not current verification.

## v0.1.0

Delivered the CLI Gemini agent, read-only SQL tool, Decimal exposure calculator and independent evaluator. Its ext-02 failure was wrong-column semantics and a false narrative, not merely an extra tool call. Later diagnostics corrected the interpretation without altering original reports or tags.
