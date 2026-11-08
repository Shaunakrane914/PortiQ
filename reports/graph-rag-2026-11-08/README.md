# Schema-graph RAG comparison — 8 November 2026

**Verdict:** Graph selection reduced initial context and reported tokens, but did not improve
answer accuracy. It failed one supplied case that the full-schema control passed. Keep it
experimental; this run does not justify changing the application's default retrieval mode.

Captured source: [`7caf262f7f415184ec237ad8ec764dc678937420`](https://github.com/Shaunakrane914/PortiQ/commit/7caf262f7f415184ec237ad8ec764dc678937420).
The [implementation and reproduction commands](../../docs/GRAPH_RETRIEVAL.md) explain the
schema-graph method and distinguish it from Microsoft's document/community GraphRAG.

## Fresh paired Gemini run

One pass of the original ten supplied questions, both conditions, alternating which condition
runs first. Same client, model (`gemini-3.1-flash-lite`), data, financial conventions, tools,
generation configuration and evaluator. No local answers, answer cache or judge model.
Dedicated SQL planning/repair keep the full schema in both conditions. The graph changes
initial schema/catalogue/domain selection, with a full-schema fallback for uncertain seeds.

| Metric | Full-schema control | Schema graph |
|---|---:|---:|
| Passed supplied cases | 10/10 | 9/10 |
| Result checks passed | 10 | 9 |
| Explicit final-answer checks passed | 10 | 9 |
| SDK attempts | 21 | 21 |
| Reported total tokens | 48,296 | 35,352 |
| Reported input tokens | 45,333 | 32,689 |
| Mean SDK service per question | 5.996 s | 6.499 s |
| Median SDK service per question | 3.102 s | 3.142 s |
| Provider errors | 0 | 1 recovered 504 |
| Attempts with unknown usage | 0 | 1 |

Reported tokens fell **26.80%**, and reported input tokens fell **27.89%**. The failed 504
attempt has no usage metadata, so these are reported-usage totals, not complete billable
usage or a guaranteed cost reduction. No attempt was dropped from the operational results.

Mean SDK service increased 8.39%. The paired question-cluster bootstrap 95% interval for the
change was **−53.04% to +188.76%**. Provider/network variability is large; no reliable speedup
was demonstrated. Service includes recovered errors and excludes deliberate pacing. The
separate 6.5-second batch interval is an experiment setting, not a new application setting.
Provider cache usage was unreported, not proven absent.

All twenty scheduled questions reached Gemini, with no circuit-blocked rows. The shared
ledger moved from 139 to 181; it was not reset. The run took 310.995 seconds including pacing.
Source/input hashes and the temporary database remained unchanged. Initial non-system
configuration hashes match within every pair, and initial prompt hashes match the offline
audit. See [analysis.json](analysis.json) and the [raw manifest](live/run-manifest.json).

### The failed case matters

Question 7 asks for Technology holdings value as a percentage of total portfolio value.
Graph mode selected every required table, but generated an INNER JOIN through sectors for
both numerator and denominator. This removed unclassified bonds from the denominator and
also returned portfolios with zero Technology holdings, contrary to the existing contract.

For Balanced Portfolio, its denominator was **772,304** instead of **1,073,279**, yielding
**50.33%** instead of **36.22%**. The control passed this case using a dedicated planning
call. The graph's incorrect SQL was syntactically valid, so execution validation did not
trigger a repair. This illustrates the difference between metadata coverage, valid SQL and
financial correctness. The existing financial instructions were retained in both prompts.
The raw failure is preserved in [records.jsonl](live/records.jsonl); it was not patched,
rescored or replaced with a successful retry.

## Offline metadata/context audit

The schema graph contains 93 table/column/rule nodes and 101 edges. It follows actual foreign
keys to retain bridge tables and falls back when seeds are unknown or disconnected.

| Audit | Supplied 10 | Author-created 50 |
|---|---:|---:|
| Reference-required table coverage | 10/10 | 46/46 data questions |
| Handling-only questions, without table references | 0 | 4 |
| Full-schema fallbacks | 0 | 1 |
| Mean full-schema initial system characters | 7,000 | 7,000 |
| Mean basic-RAG initial system characters | 8,147.2 | 8,252.2 |
| Mean graph initial system characters | 4,674.1 | 5,281.12 |
| Graph reduction versus full schema | 33.23% | 24.56% |

The extended suite was audited offline only; no fresh 50-question generated-answer score is
claimed. This audit uses reference SQL after retrieval solely to check table coverage.
Reference answers never enter runtime selection. The known splits are not unseen evaluation.
The live failure above shows why complete table coverage cannot substitute for answer tests.

The [earlier basic-RAG comparison](../rag-ablation-2026-11-08/README.md) tested appending
metadata to a full schema and found additional tokens without accuracy improvement. That
was a different run; it is not a simultaneous third arm of this live graph experiment.

## Evidence and validation

- [Offline audit](offline-audit.json), [analysis](analysis.json), [environment](environment.json).
- Raw live [results](live/results.json), [records](live/records.jsonl), [pairs](live/pairs.csv)
  and [manifest](live/run-manifest.json).
- A [failed minimal probe](provider-unavailable-probe.json) before implementation checks,
  followed by a [successful recovery probe](provider-recovery-probe.json) before the run.
- [SHA-256 manifest](artifact-sha256.json) covers all nine JSON/JSONL/CSV evidence files.

Before capture, Ruff, formatting and mypy passed; the full local suite passed 245 tests with
one opt-in live test skipped. Two additional post-capture regression cases verify that
unknown/disconnected graph selection sends the exact original prompt. Those test additions
do not change the captured runtime source. No frontend or application retrieval default was
changed by the experiment.
