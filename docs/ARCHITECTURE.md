# Architecture

The required path remains `CLI -> PortfolioAgent -> Gemini function calls -> SQL/exposure tools -> independent evaluator`. The SQL authorization policy and exposure formula are retained; additive timings do not alter their decisions. Nine supplied tables remain small enough for explicit schema context.

`analytics.py` adds fixed read-only portfolio queries, snapshots, warnings and reconciliation. It reuses `calculate_exposure`; neither FastAPI nor JavaScript reimplements financial calculations. Recorded weights are compared with normalized `quantity * current_price` values only when every value is valid and one known currency is present. No FX, cash plug, accrued interest or AUM scaling is inferred.

`renderer.py` renders validated results deterministically. `planning.py` adds a single typed `execute_plan` declaration: validate the entire graph, authorize SQL, execute ordered steps, resolve scalar dependencies and render. An invalid or insufficient plan can fall back to the original agent. A valid but semantically wrong query cannot be detected generally; this is why the experimental planner remains optional.

`service.py` is shared by optional CLI modes and the API. It owns the explicit local registry, version-aware exact cache, bounded ephemeral sessions and optional sequential model fallback. Original CLI asks and evaluations still use the original agent directly by default. No runtime module reads benchmark answers.

`model.py` records each actual SDK invocation; SDK automatic retries are disabled. `quota.py` handles atomic UTC-day reservations and safe error classification. The metered wrapper applies bounded retries; pacing, provider service, backoff and end-to-end time are separate. A transient-failure circuit prevents a failing transport from consuming the entire local budget and refreshes the SDK client after cooldown.

`api.py` is a thin adapter with input/response bounds, optional token authentication, origin/host rules, request IDs, safe errors and one concurrent analysis. A single worker is supported. `web/` is static same-origin HTML/CSS/JS with safe DOM construction and six views; no frontend package is needed at runtime.

The exact cache stores at most 64 successful responses for 300 seconds. Identity includes exact trimmed question, database bytes and rebuild identity, code/prompt/calculation version, model/fallback configuration, strategy and session context. Deep copies prevent caller mutation. Local and cache answers advertise zero SDK calls; model evaluations bypass both.

Sessions hold at most eight recent turns, compact successful-tool summaries, ordered portfolio references and up to ten security symbols. At most 100 sessions survive for 30 minutes. Selected portfolio IDs come from validated data; unclear ordinal references request clarification. Conversation data stays in server memory. The session ID is an opaque capability, not an authenticated user identity.

Docker installs the locked web extra and runs as UID/GID 10001. The image excludes `.env`, local databases and developer artifacts. The supplied data initializes into a writable runtime directory. Browser/container CI is separate from the unchanged four-job Python workflow.
