# Measured performance

`uv run python scripts/benchmark.py` measures 200 repetitions each of Balanced Portfolio
exposure and a portfolio COUNT query, with correctness assertions and no answer cache.
The committed `reports/performance.json` contains all samples, mean, median, p95, timestamp
and tracemalloc peak. OS filesystem cache is uncontrolled. These are local microbenchmarks,
not concurrency/load tests or portable service guarantees.

The supplied indexes were retained. The actual exposure query plan uses
`idx_holdings_portfolio` to locate holdings and INTEGER PRIMARY KEY lookups for securities
and sectors. No additional index was justified for this 603-row dataset, and no index
speedup is claimed.

The first live SQL vertical slice required three SDK requests for a simple count: routing,
SQL generation and summarization. The final design generates the SQL in the routing
function call, reducing simple successful flows to two SDK requests. Structurally complex
queries use an additional focused planning call: an observed sector-aggregate scope error
showed that reducing all planning to the routing request sacrificed correctness. The initial
trace and final reports record actual request counts. There is no controlled before/after
latency experiment across identical service/quota conditions, so no speedup percentage is claimed.

The default model request interval is 13 seconds; the release evaluation uses 6.5 seconds
for Flash-Lite. The limiter is per backend/process and is not a distributed quota service.
Live end-to-end durations include this wait. A quota failure is surfaced immediately rather
than being disguised as a successful cached answer. The model schema context is serialized
once per agent instance, and each question starts a fresh conversation to bound context growth.

Further optimization should be driven by deployment measurements: separate network/service
latency from intentional pacing, add model-specific request budgets, then assess query-plan
bottlenecks on a much larger dataset. Persistent caching would need a database/content hash,
model/prompt version and explicit invalidation; it is intentionally absent here.
