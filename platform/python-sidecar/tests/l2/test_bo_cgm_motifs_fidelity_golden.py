"""Golden-value fidelity test for bo_cgm_motifs motif_name and citation_human (pure stellium detector), and for the sub-graph
subgraph_label / citation_human (pure connected-component builder)."""
from __future__ import annotations

from pipeline.orchestrator.writers.bo_cgm_motifs import _compute_sub_graphs, _detect_stellia


def test_stellium_motif_name_and_citation_human_golden() -> None:
    # Three grahas share house 7: a stellium of size 3 (the threshold), narrated with the house and the count.
    graha_nodes = [
        {"node_id": "n1", "node_subject": "sun", "node_label_human": "Sun",
         "position_in_chart_jsonb": {"house": 7}},
        {"node_id": "n2", "node_subject": "mercury", "node_label_human": "Mercury",
         "position_in_chart_jsonb": {"house": 7}},
        {"node_id": "n3", "node_subject": "venus", "node_label_human": "Venus",
         "position_in_chart_jsonb": {"house": 7}},
        {"node_id": "n4", "node_subject": "moon", "node_label_human": "Moon",
         "position_in_chart_jsonb": {"house": 2}},
    ]
    motifs = _detect_stellia(graha_nodes, {})
    assert len(motifs) == 1
    motif = motifs[0]
    built = {"motif_name": motif["motif_name"], "citation_human": motif["citation_human"]}
    assert built == {
        "motif_name": "Stellium in House 7: Sun, Mercury, Venus",
        "citation_human": "Stellium: 3 grahas in house 7, pooling their energies in a single bhava",
    }


def test_sub_graph_label_and_citation_human_golden() -> None:
    # Sun is joined to Moon and to Mars (two edges); Venus is isolated. The one component of 3 nodes has Sun as
    # its centroid (highest intra-component degree: 2), so the label names the node count and the centroid.
    nodes = [
        {"node_id": "n1", "node_subject": "sun", "node_label_human": "Sun"},
        {"node_id": "n2", "node_subject": "moon", "node_label_human": "Moon"},
        {"node_id": "n3", "node_subject": "mars", "node_label_human": "Mars"},
        {"node_id": "n4", "node_subject": "venus", "node_label_human": "Venus"},
    ]
    edges = [
        {"edge_id": "e1", "from_node_id": "n1", "to_node_id": "n2"},
        {"edge_id": "e2", "from_node_id": "n1", "to_node_id": "n3"},
    ]
    rows = _compute_sub_graphs("chart", "lahiri_chitrapaksha", "build", "2026-10-07T00:00:00+00:00", nodes, edges)
    assert len(rows) == 1
    row = rows[0]
    built = {"subgraph_label": row["subgraph_label"], "citation_human": row["citation_human"]}
    assert built == {
        "subgraph_label": "Component of 3 nodes centred on Sun",
        "citation_human": "Connected component: 3 CGM nodes joined through 2 edges into one structural neighbourhood",
    }
