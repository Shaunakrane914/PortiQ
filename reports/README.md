# Evaluation and verification report index

**Current result: [50/50 passed in one full CLI run](single-run-2026-11-09/README.md).**
The fresh native v4 evaluator ran all fifty frozen questions once in order and exited 0,
with no post-run answer substitutions. All 46 data-answer checks and three hybrids pass.
The capture records 93 SDK attempts, 205,940 reported tokens and 747.520 seconds of CLI wall time; mean/p95 question times
are 14.926/28.658 seconds. Full provider, pacing, backoff and SQL-work metrics are retained.

[Campaign accounting](single-run-2026-11-09/campaign-metrics.json) covers every earlier
genuine verification/recovery plus this fresh full run: 243 SDK attempts and
519,072 captured reported tokens. Across that broader history, 8 failed attempts
have unreported usage and two live-pytest calls have uncollected token metadata. Reported
tokens are not complete billing totals or Google's remaining quota.

| Evidence | Scope |
|---|---|
| [Fresh full CLI run](single-run-2026-11-09/README.md) | Current single-run 50/50; native JSON/Markdown, terminal streams, input/runtime hashes and metrics |
| [Earlier completion view](completion-2026-11-09/README.md) | Historical retry-aware summary with all attempts and usage accounted for |
| [New-key capture index](retest-2026-11-09/README.md) | Supplied 10/10, live conversations 9/9, dashboard/Streamlit, HTTP/stub soak, Docker and assignment integrity |
| [Earlier assurance](assurance-2026-11-09/README.md) | Verifier corrections, offline replay, adversarial checks and quota-interrupted attempts |
| [No-RAG supplied](supplied-no-rag-2026-11-09/README.md) | Fresh 10/10 under evaluator v3, source `0b3e94a` |
| [After graph removal](supplied-after-graph-removal-2026-11-08/README.md) | Fresh 10/10 under v3, source `f14ea21`; BM25 still active |
| [Supplied v3](supplied-v3-2026-11-08/README.md) | Historical supplied captures and verifier-format diagnosis |
| [Extended v2](cli-2026-11-08/README.md) | Historical 50/50 on `4b49d95`; evaluator v2 |

The [engineering decision](../docs/ENGINEERING_NOTES.md#metadata-retrieval-evaluated-and-excluded)
links the archived BM25 and schema-graph experiments. Original captures and their outcomes
remain unchanged; single-run, retry-aware, offline and stub evidence retain distinct scopes.
