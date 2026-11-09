# Evaluation and verification report index

The [current completion report](completion-2026-11-09/README.md) records **50/50 extended
passed after retries**, supplied CLI 10/10, all three hybrids passing and live concurrent
conversations 9/9. It includes every extended execution across evaluation, recovery and
confirmation: **54 executions, 102 SDK attempts, 217,421 reported tokens** and **865.927
seconds of summed capture time**. Six attempts have unreported usage.

The retry-aware summary independently verifies the latest answer for every case and retains
all source capture hashes. [Campaign metrics](completion-2026-11-09/campaign-metrics.json)
cover all new-key checks through confirmation: 150 genuine SDK attempts and 313,132 captured
reported tokens. The token total omits six failed attempts with unknown usage and two
live-pytest calls whose token metadata was not collected. It is not a complete billing total.

| Evidence | Scope |
|---|---|
| [Completion and metrics](completion-2026-11-09/README.md) | Current 50/50 completion after retries, final-answer re-verification and all execution accounting |
| [New-key capture index](retest-2026-11-09/README.md) | Raw evaluation, recovery, live HTTP/browser, load, Docker and assignment-integrity evidence |
| [Earlier assurance](assurance-2026-11-09/README.md) | Verifier corrections, offline replay, adversarial checks and quota-interrupted attempts |
| [No-RAG supplied](supplied-no-rag-2026-11-09/README.md) | Fresh 10/10 under evaluator v3, source `0b3e94a` |
| [After graph removal](supplied-after-graph-removal-2026-11-08/README.md) | Fresh 10/10 under v3, source `f14ea21`; BM25 still active |
| [Supplied v3](supplied-v3-2026-11-08/README.md) | Earlier supplied captures with verifier-format diagnosis |
| [Extended v2](cli-2026-11-08/README.md) | Historical 50/50 on `4b49d95`, 92 SDK attempts, 201,404 reported tokens; limited narrative verification |

Raw captures retain their original outcomes. Retry-aware completion, single-run results,
offline replay and stub load tests are distinct evidence scopes.

Both retrieval experiments were removed from the active architecture and preserved in Git:
[BM25 paired evidence](https://github.com/Shaunakrane914/PortiQ/blob/d65927b2e59e07c76ff3795e1395c0724a439241/reports/rag-ablation-2026-11-08/README.md)
and [schema-graph evidence](https://github.com/Shaunakrane914/PortiQ/blob/8a6143c96d1780f1890ff8d7db1c92cc5dbdd4a8/reports/graph-rag-2026-11-08/README.md).
See the [engineering decision](../docs/ENGINEERING_NOTES.md#metadata-retrieval-evaluated-and-excluded).
