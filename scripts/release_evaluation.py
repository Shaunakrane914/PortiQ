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
    parser.add_argument(
        "--suites",
        nargs="+",
        choices=["semantic", "supplied", "extended"],
        default=["semantic", "supplied", "extended"],
    )
    args = parser.parse_args()
    settings = Settings.from_env().model_copy(update={"request_interval": 6.5})
    backend = GeminiBackend(settings)
    try:
        agent = PortfolioAgent(settings, backend)
        specifications = {
            "semantic": ("evaluation/semantic_regression.json", args.semantic_trials),
            "supplied": ("ground_truth_dataset.json", args.supplied_trials),
            "extended": ("evaluation/extended.json", 1),
        }
        reports = []
        for name in args.suites:
            filename, trials = specifications[name]
            reports.append(
                evaluate(
                    agent,
                    settings.source / filename,
                    args.output_dir / f"{name}.json",
                    trials=trials,
                )
            )
        return int(any(report["passed"] != report["total"] for report in reports))
    finally:
        backend.close()


if __name__ == "__main__":
    raise SystemExit(main())
