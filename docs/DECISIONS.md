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

**Historical v0.1.x decision: no cache or frontend.** Fresh results keep model reliability measurable.
Optional visualization and APIs would increase install scope while the core assessment is
CLI-first. Core tools return structured data that a later UI can reuse without duplication.

**Bounded classification grounding.** Distinct `portfolios.status` and `strategy_type`
values are read from the current database and supplied to both routing and SQL planning.
This resolves overlapping business terminology without a question lookup or fixed mapping.
The first broader implementation also exposed industry aliases and regressed sector queries;
the retained reports motivated limiting this patch to the two portfolio classifications.
Domains are bounded, labeled as untrusted data, and refreshed with each agent instance.

**Independent evaluation dimensions.** Extra tool calls and incorrect evidence are separate
failures, both visible even when one already makes strict pass impossible. Distinct evidence
matching allows a correct answer after discovery while preserving its routing penalty.
Small deterministic prose checks live exclusively in evaluation and declare their coverage.
Provider errors receive no narrative judgment: an HTTP status code is not a financial claim.

**Preserve exposure references at the model boundary.** A retry revealed that the model
could bypass the existing ambiguity resolver by inventing a full name from a vague fragment.
The tool schema and prompt now explicitly require the original reference. Name resolution
and financial arithmetic are unchanged; no question-specific router was added. As with
other semantic model instructions, repeated live checks provide evidence rather than a
universal guarantee that a model will never infer an unsupported identity.

**Model support is checked, not assumed.** Model listing alone did not establish generation
availability: a listed historical model returned 404, a latest alias timed out, and the first
working preview hit daily quota. The selected stable Flash-Lite model is configurable and
the report records both configured and provider-reported versions.


## v0.2 platform decisions

**Keep the original default.** A typed single-call graph reduces calls on many questions, but a measured Technology-sector valuation result regressed. Valid SQL is not proof of semantic equivalence. The experimental strategy remains opt-in and can fall back to the original orchestration for invalid/insufficient plans. Deterministic rendering uses authoritative tool results; original model synthesis remains available in the original strategy.

**Small shared modules.** A single analytics service and explicit four-capability registry are sufficient for thirteen portfolios. FastAPI and the static dashboard consume the same calculations as CLI extensions. No vector database, retrieval framework, LangGraph, frontend framework or duplicate financial engine is justified by this dataset.

**Different financial bases stay visible.** Recorded allocation, stock-only sector exposure and quote-value reconstruction answer different questions. Missing AUM currency, dates, bond conventions or weights produce notices rather than inferred values. Unknown histories remain absent.

**Bounded exact caching and context.** An exact cache is easier to audit than semantic similarity. Database bytes plus rebuild identity prevent stale answers even after an identical rebuild. Bounded ephemeral sessions support follow-ups while preserving independent CLI behavior and evaluation bypass. No persistent chat store was needed.

**Conservative outage handling.** Actual failed SDK calls consume the local budget. Structured quota details determine whether a retry is useful; waits are bounded. After repeated transport/transient failures, a cooldown and fresh client provide bounded recovery. This follows observed operational failure, not an unmeasured latency claim. Sequential explicitly configured fallback is supported; parallel hedging is deferred because it spends additional quota.

**Optional local platform.** Plain browser assets and an optional Python web extra keep core installation independent. The non-root image is verified locally and in CI. Public hosting and multi-user identity remain separate work rather than implied by Docker readiness.
