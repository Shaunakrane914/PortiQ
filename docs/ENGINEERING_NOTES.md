# Engineering notes

The supported application uses the original Gemini orchestrator, shared read-only SQL and equity-only exposure tools, and an optional four-page API/dashboard. The experimental planner was removed in cleanup commit `122dee6` after accuracy and ambiguity regressions. Earlier measurements and detailed investigation notes remain available in the [pre-cleanup Git snapshot](https://github.com/Shaunakrane914/PortiQ/tree/ace58054c7a778817d68a7c1d81386b7dffd95e8).

## Design decisions

- **CLI first.** `portfolio-agent chat --context` provides terminal conversation. Single-question asks remain independent by default. The base installation does not need FastAPI, Node or a browser; the web extra consumes the same business logic.
- **Manual typed tool dispatch.** Gemini chooses tools, while Python validates arguments and executes them. SQL uses parsed validation, SQLite authorization, read-only connections and resource limits. Prompts do not provide the security boundary.
- **Deterministic financial authority.** Exposure uses stock `current_weight`, normalized within equities with Decimal arithmetic. Bonds are excluded. Recorded allocation and quote-value reconstruction have separate denominators; no FX, inferred cash or AUM scaling is introduced. See [data conventions](DATA_ASSUMPTIONS.md).
- **Small explicit local registry.** Count, unambiguous exposure, holdings and metadata can run without a model. Other requests use Gemini. Local/cache execution is visibly labeled; live evaluation bypasses both.
- **Exact cache and bounded context.** Deep-copied successes use data/code/model/strategy/session identity, a 64-entry LRU and 300-second TTL. Ephemeral sessions retain eight turns, compact references and selected portfolios. Ambiguous references require clarification.
- **Conservative provider handling.** Every SDK invocation consumes the configured budget, including delivery-unknown failures. Pacing, service and backoff are separate. An optional SQLite ledger coordinates processes using the same file; it is not Google's quota meter or a global scheduler. Retries and a transient-failure circuit are bounded. Explicit sequential fallback is optional; hedging is deferred.
- **Thin local platform.** Static browser assets use safe DOM construction and explicit calculation bases. The API supports one worker with optional bearer access, origin/host rules, response bounds and safe errors. Public hosting and multi-user identity/cost controls remain separate work. See [security](SECURITY.md) and [limitations](KNOWN_LIMITATIONS.md).

## Historical experiments

These observations describe recorded pre-cleanup revisions, not a fresh score for the current checkout.

| Suite | Original orchestration | Removed experimental planner |
|---|---:|---:|
| Supplied | 10/10; 21 SDK calls; 58,116 tokens | 9/10; 10 calls; 25,239 tokens |
| Extended | 50/50; 97 calls; 266,304 tokens | 50/50; 50 calls; 124,739 tokens |
| Platform | 8/8; 15 calls; 40,719 tokens | 7/8; 8 calls; 19,956 tokens |

The completed comparison used alternating strategy order, one 6.5-second-paced backend, no local/cache shortcuts and independent frozen references. It recorded 201 SDK invocations, 535,073 reported tokens and no provider failures. The experimental Technology-sector query returned thirteen portfolios instead of the required eight; another case guessed a portfolio from an ambiguous reference. Lower call counts did not justify promotion, and the experiment was later removed from runtime.

Extended median/p95 Python analysis time was 13.139/27.363 seconds for the original and 6.359/13.224 for the experimental path. Mean SDK service/pacing was 8.264/7.113 seconds versus 3.051/3.874. SDK service includes transport; these observations do not isolate inference or prove a controlled speedup. The current default retained the historical v0.1.1 call counts, and its observed extended mean was slower under different service conditions.

A separate local/cache experiment passed 80/80 checks per mode with zero SDK requests. Median/p95 warm service time was 3.90/5.15 ms locally and 2.06/2.84 ms from exact cache. These are Python timings, not HTTP targets. Both offline benchmarks now live in one helper:

```powershell
uv run python scripts/benchmark.py --mode tools --output reports/local/tools-new.json
uv run python scripts/benchmark.py --mode cache --output reports/local/cache-new.json
```

An earlier interrupted comparison exhausted its explicit 250-SDK-attempt budget after 36 successful calls, 27 transient failures, one timeout and 186 connection errors. A fresh-client probe subsequently succeeded; the root cause is unproven. Failed-run successes were not stitched into the later completed run. Raw reporting quirks also remain archived: `repair_questions` included one focused planning step, and the combined record file retained a false progress-completion marker while six per-suite reports correctly marked completion. Separate diagnostics validated all 136 records and contiguous request accounting.

Alternative-model live comparisons, schema-context ablations, hedging and public deployment were deferred rather than assigned predicted results. Nine tables did not justify a retrieval framework or vector database.

## Verification and reviewer path

Start with [README](../README.md), demonstrate `chat`, `ask --show-sql`, `exposure` and the supplied evaluator, then show the optional dashboard. Full-result comparison checks projection, ordering, duplicates and numeric values; limited narrative assertions declare their coverage. Mock policy tests, offline replay and fresh model runs are separate kinds of evidence.

The v0.1.0 Passive/status failure was a genuine wrong-column answer. v0.1.1 grounded classification values in the database and passed its archived 10/10 supplied and 50/50 extended regressions. Original inputs, frozen suites and v0.1.1 reports remain unchanged. Detailed old investigations are available in Git history; current source never loads benchmark answers.

Before the latest consolidation, post-cleanup checks passed 196 tests with two live skips, eight offline browser tests and one uncached Gemini browser request. These are dated verification observations, not automatic guarantees after further changes. Re-run the commands in README for the current tree. Docker checks exercise real startup, non-root execution, internal-artifact exclusion, deterministic analytics and missing-key behavior. Build assertions reject secrets/local artifacts; no container image or public site is claimed as deployed.

For an interview, explain the separate SQL safety and semantic-correctness boundaries, equity versus whole-portfolio denominators, unknown currencies/valuation dates, actual SDK accounting, cache/context isolation, and why a faster wrong planner was removed. Stronger future validation would use externally authored blind cases and isolated resource limits, rather than more framework dependencies.
