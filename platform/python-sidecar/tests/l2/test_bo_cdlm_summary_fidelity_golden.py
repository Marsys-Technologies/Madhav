"""Golden-value fidelity test for bo_cdlm_summary narration (citation_human).

Rule, read from the writer: cells are grouped by domain_relationship_class; each
distinct class present becomes one pattern cluster whose citation is
"CDLM pattern cluster '<class>' over <N> cells", N = number of member cells.
Three hand-built cells: two positive_strong, one inverse.
"""
from __future__ import annotations

from pipeline.orchestrator.writers.bo_cdlm_summary import _build_clusters


def _cell(cell_id: str, row: str, col: str, rel: str, strength: float) -> dict:
    return {
        "cell_id": cell_id,
        "domain_row": row,
        "domain_col": col,
        "computed_linkage_strength": strength,
        "domain_relationship_class": rel,
        "shared_signal_ids_array": [f"sig-{cell_id}"],
    }


def test_pattern_cluster_citation_human_states_hand_counted_cell_total() -> None:
    cells = [
        _cell("c1", "career", "wealth", "positive_strong", 2500.0),
        _cell("c2", "career", "health", "positive_strong", 2100.0),
        _cell("c3", "family", "wealth", "inverse", 300.0),
    ]
    clusters = _build_clusters(
        "chart-1", "lahiri", "build-1", cells, "2026-01-01T00:00:00+00:00"
    )
    by_marker = {c["pattern_marker_type"]: c for c in clusters}

    strong_row = by_marker["positive_strong_linkage_cluster"]
    citation_human = strong_row["citation_human"]
    assert citation_human == "CDLM pattern cluster 'positive_strong' over 2 cells"
    assert by_marker["inverse_linkage_cluster"]["involved_cells_array"] == ["c3"]
