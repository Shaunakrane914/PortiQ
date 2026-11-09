# New-key verification captures — 9 November 2026

**Current extended result: [50/50 passed after retries](../completion-2026-11-09/README.md).**
The completion report includes the original evaluation, recovery and requested confirmation:
54 executions, 102 SDK attempts, 217,421 reported tokens and 865.927 seconds of summed
capture time. All raw capture outcomes remain unchanged. The retry-aware summary links
each final answer to its source and independently verifies it against the original rules.

This directory retains the new-key captures on the unchanged runtime from `2a68b74`
through `a29d1c0`, Gemini `gemini-3.1-flash-lite` and evaluator v4. No runtime changes were
required. The latest confirmation and full metrics are in the linked completion report.

| Check | Result or scope | Evidence |
|---|---|---|
| Supplied CLI, fresh generation | 10/10; 21 SDK attempts; 48,292 reported tokens | [JSON](supplied-first/supplied.json), [manifest](supplied-first/run-manifest.json) |
| Extended CLI capture | Original full evaluation, with provider metrics and per-case outcomes | [JSON](extended-first/extended.json), [manifest](extended-first/run-manifest.json) |
| Earlier recovery | 2/2; 4 SDK attempts; 9,307 reported tokens; included in completion accounting | [JSON](provider-recovery.json), [manifest](provider-recovery-manifest.json) |
| Real concurrent hybrid conversations | 9/9; three users, three turns each; 22 SDK attempts; 40,972 reported tokens | [Capture](live-conversations.json) |
| Dashboard and Streamlit, actual Gemini | 2/2; local/cache disabled; visible SQL and correct answers | [Results](live-browser-summary.json), [dashboard](dashboard-live.json), [Streamlit](streamlit-live.json) |
| Non-live browser checks | 11 passed; live-only case separately exercised | [Summary](browser-summary.json) |
| Python 3.14 suite | 282 passed; opt-in live case separately passed; lint/format/types pass | [Quality](quality-summary.json) |
| Isolated Python 3.11 suite | 281 passed; live and optional GUI skipped | [Quality](quality-summary.json) |
| Opt-in live pytest | 1 passed, 282 deselected; two genuine SDK attempts | [Capture-time analysis](analysis.json) |
| 60-second HTTP/stub soak | 1,225 requests: 613 correct accepted answers, 612 controlled overload responses; recovery/shutdown pass | [Summary](http-soak-summary.json), [full compressed capture](http-soak.json.gz) |
| Production-profile Docker | All 16 checks pass; zero provider calls | [Capture](production-container.json) |
| Original exercise integrity | All 13 supplied files byte-identical | [Audit](original-assignment-integrity.json) |

Both CLI captures use fresh 603-row databases, unchanged original/frozen inputs, full-schema
context, no RAG, no fallback, no local routing and no cache. Manifests verify runtime/input/
database integrity. Capture-time analyses and provider errors retain their recorded scope;
new completion totals live in their own summary rather than overwriting the original files.

Six provider-error attempts have unreported usage. The local daily guard and retained ledger
were not reset. Reported tokens are not complete billing totals or Google's quota balance.

The first two browser setup attempts used an incorrect temporary working directory;
correcting the test harness cwd resolved startup. Passing checks emitted Windows asyncio
connection-reset callbacks during teardown, a Starlette TestClient deprecation and one
sqlite ResourceWarning. Summaries retain those observations. Single-process behavior is
verified; distributed deployment, hours of provider load and availability SLAs are unverified.

[SHA-256 manifest](artifact-sha256.json) protects the original 25 evidence artifacts.
[Integrity audit](integrity-audit.json) verifies earlier capture hashes and scans artifacts
for credentials and local user paths. The complete stub capture is gzip-compressed with
its original byte hash retained. Published dashboard session capability is replaced with
SHA-256. The newest confirmation has its own [manifest](../completion-2026-11-09/artifact-sha256.json).
