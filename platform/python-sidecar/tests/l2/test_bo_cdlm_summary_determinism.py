"""CDLM sibling outputs must not inherit the database's cell-fetch order."""
from __future__ import annotations

import json
from itertools import permutations

from pipeline.orchestrator.writers.bo_cdlm_summary import (
    _build_clusters,
    _build_rollups,
)


def _cell(cell_id: str, partner: str) -> dict:
    return {
        "cell_id": cell_id,
        "domain_row": "career",
        "domain_col": partner,
        "computed_linkage_strength": 1.0,
        "cross_domain_contradiction_flag": False,
        "domain_relationship_class": "positive_strong",
        "shared_signal_ids_array": [f"signal-{cell_id}"],
    }


def test_rollup_top_three_breaks_equal_strength_ties_by_domain() -> None:
    # Four equal partners straddle the top-three boundary. Fetch order must
    # never choose which equally strong domain is omitted.
    cells = [
        _cell("c4", "wealth"),
        _cell("c3", "travel"),
        _cell("c2", "residence"),
        _cell("c1", "health"),
    ]
    expected = [
        {"domain": "health", "strength": 1.0},
        {"domain": "residence", "strength": 1.0},
        {"domain": "travel", "strength": 1.0},
    ]
    for order in permutations(cells):
        rows = _build_rollups("chart-1", "lahiri", "build-1", list(order), "now")
        career = next(row for row in rows if row["domain"] == "career")
        assert json.loads(career["top_3_linked_domains_jsonb"]) == expected
        assert career["total_outbound_linkage"] == 4.0
        assert career["signal_count_for_domain"] == 4


def test_cluster_member_ids_have_canonical_order_without_losing_members() -> None:
    cells = [_cell("c3", "wealth"), _cell("c1", "health"), _cell("c2", "travel")]
    for order in permutations(cells):
        rows = _build_clusters("chart-1", "lahiri", "build-1", list(order), "now")
        assert len(rows) == 1
        cluster = rows[0]
        assert cluster["involved_cells_array"] == ["c1", "c2", "c3"]
        assert cluster["cluster_strength_total"] == 3.0
        assert cluster["involved_signals_array"] == ["signal-c1", "signal-c2", "signal-c3"]
        assert cluster["citation_human"] == "CDLM pattern cluster 'positive_strong' over 3 cells"
