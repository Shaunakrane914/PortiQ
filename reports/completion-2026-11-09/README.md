# 50/50 passed after retries — 9 November 2026

**Latest implementation: [50/50 extended, 10/10 supplied and measured interactive latency](../latency-2026-11-09/README.md).**
This page retains the historical capture scope and metrics below.

**Latest result: [50/50 passed in one full CLI run](../single-run-2026-11-09/README.md).**
This page retains the earlier retry-aware reporting scope and its original metrics.

**All 50 extended questions pass after retries**, including 46 verified data answers,
four handling cases and all three hybrids. Supplied CLI evaluation passes 10/10, and
three concurrent hybrid conversations complete all nine answers correctly.

[Completion JSON](completion.json) independently verifies the latest recorded answer for
every extended case using evaluator v4, the original full-suite rules, re-executed SQL and
CSV-derived financial references. It selects the latest attempt rather than the best result.
Every case links to its source capture and record index. This is a retry-aware completion
summary across captures, not a new single uninterrupted run. Original raw captures remain intact.

## Extended evaluation metrics

Accounting includes the full evaluation, the earlier recovery and the requested confirmation
retry. The confirmation passed [2/2](retry.json) using four SDK attempts and 9,324 reported
tokens, with a 21.074-second capture time. The [manifest](retry-manifest.json) records its
source `a29d1c0`, ledger and original-input hashes; the [selected suite](retry-suite.json)
contains the two unchanged original questions. Runtime hashes match the full evaluation.

| Metric | Value |
|---|---|
| Unique cases passed | **50/50 after retries** |
| Verified final data answers / handling cases | 46/46 / 4/4 |
| Hybrid questions | 3/3 |
| Question executions, including recovery and confirmation | 54 |
| Genuine SDK attempts, including failures | 102 |
| Captured reported tokens | 217,421 |
| Provider-error attempts / attempts with unreported usage | 6 / 6 |
| Summed capture wall time, excluding idle gaps | 865.927 s |
| Calendar span, including gaps between captures | 2,182.814 s |
| Mean / p95 per question execution, all 54 included | 15.990 s / 47.091 s |
| Provider service / pacing / backoff totals | 581.219 s / 237.378 s / 4.631 s |
| Final-answer mean relative SQLite pager-work score | 98.25/100 |
| Batch-only SDK spacing | 6.5 s |
| Cache / local answers / fallback models | Disabled / disabled / none |

Summed wall time is the sum of the three captured durations; it is not a claim of continuous
execution. Provider service, pacing and backoff are separate components, with remaining
time spent in other agent/evaluator work. Six attempts have no provider usage metadata,
so token counts are reported usage rather than complete billing totals. The pager-work
score uses the latest verified answers and matched fresh private caches. It is not physical
device I/O, a general optimizer score or a controlled comparison with older runs.

## All new-key checks through confirmation

[Campaign metrics](campaign-metrics.json) account for all genuine-provider checks in this
verification campaign. Extended evaluation/retries are counted once as the combined row.

| Check | Result | SDK attempts | Captured reported tokens |
|---|---|---:|---:|
| Extended CLI, recovery and confirmation | 50/50 after retries | 102 | 217,421 |
| Supplied CLI | 10/10 | 21 | 48,292 |
| Concurrent hybrid conversations | 9/9 | 22 | 40,972 |
| Dashboard genuine browser answer | 1/1 | 2 | 4,371 |
| Streamlit genuine browser answer | 1/1 | 1 | 2,076 |
| Opt-in live pytest | 1/1 | 2 | Not collected by the assertion |
| **All genuine checks** | | **150** | **313,132 captured** |

The local daily ledger advanced from 0 to 150 attempts; its configured 1,000-attempt guard
was unchanged. Captured tokens omit six failed SDK attempts with unreported usage and
two live-pytest calls whose usage was not collected. This is not Google's remaining quota
or a complete billing total. No new provider calls were made to build the completion summary.

Key-free verification also passed: 282 local Python 3.14 tests, 281 isolated Python 3.11
tests, 11 non-live browser cases, lint/format/type checks across 19 source files, 16 production
Docker checks and byte integrity for all 13 original assignment files. The live-only Python
case and browser case were exercised separately above. The HTTP/stub soak made 1,225
requests: 613 correct accepted answers and 612 controlled `503 Retry-After: 1` responses,
with recovery, accounting, session/client bounds and shutdown passing. Stub calls/tokens
are excluded from genuine provider totals. Its 402.75 ms overall p95 and 71.39 ms maximum
readiness time are local stub measurements.

The real nine-answer HTTP protocol used three users and stable isolated sessions. Its
155.569-second wall time and 40.901/61.593-second HTTP p50/p95 include shared batch pacing;
no quota responses occurred. Supplied CLI wall time was 175.066 seconds, with mean/p95
17.192/24.081 seconds. These are observed capture metrics, not a model-latency SLA.

Five runtime CI jobs passed on `a29d1c0`: [Python quality](https://github.com/Shaunakrane914/PortiQ/actions/runs/42573706764)
and [platform/browser/Docker](https://github.com/Shaunakrane914/PortiQ/actions/runs/42573706710).
The [new-key capture index](../retest-2026-11-09/README.md) contains their local evidence.
Known finite suites, unsupported arbitrary prose formats, distributed coordination,
hours-long provider load and externally operated TLS/monitoring remain subject to the
[documented limits](../../docs/KNOWN_LIMITATIONS.md). No runtime, prompt, safety boundary
or evaluator pass condition changed to obtain this completion result.

## Provenance

[SHA-256 manifest](artifact-sha256.json) covers the completion JSON, campaign metrics,
confirmation capture, selected suite and manifest. The completion JSON records hashes of
all input captures and manifests, including every original execution. Those files retain
their original outcomes. Historical [capture hashes](../retest-2026-11-09/artifact-sha256.json)
remain unchanged. Capture timestamps use UTC; this report uses the local India date.
