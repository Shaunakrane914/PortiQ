# Engineering decisions and evidence

The original [assignment](assignment/README.md) prioritizes a simple working CLI, accurate tool results, a supplied-ground-truth evaluator and brief documentation. [Submission](SUBMISSION.md) provides the requirement map; this document records why the implementation and optional extensions take their current form.

## Current decisions

- **CLI first.** `chat` accepts questions directly; `ask` handles one question; `evaluate` defaults to the supplied ten. The base package needs no web/Node runtime. The optional dashboard is a reviewer convenience, not a required component.
- **Manual typed tools.** Gemini selects SQL/exposure/respond. Python validates arguments, enforces SQL safety and performs deterministic arithmetic. Neither hardcoded benchmark answers nor schema retrieval frameworks replace question interpretation.
- **Compact metadata, one supported orchestrator.** Nine tables fit complete schema context. Formatting is compacted without changing parsed SQL structure; live portfolio domains prevent status/strategy confusion, and the catalogue supports safe name resolution. The removed experimental planner remains absent.
- **Accuracy before savings.** Supported explicit scalar-only requests can directly render one validated SQL cell after real Gemini generation. Other shapes and guarded compound requests retain synthesis. Usage/rendering labels expose the distinction. A faster wrong planner was previously rejected.
- **Deterministic financial authority.** Stock weights normalize within equities, excluding bonds. Recorded weights, market-value arithmetic, supplied AUM and optional reconstructed weights are separate bases. [Data conventions](DATA_ASSUMPTIONS.md) prohibit inferred cash, FX, AUM scaling or live-data repairs.
- **Simple SQLite persistence.** File-backed atomic initialization and read-only query connections support CLI process reuse and the API. The brief's in-memory hint is recorded as a setup difference, rather than claiming an unsupported mode.
- **Optional local/cache/context.** Four explicit capabilities, a 64-entry/300-second exact cache and bounded ephemeral sessions share the service layer. They are labeled, opt-in in CLI, visible in UI, and bypassed by live evaluation.
- **Measured provider use.** Actual SDK invocations, reported input/output/total tokens, unknown thinking usage, service, pacing and backoff remain separate. SDK automatic retries are disabled; bounded application retry/circuit/fallback and an optional shared daily ledger do not claim Google's quota authority.
- **Small optional platform.** One worker/one concurrent analysis, static same-origin assets and an explicitly anonymous Render demo match the selected review scope. Production multi-user controls, general concurrency, RAG/GraphRAG and logical-I/O scoring are deferred.

## Latest CLI-only evidence: 8 November 2026

The [published CLI run](../reports/cli-2026-11-08/README.md) invokes `portfolio-agent evaluate --suite extended` as a real subprocess on `4b49d95`. All fifty frozen questions run with local/cache disabled. It passed **50/50**, including 46 reference-data and four handling cases, with **92 SDK invocations**, **201,404 reported tokens** and zero provider errors. All six configured narrative cases passed; separate assistant review found no visible value/handling mismatch across the complete answers.

Process wall time was 593.976 seconds; question mean/median/p95 were 11.856/12.938/13.496 seconds, with mean service/pacing of 2.581/9.262 seconds. Pacing-inclusive CLI timings are not model-only or hosted latency. The shared daily ledger moved from 120 to 212 under a user-approved process-only 300-attempt cap. Normal defaults and Google billing were unchanged. These are capture-time counts, not current quota balances.

All 603 database rows matched the supplied CSVs and all 78 frozen input/historical Git blobs matched the baseline. Exact capture bytes, source hashes, transcript and unknown usage fields are published. The archived original extended run also scored 50/50 with 266,304 tokens: the latest run used 24.37% fewer, with no observed regression on those cases. It is a historical comparison, not a controlled causal latency experiment or unseen validation.

## Earlier scalar/prompt comparison

A small original/optimized comparison alternated order on one reused 6.5-second-paced backend. Original/optimized SDK service was 4.160/1.215 seconds for explicit Bond count, 2.695/2.781 for Passive names and 2.189/2.643 for Balanced exposure. Calls/tokens were 2/5,284 versus 1/2,023 for count; both other cases retained two calls with fewer prompt tokens. All six answers passed their checks.

Service includes transport. The prompt reduction did not show a consistent service-time gain for the list/exposure cases. Sequential end-to-end medians were 12.841/13.128 seconds because they included pacing inherited from prior requests. A separate fresh-browser scalar check recorded 1.518 seconds of API analysis and one SDK call; a hosted probe recorded 1.939 seconds. These isolated captures do not guarantee future latency. Raw paired/browser observations remain local; the later full CLI evidence above is versioned.

An adaptive 60-second rolling quota controller (`AdaptiveRateLimiter`) with a 12 RPM safety ceiling governs SDK calls with 0s default pacing and question-level cooldown, reducing live hosted latency on Render to ~1.8–2.6s. The existing HTTP socket-client rate limit is a separate control.

## Historical experiments and cleanup

These pre-cleanup observations describe their recorded revisions. Removed source/evidence remains in the [archive](https://github.com/Shaunakrane914/PortiQ/tree/ace58054c7a778817d68a7c1d81386b7dffd95e8).

| Suite | Original orchestration | Removed experimental planner |
|---|---:|---:|
| Supplied | 10/10; 21 SDK calls; 58,116 tokens | 9/10; 10 calls; 25,239 tokens |
| Extended | 50/50; 97 calls; 266,304 tokens | 50/50; 50 calls; 124,739 tokens |
| Platform | 8/8; 15 calls; 40,719 tokens | 7/8; 8 calls; 19,956 tokens |

The completed comparison recorded 201 SDK invocations and 535,073 tokens with no provider failures. The experimental Technology-sector query returned thirteen portfolios instead of eight; an ambiguous reference was also guessed. Lower call counts did not justify promotion. Cleanup `122dee6` removed that planner, merged rendering into `agent.py` and reduced documentation/helpers. Only the original orchestrator remains supported, with the later guarded scalar rendering change.

An earlier interrupted attempt exhausted its 250-invocation guard after 36 successes, 27 transient failures, one timeout and 186 connection failures. A fresh-client probe later succeeded; cause is unproven. Failed fragments were not stitched into a passing run. Archived reporting quirks (`repair_questions` including focused planning, a combined false progress marker) remain documented rather than rewritten.

The v0.1.0 Passive/status error was semantic and narrative, not merely extra routing. v0.1.1's live categorical domains and stronger result/narrative checks corrected it. Historical supplied 10/10, extended 50/50 and categorical/ambiguity scores remain tied to their original captures, not relabeled as current tests.

Offline benchmarks use one helper:

```powershell
uv run python scripts/benchmark.py --mode tools --output reports/local/tools-new.json
uv run python scripts/benchmark.py --mode cache --output reports/local/cache-new.json
```

They refuse existing output names and spend no Gemini quota. Historical cache/local samples measured warm Python service, not browser/public API latency. Alternative-model comparisons, schema-context ablations and hedging were not assigned invented results. Public hosting was deferred in those old experiments; a Render review demo was subsequently deployed.

## CI and review

CI preserves four Ubuntu/Windows x Python 3.11/3.13 jobs and a separate Playwright/container job. Repeated `setup-uv` GitHub Release downloads returned HTTP 504 before tests; `84d296a` switched to runner Python via `actions/setup-python@v6` plus the same pinned `uv==0.11.26` from PyPI. `UV_PYTHON_DOWNLOADS=never` keeps the selected interpreter, and matrix fail-fast is disabled so every job can finish. All five jobs passed on that commit. Future check results belong to their own revisions.

The recorded application verification passed 212 Python tests with two live skips, eight offline browser tests and a real non-root container HTTP check. CI is key-free. Fresh model evaluations require explicit quota and are separate from test/replay scores. The owner's later cleanup removed failed Actions runs; versioned model-evaluation evidence was not deleted or altered.

Reviewers should start with CLI quick start, supplied evaluation, the published full CLI regression and then the optional dashboard. Explain SQL safety versus semantic correctness, equity versus whole-portfolio denominators, unknown AUM currency/valuation conventions, actual SDK accounting and why faster incorrect behavior was rejected. External blind cases and stronger isolation would add more evidence than additional framework layers.
