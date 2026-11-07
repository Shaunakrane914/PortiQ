# Evaluation: ground_truth_dataset.json

7/10 passed. Answer correctness: 8/10. Routing: 8/10. Limited narrative checks: 4 cases, 0 failures. Unchecked prose is not certified. Model: `gemini-3.1-flash-lite`. Cache disabled. Trials: 1.

| Trial | ID | Strict pass | Answer | Routing | Narrative | Failure |
|---|---|---|---|---|---|---|
| 1 | 1 | True | True | True | passed |  |
| 1 | 2 | True | True | True | not_checked |  |
| 1 | 3 | False | True | False | not_checked | routing: Expected tools ['sql_query']; got ['sql_query', 'sql_query', 'sql_query']. |
| 1 | 4 | True | True | True | passed |  |
| 1 | 5 | False | False | True | not_checked | result: Reference 0: Projection width: expected ['holding_id', 'symbol', 'company_name', 'quantity', 'cost_basis'], got ['symbol', 'company_name', 'cost_basis']. |
| 1 | 6 | True | True | True | not_checked |  |
| 1 | 7 | False | False | False | not_checked | status: Expected answer; actual error: Analytical tool budget exhausted. / routing: Expected tools ['sql_query']; got ['sql_query', 'sql_query', 'sql_query', 'sql_query', 'sql_query', 'sql_query']. / result: Reference 0: Row count: expected 8, actual 0.; Projection width: expected ['portfolio_name', 'tech_value', 'total_value', 'tech_percentage'], got ['sector_name'].; Row count: expected 8, actual 0.; Projection width: expected ['portfolio_name', 'tech_value', 'total_value', 'tech_percentage'], got ['sector_name', 'industry_group'].; Projection width: expected ['portfolio_name', 'tech_value', 'total_value', 'tech_percentage'], got ['count(*)'].; Row count: expected 8, actual 0. |
| 1 | 8 | True | True | True | not_checked |  |
| 1 | 9 | True | True | True | passed |  |
| 1 | 10 | True | True | True | passed |  |
