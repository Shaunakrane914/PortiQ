# Supplied-question CLI evaluation with evaluator v3

The first complete genuine CLI run on `f3a9954` scored **8/10**. All ten tool results and
routing contracts were correct. Two exposure narratives were falsely rejected because their
tables put percentage units in the header (`Exposure (%)`) rather than each numeric cell.
The verifier was corrected and positive/negative/missing/extra-sector regression tests added.
The original failed run's JSON, Markdown, terminal streams and manifest are retained unchanged.

This run used 21 actual SDK calls and 54,076 reported tokens. Local/cache paths were disabled.
Its 6.5-second SDK interval was a child-process batch setting; normal application pacing and
the retained daily ledger were not reset or changed. No failed fragments are stitched into
later results.
