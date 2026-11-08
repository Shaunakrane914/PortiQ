# Supplied CLI verification after graph removal

The fresh, complete CLI run on [`f14ea21`](https://github.com/Shaunakrane914/PortiQ/commit/f14ea2195d950145081a51b15f63fde9529e539e)
passed **10/10** supplied questions with evaluator v3. All ten routing, result and explicit
final-answer checks passed. This used real `gemini-3.1-flash-lite` generation, full-schema
context and basic BM25 retrieval, with local answers and answer caching disabled.

| Metric | Recorded value |
|---|---:|
| Supplied questions passed | 10/10 |
| Explicit final-answer checks | 10 passed, 0 failed |
| Actual SDK attempts | 21 |
| Reported tokens | 54,093 |
| Provider errors / attempts with unknown usage | 0 / 0 |
| CLI wall time including batch pacing | 144.654 s |
| Mean / p95 question time | 14.302 / 24.116 s |
| Correctness-gated SQLite VM-work score | 95.52/100 |

The run crossed into 9 November 2026 in India; the directory and manifest use the
8 November UTC date. Its 6.5-second interval was a child-process batch setting. Application
pacing, provider configuration and the retained quota ledger were not reset. Daily local
attempts moved from 181 to 202. The freshly initialized temporary database contained all
603 supplied rows and remained byte-identical, as did the captured runtime and inputs.

Question 7 passed with Balanced Portfolio's total value **1,073,279** and Technology share
**36.22%**. The financial denominator regression from the archived graph run is not present
in this fresh run. This is one known supplied-suite pass, not unseen accuracy or a controlled
latency comparison. No fragments or retries of only failed cases were stitched together.

The active runtime, scripts and tests exactly match pre-graph commit `0790da7`; removing
the optional experiment did not require changing the ordinary agent, tools, CLI or dashboard.
Key-free validation passed: **235 tests**, one opt-in live test skipped, Ruff, formatting
and mypy across 19 source files. Graph code and evidence remain on the
[archive branch](https://github.com/Shaunakrane914/PortiQ/tree/archive/schema-graph-rag-2026-11-08).
See the [engineering decision](../../docs/ENGINEERING_NOTES.md#schema-graph-retrieval-archived).

The immutable capture contains [JSON](supplied.json), [Markdown](supplied.md),
[manifest](run-manifest.json), [terminal stdout](cli-stdout.txt) and
[stderr](cli-stderr.txt). [SHA-256 hashes](artifact-sha256.json) cover those five raw files.
