"""Re-score historical ext-02 evidence without changing old reports or calling Gemini."""

import hashlib
import json

from portiq.agent import AgentResponse
from portiq.config import Settings
from portiq.evaluation import score_answer


def main() -> None:
    settings = Settings.from_env()
    cases = json.loads((settings.source / "evaluation/extended.json").read_text())["questions"]
    case = next(c for c in cases if c["id"] == "ext-02")
    records = []
    for filename in ("extended-final.json", "extended-regression.json"):
        file = settings.source / "reports" / filename
        report = json.loads(file.read_text(encoding="utf-8"))
        old = next(r for r in report["records"] if r["id"] == case["id"])
        scored = score_answer(
            settings,
            case,
            AgentResponse.model_validate(old["actual"]),
            narrative_rules=["portfolio_names"],
        )
        records.append(
            {
                "original_file": filename,
                "original_sha256": hashlib.sha256(file.read_bytes()).hexdigest(),
                "diagnostics": scored,
            }
        )
    path = settings.source / "reports/v0.1.1/historical-ext02.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "mode": "Offline re-score of historical traces; no new model calls.",
                "evaluator_version": 2,
                "records": records,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        "Historical ext-02: wrong results, false narrative and extra routing reported separately."
    )


if __name__ == "__main__":
    main()
