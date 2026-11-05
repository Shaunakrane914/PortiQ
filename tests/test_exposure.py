import csv
import sqlite3
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

import pytest

from portiq.errors import DataError, PortfolioError
from portiq.exposure import calculate_exposure, resolve_portfolio


def test_independent_csv_reconciliation_all_portfolios(database: Path, source: Path) -> None:
    def read(name: str) -> list[dict[str, str]]:
        with (source / "data" / f"{name}.csv").open(newline="") as f:
            return list(csv.DictReader(f))

    securities = {s["security_id"]: s for s in read("securities")}
    sectors = {s["sector_id"]: s["sector_name"] for s in read("sectors")}
    for portfolio in read("portfolios"):
        expected = defaultdict(Decimal)
        for holding in read("holdings"):
            security = securities[holding["security_id"]]
            if (
                holding["portfolio_id"] == portfolio["portfolio_id"]
                and security["asset_type"] == "Stock"
            ):
                expected[sectors[security["sector_id"]]] += Decimal(holding["current_weight"])
        if not expected:
            with pytest.raises(PortfolioError, match="undefined"):
                calculate_exposure(database, portfolio["portfolio_name"])
            continue
        total = sum(expected.values())
        result = calculate_exposure(database, portfolio["portfolio_name"])
        assert set(result.sectors) == set(expected)
        for sector, weight in expected.items():
            assert abs(Decimal(result.sectors[sector]) - weight * 100 / total) <= Decimal("0.005")


@pytest.mark.parametrize("reference", ["international equity", " INTERNATIONAL Equity Fund ", "7"])
def test_resolution(database: Path, reference: str) -> None:
    assert resolve_portfolio(database, reference) == (7, "International Equity Fund")


@pytest.mark.parametrize("reference", ["", "999", "unknown", "%", "' OR 1=1 --", "x" * 201])
def test_missing_portfolio(database: Path, reference: str) -> None:
    with pytest.raises(PortfolioError):
        calculate_exposure(database, reference)


def test_ambiguous(database: Path) -> None:
    with pytest.raises(PortfolioError, match="Ambiguous"):
        calculate_exposure(database, "equity")


@pytest.mark.parametrize("weight", [None, -0.1, 1.1, "bad", 0])
def test_invalid_or_zero_weights(database: Path, weight: object) -> None:
    with sqlite3.connect(database) as conn:
        conn.execute("UPDATE holdings SET current_weight=? WHERE portfolio_id=3", (weight,))
    with pytest.raises((DataError, PortfolioError)):
        calculate_exposure(database, "3")


def test_missing_sector(database: Path) -> None:
    with sqlite3.connect(database) as conn:
        conn.execute("UPDATE securities SET sector_id=NULL WHERE security_id=1")
    with pytest.raises(DataError, match="missing sector"):
        calculate_exposure(database, "3")


def test_empty_portfolio(database: Path) -> None:
    with sqlite3.connect(database) as conn:
        conn.execute("DELETE FROM holdings WHERE portfolio_id=3")
    with pytest.raises(PortfolioError, match="undefined"):
        calculate_exposure(database, "3")
