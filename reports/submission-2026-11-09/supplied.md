# Evaluation: ground_truth_dataset.json

5/10 passed. Answer correctness: 5/10. Routing: 10/10. Deterministic answer checks: 10 cases, 3 failures. Unchecked prose is not certified. Model: `gemini-3.1-flash-lite`. Cache disabled. Trials: 1.

| Trial | ID | Strict pass | Answer | Routing | Narrative | Failure |
|---|---|---|---|---|---|---|
| 1 | 1 | True | True | True | passed |  |
| 1 | 2 | True | True | True | passed |  |
| 1 | 3 | False | False | True | passed | result: Reference 0: Projection width: expected ['symbol', 'company_name'], got ['symbol', 'company_name', 'asset_type', 'market_cap', 'current_price']. |
| 1 | 4 | True | True | True | passed |  |
| 1 | 5 | False | False | True | failed | result: Reference 0: Projection width: expected ['holding_id', 'symbol', 'company_name', 'quantity', 'cost_basis'], got ['company_name', 'cost_basis']. / faithfulness: Reference 0: missing or incorrect complete row [1, 'AAPL', 'Apple Inc.', 2500.0, 438000.0].; Reference 0: missing or incorrect complete row [8, 'AMZN', 'Amazon.com Inc.', 100.0, 320000.0].; Reference 0: missing or incorrect complete row [2, 'MSFT', 'Microsoft Corporation', 800.0, 304400.0].; Reference 0: missing or incorrect complete row [3, 'NVDA', 'NVIDIA Corporation', 400.0, 288040.0].; Reference 0: missing or incorrect complete row [6, 'CRM', 'Salesforce Inc.', 1000.0, 185400.0]. |
| 1 | 6 | False | False | True | passed | result: Reference 0: Ordered row 0: expected ['Consumer Discretionary', 3380.0], actual ['Automotive', 248.5]. |
| 1 | 7 | False | False | True | failed | result: Reference 0: Projection width: expected ['portfolio_name', 'tech_value', 'total_value', 'tech_percentage'], got ['portfolio_name', 'technology_value', 'technology_percentage']. / faithfulness: Reference 0: missing or incorrect complete row ['Tech Innovation Fund', 1565292.5, 1565292.5, 100.0].; Reference 0: missing or incorrect complete row ['Growth Equity Fund', 1866148.0, 2204148.0, 84.67].; Reference 0: missing or incorrect complete row ['Total International Index Fund', 1427086.0, 2281686.0, 62.55].; Reference 0: missing or incorrect complete row ['International Equity Fund', 346888.0, 734928.0, 47.2].; Reference 0: missing or incorrect complete row ['Total Stock Market Index Fund', 3093520.0, 6622340.0, 46.71].; Reference 0: missing or incorrect complete row ['Balanced Portfolio', 388704.0, 1073279.0, 36.22].; Reference 0: missing or incorrect complete row ['Emerging Markets Fund', 339095.0, 1045100.0, 32.45].; Reference 0: missing or incorrect complete row ['ESG Sustainable Fund', 272978.0, 1007228.0, 27.1]. |
| 1 | 8 | False | False | True | failed | result: Reference 0: Projection width: expected ['portfolio_name', 'sector_count', 'total_holdings', 'diversification_ratio'], got ['portfolio_name', 'sector_count', 'var_95', 'var_99', 'cvar_95', 'beta', 'correlation_sp500', 'tracking_error', 'information_ratio', 'sortino_ratio']. / faithfulness: Reference 0: missing or incorrect complete row ['Total Stock Market Index Fund', 6, 12, 0.5]. |
| 1 | 9 | True | True | True | passed |  |
| 1 | 10 | True | True | True | passed |  |
