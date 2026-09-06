"""bo_karanajala: is_cross_subsystem must match its own documented contract.

The module docstring states: "is_cross_subsystem: True when from/to nodes span
different traditions." _build_arudha_special_lagna_nodes_and_edges() hardcoded
`is_cross_subsystem: False` for BOTH edge types it emits, even though
arudha_house edges are genuinely jaimini->parashari (subsystem_from/
subsystem_to disagree right beside the hardcoded False) while
special_lagna_house edges are parashari->parashari (subsystem_from ==
subsystem_to, so False was already correct there). Found live: 285 of 285
arudha_house edges in production disagreed with the module's own contract.

Fixed to `is_cross_subsystem: node_type == "arudha"` -- this test guards the
wiring, not the live-data resync (a separate, later rebuild).
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
BUILD_ID = "b1b1b1b1-1111-1111-1111-111111111111"
AYA      = "lahiri_chitrapaksha"
NOW      = "2026-06-29T00:00:00+00:00"


def _facts_fixture() -> dict:
    return {
        ("arudha", "ARUDHA_A1"): {"house": 5, "sign": "Leo", "sign_lord": "Sun", "fact_id": "f1"},
        ("special_lagna", "GHATI_LAGNA"): {"house": 3, "sign": "Gemini", "sign_lord": "Mercury", "fact_id": "f2"},
    }


def _run(node_map: dict) -> list[dict]:
    from pipeline.orchestrator.writers.bo_karanajala import _build_arudha_special_lagna_nodes_and_edges

    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value = MagicMock()
    with patch(
        "pipeline.orchestrator.writers.bo_karanajala._fetch_arudha_special_lagna_facts",
        return_value=_facts_fixture(),
    ):
        _inserted, edges = _build_arudha_special_lagna_nodes_and_edges(
            conn, CHART_ID, AYA, BUILD_ID, NOW, node_map, lookups=None,
        )
    return edges


def _edge_by_type(edges: list[dict], edge_type: str) -> dict:
    matches = [e for e in edges if e["edge_type"] == edge_type]
    assert len(matches) == 1, f"expected exactly one {edge_type} edge, got {len(matches)}"
    return matches[0]


def test_arudha_house_edge_is_flagged_cross_subsystem() -> None:
    """jaimini (arudha) -> parashari (bhava) is genuinely cross-tradition."""
    node_map = {("bhava", "5"): "bhava-node-5", ("bhava", "3"): "bhava-node-3"}
    edges = _run(node_map)
    edge = _edge_by_type(edges, "arudha_house")

    assert edge["subsystem_from"] == "jaimini"
    assert edge["subsystem_to"] == "parashari"
    assert edge["is_cross_subsystem"] is True, (
        "arudha_house spans jaimini->parashari and must be flagged cross-subsystem"
    )


def test_special_lagna_house_edge_is_not_flagged_cross_subsystem() -> None:
    """parashari (special lagna) -> parashari (bhava) is same-tradition."""
    node_map = {("bhava", "5"): "bhava-node-5", ("bhava", "3"): "bhava-node-3"}
    edges = _run(node_map)
    edge = _edge_by_type(edges, "special_lagna_house")

    assert edge["subsystem_from"] == "parashari"
    assert edge["subsystem_to"] == "parashari"
    assert edge["is_cross_subsystem"] is False, (
        "special_lagna_house is parashari->parashari and must stay same-subsystem"
    )


def test_is_cross_subsystem_always_agrees_with_subsystem_from_vs_to() -> None:
    """The general contract, not just these two specific edge types."""
    node_map = {("bhava", "5"): "bhava-node-5", ("bhava", "3"): "bhava-node-3"}
    edges = _run(node_map)
    for edge in edges:
        expected = edge["subsystem_from"] != edge["subsystem_to"]
        assert edge["is_cross_subsystem"] == expected, (
            f"{edge['edge_type']}: is_cross_subsystem={edge['is_cross_subsystem']} but "
            f"subsystem_from={edge['subsystem_from']!r} subsystem_to={edge['subsystem_to']!r}"
        )
