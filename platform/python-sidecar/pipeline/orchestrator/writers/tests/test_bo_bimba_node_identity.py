"""bo_bimba must never write a random node_id.

Nirmāṇa #1888 (D-CND-29). `node_id` was `str(uuid.uuid4())` at four emit sites, so
every bo_bimba rebuild minted fresh identities for the same logical nodes. That is
the mechanism behind bodha_cgm_paths/bodha_cgm_sub_graphs going 100%/33% orphaned
the moment bo_bimba rebuilt without them (measured live in #1888) -- the same
defect class as bo_laksana's signal_id (#1804/D-CND-11) and L4's phala_anchor_id
(#1754/D-CND-04), the third confirmed instance per D-CND-29.

The identity itself is computed by `bodha_cgm_node_identity()` (migration 714),
the single source of truth, verified against production in that migration's
dry-run: the natural key is exactly unique (1101/1101 nodes across all three
charts). These tests cover what that dry-run cannot: the WIRING -- that the writer
calls the function, assigns the result back onto the row dicts, cannot be
bypassed, and reports collapses honestly. Mirrors
test_bo_laksana_signal_identity.py's shape exactly.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "bo_bimba.py"


class _FakeConn:
    """Returns a derived-looking id per row, echoing the input index.

    bo_bimba.py calls `conn.execute(sql, params).fetchall()` directly (no
    `.cursor()` indirection) -- this fake matches that shape, not
    test_bo_laksana_signal_identity's cursor-based one.
    """

    def __init__(self) -> None:
        self.log: list = []
        self._rows: list[tuple[int, str]] = []

    def execute(self, sql: str, params=None) -> "_FakeConn":
        self.log.append((sql, params))
        payload = json.loads(params[0])
        # Mimic bodha_cgm_node_identity: a pure function of the identity tuple.
        self._rows = [
            (e["i"], "det-{}-{}-{}".format(e["ayanamsha_id"], e["node_type"], e["node_subject"]))
            for e in payload
        ]
        return self

    def fetchall(self):
        return self._rows


def _row(node_id, aya="lahiri", ntype="graha", subject="Sun") -> dict:
    return {
        "node_id": node_id,
        "chart_id": "482012f1-710e-4a25-994a-93821f5871aa",
        "ayanamsha_id": aya,
        "node_type": ntype,
        "node_subject": subject,
    }


def test_assigns_the_database_derived_identity_onto_the_row() -> None:
    from pipeline.orchestrator.writers.bo_bimba import assign_deterministic_node_ids

    conn = _FakeConn()
    rows = [_row(None), _row(None, subject="Moon")]
    assign_deterministic_node_ids(conn, rows)

    assert all(r["node_id"].startswith("det-") for r in rows)
    assert rows[0]["node_id"] != rows[1]["node_id"]


def test_identity_comes_from_sql_not_reimplemented_in_python() -> None:
    """The function must be CALLED. A Python copy is free to drift from the SQL one."""
    from pipeline.orchestrator.writers.bo_bimba import assign_deterministic_node_ids

    conn = _FakeConn()
    assign_deterministic_node_ids(conn, [_row(None)])
    sql = conn.log[0][0]
    assert "bodha_cgm_node_identity(" in sql, "the writer must call the SQL identity function"
    assert SOURCE.read_text(encoding="utf-8").count("uuid_generate_v5") == 0, (
        "the identity algorithm must not be reimplemented in Python"
    )


def test_same_identity_tuple_yields_the_same_id_across_separate_calls() -> None:
    """Determinism at the wiring level: two runs, same inputs, same id."""
    from pipeline.orchestrator.writers.bo_bimba import assign_deterministic_node_ids

    first, second = [_row(None)], [_row(None)]
    assign_deterministic_node_ids(_FakeConn(), first)
    assign_deterministic_node_ids(_FakeConn(), second)
    assert first[0]["node_id"] == second[0]["node_id"]


def test_reports_collapse_honestly_rather_than_assuming_none() -> None:
    """D-CND-29: two rows sharing a derived identity ARE the same node -- but say so."""
    from pipeline.orchestrator.writers.bo_bimba import assign_deterministic_node_ids

    rows = [_row(None), _row(None)]  # identical identity tuples
    collapsed = assign_deterministic_node_ids(_FakeConn(), rows)
    assert collapsed == 1
    assert assign_deterministic_node_ids(_FakeConn(), [_row(None), _row(None, subject="Moon")]) == 0


def test_no_emit_site_can_construct_a_random_node_id() -> None:
    """The defect itself, guarded at the source.

    Four emit sites carried `str(uuid.uuid4())`. A fifth is easy to add by
    copy-paste, and it would reintroduce the orphan class silently -- the row
    would look completely normal.
    """
    text = SOURCE.read_text(encoding="utf-8")
    offenders = [
        line.strip()
        for line in text.splitlines()
        if "node_id" in line and "uuid4" in line and not line.strip().startswith("#")
    ]
    assert offenders == [], f"node_id must never be randomly generated: {offenders}"


def test_derivation_runs_on_the_single_insert_path_not_at_the_emit_sites() -> None:
    """Placement matters: emit sites multiply, the insert path does not."""
    text = SOURCE.read_text(encoding="utf-8")
    insert_at = text.index("def _batch_insert(")
    assign_at = text.index("assign_deterministic_node_ids(conn, nodes)", insert_at)
    inserted_at = text.index("inserted = 0", insert_at)
    assert assign_at < inserted_at, (
        "identities must be derived before any row is written"
    )
