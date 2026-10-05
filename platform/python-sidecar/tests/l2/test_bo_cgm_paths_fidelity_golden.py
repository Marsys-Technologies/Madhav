"""Golden-value fidelity test for bo_cgm_paths.path_label_human (pure builder, no database)."""
from __future__ import annotations

from pipeline.orchestrator.writers.bo_cgm_paths import _build_dispositor_chains


def test_path_label_human_golden_two_hop_chain_to_self_ruling_graha() -> None:
    # Moon in Taurus is disposed by Venus; Venus in Gemini by Mercury; Mercury sits in Gemini,
    # a sign it rules, so the chain ends at a final dispositor after exactly two hops.
    nodes = [
        {"node_id": "n-moon", "node_subject": "moon", "node_label_human": "Moon",
         "position_in_chart_jsonb": {"sign": "taurus"}},
        {"node_id": "n-venus", "node_subject": "venus", "node_label_human": "Venus",
         "position_in_chart_jsonb": {"sign": "gemini"}},
        {"node_id": "n-merc", "node_subject": "mercury", "node_label_human": "Mercury",
         "position_in_chart_jsonb": {"sign": "gemini"}},
    ]
    edges = [
        {"edge_id": "e1", "from_node_id": "n-moon", "to_node_id": "n-venus", "edge_type": "dispositor",
         "relationship_basis": "dispositor", "computed_strength": 1.0},
        {"edge_id": "e2", "from_node_id": "n-venus", "to_node_id": "n-merc", "edge_type": "dispositor",
         "relationship_basis": "dispositor", "computed_strength": 1.0},
    ]
    by_from: dict = {}
    for e in edges:
        by_from.setdefault(e["from_node_id"], []).append(e)
    node_by_id = {n["node_id"]: n for n in nodes}

    chains = {c["from_node_id"]: c for c in _build_dispositor_chains(nodes, by_from, node_by_id)}
    path_label_human = chains["n-moon"]["label"]
    assert path_label_human == "Moon → Venus → Mercury (final dispositor)"
