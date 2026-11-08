# Full-schema CLI verification without RAG — 9 November 2026

The fresh complete supplied CLI run on [`0b3e94a`](https://github.com/Shaunakrane914/PortiQ/commit/0b3e94af6d124982bd399a170a20a2cc5dc38a98)
passed **10/10** with evaluator v3, including all ten explicit final-answer checks. The
agent uses the complete schema, database-derived categorical values, portfolio catalogue
and unchanged financial conventions. Neither BM25 nor graph retrieval is active.

| Metric | Recorded value |
|---|---:|
| Supplied questions passed | 10/10 |
| Explicit final-answer checks | 10 passed, 0 failed |
| Actual SDK attempts | 21 |
| Reported tokens | 48,293 |
| Provider errors / attempts with unknown usage | 0 / 0 |
| CLI wall time including batch pacing | 146.503 s |
| Mean / p95 question time | 14.540 / 19.471 s |
| Correctness-gated SQLite VM-work score | 95.52/100 |

This was genuine `gemini-3.1-flash-lite` generation through `python -m portiq ... evaluate`,
with local answers, answer caching and fallback models disabled. No LLM judge was used.
The 6.5-second request interval was a child-process batch setting; normal application
settings and the retained ledger were not reset. Local daily attempts moved from 202 to
223. The newly initialized database contained all 603 supplied rows. Source/input hashes
and database bytes remained unchanged throughout the run.

Before capture, **232 core tests passed**, one opt-in live test was skipped, and Ruff,
formatting and mypy across 18 source files passed. A separate offline check confirmed that
all ten initial system prompts and non-system generation configurations exactly match
the archived experiment's no-RAG control. This equivalence check made zero SDK calls and
does not itself establish generated-answer accuracy; the fresh live run above does.

The source change removes retrieval integration and its response/configuration fields.
The database loader, financial prompts, SQL validation/repair, exposure calculator, CLI,
service, dashboard and dependency files were unchanged. The [engineering decision](../../docs/ENGINEERING_NOTES.md#metadata-retrieval-evaluated-and-excluded)
links both archived implementations and benchmarks. The original task's RAG enhancement
is explicitly optional and is now marked evaluated and excluded.

This is one pass of a known ten-question suite, not unseen/general accuracy, an assurance
against all financial mistakes, or a new controlled latency comparison. Historical captures
retain their own source and metrics. No successful fragments were stitched into this run.
The directory uses the local India date; the manifest timestamps use UTC.

Immutable captured files: [JSON](supplied.json), [Markdown](supplied.md),
[manifest](run-manifest.json), [stdout](cli-stdout.txt) and [stderr](cli-stderr.txt).
[SHA-256 hashes](artifact-sha256.json) cover these five files.
