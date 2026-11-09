# Evaluation and verification report index

The [latest retest](retest-2026-11-09/README.md) uses the newly configured private Gemini
credential on source `2a68b74`. It includes a fresh supplied-ten CLI evaluation and the
completed three-user, nine-answer hybrid conversation protocol, with separate browser,
HTTP/stub soak and production Docker checks. Raw captures identify their exact scope;
stub requests and offline replays are never counted as fresh model accuracy.

The fresh extended v4 run scored **48/50**. Two provider-timeout failures passed in a
separate 2/2 recovery check; the original full-run score and six unknown-usage attempts
remain recorded. It is not reported as a clean fresh 50/50 result.

The [previous assurance](assurance-2026-11-09/README.md) retains the evaluator corrections,
50-answer offline replay, adversarial prose checks and earlier failed/quota-interrupted live
protocols. The new run does not overwrite or combine their answers into a passing score.

| Historical capture | Recorded scope |
|---|---|
| [No-RAG supplied](supplied-no-rag-2026-11-09/README.md) | Fresh 10/10 under evaluator v3, source `0b3e94a` |
| [After graph removal](supplied-after-graph-removal-2026-11-08/README.md) | Fresh 10/10 under v3, source `f14ea21`; BM25 still active |
| [Supplied v3](supplied-v3-2026-11-08/README.md) | Initial 8/10 and separate later 10/10, with verifier-format diagnosis |
| [Extended v2](cli-2026-11-08/README.md) | 50/50 on `4b49d95`, 92 SDK attempts, 201,404 reported tokens; limited narrative verification |

Both retrieval experiments were removed from the active architecture and preserved in Git:
[BM25 paired evidence](https://github.com/Shaunakrane914/PortiQ/blob/d65927b2e59e07c76ff3795e1395c0724a439241/reports/rag-ablation-2026-11-08/README.md)
and [schema-graph evidence](https://github.com/Shaunakrane914/PortiQ/blob/8a6143c96d1780f1890ff8d7db1c92cc5dbdd4a8/reports/graph-rag-2026-11-08/README.md).
See the [engineering decision](../docs/ENGINEERING_NOTES.md#metadata-retrieval-evaluated-and-excluded).
