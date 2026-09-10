"""bo_karanajala must never write a random edge_id or contradiction_id.

Same defect class as bo_bimba's node_id (Nirmana #1888, D-CND-29) -- see
test_bo_bimba_node_identity.py, which this file mirrors exactly. `edge_id` and
`contradiction_id` were `str(uuid.uuid4())` at every emit site, so every
bo_karanajala rebuild minted fresh identities for the same logical edge/
contradiction, orphaning any downstream reference (bo_cgm_paths'
path_edge_ids_array, bo_cgm_motifs' involved_edge_ids_array/edge_ids_array) the
moment bo_karanajala rebuilds without them in the same pass.

The identities themselves are computed by `bodha_cgm_edge_identity()` and
`bodha_contradiction_identity()` (migration 950), the single source of truth.
These tests cover the WIRING -- that the writer calls the functions, assigns
the result back onto the row dicts, cannot be bypassed, and reports collapses
honestly.
"""
from __future__ import annotations

import json
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "bo_karanajala.py"


class _FakeConn:
    """Returns a derived-looking id per row, echoing the input index.

    bo_karanajala.py calls `conn.execute(sql, params).fetchall()` directly (no
    `.cursor()` indirection) for the identity round-trip -- this fake matches
    that shape, mirroring test_bo_bimba_node_identity.py's _FakeConn.
    """

    def __init__(self) -> None:
        self.log: list = []
        self._rows: list[tuple[int, str]] = []

    def execute(self, sql: str, params=None) -> "_FakeConn":
        self.log.append((sql, params))
        payload = json.loads(params[0])
        if "edge_type" in payload[0]:
            self._rows = [
                (e["i"], "edge-det-{}-{}-{}".format(
                    e["edge_type"], e["from_node_id"], e["to_node_id"]))
                for e in payload
            ]
        else:
            self._rows = [
                (e["i"], "contra-det-{}-{}".format(e["signal_a_id"], e["signal_b_id"]))
                for e in payload
            ]
        return self

    def fetchall(self):
        return self._rows


def _edge(edge_id=None, edge_type="aspect", from_node="n1", to_node="n2") -> dict:
    return {
        "edge_id": edge_id,
        "chart_id": "482012f1-710e-4a25-994a-93821f5871aa",
        "ayanamsha_id": "lahiri_chitrapaksha",
        "snapshot_type": "static_natal",
        "edge_type": edge_type,
        "from_node_id": from_node,
        "to_node_id": to_node,
    }


def _contradiction(contradiction_id=None, sig_a="s1", sig_b="s2") -> dict:
    return {
        "contradiction_id": contradiction_id,
        "chart_id": "482012f1-710e-4a25-994a-93821f5871aa",
        "ayanamsha_id": "lahiri_chitrapaksha",
        "signal_a_id": sig_a,
        "signal_b_id": sig_b,
    }


def test_assigns_the_database_derived_edge_identity_onto_the_row() -> None:
    from pipeline.orchestrator.writers.bo_karanajala import assign_deterministic_edge_ids

    conn = _FakeConn()
    edges = [_edge(), _edge(to_node="n3")]
    assign_deterministic_edge_ids(conn, edges)

    assert all(e["edge_id"].startswith("edge-det-") for e in edges)
    assert edges[0]["edge_id"] != edges[1]["edge_id"]


def test_assigns_the_database_derived_contradiction_identity_onto_the_row() -> None:
    from pipeline.orchestrator.writers.bo_karanajala import assign_deterministic_contradiction_ids

    conn = _FakeConn()
    rows = [_contradiction(), _contradiction(sig_b="s3")]
    assign_deterministic_contradiction_ids(conn, rows)

    assert all(r["contradiction_id"].startswith("contra-det-") for r in rows)
    assert rows[0]["contradiction_id"] != rows[1]["contradiction_id"]


def test_edge_identity_comes_from_sql_not_reimplemented_in_python() -> None:
    """The function must be CALLED. A Python copy is free to drift from the SQL one."""
    from pipeline.orchestrator.writers.bo_karanajala import assign_deterministic_edge_ids

    conn = _FakeConn()
    assign_deterministic_edge_ids(conn, [_edge()])
    sql = conn.log[0][0]
    assert "bodha_cgm_edge_identity(" in sql, "the writer must call the SQL identity function"
    assert SOURCE.read_text(encoding="utf-8").count("uuid_generate_v5") == 0, (
        "the identity algorithm must not be reimplemented in Python"
    )


def test_contradiction_identity_comes_from_sql_not_reimplemented_in_python() -> None:
    from pipeline.orchestrator.writers.bo_karanajala import assign_deterministic_contradiction_ids

    conn = _FakeConn()
    assign_deterministic_contradiction_ids(conn, [_contradiction()])
    sql = conn.log[0][0]
    assert "bodha_contradiction_identity(" in sql, (
        "the writer must call the SQL identity function"
    )


def test_same_edge_identity_tuple_yields_the_same_id_across_separate_calls() -> None:
    """Determinism at the wiring level: two runs, same inputs, same id."""
    from pipeline.orchestrator.writers.bo_karanajala import assign_deterministic_edge_ids

    first, second = [_edge()], [_edge()]
    assign_deterministic_edge_ids(_FakeConn(), first)
    assign_deterministic_edge_ids(_FakeConn(), second)
    assert first[0]["edge_id"] == second[0]["edge_id"]


def test_reports_edge_collapse_honestly_rather_than_assuming_none() -> None:
    """D-CND-29 class: two rows sharing a derived identity ARE the same edge -- but say so."""
    from pipeline.orchestrator.writers.bo_karanajala import assign_deterministic_edge_ids

    rows = [_edge(), _edge()]  # identical identity tuples
    collapsed = assign_deterministic_edge_ids(_FakeConn(), rows)
    assert collapsed == 1
    assert assign_deterministic_edge_ids(_FakeConn(), [_edge(), _edge(to_node="n3")]) == 0


def test_reports_contradiction_collapse_honestly_rather_than_assuming_none() -> None:
    from pipeline.orchestrator.writers.bo_karanajala import assign_deterministic_contradiction_ids

    rows = [_contradiction(), _contradiction()]  # identical identity tuples
    collapsed = assign_deterministic_contradiction_ids(_FakeConn(), rows)
    assert collapsed == 1


def test_no_emit_site_can_construct_a_random_edge_or_contradiction_id() -> None:
    """The defect itself, guarded at the source.

    Nine emit sites carried `str(uuid.uuid4())` (eight edge_id, one
    contradiction_id, one arudha/special_lagna node_id). A tenth is easy to add
    by copy-paste, and it would reintroduce the orphan class silently -- the
    row would look completely normal.
    """
    text = SOURCE.read_text(encoding="utf-8")
    offenders = [
        line.strip()
        for line in text.splitlines()
        if ("edge_id" in line or "contradiction_id" in line or "node_id" in line)
        and "uuid4" in line
        and not line.strip().startswith("#")
    ]
    assert offenders == [], f"identity columns must never be randomly generated: {offenders}"
    assert "import uuid" not in text, "uuid module should no longer be needed in this writer"


def test_edge_derivation_runs_on_the_single_insert_path_not_at_the_emit_sites() -> None:
    """Placement matters: emit sites multiply, the insert path does not."""
    text = SOURCE.read_text(encoding="utf-8")
    run_at = text.index("def run(self, ctx")
    assign_at = text.index("assign_deterministic_edge_ids(conn, edges)", run_at)
    insert_at = text.index("_batch_insert(conn, edges, _EDGE_INSERT)", run_at)
    assert assign_at < insert_at, "identities must be derived before any row is written"
