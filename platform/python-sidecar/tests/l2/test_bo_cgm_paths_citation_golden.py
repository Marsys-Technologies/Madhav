"""Golden-value narration fidelity test for bo_cgm_paths.citation_human, over a fake connection (no database).

_write_aya inserts one row per dispositor chain and states, on every row, the method the chain came from: the graha to sign-lord traversal that stops at a self-ruling graha
(or at the depth cap). The expected sentence is stated by hand from that method. It is the same sentence on every row (a constant citation, reported as a finding).
"""
from __future__ import annotations

from pipeline.orchestrator.writers.bo_cgm_paths import _write_aya

_NODES = [
    {"node_id": "n-moon", "node_subject": "moon", "node_label_human": "Moon", "position_in_chart_jsonb": {"sign": "taurus"}},
    {"node_id": "n-venus", "node_subject": "venus", "node_label_human": "Venus", "position_in_chart_jsonb": {"sign": "taurus"}},
]
_EDGES = [
    {"edge_id": "e1", "from_node_id": "n-moon", "to_node_id": "n-venus", "edge_type": "dispositor",
     "relationship_basis": "dispositor", "computed_strength": 1.0},
]


class _Cursor:
    def __init__(self, conn):
        self.conn = conn
        self._rows = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        if "INSERT INTO" in sql:
            self.conn.inserted.append(params)
            self._rows = []
        elif "FROM bodha_cgm_edges" in sql:
            self._rows = [dict(e) for e in _EDGES]
        elif "FROM bodha_cgm_nodes" in sql:
            self._rows = [dict(n) for n in _NODES]
        else:
            self._rows = []

    def fetchall(self):
        return self._rows


class _Conn:
    def __init__(self):
        self.inserted = []

    def cursor(self):
        return _Cursor(self)


def test_cgm_paths_citation_human_states_the_traversal_method():
    conn = _Conn()
    n = _write_aya(conn, "chart-1", "lahiri_chitrapaksha", "build-1", "2026-10-05T00:00:00+00:00")
    assert n >= 1 and len(conn.inserted) == n
    row = conn.inserted[0]
    assert row["citation_human"] == "CGM dispositor chain: graha → sign-lord traversal until self-ruling or max depth"
