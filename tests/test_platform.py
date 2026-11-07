import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from decimal import Decimal
from pathlib import Path

import pytest
from google.genai import errors
from pydantic import ValidationError
from test_agent import FakeBackend, call

from portiq.analytics import Holding, PortfolioService, reconcile
from portiq.config import Settings
from portiq.errors import ModelError, PortiqError
from portiq.planning import OneCallAgent, Plan
from portiq.quota import RequestBudget, classify
from portiq.renderer import financial, render_tools
from portiq.service import AnalysisService, ExactCache, Sessions, local_answer


def holding(**changes: object) -> Holding:
    return Holding.model_validate(
        {
            "holding_id": 1,
            "symbol": "AAA",
            "company_name": "A",
            "asset_type": "Stock",
            "sector": "Technology",
            "currency": "USD",
            "quantity": 2,
            "current_price": 10,
            "current_weight": 0.5,
            "cost_basis": 15,
            **changes,
        }
    )


def test_reconciliation_independent_arithmetic_and_duplicates() -> None:
    r = reconcile(
        [holding(), holding(holding_id=2, quantity=6, asset_type="Bond", current_weight=0.3)]
    )
    assert r.comparable and r.quoted_total_value == "80.0000"
    assert r.rows[0].reconstructed_percent == "25.0000"
    assert r.rows[0].difference_pp == "-25.0000"
    assert r.rows[1].symbol == r.rows[0].symbol  # Rows retain holding identities.
    assert r.unrepresented_percent == "20.0000"
    assert {n.code for n in r.warnings} >= {"bond_quotes", "valuation_dates", "weight_total"}
    assert sum(Decimal(s["reconstructed_percent"]) for s in r.sectors) == 100


@pytest.mark.parametrize(
    "changes,code",
    [
        ({"currency": "INR"}, "currencies"),
        ({"currency": None}, "currencies"),
        ({"current_price": None}, "market_values"),
        ({"quantity": -1}, "market_values"),
        ({"current_weight": 2}, "weights"),
        ({"current_weight": None}, "weights"),
    ],
)
def test_unsafe_reconciliation_basis(changes: dict, code: str) -> None:
    r = reconcile([holding(), holding(holding_id=2, **changes)])
    assert code in {w.code for w in r.warnings}
    if code != "weights":
        assert not r.comparable and r.quoted_total_value is None
        assert all(row.reconstructed_percent is None for row in r.rows)
    else:
        assert r.recorded_total_percent is None and all(
            s["recorded_percent"] is None for s in r.sectors
        )


def test_empty_zero_and_overweight() -> None:
    assert not reconcile([]).comparable
    assert not reconcile([holding(quantity=0)]).comparable
    r = reconcile([holding(current_weight=0.6), holding(holding_id=2, current_weight=0.6)])
    assert r.overweight_percent == "20.0000" and r.unrepresented_percent == "0.0000"


def test_all_portfolio_snapshots_reconcile_csv_basis(database: Path, source: Path) -> None:
    import csv

    service = PortfolioService(database)
    securities = {
        r["security_id"]: r for r in csv.DictReader((source / "data/securities.csv").open())
    }
    rows = list(csv.DictReader((source / "data/holdings.csv").open()))
    for portfolio in service.portfolios():
        snapshot = service.snapshot(portfolio["portfolio_id"])
        owned = [r for r in rows if int(r["portfolio_id"]) == portfolio["portfolio_id"]]
        total = sum(
            (
                Decimal(r["quantity"]) * Decimal(securities[r["security_id"]]["current_price"])
                for r in owned
            ),
            Decimal(0),
        )
        if snapshot.reconciliation.comparable:
            assert abs(Decimal(snapshot.reconciliation.quoted_total_value) - total) < Decimal(
                ".0001"
            )
        assert len(snapshot.holdings) == len(owned)
    overview = service.overview()
    assert overview["portfolio_count"] == 13 and overview["reported_aum_sum"] is None
    with pytest.raises(PortiqError):
        service.snapshot(999)


def test_missing_history_is_not_zero(database: Path) -> None:
    with closing(sqlite3.connect(database)) as conn, conn:
        conn.execute("DELETE FROM portfolio_performance WHERE portfolio_id=1")
    s = PortfolioService(database).snapshot(1)
    assert s.performance == [] and "performance" in {n.code for n in s.warnings}


@pytest.mark.parametrize(
    "value,currency,percent,expected",
    [
        ("1234.567", "INR", False, "1,234.57 INR"),
        ("3.5", None, True, "3.50%"),
        ("0", None, False, "0.00 (currency unspecified)"),
        ("NaN", "USD", False, "Not available"),
    ],
)
def test_financial_format(value: str, currency: str | None, percent: bool, expected: str) -> None:
    assert financial(value, currency=currency, percent=percent) == expected


def test_renderer_preserves_nulls_duplicates_and_bounds(database: Path) -> None:
    r = local_answer(Settings(database=database), "Count all portfolios", None)
    assert r and r.api_calls == 0 and "13" in r.answer
    r.tools[0].result = {
        "columns": ["x", "x"],
        "rows": [[None, 0], [None, 0], [None, 0]],
        "truncated": False,
    }
    text = render_tools(r.tools, max_rows=2)
    assert text.count("Not available | 0") == 2 and "Showing" in text
    assert "USD" not in text


def test_one_call_hybrid_dependency(database: Path) -> None:
    backend = FakeBackend(
        [
            call(
                "execute_plan",
                status="answer",
                steps=[
                    {
                        "tool": "sql_query",
                        "sql": "SELECT portfolio_name FROM portfolios WHERE portfolio_id=3",
                    },
                    {"tool": "exposure_calculator", "from_step": 0},
                ],
            )
        ]
    )
    r = OneCallAgent(Settings(database=database), backend).answer(
        "Identify portfolio 3 and calculate exposure"
    )
    assert r.status == "answer" and r.api_calls == 1 and len(r.tools) == 2
    assert r.tools[1].result["sectors"] == {"Technology": "100.00"}
    assert "Tech Innovation Fund" in r.answer


@pytest.mark.parametrize(
    "steps",
    [
        [{"tool": "sql_query", "sql": "DROP TABLE holdings"}],
        [{"tool": "exposure_calculator", "from_step": 0}],
        [{"tool": "exposure_calculator", "portfolio": "3", "from_step": 0}],
        [{"tool": "unexpected"}],
    ],
)
def test_plan_validation(steps: list) -> None:
    with pytest.raises((ValidationError, PortiqError)):
        Plan.model_validate({"status": "answer", "steps": steps})


def test_invalid_plan_falls_back_and_accounts_request(database: Path) -> None:
    backend = FakeBackend(
        [
            call("execute_plan", status="answer", steps=[]),
            call(
                "sql_query",
                question="Count",
                sql="SELECT COUNT(*) FROM portfolios",
                explanation="count",
            ),
            call("respond", status="answer", answer="13 portfolios."),
        ]
    )
    r = OneCallAgent(Settings(database=database), backend).answer("Count portfolios")
    assert r.api_calls == 3 and "fallback" in r.strategy and r.status == "answer"


def test_one_call_provider_failure_no_unbounded_fallback(database: Path) -> None:
    b = FakeBackend([ModelError("Daily limit", kind="daily_quota")])
    r = OneCallAgent(Settings(database=database), b).answer("Count portfolios")
    assert r.status == "error" and r.api_calls == 1


def test_atomic_budget_across_connections(tmp_path: Path) -> None:
    a = RequestBudget(10, tmp_path / "budget.db")
    b = RequestBudget(10, tmp_path / "budget.db")
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda i: (a if i % 2 else b).reserve(), range(60)))
    assert sum(results) == 10 and a.used() == b.used() == 10
    a.close()
    b.close()


@pytest.mark.parametrize(
    "code,payload,kind,retry",
    [
        (429, {"quotaId": "RequestsPerDay"}, "daily_quota", False),
        (429, {"details": [{"retryDelay": "2.5s"}]}, "rate_limit", True),
        (429, {"details": [{"retryDelay": "120s"}]}, "rate_limit", False),
        (503, {}, "provider_transient", True),
        (504, {}, "provider_transient", True),
        (403, {}, "authentication", False),
        (404, {}, "unsupported_model", False),
    ],
)
def test_error_classification(code: int, payload: dict, kind: str, retry: bool) -> None:
    result = classify(errors.APIError(code, payload))
    assert result[:2] == (kind, retry)


def test_cache_context_rebuild_and_mutation(database: Path) -> None:
    s = AnalysisService(Settings(database=database))
    r, sid = s.ask("Count all portfolios")
    r.answer = "mutated"
    hit, _ = s.ask("Count all portfolios", session_id=sid)
    assert hit.cache == "hit" and hit.answer != "mutated" and hit.api_calls == 0
    other, _ = s.ask("Count all portfolios")
    assert other.cache == "miss"
    with closing(sqlite3.connect(database)) as conn, conn:
        conn.execute(
            "INSERT INTO portfolios(portfolio_id,portfolio_name) VALUES(99,'New Portfolio')"
        )
    newer, _ = s.ask("Count all portfolios", session_id=sid)
    assert newer.cache == "miss" and "14" in newer.answer
    fresh, _ = s.ask("Count all portfolios", session_id=sid, cached=False)
    assert fresh.cache == "disabled"


def test_conversation_selection_switch_and_isolation(database: Path) -> None:
    s = AnalysisService(Settings(database=database))
    first, sid = s.ask("Show holdings for Balanced Portfolio", conversation=True)
    exposure, _ = s.ask("Calculate sector exposure for its", session_id=sid, conversation=True)
    from portiq.exposure import resolve_portfolio

    assert (
        first.context_portfolio
        == exposure.context_portfolio
        == resolve_portfolio(database, "Balanced Portfolio")[0]
    )
    assert exposure.tools[0].result["portfolio_name"] == "Balanced Portfolio"
    switched, _ = s.ask(
        "Calculate sector exposure for Tech Innovation Fund", session_id=sid, conversation=True
    )
    assert switched.context_portfolio == 3
    unresolved, _ = s.ask("What about the second one?", conversation=True)
    assert unresolved.status == "clarification"
    for _ in range(12):
        s.ask("Count all portfolios", session_id=sid, conversation=True, cached=False)
    assert len(s.sessions.items[sid].history) == 8
    with pytest.raises(PortiqError):
        s.sessions.get("untrusted-session-id")


def test_local_registry_rejects_broad_ambiguous_and_altered_intents(database: Path) -> None:
    settings = Settings(database=database)
    for q in [
        "Count all high risk portfolios",
        "Count all low risk portfolios",
        "Calculate sector exposure for equity fund",
        "Predict portfolio returns",
    ]:
        assert local_answer(settings, q, None) is None


def test_cache_lru_ttl_and_failed_results(database: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    clock = [1.0]
    monkeypatch.setattr("portiq.service.time.monotonic", lambda: clock[0])
    cache = ExactCache(capacity=1, ttl=2)
    answer = local_answer(Settings(database=database), "Count all portfolios", None)
    assert answer
    cache.put("a", answer)
    cache.put("b", answer)
    assert cache.get("a") is None
    clock[0] = 4
    assert cache.get("b") is None
    answer.status = "error"
    cache.put("error", answer)
    assert cache.get("error") is None
    sessions = Sessions(capacity=1, ttl=2)
    sid, _ = sessions.get(None)
    clock[0] = 7
    with pytest.raises(PortiqError):
        sessions.get(sid)


def test_identical_data_rebuild_invalidates_cache(database: Path, source: Path) -> None:
    from portiq.database import initialize

    service = AnalysisService(Settings(database=database))
    _, sid = service.ask("Count all portfolios")
    initialize(source, database, rebuild=True)
    result, _ = service.ask("Count all portfolios", session_id=sid)
    assert result.cache == "miss" and "13" in result.answer


def test_data_quality_kinds_distinguish_absent_and_invalid() -> None:
    missing = reconcile([holding(current_price=None)])
    invalid = reconcile([holding(quantity=-1)])
    assert next(w for w in missing.warnings if w.code == "market_values").kind == "incomplete"
    assert next(w for w in invalid.warnings if w.code == "market_values").kind == "invalid"
