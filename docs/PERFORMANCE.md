# Performance and cost measurements

Performance evidence is observational. SDK wall time includes network and provider work, not isolated model inference. Deliberate pacing and retry backoff are reported separately. Historical v0.1.1 and current runs occurred at different times; no controlled speedup is claimed across releases.

The paired experiment alternates existing/experimental strategy order for the same frozen questions on one shared backend. It disables cache and local routing. Reports include per-case actual SDK invocations, configured/provider models, reported tokens, service/pacing/backoff, SQL validation/execution, exposure work and end-to-end Python analysis time. The independent oracle is excluded from analysis latency. See the current report index for completed measurements.

The initial attempt encountered sustained provider/connection failure and reached 250 SDK invocations. Its latency distribution is dominated by retries/timeouts and is not a valid planner speed comparison. That attempt is preserved in full. Reduced request count does not compensate for the experimental planner's observed wrong answer; it remains opt-in.

## Measured local execution and exact cache

Twenty paired repeats of four capabilities (count, exposure, holdings, metadata), with independent CSV references and a warm filesystem:

| Mode | Correct checks | SDK calls | Median | p95 |
|---|---:|---:|---:|---:|
| Local calculation | 80/80 | 0 | 3.90 ms | 5.15 ms |
| Exact cache hit | 80/80 | 0 | 2.06 ms | 2.84 ms |

These are Python service wall times on the development machine, including data/code identity checks. They are not network response targets or a guarantee on other hosts. The cache is cleared before each pair. Full samples and timing stages are in `reports/v0.2.0/local-cache.json`. Cache hits still calculate identity; that intentional cost guards against stale data.

## Deliberate constraints

Default SDK start spacing is 13 seconds; paired evaluations use 6.5 seconds for the configured account. Long observed answers can exceed the interval, so actual pacing may be zero. Daily counters reserve every actual invocation, including failed retries and explicit fallback attempts. SDK automatic retries are disabled; unknown provider usage is counted as unknown. A bounded circuit prevents a prolonged failing connection from consuming the entire configured budget.

The original path retains model synthesis. The one-call path uses deterministic rendering and generally avoids a synthesis request, but must demonstrate accuracy before promotion. Full-schema versus focused-metadata and alternative-model comparisons are deferred; no estimated token savings are reported. Sequential fallback is configured/tested offline, while hedging is deferred to conserve quota.


## Complete paired live results

All numbers below are per question, seconds; service is the sum of SDK wall times. One shared 6.5-second-paced backend, alternating order, one trial, cache/local disabled. No provider failures, retry backoff or fallback in this completed run.

| Suite / strategy | Strict pass | SDK calls | Reported tokens | Mean service | Mean pacing | Median end-to-end | p95 end-to-end |
|---|---:|---:|---:|---:|---:|---:|---:|
| Supplied / original | 10/10 | 21 | 58,116 | 6.970 | 7.516 | 12.943 | 23.114 |
| Supplied / experimental | 9/10 | 10 | 25,239 | 2.019 | 4.725 | 6.546 | 10.799 |
| Extended / original | 50/50 | 97 | 266,304 | 8.264 | 7.113 | 13.139 | 27.363 |
| Extended / experimental | 50/50 | 50 | 124,739 | 3.051 | 3.874 | 6.359 | 13.224 |
| Platform / original | 8/8 | 15 | 40,719 | 2.493 | 9.637 | 12.918 | 13.088 |
| Platform / experimental | 7/8 | 8 | 19,956 | 1.377 | 5.186 | 6.507 | 6.934 |

Total: 201 SDK invocations, 535,073 reported tokens; usage available for every invocation. Reported candidate output is kept separate from input/thinking usage. Lower experimental cost/latency did not satisfy the correctness/ambiguity promotion rule. Original q7 used one focused SQL-planning call; no subsequent repairs were required. See the reporting-field caveats in EXPERIMENTS and `paired-analysis.json`.

Historical v0.1.1 used 21 calls / 57,977 tokens on supplied and 97 / 265,499 on extended. Current default call counts are unchanged; token totals vary slightly. Historical pacing-inclusive mean/p95 were 16.907/23.817 seconds supplied and 13.565/23.706 extended; current means are 14.493 and 15.380 seconds respectively. The extended mean/p95 are worse in the new observation. Different service conditions and timing boundaries prevent a controlled causal speedup/regression claim. Historical reports do not separately expose current-style raw SDK/pacing measurements.
