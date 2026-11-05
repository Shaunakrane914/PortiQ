"""Run repeatability and the frozen extended suite against one paced live backend."""

import argparse
from pathlib import Path

from portiq.agent import PortfolioAgent
from portiq.config import Settings
from portiq.evaluation import evaluate
from portiq.model import GeminiBackend


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fresh release regression, preserving prior reports"
    )
    parser.add_argument("--output-dir", type=Path, default=Path("reports/local/v0.1.1"))
    parser.add_argument("--supplied-trials", type=int, choices=range(1, 4), default=1)
    parser.add_argument("--semantic-trials", type=int, choices=range(1, 4), default=2)
    args = parser.parse_args()
    settings = Settings.from_env().model_copy(update={"request_interval": 6.5})
    backend = GeminiBackend(settings)
    try:
        agent = PortfolioAgent(settings, backend)
        semantic = evaluate(
            agent,
            settings.source / "evaluation/semantic_regression.json",
            args.output_dir / "semantic.json",
            trials=args.semantic_trials,
        )
        supplied = evaluate(
            agent,
            settings.source / "ground_truth_dataset.json",
            args.output_dir / "supplied.json",
            trials=args.supplied_trials,
        )
        extended = evaluate(
            agent,
            settings.source / "evaluation/extended.json",
            args.output_dir / "extended.json",
        )
        return (
            0
            if (
                semantic["passed"] == semantic["total"]
                and supplied["passed"] == supplied["total"]
                and extended["passed"] == extended["total"]
            )
            else 1
        )
    finally:
        backend.close()


if __name__ == "__main__":
    raise SystemExit(main())
