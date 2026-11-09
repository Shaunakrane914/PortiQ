from portiq.agent import ToolTrace, render_tools
from portiq.faithfulness import verify_answer


def make_tool(
    columns: list[str], rows: list[list[object]], sql: str = "", question: str = ""
) -> ToolTrace:
    return ToolTrace(
        tool="sql_query",
        arguments={"sql": sql, "question": question},
        result={"columns": columns, "rows": rows, "truncated": False, "sql": sql},
        duration_ms=1.0,
    )


def test_render_count_scalar() -> None:
    trace = make_tool(["COUNT(*)"], [[13]], question="Count all portfolios")
    rendered = render_tools([trace], question="Count all portfolios")
    assert "Total portfolios: 13" in rendered or "13" in rendered
    expected = [{"columns": ["COUNT(*)"], "rows": [[13]], "tool": "sql_query"}]
    assert verify_answer(rendered, expected, [])["status"] == "passed"


def test_render_count_distinct() -> None:
    trace = make_tool(["COUNT(DISTINCT asset_type)"], [[2]], question="Count distinct asset types")
    rendered = render_tools([trace], question="Count distinct asset types")
    assert "2" in rendered
    expected = [{"columns": ["COUNT(DISTINCT asset_type)"], "rows": [[2]], "tool": "sql_query"}]
    assert verify_answer(rendered, expected, [])["status"] == "passed"


def test_render_sum() -> None:
    trace = make_tool(["SUM(total_aum)"], [[5000000.0]], question="Total AUM")
    rendered = render_tools([trace], question="Total AUM")
    assert "5,000,000" in rendered
    assert "$" not in rendered  # Never invent currency symbols
    expected = [{"columns": ["SUM(total_aum)"], "rows": [[5000000.0]], "tool": "sql_query"}]
    assert verify_answer(rendered, expected, [])["status"] == "passed"


def test_render_avg() -> None:
    trace = make_tool(["AVG(current_price)"], [[125.5]], question="Average price")
    rendered = render_tools([trace], question="Average price")
    assert "125.5" in rendered
    assert "$" not in rendered
    expected = [{"columns": ["AVG(current_price)"], "rows": [[125.5]], "tool": "sql_query"}]
    assert verify_answer(rendered, expected, [])["status"] == "passed"


def test_render_min_max() -> None:
    trace = make_tool(
        ["MIN(current_price)", "MAX(current_price)"],
        [[28.95, 3380.0]],
        question="Minimum and maximum current price",
    )
    rendered = render_tools([trace], question="Minimum and maximum current price")
    assert "28.95" in rendered and "3,380" in rendered
    assert "$" not in rendered
    expected = [
        {
            "columns": ["MIN(current_price)", "MAX(current_price)"],
            "rows": [[28.95, 3380.0]],
            "tool": "sql_query",
        }
    ]
    assert verify_answer(rendered, expected, [])["status"] == "passed"


def test_render_single_column_list() -> None:
    trace = make_tool(
        ["portfolio_name"],
        [["Balanced Portfolio"], ["Conservative Income Fund"], ["Growth Portfolio"]],
        question="List portfolios",
    )
    rendered = render_tools([trace], question="List portfolios")
    assert "3 matching portfolios:" in rendered
    assert "* Balanced Portfolio" in rendered
    expected = [
        {
            "columns": ["portfolio_name"],
            "rows": [["Balanced Portfolio"], ["Conservative Income Fund"], ["Growth Portfolio"]],
            "tool": "sql_query",
        }
    ]
    assert (
        verify_answer(
            rendered,
            expected,
            ["Balanced Portfolio", "Conservative Income Fund", "Growth Portfolio"],
        )["status"]
        == "passed"
    )


def test_render_zero_rows() -> None:
    trace = make_tool(["portfolio_name"], [], question="List matching portfolios")
    rendered = render_tools([trace], question="List matching portfolios")
    assert "No matching rows." in rendered
    expected = [{"columns": ["portfolio_name"], "rows": [], "tool": "sql_query"}]
    assert verify_answer(rendered, expected, ["Balanced Portfolio"])["status"] == "passed"


def test_render_null_values() -> None:
    trace = make_tool(["benchmark_id"], [[None]], question="Show benchmark ID")
    rendered = render_tools([trace], question="Show benchmark ID")
    assert "Not available" in rendered
    expected = [{"columns": ["benchmark_id"], "rows": [[None]], "tool": "sql_query"}]
    assert verify_answer(rendered, expected, [])["status"] == "passed"


def test_render_negative_values() -> None:
    trace = make_tool(["unrealized_pnl"], [[-1234.56]], question="Unrealized PnL")
    rendered = render_tools([trace], question="Unrealized PnL")
    assert "-1,234.56" in rendered
    assert "$" not in rendered
    expected = [{"columns": ["unrealized_pnl"], "rows": [[-1234.56]], "tool": "sql_query"}]
    assert verify_answer(rendered, expected, [])["status"] == "passed"


def test_render_exposure_equity_only_with_basis() -> None:
    trace = ToolTrace(
        tool="exposure_calculator",
        arguments={"portfolio": "Balanced Portfolio"},
        result={
            "portfolio_name": "Balanced Portfolio",
            "sectors": {"Technology": 61.11, "Healthcare": 22.22, "Financial Services": 16.67},
        },
        duration_ms=1.0,
    )
    rendered = render_tools([trace])
    assert "equity-only sector exposure" in rendered
    assert "| Sector | Exposure (%) |" in rendered
    assert "61.11%" in rendered and "22.22%" in rendered and "16.67%" in rendered
    assert "bonds excluded" in rendered
    expected = [
        {
            "portfolio_name": "Balanced Portfolio",
            "sectors": {"Technology": 61.11, "Healthcare": 22.22, "Financial Services": 16.67},
            "tool": "exposure_calculator",
        }
    ]
    assert verify_answer(rendered, expected, ["Balanced Portfolio"])["status"] == "passed"


def test_local_answer_paraphrased_queries(tmp_path) -> None:
    import sqlite3

    from portiq.config import Settings
    from portiq.service import local_answer

    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE portfolios (portfolio_id INTEGER PRIMARY KEY, "
        "portfolio_name TEXT, is_active INTEGER)"
    )
    conn.execute(
        "CREATE TABLE securities (security_id INTEGER PRIMARY KEY, symbol TEXT, "
        "company_name TEXT, asset_type TEXT, sector_id INTEGER)"
    )
    conn.execute("CREATE TABLE sectors (sector_id INTEGER PRIMARY KEY, sector_name TEXT)")
    conn.execute(
        "CREATE TABLE holdings (holding_id INTEGER PRIMARY KEY, portfolio_id INTEGER, "
        "security_id INTEGER, current_weight REAL, quantity REAL, cost_basis REAL)"
    )
    conn.execute("INSERT INTO portfolios VALUES (1, 'Balanced Portfolio', 1)")
    conn.execute("INSERT INTO portfolios VALUES (2, 'Growth Fund', 1)")
    conn.execute("INSERT INTO sectors VALUES (1, 'Technology')")
    conn.execute("INSERT INTO securities VALUES (1, 'AAPL', 'Apple Inc.', 'Stock', 1)")
    conn.execute("INSERT INTO holdings VALUES (1, 1, 1, 1.0, 100, 150.0)")
    conn.commit()
    conn.close()

    settings = Settings(database=db_path)

    # Count paraphrases
    for q in [
        "count all portfolios",
        "how many portfolios do we have",
        "how many portfolios are there",
        "total number of portfolios",
        "how many funds do we have",
        "count all funds",
    ]:
        res = local_answer(settings, q, None)
        assert res is not None, f"Failed on {q}"
        assert "Total portfolios: 2" in res.answer or "2" in res.answer

    # Exposure paraphrases
    for q in [
        "sector exposure for Balanced Portfolio",
        "what is Balanced Portfolio's equity-sector allocation",
        "Balanced Portfolio's sector breakdown",
        "show Balanced Portfolio's allocation",
    ]:
        res = local_answer(settings, q, None)
        assert res is not None, f"Failed on {q}"
        assert "Technology" in res.answer
        assert "| Sector | Exposure (%) |" in res.answer
