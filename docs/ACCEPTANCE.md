# Acceptance record

The implementation and dataset are runnable independently from the CLI. This file records
measured checks rather than declaring every target met. Live evaluation artifacts are the
source of truth for model accuracy; the final release update records all completed runs.

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

Release checks still in progress at this record's initial publication:

- Completion of the frozen 50-case live evaluation and separate model comparison.
- Final aggregate results, coverage and hosted GitHub Actions status.

Optional dashboard/API work remains deferred. This is not a claim of production readiness
or a hiring outcome. Review EVALUATION.md and KNOWN_LIMITATIONS.md before interpreting scores.
