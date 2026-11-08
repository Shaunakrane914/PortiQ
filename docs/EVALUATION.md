# Evaluation methodology and evidence

`uv run portfolio-agent evaluate` selects the original [ten supplied questions](../ground_truth_dataset.json),
eight SQL and two exposure. `--suite extended` selects the separate author-created
[50-question regression](../evaluation/extended.json). Runtime planning/retrieval never reads
questions, IDs, expected SQL or narrative rules from these files.

```powershell
uv run portfolio-agent evaluate --output reports/local/supplied-new.json
uv run portfolio-agent evaluate --suite extended --output reports/local/extended-new.json
```

These use genuine Gemini with local/cache disabled. A key, initialized database and enough
quota are required. Select a fresh output path. JSON, Markdown and an intermediate progress
file are written; any case failure returns exit 1. `--trials 1..5`, `--limit` and
`--split development|validation|heldout` select repetitions/subsets. All extended cases have
been observed, including the old heldout labels; they are not blind validation.

## Evaluator v3: answer verification and SQL efficiency

Each case records separate status, routing, evidence, answer-verification and SQL-validity
dimensions. Correct reference data alone cannot make an incorrect final answer pass.

- SQL references execute independently. Generated SQL is re-executed through the read-only
  safety boundary and must agree with its recorded columns/rows. Every reference needs a
  distinct matching result; duplicate multiplicities, projection positions, ordering and
  numeric tolerance are checked. Truncated evidence cannot pass.
- Exposure references join the original CSVs using independent dictionaries and Decimal
  arithmetic. Correct portfolio identity, sector sets and finite percentages must match
  within 0.005001 percentage points.
- `answer_verification` infers explicit scalar/list/table/exposure coverage from references.
  All required result rows/fields or sector percentages must be stated. Multi-column numeric
  answers use tables in tool-column order. Wrong scalars, missing rows, swapped table values,
  conflicting list counts and clear empty-result contradictions fail even without a configured
  narrative rule. All ten supplied question formats have positive and adversarial tests.
- Additional focused assertions in [faithfulness.json](../evaluation/faithfulness.json) remain
  separate. Their legacy status is not the entire v3 answer-verification result.
- `answer_correct` requires correct status/reference evidence and no failed final-answer check.
  `passed` additionally requires the expected analytical tool multiset. Extra discovery SQL can
  therefore fail strict routing despite a correct result.
- `sql_efficiency` records generated/reference query plans and SQLite progress callbacks with
  interval one. `efficiency_score = 100 * min(1, reference work / generated work)` for a correct
  answer; incorrect SQL/answers receive zero. Efficiency never overrides correctness. Engine
  callbacks are an approximate VM-work metric, not logical page/disk I/O. `logical_page_reads`
  stays null. Small-data scores do not establish production query performance.

The answer checker verifies explicit supported formats, not arbitrary English entailment.
Unsupported paraphrases, omitted fields or reordered prose columns can be conservatively
rejected. Extra unstructured claims, advice and every possible negation are not certified.
Handling cases have no factual answer contract and are not counted as successful narrative
verification. No LLM judge or extra judge SDK calls are used.

Reports identify evaluator version, data/suite/runtime hashes, configured model, actual SDK
metrics and generation mode. Injected fake backends are explicitly labeled non-live. Missing
provider usage remains unknown. Service, pacing, backoff and end-to-end time are distinct.

## Controlled metadata-RAG experiment

Run `uv run python scripts/rag_ablation.py --output reports/local/rag-new --trials 2` from a
clean checkout with sufficient quota. It alternates conditions and reverses their order on
the second trial. One client, isolated CSV-loaded database, full schema, catalogue, tools,
temperature and evaluator are shared; only retrieved context changes. The usual local/cache
paths and any judge model are absent. The 6.5-second SDK interval is experiment-only.

The [8 November comparison](../reports/rag-ablation-2026-11-08/README.md), source `e862996`,
completed its first ten-question paired pass: both conditions 10/10, 21 SDK calls, 48,271
tokens off versus 54,074 on. No SQL-work-score improvement occurred (95.52 mean each).
Service time includes transport; its descriptive bootstrap interval (-19.70% to +61.64%
for on-minus-off relative mean) does not establish a reliable speed change.

The planned repeat encountered four provider-transient errors, including a 504, and left seven subsequent entries
blocked before any SDK call. The captured legacy `complete=true` only meant forty schedule
rows existed; it does not certify forty genuine model executions or complete two-pass
accuracy. The raw capture is unchanged. The primary analysis uses the first complete
prescheduled trial; a separately labeled post-hoc sensitivity includes fifteen fully
answered, error-free pairs. These are not stitched into a new complete run. A separate
one-call recovery probe also returned 504 and is excluded from both conditions.

The benchmark runner was corrected after this capture to stop on an open circuit, mark
pre-SDK blocked rows incomplete and omit zero-call timing pairs. A regression test prevents
that completion-label mistake. Ordinary application retrieval defaults were not changed.

## Current and historical evidence

The archived [schema-graph comparison](https://github.com/Shaunakrane914/PortiQ/blob/8a6143c96d1780f1890ff8d7db1c92cc5dbdd4a8/reports/graph-rag-2026-11-08/README.md), source
`7caf262`, completed all twenty entries: full schema 10/10 versus graph 9/10, with 21 SDK
attempts each. Reported tokens were 48,296 versus 35,352 (26.80% lower); one graph attempt
returned 504 without usage metadata. No reliable latency gain was demonstrated. Question 7
had every required table but dropped bonds from its value denominator. Offline metadata
coverage for 10 supplied and 46 extended data cases is not an accuracy score. The graph
implementation and its reproduction commands now live only on the archive branch;
[the engineering decision](ENGINEERING_NOTES.md#schema-graph-retrieval-archived) explains
its removal. The active comparison runner supports basic BM25 versus full schema only.

| Evidence | Recorded result | Scope |
|---|---|---|
| [Fresh supplied CLI capture](../reports/supplied-v3-2026-11-08/README.md), `b8db4a9` | **10/10 supplied**, 21 SDK calls, 54,075 reported tokens | Evaluator v3; all ten explicit answer-format checks passed; cache/local disabled |
| [First v3 supplied capture](../reports/supplied-v3-2026-11-08/supplied.json), `f3a9954` | **8/10**, 21 SDK calls, 54,076 tokens | Two false negatives for correct exposure tables with percentage units in their header; raw failed run retained |
| [Retained CLI-only capture](../reports/cli-2026-11-08/README.md), `4b49d95` | 50/50 extended; 92 SDK calls; 201,404 reported tokens | Evaluator v2: 46 data and four handling cases; six configured narrative cases |
| [Original-agent supplied capture](https://github.com/Shaunakrane914/PortiQ/blob/95436a7/reports/v0.2.0/supplied.json) | 10/10 | Historical source/evaluator, not current v3 certification |
| [Original-agent extended capture](https://github.com/Shaunakrane914/PortiQ/blob/95436a7/reports/v0.2.0/extended.json) | 50/50; 97 SDK calls; 266,304 tokens | Historical comparison, not a controlled latency experiment |
| [v0.1.1 supplied](https://github.com/Shaunakrane914/PortiQ/blob/95436a7/reports/v0.1.1/supplied.json) / [extended](https://github.com/Shaunakrane914/PortiQ/blob/95436a7/reports/v0.1.1/extended.json) | 10/10 / 50/50 | Historical release evidence |

The fresh supplied run took 132.471 seconds of CLI wall time, with 13.143-second mean and
19.520-second p95 question time, including its child-process-only 6.5-second batch spacing.
No normal pacing settings or ledger records were reset. It is a full independent run, not
a rescore or retry of only the failed questions. Later GUI work changed Streamlit startup
and presentation, with separate key-free AppTest and actual-server Playwright checks.
Subsequent experimental retrieval controls have their own pinned source and paired evidence
above; the historical supplied capture is not silently recertified for those modes.

The retained eight CLI capture files remain byte-exact and have
[SHA-256 hashes](../reports/cli-2026-11-08/artifact-sha256.json). Their original scores, failures,
runtime hashes and six-case narrative coverage are not rewritten to imply v3 checks.
Earlier reports removed from the current tree remain accessible at the pinned history links.

## Key-free verification

Ruff, format, mypy, pytest and browser/container checks do not spend Gemini quota. Streamlit's
AppTest runs with explicit local mode and no key. Concurrency tests synchronize injected fake
provider calls and check quota/session isolation; they are not live accuracy results.
See [enhancements](ENHANCEMENTS.md) for the production/concurrency verification scope.
