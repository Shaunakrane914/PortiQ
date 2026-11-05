import os
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import SecretStr

from portiq.cli import main
from portiq.config import Settings
from portiq.errors import ModelError


def test_configuration_secret_not_serialized() -> None:
    settings = Settings(api_key=SecretStr("my-test-secret"))
    assert "my-test-secret" not in repr(settings)
    assert "my-test-secret" not in settings.model_dump_json()
    with pytest.raises(ModelError, match="GEMINI_API_KEY"):
        Settings().require_key()


def test_cli_deterministic_commands(database: Path, capsys: pytest.CaptureFixture) -> None:
    assert main(["--db", str(database), "doctor"]) == 0
    assert '"integrity": "ok"' in capsys.readouterr().out
    assert main(["--db", str(database), "exposure", "3"]) == 0
    assert '"Technology": "100.00"' in capsys.readouterr().out
    assert main(["--db", str(database), "sql", "SELECT COUNT(*) FROM portfolios"]) == 0
    assert "13" in capsys.readouterr().out
    assert main(["--db", str(database), "sql", "DELETE FROM portfolios"]) == 1
    assert "Error:" in capsys.readouterr().err


def test_cli_missing_database(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    assert main(["--db", str(tmp_path / "missing.db"), "doctor"]) == 1
    assert "init-db" in capsys.readouterr().err


def test_module_entrypoint(source: Path) -> None:
    env = os.environ.copy()
    result = subprocess.run(
        [sys.executable, "-m", "portiq", "--help"],
        cwd=source,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0 and "evaluate" in result.stdout
