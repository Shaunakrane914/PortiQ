# Controlled metadata-RAG comparison — 8 November 2026

**No accuracy or SDK-call improvement was demonstrated; RAG increased reported tokens by 12.02%.** Timing is inconclusive.

The primary result is the first complete, error-free paired pass of the original ten supplied questions: **20 actual answers / 10 pairs**. Both conditions use the same client, data, model, full schema, catalogue, domains, tools, temperature, repair limits and evaluator. Only the retrieved metadata block differs. Each condition runs first on five questions. Local answers, answer caching and judge-model calls are disabled.

| Metric | RAG off | RAG on |
|---|---:|---:|
| Strict answer pass | 10/10 | 10/10 |
| Actual SDK calls | 21 | 21 |
| Reported tokens | 48,271 | 54,074 |
| Input tokens | 45,332 | 51,172 |
| Output tokens | 2,939 | 2,902 |
| Mean SDK service / question | 4.961 s | 5.348 s |
| Median SDK service / question | 3.156 s | 4.651 s |
| Provider errors in this pass | 0 | 0 |

Mean SDK service changed +7.81% (positive is slower). The descriptive question-cluster bootstrap 95% interval is **-19.70% to +61.64%**, crossing zero. SDK service includes network and excludes deliberate pacing; it is not an inference-only clock.

## Interrupted repeat

Two full paired passes were planned. During pass two, Gemini returned repeated 504 gateway errors; the shared circuit then blocked the final seven entries before any SDK call. All raw records remain preserved. The raw 16/20 per-arm operational scores and legacy `complete=true` field must **not** be interpreted as completed two-pass model accuracy. Only the first prescheduled complete trial is used for the primary comparison.

A separate minimal `Reply OK` recovery probe also returned 504. Its single SDK attempt is recorded separately and excluded from both arms. Across the interrupted capture there were 71 SDK attempts; the probe adds one. No failed fragments are stitched into a new run.

A separately labeled post-hoc sensitivity has 15 fully answered, provider-error-free pairs (including available repeat pairs). Mean service off/on is 5.929/5.876 seconds, with a bootstrap interval of -21.82% to +48.09%. This is not a complete second-pass score. No slow successful request is discarded.

The benchmark harness was corrected after capture to stop on an open circuit, mark pre-SDK blocked entries as incomplete and exclude zero-call entries from model timing pairs. The original captured files and their original flags are unchanged.

## Interpretation

The complete schema is already sent in both modes, so this RAG implementation adds metadata rather than reducing context. The table-document audit also shows noisy ranking and incomplete top-document coverage for some queries; foreign-key links in other documents are not counted by that audit. Every model request still had the full schema.

These are previously observed questions. Equal accuracy does not prove RAG never helps unseen questions or a larger document corpus. Provider caching is not controlled and its token counters were unreported, not known zero. Failed-attempt token consumption is unknown. No live RAG defaults were changed.

## Artifacts

- [Raw results, including the interrupted repeat](results.json)
- [Incremental raw records](records.jsonl)
- [Predeclared schedule, source hashes and ledger](run-manifest.json)
- [Captured pairs, including invalid blocked pairs; use analysis.json for valid comparisons](pairs.csv)
- [Primary analysis and sensitivity](analysis.json)
- [Recovery probe](provider-recovery-probe.json)
- [Retrieval document audit](retrieval-audit.json)
- [Environment](environment.json)

## Reproduce

```powershell
uv run python scripts/rag_ablation.py --output reports/local/rag-new --trials 2
```

Use a fresh directory, clean source and sufficient quota. This spends real SDK calls. A 6.5-second interval is applied only to the child experiment; normal settings and the usage ledger are not reset.
