# Evaluation: ground_truth_dataset.json

6/10 passed. Routing: 8/10. Model: `gemini-3.1-flash-lite`. Cache disabled. Trials: 1.

| Trial | ID | Pass | Failure |
|---|---|---|---|
| 1 | 1 | True |  |
| 1 | 2 | True |  |
| 1 | 3 | True |  |
| 1 | 4 | True |  |
| 1 | 5 | True |  |
| 1 | 6 | False | Ordered row 0: expected ['Consumer Discretionary', 3380.0], actual ['Automotive', 248.5]. |
| 1 | 7 | False | Projection width: expected ['portfolio_name', 'tech_value', 'total_value', 'tech_percentage'], got ['portfolio_name', 'tech_sector_value', 'tech_percentage']. |
| 1 | 8 | False | Expected tools ['sql_query']; got ['sql_query', 'exposure_calculator']. |
| 1 | 9 | True |  |
| 1 | 10 | False | Expected tools ['exposure_calculator']; got ['sql_query', 'exposure_calculator', 'exposure_calculator', 'exposure_calculator']. |
