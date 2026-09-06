"""S7 (§N.8): bodha_cgm_edges.cross_system_consensus_count must be DERIVED from
present_in_traditions_array, never a bare literal that can drift from it.

Before this fix, `cross_system_consensus_count` was the independent literal `1`
at all 8 write sites in bo_karanajala.py, hardcoded beside (not derived from)
`present_in_traditions_array` — an unearned signal wearing a measured value's
clothes (worse than NULL, since it reads as computed). The fix ties both
fields to one local `_traditions` value per site, so the count can never
silently diverge from the array it claims to summarize.

This test does not assert the CURRENT VALUE is 1 (that would just re-encode
the old literal as a new one) — it asserts the INVARIANT: the stored count
always equals len(the stored traditions array), for every edge-builder that
can be unit-tested without a live DB connection.
"""
from __future__ import annotations

import uuid

from pipeline.orchestrator.writers.bo_karanajala import (
    _build_argala_edges,
    _build_dispositor_edges,
    _graha_bhava_edge,
    _membership_edge,
)

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
BUILD_ID = str(uuid.uuid4())
AYA      = "lahiri_chitrapaksha"
NOW      = "2026-09-05T00:00:00+00:00"


def _assert_consensus_matches_traditions(edges: list[dict]) -> None:
    assert edges, "fixture produced no edges to check"
    for e in edges:
        assert e["cross_system_consensus_count"] == len(e["present_in_traditions_array"]), (
            f"edge_type={e.get('edge_type')!r}: cross_system_consensus_count="
            f"{e['cross_system_consensus_count']!r} but present_in_traditions_array="
            f"{e['present_in_traditions_array']!r}"
        )


def test_dispositor_edges_consensus_count_matches_traditions():
    node_map = {("graha", "Sun"): "node-sun", ("graha", "Saturn"): "node-sat"}
    graha_signs = {"Sun": 10, "Saturn": 10}
    edges = _build_dispositor_edges(CHART_ID, AYA, BUILD_ID, graha_signs, node_map, NOW)
    _assert_consensus_matches_traditions(edges)


def test_argala_edges_consensus_count_matches_traditions():
    node_map = {("graha", "Sun"): "node-sun", ("graha", "Jupiter"): "node-jup"}
    graha_signs = {"Sun": 1, "Jupiter": 2}  # Jupiter 2nd from Sun → argala
    edges = _build_argala_edges(CHART_ID, AYA, BUILD_ID, graha_signs, node_map, NOW)
    _assert_consensus_matches_traditions(edges)


def test_graha_bhava_edge_consensus_count_matches_traditions():
    edge = _graha_bhava_edge(
        "occupancy", CHART_ID, AYA, BUILD_ID,
        "graha-node", "bhava-node", "Saturn", 7, ["fact-1"], NOW,
    )
    _assert_consensus_matches_traditions([edge])


def test_membership_edge_consensus_count_matches_traditions():
    edge = _membership_edge(
        CHART_ID, AYA, BUILD_ID, "yoga-node", "graha-node",
        "yoga", "gajakesari", "graha", "Jupiter", ["fact-9"], NOW,
    )
    _assert_consensus_matches_traditions([edge])
