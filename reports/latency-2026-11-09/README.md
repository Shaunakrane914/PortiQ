# Lower-latency factual answers — 9 November 2026

Gemini can now finish a complete factual tool plan without a second model call to restate
the result. The app renders validated evidence directly. **Fresh accuracy remains 50/50
extended and 10/10 supplied**, with all 46/10 explicit data-answer checks passing.

Runtime source: [`1eba590`](https://github.com/Shaunakrane914/PortiQ/commit/1eba590b2b01b9a325e3d29f528dfe6bffd9586d).
[Analysis](analysis.json) records timing, provider usage, verification scope and limitations.

## Actual input-to-output measurements

These requests used genuine Gemini, no cached/local answers and **zero test spacing**.

| Local browser request | Submit to visible verified answer | SDK calls |
|---|---:|---:|
| Dashboard: list Passive portfolios | **1.454 s** | 1 |
| Streamlit: count all portfolios | **2.834 s** | 1 |

The [dashboard capture](dashboard-input-output.json) checks the generated SQL rows and all
displayed names against database records. The [Streamlit capture](streamlit-input-output.json)
checks the count, visible SQL, genuine SDK usage and disabled cache. These are two actual
local browser observations, not percentiles, hosted Render measurements or a latency SLA.
[Browser results](browser-summary.json) record both cases passing.

The separate [live baseline/candidate comparison](paired-interactive.json) used the same
client, model, full schema and fresh dataset, in baseline/candidate then candidate/baseline
order. It times agent construction through completed answer, excluding grading and browser
transport. The [control-equivalence check](baseline-equivalence.json) confirms the disabled
feature preserves the old system prompt and function schemas exactly.

| Question | Previous synthesis | Direct results | SDK calls | Reported tokens |
|---|---:|---:|---:|---:|
| List Passive portfolios | 2.837 s | **1.157 s** | 2 → 1 | 4,371 → 2,334 |
| Balanced Portfolio exposure | 2.676 s | 2.861 s | 2 → 1 | 4,315 → 2,284 |

Both variants produced independently verified answers. The exposure pair was slightly
slower despite fewer calls. Two pairs show call/token reductions and one observed speedup;
they do not establish a universal latency improvement. Provider service time varies.

## Fresh accuracy and usage

| Suite | Result | SDK attempts | Reported tokens | Directly rendered answers |
|---|---:|---:|---:|---:|
| [Extended fifty](extended-candidate/extended.json) | **50/50** | 57 | 137,274 | 41 |
| [Original supplied ten](supplied-candidate/supplied.json) | **10/10** | 13 | 29,269 | 9 |

Each is one complete native evaluator v4 trial in original order, with no post-run answer
substitution, no fallback models and no local/cache answers. Manifests verify unchanged
runtime, input and database hashes and reconcile real SDK attempts with the retained ledger:
[extended](extended-candidate/run-manifest.json), [supplied](supplied-candidate/run-manifest.json).
The extended run has zero provider errors/unknown-usage attempts. The supplied run recovered
one provider error within its normal retry policy; that attempt has unreported usage.

The [previous full-schema baseline](https://github.com/Shaunakrane914/PortiQ/blob/f6d93578e3a2b5017dd926c3aba1e36b6d4e2816/reports/single-run-2026-11-09/README.md) used 93 SDK attempts
and 205,940 reported tokens for the extended fifty. This capture uses **38.7% fewer SDK
attempts** and **33.3% fewer reported tokens**. Those full-suite runs were not interleaved;
the baseline also includes two provider-error attempts with unreported usage. This is
captured-usage evidence, not a complete billing comparison or causal latency estimate.

Correctness-gated relative SQLite pager-work scores average 98.25 extended and 93.13
supplied. The [offline renderer check](offline-rendering.json) independently verifies all
46 historically captured data answers after deterministic rendering, with zero SDK calls.
The fresh live suites separately validate the model's plan/completion behavior.

The extended accuracy run took 383.904 seconds, with mean/p95 question times 7.633/13.062
seconds. Provider service/pacing/backoff totals were 163.906/153.257/0.000 seconds.
The supplied run took 84.974 seconds, with mean/p95 8.237/20.932 seconds and service/pacing/
backoff totals 30.115/46.352/1.002 seconds. Both accuracy runs use child-only **6.5-second
batch spacing**. They are not interactive latency measurements; use the zero-spacing
measurements above for observed input-to-output examples.

This verification consumed 78 genuine SDK attempts: six paired-test attempts, 57 extended,
13 supplied and two browser attempts. The existing ledger advanced from 243 to 321; the
configured 1,000-attempt daily guard was unchanged. One supplied attempt has unreported
usage. Local counts do not reveal Google's remaining quota or a complete billing total.

## Implementation and safeguards

The existing tool schemas add optional, strictly typed `complete` flags. For a factual
request, Gemini must mark **every** analytical call in its final batch complete, including
every requested hybrid part. The app still executes the existing SQL validator/read-only
boundary and deterministic exposure calculator. It can return directly only when all
traces succeed, SQL results are nonempty/untruncated with at most 30 rows, text is losslessly
representable, floats are finite and the complete rendered answer fits 10,000 characters.
Raw numeric precision is retained instead of resynthesizing figures.

Unmarked, exploratory, ambiguous, failed, empty, truncated, large or interpretive requests
retain the normal tool loop. Complex SQL planning and bounded repairs remain active.
Completeness is still a Gemini planning claim; it is not a general proof of arbitrary
natural-language intent coverage. Known finite-suite success is not blind/unseen accuracy.
No financial convention, schema metadata, model, retry limit or production rate guard was
removed. Native application fixed spacing remains zero.

`PORTIQ_DIRECT_RESULTS=1` is the default. Set it to `0` and restart the process to restore
previous orchestration, including the earlier explicit-scalar optimization. This switch
does not enable the separate local capability registry or answer cache.

## Regression and deployment checks

- 298 Python 3.14 tests passed; the separate opt-in live test was skipped in the unit run.
- 297 isolated Python 3.11 tests passed; live and optional GUI tests were skipped.
- All 16 new direct-result tests passed, covering precision, mixed hybrid completion,
  ambiguity, truncation, invalid flags, text loss, SQL safety and baseline behavior.
- Ruff, formatting and mypy passed across 19 source files.
- Both genuine browser input-to-output checks passed.
- [Production Docker](production-container.json) passed all 16 checks on a fresh image,
  using no real key and a disposable ledger; retained usage, non-root/read-only settings,
  authentication, origins, body limits, file exclusions and clean shutdown were verified.

The tests emitted a nonfatal Starlette TestClient deprecation. Neither these checks nor
the browser samples establish distributed operation, hours of provider load or an SLA.

## Capture integrity

[SHA-256 manifest](artifact-sha256.json) covers raw captures, manifests, terminal streams
and derived records. Exact paired responses include provider metrics; public browser
captures omit session capabilities. Full test reports containing local paths remain under
ignored local reports. Prior capture hashes remain unchanged. Timestamps use UTC; this
directory uses the local India date.
