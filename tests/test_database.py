import shutil
import sqlite3
from pathlib import Path

import pytest

from portiq.database import connect_readonly, initialize, schema_context
from portiq.errors import DataError

COUNTS = {
    "sectors": 10,
    "securities": 30,
    "benchmarks": 13,
    "portfolios": 13,
    "holdings": 95,
    "transactions": 24,
    "historical_prices": 330,
    "portfolio_performance": 44,
    "risk_metrics": 44,
}


def test_import_and_integrity(database: Path) -> None:
    with connect_readonly(database) as conn:
        assert list(conn.execute("PRAGMA foreign_key_check")) == []
        assert conn.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        for table, count in COUNTS.items():
            assert conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone() == (count,)
        assert conn.execute(
            "SELECT COUNT(*) FROM securities WHERE sector_id IS NULL"
        ).fetchone() == (5,)
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("DELETE FROM holdings")
    assert "FOREIGN KEY" in schema_context(database)


def test_missing_database_does_not_create(tmp_path: Path) -> None:
    path = tmp_path / "absent.db"
    with pytest.raises(DataError, match="init-db"), connect_readonly(path):
        pass
    assert not path.exists()


def test_corrupt_database_is_actionable(tmp_path: Path) -> None:
    path = tmp_path / "corrupt.db"
    path.write_bytes(b"not a SQLite database")
    with pytest.raises(DataError, match="rebuild"):
        schema_context(path)
    assert path.read_bytes() == b"not a SQLite database"


@pytest.mark.parametrize("fail_before_allocation", [True, False])
def test_open_failure_is_safe_and_closes_allocated_connection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fail_before_allocation: bool,
) -> None:
    path = tmp_path / "present.db"
    path.touch()
    closed = []

    class BrokenConnection:
        def execute(self, sql: str) -> None:
            raise sqlite3.OperationalError("Access denied")

        def close(self) -> None:
            closed.append(True)

    def broken_connect(*args: object, **kwargs: object) -> BrokenConnection:
        if fail_before_allocation:
            raise sqlite3.OperationalError("Access denied")
        return BrokenConnection()

    monkeypatch.setattr("portiq.database.sqlite3.connect", broken_connect)
    with pytest.raises(DataError, match="Cannot open"), connect_readonly(path):
        pass
    assert closed == ([] if fail_before_allocation else [True])


def test_rebuild_is_atomic(database: Path, source: Path, tmp_path: Path) -> None:
    original = database.read_bytes()
    with pytest.raises(DataError, match="already exists"):
        initialize(source, database)
    bad = tmp_path / "bad"
    shutil.copytree(source / "data", bad / "data")
    shutil.copy(source / "database_schema.sql", bad)
    (bad / "data" / "portfolios.csv").write_text("wrong,header\n1,2\n")
    with pytest.raises(DataError, match="Column mismatch"):
        initialize(bad, database, rebuild=True)
    assert database.read_bytes() == original
    assert initialize(source, database, rebuild=True)["rows"] == COUNTS


def test_destination_cannot_replace_source(source: Path) -> None:
    file = source / "data/holdings.csv"
    original = file.read_bytes()
    with pytest.raises(DataError, match="original assessment"):
        initialize(source, file, rebuild=True)
    assert file.read_bytes() == original


@pytest.mark.parametrize(
    "change", ["missing", "duplicate", "foreign", "date", "number", "nan", "blank_id"]
)
def test_bad_data_rejected(source: Path, tmp_path: Path, change: str) -> None:
    bad = tmp_path / "bad"
    shutil.copytree(source / "data", bad / "data")
    shutil.copy(source / "database_schema.sql", bad)
    file = bad / "data" / "holdings.csv"
    text = file.read_text()
    if change == "missing":
        file.unlink()
    elif change == "duplicate":
        file.write_text(text + text.splitlines()[1] + "\n")
    else:
        replacements = {
            "foreign": ("1,1,1,2500", "1,999,1,2500"),
            "date": ("2023-09-25", "2023-99-25"),
            "number": ("2500", "oops"),
            "nan": ("0.18", "NaN"),
            "blank_id": ("1,1,1,2500", ",1,1,2500"),
        }
        file.write_text(text.replace(*replacements[change], 1))
    with pytest.raises(DataError):
        initialize(bad, tmp_path / "bad.db")
    assert not (tmp_path / "bad.db").exists()
