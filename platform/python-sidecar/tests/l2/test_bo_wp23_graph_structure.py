"""
WP-2.3 / LCA-9a-1 — CGM graph-structure completion (graha↔bhava + yoga nodes).

Proves, without a DB:
  1. graha↔bhava edges emit for lordship / occupancy / bhava_aspect.
  2. every graha↔bhava edge carries a RESOLVING L1 fact_id (B.3 / §N.5).
  3. yoga/dosha first-class nodes emit (node_type='yoga'/'dosha') from bo_bimba.
  4. yoga membership edges emit (config ↔ constituent graha/bhava) and cite a
     resolving L1 fact_id.
  5. L1 fetch parsers map fact rows → {graha, house, fact_id} correctly.

Full DATA verify (Mercury neighborhood ≤2 calls, 60 bhava nodes edged) is a
W3 concern; these are the writer-lane unit tests.
"""
from __future__ import annotations

import json
import uuid
from unittest.mock import MagicMock

import pytest

from pipeline.orchestrator.writers.bo_karanajala import (
    _build_bhava_edges,
    _build_yoga_membership_edges,
    _fetch_bhava_lordship_facts,
    _fetch_occupancy_facts,
    _fetch_graha_bhava_aspect_facts,
    _EDGE_TYPE_VALENCE,
    _EDGE_TYPE_BASIS,
)
from pipeline.orchestrator.writers.bo_bimba import (
    _build_nodes_for_aya,
    yoga_node_subject,
)

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
BUILD_ID = str(uuid.uuid4())
AYA      = "lahiri_chitrapaksha"
NOW      = "2026-07-13T00:00:00+00:00"


def _conn(rows: list[tuple]) -> MagicMock:
    c = MagicMock()
    c.execute.return_value.fetchall.return_value = rows
    return c


# ── L1 fetch parsers ──────────────────────────────────────────────────────────

class TestFetchParsers:

    def test_lordship_parses_lord_and_house(self) -> None:
        rows = [
            ("D1_H1",  "Mars_in_H7",     "fid-h1"),
            ("D1_H10", "Saturn_in_H7",   "fid-h10"),
            ("D1_H4",  "Moon_in_H11",    "fid-h4"),
        ]
        out = _fetch_bhava_lordship_facts(_conn(rows), CHART_ID, AYA)
        by_house = {f["house"]: f for f in out}
        assert by_house[1]["graha"] == "Mars"
        assert by_house[1]["fact_id"] == "fid-h1"
        assert by_house[10]["graha"] == "Saturn"
        assert by_house[4]["graha"] == "Moon"

    def test_occupancy_maps_abbreviated_codes(self) -> None:
        rows = [
            ("MAR",      7.0,  "fid-mar"),
            ("SAT",      1.0,  "fid-sat"),
            ("RAH_MEAN", 6.0,  "fid-rah"),
        ]
        out = _fetch_occupancy_facts(_conn(rows), CHART_ID, AYA)
        by_g = {f["graha"]: f for f in out}
        assert by_g["Mars"]["house"] == 7
        assert by_g["Saturn"]["house"] == 1
        assert by_g["Rahu"]["house"] == 6
        assert by_g["Rahu"]["fact_id"] == "fid-rah"

    def test_aspect_parses_house_from_key(self) -> None:
        rows = [
            ("JUP", "house_5", "fid-jup5"),
            ("MAR", "house_10", "fid-mar10"),
        ]
        out = _fetch_graha_bhava_aspect_facts(_conn(rows), CHART_ID, AYA)
        pairs = {(f["graha"], f["house"]): f["fact_id"] for f in out}
        assert pairs[("Jupiter", 5)] == "fid-jup5"
        assert pairs[("Mars", 10)] == "fid-mar10"


# ── graha↔bhava edges ─────────────────────────────────────────────────────────

def _node_map(grahas: dict[str, str], bhavas: dict[int, str],
              yogas: dict[tuple[str, str], str] | None = None
              ) -> dict[tuple[str, str], str]:
    nm: dict[tuple[str, str], str] = {}
    for g, nid in grahas.items():
        nm[("graha", g)] = nid
    for h, nid in bhavas.items():
        nm[("bhava", str(h))] = nid
    for k, nid in (yogas or {}).items():
        nm[k] = nid
    return nm


class TestBhavaEdges:

    def _facts(self):
        lordship = [{"graha": "Mars", "house": 1, "fact_id": "fid-lord-h1"}]
        occupancy = [{"graha": "Saturn", "house": 1, "fact_id": "fid-occ-sat"}]
        aspect = [{"graha": "Jupiter", "house": 5, "fact_id": "fid-asp-jup5"}]
        return lordship, occupancy, aspect

    def test_three_edge_types_emit(self) -> None:
        lordship, occupancy, aspect = self._facts()
        nm = _node_map(
            {"Mars": "n-mars", "Saturn": "n-sat", "Jupiter": "n-jup"},
            {1: "n-h1", 5: "n-h5"},
        )
        edges = _build_bhava_edges(CHART_ID, AYA, BUILD_ID,
                                   lordship, occupancy, aspect, nm, NOW)
        types = {e["edge_type"] for e in edges}
        assert types == {"lordship", "occupancy", "bhava_aspect"}

    def test_edges_go_graha_to_bhava(self) -> None:
        lordship, occupancy, aspect = self._facts()
        nm = _node_map(
            {"Mars": "n-mars", "Saturn": "n-sat", "Jupiter": "n-jup"},
            {1: "n-h1", 5: "n-h5"},
        )
        edges = _build_bhava_edges(CHART_ID, AYA, BUILD_ID,
                                   lordship, occupancy, aspect, nm, NOW)
        lord = next(e for e in edges if e["edge_type"] == "lordship")
        assert lord["from_node_id"] == "n-mars"      # graha
        assert lord["to_node_id"] == "n-h1"          # bhava
        assert lord["semantic_path_class"] == "graha_bhava"

    def test_every_bhava_edge_cites_resolving_fact_id(self) -> None:
        """B.3 / §N.5 — the derivation resolves to a chart_facts.fact_id."""
        lordship, occupancy, aspect = self._facts()
        nm = _node_map(
            {"Mars": "n-mars", "Saturn": "n-sat", "Jupiter": "n-jup"},
            {1: "n-h1", 5: "n-h5"},
        )
        edges = _build_bhava_edges(CHART_ID, AYA, BUILD_ID,
                                   lordship, occupancy, aspect, nm, NOW)
        assert edges, "expected edges"
        for e in edges:
            fids = e["constituent_fact_ids_array"]
            assert fids and all(fids), f"edge {e['edge_type']} missing fact_ids"
        by_type = {e["edge_type"]: e for e in edges}
        assert by_type["lordship"]["constituent_fact_ids_array"] == ["fid-lord-h1"]
        assert by_type["occupancy"]["constituent_fact_ids_array"] == ["fid-occ-sat"]
        assert by_type["bhava_aspect"]["constituent_fact_ids_array"] == ["fid-asp-jup5"]

    def test_temporal_hook_honest_empty_without_periods_map(self) -> None:
        """WP-2.3-temporal owns active_dasha_periods_jsonb. When _build_bhava_edges is
        called WITHOUT a dasha_periods_by_graha map (as here — the graph lane's own
        path), the temporal overlay is the honest-empty JSON array '[]', never NULL and
        never fabricated. The populated-array case is covered by test_bo_karanajala_temporal."""
        lordship, occupancy, aspect = self._facts()
        nm = _node_map({"Mars": "n-mars"}, {1: "n-h1"})
        edges = _build_bhava_edges(CHART_ID, AYA, BUILD_ID,
                                   lordship, [], [], nm, NOW)
        assert edges and all(e["active_dasha_periods_jsonb"] == "[]" for e in edges)

    def test_missing_node_skipped(self) -> None:
        lordship = [{"graha": "Mars", "house": 1, "fact_id": "fid"}]
        nm = _node_map({"Mars": "n-mars"}, {})   # no bhava node
        edges = _build_bhava_edges(CHART_ID, AYA, BUILD_ID,
                                   lordship, [], [], nm, NOW)
        assert edges == []

    def test_new_edge_types_have_valence_and_basis(self) -> None:
        for et in ("lordship", "occupancy", "bhava_aspect", "yoga_member"):
            assert et in _EDGE_TYPE_VALENCE
            assert et in _EDGE_TYPE_BASIS


# ── yoga first-class nodes (bo_bimba) ─────────────────────────────────────────

def _yoga_signal(cls: str, name: str, *, graha: str | None = None,
                 house: int | None = None, sal: float = 1.0) -> dict:
    cfg: dict = {"fact_value_text": name}
    if graha:
        cfg["graha"] = graha
    if house:
        cfg["house"] = house
    return {
        "signal_id": str(uuid.uuid4()),
        "signal_type_class": cls,
        "signal_tradition": "parashari",
        "configuration_jsonb": json.dumps(cfg),
        "domains_affected_array": ["health"],
        "computed_salience": sal,
        "verification_pass_status": "single_pass",
        "signal_type_id": f"{cls}_label:{cls}_name",
    }


class TestYogaNodes:

    def test_yoga_and_dosha_nodes_emitted(self) -> None:
        signals = [
            _yoga_signal("yoga", "Gaja Kesari Yoga", graha="Jupiter"),
            _yoga_signal("dosha", "Balarishta (Moon in Dusthana)", graha="Moon"),
        ]
        nodes = _build_nodes_for_aya(CHART_ID, AYA, BUILD_ID, signals, NOW, {})
        yoga_nodes = [n for n in nodes if n["node_type"] == "yoga"]
        dosha_nodes = [n for n in nodes if n["node_type"] == "dosha"]
        assert len(yoga_nodes) == 1
        assert yoga_nodes[0]["node_label_human"] == "Gaja Kesari Yoga"
        assert len(dosha_nodes) == 1
        assert dosha_nodes[0]["msr_signal_id"] is not None

    def test_duplicate_name_deduped_keeping_highest_salience(self) -> None:
        signals = [
            _yoga_signal("dosha", "Kala Amrita Dosha", sal=0.4),
            _yoga_signal("dosha", "Kala Amrita Dosha", sal=1.9),
        ]
        nodes = _build_nodes_for_aya(CHART_ID, AYA, BUILD_ID, signals, NOW, {})
        kad = [n for n in nodes if n["node_type"] == "dosha"]
        assert len(kad) == 1
        assert kad[0]["strength_score"] == pytest.approx(1.9)

    def test_subject_key_is_class_namespaced_slug(self) -> None:
        s = yoga_node_subject("yoga", {"fact_value_text": "Gaja Kesari Yoga"}, "x")
        assert s == "yoga:gaja_kesari_yoga"

    def test_baseline_node_counts_unchanged(self) -> None:
        """9 graha + 12 bhava + 13 domain (G13/PA-4) present alongside yoga nodes.

        Domain count updated 7→13 after G13/PA-4 (R17): bo_bimba now creates one
        CGM node per canonical domain from CANONICAL_DOMAINS (13 members) rather
        than the legacy 7-domain local list.  Graha (9) and bhava (12) unchanged.
        """
        from brahmagyan.domain_vocabulary import CANONICAL_DOMAINS as _CD
        signals = [_yoga_signal("yoga", "Some Yoga", graha="Sun")]
        nodes = _build_nodes_for_aya(CHART_ID, AYA, BUILD_ID, signals, NOW, {})
        assert len([n for n in nodes if n["node_type"] == "graha"]) == 9
        assert len([n for n in nodes if n["node_type"] == "bhava"]) == 12
        assert len([n for n in nodes if n["node_type"] == "domain"]) == len(_CD)


# ── yoga membership edges (bo_karanajala) ─────────────────────────────────────

class TestYogaMembershipEdges:

    def test_membership_edge_to_graha_cites_occupancy_fact(self) -> None:
        sig = _yoga_signal("yoga", "Gaja Kesari Yoga", graha="Jupiter")
        subject = yoga_node_subject("yoga", {"fact_value_text": "Gaja Kesari Yoga"}, "x")
        nm = _node_map({"Jupiter": "n-jup"}, {},
                       yogas={("yoga", subject): "n-yoga"})
        edges = _build_yoga_membership_edges(
            CHART_ID, AYA, BUILD_ID, [sig], nm,
            occupancy_by_graha={"Jupiter": "fid-occ-jup"},
            lord_fact_by_house={}, now=NOW,
        )
        assert len(edges) == 1
        e = edges[0]
        assert e["edge_type"] == "yoga_member"
        assert {e["from_node_id"], e["to_node_id"]} == {"n-yoga", "n-jup"}
        assert e["constituent_fact_ids_array"] == ["fid-occ-jup"]

    def test_membership_edge_to_bhava_cites_lord_fact(self) -> None:
        sig = _yoga_signal("dosha", "Some Dosha", house=4)
        subject = yoga_node_subject("dosha", {"fact_value_text": "Some Dosha"}, "x")
        nm = _node_map({}, {4: "n-h4"}, yogas={("dosha", subject): "n-dosha"})
        edges = _build_yoga_membership_edges(
            CHART_ID, AYA, BUILD_ID, [sig], nm,
            occupancy_by_graha={}, lord_fact_by_house={4: "fid-lord-h4"}, now=NOW,
        )
        assert len(edges) == 1
        assert edges[0]["constituent_fact_ids_array"] == ["fid-lord-h4"]
        assert edges[0]["to_node_id"] == "n-h4"

    def test_no_yoga_node_no_edge(self) -> None:
        sig = _yoga_signal("yoga", "Orphan Yoga", graha="Sun")
        nm = _node_map({"Sun": "n-sun"}, {})   # no yoga node in map
        edges = _build_yoga_membership_edges(
            CHART_ID, AYA, BUILD_ID, [sig], nm,
            occupancy_by_graha={"Sun": "fid"}, lord_fact_by_house={}, now=NOW,
        )
        assert edges == []

    def test_non_yoga_signals_ignored(self) -> None:
        sig = {
            "signal_type_class": "composite_state",
            "configuration_jsonb": json.dumps({"graha": "Sun"}),
            "signal_type_id": "x",
            "signal_id": str(uuid.uuid4()),
        }
        edges = _build_yoga_membership_edges(
            CHART_ID, AYA, BUILD_ID, [sig], _node_map({"Sun": "n"}, {}),
            occupancy_by_graha={}, lord_fact_by_house={}, now=NOW,
        )
        assert edges == []
