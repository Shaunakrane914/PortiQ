# Engineering decisions and evidence

## Restored working assignment conventions

Source `3359777` restores the runtime prompt strings and SQL tool descriptions from the
successful recorded `987143b` run, while retaining the modular refactor and evaluator fix.
The over-broad prompt-removal experiment reduced strict supplied accuracy. Restoring the
known conventions recovered **10/10 in a fresh original-suite run**, with 13 SDK calls,
33,885 reported tokens and all ten final-answer checks passing.
[Source-qualified results](../reports/restored-working-2026-11-09/README.md).
The 32-question run remains stopped as requested. Prior 32/32 and 50/50 are not recertified
for this version. The defaults are assignment-specific conventions, not proof of blind
generalization. No benchmark or evaluator pass condition was changed.

## Behavior-preserving maintainability refactor

Branch: `refactor/maintainability-2026-11-09`. Runtime source commit: `0a06e56`.
Baseline runtime: `1c2cc59` (also present in branch parent `4843a7d`). This work separates
responsibilities; it does not tune prompts, change financial definitions or weaken evaluation.

| Previous owner | New owner | Reason |
| --- | --- | --- |
| `agent.py`: response contracts and presentation | `answers.py` | The agent chooses/executes tools; pure rendering and response models can be used without importing orchestration or an SDK. |
| `service.py`: TTL/LRU answers and database identity | `cache.py` | Cache lifetime, invalidation and defensive-copy behavior have one owner. |
| `service.py`: sessions, locks and history | `sessions.py` | Conversation storage and bounded history are independent of model clients and caching. |
| `service.py`: sequential provider fallback | Existing `model.py` | SDK, retry, circuit and fallback behavior share the provider boundary. |

No new classes, frameworks, dependencies, commands or user features were introduced.
The three new runtime files own existing implementations; compatibility imports in
`agent.py` and `service.py` refer to the same classes/functions, without wrapper layers.
The default CLI still imports neither FastAPI nor Streamlit.

### Size and verification

- `agent.py`: **718 → 384 lines**; `service.py`: **539 → 380**. The two overloaded files
  shed 493 lines into their cohesive owners. Existing `model.py` grows 209 → 268 lines.
- Total runtime across those files and the three extracted modules changes **1,466 →
  1,507 lines**: +41 import/header lines, not 493 lines of deleted functionality.
- Primary README: **110 → 62 lines**, with deeper documents and evidence retained.
- **26 definition ASTs are identical**: 17 moved definitions and nine unchanged
  orchestration/provider definitions. Prompts, SQL execution, equity exposure, evaluator,
  configuration, quota policy and CLI files are byte-identical to the baseline.
- **170 recorded responses** from multiple captured versions produce **510 byte-identical
  rendered texts** and identical 170 early-completion decisions. System prompts, both tool
  declaration modes and response JSON schemas also match. This is offline replay, not
  a new 170-question live accuracy result.
- **345 Python tests passed; one opt-in live test skipped.** Three focused regressions
  cover dependency isolation, legacy import identity, and cache/agent evidence ownership.
  The added CLI import-isolation assertions passed in a targeted three-test rerun.
- Ruff, format checks and strict mypy passed (22 source files). All **13 key-free browser
  tests passed**; the separate opt-in genuine-Gemini dashboard test passed at `0a06e56`,
  returning the three correct Passive portfolio names in one SDK call, with cache off.
  It reported 2,438 tokens. Streamlit navigation, mode controls and mobile checks passed.
- All **13 original assignment inputs** remain byte-identical. No benchmark questions,
  reference answers or strict pass criteria were changed by this refactor.

No changed SQL values, exposure values, rendering text, completion decisions, retry policy
or public import/API contracts were observed. Runtime fingerprint keys change with source
layout as intended; this prevents old-version cache reuse. Probabilistic model behavior
outside the recorded corpus is not certified by static/replay checks.

### Evidence and remaining complexity

The earlier prompt-removal experiment completed **5/10 supplied**, then stopped after
28 of 50 extended cases (all 28 completed cases passed). It is preserved with its actual
scope in the [experiment record](../reports/submission-2026-11-09/README.md). The holdout
was sealed but not executed. These observed outcomes preceded this structural refactor;
historical 50/50 and 32/32 captures belong to other runtime hashes. Lack of a new full
live suite is not an observed functional regression from moving unchanged code.

`AnalysisService.ask` still coordinates substantial context and client-pool behavior;
the renderer still contains domain-sensitive label formatting. Splitting or simplifying
those algorithms further would risk subtle behavior changes, so they remain unchanged.
Both optional UIs, production controls and the performance profiler are retained because
removing working optional features would violate scope. The earlier evaluator diagnostic
fix remains; no new scoring changes were made here.

My maintainability assessment improves from the independent review's **5/10 to 8/10**:
ownership is clearer and the entry point shorter, while request/context and presentation
complexity remain. This is an engineering judgment, not a PL Capital score or new accuracy claim.

[Prompt-removal experiment](../reports/submission-2026-11-09/README.md), runtime `1c2cc59`,
records 5/10 supplied and an interrupted extended run (28 cases completed). The sealed
holdout was not executed. These are observed outcomes, not a full-suite claim for the
later structural refactor. [Recorded CLI session](../reports/submission-2026-11-09/CLI_TRANSCRIPT.md).

The original [assignment](assignment/README.md) prioritizes a working CLI, accurate financial
tools, a ground-truth evaluator and brief run instructions. The optional enhancements are
implemented without making web, Streamlit or Node dependencies mandatory for the core CLI.

[Historical verified result](../reports/latency-2026-11-09/README.md): **50/50 extended and 10/10 supplied** in
fresh full native v4 runs on `1eba590`. The extended capture used 57 SDK attempts and
137,274 reported tokens. Explicitly complete factual plans can render validated tool data
directly; complex/ambiguous/error/truncated cases retain normal orchestration. Zero-spacing
browser observations were 1.454s and 2.834s. Full metrics and limitations are in the report.

- `main.py` is a shortcut to the canonical parser. Global options are preserved, missing
  databases initialize only for ask/chat, and local/cache/context modes require explicit flags.
- Gemini selects typed SQL/exposure tools. SQLite executes read-only bounded SQL; Decimal
  arithmetic calculates normalized stock-only exposure. Runtime code never imports benchmarks.
- Full schema, live categorical domains and the portfolio catalogue remain in model context.
  Financial conventions and declared schema relationships are retained directly; no retrieval
  layer selects, removes or appends metadata at runtime.
- Gemini still plans factual data requests. When it explicitly completes every call in a
  batch, the app can render validated evidence without another synthesis request. SQL results
  must be nonempty, untruncated, at most 30 rows and losslessly representable; output must fit
  10,000 characters. Other requests retain the existing loop. Raw numeric precision is kept.
  `PORTIQ_DIRECT_RESULTS=0` restores previous behavior; no alternate planner or RAG is added.
- A bounded reusable client pool permits parallel requests, shares quota guards and preserves
  per-client retry/circuit state. Conversation turns serialize within each session; results,
  caches, history and per-question metrics remain isolated.
- Evaluator v4 checks actual final-answer content using explicit result-format contracts,
  independently checks SQL/CSV exposure evidence and keeps correctness separate from a
  reference-relative VM/page-access performance scores. Hybrid percentage claims are checked
  independently from SQL scalars. It does not use an LLM judge.
- The existing anonymous hosted demo remains available. A separate production configuration
  validates hosts/origins/token/storage and provides a hardened container deployment recipe.
  Distributed state, individual user identity and operational TLS/monitoring remain separate work.

See [enhancement implementation and tests](ENHANCEMENTS.md), [evaluation](EVALUATION.md) and
[limitations](KNOWN_LIMITATIONS.md) for exact verification boundaries.

## Metadata retrieval evaluated and excluded

Both retrieval strategies were evaluated against full-schema prompting in separate paired
runs of the ten supplied questions. BM25 tied at 10/10 but used **12.02% more reported tokens**.
Schema-graph retrieval used **26.8% fewer reported tokens** but scored **9/10 versus 10/10**,
including a financial denominator error. Neither demonstrated a reliable latency benefit
or fewer SDK attempts. These are small, known-suite experiments, not general accuracy claims;
one graph provider failure had unknown token usage.

Both approaches were removed from the active architecture to prioritize correctness and
reduce maintenance cost for this nine-table database. The agent sends the complete schema,
database-derived categorical values, portfolio catalogue and financial conventions directly
to Gemini. Foreign-key definitions, read-only SQL validation/repair and deterministic
financial calculations remain. RAG is optional in the assignment; it is deliberately excluded
from the submission, and no replacement retrieval system was added.

Source, reproduction commands and original evidence are preserved on
[archive/bm25-rag-2026-11-09](https://github.com/Shaunakrane914/PortiQ/tree/archive/bm25-rag-2026-11-09)
at `d65927b` and [archive/schema-graph-rag-2026-11-08](https://github.com/Shaunakrane914/PortiQ/tree/archive/schema-graph-rag-2026-11-08)
at `8a6143c`. The [BM25 comparison](https://github.com/Shaunakrane914/PortiQ/blob/d65927b2e59e07c76ff3795e1395c0724a439241/reports/rag-ablation-2026-11-08/README.md)
and [graph comparison](https://github.com/Shaunakrane914/PortiQ/blob/8a6143c96d1780f1890ff8d7db1c92cc5dbdd4a8/reports/graph-rag-2026-11-08/README.md)
retain failed/interrupted attempts and their limitations.

After both removals, **232 core tests passed** and a fresh supplied CLI evaluation on
`0b3e94a` passed **10/10**, including all ten explicit final-answer checks: 21 SDK attempts,
48,293 reported tokens and zero provider errors. The [capture](https://github.com/Shaunakrane914/PortiQ/blob/f6d93578e3a2b5017dd926c3aba1e36b6d4e2816/reports/supplied-no-rag-2026-11-09/README.md)
also records an offline check that all initial prompts/configurations match the original
no-RAG control. This known-suite verification does not establish unseen accuracy.

## Historical evidence

### Schema-graph retrieval archived

The graph implementation and its complete evidence remain at verified commit `8a6143c`.
The [retrieval decision above](#metadata-retrieval-evaluated-and-excluded) also covers the
subsequent removal of BM25. The earlier graph-removal verification below still used BM25.

Removal verification: 235 core tests passed, followed by a fresh **10/10 supplied CLI run**
on `f14ea21`, including all ten explicit final-answer checks. The [capture](https://github.com/Shaunakrane914/PortiQ/blob/f6d93578e3a2b5017dd926c3aba1e36b6d4e2816/reports/supplied-after-graph-removal-2026-11-08/README.md)
records 21 SDK attempts, 54,093 reported tokens and zero provider errors.

The fresh [supplied-ten capture](https://github.com/Shaunakrane914/PortiQ/blob/f6d93578e3a2b5017dd926c3aba1e36b6d4e2816/reports/supplied-v3-2026-11-08/README.md) on `b8db4a9`
passed 10/10 with all ten explicit v3 answer checks, 21 SDK calls and 54,075 reported tokens.
Its first complete 8/10 run is separately retained: percentage units in exposure-table headers
needed verifier format support. Added tests reject wrong/missing/extra percentages; no failed
fragments were stitched into the subsequent full run. A later GUI-only configuration-forwarding
fix does not change the evaluated analytical code.

The retained [8 November CLI capture](https://github.com/Shaunakrane914/PortiQ/blob/f6d93578e3a2b5017dd926c3aba1e36b6d4e2816/reports/cli-2026-11-08/README.md) on `4b49d95`
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
