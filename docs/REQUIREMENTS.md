# Requirement traceability

The preserved [assignment README](assignment/README.md) is authoritative. The original
CSV files, schema, ground truth, and suggested requirements remain assessment inputs.
The root README documents the implementation; `pyproject.toml` and `uv.lock` define its dependencies.

| Requirement and source | Component | Verification | State |
|---|---|---|---|
| SQLite from supplied schema/CSVs (Getting Started) | `database.py` | row counts, FK checks, malformed records, atomic rebuild tests | implemented, locally verified |
| Natural language SQL (What You'll Build 1) | Gemini SQL function arguments, `run_sql_tool` | live supplied benchmark; mock repair/error tests | implemented; see live reports |
| Equity sector exposure (What You'll Build 2) | `exposure.py` | independent CSV reference for all 13 portfolios | verified; bond-only portfolios explicitly undefined |
| CLI agent choosing tools (What You'll Build 3) | `agent.py`, `cli.py` | genuine live Gemini calls and deterministic injected backend tests | implemented; see reports |
| Ground-truth evaluator (What You'll Build 4) | `evaluation.py` | independent SQL execution, multiset/numeric/projection tests | implemented; all ten cases attempted |
| Documentation and error handling (Deliverables) | README, docs, domain errors | clean-install and CLI checks | see acceptance record |
| SQL safety (Optional Enhancements; user brief mandatory) | SQLGlot, SQLite authorizer, read-only URI, limits | mutation, function, recursion, timeout, injection tests | locally verified |
| Hybrid tools (Optional Enhancements) | bounded function-call loop | mock multi-tool and extended hybrid cases | implemented; see live reports |
| CI and typed code (user brief) | Ruff, strict mypy, pytest, Actions matrix | local quality gates; remote status must be checked separately | configured |
| Extended independent benchmark (user brief) | frozen `evaluation/extended.json` | 50 author-created cases with original SQL/CSV oracles | available; see evaluation results |
| Dashboard / API (optional in both sources) | deferred | core CLI is self-contained | intentionally deferred |

No benchmark IDs or expected queries are loaded by `agent.py`, `prompts.py`, or the tools.
Evaluation is imported lazily only by the CLI's `evaluate` command.
