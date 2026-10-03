"""After a producer finishes, unqualified table names must mean the REAL tables, never the bind-time pg_temp shadows.

``bind_l2_exact_inputs`` creates ``ON COMMIT DROP`` temp tables named like the protected tables; ``pg_temp`` is searched first. A light
writer's transaction is still open when the orchestrator runs the registry's ``integrity_check_sql`` / ``count_sql`` with unqualified
names (asset_runner._probe_asset), so those statements read the shadows: a NOT EXISTS conjunct passes vacuously and a positive one can
be satisfied or failed by rows that are not the writer's output. The wrapper therefore ends every contracted call with
``SET LOCAL search_path = public, pg_temp``. Unit part (recording connection, no database) here; real-PostgreSQL part in
``test_l2_wrapper_shadow_real_pg.py``.
"""
from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

import bodha_writers.data_plane_contracts as dpc
from bodha_writers.data_plane_contracts import l2_producer

CHART = uuid.UUID("00000000-0000-4000-8000-0000000000a1")
BUILD = "00000000-0000-4000-8000-0000000000b1"


class _Cur:
    description = None

    def __init__(self, log):
        self.log = log

    def __enter__(self):
        return self

    def __exit__(self, *_a):
        return False

    def execute(self, sql, params=None):
        self.log.append(" ".join(sql.split())[:60])


class _Conn:
    _l2_contract_test_double = True

    def __init__(self):
        self.log = []

    def cursor(self):
        return _Cur(self.log)


@pytest.fixture(autouse=True)
def _stubs(monkeypatch):
    def up(_c, *, chart_id, asset_id, partition_key):
        return ([{"layer": "L1", "asset_id": "ga_positions", "generation_id": "g", "semantic_output_digest": "f" * 64}],
                {"subject_id": "s", "chart_id": chart_id, "generation_context_id": "g", "calculation_context_id": "c", "ayanamsha_id": "x",
                 "reference_frame": "sidereal", "varga_id": "D1", "partition_key": partition_key})
    monkeypatch.setattr(dpc, "_resolve_upstream_context", up)
    monkeypatch.setattr(dpc, "_writer_source_digest", lambda _a: "a" * 64)


def _probe(body_log):
    class Probe:
        asset_id = "bo_arudha"

        def run(self, ctx):
            body_log.append("body")
            return SimpleNamespace(rows_inserted=0, rows_updated=0, rows_skipped=0, notes="")
    return l2_producer("bo_arudha")(Probe)


def test_search_path_reset_is_the_last_statement_after_completion():
    conn = _Conn()
    _probe([])().run(SimpleNamespace(build_id=BUILD, config={"chart_id": CHART}, db_conn=conn, dry_run=False))
    assert conn.log[-1] == "SET LOCAL search_path = public, pg_temp", conn.log
    assert "complete_l2_data_plane_partition" in conn.log[-2], conn.log


def test_no_reset_when_the_contract_is_skipped():
    """dry_run / plain doubles never open a generation, so there are no shadows and no statement is issued."""
    class Plain:
        def cursor(self):
            raise AssertionError("a skipped contract must not touch the connection")
    _probe([])().run(SimpleNamespace(build_id=BUILD, config={"chart_id": CHART}, db_conn=Plain(), dry_run=True))
    _probe([])().run(SimpleNamespace(build_id=BUILD, config={"chart_id": CHART}, db_conn=object(), dry_run=False))


def test_a_failing_body_issues_no_reset():
    class Boom:
        asset_id = "bo_arudha"

        def run(self, ctx):
            raise RuntimeError("writer failed")
    conn = _Conn()
    with pytest.raises(RuntimeError):
        l2_producer("bo_arudha")(Boom)().run(SimpleNamespace(build_id=BUILD, config={"chart_id": CHART}, db_conn=conn, dry_run=False))
    assert "SET LOCAL search_path = public, pg_temp" not in conn.log


def test_helper_is_transaction_local_set_local_not_set():
    import inspect
    src = inspect.getsource(dpc._resolve_unqualified_names_to_real_tables)
    assert "SET LOCAL search_path" in src and "SET search_path" not in src.replace("SET LOCAL search_path", "")
