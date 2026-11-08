# Supplied-question CLI evaluation with evaluator v3

The [final complete fresh run](final/supplied.json) on `b8db4a9` passed **10/10**:
all ten statuses, routing/result contracts and explicit final-answer checks passed.
It used **21 actual SDK calls**, **54,075 reported tokens**, zero provider errors and
132.471 seconds of CLI wall time. Mean/p95 question time was 13.143/19.520 seconds,
including batch pacing. Reference-relative SQL-efficiency mean was 95.52/100; this
is a correctness-gated VM-work score, not logical page I/O.

| Artifact | Purpose |
|---|---|
| [Final JSON](final/supplied.json) / [Markdown](final/supplied.md) | All ten actual answers, references, final-answer checks and metrics |
| [Final manifest](final/run-manifest.json) | Command, source hashes, dates, pacing scope and retained usage ledger |
| [Final terminal stdout](final/cli-stdout.txt) / [stderr](final/cli-stderr.txt) | Genuine subprocess output and exit outcome |
| [First failed capture](supplied.json) / [manifest](run-manifest.json) | Separate 8/10 capture, explained below |

The final run is independent; no successful fragments are combined. A later GUI-only
configuration-forwarding fix does not alter the evaluated agent/model/calculator/evaluator.
The supplied data and both captures remain immutable. These ten previously observed questions
do not establish blind/unseen accuracy or arbitrary prose entailment.

The first complete genuine CLI run on `f3a9954` scored **8/10**. All ten tool results and
routing contracts were correct. Two exposure narratives were falsely rejected because their
tables put percentage units in the header (`Exposure (%)`) rather than each numeric cell.
The verifier was corrected and positive/negative/missing/extra-sector regression tests added.
The original failed run's JSON, Markdown, terminal streams and manifest are retained unchanged.

This run used 21 actual SDK calls and 54,076 reported tokens. Local/cache paths were disabled.
Its 6.5-second SDK interval was a child-process batch setting; normal application pacing and
the retained daily ledger were not reset or changed. No failed fragments are stitched into
later results.
