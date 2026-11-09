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
    model: str = Field(default="gemini-3.1-flash-lite", min_length=1, max_length=120)
    api_key: SecretStr = Field(default=SecretStr(""), exclude=True, repr=False)
    max_rows: int = Field(default=1000, ge=1, le=5000)
    query_seconds: float = Field(default=2.0, gt=0, le=10)
    max_tool_calls: int = Field(default=6, ge=1, le=12)
    sql_attempts: int = Field(default=3, ge=1, le=4)
    direct_results: bool = True
    force_synthesis: bool = False
    request_interval: float = Field(default=0.0, ge=0, le=60)
    rpm_limit: int = Field(default=12, ge=1, le=120)
    rpm_window: float = Field(default=60.0, ge=1.0, le=300.0)
    rpm_cooldown_threshold: int = Field(default=8, ge=1, le=120)
    rpm_cooldown_seconds: float = Field(default=1.5, ge=0.0, le=30.0)
    max_wait_seconds: float = Field(default=10.0, ge=0.0, le=60.0)
    daily_requests: int = Field(default=200, ge=1, le=10000)
    quota_path: Path | None = None
    fallback_models: tuple[str, ...] = Field(default=(), max_length=2)
    circuit_failures: int = Field(default=3, ge=1, le=10)
    circuit_seconds: float = Field(default=30, ge=1, le=300)
    max_concurrent_analyses: int = Field(default=4, ge=1, le=32)
    environment: str = Field(default="demo", pattern="^(demo|production)$")

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv(override=False)
        return cls(
            database=Path(os.getenv("PORTIQ_DB", "portfolio_database.db")),
            source=Path(os.getenv("PORTIQ_SOURCE", ".")),
            model=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
            api_key=SecretStr(os.getenv("GEMINI_API_KEY", "")),
            direct_results=os.getenv("PORTIQ_DIRECT_RESULTS", "1") == "1",
            request_interval=float(os.getenv("PORTIQ_REQUEST_INTERVAL", "0")),
            rpm_limit=int(os.getenv("PORTIQ_RPM_LIMIT", "12")),
            rpm_window=float(os.getenv("PORTIQ_RPM_WINDOW", "60")),
            rpm_cooldown_threshold=int(os.getenv("PORTIQ_RPM_COOLDOWN_THRESHOLD", "8")),
            rpm_cooldown_seconds=float(os.getenv("PORTIQ_RPM_COOLDOWN_SECONDS", "1.5")),
            max_wait_seconds=float(os.getenv("PORTIQ_MAX_WAIT_SECONDS", "10")),
            daily_requests=int(os.getenv("PORTIQ_DAILY_REQUESTS", "200")),
            quota_path=Path(os.environ["PORTIQ_QUOTA_DB"])
            if os.getenv("PORTIQ_QUOTA_DB")
            else None,
            fallback_models=tuple(
                m.strip() for m in os.getenv("PORTIQ_FALLBACK_MODELS", "").split(",") if m.strip()
            ),
            circuit_failures=int(os.getenv("PORTIQ_CIRCUIT_FAILURES", "3")),
            circuit_seconds=float(os.getenv("PORTIQ_CIRCUIT_SECONDS", "30")),
            max_concurrent_analyses=int(os.getenv("PORTIQ_MAX_CONCURRENT_ANALYSES", "4")),
            environment=os.getenv("PORTIQ_ENV", "demo"),
        )

    def require_key(self) -> str:
        key = self.api_key.get_secret_value().strip()
        if not key:
            raise ModelError("Set GEMINI_API_KEY in your environment or local .env file.")
        return key
