# Known limitations

- This is a local take-home implementation, not a production financial advice or trading service.
- Gemini model access and quotas are external dependencies. Earlier runs reached both minute
  and daily free-tier limits. The configured model and pacing must fit the reviewer's account.
- A successful SQL execution is not proof of semantic correctness. The supplied reference
  has stricter projections, ordering and sector-presence semantics than some natural-language
  readings; the independent evaluator intentionally exposes such failures.
- Exposure is normalized within equities, which differs from whole-portfolio sector allocation.
  Both the formula and raw equity weight are returned. Bonds without equities produce an error.
- Reported AUM, prices, holdings and 2023 historical snapshots are not reconciled or updated.
  Bond face values/accrued interest and currency conversion are not defined by the assignment.
- Generated prose is separate from authoritative structured evidence. Automatic scoring does
  not validate every sentence; a narrative may misstate or add unsupported interpretation.
- Result comparison permits column aliases but uses positional projection semantics. Ordered
  ties and empty results have limitations described in EVALUATION.md.
- Strict routing scoring penalizes successful extra analytical calls, including discovery.
- The additional 50 questions were authored by the implementer. Their split does not establish
  an independently blind or externally validated generalization score.
- There is no persistent chat memory, answer cache, multi-user authentication or isolated worker.
  The SQLite execution boundary is defense in depth for local use, not a hard memory sandbox.
- The wheel excludes source datasets; install from a checkout and set PORTIQ_SOURCE when needed.
- Dashboard and REST API enhancements are deliberately deferred. The mandatory CLI is independent.

The acceptance record distinguishes completed local checks from live results and remote CI.
