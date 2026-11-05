from pathlib import Path

import pytest

from portiq.errors import QueryError
from portiq.sql import execute


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM portfolios",
        "DROP TABLE holdings",
        "SELECT 1; DELETE FROM holdings",
        "PRAGMA writable_schema=1",
        "ATTACH DATABASE ':memory:' AS evil",
        "VACUUM",
        "SELECT load_extension('evil')",
        "SELECT readfile('/etc/passwd')",
        "SELECT * FROM sqlite_master",
        "SELECT * FROM pragma_table_info('holdings')",
        "WITH RECURSIVE x(n) AS (SELECT 1 UNION ALL SELECT n+1 FROM x) SELECT * FROM x",
        "SELECT randomblob(1000000000)",
        "SELECT zeroblob(1000000000)",
        "SELECT * FROM main.portfolios",
        "SELECT 1 INTO stolen",
        "",
        "nonsense",
        "WITH x AS (DELETE FROM holdings RETURNING *) SELECT * FROM x",
        "SELECT 1; -- comment\n SELECT 2",
        "SELECT writefile('x', 'y')",
    ],
)
def test_unsafe_queries_rejected(database: Path, sql: str) -> None:
    before = database.read_bytes()
    with pytest.raises(QueryError):
        execute(database, sql)
    assert database.read_bytes() == before


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT COUNT(*) FROM portfolios;",
        "-- valid comment\n SELECT portfolio_name FROM portfolios WHERE status='Active'",
        "WITH x AS (SELECT portfolio_id FROM portfolios) SELECT COUNT(*) FROM x",
        "SELECT 1 UNION ALL SELECT 2",
        "SELECT ROUND(AVG(current_price),2) FROM securities",
        "SELECT sector_id, SUM(current_price) FROM securities GROUP BY sector_id",
        "SELECT ROW_NUMBER() OVER (ORDER BY portfolio_id), portfolio_name FROM portfolios",
    ],
)
def test_valid_analytics(database: Path, sql: str) -> None:
    assert execute(database, sql).rows


def test_parameterization_and_truncation(database: Path) -> None:
    result = execute(database, "SELECT * FROM portfolios", max_rows=2)
    assert result.truncated and len(result.rows) == 2
    assert (
        execute(
            database, "SELECT portfolio_id FROM portfolios WHERE portfolio_name=?", ("' OR 1=1 --",)
        ).rows
        == []
    )


def test_timeout(database: Path) -> None:
    with pytest.raises(QueryError, match="interrupted"):
        execute(
            database,
            "SELECT SUM(a.quantity*b.quantity*c.quantity*d.quantity) "
            "FROM holdings a CROSS JOIN holdings b CROSS JOIN holdings c CROSS JOIN holdings d",
            seconds=0.001,
        )
