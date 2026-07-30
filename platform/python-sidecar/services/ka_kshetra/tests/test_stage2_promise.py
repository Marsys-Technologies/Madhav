"""Tests for services.ka_kshetra.stage2_promise.

Offline tier: the graph model, Yen's K-shortest-loopless-paths, noisy-OR
combination, and conductance normalization are pure functions of an
in-memory graph — fully testable on small synthetic fixtures with zero DB
dependency. A separate "live" tier (skipped unless DATABASE_URL is set)
exercises the real bodha_cgm_nodes/edges + bodha_pratijna ingestion.
"""
from __future__ import annotations

import math
import os

import pytest

from services.ka_kshetra.contracts import PromisePrior, Route
from services.ka_kshetra.stage2_promise import (
    K_ROUTES,
    PromiseEdge,
    PromiseNode,
    _extract_primary_graha,
    _restrict_to_reachable,
    _stable_node_id,
    bhava_node_id,
    build_digraph,
    event_class_node_id,
    graha_node_id,
    k_shortest_routes,
    noisy_or_promise,
    normalize_conductance,
)


# ── Node/edge id helpers ───────────────────────────────────────────────────────

class TestNodeIds:
    def test_graha_node_id_uses_short_code(self):
        assert graha_node_id("Jupiter") == "graha:Ju"
        assert graha_node_id("Mars") == "graha:Ma"

    def test_bhava_node_id(self):
        assert bhava_node_id(10) == "bhava:10"

    def test_event_class_node_id(self):
        assert event_class_node_id("career_change") == "event_class:career_change"

    def test_stable_node_id_graha(self):
        assert _stable_node_id("graha", "Venus") == "graha:Ve"

    def test_stable_node_id_bhava_numeric(self):
        assert _stable_node_id("bhava", "7") == "bhava:7"

    def test_stable_node_id_other_kind(self):
        assert _stable_node_id("yoga", "gajakesari") == "yoga:gajakesari"


# ── conductance normalization ──────────────────────────────────────────────────

class TestNormalizeConductance:
    def test_midpoint(self):
        assert normalize_conductance(0.5, 0.0, 1.0) == pytest.approx(0.5)

    def test_clamped_to_unit_interval(self):
        assert normalize_conductance(-1.0, 0.0, 1.0) == pytest.approx(1e-6)
        assert normalize_conductance(2.0, 0.0, 1.0) == pytest.approx(1.0)

    def test_never_exactly_zero(self):
        # (0, 1] per §3.3 — a zero-strength edge still needs a valid cost.
        assert normalize_conductance(0.0, 0.0, 1.0) > 0.0

    def test_degenerate_scale_maps_to_one(self):
        assert normalize_conductance(5.0, 3.0, 3.0) == 1.0


# ── graph construction ─────────────────────────────────────────────────────────

class TestBuildDigraph:
    def test_edge_cost_is_negative_log_conductance(self):
        nodes = [PromiseNode("a", "graha", "A", "l2_signal"),
                 PromiseNode("b", "graha", "B", "l2_signal")]
        edges = [PromiseEdge("a", "b", "dispositor", 0.5, "l2_inherited")]
        g = build_digraph(nodes, edges)
        assert g["a"]["b"]["cost"] == pytest.approx(-math.log(0.5))

    def test_duplicate_edge_keeps_lowest_cost(self):
        nodes = [PromiseNode("a", "graha", "A", "l2_signal"),
                 PromiseNode("b", "graha", "B", "l2_signal")]
        edges = [
            PromiseEdge("a", "b", "dispositor", 0.3, "l2_inherited"),
            PromiseEdge("a", "b", "lordship", 0.9, "l2_inherited"),  # higher conductance, lower cost
        ]
        g = build_digraph(nodes, edges)
        assert g["a"]["b"]["conductance"] == pytest.approx(0.9)


class TestRestrictToReachable:
    def test_excludes_nodes_beyond_hop_limit(self):
        nodes = [PromiseNode(str(i), "graha", str(i), "l2_signal") for i in range(6)]
        edges = [PromiseEdge(str(i), str(i + 1), "dispositor", 0.8, "l2_inherited")
                 for i in range(5)]
        g = build_digraph(nodes, edges)
        sub = _restrict_to_reachable(g, "5", l_max_hops=2)
        assert "3" in sub  # 2 hops from sink
        assert "0" not in sub  # 5 hops from sink, beyond the limit

    def test_missing_sink_returns_empty_graph(self):
        g = build_digraph([], [])
        sub = _restrict_to_reachable(g, "nonexistent", l_max_hops=4)
        assert len(sub.nodes) == 0


# ── Yen's K-shortest-loopless-paths + route floor ─────────────────────────────

class TestKShortestRoutes:
    def _simple_graph(self):
        nodes = [
            PromiseNode(graha_node_id("Jupiter"), "graha", "Jupiter", "l2_signal"),
            PromiseNode(graha_node_id("Venus"), "graha", "Venus", "l2_signal"),
            PromiseNode("bhava:10", "bhava", "10th", "l2_signal"),
            PromiseNode(event_class_node_id("career_change"), "event_class", "career_change", "l2_signal"),
        ]
        edges = [
            PromiseEdge(graha_node_id("Jupiter"), "bhava:10", "lordship", 0.8, "l2_inherited"),
            PromiseEdge("bhava:10", event_class_node_id("career_change"), "class_signification", 0.7, "l2_inherited"),
            PromiseEdge(graha_node_id("Venus"), event_class_node_id("career_change"), "class_signification", 0.5, "l2_inherited"),
        ]
        return build_digraph(nodes, edges)

    def test_finds_both_routes_ranked_by_gain(self):
        g = self._simple_graph()
        routes, dropped = k_shortest_routes(
            g, [graha_node_id("Jupiter"), graha_node_id("Venus")],
            event_class_node_id("career_change"),
        )
        assert len(routes) == 2
        assert routes[0].is_primary is True
        assert routes[0].route_gain > routes[1].route_gain
        assert routes[0].route_rank == 1 and routes[1].route_rank == 2
        assert dropped == 0

    def test_route_gain_is_product_of_conductances(self):
        g = self._simple_graph()
        routes, _ = k_shortest_routes(g, [graha_node_id("Jupiter")], event_class_node_id("career_change"))
        assert routes[0].route_gain == pytest.approx(0.8 * 0.7)

    def test_no_seeds_gives_no_routes(self):
        g = self._simple_graph()
        routes, dropped = k_shortest_routes(g, [], event_class_node_id("career_change"))
        assert routes == []
        assert dropped == 0

    def test_seed_with_no_path_to_sink_is_skipped(self):
        g = self._simple_graph()
        routes, dropped = k_shortest_routes(g, ["graha:Sa"], event_class_node_id("career_change"))
        assert routes == []

    def test_route_below_floor_is_dropped_and_counted(self):
        nodes = [
            PromiseNode(graha_node_id("Saturn"), "graha", "Saturn", "l2_signal"),
            PromiseNode(event_class_node_id("x"), "event_class", "x", "l2_signal"),
        ]
        # conductance so low that p_r < ROUTE_FLOOR (0.02): p_r = c, so pick c < 0.02.
        edges = [PromiseEdge(graha_node_id("Saturn"), event_class_node_id("x"),
                              "class_signification", 0.001, "l2_inherited")]
        g = build_digraph(nodes, edges)
        routes, dropped = k_shortest_routes(g, [graha_node_id("Saturn")], event_class_node_id("x"))
        assert routes == []
        assert dropped == 1

    def test_deterministic_tie_break_on_equal_cost(self):
        # Two seeds with IDENTICAL conductance to the sink — tie-break by
        # ascending concatenated node-id string.
        nodes = [
            PromiseNode(graha_node_id("Jupiter"), "graha", "Jupiter", "l2_signal"),
            PromiseNode(graha_node_id("Venus"), "graha", "Venus", "l2_signal"),
            PromiseNode(event_class_node_id("x"), "event_class", "x", "l2_signal"),
        ]
        edges = [
            PromiseEdge(graha_node_id("Jupiter"), event_class_node_id("x"), "class_signification", 0.5, "l2_inherited"),
            PromiseEdge(graha_node_id("Venus"), event_class_node_id("x"), "class_signification", 0.5, "l2_inherited"),
        ]
        g = build_digraph(nodes, edges)
        routes, _ = k_shortest_routes(g, [graha_node_id("Jupiter"), graha_node_id("Venus")],
                                       event_class_node_id("x"))
        assert len(routes) == 2
        # 'graha:Ju' < 'graha:Ve' lexicographically -> Jupiter's route ranks first.
        assert routes[0].path_node_ids[0] == graha_node_id("Jupiter")

    def test_caps_at_k_routes(self):
        # Build K_ROUTES+3 disjoint single-hop routes into the same sink;
        # only K_ROUTES should be returned.
        n_extra = K_ROUTES + 3
        nodes = [PromiseNode(f"graha:seed{i}", "graha", f"seed{i}", "l2_signal") for i in range(n_extra)]
        nodes.append(PromiseNode(event_class_node_id("x"), "event_class", "x", "l2_signal"))
        edges = [PromiseEdge(f"graha:seed{i}", event_class_node_id("x"), "class_signification",
                              0.5 + i * 0.001, "l2_inherited") for i in range(n_extra)]
        g = build_digraph(nodes, edges)
        routes, _ = k_shortest_routes(g, [f"graha:seed{i}" for i in range(n_extra)],
                                       event_class_node_id("x"))
        assert len(routes) == K_ROUTES


# ── noisy-OR ───────────────────────────────────────────────────────────────────

class TestNoisyOrPromise:
    def test_single_route(self):
        routes = [Route("x", 1, ("a", "b"), (), 0.6, True)]
        assert noisy_or_promise(routes) == pytest.approx(0.6)

    def test_multiple_routes_saturate_but_never_exceed_one(self):
        routes = [
            Route("x", 1, ("a",), (), 0.9, True),
            Route("x", 2, ("b",), (), 0.9, False),
            Route("x", 3, ("c",), (), 0.9, False),
        ]
        p = noisy_or_promise(routes)
        assert p < 1.0
        expected = 1 - (0.1 ** 3)
        assert p == pytest.approx(expected)

    def test_no_routes_gives_zero(self):
        assert noisy_or_promise([]) == 0.0

    def test_matches_hand_computed_example(self):
        routes = [Route("x", 1, ("a",), (), 0.56, True), Route("x", 2, ("b",), (), 0.5, False)]
        expected = 1 - (1 - 0.56) * (1 - 0.5)
        assert noisy_or_promise(routes) == pytest.approx(expected)


# ── configuration_jsonb primary-graha extraction ─────────────────────────────

class TestExtractPrimaryGraha:
    def test_graha_key(self):
        assert _extract_primary_graha({"graha": "jupiter"}) == "Jupiter"

    def test_primary_graha_key(self):
        assert _extract_primary_graha({"primary_graha": "venus"}) == "Venus"

    def test_lord_key(self):
        assert _extract_primary_graha({"lord": "Mars"}) == "Mars"

    def test_body_key_fallback(self):
        assert _extract_primary_graha({"body": "saturn"}) == "Saturn"

    def test_none_when_no_recognized_key(self):
        assert _extract_primary_graha({"unrelated": "x"}) is None

    def test_none_for_non_dict(self):
        assert _extract_primary_graha(None) is None
        assert _extract_primary_graha("not a dict") is None


# ── promise_prior end-to-end over an in-memory graph (fake conn) ─────────────

class _FakeCursorResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None


class _FakeConn:
    """Minimal conn.execute(sql, params).fetchall() double, keyed by which
    table the SQL mentions (good enough for load_promise_graph's four
    distinct queries, which each touch exactly one table)."""

    def __init__(self, cgm_nodes, cgm_edges, pratijna, signals):
        self.cgm_nodes = cgm_nodes
        self.cgm_edges = cgm_edges
        self.pratijna = pratijna
        self.signals = signals

    def execute(self, sql, params=None):
        if "bodha_cgm_nodes" in sql:
            return _FakeCursorResult(self.cgm_nodes)
        if "bodha_cgm_edges" in sql:
            return _FakeCursorResult(self.cgm_edges)
        if "bodha_pratijna" in sql:
            return _FakeCursorResult(self.pratijna)
        if "bodha_msr_signals" in sql:
            return _FakeCursorResult(self.signals)
        raise AssertionError(f"unexpected SQL: {sql}")


class TestPromisePriorEndToEnd:
    def test_full_pipeline_over_fake_l2_data(self):
        from services.ka_kshetra.stage2_promise import promise_prior

        cgm_nodes = [
            {"node_id": "n1", "node_type": "graha", "node_subject": "Jupiter",
             "node_label_human": "Jupiter", "strength_score": None,
             "constituent_fact_ids_array": None},
            {"node_id": "n2", "node_type": "bhava", "node_subject": "10",
             "node_label_human": "10th house", "strength_score": None,
             "constituent_fact_ids_array": None},
        ]
        cgm_edges = [
            {"edge_type": "lordship", "from_node_id": "n1", "to_node_id": "n2",
             "computed_strength": 0.8, "cancelled_flag": False,
             "constituent_fact_ids_array": ["fact_abc"]},
        ]
        pratijna = [
            {"event_class_id": "career_change", "status": "promised", "grade": 7.0,
             "supporting_signal_ids": ["sig1"]},
        ]
        signals = [
            {"signal_id": "sig1", "configuration_jsonb": {"graha": "jupiter"},
             "computed_salience": 0.6},
        ]
        conn = _FakeConn(cgm_nodes, cgm_edges, pratijna, signals)
        result = promise_prior("chart1", "career_change", conn)
        assert isinstance(result, PromisePrior)
        assert result.p > 0.0
        assert result.n_routes >= 1
        assert "fact_abc" in result.fact_ids or "sig1" in result.fact_ids

    def test_absent_event_class_returns_zero_promise(self):
        from services.ka_kshetra.stage2_promise import promise_prior

        conn = _FakeConn([], [], [], [])
        result = promise_prior("chart1", "nonexistent_class", conn)
        assert result.p == 0.0
        assert result.n_routes == 0


# ── Live tier: needs a real DB connection ─────────────────────────────────────

_HAS_DB = bool(os.environ.get("DATABASE_URL"))


@pytest.mark.skipif(not _HAS_DB, reason="DATABASE_URL not set; skipping live DB test")
class TestLiveDbIntegration:
    def test_load_promise_graph_against_real_l2_tables(self):
        import psycopg
        from services.ka_kshetra.stage2_promise import load_promise_graph

        conn = psycopg.connect(os.environ["DATABASE_URL"], row_factory=psycopg.rows.dict_row)
        try:
            chart_id = "482012f1-710e-4a25-994a-93821f5871aa"
            nodes, edges, seeds_by_class, fact_ids = load_promise_graph(conn, chart_id)
            assert isinstance(nodes, list)
            assert isinstance(edges, list)
        finally:
            conn.close()
