# v0.1.1 acceptance record

This patch addresses the semantic-column error and evaluation blind spot identified in
the v0.1.0 review. Financial calculations, SQL authorization, dataset and frozen reference
suites remain unchanged. Runtime source revision: `03e9585`. Release evidence is indexed
in [reports/README.md](../reports/README.md).

| Review requirement | Implemented evidence | Verification |
|---|---|---|
| Fix Passive/status semantics without a question shortcut | SQLite-derived distinct values for portfolio status and strategy, exposed to routing and focused planning | Dynamic-context tests move values between columns; fresh categorical and extended runs |
| Score correctness and routing independently | Evaluator v2 checks all reference candidates even after routing mismatch; records every failure dimension | Both historical ext-02 traces fail result, routing and narrative checks; correct-result/extra-call control test |
| Clarify confusing report names without altering evidence | Report index labels supplied-final as pre-release 16/20 and supplied-release as v0.1.0's 20/20 release | Original report hashes and v0.1.0 tag preserved; helper defaults write local/versioned outputs |
| Test limited answer faithfulness | Separate evaluation-only rules for numerical claims, portfolio identities, sector percentages and contradictions | Wrong-number/identity/empty-claim tests, legitimate rounding tests, explicit not_checked coverage |

## Verified local quality

- 148 ordinary tests pass; two opt-in live tests are skipped in the normal suite.
- Overall line coverage is 94.04%; exposure and narrative-assertion modules have 100%
  line coverage, and the SQL boundary has 93.67%. Line coverage is not a claim of complete
  security or universal narrative understanding.
- Ruff formatting/linting and strict mypy pass.
- A separate Python 3.11.15 environment installs from the frozen lockfile, passes 148 tests
  and static checks without API credentials, rebuilds all nine CSVs, and reports valid
  SQLite integrity and foreign keys on the exact runtime revision.
- All four runtime CI jobs pass: Windows/Linux, Python 3.11/3.13.
- All original CSVs, schema, ground truth, frozen 50-case suite and archived assignment
  README remain unchanged. Every v0.1.0 report's committed Git blob is preserved
  byte-for-byte; Windows checkouts can normalize working-copy line endings.

See [verification.json](../reports/v0.1.1/verification.json) for measured counts, source
revision, original report hashes, coverage and hosted CI link.

## Live evidence

The final frozen runtime passes the supplied benchmark 10/10, including four configured
narrative assertion cases, and the three categorical development questions twice (6/6),
with exact routing and zero assertion failures. The full extended regression result is
recorded separately in [extended.json](../reports/v0.1.1/extended.json): **50/50**. The
targeted ambiguity case also passes all three fresh trials. Full-suite scores are not
reconstructed by combining retries or development runs. Offline replay independently
reconciles all 65 successful tool results from these final-runtime reports with zero mismatches.

These are real Gemini calls using `gemini-3.1-flash-lite`, 6.5-second request pacing and
no answer cache. Reports expose actual invocations, token totals, source/suite/rule hashes,
model versions and per-case evidence. End-to-end latency includes deliberate pacing and
any bounded transport retries. Narrative checks cover a declared subset, not all prose.

## Retained failures and correction

The v0.1.0 extended failure was more than an extra SQL call: it queried the wrong column
and falsely concluded that the requested portfolios did not exist. The old release summary
understated that error. New offline diagnostics re-score the exact old traces and show all
three failing dimensions without changing their original files or claiming a fresh model run.

The first v0.1.1 context expansion included unrelated industry aliases and caused regressions
(7/10 supplied). Limiting context to portfolio classifications restored those cases but
exposed an implicit-order mismatch (9/10). Existing projection/ordering conventions were
made explicit in the SQL argument schema. All development reports and the interrupted
partial run remain labeled in the report index; none is presented as the final release score.
The previous extended attempt passed its first 34 cases before daily quota exhaustion;
its remaining 16 HTTP 429 failures are retained separately. An evaluator regression test
now ensures provider status codes are not misclassified as financial narrative claims.
An earlier full run scored 48/50 due to HTTP 503/504. Its separate retry recovered the
hybrid case but exposed a genuine ambiguity error: the model replaced an ambiguous user
fragment with a guessed full portfolio name. The exposure argument contract now explicitly
preserves the original reference so the existing deterministic resolver can reject ambiguity.
Both the failed trace and new repeated ambiguity checks are retained in the report index.

## Scope and remaining limits

The 50 additional questions and three categorical regressions are author-created and
already observed. Their v0.1.1 results are regression evidence, not externally blind
generalization. Limited prose patterns do not certify every statement or interpretation.
Model availability/quotas remain external dependencies. Optional UI/API work stays deferred.
The release is intended for technical review, not as a production financial advice service.
