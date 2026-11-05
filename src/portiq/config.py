"""Environment configuration; secrets never participate in repr or reports."""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, SecretStr

from portiq.errors import ModelError


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    database: Path = Path("portfolio_database.db")
    source: Path = Path(".")
    model: str = Field(default="gemini-3-flash-preview", min_length=1, max_length=120)
    api_key: SecretStr = Field(default=SecretStr(""), exclude=True, repr=False)
    max_rows: int = Field(default=1000, ge=1, le=5000)
    query_seconds: float = Field(default=2.0, gt=0, le=10)
    max_tool_calls: int = Field(default=6, ge=1, le=12)
    sql_attempts: int = Field(default=3, ge=1, le=4)
    request_interval: float = Field(default=13.0, ge=0, le=60)

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv(override=False)
        return cls(
            database=Path(os.getenv("PORTIQ_DB", "portfolio_database.db")),
            source=Path(os.getenv("PORTIQ_SOURCE", ".")),
            model=os.getenv("GEMINI_MODEL", "gemini-3-flash-preview"),
            api_key=SecretStr(os.getenv("GEMINI_API_KEY", "")),
            request_interval=float(os.getenv("PORTIQ_REQUEST_INTERVAL", "13")),
        )

    def require_key(self) -> str:
        key = self.api_key.get_secret_value().strip()
        if not key:
            raise ModelError("Set GEMINI_API_KEY in your environment or local .env file.")
        return key
