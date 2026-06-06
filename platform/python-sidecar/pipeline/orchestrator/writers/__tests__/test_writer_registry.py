"""
Phase 2 AC tests: writer registry + state transitions + per-asset error recovery.
Runs without a real DB — uses mock connections/cursors.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch, call
import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mock_conn_cur():
    """Return (mock_conn, mock_cur) wired up like psycopg."""
    cur = MagicMock()
    cur.fetchone.return_value = None
    cur.fetchall.return_value = []
    conn = MagicMock()
    conn.cursor.return_value.__enter__ = lambda s: cur
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return conn, cur


# ── Writer registry ───────────────────────────────────────────────────────────

def test_register_and_get_writer():
    from pipeline.orchestrator.writers import WRITER_REGISTRY, register, get_writer

    @register("fixture.asset_a")
    def _writer(chart_id, conn):
        return 42

    assert get_writer("fixture.asset_a") is _writer
    assert WRITER_REGISTRY["fixture.asset_a"] is _writer


def test_get_writer_missing_returns_none():
    from pipeline.orchestrator.writers import get_writer
    assert get_writer("does.not.exist.xyz") is None


# ── run_asset — success path ──────────────────────────────────────────────────

def test_run_asset_success_transitions():
    """Writer returning rows → asset_throughput goes to 'lit'."""
    from pipeline.orchestrator.writers import WRITER_REGISTRY, register
    from pipeline.orchestrator import asset_runner

    @register("fixture.success")
    def _writer(chart_id, conn):
        return 7

    conn, cur = _mock_conn_cur()
    cur.fetchall.return_value = []  # no downstream assets

    with patch.object(asset_runner, "emit_event") as mock_emit, \
         patch.object(asset_runner, "compute_upstream_hash", return_value="aabbccdd"), \
         patch.object(asset_runner, "get_writer_git_hash", return_value="deaddead"):

        asset_runner.run_asset(conn, cur, "run-1", "chart-1", "fixture.success", 0)

    # Should have set state='lit' in asset_throughput
    update_calls = [str(c) for c in cur.execute.call_args_list]
    lit_call = any("'lit'" in c or "state = 'lit'" in c or "state = %s" in c for c in update_calls)
    assert lit_call or any("lit" in c for c in update_calls), \
        f"Expected 'lit' state update; got calls: {update_calls}"

    # emit_event should have fired asset.state_change to 'lit'
    emitted_types = [c.args[0]["type"] for c in mock_emit.call_args_list]
    assert "asset.state_change" in emitted_types
    assert "asset.progress" in emitted_types


# ── run_asset — error recovery ────────────────────────────────────────────────

def test_run_asset_writer_error_marks_error_state():
    """Writer raising → asset goes to 'error'; function returns (doesn't re-raise)."""
    from pipeline.orchestrator.writers import register
    from pipeline.orchestrator import asset_runner

    @register("fixture.crashing")
    def _bad_writer(chart_id, conn):
        raise RuntimeError("intentional crash")

    conn, cur = _mock_conn_cur()

    with patch.object(asset_runner, "emit_event") as mock_emit, \
         patch.object(asset_runner, "compute_upstream_hash", return_value="x"), \
         patch.object(asset_runner, "get_writer_git_hash", return_value="x"):

        # Should NOT raise — per-asset error recovery
        asset_runner.run_asset(conn, cur, "run-2", "chart-2", "fixture.crashing", 0)

    emitted = [c.args[0] for c in mock_emit.call_args_list]
    error_events = [e for e in emitted if e.get("to_state") == "error"]
    assert error_events, "Expected error state_change event"
    assert "intentional crash" in error_events[0].get("error", "")


def test_run_asset_no_writer_marks_error():
    """Missing writer registration → marks error, doesn't crash."""
    from pipeline.orchestrator import asset_runner

    conn, cur = _mock_conn_cur()

    with patch.object(asset_runner, "emit_event") as mock_emit:
        asset_runner.run_asset(conn, cur, "run-3", "chart-3", "no.writer.here", 0)

    emitted = [c.args[0] for c in mock_emit.call_args_list]
    error_events = [e for e in emitted if e.get("to_state") == "error"]
    assert error_events
    assert "no writer registered" in error_events[0].get("error", "")


# ── downstream closure ────────────────────────────────────────────────────────

def test_compute_downstream_closure_empty():
    from pipeline.orchestrator.asset_runner import compute_downstream_closure

    cur = MagicMock()
    cur.fetchall.return_value = []
    result = compute_downstream_closure(cur, "leaf.asset")
    assert result == []
    cur.execute.assert_called_once()
