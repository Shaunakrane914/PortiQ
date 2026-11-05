# Data audit and financial conventions

The input consists of 9 tables and 603 rows: sectors 10, securities 30, benchmarks 13,
portfolios 13, holdings 95, transactions 24, historical_prices 330,
portfolio_performance 44, risk_metrics 44. `data-audit.json` records source SHA-256 hashes.

Schema constraints validate primary keys, uniqueness, required cells, foreign keys,
Stock/Bond classification and transaction types. Ingestion additionally checks exact CSV
headers, row width, finite numbers, ISO dates, explicit primary keys, nonnegative holdings,
weights within [0,1], and sector mappings for stocks. Blank optional cells become SQL NULL.
Foreign-key and SQLite integrity checks pass. No original financial values were repaired.

There are 25 stocks, 5 bonds, 10 Active portfolios and 3 Passive portfolios. The five bond
records have no sector or market cap; stock-only exposure intentionally excludes them.
Index portfolios' Passive status is preserved rather than recoded as Active.

All total holding weights equal 1.00 except Total Stock Market Index Fund, which sums to
0.98. Conservative Income Fund has equity weight 0.32; Balanced Portfolio has 0.36.
Fixed Income Plus and Total Bond Market Index Fund have no equities. Exposure is undefined
for those two portfolios; an explicit error is preferable to an invented zero distribution.

Sector exposure is `100 * sector stock current_weight / sum(all stock current_weight)`.
This is allocation *within equities*, not allocation as a percentage of all assets. Decimal
arithmetic uses source-compatible decimal representations and ROUND_HALF_UP at two decimal
places. The raw total equity weight and formula accompany every result. Rounded sector
totals may differ slightly from 100. Zero-weight represented sectors are retained.

Market value is `quantity * securities.current_price`, including bonds unless filtered.
It does not reconcile to reported total_aum. For example Balanced Portfolio's supplied AUM
is 22,000,000 while calculated holdings market value is 1,073,279. The implementation never
silently replaces one with the other. Bond prices are used as supplied for assessment
compatibility; the data does not specify face-value or accrued-interest conventions.

The data is a static 2023 demonstration, not a live feed. Prices and other attributes may
be economically unrealistic; historical close prices need not equal securities.current_price.
Some bonds have maturity dates before the submission date. No prices, splits, maturities,
or sector classifications are adjusted using external financial data.

Supplied question 7's reference includes only portfolios holding Technology securities.
Its denominator includes all holdings, including bonds. Returning all portfolios with
zero Technology values is a reasonable alternate interpretation but fails that supplied
contract. This is documented and expressed as a general sector-filtered query convention,
without inserting the reference SQL into runtime code.

Supplied question 8 counts distinct equity sectors but divides by *all* holdings. This is
the provided diversification ratio, not a general risk metric. Broad phrases such as
"diversification metrics" remain underspecified outside this assessment convention.
