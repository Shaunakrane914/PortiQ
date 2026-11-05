import os
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import SecretStr
from test_agent import FakeBackend, call

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


def test_cli_ask_structured_response(
    database: Path, capsys: pytest.CaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    import json

    backend = FakeBackend(
        [
            call("exposure_calculator", portfolio="Balanced Portfolio"),
            call("respond", status="answer", answer="Technology is 61.11% within equities."),
        ]
    )
    closed = []
    backend.close = lambda: closed.append(True)
    monkeypatch.setattr("portiq.cli.GeminiBackend", lambda settings: backend)
    assert main(["--db", str(database), "ask", "Balanced Portfolio sector exposure", "--json"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "answer"
    assert output["tools"][0]["result"]["equity_weight"] == "0.36"
    assert closed == [True]


def test_cli_chat_help_answer_exit(
    database: Path, capsys: pytest.CaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    backend = FakeBackend(
        [
            call("exposure_calculator", portfolio="3"),
            call("respond", status="answer", answer="Technology 100%."),
        ]
    )
    backend.close = lambda: None
    monkeypatch.setattr("portiq.cli.GeminiBackend", lambda settings: backend)
    inputs = iter(["", "help", "Tech Innovation Fund exposure", "exit"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))
    assert main(["--db", str(database), "chat", "--show-sql"]) == 0
    output = capsys.readouterr().out
    assert "Each question" in output and "100.00%" in output


@pytest.mark.parametrize("failure,code", [(EOFError, 0), (KeyboardInterrupt, 130)])
def test_cli_interruption(
    database: Path, monkeypatch: pytest.MonkeyPatch, failure: type[BaseException], code: int
) -> None:
    backend = FakeBackend([])
    backend.close = lambda: None
    monkeypatch.setattr("portiq.cli.GeminiBackend", lambda settings: backend)

    def interrupt(prompt: str) -> str:
        raise failure

    monkeypatch.setattr("builtins.input", interrupt)
    assert main(["--db", str(database), "chat"]) == code


def test_cli_model_failure_exit(
    database: Path, capsys: pytest.CaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    backend = FakeBackend([ModelError("Service unavailable")])
    backend.close = lambda: None
    monkeypatch.setattr("portiq.cli.GeminiBackend", lambda settings: backend)
    assert main(["--db", str(database), "ask", "Count portfolios"]) == 1
    assert "Service unavailable" in capsys.readouterr().out
