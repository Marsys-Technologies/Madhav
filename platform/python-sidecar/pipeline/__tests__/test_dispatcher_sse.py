"""
test_dispatcher_sse.py — Tests for the SSE graph event helpers added in B-S3.

Covers notify_first_row_write and notify_downstream_edges: dedup logic,
non-fatal failure handling, and correct delegation to build_events emitters.
"""
import unittest
from unittest.mock import MagicMock, patch, call

from pipeline.dispatcher import (
    notify_first_row_write,
    notify_downstream_edges,
    reset_sse_emit_state,
    reset_dep_graph,
)


def _make_conn():
    conn = MagicMock()
    cursor = MagicMock()
    cursor.__enter__ = MagicMock(return_value=cursor)
    cursor.__exit__ = MagicMock(return_value=False)
    conn.cursor.return_value = cursor
    cursor.fetchone.return_value = ("notif-id-1",)
    cursor.fetchall.return_value = []
    return conn, cursor


class TestNotifyFirstRowWrite(unittest.TestCase):

    def setUp(self):
        reset_sse_emit_state()

    def test_emits_node_added_on_first_call(self):
        """First call for (asset_id, ayanamsha_id) emits node_added."""
        conn, _ = _make_conn()
        with patch("pipeline.dispatcher.emit_node_added") as mock_emit:
            notify_first_row_write(conn, "b1", "ch1", "A3", "lahiri", 100, "synthesis")
            mock_emit.assert_called_once_with(conn, "b1", "ch1", "A3", "lahiri", 100, "synthesis")

    def test_dedup_same_pair_only_emits_once(self):
        """Duplicate calls for the same (asset_id, ayanamsha_id) only emit once."""
        conn, _ = _make_conn()
        with patch("pipeline.dispatcher.emit_node_added") as mock_emit:
            notify_first_row_write(conn, "b1", "ch1", "A3", "lahiri", 100, "synthesis")
            notify_first_row_write(conn, "b1", "ch1", "A3", "lahiri", 200, "synthesis")
            notify_first_row_write(conn, "b1", "ch1", "A3", "lahiri", 300, "synthesis")
            self.assertEqual(mock_emit.call_count, 1)

    def test_different_ayanamsha_emits_separately(self):
        """Same asset_id but different ayanamsha_id yields two separate emits."""
        conn, _ = _make_conn()
        with patch("pipeline.dispatcher.emit_node_added") as mock_emit:
            notify_first_row_write(conn, "b1", "ch1", "A3", "lahiri", 100, "synthesis")
            notify_first_row_write(conn, "b1", "ch1", "A3", "kp", 100, "synthesis")
            self.assertEqual(mock_emit.call_count, 2)

    def test_different_asset_emits_separately(self):
        """Different asset_id yields two separate emits."""
        conn, _ = _make_conn()
        with patch("pipeline.dispatcher.emit_node_added") as mock_emit:
            notify_first_row_write(conn, "b1", "ch1", "A1", "lahiri", 50, "layer1")
            notify_first_row_write(conn, "b1", "ch1", "A3", "lahiri", 50, "layer2")
            self.assertEqual(mock_emit.call_count, 2)

    def test_reset_clears_dedup_state(self):
        """After reset_sse_emit_state(), the same pair triggers a new emit."""
        conn, _ = _make_conn()
        with patch("pipeline.dispatcher.emit_node_added") as mock_emit:
            notify_first_row_write(conn, "b1", "ch1", "A3", "lahiri", 100, "synthesis")
            reset_sse_emit_state()
            notify_first_row_write(conn, "b1", "ch1", "A3", "lahiri", 100, "synthesis")
            self.assertEqual(mock_emit.call_count, 2)

    def test_non_fatal_when_emit_raises(self):
        """Exceptions from emit_node_added are swallowed (non-fatal)."""
        conn, _ = _make_conn()
        with patch("pipeline.dispatcher.emit_node_added", side_effect=Exception("db down")):
            # Must not raise
            notify_first_row_write(conn, "b1", "ch1", "A3", "lahiri", 10, "l")


class TestNotifyDownstreamEdges(unittest.TestCase):

    def setUp(self):
        reset_sse_emit_state()
        reset_dep_graph()

    def _seed_dep_graph(self, rows):
        """Patch _load_dep_graph to inject known edges without DB."""
        import pipeline.dispatcher as d
        d._dep_graph = {}
        d._dep_loaded = True
        from collections import defaultdict
        reverse = defaultdict(list)
        for asset_id, depends_on in rows:
            for dep in depends_on:
                reverse[dep].append(asset_id)
        d._dep_graph = dict(reverse)

    def test_emits_edge_for_upstream_to_downstream(self):
        """notify_downstream_edges emits edge_added for upstream→asset."""
        self._seed_dep_graph([("A3", ["A1"])])
        conn, _ = _make_conn()
        with patch("pipeline.dispatcher.emit_edge_added") as mock_edge:
            notify_downstream_edges(conn, "b1", "ch1", "A3")
            mock_edge.assert_called_once_with(conn, "b1", "ch1", "A1", "A3", "data_flow")

    def test_dedup_same_edge_only_once(self):
        """Same upstream→downstream edge only emitted once per build."""
        self._seed_dep_graph([("A3", ["A1"])])
        conn, _ = _make_conn()
        with patch("pipeline.dispatcher.emit_edge_added") as mock_edge:
            notify_downstream_edges(conn, "b1", "ch1", "A3")
            notify_downstream_edges(conn, "b1", "ch1", "A3")
            self.assertEqual(mock_edge.call_count, 1)

    def test_no_edges_for_asset_not_in_graph(self):
        """Asset with no upstreams produces no edge emits."""
        self._seed_dep_graph([])
        conn, _ = _make_conn()
        with patch("pipeline.dispatcher.emit_edge_added") as mock_edge:
            notify_downstream_edges(conn, "b1", "ch1", "A_ORPHAN")
            mock_edge.assert_not_called()

    def test_non_fatal_when_emit_raises(self):
        """Exceptions from emit_edge_added are swallowed (non-fatal)."""
        self._seed_dep_graph([("A3", ["A1"])])
        conn, _ = _make_conn()
        with patch("pipeline.dispatcher.emit_edge_added", side_effect=Exception("fail")):
            # Must not raise
            notify_downstream_edges(conn, "b1", "ch1", "A3")


if __name__ == "__main__":
    unittest.main()
