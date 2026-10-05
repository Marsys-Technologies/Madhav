"""After a producer finishes, unqualified table names must mean the REAL tables, never the bind-time pg_temp shadows.

``bind_l2_exact_inputs`` creates ``ON COMMIT DROP`` temp tables named like the protected tables; ``pg_temp`` is searched first. A light
writer's transaction is still open when the orchestrator runs the registry's ``integrity_check_sql`` / ``count_sql`` with unqualified
names (asset_runner._probe_asset), so those statements read the shadows: a NOT EXISTS conjunct passes vacuously and a positive one can
be satisfied or failed by rows that are not the writer's output. The wrapper therefore ends every contracted call with
``SET LOCAL search_path = public, pg_temp`` and begins every contracted call with ``SET LOCAL search_path TO DEFAULT`` (the end-of-call
statement lasts until the transaction ends, so a second call in the same transaction would otherwise read the real tables instead of
its own fresh shadows). Unit part (recording connection, no database) here; real-PostgreSQL part in
``test_l2_wrapper_shadow_real_pg.py``.
"""
from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

import bodha_writers.data_plane_contracts as dpc
from bodha_writers.data_plane_contracts import l2_producer


@pytest.fixture(autouse=True)
def _data_plane_build_path_on(monkeypatch):
    """N-165: the data-plane build path is OFF by default. This module exercises the dormant
    contract machinery, so it switches the one explicit switch on for each test."""
    monkeypatch.setattr("ga_writers.data_plane_contracts.DATA_PLANE_BUILD_PATH_ENABLED", True)


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


# --- two contracted calls in ONE transaction (independent review MED: the end-of-call SET LOCAL lasts until the transaction ends) ---------

class _PathCur(_Cur):
    """Tracks the transaction-local search_path the way PostgreSQL does: ``SET LOCAL search_path TO DEFAULT`` puts the session default back
    (``pg_temp`` implicitly FIRST), ``SET LOCAL search_path = public, pg_temp`` puts ``pg_temp`` LAST. ``bind_l2_exact_inputs`` creates shadows."""

    def execute(self, sql, params=None):
        super().execute(sql, params)
        flat = " ".join(sql.split())
        state = self.log.state
        if flat == "SET LOCAL search_path TO DEFAULT":
            state["path"] = "default"
        elif flat == "SET LOCAL search_path = public, pg_temp":
            state["path"] = "public_first"
        elif "bind_l2_exact_inputs" in flat:
            state["shadows"] = True


class _Log(list):
    def __init__(self):
        super().__init__()
        self.state = {"path": "default", "shadows": False}


class _PathConn(_Conn):
    def __init__(self):
        self.log = _Log()

    def cursor(self):
        return _PathCur(self.log)


def _recording_probe(seen):
    class Probe:
        asset_id = "bo_arudha"

        def run(self, ctx):
            st = ctx.db_conn.log.state
            seen.append("shadow" if st["shadows"] and st["path"] == "default" else "REAL_TABLE")
            return SimpleNamespace(rows_inserted=0, rows_updated=0, rows_skipped=0, notes="")
    return l2_producer("bo_arudha")(Probe)


def test_two_wrapped_calls_in_one_transaction_each_read_their_own_shadows():
    seen: list[str] = []
    conn = _PathConn()
    ctx = SimpleNamespace(build_id=BUILD, config={"chart_id": CHART}, db_conn=conn, dry_run=False)
    wrapped = _recording_probe(seen)()
    wrapped.run(ctx)
    assert conn.log.state["path"] == "public_first", "premise: the first call ended with the integrity-check reset"
    wrapped.run(ctx)
    assert seen == ["shadow", "shadow"], seen
    assert conn.log.state["path"] == "public_first", "and the second call ends with the reset as well"


def test_the_entry_reset_is_the_first_statement_of_every_call_and_precedes_the_bind():
    conn = _PathConn()
    ctx = SimpleNamespace(build_id=BUILD, config={"chart_id": CHART}, db_conn=conn, dry_run=False)
    wrapped = _recording_probe([])()
    wrapped.run(ctx)
    wrapped.run(ctx)
    entry = [i for i, s in enumerate(conn.log) if s == "SET LOCAL search_path TO DEFAULT"]
    binds = [i for i, s in enumerate(conn.log) if "bind_l2_exact_inputs" in s]
    assert len(entry) == 2 and len(binds) == 2, list(conn.log)
    assert entry[0] == 0 and entry[0] < binds[0] and entry[1] < binds[1], list(conn.log)


def test_the_entry_reset_restores_the_default_and_never_hardcodes_a_path():
    import inspect
    src = inspect.getsource(dpc._restore_default_search_path_at_entry)
    assert "SET LOCAL search_path TO DEFAULT" in src and "public" not in src.split('"""')[2]
