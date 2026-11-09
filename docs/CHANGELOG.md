# Change history

## New-key retest — 9 November 2026

- Completed the previously quota-blocked live protocol: three users, three hybrid turns
  each, all nine answers correct with stable isolated session context and no quota responses.
- Fresh v4 CLI supplied run passed 10/10. The fresh extended run scored 48/50; two
  provider-timeout failures passed a separate 2/2 recovery check. Original failures and
  unknown usage remain recorded; the retry is not presented as a clean full 50/50 score.
- Rechecked Python 3.14/3.11, lint/format/types, actual dashboard/Streamlit browsers including
  real Gemini answers, the 60-second HTTP/stub soak, all 16 production Docker checks and
  original-assignment integrity. No runtime changes were required.
- Refreshed the evidence index and current limits, corrected an archived RAG link and the
  reviewer verification anchor. [Retest captures](../reports/retest-2026-11-09/README.md)
  preserve the earlier historical evidence rather than replacing it.

## Hybrid evaluation and operational verification — 9 November 2026

- Evaluator v4 separates exposure percentages from SQL scalar checks, supports percentages
  before sector names and retains consumed SDK metadata if scoring itself fails.
- Added an optional APSW performance extra and `evaluate --profile-io` for correctness-gated
  SQLite pager-access scoring, with engine/cache metadata and independently verified rows.
- Readiness checks all nine analytical tables and quota storage. Production rejects unsupported
  worker counts; cleanup runs in a lifespan finally block, with bounded shutdown settings.
- Added actual-HTTP soak/live conversation verification and concise reviewer/operations guides.
  Distributed availability and externally operated TLS/monitoring are not claimed.
- Live follow-ups exposed a missing selected-portfolio binding. Explicit selected/current
  portfolio references now resolve through their own session, or clarify without a model
  guess when no selection exists. The first failed live protocol is retained separately.
- Extended replay exposed six valid formats still rejected by the earlier table-only
  contract. Added bound label/value and min/max prose support, with swapped/contradictory
  claim tests, and corrected "sectors with no securities" empty-result detection.
- Final validation: 282 local tests, isolated Python 3.11 checks, fresh supplied v4 10/10,
  final offline replay 50/50 with 46 bad-prose mutations rejected, a passing HTTP soak and
  all 16 production Docker checks. The longer real-provider protocol is quota-interrupted;
  its failed/incomplete captures remain in the [evidence](../reports/assurance-2026-11-09/README.md).

## BM25 retrieval removed from active architecture — 9 November 2026

- Preserved commit `d65927b` on `archive/bm25-rag-2026-11-09`, including the original
  benchmark evidence and reproduction scripts. The graph experiment remains in its archive.
- Removed BM25 runtime integration, response provenance, its retriever, comparison runner
  and retrieval-specific tests. There were no retrieval-only third-party dependencies.
- The agent now uses full-schema context directly. Categorical values, declared relationships,
  portfolio catalogue, financial definitions and SQL safeguards remain unchanged.
- The [engineering decision](ENGINEERING_NOTES.md#metadata-retrieval-evaluated-and-excluded)
  records why both retrieval strategies were rejected. The optional RAG enhancement is
  explicitly marked evaluated and excluded rather than claimed as active functionality.
- Verification passed: 232 core tests, lint/format/types and a fresh supplied CLI **10/10**
  with 21 SDK attempts, 48,293 reported tokens and zero provider errors. The
  [no-RAG capture](../reports/supplied-no-rag-2026-11-09/README.md) is tied to source `0b3e94a`.

## Graph retrieval removed from active architecture — 9 November 2026

- Preserved verified commit `8a6143c` on `archive/schema-graph-rag-2026-11-08`, including
  implementation, tests and all experiment evidence.
- Removed graph runtime integration, its audit script/tests and bulky artifacts from `main`.
  The agent retains full-schema context, basic BM25, SQL validation/repair and financial tools.
- Recorded the correctness/complexity decision in [engineering notes](ENGINEERING_NOTES.md#schema-graph-retrieval-archived).
- Verification passed: 235 core tests, lint/format/types and a fresh supplied CLI **10/10**
  with 21 SDK attempts and zero provider errors. The [post-removal evidence](../reports/supplied-after-graph-removal-2026-11-08/README.md)
  is tied to captured source `f14ea21`.

## Experimental schema-graph retrieval — 8 November 2026

- Added table/column/rule nodes, actual FK traversal for join bridges, conservative fallback
  and response provenance. No graph database, document extraction or additional model calls.
- Offline audit retained required tables for all 10 supplied and 46 extended data questions,
  reducing initial system characters by 33.23% and 24.56% respectively.
- The fresh supplied paired run scored full schema 10/10 versus graph 9/10. Reported tokens
  fell 26.80%; a recovered 504 had unknown usage, and latency showed no reliable gain.
- Preserved the graph's incorrect bond-excluding denominator and all attempts in the
  [archived experiment evidence](https://github.com/Shaunakrane914/PortiQ/blob/8a6143c96d1780f1890ff8d7db1c92cc5dbdd4a8/reports/graph-rag-2026-11-08/README.md).
  The experiment was subsequently removed from the active architecture as noted above.

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
