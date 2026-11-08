import json
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
import sqlglot
from sqlglot import exp
from test_agent import FakeBackend, call

from portiq.agent import PortfolioAgent
from portiq.config import Settings
from portiq.schema_graph import SchemaGraph


def test_graph_is_built_from_real_schema_and_preserves_bridge_tables(database: Path) -> None:
    graph = SchemaGraph(database)
    assert graph.nodes["column:holdings.portfolio_id"]["type"] == "INTEGER"
    assert (
        "column:holdings.portfolio_id",
        "column:portfolios.portfolio_id",
        "foreign_key",
    ) in graph.edges
    # Neither the bridge name nor a metric rule occurs in this query.
    result = graph.retrieve("Show portfolio currencies")
    assert {"portfolios", "holdings", "securities"} <= set(result.tables)
    assert result.join_paths


@pytest.mark.parametrize(
    "question,tables",
    [
        ("How many portfolios exist?", {"portfolios"}),
        ("Average current price of securities in each sector", {"securities", "sectors"}),
        (
            "Sector exposure for Balanced Portfolio",
            {"portfolios", "holdings", "securities", "sectors"},
        ),
        ("Show Sharpe ratios", {"portfolio_performance"}),
        ("Show beta and value at risk", {"risk_metrics"}),
    ],
)
def test_semantic_seeds_match_actual_column_locations(
    database: Path, question: str, tables: set[str]
) -> None:
    assert set(SchemaGraph(database).retrieve(question).tables) == tables


def test_uncertain_or_disconnected_context_falls_back(database: Path) -> None:
    graph = SchemaGraph(database)
    assert graph.retrieve("Explain unknown metric xyzzy").fallback
    assert graph.retrieve(
        "Compare portfolio benchmarks"
    ).fallback  # No supplied FK connects benchmarks.


def test_graph_reflects_schema_changes_and_never_invents_a_join(database: Path) -> None:
    with closing(sqlite3.connect(database)) as conn:
        conn.execute("CREATE TABLE extra_metadata (item_id INTEGER PRIMARY KEY)")
    graph = SchemaGraph(database)
    assert "table:extra_metadata" in graph.nodes
    result = graph.retrieve("Show extra metadata for portfolios")
    assert result.fallback and "extra_metadata" in result.tables


def test_graph_context_is_smaller_with_identical_tool_and_safety_configuration(
    database: Path,
) -> None:
    backends = [
        FakeBackend([call("respond", status="unsupported", answer="No forecast.")])
        for _ in range(2)
    ]
    settings = Settings(database=database)
    agents = [
        PortfolioAgent(settings, backends[0], context_mode="full"),
        PortfolioAgent(settings, backends[1], context_mode="graph"),
    ]
    results = [agent.answer("How many portfolios exist?") for agent in agents]
    full, graph = [backend.requests[0][1] for backend in backends]
    assert len(graph.system_instruction) < len(full.system_instruction)
    assert "CREATE TABLE holdings" not in graph.system_instruction
    assert "Never" in graph.system_instruction
    assert graph.model_dump(exclude={"system_instruction"}) == full.model_dump(
        exclude={"system_instruction"}
    )
    assert results[1].context_mode == "graph" and results[1].context_tables == ["portfolios"]
    assert results[1].metadata_sources == ["schema-graph:table:portfolios"]


def test_original_questions_have_complete_reference_table_coverage(
    database: Path, source: Path
) -> None:
    # Evaluation-only check: references are never supplied to runtime retrieval.
    graph = SchemaGraph(database)
    for case in json.loads((source / "ground_truth_dataset.json").read_text())["questions"]:
        reference = case["ground_truth"]
        expected = (
            (
                {
                    t.name
                    for t in sqlglot.parse_one(reference["sql_query"], read="sqlite").find_all(
                        exp.Table
                    )
                }
                & set(graph.ddl)
            )
            if "sql_query" in reference
            else {"portfolios", "holdings", "securities", "sectors"}
        )
        assert expected <= set(graph.retrieve(case["question"]).tables), case["id"]
