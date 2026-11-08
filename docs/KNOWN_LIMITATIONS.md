# Known limitations

The [assignment checklist](SUBMISSION.md) and [enhancement guide](ENHANCEMENTS.md) map the
mandatory and optional requirements to implementations.

- Historical 50/50 extended results belong to their recorded source and evaluator version.
  The suite has been observed and is regression evidence, not blind validation.
- The latest supplied run passed 10/10 with v3 checks on `0b3e94a` after both retrieval removals;
  it is a known finite suite. Earlier captures retain their own source and verification scope.
- Evaluator v4 verifies explicit scalar, list, table and exposure representations. Missing
  required fields and clear contradictions fail. Unsupported paraphrases can fail, and the
  checker does not prove arbitrary English entailment, advice or additional unstructured claims.
- Numeric tables use tool column order. Reordered prose columns or alternative tied ordering
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
