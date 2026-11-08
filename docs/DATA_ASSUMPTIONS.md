# Data audit and financial conventions

The original assignment requires sector exposure from holding weights and security sectors, excluding bond holdings. The implementation follows the supplied reference semantics and does not repair data using outside financial information.

## Supplied data

The nine tables contain 603 rows: sectors 10, securities 30, benchmarks 13, portfolios 13, holdings 95, transactions 24, historical_prices 330, portfolio_performance 44 and risk_metrics 44. [data-audit.json](data-audit.json) records source SHA-256 values. The [latest independent database/CSV audit](../reports/cli-2026-11-08/database-csv-audit.json) matched all 603 rows, including types and duplicate multiplicities.

Initialization checks exact CSV headers and row widths, primary keys, uniqueness, required cells, foreign keys, finite numbers, ISO dates, supported asset/transaction classifications, nonnegative holding quantities, valid weights and stock-sector mappings. Blank optional cells become SQL NULL. It validates foreign keys/integrity and atomically replaces a database only with explicit `--rebuild`. Original CSV/schema/assessment inputs are protected against accidental overwrite.

There are 25 stocks, five bonds, ten Active portfolios and three Passive portfolios. Bond rows lack sector/market-cap values; these are missing classifications, not zero-valued stock sectors. Passive is a stored portfolio `status`, distinct from `strategy_type`; runtime domain metadata preserves that distinction.

## Required equity sector exposure

```text
sector exposure (%) = 100 * sum(Stock current_weight in sector)
                           / sum(all Stock current_weight in portfolio)
```

This is allocation **within equities**. `current_weight` is a fraction; bonds do not contribute to either numerator or denominator. Decimal arithmetic uses source-compatible decimal representations and ROUND_HALF_UP to two decimal places. Results include the original total equity weight, formula and rounding basis. Represented zero-weight sectors are retained; displayed percentages can total slightly above/below 100 because of rounding.

Balanced Portfolio has equity weight 0.36: Technology 61.11%, Financials 22.22%, Healthcare 16.67%. Conservative Income Fund has equity weight 0.32. Fixed Income Plus and Total Bond Market Index Fund have no positive equity weight, so equity-only exposure is undefined rather than an invented zero distribution. Missing/invalid stock weights or sector mappings produce an error.

Recorded weights total 1.00 for every portfolio except Total Stock Market Index Fund, whose total is 0.98. The application does not infer cash to fill the gap. Portfolio names/IDs are resolved using exact normalized names or unique contiguous whole-token fragments; ambiguous references require clarification.

## Market value, AUM and reconciliation

The supplied market-value convention is `quantity * securities.current_price`, including bonds unless excluded by the question. It differs from `cost_basis` and `portfolios.total_aum`. Balanced Portfolio has supplied AUM 22,000,000 and illustrative holdings quote value 1,073,279; neither is silently substituted for the other.

AUM currencies are unspecified. Raw arithmetic such as `SUM(total_aum)` remains available for assessment/SQL questions, but a comparable economic aggregate AUM is not established. The dashboard therefore omits the aggregate AUM card and labels individual AUM currency as unspecified. There is no FX conversion, rescaling to AUM or implied currency assignment.

Optional reconciliation compares recorded weights with normalized quote-value weights only when all quantities/prices are valid, total value is positive and every holding has the same known currency. Missing values remain missing; mixed/unknown currencies prevent a combined denominator. Recorded-weight gaps/overweights are disclosed. Reconstructed allocations are illustrations, not corrected official allocations.

Bond prices are used as supplied for reference compatibility. The dataset omits complete face-value, accrued-interest and pricing conventions. Current-price valuation dates are also absent. Warnings accompany reconstructed values even when their arithmetic is valid.

## Static observations and reference-specific conventions

Historical/performance observations are demonstration snapshots from 2023, not a live feed. `securities.current_price` need not equal the latest historical close. Some supplied maturities are in the past relative to this review. No splits, prices, maturities, forecasts or classifications are updated from external sources. A missing series is empty, not zero performance; "latest" means the latest available dataset date.

Supplied question 7 includes only portfolios holding Technology securities; its percentage denominator is all holdings, including bonds. Zero-sector portfolios are included only when explicitly requested. This is a general query convention rather than embedded reference SQL.

Supplied question 8 uses distinct **Stock** sectors divided by **all** holding rows, rounded to three decimals. This is the supplied diversification ratio, not a universal risk metric or the equity-weight exposure formula. Outside that declared convention, broad diversification requests can require clarification.
