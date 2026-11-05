"""Safe errors for CLI and model-facing tool responses."""


class PortiqError(Exception):
    """Expected application failure with a user-safe message."""


class DataError(PortiqError):
    """Missing, inconsistent, or malformed input data."""


class QueryError(PortiqError):
    """Rejected, invalid, or resource-limited query."""


class ModelError(PortiqError):
    """Unavailable model or malformed model response."""


class PortfolioError(PortiqError):
    """Portfolio reference requires correction or clarification."""
