# Known limitations

[Prompt-removal experiment](../reports/submission/README.md), runtime `1c2cc59`,
records 5/10 supplied and an interrupted extended run (28 cases completed). The sealed
holdout was not executed. These are observed outcomes, not a full-suite claim for the
later structural refactor. [Recorded CLI session](../reports/submission/CLI_TRANSCRIPT.md).

The [assignment checklist](SUBMISSION.md) and [enhancement guide](ENHANCEMENTS.md) map the
mandatory and optional requirements to implementations.

- Historical 50/50 extended results belong to their recorded source and evaluator version.
  The suite has been observed and is regression evidence, not blind validation.
- The fresh supplied v4 retest passed 10/10 on `2a68b74`; the earlier verifier replay accepts
  all fifty archived answers and rejects 46 bad-prose mutations. Known finite suites and
  different generation/replay scopes are not blind validation.
- The [historical direct-result implementation](../reports/latency/README.md) passes fresh extended 50/50
  and supplied 10/10. The extended capture uses 57 SDK attempts and 137,274 reported tokens.
  Normal bounded SDK retries remain active; one supplied attempt had unreported usage.
- Direct rendering requires Gemini's complete-plan claim plus successful bounded evidence;
  it is not a proof of arbitrary natural-language intent coverage. Empty, truncated, large,
  ambiguous or interpretive requests retain normal orchestration. SQL data over 30 rows and
  answers over 10,000 characters do not use this optimization. Known-suite success is not
  blind/unseen accuracy. The two interactive pairs showed one faster and one slightly slower
  example; browser timings are local observations, not production percentiles or an SLA.
- Evaluator v4 verifies explicit scalar, list, table and exposure representations. Missing
  required fields and clear contradictions fail. Unsupported paraphrases can fail, and the
  checker does not prove arbitrary English entailment, advice or additional unstructured claims.
- Numeric tables use tool column order; explicit labelled pairs and aggregate prose are supported.
  Reordered arbitrary prose columns or alternative tied ordering
  can be penalized. A correct tool result alone does not certify the final narrative.
- Default SQLite progress callbacks measure VM work. Optional `--profile-io` counts pager
  hits + misses using APSW on fresh private caches; physical device I/O is not measured.
  Scores are correctness-gated relative to the reference, not a general query optimizer.
- Metadata RAG is deliberately excluded from the active submission. BM25 added 12.02%
  reported tokens at equal observed accuracy; graph retrieval scored 9/10 versus 10/10.
  Neither demonstrated a reliable speed gain. The agent retains the full schema, live
  categorical values, catalogue and financial conventions. The [engineering decision and archives](ENGINEERING_NOTES.md#metadata-retrieval-evaluated-and-excluded)
  preserve both experiments. No external-document or large-schema retrieval benefit is claimed.
- One process supports bounded parallel analyses with separate model clients and per-session
  locks. Multiple processes would have separate sessions/RPM/capacity state. A retained SQLite
  ledger coordinates daily usage only; distributed deployment needs external coordination.
  Production rejects multi-worker environment settings; scale within the bounded client pool.
- HTTP/stub soak and Docker verification passed. The new-key real three-user hybrid retest
  completed all nine answers correctly, including session-bound follow-ups, without quota
  errors. The earlier quota-interrupted captures remain intact. This bounded protocol does
  not establish hours of provider load, unrestricted throughput or distributed availability.
- Random session IDs are bearer capabilities, not user identities. The production profile
  uses the existing shared bearer token, not individual accounts, roles or per-user budgets.
- The public Render demo remains anonymous. Production must be explicitly configured and
  deployed with TLS, secrets, retained storage and monitoring. No availability SLA or security
  certification is claimed. The local Streamlit interface is not the production serving path.
- SDK calls can fail from network/provider quota and may exceed interactive latency expectations.
  Local counters are not Google's quota meter. A multi-step answer can exhaust a rate window
  between calls; it returns a retryable failure instead of inventing results.
- The local/cache registry covers four explicit capabilities. CLI/UI/Streamlit opt in; raw API
  request fields still default to true when omitted. Evaluation bypasses both.
- Source data has no reliable cross-portfolio currency/valuation basis. No inferred FX, live
  prices, recommendations or total-AUM comparability is claimed. Bond-only exposure is undefined.
- SQLite is file-backed rather than implementing the brief's in-memory setup hint. The brief
  also provides a file-backed example. Runtime database changes require an explicit rebuild.
- The repository and supplied data remain public by the owner's choice. Removing website
  pages does not remove copies in Git history. Secrets remain private runtime configuration.
