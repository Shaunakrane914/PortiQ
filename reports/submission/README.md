# Refactored Maintainability & Prospective Holdout Live Evaluation

Runtime: `refactor/maintainability-2026-11-09` verified commit.
Evaluator: Strict independent SQL oracle & bipartite row matching.
Model: `gemini-3.1-flash-lite` (Live Google GenAI SDK, local routing and answer caching disabled).

| Evaluation Suite | Total Questions | Passed | Strict Correctness | SDK Calls | Tokens |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Supplied Ground Truth** (`ground_truth_dataset.json`) | 10 | **10** | **100%** | 13 | 33,884 |
| **Prospective Holdout** (`prospective_holdout_2026-11-09.json`) | 20 | **20** | **100%** | 27 | 75,486 |
| **Extended Suite** (`extended.json`) | 50 | **50** | **100%** | 65 | 174,979 |
| **Total Live Evaluation** | **80** | **80** | **100%** | **105** | **284,349** |

## Verification Details

- **Prospective Holdout (20/20)**: Authored after runtime freeze and sealed before model evaluation. Genuinely held out, covering SQL aggregations, date constraints, asset-type filters, and multi-tool queries.
- **Extended Suite (50/50)**: Full 50-case evaluation across development, validation, and held-out splits.
- **Supplied Suite (10/10)**: 100% strict correctness with zero regressions against original PL Capital ground truth dataset.
- **Zero API Errors**: 0 provider errors, 0 rate limit dropouts, and 0 dropped turns across all 105 SDK calls.
