"""Verify current deterministic tools preserve recorded live evidence; no new AI score."""

import hashlib
import json
import subprocess
from pathlib import Path

from portiq.config import Settings
from portiq.evaluation import compare_rows
from portiq.exposure import calculate_exposure
from portiq.sql import execute


def main() -> int:
    settings = Settings.from_env()
    checked = 0
    failures = []
    hashes = {}
    for name in ("supplied-release", "extended-regression"):
        path = Path("reports") / f"{name}.json"
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        report = json.loads(path.read_text(encoding="utf-8"))
        for record in report["records"]:
            for tool in record.get("actual", {}).get("tools", []):
                stored = tool["result"]
                if stored is None:
                    continue
                checked += 1
                if tool["tool"] == "sql_query":
                    current = execute(settings.database, stored["sql"])
                    error = compare_rows(stored["rows"], current.rows, ordered=True)
                    if current.columns != stored["columns"]:
                        error = "Column projection changed."
                else:
                    current_exposure = calculate_exposure(
                        settings.database,
                        str(stored["portfolio_id"]),
                    ).model_dump()
                    error = None if current_exposure == stored else "Exposure evidence changed."
                if error:
                    failures.append({"suite": name, "id": record["id"], "error": error})
    result = {
        "mode": "offline deterministic replay; not a new Gemini accuracy measurement",
        "runtime_commit": subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip(),
        "report_sha256": hashes,
        "checked_tools": checked,
        "failures": failures,
    }
    Path("reports/replay.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"{checked} recorded tool results checked; {len(failures)} mismatches.")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
