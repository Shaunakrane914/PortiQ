"""Offline schema coverage/context audit. This does not measure generated-answer accuracy."""

import argparse
import hashlib
import json
import statistics
import tempfile
from pathlib import Path

import sqlglot
from google.genai import types
from sqlglot import exp

from portiq.agent import PortfolioAgent
from portiq.config import Settings
from portiq.database import initialize
from portiq.errors import ModelError
from portiq.schema_graph import SchemaGraph


class PromptCapture:
    """Stop at the provider boundary without invoking an SDK or generating an answer."""

    system: str = ""

    def generate(
        self, contents: list[types.Content], config: types.GenerateContentConfig
    ) -> types.GenerateContentResponse:
        self.system = str(config.system_instruction or "")
        raise ModelError("Offline prompt capture; no provider request.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Select a fresh output file; existing evidence is never replaced.")
    source = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="portiq-graph-audit-") as temporary:
        database = Path(temporary) / "portfolio.db"
        initialize(source, database)
        settings = Settings(source=source, database=database)
        graph = SchemaGraph(database)
        capture = PromptCapture()
        agents = {
            mode: PortfolioAgent(settings, capture, context_mode=mode)
            for mode in ("full", "basic", "graph")
        }
        rows = []
        for filename in ("ground_truth_dataset.json", "evaluation/extended.json"):
            for case in json.loads((source / filename).read_text())["questions"]:
                context = graph.retrieve(case["question"])
                references = case.get("references", [case.get("ground_truth", {})])
                required: set[str] = set()
                for reference in references:
                    if "sql_query" in reference:
                        required.update(
                            t.name
                            for t in sqlglot.parse_one(
                                reference["sql_query"], read="sqlite"
                            ).find_all(exp.Table)
                            if t.name in graph.ddl
                        )
                    elif "parameters" in reference:
                        required.update({"portfolios", "holdings", "securities", "sectors"})
                prompts = {}
                response = None
                for mode, agent in agents.items():
                    response = agent.answer(case["question"])
                    prompts[mode] = {
                        "characters": len(capture.system),
                        "sha256": hashlib.sha256(capture.system.encode()).hexdigest(),
                    }
                assert response is not None
                rows.append(
                    {
                        "suite": filename,
                        "id": case["id"],
                        "question": case["question"],
                        "selected_tables": response.context_tables,
                        "required_reference_tables": sorted(required),
                        "missing_tables": sorted(required - set(response.context_tables)),
                        "coverage_checked": bool(required),
                        "seed_reasons": context.seed_reasons,
                        "join_paths": context.join_paths,
                        "fallback": response.context_fallback,
                        "prompts": prompts,
                    }
                )
        summaries = {}
        for filename in ("ground_truth_dataset.json", "evaluation/extended.json"):
            selected = [r for r in rows if r["suite"] == filename]
            characters = {
                mode: statistics.mean(r["prompts"][mode]["characters"] for r in selected)
                for mode in agents
            }
            summaries[filename] = {
                "questions": len(selected),
                "reference_table_checks": sum(r["coverage_checked"] for r in selected),
                "complete_table_coverage": sum(
                    r["coverage_checked"] and not r["missing_tables"] for r in selected
                ),
                "fallbacks": sum(r["fallback"] is not None for r in selected),
                "mean_initial_system_characters": characters,
                "graph_vs_full_character_reduction_percent": 100
                * (1 - characters["graph"] / characters["full"]),
                "graph_vs_basic_character_reduction_percent": 100
                * (1 - characters["graph"] / characters["basic"]),
            }
        result = {
            "scope": "Offline audit only. Reference SQL is used only for table coverage after "
            "runtime retrieval. No answers generated; no SDK calls; no tokens or latency "
            "measured. Complete table coverage does not prove correct columns, SQL or answers. "
            "Known author-created splits are not unseen validation.",
            "graph_nodes": len(graph.nodes),
            "graph_edges": len(graph.edges),
            "summaries": summaries,
            "rows": rows,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summaries, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
