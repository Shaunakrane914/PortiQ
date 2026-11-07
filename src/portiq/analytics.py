"""Local dataset analytics. Recorded weights and quote-value reconstructions stay distinct."""

from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from portiq.database import connect_readonly
from portiq.errors import PortfolioError
from portiq.exposure import ExposureResult, calculate_exposure, resolve_portfolio


class Notice(BaseModel):
    kind: str
    code: str
    message: str


class Holding(BaseModel):
    holding_id: int
    symbol: str
    company_name: str
    asset_type: str
    sector: str | None
    currency: str | None
    quantity: float | None
    current_price: float | None
    current_weight: float | None
    cost_basis: float | None


class AllocationRow(BaseModel):
    holding_id: int
    symbol: str
    sector: str
    currency: str | None
    recorded_percent: str | None
    position_value: str | None
    reconstructed_percent: str | None
    difference_pp: str | None


class Reconciliation(BaseModel):
    rows: list[AllocationRow]
    sectors: list[dict[str, str | None]]
    recorded_total_percent: str | None
    unrepresented_percent: str | None
    overweight_percent: str | None
    quoted_total_value: str | None
    currency: str | None
    comparable: bool
    warnings: list[Notice]
    methodology: str = (
        "Recorded: current_weight × 100. Reconstructed: quantity × current_price / sum of "
        "all listed quote values × 100, including bonds. Difference = reconstructed minus "
        "recorded percentage points. No FX conversion, accrued interest, inferred cash, "
        "valuation date or AUM scaling. Bond quote conventions may differ"
        " from economic value."
    )
    source_columns: list[str] = Field(
        default_factory=lambda: [
            "holdings.quantity",
            "holdings.current_weight",
            "securities.current_price",
            "securities.currency",
            "securities.asset_type",
            "sectors.sector_name",
        ]
    )


class Snapshot(BaseModel):
    portfolio: dict[str, Any]
    holdings: list[Holding]
    exposure: ExposureResult | None
    reconciliation: Reconciliation
    performance: list[dict[str, Any]]
    risk: list[dict[str, Any]]
    prices: list[dict[str, Any]]
    composition_percent: dict[str, str]
    warnings: list[Notice]


def records(path: Path, sql: str, parameters: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    """Fixed application queries only; generated SQL uses the existing SQL boundary."""
    with connect_readonly(path) as conn:
        cursor = conn.execute(sql, parameters)
        names = [c[0] for c in cursor.description]
        return [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]


def number(value: Any) -> Decimal | None:
    try:
        result = Decimal(str(value))
        return result if result.is_finite() else None
    except (InvalidOperation, ValueError):
        return None


def display(value: Decimal | None) -> str | None:
    return (
        str(value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))
        if value is not None
        else None
    )


def invalid_number(raw: Any, *, weight: bool = False) -> bool:
    if raw is None:
        return False
    value = number(raw)
    return value is None or value < 0 or (weight and value > 1)


def reconcile(holdings: list[Holding]) -> Reconciliation:
    warnings = [
        Notice(
            kind="incomplete",
            code="valuation_dates",
            message=(
                "Current-price valuation dates and portfolio AUM currency are not supplied; "
                "reconstructed allocations are quote-value illustrations, not "
                "corrected recorded weights."
            ),
        )
    ]
    currencies = {h.currency for h in holdings}
    values: list[Decimal | None] = []
    weights: list[Decimal | None] = []
    for h in holdings:
        quantity, price, weight = (
            number(h.quantity),
            number(h.current_price),
            number(h.current_weight),
        )
        values.append(
            quantity * price
            if quantity is not None and quantity >= 0 and price is not None and price >= 0
            else None
        )
        weights.append(weight if weight is not None and 0 <= weight <= 1 else None)
    if any(v is None for v in values):
        invalid = any(
            invalid_number(h.quantity) or invalid_number(h.current_price) for h in holdings
        )
        warnings.append(
            Notice(
                kind="invalid" if invalid else "incomplete",
                code="market_values",
                message="Missing or invalid quantity/price prevents a complete reconstruction.",
            )
        )
    if any(w is None for w in weights):
        invalid_weight = any(invalid_number(h.current_weight, weight=True) for h in holdings)
        warnings.append(
            Notice(
                kind="invalid" if invalid_weight else "incomplete",
                code="weights",
                message="Missing, non-finite or out-of-range recorded weights; recorded "
                "totals are unavailable.",
            )
        )
    if len(currencies) != 1 or None in currencies or "" in currencies:
        warnings.append(
            Notice(
                kind="incomplete",
                code="currencies",
                message="Mixed or unknown currencies: no combined quote-value denominator"
                " or reconstructed weights are reported.",
            )
        )
    total = sum((v for v in values if v is not None), Decimal(0))
    comparable = (
        bool(holdings)
        and all(v is not None for v in values)
        and len(currencies) == 1
        and bool(next(iter(currencies), None))
        and total > 0
    )
    if total <= 0:
        warnings.append(
            Notice(
                kind="incomplete",
                code="denominator",
                message="No positive complete quote-value denominator.",
            )
        )
    if any(h.asset_type == "Bond" for h in holdings):
        warnings.append(
            Notice(
                kind="convention",
                code="bond_quotes",
                message="Bond face-value units, accrued interest and quote conventions "
                "are unspecified. Quote-value weights may differ from economic "
                "allocations.",
            )
        )
    recorded = (
        sum((w for w in weights if w is not None), Decimal(0))
        if all(w is not None for w in weights)
        else None
    )
    if recorded is not None and abs(recorded - 1) > Decimal("0.000001"):
        warnings.append(
            Notice(
                kind="concern",
                code="weight_total",
                message="Listed recorded weights do not total 100%; the difference is "
                "unrepresented or excess weight, not inferred cash or a confirmed"
                " data error.",
            )
        )
    rows = []
    sector_weights: dict[str, Decimal] = defaultdict(Decimal)
    sector_values: dict[str, Decimal] = defaultdict(Decimal)
    for h, weight, value in zip(holdings, weights, values, strict=True):
        sector = "Bond" if h.asset_type == "Bond" else h.sector or "Unclassified stock"
        rebuilt = value / total * 100 if comparable and value is not None else None
        recorded_pp = weight * 100 if weight is not None else None
        rows.append(
            AllocationRow(
                holding_id=h.holding_id,
                symbol=h.symbol,
                sector=sector,
                currency=h.currency,
                recorded_percent=display(recorded_pp),
                position_value=display(value),
                reconstructed_percent=display(rebuilt),
                difference_pp=display(
                    rebuilt - recorded_pp
                    if rebuilt is not None and recorded_pp is not None
                    else None
                ),
            )
        )
        if weight is not None:
            sector_weights[sector] += weight * 100
        if value is not None:
            sector_values[sector] += value
    sectors = [
        {
            "sector": s,
            "recorded_percent": display(sector_weights[s]) if recorded is not None else None,
            "reconstructed_percent": display(sector_values[s] / total * 100)
            if comparable
            else None,
            "difference_pp": display(sector_values[s] / total * 100 - sector_weights[s])
            if comparable and recorded is not None
            else None,
        }
        for s in sorted(set(sector_values) | set(sector_weights))
    ]
    return Reconciliation(
        rows=rows,
        sectors=sectors,
        recorded_total_percent=display(recorded * 100 if recorded is not None else None),
        unrepresented_percent=display(
            max(1 - recorded, Decimal(0)) * 100 if recorded is not None else None
        ),
        overweight_percent=display(
            max(recorded - 1, Decimal(0)) * 100 if recorded is not None else None
        ),
        quoted_total_value=display(total) if comparable else None,
        currency=next(iter(currencies)) if comparable else None,
        comparable=comparable,
        warnings=warnings,
    )


class PortfolioService:
    def __init__(self, path: Path) -> None:
        self.path = path

    def portfolios(self) -> list[dict[str, Any]]:
        return records(self.path, "SELECT * FROM portfolios ORDER BY portfolio_name")

    def holdings(self, portfolio_id: int) -> list[Holding]:
        resolve_portfolio(self.path, str(portfolio_id))
        return [
            Holding.model_validate(r)
            for r in records(
                self.path,
                """SELECT h.holding_id,
          s.symbol,s.company_name,s.asset_type,sec.sector_name AS sector,s.currency,h.quantity,
          s.current_price,h.current_weight,h.cost_basis FROM holdings h JOIN securities s
          ON s.security_id=h.security_id LEFT JOIN sectors sec ON sec.sector_id=s.sector_id
          WHERE h.portfolio_id=? ORDER BY h.holding_id""",
                (portfolio_id,),
            )
        ]

    def snapshot(self, portfolio_id: int) -> Snapshot:
        portfolios = [p for p in self.portfolios() if p["portfolio_id"] == portfolio_id]
        if not portfolios:
            raise PortfolioError("Portfolio not found.")
        holdings = self.holdings(portfolio_id)
        reconciliation = reconcile(holdings)
        warnings = list(reconciliation.warnings)
        if any(h.asset_type == "Stock" and not h.sector for h in holdings):
            warnings.append(
                Notice(
                    kind="invalid",
                    code="classification",
                    message="A stock has no sector classification; "
                    "sector analytics are incomplete.",
                )
            )
        try:
            exposure = calculate_exposure(self.path, str(portfolio_id))
        except PortfolioError as exc:
            exposure = None
            warnings.append(Notice(kind="incomplete", code="equity_denominator", message=str(exc)))
        performance = records(
            self.path,
            "SELECT * FROM portfolio_performance WHERE portfolio_id=? ORDER BY performance_date",
            (portfolio_id,),
        )
        risk = records(
            self.path,
            "SELECT * FROM risk_metrics WHERE portfolio_id=? ORDER BY calculation_date DESC",
            (portfolio_id,),
        )
        prices = records(
            self.path,
            """SELECT s.symbol,p.price_date,p.close_price,s.currency
            FROM historical_prices p JOIN securities s ON s.security_id=p.security_id
            WHERE EXISTS(SELECT 1 FROM holdings h
            WHERE h.security_id=s.security_id AND h.portfolio_id=?)
            ORDER BY p.price_date,s.symbol LIMIT 1000""",
            (portfolio_id,),
        )
        for code, values in [
            ("performance", performance),
            ("risk", risk),
            ("historical_prices", prices),
        ]:
            if not values:
                warnings.append(
                    Notice(
                        kind="incomplete",
                        code=code,
                        message=f"No recorded {code.replace('_', ' ')} observations; "
                        "not reported as zero.",
                    )
                )
        composition: dict[str, Decimal] = defaultdict(Decimal)
        for h in holdings:
            weight = number(h.current_weight)
            if weight is not None and 0 <= weight <= 1:
                composition[h.asset_type] += weight * 100
        return Snapshot(
            portfolio=portfolios[0],
            holdings=holdings,
            exposure=exposure,
            reconciliation=reconciliation,
            performance=performance,
            risk=risk,
            prices=prices,
            composition_percent={k: str(v) for k, v in composition.items()},
            warnings=warnings,
        )

    def overview(self) -> dict[str, Any]:
        portfolios = self.portfolios()
        snapshots = [self.snapshot(p["portfolio_id"]) for p in portfolios]
        return {
            "portfolio_count": len(portfolios),
            "active_count": sum(p["status"] == "Active" for p in portfolios),
            "reported_aum_sum": None,
            "aum_basis": "Aggregate AUM unavailable: portfolio AUM currencies and valuation "
            "dates are unspecified. Individual recorded AUM values remain available.",
            "holding_count": sum(len(s.holdings) for s in snapshots),
            "portfolios": portfolios,
            "composition": [
                {"name": s.portfolio["portfolio_name"], **s.composition_percent} for s in snapshots
            ],
            "quality": [
                {
                    "portfolio_name": s.portfolio["portfolio_name"],
                    "notices": [n.model_dump() for n in s.warnings],
                }
                for s in snapshots
            ],
        }
