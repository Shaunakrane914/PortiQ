# 50/50 passed in one full CLI run — 9 November 2026

**Latest implementation: [50/50 extended, 10/10 supplied and measured interactive latency](../latency-2026-11-09/README.md).**
This page retains the historical capture scope and metrics below.

**All 50 questions passed in this fresh, single full CLI evaluation.** The frozen extended
suite ran once in its original order. All 46 data-answer checks, four handling cases and
three hybrid questions passed. No answers were substituted from earlier captures and no
questions were retried after this run to construct its score.

The unmodified evaluator v4 wrote [the raw result](extended.json) and exited 0.
[Terminal output](cli-stdout.txt), [Markdown results](extended.md) and the
[run manifest](run-manifest.json) retain the complete evidence. The source commit is
`a9f1e67`; the model is `gemini-3.1-flash-lite`. No runtime, prompt, evaluation
criteria or original input changed for this run.

## Single-run metrics

| Metric | Recorded value |
|---|---:|
| Strict question passes | **50/50** |
| Trial count / question executions | 1 / 50 |
| Data-answer checks / handling cases | 46/46 / 4/4 |
| Hybrid questions | 3/3 |
| SDK attempts | 93 |
| Reported tokens | 205,940 |
| Provider-error attempts | 2 |
| Attempts with unreported usage | 2 |
| Full CLI wall time | 747.520 s |
| Mean / p95 question duration | 14.926 s / 28.658 s |
| Provider service / pacing / backoff totals | 431.934 s / 270.691 s / 2.298 s |
| Mean correctness-gated SQLite pager-work score | 98.25/100 |
| Child-process SDK spacing | 6.5 s |

The capture uses a fresh 603-row database, full-schema context and genuine Gemini for every
data question. Local fast paths, answer caching and fallback models are disabled. Provider
attempts reconcile with the retained quota ledger. Normal application pacing and the
configured daily guard were unchanged. Wall time includes batch pacing and evaluation work;
service/pacing/backoff are separate components. Pager accesses are measured on matched
fresh private caches and are not physical device I/O or a general optimizer guarantee.

[Analysis](analysis.json) verifies all fifty IDs, one trial, genuine provider use for all
data cases, every data-answer check, unchanged source/input/database bytes, the original
suite hash, disabled cache/local modes and actual-SDK accounting. This is a known regression
suite, not blind validation or a general correctness guarantee for unseen questions.

## Other verified checks

| Check | Result | Recorded usage |
|---|---|---|
| Supplied CLI | 10/10 | 21 SDK attempts; 48,292 reported tokens |
| Concurrent hybrid conversations | 9/9; three users, three turns | 22 SDK attempts; 40,972 reported tokens |
| Dashboard / Streamlit genuine browser answers | 2/2 | 3 SDK attempts; 6,447 reported tokens |
| Local Python 3.14 | 282 passed; live-only case separately passed | Zero provider calls in this suite |
| Isolated Python 3.11 | 281 passed; live and optional GUI skipped | Zero provider calls |
| Opt-in live pytest | 1 passed | 2 SDK attempts; token metadata not collected |
| Non-live browser cases | 11 passed | Zero provider calls |
| Lint / format / types | Passed; 19 typed source files | Zero provider calls |
| Production Docker checks | 16/16 | Isolated test ledger; zero provider calls |
| HTTP/stub soak | 1,225 requests; 613 correct accepted, 612 controlled overload responses | Zero provider calls |
| Original assignment integrity | All 13 supplied files byte-identical | Zero provider calls |

The HTTP/stub soak passed accounting, bounded sessions/clients, readiness, recovery and
shutdown. Its 402.75 ms overall p95 is a local stub measurement. Real concurrent HTTP
capture wall time was 155.569 seconds with p50/p95 40.901/61.593 seconds including shared
batch pacing. Supplied CLI wall time was 175.066 seconds with mean/p95 17.192/24.081 seconds.
The [earlier capture index](../retest-2026-11-09/README.md) links those raw results. Distributed
coordination, hours of provider load and an availability SLA remain outside verified scope.

## Complete verification-campaign accounting

[Campaign metrics](campaign-metrics.json) include all earlier genuine checks and this fresh
full run: **243 SDK attempts** and **519,072 captured reported tokens**.
The retained daily ledger advanced from 0 to 243; the configured
1,000-attempt guard was unchanged. Earlier failed and recovery attempts
remain included in campaign totals. Across that broader history, 8
failed SDK attempts have unreported usage and two live-pytest calls have uncollected token
metadata. Campaign tokens are therefore partial accounting, not a billing total or Google's
remaining quota. This run's metrics are separately reported above.

[SHA-256 manifest](artifact-sha256.json) protects the raw results, manifests, terminal
streams and derived metrics. Original captures and their hashes remain intact. Capture
timestamps are UTC; this directory uses the local India date.
