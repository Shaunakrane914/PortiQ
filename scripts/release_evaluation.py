"""Run repeatability and the frozen extended suite against one paced live backend."""

from pathlib import Path

from portiq.agent import PortfolioAgent
from portiq.config import Settings
from portiq.evaluation import evaluate
from portiq.model import GeminiBackend


def main() -> int:
    settings = Settings.from_env().model_copy(update={"request_interval": 6.5})
    backend = GeminiBackend(settings)
    try:
        agent = PortfolioAgent(settings, backend)
        supplied = evaluate(
            agent,
            settings.source / "ground_truth_dataset.json",
            Path("reports/supplied-release.json"),
            trials=2,
        )
        extended = evaluate(
            agent,
            settings.source / "evaluation/extended.json",
            Path("reports/extended-regression.json"),
        )
        return (
            0
            if (supplied["passed"] == supplied["total"] and extended["passed"] == extended["total"])
            else 1
        )
    finally:
        backend.close()


if __name__ == "__main__":
    raise SystemExit(main())
