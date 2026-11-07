# Interview notes

- v0.1.0's Passive-portfolio failure was valid SQL with the wrong semantics: the value
  belonged to `status`, not `strategy_type`. v0.1.1 exposes both fields' actual distinct
  values rather than adding an exact-question shortcut. A test moves the value between
  columns to prove that context follows the data. An initially broader metadata expansion
  caused sector/industry confusion and was narrowed based on a retained failed live run.
- Result correctness and routing efficiency are separate. Historical ext-02 fails both,
  and the new name/contradiction assertions also flag its false narrative. An extra useful
  discovery query can instead have correct results and inefficient routing. Limited prose
  assertions do not certify every statement or replace exact SQL/financial comparison.

- Gemini function calling exposes explicit typed choices; the model, not a keyword table,
  chooses tools. Tool calls are dispatched manually so SQL validation cannot be bypassed.
- Sector exposure uses stored fractional stock weights divided by total stock weight. Bonds
  do not contribute to either numerator or denominator. Balanced Portfolio's denominator is
  0.36; the index portfolio with weights totaling 0.98 is normalized rather than patched.
- Read-only URI mode and the SQLite authorizer enforce safety independently of the prompt
  and SQL parser. A SELECT-only prefix check would miss nested writes, functions and commands.
- Repair is bounded to avoid runaway API cost and repeated invalid SQL. Identical failing
  statements terminate early; repaired SQL goes through the same checks.
- Equivalent SQL can have different strings. The evaluator compares full results with
  duplicate multiplicity and numerical tolerances, preserving reference ordering. Extra
  columns fail even when the narrative sounds right.
- The supplied ten questions are a development benchmark. The additional fifty were
  authored here, frozen before execution, and split into development/validation/heldout.
  They do not prove external generalization or independent reviewer validation.
- Mocked Gemini responses establish orchestration/error-path behavior, not live model
  accuracy. Live reports include every attempted question, including quota failures.
- The resolver rejects ambiguous references with candidates. The model is instructed to
  preserve the original reference; a retained failure shows why guessing a full name before
  calling the resolver can bypass that protection. Repeated live checks cover this contract.
  Unsupported predictions are separate from factual queries against the static dataset.
- Performance is dominated by network and quota pacing; local exposure and SQL timings are
  measured separately. No index improvement or speedup percentage is claimed without a
  controlled before/after experiment.
- With two more weeks: externally authored blind questions, mutation datasets, semantic
  column contracts, tied-order comparison, narrative citation checks, isolated worker
  resource limits, richer live API fault tests, and a small UI sharing the same services.
