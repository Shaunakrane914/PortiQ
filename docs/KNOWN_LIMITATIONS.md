# Known limitations

The [assignment checklist](SUBMISSION.md) and [enhancement guide](ENHANCEMENTS.md) map the
mandatory and optional requirements to implementations.

- Historical 50/50 extended results belong to their recorded source and evaluator version.
  The suite has been observed and is regression evidence, not blind validation.
- The fresh supplied run passed 10/10 with v3 checks on `b8db4a9`; it is also a known finite
  suite. The later GUI startup configuration fix is covered separately by key-free checks.
- Evaluator v3 verifies explicit scalar, list, table and exposure representations. Missing
  required fields and clear contradictions fail. Unsupported paraphrases can fail, and the
  checker does not prove arbitrary English entailment, advice or additional unstructured claims.
- Numeric tables use tool column order. Reordered prose columns or alternative tied ordering
  can be penalized. A correct tool result alone does not certify the final narrative.
- SQLite progress callbacks measure VM work approximately, not logical page reads or physical
  I/O. Performance scores are relative to the reference on the same small database and are
  correctness gated. They are not a general query optimizer or large-data benchmark.
- Metadata RAG retrieves schema descriptions locally with BM25 and retains full DDL. It uses
  no embeddings, external documents or GraphRAG. Retrieval usefulness on unseen large schemas
  has not been established by the supplied ten-question suite.
- One process supports bounded parallel analyses with separate model clients and per-session
  locks. Multiple processes would have separate sessions/RPM/capacity state. A retained SQLite
  ledger coordinates daily usage only; distributed deployment needs external coordination.
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
