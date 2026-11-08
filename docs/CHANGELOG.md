# Change history

The full development narrative and removed experiment artifacts remain in the [pre-cleanup snapshot](https://github.com/Shaunakrane914/PortiQ/tree/ace58054c7a778817d68a7c1d81386b7dffd95e8). Tags and historical reports are not rewritten.

## Current consolidation

- Merged container startup into `api.py`; Docker now uses `python -m portiq.api`.
- Combined tool and cache measurements in `scripts/benchmark.py`; outputs default to ignored local reports and existing evidence is not overwritten.
- Removed the one-off historical diagnostic script and unused planner telemetry/summary code.
- Consolidated decisions, experiments, performance, acceptance, interview and requirement notes into [engineering notes](ENGINEERING_NOTES.md).
- Retained CLI chat, genuine Gemini orchestration, SQL authorization, financial formulas, API/dashboard, tests and original assessment inputs.

## Cleanup after v0.2 experiments

Commit `122dee6` removed the experimental planner and selected development artifacts and moved deterministic rendering into `agent.py`. A follow-up guard rejects the removed API strategy instead of silently using the original agent. Documentation distinguishes archived measurements from current checks; removed evidence remains in Git history.

## v0.2 platform work

Added shared analytics/reconciliation, local capabilities, exact caching, bounded conversation context, actual SDK accounting, quota-aware retries/circuit/fallback, optional FastAPI/static dashboard and non-root Docker checks. The original planner remains supported.

Archived original-agent results were 10/10 supplied, 50/50 extended and 8/8 platform. Experimental results were 9/10, 50/50 and 7/8, including a Technology-sector projection mismatch and unjustified portfolio guess. The experimental path was not promoted and was later removed. A failed 250-attempt provider run and reporting-metadata caveats remain explicitly documented in the archived evidence. Intermediate container artifact inclusion was corrected before any image publication.

## v0.1.1

Fixed Passive/status semantics using database-derived classification values, separated result/routing/narrative scoring, and preserved historical failures. Archived fresh results: 10/10 supplied, 50/50 extended, 6/6 categorical and 3/3 ambiguity; 148 ordinary tests, 94.04% line coverage and four CI jobs. These are historical source-specific results.

## v0.1.0

Delivered the CLI-first Gemini agent, read-only SQL tool, Decimal exposure calculator and independent evaluator. Its extended ext-02 failure was genuinely wrong-column semantics and a false narrative, not merely an extra tool call. Later diagnostics corrected that interpretation without altering the old reports.


## Public interface cleanup

Reduced navigation to four portfolio views. Removed internal reports/configuration/cache endpoints and schema discovery, redacted browser errors, and removed assessment branding. The default local interface has no added password wall; existing optional deployment controls remain. The web image excludes historical reports and benchmark fixtures. Applied a midnight-navy, ivory and champagne-gold palette with tested text contrast. The repository remains public by the owner's explicit choice; website cleanup does not hide existing GitHub copies.
