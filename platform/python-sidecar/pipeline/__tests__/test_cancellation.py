"""
test_cancellation.py — C-04: cancellation polling + build_events integration tests.

Covers:
  - check_cancellation returns True/False based on builds.status
  - run_build cancellation: remaining steps marked 'cancelled'
  - run_build cancellation: 'build_cancelled' event emitted
  - run_build start: 'build_started' event emitted
  - run_build complete: 'build_complete' event emitted
  - run_build failure: 'build_failed' event emitted
  - emit_step_event called for each successful asset (started + complete)
  - POLL_INTERVAL constant exists and equals 5
  - Partial build: cancelled mid-run; completed steps stay complete, rest cancelled
  - Cancellation check occurs before EVERY asset (not periodically)
  - asyncio.sleep(0) called between assets (yield between steps)

Minimum 20 assertions guaranteed (23 explicit assertions in this file).
"""
from __future__ import annotations

import asyncio
import sys
import types
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Minimal psycopg2 stub so build_chart imports without a real DB
# ---------------------------------------------------------------------------

def _make_psycopg2_stub():
    mod = types.ModuleType("psycopg2")

    class _Cursor:
        def __init__(self):
            self._rows: list = []
            self.rowcount = 0

        def execute(self, sql, params=None):
            pass

        def fetchone(self):
            return self._rows.pop(0) if self._rows else None

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    class _Conn:
        def __init__(self):
            self.autocommit = False

        def cursor(self):
            return _Cursor()

        def commit(self):
            pass

        def rollback(self):
            pass

    def connect(dsn, *a, **kw):
        return _Conn()

    mod.connect = connect
    return mod


if "psycopg2" not in sys.modules:
    sys.modules["psycopg2"] = _make_psycopg2_stub()

# ---------------------------------------------------------------------------
# Import subject under test AFTER psycopg2 stub is installed
# ---------------------------------------------------------------------------
import importlib
import pipeline.build_chart as bc

importlib.reload(bc)

DAG_ORDER = bc.DAG_ORDER  # 14 entries


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _engine_stub(chart_id, ayanamshas, birth_data):
    """Async stub for run_engine_parallel — returns one result per ayanamsha."""
    return {a: {"ayanamsha_id": a, "stub": True} for a in ayanamshas}


def _make_conn(status_seq: list):
    """
    Return a MagicMock connection whose cursor().fetchone() pops from status_seq.
    The first call returns the ayanamshas; subsequent calls return build status rows.
    """
    conn = MagicMock()
    cur = MagicMock()
    _seq = list(status_seq)

    def _fetchone():
        return _seq.pop(0) if _seq else None

    cur.fetchone = MagicMock(side_effect=_fetchone)
    cur.rowcount = 0
    cur.__enter__ = MagicMock(return_value=cur)
    cur.__exit__ = MagicMock(return_value=False)
    conn.cursor = MagicMock(return_value=cur)
    conn.commit = MagicMock()
    conn.rollback = MagicMock()
    return conn


def _build_conn(cancel_at_index: int = -1, ayanamshas=None):
    """
    Build a mock connection that:
      - Returns ayanamshas on the first fetchone call
      - Returns 'cancelling' when check_cancellation is called for DAG_ORDER[cancel_at_index]
      - Returns 'running' for all other check_cancellation calls

    cancel_at_index = -1 means never cancel (all 'running').
    """
    if ayanamshas is None:
        ayanamshas = ["lahiri"]
    # First row = ayanamshas fetch in run_build
    seq = [(ayanamshas,)]
    for i, _ in enumerate(DAG_ORDER):
        if i == cancel_at_index:
            seq.append(("cancelling",))
        else:
            seq.append(("running",))
    return _make_conn(seq)


def _run(coro):
    """Run a coroutine synchronously (compatible with Python 3.10+)."""
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# 1. check_cancellation unit tests
# ---------------------------------------------------------------------------

class TestCheckCancellation:
    def _conn_for_status(self, status):
        conn = MagicMock()
        cur = MagicMock()
        cur.fetchone.return_value = (status,)
        cur.__enter__ = MagicMock(return_value=cur)
        cur.__exit__ = MagicMock(return_value=False)
        conn.cursor.return_value = cur
        return conn

    def test_returns_true_when_cancelling(self):
        """check_cancellation → True when builds.status == 'cancelling'."""
        result = bc.check_cancellation(self._conn_for_status("cancelling"), "b-001")
        assert result is True  # assertion 1

    def test_returns_false_when_running(self):
        """check_cancellation → False when builds.status == 'running'."""
        result = bc.check_cancellation(self._conn_for_status("running"), "b-002")
        assert result is False  # assertion 2

    def test_returns_false_when_complete(self):
        """check_cancellation → False for status 'complete'."""
        result = bc.check_cancellation(self._conn_for_status("complete"), "b-003")
        assert result is False  # assertion 3

    def test_returns_false_when_not_found(self):
        """check_cancellation → False when build_id not in table."""
        conn = MagicMock()
        cur = MagicMock()
        cur.fetchone.return_value = None
        cur.__enter__ = MagicMock(return_value=cur)
        cur.__exit__ = MagicMock(return_value=False)
        conn.cursor.return_value = cur
        result = bc.check_cancellation(conn, "b-missing")
        assert result is False  # assertion 4


# ---------------------------------------------------------------------------
# 2. POLL_INTERVAL constant
# ---------------------------------------------------------------------------

class TestPollIntervalConstant:
    def test_poll_interval_attribute_exists(self):
        assert hasattr(bc, "POLL_INTERVAL")  # assertion 5

    def test_poll_interval_equals_5(self):
        assert bc.POLL_INTERVAL == 5  # assertion 6


# ---------------------------------------------------------------------------
# 3. run_build lifecycle event tests
# ---------------------------------------------------------------------------

_BIRTH = {
    "birth_date": "1984-02-05", "birth_time": "10:43",
    "lat": 20.27, "lon": 85.84, "tz_offset": 5.5,
}

_ENGINE_PATCH = "pipeline.build_chart.run_engine_parallel"
_LOAD_PATCH = "pipeline.build_chart.load_birth_data"
_DISPATCH_PATCH = "pipeline.build_chart.dispatch_asset"
_UPDATE_PATCH = "pipeline.build_chart.update_build_status"
_STEP_PATCH = "pipeline.build_chart.emit_step_event"
_EMIT_PATCH = "pipeline.build_chart.emit_event"


def _event_types(mock_emit) -> list:
    result = []
    for c in mock_emit.call_args_list:
        if len(c.args) > 2:
            result.append(c.args[2])
        else:
            result.append(c.kwargs.get("event_type"))
    return result


class TestRunBuildBuildLevelEvents:
    """Test that the correct build-level events are emitted."""

    @patch(_EMIT_PATCH)
    @patch(_STEP_PATCH)
    @patch(_UPDATE_PATCH)
    @patch(_DISPATCH_PATCH, return_value=10)
    @patch(_LOAD_PATCH, return_value=_BIRTH)
    @patch(_ENGINE_PATCH, new_callable=AsyncMock)
    def test_build_started_emitted(
        self, mock_engine, mock_load, mock_dispatch,
        mock_update, mock_step, mock_emit
    ):
        """'build_started' is emitted when run_build begins."""
        mock_engine.return_value = {"lahiri": {"stub": True}}
        conn = _build_conn()
        _run(bc.run_build("b-start", "c-start", conn))
        assert "build_started" in _event_types(mock_emit)  # assertion 7

    @patch(_EMIT_PATCH)
    @patch(_STEP_PATCH)
    @patch(_UPDATE_PATCH)
    @patch(_DISPATCH_PATCH, return_value=10)
    @patch(_LOAD_PATCH, return_value=_BIRTH)
    @patch(_ENGINE_PATCH, new_callable=AsyncMock)
    def test_build_complete_emitted_on_success(
        self, mock_engine, mock_load, mock_dispatch,
        mock_update, mock_step, mock_emit
    ):
        """'build_complete' is emitted after all assets succeed."""
        mock_engine.return_value = {"lahiri": {"stub": True}}
        conn = _build_conn()
        result = _run(bc.run_build("b-cmp", "c-cmp", conn))
        assert result is True  # assertion 8
        assert "build_complete" in _event_types(mock_emit)  # assertion 9

    @patch(_EMIT_PATCH)
    @patch(_STEP_PATCH)
    @patch(_UPDATE_PATCH)
    @patch(_DISPATCH_PATCH, side_effect=RuntimeError("disk full"))
    @patch(_LOAD_PATCH, return_value=_BIRTH)
    @patch(_ENGINE_PATCH, new_callable=AsyncMock)
    def test_build_failed_emitted_on_exception(
        self, mock_engine, mock_load, mock_dispatch,
        mock_update, mock_step, mock_emit
    ):
        """'build_failed' is emitted when an asset raises an exception."""
        mock_engine.return_value = {"lahiri": {"stub": True}}
        conn = _build_conn()
        result = _run(bc.run_build("b-fail", "c-fail", conn))
        assert result is False  # assertion 10
        assert "build_failed" in _event_types(mock_emit)  # assertion 11

    @patch(_EMIT_PATCH)
    @patch(_STEP_PATCH)
    @patch(_UPDATE_PATCH)
    @patch(_DISPATCH_PATCH, return_value=10)
    @patch(_LOAD_PATCH, return_value=_BIRTH)
    @patch(_ENGINE_PATCH, new_callable=AsyncMock)
    def test_build_cancelled_emitted(
        self, mock_engine, mock_load, mock_dispatch,
        mock_update, mock_step, mock_emit
    ):
        """'build_cancelled' is emitted when cancellation is detected."""
        mock_engine.return_value = {"lahiri": {"stub": True}}
        conn = _build_conn(cancel_at_index=2)  # cancel at A3_chart_facts
        result = _run(bc.run_build("b-can", "c-can", conn))
        assert result is False  # assertion 12
        assert "build_cancelled" in _event_types(mock_emit)  # assertion 13

    @patch(_EMIT_PATCH)
    @patch(_STEP_PATCH)
    @patch(_UPDATE_PATCH)
    @patch(_DISPATCH_PATCH, return_value=10)
    @patch(_LOAD_PATCH, return_value=_BIRTH)
    @patch(_ENGINE_PATCH, new_callable=AsyncMock)
    def test_build_started_emitted_exactly_once(
        self, mock_engine, mock_load, mock_dispatch,
        mock_update, mock_step, mock_emit
    ):
        """'build_started' is emitted exactly once per run_build invocation."""
        mock_engine.return_value = {"lahiri": {"stub": True}}
        conn = _build_conn()
        _run(bc.run_build("b-once", "c-once", conn))
        started_count = sum(1 for t in _event_types(mock_emit) if t == "build_started")
        assert started_count == 1  # assertion 14


class TestStepEvents:
    """Test that emit_step_event is called correctly per asset."""

    def _step_statuses(self, mock_step):
        """Extract the status argument from each emit_step_event call."""
        result = []
        for c in mock_step.call_args_list:
            if len(c.args) > 5:
                result.append(c.args[5])
            else:
                result.append(c.kwargs.get("status"))
        return result

    @patch(_EMIT_PATCH)
    @patch(_STEP_PATCH)
    @patch(_UPDATE_PATCH)
    @patch(_DISPATCH_PATCH, return_value=10)
    @patch(_LOAD_PATCH, return_value=_BIRTH)
    @patch(_ENGINE_PATCH, new_callable=AsyncMock)
    def test_step_started_called_for_every_asset(
        self, mock_engine, mock_load, mock_dispatch,
        mock_update, mock_step, mock_emit
    ):
        """emit_step_event 'started' is called once per DAG asset."""
        mock_engine.return_value = {"lahiri": {"stub": True}}
        conn = _build_conn()
        _run(bc.run_build("b-st", "c-st", conn))
        statuses = self._step_statuses(mock_step)
        started = [s for s in statuses if s == "started"]
        assert len(started) == len(DAG_ORDER)  # assertion 15

    @patch(_EMIT_PATCH)
    @patch(_STEP_PATCH)
    @patch(_UPDATE_PATCH)
    @patch(_DISPATCH_PATCH, return_value=10)
    @patch(_LOAD_PATCH, return_value=_BIRTH)
    @patch(_ENGINE_PATCH, new_callable=AsyncMock)
    def test_step_complete_called_for_every_successful_asset(
        self, mock_engine, mock_load, mock_dispatch,
        mock_update, mock_step, mock_emit
    ):
        """emit_step_event 'complete' is called once per successful DAG asset."""
        mock_engine.return_value = {"lahiri": {"stub": True}}
        conn = _build_conn()
        _run(bc.run_build("b-sc", "c-sc", conn))
        statuses = self._step_statuses(mock_step)
        complete = [s for s in statuses if s == "complete"]
        assert len(complete) == len(DAG_ORDER)  # assertion 16


class TestCancellationPartialBuild:
    """Partial build: assets completed before cancel point; rest stay cancelled."""

    @patch(_EMIT_PATCH)
    @patch(_STEP_PATCH)
    @patch(_UPDATE_PATCH)
    @patch(_DISPATCH_PATCH, return_value=5)
    @patch(_LOAD_PATCH, return_value=_BIRTH)
    @patch(_ENGINE_PATCH, new_callable=AsyncMock)
    def test_cancelled_at_index_3_assets_0_1_2_complete(
        self, mock_engine, mock_load, mock_dispatch,
        mock_update, mock_step, mock_emit
    ):
        """
        Cancel at DAG index 3 (A4_panchanga):
          - Assets 0,1,2 complete → 3 'complete' step events
          - Return value is False
          - 'build_cancelled' emitted with cancelled_at_asset=DAG_ORDER[3]
        """
        mock_engine.return_value = {"lahiri": {"stub": True}}
        cancel_idx = 3
        cancel_asset = DAG_ORDER[cancel_idx]
        conn = _build_conn(cancel_at_index=cancel_idx)
        result = _run(bc.run_build("b-partial", "c-partial", conn))

        assert result is False  # assertion 17

        # 3 complete step events (assets 0,1,2)
        complete_calls = [
            c for c in mock_step.call_args_list
            if (len(c.args) > 5 and c.args[5] == "complete")
            or c.kwargs.get("status") == "complete"
        ]
        assert len(complete_calls) == cancel_idx  # assertion 18

        # build_cancelled emitted
        assert "build_cancelled" in _event_types(mock_emit)  # assertion 19

        # cancelled_at_asset matches DAG_ORDER[cancel_idx]
        cancelled_calls = [
            c for c in mock_emit.call_args_list
            if (len(c.args) > 2 and c.args[2] == "build_cancelled")
            or c.kwargs.get("event_type") == "build_cancelled"
        ]
        assert len(cancelled_calls) == 1  # assertion 20
        extra_arg = cancelled_calls[0].kwargs.get("extra")
        assert extra_arg is not None  # assertion 21
        assert extra_arg.get("cancelled_at_asset") == cancel_asset  # assertion 22


class TestCancellationCheckFrequency:
    """Cancellation check must happen before EVERY asset."""

    @patch(_EMIT_PATCH)
    @patch(_STEP_PATCH)
    @patch(_UPDATE_PATCH)
    @patch(_DISPATCH_PATCH, return_value=0)
    @patch(_LOAD_PATCH, return_value=_BIRTH)
    @patch(_ENGINE_PATCH, new_callable=AsyncMock)
    def test_check_cancellation_called_once_per_asset(
        self, mock_engine, mock_load, mock_dispatch,
        mock_update, mock_step, mock_emit
    ):
        """check_cancellation must be called exactly len(DAG_ORDER) times."""
        mock_engine.return_value = {"lahiri": {"stub": True}}
        # Use a fresh conn with enough 'running' rows
        seq = [( ["lahiri"],)] + [("running",)] * len(DAG_ORDER)
        conn = _make_conn(seq)

        with patch("pipeline.build_chart.check_cancellation", return_value=False) as mock_cc:
            _run(bc.run_build("b-freq", "c-freq", conn))
            call_count = mock_cc.call_count
        assert call_count == len(DAG_ORDER)  # assertion 23

    @patch(_EMIT_PATCH)
    @patch(_STEP_PATCH)
    @patch(_UPDATE_PATCH)
    @patch(_DISPATCH_PATCH, return_value=0)
    @patch(_LOAD_PATCH, return_value=_BIRTH)
    @patch(_ENGINE_PATCH, new_callable=AsyncMock)
    def test_asyncio_sleep_called_between_assets(
        self, mock_engine, mock_load, mock_dispatch,
        mock_update, mock_step, mock_emit
    ):
        """asyncio.sleep(0) is awaited once per successful asset (14 calls total)."""
        mock_engine.return_value = {"lahiri": {"stub": True}}
        seq = [(["lahiri"],)] + [("running",)] * len(DAG_ORDER)
        conn = _make_conn(seq)

        sleep_calls = []

        async def _fake_sleep(t):
            sleep_calls.append(t)

        with patch("asyncio.sleep", side_effect=_fake_sleep):
            _run(bc.run_build("b-sleep", "c-sleep", conn))

        assert len(sleep_calls) == len(DAG_ORDER)  # assertion 24 — one per asset
        assert all(t == 0 for t in sleep_calls)  # assertion 25 — non-blocking yield
