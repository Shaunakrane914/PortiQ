"""Community Cloud entry point for the existing PortiQ Streamlit interface."""

import os
from pathlib import Path

from portiq.streamlit_app import main

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    os.environ.setdefault("PORTIQ_SOURCE", str(root))
    os.environ.setdefault("PORTIQ_DB", str(root / ".portiq" / "portfolio.db"))
    os.environ.setdefault("PORTIQ_QUOTA_DB", str(root / ".portiq" / "quota.sqlite"))
    main()
