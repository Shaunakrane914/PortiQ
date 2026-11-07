# Evaluation and verification report index

Use the versioned release reports below. Files whose names contain `final` at the top
level are historical v0.1.0 development evidence, not the newest release score.

## v0.1.1 — release evidence

| Artifact | Purpose |
|---|---|
| [semantic.json](v0.1.1/semantic.json) / [summary](v0.1.1/semantic.md) | **6/6** fresh, repeated categorical-column regressions |
| [supplied.json](v0.1.1/supplied.json) / [summary](v0.1.1/supplied.md) | **10/10** fresh supplied benchmark under evaluator v2 |
| [extended.json](v0.1.1/extended.json) / [summary](v0.1.1/extended.md) | **50/50** fresh full regression on the final runtime |
| [ambiguity-regression.json](v0.1.1/ambiguity-regression.json) / [summary](v0.1.1/ambiguity-regression.md), [exact case](v0.1.1/ambiguity-regression-suite.json) | **3/3** targeted ambiguity checks after strengthening original-reference preservation |
| [preflight/error-gated-runtime/extended.json](v0.1.1/preflight/error-gated-runtime/extended.json) / [summary](v0.1.1/preflight/error-gated-runtime/extended.md) | Earlier full regression: **48/50**; ext-46/47 failed with provider HTTP 503/504 after both bounded attempts |
| [preflight/error-gated-runtime/provider-retry.json](v0.1.1/preflight/error-gated-runtime/provider-retry.json) / [summary](v0.1.1/preflight/error-gated-runtime/provider-retry.md) | Separate retry **1/2**: hybrid recovered; ambiguity case incorrectly guessed Growth Equity Fund. Motivated the original-reference contract fix; not merged into any full score |
| [preflight/error-gated-runtime/supplied.json](v0.1.1/preflight/error-gated-runtime/supplied.json), [semantic.json](v0.1.1/preflight/error-gated-runtime/semantic.json), [replay.json](v0.1.1/preflight/error-gated-runtime/replay.json) | Earlier runtime: 10/10 supplied, 6/6 categorical and 63 deterministic tool results replayed; before ambiguity-contract strengthening |
| [preflight/quota-limited-extended.json](v0.1.1/preflight/quota-limited-extended.json) / [summary](v0.1.1/preflight/quota-limited-extended.md) | Previous attempt: 34/50; first 34 passed, remaining 16 returned daily-quota HTTP 429. Preserved before fixing error-message narrative classification |
| [preflight/supplied.json](v0.1.1/preflight/supplied.json), [preflight/semantic.json](v0.1.1/preflight/semantic.json) | Previous runtime checks: 10/10 supplied and 6/6 categorical; before the evaluator's non-answer gating fix |
| [verification.json](v0.1.1/verification.json), [replay.json](v0.1.1/replay.json), [performance.json](v0.1.1/performance.json) | Local/hosted checks, deterministic offline replay, and microbenchmark samples; not additional live model scores |
| [clean-install.json](v0.1.1/clean-install.json) | Exact-runtime Python 3.11 clean installation, full tests and credential-free database/CLI checks |
| [historical-ext02.json](v0.1.1/historical-ext02.json) | Offline diagnostics of both original failed traces, with original file hashes |
| [passive-live-initial.json](v0.1.1/passive-live-initial.json) | Initial real-Gemini fix confirmation before the complete release run |
| [development-wide-context-supplied.md](v0.1.1/development-wide-context-supplied.md) / [JSON](v0.1.1/development-wide-context-supplied.json) | Retained 7/10 development run: unrelated industry aliases and projection errors |
| [development-wide-context-semantic.md](v0.1.1/development-wide-context-semantic.md) | Retained 6/6 categorical development cases from that broader context |
| [development-wide-context-interrupted.json](v0.1.1/development-wide-context-interrupted.json) | Incomplete extended run stopped after the supplied regressions were observed |
| [development-narrow-context-supplied.md](v0.1.1/development-narrow-context-supplied.md) / [JSON](v0.1.1/development-narrow-context-supplied.json) | Retained 9/10 development run, exposing an implicit ordering mismatch |

Fresh reports distinguish `result_correct`, `answer_correct`, `routing_correct`, and
limited `faithfulness` assertions. `passed` remains the strict combined score. A passing
limited assertion is not certification of all model prose. The extra questions are
author-created development/regression cases, not a new blind benchmark.

## v0.1.0 — preserved historical evidence

| Artifact | Classification and recorded result |
|---|---|
| [supplied-release.md](supplied-release.md) / [JSON](supplied-release.json) | v0.1.0 release: 20/20 across two fresh trials |
| [supplied-final.md](supplied-final.md) / [JSON](supplied-final.json) | **Pre-release development run: 16/20**, superseded by supplied-release; filename retained for provenance |
| [supplied-flash-lite.md](supplied-flash-lite.md) | Earlier development run: 6/10 |
| [supplied-initial.md](supplied-initial.md) | Earlier quota-limited run: 1/10 |
| [supplied-paced.md](supplied-paced.md) | Earlier quota/projection failures: 2/10 |
| [supplied-flash36.md](supplied-flash36.md) | Alternate model API failures: 0/10; not a capability estimate |
| [extended-final.md](extended-final.md) / [JSON](extended-final.json) | First frozen 50-case run: 49/50 |
| [extended-regression.md](extended-regression.md) / [JSON](extended-regression.json) | Later v0.1.0 regression: 49/50 |
| [catalogue-development.json](catalogue-development.json), [planner-development.json](planner-development.json), [sql-planner-development.json](sql-planner-development.json) | Small supplied-development diagnostics, not complete benchmark scores |
| [transport-interrupted.json](transport-interrupted.json) | Explicitly incomplete run interrupted to implement transport retries |
| [verification.json](verification.json) | v0.1.0: 116 tests passed, one skipped; 92.95% overall coverage |
| [performance.json](performance.json) | v0.1.0 local 200-iteration SQL/exposure samples |
| [replay.json](replay.json) | Offline compatibility replay of 70 v0.1.0 tool results; not new live accuracy |

**Correction to the old release summary:** `ext-02` was a semantic failure as well as
an extra-call failure. Both old runs queried `strategy_type='Passive'`, returned no matching
portfolios, and falsely concluded that none existed. The expected three portfolios have
`status='Passive'`. Evaluator v1 stopped at routing, leaving this result failure obscured.
The original JSON/Markdown evidence and Git tag remain unchanged; the v2 offline diagnostic
reports routing, result correctness and narrative assertion failures independently.
