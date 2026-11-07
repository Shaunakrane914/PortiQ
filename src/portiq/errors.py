"""Safe errors for CLI and model-facing tool responses."""


class PortiqError(Exception):
    """Expected application failure with a user-safe message."""


class DataError(PortiqError):
    """Missing, inconsistent, or malformed input data."""


class QueryError(PortiqError):
    """Rejected, invalid, or resource-limited query."""


class ModelError(PortiqError):
    """Unavailable model or malformed model response."""

    def __init__(
        self,
        message: str,
        *,
        retryable: bool = False,
        kind: str = "provider_error",
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message)
        self.retryable = retryable
        self.kind = kind
        self.retry_after = retry_after


class PortfolioError(PortiqError):
    """Portfolio reference requires correction or clarification."""
