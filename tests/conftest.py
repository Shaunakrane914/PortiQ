from pathlib import Path

import pytest

from portiq.database import initialize


@pytest.fixture
def source() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def database(tmp_path: Path, source: Path) -> Path:
    path = tmp_path / "portfolio.db"
    initialize(source, path)
    return path
