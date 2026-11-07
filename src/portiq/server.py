"""Optional container entry point. Fresh data initialization precedes the HTTP server."""

import os

from portiq.config import Settings
from portiq.database import initialize
from portiq.errors import PortiqError


def main() -> None:
    import uvicorn

    from portiq.api import create_app

    settings = Settings.from_env()
    host = os.getenv("PORTIQ_HOST", "127.0.0.1")
    if (
        host not in {"127.0.0.1", "localhost"}
        and settings.api_key.get_secret_value()
        and not os.getenv("PORTIQ_DEMO_TOKEN")
    ):
        raise PortiqError("Set PORTIQ_DEMO_TOKEN for networked Gemini access.")
    if not settings.database.exists():
        initialize(settings.source, settings.database)
    uvicorn.run(
        create_app(settings), host=host, port=int(os.getenv("PORT", "8000")), proxy_headers=False
    )


if __name__ == "__main__":
    main()
