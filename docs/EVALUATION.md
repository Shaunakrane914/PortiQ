# Evaluation methodology — v0.1.1

Production modules never import benchmark questions, IDs, expected SQL, or narrative rules.
The supplied ten and additional fifty remain unchanged. See the [report index](../reports/README.md)
for release evidence and clearly labeled historical runs. All fresh runs are uncached.

## Independent dimensions

- `status_correct`: answer/clarification/unsupported status agrees with the case contract.
- `result_correct`: all independent reference results match distinct successful tool results.
  It is null for subjective handling cases without a reference result.
- `routing_correct`: the successful analytical tool multiset exactly matches the required
  multiset. Extra discovery calls fail this strict efficiency contract. For clarification
  and unsupported cases, the existing status-based handling contract is preserved.
- `faithfulness`: passed/failed/not_checked for explicitly configured, finite narrative assertions.
- `answer_correct`: correct status, correct reference evidence where applicable, and no
  failed configured narrative assertion. This operational measure does not certify unchecked prose.
- `passed`: `answer_correct AND routing_correct`. No incorrect route is forgiven to improve
  the strict score. Configured narrative assertions can make this stricter than evaluator v1.

Every dimension is evaluated even when routing is wrong. Per-reference candidate comparisons,
expected and actual data, and all dimension-specific failures are retained. A case with a
harmless extra discovery call can have correct results but incorrect routing. A valid SQL
query against the wrong column can have `sql_valid=true` and `result_correct=false`.

For answers with extra calls, correctness requires an injective assignment of all reference
results to matching tool evidence, rather than blindly taking the first or last call. This
does not prove that every extra query is useful; strict routing still fails. Additional
narrative assertions prevent some false conclusions from hiding behind correct intermediate data.

## Structured result comparison

Trusted reference SQL executes on an independent read-only connection. Every generated query
is independently re-executed through the safety boundary, and its result must agree with
the recorded tool result. Claimed columns, truncation, projection width, rows and numerical
values are checked. Aliases may differ from the reference, but projection position matters.

Numeric cells use relative tolerance 1e-7 and absolute tolerance 1e-6. NULL differs from zero;
strings do not equal numbers. Top-level reference ORDER BY requires ordered comparison.
Unordered rows use a maximum bipartite match to preserve duplicates and handle tolerance
overlap. Ordered ties currently follow reference execution order, which can penalize another
valid tied order. Empty results have limited discriminatory power.

Exposure references read original CSVs and join with Python dictionaries independently of
the production calculator and resolver. Sector sets, portfolio identity, finite values and
every percentage must match within 0.005001 percentage points. NaN/Infinity cannot pass.

## Limited narrative assertions

`evaluation/faithfulness.json` defines additional contracts separately from the unchanged
reference suites. The sidecar is loaded only by evaluation; it never enters a runtime prompt.
The configured subset covers total portfolio count, selected scalar financial answers,
portfolio-name lists, single-portfolio exposure claims, and one hybrid case.

Assertions check numerical presence and contradictory portfolio counts; required/mismatched
portfolio identities; stated canonical sector percentages; and explicit "no portfolios/no
results" claims that contradict a nonempty reference. Scalar amounts support commas and
thousand/million/billion abbreviations. Declared decimal precision determines rounding
tolerance; portfolio counts require the exact count. Percentage checks permit rounding to
the number of decimals actually stated. Unknown canonical sectors with claimed exposure fail.

This is not an LLM judge or a complete natural-language verifier. It does not certify
unsupported recommendations, all synonyms/negations, arbitrary new entity names, every
table layout, or all prose. A configured exposure case with no recognizable identity or
percentage claims can remain `not_checked`. Exact name-list contracts require every name.
There can be false positives for complex contextual comparisons or negations. Reports expose
every actual assertion and count checked/failed cases; unchecked cases are not advertised
as narrative-faithfulness successes. CI includes wrong numbers, wrong identities, invented
sector percentages, contradictions, missing coverage, legitimate rounding and invalid contracts.
Non-answer statuses receive `not_checked` with the configured rules retained for audit;
provider error codes are never interpreted as factual numerical claims.

## The original ext-02 failure

Both v0.1.0 extended report Git blobs remain byte-for-byte unchanged. Their 49/50 failure involved
wrong semantics: the agent filtered `strategy_type` for a value stored under `status`, then
claimed no relevant portfolios existed. Evaluator v1 stopped at the extra-call failure.
`scripts/review_diagnostics.py` re-scores those exact traces offline with independent references
and reports routing, result and narrative failures. This is diagnostic re-scoring, not a new
Gemini run. The old release description understated the error and has been corrected.

## Fresh validation and provenance

The 50 author-created cases were frozen before their first v0.1.0 run: 34 SQL, 9 exposure,
3 hybrid, 2 clarification and 2 unsupported/security cases. Splits remain 17 development,
17 validation, 16 heldout. All have now been observed, so v0.1.1 reruns are regression tests,
not new unseen validation. The three categorical regressions are explicit development cases.

`scripts/release_evaluation.py` runs the categorical suite twice, the supplied set once by
default (configurable), and all 50 extended cases. Output defaults to ignored local reports;
`--output-dir reports/v0.1.1` publishes a versioned release evidence set without overwriting v0.1.0.

Reports include evaluator version, model/provider versions, categorical runtime source hashes,
suite and narrative-rule hashes, configuration/budgets, per-case evidence, all failure dimensions,
API calls, token totals, pacing-inclusive mean/p95 latency and timestamp. SDK automatic retries
are disabled; bounded application transport retries count every backend invocation. Mock tests
and offline re-scoring are never counted as fresh live AI accuracy.
