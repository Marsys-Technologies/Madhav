"""Golden-value fidelity test for bo_cgm_motifs motif_name and citation_human (pure stellium detector)."""
from __future__ import annotations

from pipeline.orchestrator.writers.bo_cgm_motifs import _detect_stellia


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
