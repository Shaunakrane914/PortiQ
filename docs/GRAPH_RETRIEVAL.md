# Experimental schema-graph retrieval

The assignment asks for RAG or GraphRAG to find question-relevant metadata. The graph
experiment implements that requirement over the existing SQLite schema. It is available
through `PortfolioAgent(..., context_mode="graph")`; the application default remains basic
BM25 retrieval until a measured comparison supports changing it.

`schema_graph.py` builds table and column nodes from SQLite, foreign-key edges from actual
constraints, and metric-rule nodes linking financial concepts to their required tables.
Question terms, column names and bounded portfolio/sector/symbol values seed relevant
tables. Breadth-first traversal adds intermediate tables along actual foreign-key paths.
For example, a question about portfolio currencies selects portfolios and securities;
traversal adds holdings even though the question never names it.

The selected DDL replaces the full initial schema. Portfolio domains and the catalogue
are included when portfolios are selected. Financial conventions, tool declarations and
safety instructions remain unchanged. Dedicated SQL planning and repair still receive
the full schema in both conditions. Unknown seeds, disconnected seeds, or selections that
offer no context saving fall back to the original full prompt. Source IDs, selected tables,
fallback reasons and initial context character counts are recorded in responses.

This is **schema-graph RAG**, not Microsoft's full document GraphRAG pipeline. There are
no document entity extraction calls, community summaries, embeddings, graph database or
additional model requests. Microsoft's [local search documentation](https://microsoft.github.io/graphrag/query/local_search/)
describes its richer document/entity/relationship approach. The implementation here targets
the narrower metadata task in the assignment. Google's [text-to-SQL guidance](https://cloud.google.com/blog/products/databases/techniques-for-improving-text-to-sql)
also discusses selecting relevant datasets, tables and columns for model context.

## Reproduce the checks

Run from the repository root with dependencies installed:

```powershell
# Offline: no API key, SDK calls, token measurement or generated answers.
uv run python scripts/schema_graph_audit.py --output reports/local/schema-graph-audit.json

# Live paired test: requires GEMINI_API_KEY in the local environment/.env.
# Commit source first; output directories must be fresh.
uv run python scripts/rag_ablation.py --treatment graph --trials 1 --output reports/local/schema-graph-live
```

The offline audit compares full, basic and graph initial system prompts on the supplied 10
and author-created 50 questions. Reference SQL is used only after runtime retrieval to audit
table coverage; it is never passed to retrieval or generation. Handling-only cases have no
reference-table check. Coverage does not prove correct SQL, column selection, routing or
final prose. Character reductions must not be described as measured token savings.

The live runner alternates which condition runs first for each question and shares one
client, limiter and ledger. Both conditions use genuine Gemini generation, no local answers,
no answer cache, the same data/evaluator/tools and the same model settings. It records all
SDK attempts, reported usage, errors, service time and deliberate pacing separately. Provider
prompt caching is observed when reported, not controlled. One known ten-question pass is
small-sample evidence, not proof of unseen accuracy or a statistically reliable speedup.

## Limits

The [fresh paired comparison](../reports/graph-rag-2026-11-08/README.md) scored **10/10 for
full schema and 9/10 for graph context**, with 21 SDK attempts each. Graph mode used 26.80%
fewer reported tokens, but one recovered 504 had unknown usage and latency did not show a
reliable improvement. Its failed sector-value query excluded bonds from the denominator
despite complete table coverage. This is a useful context-compression experiment, not a
demonstrated accuracy improvement or grounds to switch the default.

Semantic aliases and metric rules are deliberately small and inspectable. They can miss
paraphrases, and connected seed selection cannot guarantee that every needed table was
recognized. Full-schema SQL repair limits the damage but may add model calls. An absent
declared foreign key does not authorize an invented relationship: portfolio benchmark
questions currently fall back because the supplied benchmark table is disconnected.
The graph is rebuilt when the agent is constructed; arbitrary schema changes after that
require constructing a new agent. No large-schema or external-document benchmark is claimed.

Tests in `tests/test_schema_graph.py` verify actual column/FK nodes, bridge discovery,
unknown/disconnected fallback, schema changes, unchanged generation configuration and
supplied-reference table coverage. Live results must be read separately from these tests.
