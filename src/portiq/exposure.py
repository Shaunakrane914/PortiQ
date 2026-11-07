"""Weight-based equity exposure; arithmetic is independent of the language model."""

import re
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from portiq.database import connect_readonly
from portiq.errors import DataError, PortfolioError


class ExposureInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    portfolio: str = Field(
        min_length=1,
        max_length=200,
        description=(
            "Portfolio name, name fragment or numeric ID as supplied in the user's request. "
            "Preserve the original reference; never replace an ambiguous fragment with a guessed "
            "full name or ID. The tool resolves unique partial names and rejects ambiguous ones."
        ),
    )


class ExposureResult(BaseModel):
    portfolio_id: int
    portfolio_name: str
    equity_weight: str
    sectors: dict[str, str]
    basis: str = "Stock current_weight / sum(Stock current_weight) * 100"
    rounding: str = "2 decimals, ROUND_HALF_UP; displayed totals can differ from 100 by rounding"


def normalize(text: str) -> str:
    return " ".join(re.findall(r"\w+", text.casefold()))


def resolve_portfolio(path: Path, reference: str) -> tuple[int, str]:
    reference = reference.strip()
    if not reference or len(reference) > 200:
        raise PortfolioError("Provide a portfolio name or numeric ID (at most 200 characters).")
    with connect_readonly(path) as conn:
        portfolios = list(conn.execute("SELECT portfolio_id, portfolio_name FROM portfolios"))
    if reference.isdigit():
        matches = [p for p in portfolios if p[0] == int(reference)]
    else:
        term = normalize(reference)
        matches = [p for p in portfolios if normalize(p[1]) == term]
        if not matches:
            # Whole tokens avoid LIKE wildcards and arbitrary fuzzy matches.
            matches = [p for p in portfolios if f" {term} " in f" {normalize(p[1])} "]
    if not matches:
        raise PortfolioError("Portfolio not found. Use an existing portfolio name or ID.")
    if len(matches) > 1:
        raise PortfolioError(
            "Ambiguous portfolio; choose one of: " + ", ".join(p[1] for p in matches)
        )
    return int(matches[0][0]), str(matches[0][1])


def calculate_exposure(path: Path, reference: str) -> ExposureResult:
    portfolio_id, name = resolve_portfolio(path, reference)
    with connect_readonly(path) as conn:
        rows = list(
            conn.execute(
                "SELECT h.current_weight, sec.sector_name FROM holdings h "
                "JOIN securities s ON h.security_id=s.security_id "
                "LEFT JOIN sectors sec ON s.sector_id=sec.sector_id "
                "WHERE h.portfolio_id=? AND s.asset_type='Stock'",
                (portfolio_id,),
            )
        )
    weights: dict[str, Decimal] = defaultdict(Decimal)
    for weight, sector in rows:
        try:
            value = Decimal(str(weight))
        except InvalidOperation as exc:
            raise DataError("Equity holding has a missing or invalid weight.") from exc
        if not value.is_finite() or not 0 <= value <= 1 or not sector:
            raise DataError("Equity holding has an invalid weight or missing sector.")
        weights[sector] += value
    total = sum(weights.values(), Decimal(0))
    if not rows or total == 0:
        raise PortfolioError("Portfolio has no positive equity weight; exposure is undefined.")
    sectors = {
        sector: str((weight / total * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        for sector, weight in sorted(weights.items(), key=lambda item: (-item[1], item[0]))
    }
    return ExposureResult(
        portfolio_id=portfolio_id, portfolio_name=name, equity_weight=str(total), sectors=sectors
    )
