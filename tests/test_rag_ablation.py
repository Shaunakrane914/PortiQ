"""Guard against reporting circuit-blocked benchmark rows as completed model comparisons."""

import importlib.util
from pathlib import Path


def test_circuit_blocked_rows_cannot_complete_the_experiment(source: Path) -> None:
    spec = importlib.util.spec_from_file_location(
        "rag_ablation", source / "scripts/rag_ablation.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    completed = [{"provider_attempts": [{"error_kind": None}]}]
    blocked = {"provider_attempts": []}
    assert module.protocol_complete(completed, 1)
    assert not module.protocol_complete(completed, 2)
    assert not module.protocol_complete(completed + [blocked], 2)
