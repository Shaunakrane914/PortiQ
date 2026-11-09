# Evaluation methodology and evidence

`uv run portfolio-agent evaluate` selects the original [ten supplied questions](../ground_truth_dataset.json),
eight SQL and two exposure. `--suite extended` selects the separate author-created
[50-question regression](../evaluation/extended.json). Runtime planning never reads
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

## Evaluator v4: answer verification and SQL efficiency

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
  All required result rows/fields or sector percentages must be stated. Tables retain tool
  column order; explicit label/value pairs and named min/max aggregate prose are also
  supported, with each value bound to its own label and conflicting claims rejected.
  Wrong scalars, missing rows, swapped table values,
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
  callbacks are an approximate VM-work metric. Optional `--profile-io` (performance extra)
  measures SQLite pager cache hits + misses for both queries on matched fresh private caches.
  Result rows must independently agree before scoring; engine/cache metadata and both VM and
  page metrics are recorded. Pager accesses are not physical storage reads or SQL Server's
  exact I/O accounting. See [measurement details](OPERATIONS.md#performance-aware-evaluation).

Hybrid verification masks only explicitly sector-bound percentages from SQL scalar checks;
those percentages remain independently checked against the exposure reference. Both
`Technology: 93%` and `93% in Technology` are supported, as are typed percentage tables.
Unrelated wrong/negated scalar claims still fail. Required tool results remain distinct;
omitting either analytical tool cannot pass. The three archived hybrid answers now pass
replay, while wrong/missing/contradictory claim mutations fail. These replays make zero model
calls and are separate from live evidence. If evaluation fails after an answer was generated,
its actual SDK/token metadata is retained rather than silently discarded.

The answer checker verifies explicit supported formats, not arbitrary English entailment.
Unsupported paraphrases, omitted fields or reordered prose columns can be conservatively
rejected. Extra unstructured claims, advice and every possible negation are not certified.
Handling cases have no factual answer contract and are not counted as successful narrative
verification. No LLM judge or extra judge SDK calls are used.
Multiple independent scalar references or overlapping exposure narratives can still require
explicit separable formatting; this is not an unrestricted natural-language entailment judge.
Descriptions such as "sectors with no securities" do not imply an empty overall result.

Reports identify evaluator version, data/suite/runtime hashes, configured model, actual SDK
metrics and generation mode. Injected fake backends are explicitly labeled non-live. Missing
provider usage remains unknown. Service, pacing, backoff and end-to-end time are distinct.

## Archived metadata-RAG experiments

Retrieval was evaluated and removed from the active architecture. Reproduction scripts and
retrieval-specific tests remain only on the archive branches linked in the
[engineering decision](ENGINEERING_NOTES.md#metadata-retrieval-evaluated-and-excluded).
The paired BM25 experiment alternated conditions, sharing one client, isolated CSV-loaded
database, full schema, catalogue, tools, temperature and evaluator. Only the appended
retrieved context changed. Its 6.5-second SDK interval was experiment-only; local answers,
answer cache and judge models were disabled.

The [8 November comparison](https://github.com/Shaunakrane914/PortiQ/blob/d65927b2e59e07c76ff3795e1395c0724a439241/reports/rag-ablation-2026-11-08/README.md), source `e862996`,
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

The archived benchmark runner was corrected after capture to stop on an open circuit, mark
pre-SDK blocked rows incomplete and omit zero-call timing pairs. Its regression test is
preserved with the experiment. Ordinary evaluation does not contain a retrieval mode switch.

## Current and historical evidence

The [new-key retest](../reports/retest-2026-11-09/README.md), source `2a68b74`, completed
the previously quota-blocked three-user hybrid conversation protocol: all nine fresh
answers and session follow-ups passed, with 22 SDK attempts, 40,972 reported tokens and
no quota responses. A separate fresh supplied CLI run passed 10/10 under v4, with 21
SDK attempts and 48,292 reported tokens. Both disable local/cache/fallback answers.

The fresh extended v4 run completed all fifty cases at **48/50**, including all three
hybrids. Questions 12 and 13 failed after provider HTTP 504s; cases 26 and 41 recovered
within their bounded retries. Six SDK errors had unreported usage. A separate post-run
retry of only questions 12 and 13 passed 2/2; it is not stitched into a 50/50 full score.

The [earlier 9 November verification](../reports/assurance-2026-11-09/README.md) includes a fresh
supplied v4 CLI pass at `a3b9b24` (10/10, 21 SDK attempts, 48,249 reported tokens, measured page
accesses), a final-source offline replay at `bfcca5e` (50/50 archived answers, 46 wrong-prose
mutations rejected) and actual HTTP/Docker checks. The subsequent real-provider conversation
attempt accepted four correct answers but hit daily quota on two others and did not complete
its planned nine questions. Those original failed/incomplete captures remain intact;
the new retest is independent. None of these scopes is substituted for another.

The archived [schema-graph comparison](https://github.com/Shaunakrane914/PortiQ/blob/8a6143c96d1780f1890ff8d7db1c92cc5dbdd4a8/reports/graph-rag-2026-11-08/README.md), source
`7caf262`, completed all twenty entries: full schema 10/10 versus graph 9/10, with 21 SDK
attempts each. Reported tokens were 48,296 versus 35,352 (26.80% lower); one graph attempt
returned 504 without usage metadata. No reliable latency gain was demonstrated. Question 7
had every required table but dropped bonds from its value denominator. Offline metadata
coverage for 10 supplied and 46 extended data cases is not an accuracy score. The graph
implementation and its reproduction commands now live only on the archive branch;
[the engineering decision](ENGINEERING_NOTES.md#metadata-retrieval-evaluated-and-excluded)
explains why both retrieval strategies and their comparison runners were removed from main.

| Evidence | Recorded result | Scope |
|---|---|---|
| [New-key supplied v4 CLI](../reports/retest-2026-11-09/supplied-first/supplied.json), `2a68b74` | **10/10**, 21 SDK attempts, 48,292 reported tokens | Fresh generation on the final verifier/context runtime; all ten answer checks, measured SQL pager work |
| [New-key extended v4 CLI](../reports/retest-2026-11-09/extended-first/extended.json), `2a68b74` | **48/50**, 94 SDK attempts, 198,790 reported tokens | Fresh full run; two provider-timeout failures, all three hybrids pass; six attempts have unknown usage |
| [Separate provider recovery](../reports/retest-2026-11-09/provider-recovery.json), `2a68b74` | **2/2**, 4 SDK attempts, 9,307 reported tokens | One post-run retry of the two failed questions; original full score remains 48/50 |
| [New-key live concurrent conversations](../reports/retest-2026-11-09/live-conversations.json), `2a68b74` | **9/9**, 22 SDK attempts, 40,972 reported tokens | Three concurrent users, three turns each; both tools, isolated session follow-ups; no quota failures |
| [Fresh supplied v4 CLI](../reports/assurance-2026-11-09/supplied/supplied.json), `a3b9b24` | **10/10**, 21 SDK attempts, 48,249 reported tokens | Fresh generation, all ten final-answer checks, eight SQL page profiles; later compatible verifier/context fixes have separate proof |
| [Final historical replay](../reports/assurance-2026-11-09/historical-replay-final.json), `bfcca5e` | **50/50**, 46 bad-prose mutations rejected | Offline archived answers; zero provider calls; not a fresh 50-question model run |
| [Full-schema CLI capture without RAG](../reports/supplied-no-rag-2026-11-09/README.md), `0b3e94a` | **10/10 supplied**, 21 SDK attempts, 48,293 reported tokens | Evaluator v3; all ten explicit answer checks passed; no active retrieval, cache/local disabled, zero provider errors |
| [Post-removal supplied CLI capture](../reports/supplied-after-graph-removal-2026-11-08/README.md), `f14ea21` | **10/10 supplied**, 21 SDK attempts, 54,093 reported tokens | Evaluator v3; all ten explicit answer checks passed; full schema/basic BM25, graph removed, cache/local disabled |
| [Fresh supplied CLI capture](../reports/supplied-v3-2026-11-08/README.md), `b8db4a9` | **10/10 supplied**, 21 SDK calls, 54,075 reported tokens | Evaluator v3; all ten explicit answer-format checks passed; cache/local disabled |
| [First v3 supplied capture](../reports/supplied-v3-2026-11-08/supplied.json), `f3a9954` | **8/10**, 21 SDK calls, 54,076 tokens | Two false negatives for correct exposure tables with percentage units in their header; raw failed run retained |
| [Retained CLI-only capture](../reports/cli-2026-11-08/README.md), `4b49d95` | 50/50 extended; 92 SDK calls; 201,404 reported tokens | Evaluator v2: 46 data and four handling cases; six configured narrative cases |
| [Original-agent supplied capture](https://github.com/Shaunakrane914/PortiQ/blob/95436a7/reports/v0.2.0/supplied.json) | 10/10 | Historical source/evaluator, not current v3 certification |
| [Original-agent extended capture](https://github.com/Shaunakrane914/PortiQ/blob/95436a7/reports/v0.2.0/extended.json) | 50/50; 97 SDK calls; 266,304 tokens | Historical comparison, not a controlled latency experiment |
| [v0.1.1 supplied](https://github.com/Shaunakrane914/PortiQ/blob/95436a7/reports/v0.1.1/supplied.json) / [extended](https://github.com/Shaunakrane914/PortiQ/blob/95436a7/reports/v0.1.1/extended.json) | 10/10 / 50/50 | Historical release evidence |

The historical `b8db4a9` supplied run took 132.471 seconds of CLI wall time, with 13.143-second mean and
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
