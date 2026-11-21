"""NIR-04 — Dead-connection cleanup fallback in orchestrator runner.py.

Simulates the Cloud SQL Auth Proxy TCP reset observed in `brahma-build-pipeline-job-lmdpv`:
when `_schedule_parallel` raises `psycopg.OperationalError` and the main connection `conn`
is dead/closed (or fails on rollback/execute), `execute_run` must open a fresh fallback
connection via `connect()`, mark `build_runs` `'failed'`, abort remaining `'queued'`
`build_run_assets`, commit and close the fallback connection, and re-raise the exception.
"""
from __future__ import annotations

import json
import pathlib
import sys

import psycopg
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.orchestrator import runner  # noqa: E402

CHART_ID = "cb73cd3d-9eba-4220-9902-0de91566e980"
RUN_ID = "9bb668e7-8507-4eff-a06a-36e24ef22e4b"
PLAN = ["ga_structural", "ga_yoga"]


def _frozen_run_row() -> dict:
    manifest = {
        "version": "nirmana-run-manifest/v1",
        "chart_id": CHART_ID,
        "scope": "layer",
        "scope_target": "ganita",
        "action": "rebuild",
        "waves": [["ga_structural"], ["ga_yoga"]],
        "assets": [
            {
                "asset_id": asset_id,
                "scope": "per_chart",
                "depends_on": ["ga_structural"] if asset_id == "ga_yoga" else [],
                "natural_key_partition": None,
                "has_cowriters": False,
                "expected_code_digest": "0" * 64,
            }
            for asset_id in PLAN
        ],
    }
    return {
        "id": RUN_ID,
        "chart_id": CHART_ID,
        "scope": "layer",
        "scope_target": "ganita",
        "action": "rebuild",
        "plan": PLAN,
        "state": "planned",
        "plan_manifest": manifest,
        "plan_manifest_digest": runner._canonical_manifest_digest(manifest),
        "_preflight_manifest_text": json.dumps(manifest, ensure_ascii=True, sort_keys=True, separators=(",", ":")),
    }


class _MainCursor:
    def __init__(self, conn: _MainConn):
        self._conn = conn
        self._result = None
        self.calls: list[tuple[str, tuple | None]] = []

    def execute(self, sql: str, params=None):
        s = " ".join(sql.split())
        self.calls.append((s, params))
        if self._conn.dead:
            raise psycopg.OperationalError("consuming input failed: server closed the connection unexpectedly")
        if "FROM build_runs WHERE id" in s:
            self._result = [_frozen_run_row()]
        elif "count(*) AS active" in s:
            self._result = [{"active": 0}]
        elif "pg_try_advisory_lock" in s:
            self._result = [{"got": True}]
        elif "UPDATE build_runs SET state='running'" in s:
            self._result = [{"id": RUN_ID}]
        elif "FROM asset_registry" in s:
            self._result = [
                {
                    "asset_id": a,
                    "scope": "per_chart",
                    "depends_on": ["ga_structural"] if a == "ga_yoga" else [],
                    "natural_key_partition": None,
                    "has_cowriters": False,
                }
                for a in PLAN
            ]
        else:
            self._result = []

    def fetchone(self):
        return self._result[0] if self._result else None

    def fetchall(self):
        return list(self._result or [])


class _MainConn:
    def __init__(self, *, mark_closed_on_drop: bool = False):
        self.autocommit = False
        self.dead = False
        self.closed = False
        self._mark_closed_on_drop = mark_closed_on_drop
        self._cur = _MainCursor(self)

    def cursor(self):
        return self._cur

    def kill(self):
        self.dead = True
        if self._mark_closed_on_drop:
            self.closed = True

    def rollback(self):
        if self.dead:
            raise psycopg.OperationalError("connection already closed")

    def commit(self):
        if self.dead:
            raise psycopg.OperationalError("connection already closed")

    def close(self):
        self.closed = True


class _FallbackCursor:
    def __init__(self):
        self.calls: list[tuple[str, tuple | None]] = []

    def execute(self, sql: str, params=None):
        self.calls.append((" ".join(sql.split()), params))


class _FallbackConn:
    def __init__(self):
        self.autocommit = True
        self.commits = 0
        self.closed = False
        self.cur = _FallbackCursor()

    def cursor(self):
        return self.cur

    def commit(self):
        self.commits += 1

    def close(self):
        self.closed = True


@pytest.mark.parametrize("mark_closed_on_drop", [False, True])
def test_execute_run_uses_fresh_fallback_conn_when_main_conn_dies(monkeypatch, mark_closed_on_drop):
    main_conn = _MainConn(mark_closed_on_drop=mark_closed_on_drop)
    fallback_conn = _FallbackConn()
    connect_calls = []

    def fake_connect():
        connect_calls.append(len(connect_calls))
        return fallback_conn if len(connect_calls) > 1 else main_conn

    def failing_schedule(*_args, **_kwargs):
        main_conn.kill()
        raise psycopg.OperationalError("consuming input failed: server closed the connection unexpectedly")

    emitted: list[dict] = []
    monkeypatch.setattr(runner, "connect", fake_connect)
    monkeypatch.setattr(runner, "_verify_sidecar_code_matches_manifest", lambda _frozen: None)
    monkeypatch.setattr(runner, "_WRITER_GAP_MODE", "off")
    monkeypatch.setattr(runner, "_schedule_parallel", failing_schedule)
    monkeypatch.setattr(runner, "emit_event", emitted.append)
    monkeypatch.setattr(runner.signal, "signal", lambda *_args: None)
    monkeypatch.setattr("pipeline.orchestrator.writers.discover_all", lambda: None)

    with pytest.raises(psycopg.OperationalError, match="server closed the connection unexpectedly"):
        runner.execute_run(RUN_ID)

    assert len(connect_calls) == 2
    assert fallback_conn.autocommit is False
    assert fallback_conn.commits == 1
    assert fallback_conn.closed is True

    sqls = [sql for sql, _ in fallback_conn.cur.calls]
    assert any("UPDATE build_runs SET state = 'failed'" in sql for sql in sqls)
    assert any("UPDATE build_run_assets SET state = 'aborted'" in sql and "state = 'queued'" in sql for sql in sqls)
    assert any(ev.get("type") == "run.state_change" and ev.get("state") == "failed" for ev in emitted)


def test_terminalize_crashed_run_uses_healthy_main_conn_without_fallback(monkeypatch):
    main_conn = _MainConn()
    cur = main_conn.cursor()
    connect_called = False

    def fail_if_called():
        nonlocal connect_called
        connect_called = True
        raise AssertionError("connect() should not be called when main conn is healthy")

    monkeypatch.setattr(runner, "connect", fail_if_called)
    monkeypatch.setattr(runner, "emit_event", lambda _ev: None)

    runner._terminalize_crashed_run(main_conn, cur, RUN_ID, CHART_ID, RuntimeError("boom"))

    assert connect_called is False
    assert any("UPDATE build_runs SET state = 'failed'" in sql for sql, _ in cur.calls)
    assert any("UPDATE build_run_assets SET state = 'aborted'" in sql for sql, _ in cur.calls)


def test_terminalize_crashed_run_logs_and_does_not_mask_when_fallback_also_fails(monkeypatch):
    main_conn = _MainConn(mark_closed_on_drop=True)
    main_conn.kill()

    def broken_connect():
        raise psycopg.OperationalError("proxy completely unreachable")

    monkeypatch.setattr(runner, "connect", broken_connect)
    # Must not raise — caller re-raises the original exception.
    runner._terminalize_crashed_run(main_conn, main_conn.cursor(), RUN_ID, CHART_ID, RuntimeError("primary failure"))
