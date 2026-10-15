"""C35 — tests for scripts/gochara/sealed_generation_staleness.py.

No database: a psycopg3-shaped fake connection answers by substring-matching the SQL
the script issues, so the tests prove (a) the script calls ONLY the existing
migration-1206 functions and never re-implements their logic, (b) the session is
forced read-only before any check statement, (c) fresh -> exit 0, stale (l1 drift /
daśā drift / completeness violation) -> exit 4, and any failure to run (no snapshot,
driver/DB error, no DATABASE_URL) -> exit 3.
"""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[5]
MODULE_PATH = REPO / "platform/python-sidecar/scripts/gochara/sealed_generation_staleness.py"
SPEC = importlib.util.spec_from_file_location("sealed_generation_staleness", MODULE_PATH)
assert SPEC and SPEC.loader
staleness = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(staleness)

CHART = "482012f1-710e-4a25-994a-93821f5871aa"
GENERATION = "5.0"
SNAP_ROW = (["fact-a", "fact-b"], ["11111111-1111-1111-1111-111111111111"], "L1SNAP", "DASHASNAP")


class FakeCursor:
    def __init__(self, conn: "FakeConn") -> None:
        self.conn = conn

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, *exc) -> bool:
        return False

    def execute(self, sql: str, params: list | None = None) -> None:
        self.conn.executed.append((sql, params))
        self.conn.result = self.conn.router(sql, params)

    def fetchone(self):
        return self.conn.result[0] if self.conn.result else None

    def fetchall(self) -> list:
        return self.conn.result


class FakeConn:
    def __init__(self, router) -> None:
        self.router = router
        self.executed: list[tuple[str, list | None]] = []
        self.result: list = []

    def cursor(self) -> FakeCursor:
        return FakeCursor(self)

    def __enter__(self) -> "FakeConn":
        return self

    def __exit__(self, *exc) -> bool:
        return False


def make_router(
    snap=SNAP_ROW,
    live_l1: str = "L1SNAP",
    live_dasha: str = "DASHASNAP",
    violations: list | None = None,
):
    def router(sql: str, params):
        if "FROM public.ka_gochara_search_input_snapshot" in sql:
            return [snap] if snap is not None else []
        if "ka_gochara_search_l1_facts_digest" in sql:
            assert params[0] == CHART and params[1] == list(SNAP_ROW[0])
            return [(live_l1,)]
        if "ka_gochara_search_dasha_digest" in sql:
            assert params[0] == CHART and params[1] == list(SNAP_ROW[1])
            return [(live_dasha,)]
        if "ka_gochara_search_completeness_violations" in sql:
            assert params == [CHART, GENERATION]
            return list(violations or [])
        if sql.startswith("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY"):
            return []
        raise AssertionError(f"unexpected SQL: {sql}")

    return router


def test_fresh_exit0(capsys) -> None:
    conn = FakeConn(make_router())
    assert staleness.run(conn, CHART, GENERATION) == 0
    report = __import__("json").loads(capsys.readouterr().out)
    assert report["status"] == "fresh"
    assert report["reasons"] == []
    assert report["chart_id"] == CHART and report["generation"] == GENERATION


def test_l1_drift_exit4(capsys) -> None:
    conn = FakeConn(make_router(live_l1="L1DRIFTED"))
    assert staleness.run(conn, CHART, GENERATION) == 4
    report = __import__("json").loads(capsys.readouterr().out)
    assert report["status"] == "stale"
    assert any("l1_facts_digest drift" in r and "L1SNAP" in r and "L1DRIFTED" in r for r in report["reasons"])


def test_dasha_drift_exit4(capsys) -> None:
    conn = FakeConn(make_router(live_dasha="DASHADRIFTED"))
    assert staleness.run(conn, CHART, GENERATION) == 4
    report = __import__("json").loads(capsys.readouterr().out)
    assert any("dasha_digest drift" in r for r in report["reasons"])


def test_completeness_violation_exit4(capsys) -> None:
    violations = [("conjunction", "partition_without_inventory", "event_class partition has no search inventory")]
    conn = FakeConn(make_router(violations=violations))
    assert staleness.run(conn, CHART, GENERATION) == 4
    report = __import__("json").loads(capsys.readouterr().out)
    assert any("conjunction" in r and "partition_without_inventory" in r for r in report["reasons"])


def test_missing_snapshot_raises() -> None:
    conn = FakeConn(make_router(snap=None))
    with pytest.raises(staleness.SnapshotMissing):
        staleness.check_staleness(conn, CHART, GENERATION)


def test_session_is_forced_read_only_before_any_check() -> None:
    conn = FakeConn(make_router())
    assert staleness.run(conn, CHART, GENERATION) == 0
    statements = [sql for sql, _ in conn.executed]
    assert statements[0] == "SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY"
    for sql in statements[1:]:
        assert sql.lstrip().upper().startswith("SELECT"), sql


def _patch_main(monkeypatch, conn, dsn: str | None = "postgresql://fake"):
    fake_psycopg = types.SimpleNamespace(connect=lambda _dsn, autocommit=True: conn)
    monkeypatch.setitem(sys.modules, "psycopg", fake_psycopg)
    monkeypatch.setattr(sys, "argv", ["sealed_generation_staleness.py", "--chart-id", CHART, "--generation", GENERATION])
    if dsn is None:
        monkeypatch.delenv("DATABASE_URL", raising=False)
    else:
        monkeypatch.setenv("DATABASE_URL", dsn)


def test_main_fresh_exit0(monkeypatch, capsys) -> None:
    _patch_main(monkeypatch, FakeConn(make_router()))
    assert staleness.main() == 0
    assert "fresh" in capsys.readouterr().out


def test_main_stale_exit4(monkeypatch, capsys) -> None:
    _patch_main(monkeypatch, FakeConn(make_router(live_l1="X")))
    assert staleness.main() == 4


def test_main_missing_snapshot_exit3(monkeypatch, capsys) -> None:
    _patch_main(monkeypatch, FakeConn(make_router(snap=None)))
    assert staleness.main() == 3
    assert "no sealed input snapshot" in capsys.readouterr().err


def test_main_db_error_exit3(monkeypatch, capsys) -> None:
    def boom(sql, params):
        raise RuntimeError("connection reset")

    _patch_main(monkeypatch, FakeConn(boom))
    assert staleness.main() == 3
    assert "could not run" in capsys.readouterr().err


def test_main_no_database_url_exit3(monkeypatch, capsys) -> None:
    _patch_main(monkeypatch, FakeConn(make_router()), dsn=None)
    assert staleness.main() == 3
    assert "DATABASE_URL is required" in capsys.readouterr().err
