# Evaluation methodology

The supplied ten questions are development material. Production modules do not import
their answers, SQL or identifiers. Prompt conventions were refined after genuine failures
on that supplied development set; scores on it do not establish unseen generalization.
Earlier unsuccessful runs are retained, including API-quota failures.

SQL scoring executes trusted reference SQL using an independent SQLite connection,
re-executes generated SQL through the safety boundary, and reconciles the actual returned
rows with that execution. The reference projection width must match. Values are positional;
alias spelling is not scored. Numeric cells use relative tolerance 1e-7 and absolute tolerance
1e-6. NULL differs from zero and strings do not equal numbers.

Top-level ORDER BY in the reference makes row order mandatory. Unordered output uses a
maximum bipartite match of complete rows so duplicate multiplicities and tolerance overlap
are handled correctly. Ties in ordered queries currently follow reference execution order;
an equally valid alternative tie order may fail. Extra, missing and truncated rows fail.
An empty result with the correct projection has limited ability to reveal semantic mistakes.

Exposure expectations read the original CSV files directly, join using Python dictionaries,
and calculate unrounded Decimal references without calling the production resolver or
calculator. Every sector and its numerical value must agree within 0.005001 percentage
points, allowing the production tool's two-decimal rounding. Portfolio identity must match.

Routing is deliberately strict: the multiset of successful analytical calls must match
the case's required calls. Extra discovery calls count as a routing mismatch, even if they
are harmless. This distinguishes routing efficiency from result validity, but can penalize
a defensible alternative workflow. There is no automatic prose-faithfulness score; the
reported accuracy measures structured evidence plus status/routing, not every final sentence.

The 50 additional questions were authored in this project and frozen in Git before their
first live evaluation. They include 34 SQL questions, 9 exposure questions, 3 hybrid questions,
2 clarification cases and 2 unsupported/security cases. The split is 17 development,
17 validation and 16 heldout. They are held out from runtime prompts, but not externally
authored or blind to the implementation author. Exact projections/order are specified in
many questions to avoid confusing underspecification with SQL competence.

Subjective handling cases score explicit status (clarification/unsupported), not exact prose.
They complement deterministic security tests and do not prove resistance to every injection.
Mock orchestration tests are never counted as live model accuracy.

Each live report includes per-case expected/actual data, status, routing, SQL validity where
applicable, failures, latency, SDK call count, provider token counts, model versions and
cache status. New reports also include source, suite and runtime hashes and pacing/budgets.
SDK automatic retries are disabled in the final implementation, so request accounting does
not hide automatic transport retries. No persistent answer cache is used.

The release script runs two uncached supplied trials, then one complete extended trial.
Latency includes intentional quota pacing as well as model/network time; it should not be
presented as unthrottled model latency. Comparison runs across models are separate artifacts,
not interchangeable samples of one configuration.

Results are recorded in the committed JSON/Markdown files in `reports/`; read the acceptance
record for the final measured outcome. A failed run is not replaced by a fictional target score.
