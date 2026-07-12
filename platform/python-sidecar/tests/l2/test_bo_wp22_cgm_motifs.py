"""
WP-2.2-CGM / LCA-6 — CGM motif + sub-graph + topology layer fires on real edges.

Proves, without a DB, that the motif/topology layer produces motif_count > 0 from
GENUINE structural patterns once the WP-2.3 edge set (dispositor edges, yoga nodes,
yoga_member edges, graha positions) is present — closing the LCA-6 native-motif-zero.

DATA-level confirmation on a live native rebuild is a W3 concern (production is
read-only in the writer wave); these are the writer-lane unit tests over
representative real-shaped input.
"""
from __future__ import annotations

import json
import uuid
from typing import Any

import pytest

from pipeline.orchestrator.writers.bo_cgm_motifs import (
    BoCgmMotifsWriter,
    _detect_yoga_clusters,
    _detect_mutual_reception,
    _detect_stellia,
    _detect_parivartana_chains,
    _detect_mutual_aspects,
    _compute_sub_graphs,
    _compute_topology,
    _write_aya,
    _scc_count,
    _triangle_count,
    _undirected_adjacency,
    _connected_components,
)
from pipeline.orchestrator.writers import ContextSpec

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
BUILD_ID = str(uuid.uuid4())
AYA      = "lahiri_chitrapaksha"
NOW      = "2026-07-13T00:00:00+00:00"


def _node(node_type: str, subject: str, **kw) -> dict:
    d = {
        "node_id": str(uuid.uuid4()),
        "node_type": node_type,
        "node_subject": subject,
        "node_label_human": subject.capitalize(),
        "position_in_chart_jsonb": None,
        "strength_score": None,
    }
    d.update(kw)
    return d


def _edge(etype: str, frm: str, to: str, basis: str = "", strength: float = 1.0) -> dict:
    return {
        "edge_id": str(uuid.uuid4()),
        "from_node_id": frm,
        "to_node_id": to,
        "edge_type": etype,
        "relationship_basis": basis,
        "computed_strength": strength,
    }


def _edge_by_from(edges: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for e in edges:
        out.setdefault(str(e["from_node_id"]), []).append(e)
    return out


# ── yoga_cluster — the LCA-6 primary guarantor ────────────────────────────────

class TestYogaCluster:

    def test_yoga_cluster_fires_with_two_members(self) -> None:
        yoga = _node("yoga", "gajakesari")
        moon = _node("graha", "moon")
        jup  = _node("graha", "jupiter")
        edges = [
            _edge("yoga_member", yoga["node_id"], moon["node_id"]),
            _edge("yoga_member", yoga["node_id"], jup["node_id"]),
        ]
        node_by_id = {n["node_id"]: n for n in (yoga, moon, jup)}
        motifs = _detect_yoga_clusters([yoga], _edge_by_from(edges), node_by_id)
        assert len(motifs) == 1
        m = motifs[0]
        assert m["motif_class"] == "yoga_cluster"
        assert yoga["node_id"] in m["node_ids"]
        assert set(m["edge_ids"]) == {e["edge_id"] for e in edges}
        assert m["strength"] > 0

    def test_yoga_cluster_requires_min_two_members(self) -> None:
        yoga = _node("yoga", "single_config")
        mars = _node("graha", "mars")
        edges = [_edge("yoga_member", yoga["node_id"], mars["node_id"])]
        node_by_id = {n["node_id"]: n for n in (yoga, mars)}
        motifs = _detect_yoga_clusters([yoga], _edge_by_from(edges), node_by_id)
        assert motifs == []

    def test_yoga_cluster_dedupes_repeat_member_edges(self) -> None:
        yoga = _node("dosha", "kuja_dosha")
        mars = _node("graha", "mars")
        h7   = _node("bhava", "7")
        # mars edged twice (two signals same subject) + house once → 2 distinct members
        edges = [
            _edge("yoga_member", yoga["node_id"], mars["node_id"]),
            _edge("yoga_member", yoga["node_id"], mars["node_id"]),
            _edge("yoga_member", yoga["node_id"], h7["node_id"]),
        ]
        node_by_id = {n["node_id"]: n for n in (yoga, mars, h7)}
        motifs = _detect_yoga_clusters([yoga], _edge_by_from(edges), node_by_id)
        assert len(motifs) == 1
        assert len(set(motifs[0]["node_ids"])) == 3  # config + mars + h7


# ── mutual_reception / parivartana / stellium (now firing post-WP-2.3) ─────────

class TestDispositorMotifs:

    def test_mutual_reception_fires_on_dispositor_edges(self) -> None:
        merc = _node("graha", "mercury")
        jup  = _node("graha", "jupiter")
        edges = [
            _edge("dispositor", merc["node_id"], jup["node_id"], basis="dispositor"),
            _edge("dispositor", jup["node_id"], merc["node_id"], basis="dispositor"),
        ]
        motifs = _detect_mutual_reception([merc, jup], _edge_by_from(edges))
        assert len(motifs) == 1
        assert motifs[0]["motif_class"] == "mutual_reception"
        assert len(motifs[0]["edge_ids"]) == 2

    def test_parivartana_chain_length_3(self) -> None:
        a = _node("graha", "sun")
        b = _node("graha", "mars")
        c = _node("graha", "saturn")
        edges = [
            _edge("dispositor", a["node_id"], b["node_id"], basis="dispositor"),
            _edge("dispositor", b["node_id"], c["node_id"], basis="dispositor"),
            _edge("dispositor", c["node_id"], a["node_id"], basis="dispositor"),
        ]
        motifs = _detect_parivartana_chains([a, b, c], _edge_by_from(edges))
        assert len(motifs) >= 1
        assert any(m["motif_class"] == "parivartana_chain" for m in motifs)

    def test_stellium_three_in_house(self) -> None:
        nodes = [_node("graha", g, position_in_chart_jsonb={"house": 10})
                 for g in ("sun", "mercury", "saturn")]
        motifs = _detect_stellia(nodes, {})
        assert len(motifs) == 1
        assert motifs[0]["motif_class"] == "stellium"


# ── mutual_aspect pairs + triangles ───────────────────────────────────────────

class TestMutualAspect:

    def test_mutual_aspect_pair(self) -> None:
        mars = _node("graha", "mars")
        jup  = _node("graha", "jupiter")
        edges = [
            _edge("aspect", mars["node_id"], jup["node_id"]),
            _edge("aspect", jup["node_id"], mars["node_id"]),
        ]
        motifs = _detect_mutual_aspects([mars, jup], _edge_by_from(edges))
        classes = {m["motif_class"] for m in motifs}
        assert "mutual_aspect" in classes

    def test_mutual_aspect_triangle(self) -> None:
        a = _node("graha", "sun")
        b = _node("graha", "moon")
        c = _node("graha", "mars")
        edges = []
        for x, y in ((a, b), (b, c), (a, c)):
            edges.append(_edge("aspect", x["node_id"], y["node_id"]))
            edges.append(_edge("aspect", y["node_id"], x["node_id"]))
        motifs = _detect_mutual_aspects([a, b, c], _edge_by_from(edges))
        classes = {m["motif_class"] for m in motifs}
        assert "mutual_aspect_triangle" in classes
        tri = [m for m in motifs if m["motif_class"] == "mutual_aspect_triangle"][0]
        assert len(tri["node_ids"]) == 3
        assert len(tri["edge_ids"]) == 6

    def test_one_way_aspect_no_mutual(self) -> None:
        mars = _node("graha", "mars")
        jup  = _node("graha", "jupiter")
        edges = [_edge("aspect", mars["node_id"], jup["node_id"])]
        motifs = _detect_mutual_aspects([mars, jup], _edge_by_from(edges))
        assert motifs == []


# ── sub-graph + topology derivation ───────────────────────────────────────────

class TestTopology:

    def test_connected_components(self) -> None:
        a, b, c, d = "a", "b", "c", "d"
        edges = [
            {"from_node_id": a, "to_node_id": b, "edge_id": "e1"},
            {"from_node_id": b, "to_node_id": c, "edge_id": "e2"},
        ]
        adj, _ = _undirected_adjacency([a, b, c, d], edges)
        comps = _connected_components([a, b, c, d], adj)
        sizes = sorted(len(x) for x in comps)
        assert sizes == [1, 3]  # {a,b,c} and isolated {d}

    def test_triangle_count(self) -> None:
        a, b, c = "a", "b", "c"
        edges = [
            {"from_node_id": a, "to_node_id": b, "edge_id": "e1"},
            {"from_node_id": b, "to_node_id": c, "edge_id": "e2"},
            {"from_node_id": a, "to_node_id": c, "edge_id": "e3"},
        ]
        adj, _ = _undirected_adjacency([a, b, c], edges)
        assert _triangle_count([a, b, c], adj) == 1

    def test_scc_count_directed_cycle(self) -> None:
        a, b, c = "a", "b", "c"
        edges = [
            {"from_node_id": a, "to_node_id": b},
            {"from_node_id": b, "to_node_id": c},
            {"from_node_id": c, "to_node_id": a},
        ]
        # one 3-cycle → a single SCC
        assert _scc_count([a, b, c], edges) == 1

    def test_compute_sub_graphs_emits_components(self) -> None:
        n1 = _node("graha", "sun")
        n2 = _node("graha", "moon")
        n3 = _node("bhava", "1")
        nodes = [n1, n2, n3]
        edges = [
            _edge("occupancy", n1["node_id"], n3["node_id"]),
            _edge("occupancy", n2["node_id"], n3["node_id"]),
        ]
        rows = _compute_sub_graphs(CHART_ID, AYA, BUILD_ID, NOW, nodes, edges)
        assert len(rows) == 1
        assert len(rows[0]["node_ids_array"]) == 3
        assert rows[0]["subgraph_type"] == "connected_component"

    def test_compute_topology_summary(self) -> None:
        n1 = _node("graha", "sun")
        n2 = _node("graha", "moon")
        nodes = [n1, n2]
        edges = [_edge("aspect", n1["node_id"], n2["node_id"])]
        topo = _compute_topology(CHART_ID, AYA, BUILD_ID, NOW, nodes, edges, [])
        assert topo["total_nodes"] == 2
        assert topo["total_edges"] == 1
        assert topo["graph_fingerprint_hash"]


# ── full _write_aya integration over a native-shaped graph ────────────────────

class _FakeCursor:
    def __init__(self, store: dict):
        self._store = store
        self._last: list[dict] = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql: str, params: Any = None):
        s = sql.strip().upper()
        if s.startswith("SELECT"):
            if "BODHA_CGM_NODES" in s:
                self._last = self._store["nodes"]
            elif "BODHA_CGM_EDGES" in s:
                self._last = self._store["edges"]
            else:
                self._last = []
        elif s.startswith("INSERT"):
            if "BODHA_CGM_MOTIFS" in s:
                self._store["motif_inserts"].append(params)
            elif "BODHA_CGM_SUB_GRAPHS" in s:
                self._store["subgraph_inserts"].append(params)
            elif "BODHA_CGM_CHART_TOPOLOGY" in s:
                self._store["topology_inserts"].append(params)
        else:
            self._last = []

    def fetchall(self):
        return self._last

    @property
    def description(self):
        if not self._last:
            return []
        return [type("C", (), {"name": k})() for k in self._last[0].keys()]


class _FakeConn:
    def __init__(self, store: dict):
        self._store = store

    def cursor(self):
        return _FakeCursor(self._store)


def _native_shaped_graph() -> dict:
    """A representative post-WP-2.3 CGM graph: grahas w/ positions, a yoga node
    with ≥2 members, a mutual-reception dispositor pair, a 3-graha stellium."""
    sun  = _node("graha", "sun",     position_in_chart_jsonb={"house": 10, "sign": "capricorn"})
    moon = _node("graha", "moon",    position_in_chart_jsonb={"house": 10, "sign": "capricorn"})
    merc = _node("graha", "mercury", position_in_chart_jsonb={"house": 10, "sign": "capricorn"})
    jup  = _node("graha", "jupiter", position_in_chart_jsonb={"house": 4,  "sign": "cancer"})
    ven  = _node("graha", "venus",   position_in_chart_jsonb={"house": 11, "sign": "aquarius"})
    yoga = _node("yoga", "budhaditya")
    nodes = [sun, moon, merc, jup, ven, yoga]

    edges = [
        # yoga cluster: budhaditya = sun + mercury
        _edge("yoga_member", yoga["node_id"], sun["node_id"]),
        _edge("yoga_member", yoga["node_id"], merc["node_id"]),
        # mutual reception: mercury <-> jupiter
        _edge("dispositor", merc["node_id"], jup["node_id"], basis="dispositor"),
        _edge("dispositor", jup["node_id"], merc["node_id"], basis="dispositor"),
        # conjunction edges inside the H10 stellium
        _edge("conjunction", sun["node_id"], moon["node_id"]),
        _edge("conjunction", moon["node_id"], merc["node_id"]),
    ]
    return {
        "nodes": nodes,
        "edges": edges,
        "motif_inserts": [],
        "subgraph_inserts": [],
        "topology_inserts": [],
    }


class TestWriteAyaIntegration:

    def test_write_aya_produces_positive_motif_count(self) -> None:
        store = _native_shaped_graph()
        conn = _FakeConn(store)
        m, s, t = _write_aya(conn, CHART_ID, AYA, BUILD_ID, NOW)
        # LCA-6: aggregate motif_count MUST be > 0 from real patterns
        assert m > 0, "native-shaped graph produced ZERO motifs — LCA-6 regression"
        assert len(store["motif_inserts"]) == m
        classes = {row["motif_class"] for row in store["motif_inserts"]}
        # yoga_cluster is the guarantor; mutual_reception + stellium also fire here
        assert "yoga_cluster" in classes
        assert "mutual_reception" in classes
        assert "stellium" in classes
        # sub-graphs + topology also emitted
        assert s >= 1
        assert t == 1
        # every motif carries edge lineage (§N.5) where it rests on edges
        for row in store["motif_inserts"]:
            assert isinstance(row["involved_edge_ids_array"], list)

    def test_write_aya_empty_graph_is_zero(self) -> None:
        store = {"nodes": [], "edges": [], "motif_inserts": [],
                 "subgraph_inserts": [], "topology_inserts": []}
        conn = _FakeConn(store)
        m, s, t = _write_aya(conn, CHART_ID, AYA, BUILD_ID, NOW)
        assert (m, s, t) == (0, 0, 0)


class TestWriterContract:

    def test_registered(self) -> None:
        assert BoCgmMotifsWriter().asset_id == "bo_cgm_motifs"

    def test_dry_run_zero(self) -> None:
        ctx = ContextSpec(
            asset_id="bo_cgm_motifs", build_id=BUILD_ID,
            db_conn=_FakeConn({}), config={"chart_id": CHART_ID}, dry_run=True,
        )
        assert BoCgmMotifsWriter().run(ctx).rows_inserted == 0
