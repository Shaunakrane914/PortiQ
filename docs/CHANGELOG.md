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

The later regression run also scored 49/50. `8d88898` handled corrupt SQLite files and
accepted valid case-insensitive `main` qualification; new tests caught and fixed an
authorizer case-sensitivity issue. Its local suite passes 116 tests. Offline replay
reconciled all 70 recorded release tool results with zero mismatches. No additional
live accuracy claim is inferred from that replay.

## v0.1.1 review corrections

- `b0514c8` added database-derived categorical context for routing and planning, with
  regression tests that change the database values rather than matching question text.
- `11bd796` separated answer, reference-result, routing and limited narrative dimensions.
  Both old `ext-02` traces now expose the wrong column and false conclusion independently
  of their extra-call failure. Original evidence is preserved.
- `076600d` restricted classification context to portfolio status and strategy after a
  broader version exposed unrelated industry aliases and regressed supplied cases (7/10).
  The narrower context scored 9/10, with an implicit ordering mismatch.
- `b5e27a9` exposed the existing projection/ordering contract in the SQL argument schema.
  Fresh checks passed 10/10 supplied and 6/6 categorical cases. A subsequent extended
  attempt passed 34 cases then reached the provider's daily quota; all 16 HTTP 429 failures
  remain in the preflight report, without being counted as model capability evidence.
- `25c0dd5` prevents non-answer error messages from being treated as numerical claims.
  Its full live run scored 48/50 after two provider failures. A separate retry scored
  1/2 and exposed an ambiguity error in the other case; both records remain unchanged.
  Offline quality checks pass 148 tests, with two opt-in live tests skipped.
- `03e9585` makes the exposure argument's original-reference contract explicit: the model
  must not replace an ambiguous fragment with a guessed full name or ID. The optional
  live regression now checks both categorical semantics and ambiguity handling. Fresh
  repeated ambiguity checks and a new full release run validate this final runtime.

The final runtime's fresh release run passed 10/10 supplied, 50/50 extended and 6/6
categorical cases. Its separate ambiguity check passed 3/3. All 65 successful recorded
tool results were replayed offline with zero mismatches. The exact runtime passes the
four hosted CI jobs and a clean Python 3.11 installation with 148 tests; historical
failures remain visible instead of being combined into a reconstructed score.

The report index distinguishes historical `supplied-final` (16/20 pre-release) from
`supplied-release` (20/20 v0.1.0 release). Helper defaults write to local or versioned
paths so published v0.1.0 evidence is preserved.


## v0.2.0 platform upgrade

- Preserved original inputs, tests, benchmarks, SQL authorization, exposure formula, CLI defaults and historical releases.
- Added deterministic tool rendering, experimental typed one-call graphs with original-agent fallback, an explicit four-capability local registry and bounded exact caching.
- Added recorded/quote allocation reconciliation, snapshots, concentration summaries, actual historical observations and explicit data-quality/currency warnings.
- Added actual SDK attempt/token/service/pacing metrics, atomic optional shared request budget, error-aware retries, optional sequential fallback and a bounded failure circuit following observed transport failures.
- Added bounded opt-in conversation context, thin FastAPI endpoints and an original six-view static dashboard with safe DOM/CSV export.
- Added non-root Docker packaging, key-free API/browser/container checks and separate eight-case platform regression cases.
- Current local quality: 204 passed, two opt-in live skips, 91.80% line coverage, strict mypy/Ruff pass. A clean Python 3.11 archive install and all five current CI jobs pass. Eight offline browser checks pass; genuine uncached browser evidence is separate.
- Kept one-call opt-in after reproduced 13-versus-eight-row Technology-sector valuation regression. Retained the incomplete 250-attempt provider-failure run and fresh-client probe transparently. Final live scores and release decision belong to the versioned evidence and acceptance audit.

- Complete fresh live comparison: default 10/10 supplied, 50/50 extended, 8/8 new platform; experimental 9/10, 50/50, 7/8. Default categorical repetitions pass 6/6 and ambiguity repetitions 3/3. No provider failures in the completed paired run.
- Final genuine browser analysis passes with two SDK calls, 5,327 reported tokens and cache disabled. A distinct capture preserves earlier evidence.
- Final packaging audit caught an overly broad report-directory exception that admitted local developer artifacts into an intermediate image. Explicit ten-file report copies, a corrected build-context allowlist and build-time exclusion assertions fix the issue. The rebuilt non-root image passes HTTP/archive-score checks and graceful shutdown; no container image was publicly published.
- Raw experiment reports retain their original metric/completion metadata quirks; a separate validated diagnostic explains them, and the helper fixes labels/marker for future runs without rewriting evidence.
