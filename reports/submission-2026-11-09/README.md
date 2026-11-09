# Frozen prompt-removal experiment ? incomplete

Runtime: `1c2cc5962de2d2c43c554bd7969ad372b84afbdc`; data and holdout seal:
`4843a7d9dbcebbf6bab3e5987b0689fd4c515fc8`. Source hashes matched before the run and
when inspected after interruption. This is evidence about that runtime, not a fresh
accuracy certification of the later structural refactor.

| Run | Observed outcome | SDK attempts | Reported tokens |
| --- | --- | ---: | ---: |
| Supplied ten | **5/10 strict**, one complete native CLI trial | 12 | 30,887 |
| Extended fifty | **28 completed cases passed; 22 not executed** | 28 | 69,500 |
| Prospective holdout | Sealed after runtime freeze; **not executed** | 0 | 0 |
| Recorded CLI count | Correct result 13, cache disabled | 1 | 2,422 |

The extended process ended before completing during a task transition; the exact termination
cause was not established. No parent or evaluation process remained. Its native progress
capture is retained byte-for-byte as [extended-partial.json](extended-partial.json).
There is **no full extended score**, no held-out score and no selective replacement of cases.

[Supplied raw results](supplied.json), [native terminal output](supplied-stdout.txt),
[run manifest](run-manifest.json), [campaign summary](summary.json) and the
[genuine CLI transcript](CLI_TRANSCRIPT.md) are retained. The raw CLI response is also
available in [cli-1.json](cli-1.json), so reviewers do not need a Gemini key to inspect it.

## What the failures establish

Supplied cases 3, 5, 6, 7 and 8 failed the unchanged strict oracle after default answer
projections, unconditional ordering/join patterns and the supplied diversification formula
were removed. Case 3 returned additional fields with correct reference data; case 6 used
a different ordering. Cases 5 and 7 omitted reference fields; case 8 selected other metrics.
These are real strict failures, not provider downtime. The data-only diagnostic passes
6/10 but does not override strict scoring or certify arbitrary narrative correctness.
The result cannot be described as an improvement in assignment accuracy.

General financial definitions, schema/domain context, SQL protections and equity arithmetic
remained. This experiment does not prove that legitimate business definitions should be
removed. The subsequent maintainability refactor preserves this captured runtime's behavior
and has separate AST, rendering, request-schema, unit and UI verification.

## Measurement limits

Normal bounded repairs/retries remained enabled. Model: `gemini-3.1-flash-lite`. Live evaluation
used no local answers, cache or fallback models, with 6.5-second SDK spacing and optional
correctness-gated SQLite pager measurement. Evaluation duration includes pacing and oracle
work; it is not an interactive latency claim. Per-question API, token, service, pacing,
backoff, tool and SQL-work metrics are in the raw JSON. 0 provider-error
attempts and 0 unknown-usage attempts were recorded among
41 SDK attempts, including the later CLI transcript.

The 20-question set was authored after freezing, validated offline and sealed before any
held-out model call. It remains unevaluated. Its author is the implementation agent;
independent external authorship or blind-validation results are not claimed.
The owner quota ledger and all original assignment inputs were preserved.
