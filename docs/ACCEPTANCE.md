# Acceptance record

The implementation and dataset are runnable independently from the CLI. Runtime revision
`b51a242` has passed local checks and all four hosted CI jobs. Live evaluation artifacts
are the source of truth for model accuracy; earlier unsuccessful runs remain available.

Verified locally:

- All nine original CSVs load to SQLite with 603 rows and valid foreign keys.
- Original assessment data, schema, ground truth, requirements and archived README are preserved.
- Read-only SQL execution rejects unsafe operations; exposure reconciles independently for
  every supplied portfolio, with explicit undefined results for the two bond-only portfolios.
- Genuine Gemini function calling and natural-language SQL execute from the CLI.
- Both complete supplied development runs and repeat trials are recorded, including failures.
- Ruff and strict mypy pass; normal tests need no API credentials.
- A fresh Python 3.11.15 environment with no API key installs from the lockfile and passes
  its tests, database initialization, doctor, explicit SQL and exposure smoke checks.
- The updated isolated environment passes all 110 ordinary tests; the opt-in live test is skipped.
- The final supplied benchmark passes 20/20 across two uncached trials (10/10 each), with
  20/20 exact routing matches using configured and provider model `gemini-3.1-flash-lite`.
- The first frozen extended benchmark passes 49/50. Its failure is an extra successful SQL
  call, penalized by the documented strict routing contract. It predates catalogue/planner fixes.
- Local coverage is 92.64% overall, 100% exposure and 93.67% SQL; Ruff and strict mypy pass.
- Current API credentials are absent from tracked/staged files; original input hashes are unchanged.

Measured supplied release performance includes 6.5-second request pacing: mean 17.854 s,
p95 42.669 s, 45 actual backend invocations and 104,975 provider-reported tokens across
20 questions. These include transient retries and are not unthrottled model benchmarks.
Local 200-iteration microbenchmarks measure exposure mean 1.610 ms and SQL mean 1.160 ms;
raw samples and tracemalloc peak are committed in `reports/performance.json`.

Release checks still in progress at this record's current publication:

- Completion of the post-change extended regression run and final release tag.

The alternate `gemini-3.6-flash` comparison scores 0/10 because its API requests failed
(400/503); it does not establish that model's analytical accuracy. The interrupted transport
run is labeled incomplete. Neither is combined into the final model's supplied release score.

Optional dashboard/API work remains deferred. This is not a claim of production readiness
or a hiring outcome. Review EVALUATION.md and KNOWN_LIMITATIONS.md before interpreting scores.
