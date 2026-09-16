"""DP-SD-015 regression: L2 Karanajala has no resolved temporal overlay.

The legacy column remains readable, but new edge generations write NULL and no
L2 source imports or calls a Kāla resolver. Exact L1 clock identities may be
referenced elsewhere only without temporal interpretation.
"""
from __future__ import annotations

import ast
import uuid
from pathlib import Path

from pipeline.orchestrator.writers.bo_karanajala import (
    KNOWN_GRAHAS,
    _build_dasha_periods_by_graha,
    _dasha_periods_for_graha,
    _graha_bhava_edge,
    _membership_edge,
)


CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
BUILD_ID = str(uuid.uuid4())
AYA = "lahiri_chitrapaksha"
NOW = "2026-07-13T00:00:00+00:00"


def test_legacy_temporal_helpers_never_resolve_periods():
    assert _dasha_periods_for_graha("Saturn", [object()], object()) == []
    assert _build_dasha_periods_by_graha([object()], object()) == {
        graha: None for graha in KNOWN_GRAHAS
    }


def test_graha_bhava_edge_preserves_fact_ids_but_writes_null_window():
    edge = _graha_bhava_edge(
        "occupancy", CHART_ID, AYA, BUILD_ID,
        "graha-node", "bhava-node", "Saturn", 7, ["fact-1"], NOW,
        [{"start": "2000-01-01", "end": "2019-01-01"}],
    )
    assert edge["active_dasha_periods_jsonb"] is None
    assert edge["constituent_fact_ids_array"] == ["fact-1"]
    assert edge["edge_type"] == "occupancy"


def test_membership_edge_writes_null_window_even_if_legacy_argument_supplied():
    edge = _membership_edge(
        CHART_ID, AYA, BUILD_ID, "yoga-node", "graha-node",
        "yoga", "gajakesari", "graha", "Jupiter", ["fact-9"], NOW,
        [{"start": "2019-01-01", "end": "2035-01-01"}],
    )
    assert edge["active_dasha_periods_jsonb"] is None
    assert edge["constituent_fact_ids_array"] == ["fact-9"]


def test_source_has_no_l3_import_or_activation_resolver_call():
    source_path = Path(__file__).parents[2] / "pipeline/orchestrator/writers/bo_karanajala.py"
    source = source_path.read_text()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert not (node.module or "").startswith("services.ka_")
    assert "resolve_activation_windows(" not in source
    assert "load_dasha_timeline(" not in source
