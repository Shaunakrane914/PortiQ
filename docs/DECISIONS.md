# Engineering decisions

**One agent and two analytical tools.** The assignment needs explicit Gemini tool selection,
not distributed agents. Manual function dispatch gives typed inputs, bounded execution and
inspectable evidence. Alternatives were a keyword router (poor generalization) and automatic
function execution (less application control). Mock tests verify loop behavior; live reports
measure actual model behavior separately.

**Combine SQL planning and routing.** The first working vertical slice used three SDK calls
for a simple SQL question: route, generate, summarize. It actually exhausted a free-tier quota.
Generating SQL in the routing function call removes the redundant generation call on simple
valid queries. A later real sector-aggregate failure showed that complex drafts needed a
focused planner: drafts with five joins or two CTEs receive that additional call. This is
an explicit correctness/cost trade-off, not a question-specific route. Planning and repair
share one JSON generator and execution boundary. No latency speedup percentage is claimed.

**SQLite and atomic file initialization.** The assignment suggests an in-memory database as
a starting point; a reproducible on-disk SQLite database allows independent CLI processes,
OS read-only mode and inspection. Temporary-file construction makes failed rebuilds safe.
No extra indexes were added to the supplied schema.

**Deterministic Decimal exposure.** The LLM resolves intent but never performs allocation
arithmetic. Direct CSV reference calculations independently reconcile every portfolio. An
alternative market-value exposure basis was rejected because the assignment explicitly uses
current_weight and excludes bonds.

**Strict structured evaluation.** Reference SQL results, not SQL strings or narrative keywords,
are compared. Projection width, every value, duplicates, numeric tolerance, ordering and
truncation matter. Exposure references read CSVs independently. The evaluator permits aliases
but requires the reference projection's positional meaning and values. Empty results have
limited discriminatory power; stronger metamorphic datasets are a future improvement.

**No cache or frontend for this release.** Fresh results keep model reliability measurable.
Optional visualization and APIs would increase install scope while the core assessment is
CLI-first. Core tools return structured data that a later UI can reuse without duplication.

**Model support is checked, not assumed.** Model listing alone did not establish generation
availability: a listed historical model returned 404, a latest alias timed out, and the first
working preview hit daily quota. The selected stable Flash-Lite model is configurable and
the report records both configured and provider-reported versions.
