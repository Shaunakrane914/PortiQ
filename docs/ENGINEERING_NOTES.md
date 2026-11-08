# Engineering decisions and evidence

The original [assignment](assignment/README.md) prioritizes a working CLI, accurate financial
tools, a ground-truth evaluator and brief run instructions. The optional enhancements are
implemented without making web, Streamlit or Node dependencies mandatory for the core CLI.

- `main.py` is a shortcut to the canonical parser. Global options are preserved, missing
  databases initialize only for ask/chat, and local/cache/context modes require explicit flags.
- Gemini selects typed SQL/exposure tools. SQLite executes read-only bounded SQL; Decimal
  arithmetic calculates normalized stock-only exposure. Runtime code never imports benchmarks.
- Full schema, live categorical domains and the portfolio catalogue remain in model context.
  Local metadata retrieval adds relevant column/foreign-key descriptions with provenance.
- A guarded scalar-only request can avoid the model summary call. Other shapes retain the
  original tool loop. No unsuccessful alternate planner is restored.
- A bounded reusable client pool permits parallel requests, shares quota guards and preserves
  per-client retry/circuit state. Conversation turns serialize within each session; results,
  caches, history and per-question metrics remain isolated.
- Evaluator v3 checks actual final-answer content using explicit result-format contracts,
  independently checks SQL/CSV exposure evidence and keeps correctness separate from a
  reference-relative VM-work performance score. It does not use an LLM judge.
- The existing anonymous hosted demo remains available. A separate production configuration
  validates hosts/origins/token/storage and provides a hardened container deployment recipe.
  Distributed state, individual user identity and operational TLS/monitoring remain separate work.

See [enhancement implementation and tests](ENHANCEMENTS.md), [evaluation](EVALUATION.md) and
[limitations](KNOWN_LIMITATIONS.md) for exact verification boundaries.

## Historical evidence

The fresh [supplied-ten capture](../reports/supplied-v3-2026-11-08/README.md) on `b8db4a9`
passed 10/10 with all ten explicit v3 answer checks, 21 SDK calls and 54,075 reported tokens.
Its first complete 8/10 run is separately retained: percentage units in exposure-table headers
needed verifier format support. Added tests reject wrong/missing/extra percentages; no failed
fragments were stitched into the subsequent full run. A later GUI-only configuration-forwarding
fix does not change the evaluated analytical code.

The retained [8 November CLI capture](../reports/cli-2026-11-08/README.md) on `4b49d95`
passed 50/50 under evaluator v2 with 92 SDK calls and 201,404 reported tokens. Its six
configured narrative cases passed; that capture is not retroactively verified under v3.
Original data and the eight captured artifact bytes remain unchanged.

An earlier original-agent extended run used 266,304 tokens. The 24.37% difference is a
historical observation, not a controlled causal latency result. Service time, pacing,
backoff and total duration must be reported separately.

The removed experimental planner reduced calls in some captures but failed supplied and
ambiguity questions. Its fragments were not stitched into passing scores. Historical
reports removed by cleanup remain available in
[commit history](https://github.com/Shaunakrane914/PortiQ/tree/95436a7/reports).
The deleted benchmark/release helpers are not current run instructions.

CI uses Python 3.11/3.13 on Ubuntu/Windows and a separate browser/container/Streamlit job.
Key-free test scores, replay and fresh Gemini accuracy runs are always separate evidence.
