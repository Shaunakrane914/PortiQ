# Interview notes

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
- Ambiguous names produce candidates and clarification, never a silent arbitrary match.
  Unsupported predictions are separate from factual queries against the static dataset.
- Performance is dominated by network and quota pacing; local exposure and SQL timings are
  measured separately. No index improvement or speedup percentage is claimed without a
  controlled before/after experiment.
- With two more weeks: externally authored blind questions, mutation datasets, semantic
  column contracts, tied-order comparison, narrative citation checks, isolated worker
  resource limits, richer live API fault tests, and a small UI sharing the same services.
