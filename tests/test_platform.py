import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from decimal import Decimal
from pathlib import Path

import pytest
from test_agent import FakeBackend, call

from portiq.agent import _financial as financial
from portiq.agent import render_tools
from portiq.analytics import Holding, PortfolioService, reconcile
from portiq.config import Settings
from portiq.errors import PortiqError
from portiq.quota import RequestBudget
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
    assert r.largest_discrepancies[0].holding_id == 2
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


def test_compact_model_schema_preserves_sql_structure_and_constraints(database: Path) -> None:
    import sqlglot

    from portiq.database import connect_readonly, schema_context

    with closing(sqlite3.connect(database)) as conn, conn:
        conn.execute(
            'CREATE TABLE "extra table" (id INTEGER PRIMARY KEY, name TEXT DEFAULT '
            "'Mixed Case' CHECK(length(name)>0), UNIQUE(name))"
        )
    with connect_readonly(database) as conn:
        original = [
            r[0]
            for r in conn.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        ]
    compact = schema_context(database, compact=True)
    assert len(compact) < len(schema_context(database))
    assert len(compact.splitlines()) == len(original)
    for full, short in zip(original, compact.splitlines(), strict=True):
        assert sqlglot.parse_one(full, read="sqlite") == sqlglot.parse_one(short, read="sqlite")


@pytest.mark.parametrize("value", ["0", "NULL", "-2", "13"])
def test_explicit_scalar_format_uses_gemini_sql_without_synthesis(
    database: Path, value: str
) -> None:
    from portiq.agent import PortfolioAgent

    backend = FakeBackend(
        [
            call(
                "sql_query",
                question="Value",
                sql=f"SELECT {value} AS value FROM portfolios LIMIT 1",
                explanation="Read one scalar",
            ),
        ]
    )
    answer = PortfolioAgent(Settings(database=database), backend).answer(
        "Read a recorded value. Return a single value."
    )
    assert answer.status == "answer" and answer.api_calls == 1
    assert answer.execution_source == "Gemini planned analysis"
    assert answer.rendering == "deterministic scalar rendering after Gemini SQL"
    assert ("Not available" if value == "NULL" else value) in answer.answer
    assert len(backend.requests) == 1 and len(answer.tools) == 1


@pytest.mark.parametrize(
    "question,sql",
    [
        ("Count all portfolios", "SELECT COUNT(*) FROM portfolios"),
        (
            "Count portfolios and show exposure. Return just the count.",
            "SELECT COUNT(*) FROM portfolios",
        ),
        ("Show names. Return a single value.", "SELECT portfolio_name FROM portfolios"),
        (
            "Show count and average. Return one value.",
            "SELECT COUNT(*),AVG(total_aum) FROM portfolios",
        ),
    ],
)
def test_non_scalar_or_compound_requests_keep_model_synthesis(
    database: Path,
    question: str,
    sql: str,
) -> None:
    from portiq.agent import PortfolioAgent

    backend = FakeBackend(
        [
            call("sql_query", question=question, sql=sql, explanation="Read requested data"),
            call("respond", status="answer", answer="Grounded model summary"),
        ]
    )
    answer = PortfolioAgent(Settings(database=database), backend).answer(question)
    assert answer.api_calls == 2 and answer.answer == "Grounded model summary"
    assert answer.rendering == "model synthesis with authoritative tool evidence"


def test_truncated_scalar_shaped_results_keep_synthesis(database: Path) -> None:
    from portiq.agent import PortfolioAgent

    backend = FakeBackend(
        [
            call(
                "sql_query",
                question="Names",
                sql="SELECT portfolio_name FROM portfolios",
                explanation="Read names",
            ),
            call("respond", status="answer", answer="The result is truncated."),
        ]
    )
    answer = PortfolioAgent(Settings(database=database, max_rows=1), backend).answer(
        "List names. Return one value."
    )
    assert answer.tools[0].result["truncated"] and answer.api_calls == 2


def test_parallel_analytical_calls_are_not_discarded_by_scalar_format(database: Path) -> None:
    from google.genai import types

    from portiq.agent import PortfolioAgent

    first = call(
        "sql_query",
        question="Portfolios",
        sql="SELECT COUNT(*) FROM portfolios",
        explanation="Count portfolios",
    )
    first.candidates[0].content.parts.append(
        types.Part(
            function_call=types.FunctionCall(
                name="sql_query",
                id="second",
                args={
                    "question": "Securities",
                    "sql": "SELECT COUNT(*) FROM securities",
                    "explanation": "Count securities",
                },
            )
        )
    )
    backend = FakeBackend([first, call("respond", status="answer", answer="Both results shown.")])
    answer = PortfolioAgent(Settings(database=database), backend).answer(
        "Read the summary. Return one value."
    )
    assert len(answer.tools) == 2 and answer.api_calls == 2
    assert len(backend.requests[-1][0][-1].parts) == 2


def test_atomic_budget_across_connections(tmp_path: Path) -> None:
    a = RequestBudget(10, tmp_path / "budget.db")
    b = RequestBudget(10, tmp_path / "budget.db")
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda i: (a if i % 2 else b).reserve(), range(60)))
    assert sum(results) == 10 and a.used() == b.used() == 10
    a.close()
    b.close()


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


def test_fragment_and_id_selection_propagates_correct_context(database: Path) -> None:
    s = AnalysisService(Settings(database=database))
    first, sid = s.ask("Show holdings for Tech Innovation", selected=4, conversation=True)
    assert first.context_portfolio == 3
    follow, _ = s.ask("What is its sector exposure?", session_id=sid, conversation=True)
    assert follow.tools[0].result["portfolio_name"] == "Tech Innovation Fund"
    changed, _ = s.ask("Calculate sector exposure for 4", session_id=sid, conversation=True)
    assert changed.context_portfolio == 4
    balanced, _ = s.ask("What is its sector exposure?", session_id=sid, conversation=True)
    assert balanced.tools[0].result["portfolio_name"] == "Balanced Portfolio"


def test_missing_stock_classification_is_reported(database: Path) -> None:
    with closing(sqlite3.connect(database)) as conn, conn:
        conn.execute("UPDATE securities SET sector_id=NULL WHERE asset_type='Stock'")
    snapshot = PortfolioService(database).snapshot(1)
    assert snapshot.exposure is None
    assert any(w.code == "classification" and w.kind == "invalid" for w in snapshot.warnings)


def test_clarification_is_available_to_a_metric_followup(database: Path) -> None:
    backend = FakeBackend(
        [
            call(
                "respond", status="clarification", answer="Largest by quantity or recorded weight?"
            ),
            call(
                "sql_query",
                question="Largest recorded holding",
                sql=(
                    "SELECT symbol FROM holdings h JOIN securities s "
                    "ON s.security_id=h.security_id WHERE portfolio_id=4 "
                    "ORDER BY current_weight DESC LIMIT 1"
                ),
                explanation="Rank recorded weights",
            ),
            call("respond", status="answer", answer="The result is shown in the tool table."),
        ]
    )
    service = AnalysisService(Settings(database=database), backend)
    first, sid = service.ask("Which is the largest?", selected=4, conversation=True, local=False)
    assert first.status == "clarification"
    second, _ = service.ask("By recorded weight", session_id=sid, conversation=True, local=False)
    assert second.status == "answer"
    context = backend.requests[1][0][0].parts[0].text
    assert "Balanced Portfolio" in context and "quantity or recorded weight" in context
