# New-key retest — 9 November 2026

The newly configured private Gemini credential works. The previously quota-blocked
three-user conversation protocol now completes **9/9 correct answers**, including
session-bound follow-ups. The fresh supplied CLI evaluation passes **10/10**.

The full extended CLI run scored **48/50**. Two requests failed after Gemini HTTP 504s;
both passed a separate **2/2 recovery check**. That retry is not combined into a claimed
clean full 50/50 score. No runtime changes were required. Captures use runtime source
[`2a68b74`](https://github.com/Shaunakrane914/PortiQ/commit/2a68b74e6756071badccd9d00a83e9031cb82318),
Gemini `gemini-3.1-flash-lite` and evaluator v4. Current documentation changes do not
alter that runtime. [Analysis](analysis.json) records exact timing and usage scope.

| Check | Result | Evidence |
|---|---|---|
| Supplied CLI, fresh generation | 10/10; 21 SDK attempts; 48,292 reported tokens; all ten final-answer checks pass | [JSON](supplied-first/supplied.json), [manifest](supplied-first/run-manifest.json) |
| Extended CLI, fresh generation | 48/50; 94 SDK attempts; 198,790 reported tokens; all three hybrids pass | [JSON](extended-first/extended.json), [manifest](extended-first/run-manifest.json) |
| Separate provider recovery | 2/2; 4 SDK attempts; 9,307 reported tokens; no provider errors | [JSON](provider-recovery.json), [manifest](provider-recovery-manifest.json) |
| Real concurrent hybrid conversations | 9/9; three users, three turns each; 22 SDK attempts; 40,972 reported tokens | [Capture](live-conversations.json) |
| Dashboard and Streamlit, actual Gemini | 2/2; local answers/cache disabled; visible SQL and correct answers | [Results](live-browser-summary.json), [dashboard](dashboard-live.json), [Streamlit](streamlit-live.json) |
| Non-live browser checks | 11 passed; one live-only case separately exercised above | [Summary](browser-summary.json) |
| Local Python 3.14 suite | 282 passed; live-only case skipped here and separately passed; lint/format/types pass | [Quality summary](quality-summary.json) |
| Isolated Python 3.11 suite | 281 passed; live and optional GUI cases skipped | [Quality summary](quality-summary.json) |
| Opt-in live pytest | 1 passed, 282 deselected; two genuine SDK attempts | [Analysis](analysis.json) |
| 60-second HTTP/stub soak | 1,225 requests: 613 correct accepted answers, 612 controlled overload responses; recovery/shutdown pass | [Summary](http-soak-summary.json), [complete compressed capture](http-soak.json.gz) |
| Production-profile Docker | All 16 checks pass; zero provider calls | [Capture](production-container.json) |
| Original exercise integrity | All 13 supplied files byte-identical | [Audit](original-assignment-integrity.json) |

## Failure, recovery and usage accounting

`ext-12` (holdings counts by portfolio) and `ext-13` (portfolios holding AAPL) exhausted
their bounded provider retries and returned structured errors. `ext-26` and `ext-41`
encountered one transient provider failure each but recovered within the same request.
The original full run exits 1 and retains all fifty outcomes. It contains 44 successful
explicit data-answer checks, four successful handling cases and two provider failures.
No generated factual answer failed verification in this run; this does not convert its
strict score into 50/50 or establish unseen-question accuracy.

All six failed SDK attempts have unreported usage. Reported tokens are therefore partial
accounting, not a complete billing total. The separate live pytest assertion does not
collect token metadata and is excluded from token totals. The retained daily ledger
advanced from 0 to 146 SDK attempts across all genuine checks; the existing configured
1,000-attempt local guard was unchanged. This is not Google's remaining quota meter.

Both full CLI captures use fresh 603-row databases, unchanged original/frozen inputs,
full-schema context, no RAG, no fallback model, no local routing and no answer cache.
Their manifests verify source/input/database integrity. The recovery capture selects only
the two transient-provider failures from the original extended suite, with that original
capture's hash recorded. Older [failed and incomplete captures](../assurance-2026-11-09/README.md)
remain unchanged and are not merged into any current score.

## Timing, performance and operational scope

The supplied CLI took 175.066 seconds of wall time; mean/p95 question times were
17.192/24.081 seconds. The extended CLI took 824.228 seconds; mean/p95 were
16.439/47.091 seconds, including provider failures and retries. These batch runs and the
real HTTP protocol use child-only 6.5-second SDK spacing. Normal application pacing was
not changed. Provider service, pacing and backoff totals are separately retained.
This retest is not a controlled latency or cost comparison with older captures.

Both CLI runs profile generated/reference SQLite pager hits plus misses on matched fresh
private connections. Correctness-gated mean page-work scores were 100 supplied and 92.85
extended; a wrong or missing answer cannot earn a performance pass. VM counts/query plans
remain recorded. These are logical page accesses, not physical device I/O or optimality proof.

The real HTTP protocol lasted 155.569 seconds and passed identity/answer checks for all
nine hybrids, stable per-user sessions, bounded clients, accounting and clean shutdown.
Its 40.901/61.593-second HTTP p50/p95 include shared batch pacing and concurrent queueing;
they are not standalone model-inference latency. No quota responses occurred.

The separate 60-second HTTP soak uses an explicit 100 ms deterministic SDK stub: zero
real provider calls, all accepted responses correct, capacity four with eight actors,
controlled `503 Retry-After: 1`, readiness responsiveness and post-load recovery. Its
402.75 ms overall p95 is not a Gemini latency measurement. Docker verification uses a
disposable test ledger and no real key, checking authentication/origins/body limits,
readiness, file exclusions, UID 10001, read-only root, dropped capabilities, resource
bounds, retained usage across restart and clean shutdown.

The first two browser setup attempts timed out because the temporary test configuration
resolved its server working directory under `reports/local`. Explicit repository cwd
fixed the harness; the original database was intact. Passing browser cases also emitted
Windows asyncio connection-reset callbacks during teardown. Local tests emitted a
Starlette TestClient deprecation and one sqlite ResourceWarning; checks still exited 0.
These observations are retained in the summaries rather than hidden.

One application process with bounded concurrent analyses remains the supported topology.
Hours of real-provider load, distributed coordination, externally operated TLS/monitoring
and availability SLAs are not established by this retest. See [operations](../../docs/OPERATIONS.md).

## Capture integrity

[SHA-256 manifest](artifact-sha256.json) covers the raw and derived evidence files, excluding
this index, attributes and the manifest itself. The full stub capture is gzip-compressed
without changing its uncompressed bytes; its summary records the original byte hash.
Dashboard session capability is replaced with its SHA-256 in the published copy; the
original capture stays under ignored local reports. Summaries omit machine-specific paths.
[Integrity audit](integrity-audit.json) checks prior published capture hashes and scans new
artifacts for the configured key, credential-shaped text and local Windows user paths.
Capture timestamps use UTC; this directory uses the local India date.
