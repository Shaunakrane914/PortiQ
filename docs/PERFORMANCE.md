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
