# Development record

This history records actual implementation steps. Nothing was backdated or rewritten.

- `a0b350e`: preserved the supplied assessment and nine source datasets.
- `47a3cf4`: implemented atomic ingestion, Decimal exposure and read-only SQL defenses;
  fixed the SQLite COUNT(*) authorizer case after two real test failures.
- `f063c72`: added genuine Gemini orchestration, bounded SQL repair, CLI and independent
  evaluation; verified a real count question end to end.
- `e498c17`: combined routing and SQL planning to remove a redundant model call, added
  configurable quota pacing, and froze the 50-case author-created suite.
- `3ad6fdb`: clarified projection/ordering/diversification conventions after actual supplied
  benchmark failures; added source hashes, ingestion validation, security tests and CI.
- `1b4cd0e`: published CLI documentation and retained unsuccessful benchmark artifacts.

Publication required the connected GitHub app to create the workflow because the local
OAuth token lacked workflow scope. The app created `ed1644c`; the local branch merged
that actual commit (`331531a`) and preserved its exact workflow bytes (`bc32c59`). No
remote history was replaced. The workflow-only intermediate commit's CI failed; the
combined implementation has its own separate Actions run and must be judged by that run.

Failures retained for review include minute/daily API quota exhaustion, unsupported model
requests, extra result columns, missing denominator columns, inappropriate tool selection,
zero-sector portfolios and overbroad name interpretation. These are not hidden behind a
claimed 100% accuracy score. Later release notes distinguish any verified improvements.

`52a2cb4` added the live portfolio catalogue, focused planning for structurally complex SQL,
source-overwrite protection and incremental result byte limits. A standalone planner check
fixed sector-presence semantics; a subsequent check still failed ordering and was retained.
`b51a242` finalized ordering instructions and added bounded, counted transport retries after
real ConnectError/ReadTimeout failures. Its fresh supplied release run scored 10/10 twice.
All 110 ordinary tests pass, and its four hosted CI matrix jobs pass. The first extended
run scored 49/50 before these changes; a later run is labeled regression coverage.
