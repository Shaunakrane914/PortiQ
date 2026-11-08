# CLI-only 50-question run — 8 November 2026

The actual `portfolio-agent evaluate --suite extended` CLI subprocess passed **50/50** on source revision [`4b49d95`](https://github.com/Shaunakrane914/PortiQ/commit/4b49d95332ff212287ca8480d8ebde19e2c93a80). No browser, HTTP request, local capability registry or answer cache was used. This commit publishes evidence from that completed run; it does not represent another model run.

| Metric | Observed result |
|---|---:|
| Reference data results | 46/46 |
| Clarification / unsupported-security cases | 4/4 |
| Configured narrative assertions | 6 cases checked, 0 failures |
| Actual SDK invocations | 92 |
| Reported input / output / total tokens | 192,297 / 9,107 / 201,404 |
| Provider errors / backoff | 0 / 0 s |
| Complete CLI wall time | 593.976 s |
| Question mean / median / p95 | 11.856 / 12.938 / 13.496 s |
| Mean SDK service / deliberate pacing per question | 2.581 / 9.262 s |

The archived pre-cleanup original run on the same frozen suite passed 50/50 with 266,304 reported tokens. This run used 24.37% fewer reported tokens with no observed accuracy regression on those questions. This is historical context, not a controlled latency/causal comparison. All cases were previously observed; these are regression results, not blind validation. SDK service includes network transport. Thinking tokens were not separately reported and remain unknown. Only six cases have configured automated narrative assertions; unchecked prose is not certified. A separate assistant review of all complete answers found no visible value or handling mismatch.

## Evidence

| File | Contents |
|---|---|
| [review.md](review.md) | Complete questions/answers, per-question metrics, comparisons and scope |
| [extended.json](extended.json) | Raw generated SQL, tool results, independent references, provider metrics and every failure dimension |
| [extended.md](extended.md) | Original evaluator's strict per-question score table |
| [summary.json](summary.json) | Aggregate and per-question accuracy, timing and token fields, including unknown usage fields |
| [cli-transcript.txt](cli-transcript.txt) | Actual CLI stdout/stderr capture; process exited 0 |
| [run-manifest.json](run-manifest.json) | Exact CLI argv, source revision, before/after hashes, wall time and shared-ledger accounting |
| [database-csv-audit.json](database-csv-audit.json) | Independent read-only comparison: all 603 SQLite rows match the nine supplied CSVs |
| [validation.json](validation.json) | All 78 frozen input/historical Git blobs unchanged; assistant-review scope |
| [artifact-sha256.json](artifact-sha256.json) | SHA-256 of the eight original capture files |

The eight captured files are copied byte-for-byte from the original local run. Their recorded local output paths are intentionally preserved; the folder's `.gitattributes` disables newline conversion so their hashes remain verifiable after cloning. No source or benchmark files were modified for the run.

The user approved a 300-attempt cap for this CLI process only. The shared UTC-day ledger was retained and moved from 120 to 212 attempts; the normal configured cap remained 200. Google quota and billing settings were not changed. Those usage counts describe capture time, not current project usage. Reports remain excluded from the hosted application/container.
