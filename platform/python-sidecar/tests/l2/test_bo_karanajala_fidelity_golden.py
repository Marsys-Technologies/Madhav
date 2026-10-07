"""Golden-value narration fidelity test for bo_karanajala.citation_human (the dispositor edge sentence).

Rule stated by hand: a graha in a sign is disposed by that sign's lord, and the edge says so as 'Dispositor: <graha> (sign <n>) -> lord <lord>'. Moon in Taurus (sign 2) is disposed by
Venus (the lord of Taurus); Mars in Scorpio (sign 8) is disposed by Mars itself, a self-ruling graha, so no edge is emitted; Saturn in Aries (sign 1) is disposed by Mars.
(The argala sentence, which prints '2th' for the second house, is deliberately not pinned here: see the findings file.)
"""
from __future__ import annotations

from pipeline.orchestrator.writers.bo_karanajala import _build_dispositor_edges


def test_dispositor_edge_citation_human_names_graha_sign_and_lord():
    node_map = {("graha", g): f"node-{g}" for g in ("Moon", "Venus", "Mars", "Saturn")}
    edges = _build_dispositor_edges(
        "chart-1", "lahiri_chitrapaksha", "build-1",
        {"Moon": 2, "Mars": 8, "Saturn": 1}, node_map, "2026-10-05T00:00:00+00:00", None,
    )
    by_from = {e["from_node_id"]: e for e in edges}
    assert sorted(by_from) == ["node-Moon", "node-Saturn"]
    assert by_from["node-Moon"]["citation_human"] == "Dispositor: Moon (sign 2) → lord Venus"
    assert by_from["node-Saturn"]["citation_human"] == "Dispositor: Saturn (sign 1) → lord Mars"
