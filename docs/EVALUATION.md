# Evaluation methodology and evidence

The assignment requires a CLI evaluator for the supplied ground truth. `uv run portfolio-agent evaluate` selects [ground_truth_dataset.json](../ground_truth_dataset.json): **10 supplied questions, eight SQL and two exposure**. `--suite extended` selects the separate [50-question author-created regression](../evaluation/extended.json). Runtime planning code never reads benchmark questions, IDs, reference SQL or narrative rules.

## Reproduce the required evaluation

```powershell
uv run portfolio-agent evaluate --output reports/local/supplied-new.json
uv run portfolio-agent evaluate --suite extended --output reports/local/extended-new.json
```

These commands use real Gemini calls with local routing and exact answer caching disabled. They require a configured key, initialized data and sufficient provider/local quota. Choose new paths: the evaluator writes its JSON, Markdown and progress files at the selected path. Completed runs exit 0 only if every case passes; failures return 1. Partial/failed runs must remain distinct from subsequent complete runs.

`--trials 1..5` repeats a suite; `--split development|validation|heldout` and `--limit` select subsets. Label such reports as subsets/repetitions rather than a full fresh fifty. All extended cases have been observed, including those originally labeled heldout; reruns are regression evidence, not blind validation.

## Current and historical results

| Evidence | Captured result | Meaning |
|---|---|---|
| [CLI-only 8 November 2026](../reports/cli-2026-11-08/README.md), source `4b49d95` | **50/50 extended**, 92 SDK calls, 201,404 reported tokens, zero provider errors | Actual CLI subprocess; 46 data cases and four handling cases; cache/local disabled |
| [Pre-cleanup original-agent supplied](../reports/v0.2.0/supplied.json) | **10/10 supplied** | Historical capture; not a new supplied-suite run for the current source |
| [Pre-cleanup original-agent extended](../reports/v0.2.0/extended.json) | **50/50**, 97 SDK calls, 266,304 tokens | Same frozen extended questions; historical comparison, not a controlled speed ablation |
| [v0.1.1 supplied](../reports/v0.1.1/supplied.json) / [extended](../reports/v0.1.1/extended.json) | **10/10 / 50/50** | Historical release evidence, with separate categorical/ambiguity reports |

The latest CLI run used 24.37% fewer reported tokens than the archived original extended run and showed no score regression on these cases. Different dates, model service conditions and source revisions prevent a causal general latency claim. Its 593.976-second process wall time and 11.856 / 12.938 / 13.496-second question mean/median/p95 include deliberate pacing. Mean SDK service was 2.581 seconds per question; service includes transport.

The published [raw CLI report](../reports/cli-2026-11-08/extended.json) contains generated SQL, outputs, references, all failures and per-call metrics. [summary.json](../reports/cli-2026-11-08/summary.json) includes input/output usage, unknown thinking usage, per-question metrics and comparison scope. The [transcript](../reports/cli-2026-11-08/cli-transcript.txt) and [manifest](../reports/cli-2026-11-08/run-manifest.json) identify the exact command, exit code, process-only 300-attempt exception and source/data hashes.

All 603 database rows matched the nine CSVs in a separate read-only audit. All 78 frozen input/historical Git blobs were unchanged. The eight original capture files are byte-preserved under scoped `.gitattributes`; verify them with [artifact-sha256.json](../reports/cli-2026-11-08/artifact-sha256.json). Capture-time local paths/counters intentionally remain in the raw manifest and are not live account balances.

No fresh supplied-ten model score is claimed by the current documentation update. The documented evaluator is available to produce one when explicitly run with quota.

## Independent dimensions

- `status_correct`: answer, clarification or unsupported matches the case contract.
- `result_correct`: all reference outputs match distinct successful tool results; null when a handling case has no reference data result.
- `sql_valid`: generated SQL independently executes and agrees with recorded tool output; safety does not imply correct interpretation.
- `routing_correct`: for data answers, the successful analytical tool multiset exactly matches the required multiset. Handling cases retain the existing status-based contract, which permits discovery queries before clarification.
- `faithfulness`: passed/failed/not_checked for configured finite narrative assertions.
- `answer_correct`: correct status, correct reference evidence where checked and no failed configured narrative assertion.
- `passed`: `answer_correct AND routing_correct`. Extra successful discovery calls on a data-answer case can fail strict routing even if its final data is correct.

The latest CLI run passed 46/46 reference-data cases, 50/50 statuses/routing contracts and all six configured narrative cases. SQL validity was checked in 39 questions: the 37 data questions using SQL plus two discovery queries in clarification cases. The security/prediction cases did not execute analytical tools. These counts are different checks, not interchangeable accuracy denominators.

## Structured evidence comparison

Reference SQL runs on an independent read-only connection. Generated SQL is independently re-executed through the safety boundary, and its columns/rows must match its claimed tool result. Every reference must match a distinct candidate result; multiple references cannot reuse one result. Truncated outputs cannot pass.

Comparison checks all rows, projection widths, duplicate multiplicities, numeric values and required ordering. Aliases may differ, but projected positions matter. Numeric tolerance is relative `1e-7`, absolute `1e-6`; NULL differs from zero and numeric strings differ from numbers. Ordered references use top-level `ORDER BY`; unordered results use maximum bipartite matching. Ties follow the reference execution order, so another valid tied order can be penalized.

Exposure references join original CSVs using independent Python dictionaries/Decimal arithmetic, not the production calculator or resolver. Portfolio identity, sector sets and finite percentages must match within 0.005001 percentage points. NaN/Infinity cannot pass. This tests the assignment's stock-only normalization independently of generated narrative.

## Narrative checks and scope

[faithfulness.json](../evaluation/faithfulness.json) is evaluation-only; it never enters prompts. Configured rules check selected scalar values, portfolio counts/names, sector percentages/identities and one hybrid answer. Numerical parsing permits commas, scale words and declared rounding. Contradictory empty-result claims are checked where configured. Non-answer statuses do not count as narrative successes.

Only **six** cases in the latest fifty had automated narrative assertions. The remaining prose is not certified by data-result scoring. A separate assistant review read all fifty complete answers against their evidence and found no visible value/handling mismatch; it is explicitly separate from an automated oracle or another Gemini evaluation. It does not establish accuracy for arbitrary prose, negation, recommendations or unseen questions.

## Other validation modes

Ordinary CI is key-free: Python 3.11/3.13 on Ubuntu/Windows, Ruff, format, mypy, pytest, CLI smoke, browser checks and a real credential-free container check. The most recent application verification passed 212 Python tests with two opt-in live skips, eight offline browser tests and one skipped live browser case. Test counts describe that revision and can change.

`PORTIQ_LIVE=1` enables explicitly marked live Python tests; `PORTIQ_WEB_LIVE=1` enables genuine browser Gemini tests. They spend quota and are not part of normal CI. Offline replay, SQL/exposure unit tests, local/cache microbenchmarks and browser tests without a key are not fresh model accuracy runs.

```powershell
uv run python scripts/benchmark.py --mode tools --output reports/local/tools-new.json
uv run python scripts/benchmark.py --mode cache --output reports/local/cache-new.json
```

The benchmark helper refuses existing output paths and makes zero SDK calls. It measures local Python service time, not hosted latency. The optional `scripts/release_evaluation.py` runs selected supplied/semantic/extended suites with a shared 6.5-second-paced backend; always select a new output directory. Do not republish into existing historical release folders.

## Historical interpretation

The original v0.1.0 `Passive` failure queried `strategy_type` for a value stored under `status`, then falsely claimed no matching portfolios. It was a semantic/result failure, not merely extra routing. v0.1.1 added live classification domains and stronger evaluation. Original reports/tags remain unchanged; the [historical index](../reports/README.md) and [pre-cleanup archive](https://github.com/Shaunakrane914/PortiQ/tree/ace58054c7a778817d68a7c1d81386b7dffd95e8) retain that context.

The removed experimental planner was faster in some captures but failed supplied/ambiguity cases and was not promoted. A separate interrupted provider-outage comparison exhausted 250 attempts; its successful fragments were not stitched into later runs. Current code supports the original orchestrator with compact context and guarded scalar rendering, not the removed strategy. [Engineering notes](ENGINEERING_NOTES.md) record those tradeoffs without treating archived scores as fresh verification.
