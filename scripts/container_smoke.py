"""Verify a running credential-free container using actual HTTP responses."""

import argparse
import http.client
import json
import time
import urllib.error
import urllib.request
from pathlib import Path


def wait_for_health(url: str) -> None:
    for _ in range(30):
        try:
            with urllib.request.urlopen(url + "/api/health", timeout=2) as r:
                assert json.load(r)["status"] == "ok"
            break
        except (urllib.error.URLError, TimeoutError, http.client.HTTPException, ConnectionError):
            time.sleep(1)
    else:
        raise RuntimeError("Container did not become healthy.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--output", type=Path, default=Path("reports/local/container.json"))
    args = parser.parse_args()
    checks = []
    wait_for_health(args.url)
    for path in [
        "/",
        "/api/portfolios",
        "/api/portfolios/4/exposure",
        "/api/portfolios/4/reconciliation",
    ]:
        with urllib.request.urlopen(args.url + path, timeout=5) as r:
            payload = r.read()
            assert r.status == 200
            checks.append({"path": path, "status": r.status, "bytes": len(payload)})
            if path.endswith("/exposure"):
                assert json.loads(payload)["sectors"]["Technology"] == "61.11"
    body = json.dumps({"question": "What is the AAPL price?", "local": False}).encode()
    try:
        urllib.request.urlopen(
            urllib.request.Request(
                args.url + "/api/ask", data=body, headers={"Content-Type": "application/json"}
            )
        )
    except urllib.error.HTTPError as exc:
        assert exc.code == 503
        checks.append({"path": "/api/ask without credentials", "status": exc.code})
    else:
        raise AssertionError("Model request must fail cleanly without credentials.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {"mode": "actual container HTTP smoke; no Gemini calls", "checks": checks}, indent=2
        )
        + "\n",
        encoding="utf-8",
    )
    print("Container health, dashboard, local analytics and missing-credential behavior passed.")


if __name__ == "__main__":
    main()
