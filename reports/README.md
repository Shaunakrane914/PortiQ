# Evaluation and verification report index

**Current result: [50/50 extended and 10/10 supplied](latency-2026-11-09/README.md)** on
the direct-results implementation. The full native v4 trials preserve all data-answer
checks. Extended usage is 57 SDK attempts and 137,274 reported tokens; supplied is 13
and 29,269. No post-run answer substitutions were used.

Actual uncached, zero-spacing local browser click-to-answer examples were 1.454s and
2.834s. The paired agent comparison showed 2.837→1.157s for a list and 2.676→2.861s for
exposure, both with 2→1 SDK calls. These are descriptive samples, not an SLA or general
latency percentile. Batch accuracy timing is documented separately.

Original captures remain intact. The earlier single-run and retry-aware records retain
their own source versions, provider counts and campaign accounting snapshots.

| Evidence | Scope |
|---|---|
| [Smarter answer (2 SDK) live checks](smarter-mode-2026-11-09/README.md) | Per-request smarter toggle verification across web dashboard and Streamlit, real 2 vs 1 SDK calls |
| [Current latency and accuracy](latency-2026-11-09/README.md) | Fresh 50/50 and 10/10, paired no-spacing results, true local browser input-to-output, regression and Docker checks |
| [Earlier full CLI run](single-run-2026-11-09/README.md) | Current single-run 50/50; native JSON/Markdown, terminal streams, input/runtime hashes and metrics |
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
