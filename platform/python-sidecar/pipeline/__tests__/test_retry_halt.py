"""
tests/test_retry_halt.py — C-05 retry-then-halt logic tests.

Covers:
  - MAX_RETRIES constant == 3
  - RETRY_DELAYS constant == [2, 4, 8]
  - dispatch_asset_with_retry succeeds on first attempt
  - dispatch_asset_with_retry retries on transient failure
  - dispatch_asset_with_retry exhausts all 3 attempts and returns (0, error_msg)
  - dispatch_asset_with_retry succeeds on 2nd attempt (1 failure + 1 success)
  - dispatch_asset_with_retry succeeds on 3rd attempt (2 failures + 1 success)
  - error_msg is None on success, non-empty string on exhaustion
  - retry_count updated in build_steps on retries (mock conn)
  - run_build marks build 'failed' when dispatch_asset_with_retry exhausts
  - run_build returns True / marks 'complete' when all assets succeed after retries
"""
from __future__ import annotations

import asyncio
import sys
import types
import unittest
from unittest.mock import AsyncMock, MagicMock, call, patch

# ---------------------------------------------------------------------------
# Minimal stubs so the module can be imported without real DB / pyjhora_adapter
# ---------------------------------------------------------------------------

# Stub psycopg2 before importing the module under test
_psycopg2_stub = types.ModuleType("psycopg2")
_psycopg2_stub.connect = MagicMock()
sys.modules.setdefault("psycopg2", _psycopg2_stub)

# Stub build_events (used by build_chart at import time via try/except)
_build_events_stub = types.ModuleType("pipeline.build_events")
_build_events_stub.emit_event = MagicMock(return_value=None)
_build_events_stub.emit_step_event = MagicMock(return_value=None)
sys.modules.setdefault("pipeline.build_events", _build_events_stub)

import pipeline.build_chart as bc  # noqa: E402  (must come after stubs)


# ---------------------------------------------------------------------------
# Helper: build a minimal mock psycopg2-style connection
# ---------------------------------------------------------------------------

def _make_conn():
    conn = MagicMock()
    cur = MagicMock()
    cur.__enter__ = MagicMock(return_value=cur)
    cur.__exit__ = MagicMock(return_value=False)
    conn.cursor.return_value = cur
    conn.commit = MagicMock()
    return conn


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------

class TestRetryConstants(unittest.TestCase):
    def test_max_retries_is_3(self):
        """MAX_RETRIES == 3 (assertion 1)"""
        self.assertEqual(bc.MAX_RETRIES, 3)

    def test_retry_delays_is_2_4_8(self):
        """RETRY_DELAYS == [2, 4, 8] (assertion 2)"""
        self.assertEqual(bc.RETRY_DELAYS, [2, 4, 8])

    def test_retry_delays_length_matches_max_retries(self):
        """len(RETRY_DELAYS) == MAX_RETRIES (one delay entry per attempt) (assertion 3)"""
        self.assertEqual(len(bc.RETRY_DELAYS), bc.MAX_RETRIES)


# ---------------------------------------------------------------------------
# 2. dispatch_asset_with_retry — success on first attempt
# ---------------------------------------------------------------------------

class TestDispatchAssetWithRetrySuccessFirstAttempt(unittest.TestCase):
    def test_success_first_attempt_returns_rows_written(self):
        """On first-attempt success, returns (rows_written, None) (assertion 4)"""
        conn = _make_conn()
        with patch("pipeline.build_chart.dispatch_asset", return_value=42):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                rows, err = asyncio.run(
                    bc.dispatch_asset_with_retry(
                        "A2_forensic_render", "build-1", "chart-1", ["lahiri"], conn, {}
                    )
                )
        self.assertEqual(rows, 42)  # assertion 4a
        self.assertIsNone(err)       # assertion 5

    def test_success_first_attempt_no_sleep(self):
        """No asyncio.sleep called on immediate success (assertion 6)"""
        conn = _make_conn()
        with patch("pipeline.build_chart.dispatch_asset", return_value=10):
            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                asyncio.run(
                    bc.dispatch_asset_with_retry(
                        "A3_chart_facts", "build-1", "chart-1", ["lahiri"], conn, {}
                    )
                )
        mock_sleep.assert_not_called()  # assertion 6


# ---------------------------------------------------------------------------
# 3. dispatch_asset_with_retry — exhausts all 3 attempts
# ---------------------------------------------------------------------------

class TestDispatchAssetWithRetryExhaustion(unittest.TestCase):
    def test_exhaustion_returns_0_rows_and_error_msg(self):
        """After 3 failures, returns (0, non-empty-string) (assertions 7, 8)"""
        conn = _make_conn()
        with patch("pipeline.build_chart.dispatch_asset", side_effect=RuntimeError("boom")):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                rows, err = asyncio.run(
                    bc.dispatch_asset_with_retry(
                        "A4_panchanga", "build-1", "chart-1", ["lahiri"], conn, {}
                    )
                )
        self.assertEqual(rows, 0)           # assertion 7
        self.assertIsNotNone(err)           # assertion 8a
        self.assertIsInstance(err, str)     # assertion 8b
        self.assertGreater(len(err), 0)     # assertion 8c — non-empty string

    def test_exhaustion_attempt_count(self):
        """dispatch_asset is called exactly MAX_RETRIES times on total failure (assertion 9)"""
        conn = _make_conn()
        with patch("pipeline.build_chart.dispatch_asset", side_effect=ValueError("fail")) as mock_d:
            with patch("asyncio.sleep", new_callable=AsyncMock):
                asyncio.run(
                    bc.dispatch_asset_with_retry(
                        "A5_sensitive_points", "build-1", "chart-1", ["lahiri"], conn, {}
                    )
                )
        self.assertEqual(mock_d.call_count, bc.MAX_RETRIES)  # assertion 9

    def test_exhaustion_error_msg_contains_exception_type(self):
        """error_msg includes exception type name (assertion 10)"""
        conn = _make_conn()
        with patch("pipeline.build_chart.dispatch_asset", side_effect=TypeError("bad type")):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                _, err = asyncio.run(
                    bc.dispatch_asset_with_retry(
                        "A6_vargas", "build-1", "chart-1", ["lahiri"], conn, {}
                    )
                )
        self.assertIn("TypeError", err)  # assertion 10


# ---------------------------------------------------------------------------
# 4. dispatch_asset_with_retry — succeeds on 2nd attempt
# ---------------------------------------------------------------------------

class TestDispatchAssetWithRetrySuccessOnSecondAttempt(unittest.TestCase):
    def test_success_on_second_attempt(self):
        """1 failure then success: returns (rows, None) (assertion 11)"""
        conn = _make_conn()
        side_effects = [RuntimeError("transient"), 7]

        def _dispatch(*a, **kw):
            val = side_effects.pop(0)
            if isinstance(val, Exception):
                raise val
            return val

        with patch("pipeline.build_chart.dispatch_asset", side_effect=_dispatch):
            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                rows, err = asyncio.run(
                    bc.dispatch_asset_with_retry(
                        "A7_dashas", "build-1", "chart-1", ["lahiri"], conn, {}
                    )
                )

        self.assertEqual(rows, 7)          # assertion 11a
        self.assertIsNone(err)             # assertion 11b
        mock_sleep.assert_called_once()    # exactly one sleep (assertion 12)

    def test_success_on_second_attempt_sleep_delay(self):
        """Sleep uses RETRY_DELAYS[0] (2s) on first retry (assertion 13)"""
        conn = _make_conn()
        side_effects = [OSError("oops"), 3]

        def _dispatch(*a, **kw):
            val = side_effects.pop(0)
            if isinstance(val, Exception):
                raise val
            return val

        with patch("pipeline.build_chart.dispatch_asset", side_effect=_dispatch):
            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                asyncio.run(
                    bc.dispatch_asset_with_retry(
                        "A8_t1_structural", "build-1", "chart-1", ["lahiri"], conn, {}
                    )
                )
        mock_sleep.assert_called_once_with(bc.RETRY_DELAYS[0])  # assertion 13


# ---------------------------------------------------------------------------
# 5. dispatch_asset_with_retry — succeeds on 3rd attempt
# ---------------------------------------------------------------------------

class TestDispatchAssetWithRetrySuccessOnThirdAttempt(unittest.TestCase):
    def test_success_on_third_attempt(self):
        """2 failures then success: returns (rows, None) (assertion 14)"""
        conn = _make_conn()
        side_effects = [RuntimeError("e1"), RuntimeError("e2"), 15]

        def _dispatch(*a, **kw):
            val = side_effects.pop(0)
            if isinstance(val, Exception):
                raise val
            return val

        with patch("pipeline.build_chart.dispatch_asset", side_effect=_dispatch):
            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                rows, err = asyncio.run(
                    bc.dispatch_asset_with_retry(
                        "A9_sade_sati", "build-1", "chart-1", ["lahiri"], conn, {}
                    )
                )

        self.assertEqual(rows, 15)          # assertion 14a
        self.assertIsNone(err)              # assertion 14b
        self.assertEqual(mock_sleep.call_count, 2)  # assertion 15 — two sleeps

    def test_success_on_third_attempt_backoff_sequence(self):
        """Sleep calls use RETRY_DELAYS[0] then RETRY_DELAYS[1] (2s, 4s) (assertion 16)"""
        conn = _make_conn()
        side_effects = [ValueError("v1"), ValueError("v2"), 0]

        def _dispatch(*a, **kw):
            val = side_effects.pop(0)
            if isinstance(val, Exception):
                raise val
            return val

        with patch("pipeline.build_chart.dispatch_asset", side_effect=_dispatch):
            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                asyncio.run(
                    bc.dispatch_asset_with_retry(
                        "A10_msr", "build-1", "chart-1", ["lahiri"], conn, {}
                    )
                )
        self.assertEqual(
            mock_sleep.call_args_list,
            [call(bc.RETRY_DELAYS[0]), call(bc.RETRY_DELAYS[1])],
        )  # assertion 16


# ---------------------------------------------------------------------------
# 6. retry_count update in build_steps
# ---------------------------------------------------------------------------

class TestRetryCountUpdate(unittest.TestCase):
    def test_retry_count_updated_on_retry(self):
        """build_steps.retry_count += 1 is attempted for each retry (assertion 17)"""
        conn = _make_conn()
        side_effects = [RuntimeError("t1"), RuntimeError("t2"), 5]

        def _dispatch(*a, **kw):
            val = side_effects.pop(0)
            if isinstance(val, Exception):
                raise val
            return val

        with patch("pipeline.build_chart.dispatch_asset", side_effect=_dispatch):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                rows, err = asyncio.run(
                    bc.dispatch_asset_with_retry(
                        "A11_cdlm", "build-1", "chart-1", ["lahiri"], conn, {}
                    )
                )

        # Two retries happened → cursor().execute called at least twice for retry_count
        # (commit called for each retry)
        self.assertGreaterEqual(conn.commit.call_count, 2)   # assertion 17
        self.assertEqual(rows, 5)
        self.assertIsNone(err)


# ---------------------------------------------------------------------------
# 7. run_build integration — failed asset halts build
# ---------------------------------------------------------------------------

class TestRunBuildFailure(unittest.TestCase):
    def _build_conn(self, ayanamshas=None):
        """Returns a mock conn that returns ayanamshas for the first SELECT."""
        if ayanamshas is None:
            ayanamshas = ["lahiri"]
        conn = _make_conn()
        # First fetchone() call returns the ayanamshas row
        conn.cursor.return_value.fetchone.side_effect = [
            (ayanamshas,),   # SELECT ayanamshas
            ("running",),    # SELECT status (cancellation check — not cancelling)
        ]
        return conn

    def test_run_build_fails_when_retry_exhausted(self):
        """run_build returns False when dispatch_asset_with_retry exhausts (assertion 18)"""
        conn = _make_conn()
        conn.cursor.return_value.fetchone.side_effect = [
            (["lahiri"],),   # SELECT ayanamshas FROM builds
            ("running",),    # check_cancellation for A1_engine
            ("running",),    # check_cancellation for A2_*
        ]

        async def _fake_retry(*args, **kwargs):
            return 0, "RuntimeError: permanent failure"

        async def _fake_engine(*args, **kwargs):
            return {"lahiri": {"stub": True}}

        with patch.object(bc, "run_engine_parallel", _fake_engine):
            with patch.object(bc, "dispatch_asset_with_retry", _fake_retry):
                with patch("pipeline.build_chart.emit_event"):
                    with patch("pipeline.build_chart.emit_step_event"):
                        with patch("pipeline.build_chart.update_build_status"):
                            result = asyncio.run(bc.run_build("build-1", "chart-1", conn))

        self.assertFalse(result)  # assertion 18


# ---------------------------------------------------------------------------
# 8. run_build integration — all assets succeed (including retried ones)
# ---------------------------------------------------------------------------

class TestRunBuildSuccess(unittest.TestCase):
    def test_run_build_succeeds_when_all_assets_complete(self):
        """run_build returns True when all 14 assets succeed (assertion 19)"""
        conn = _make_conn()
        # Provide enough fetchone responses:
        # 1 for SELECT ayanamshas, then 14 for cancellation checks (one per DAG asset)
        fetchone_responses = [(["lahiri"],)] + [("running",)] * 14
        conn.cursor.return_value.fetchone.side_effect = fetchone_responses

        async def _fake_retry(*args, **kwargs):
            return 1, None  # always succeeds

        async def _fake_engine(*args, **kwargs):
            return {"lahiri": {"stub": True}}

        def _fake_load_birth(*args, **kwargs):
            return {"birth_date": "1984-02-05", "birth_time": "10:43",
                    "lat": 20.27, "lon": 85.84, "tz_offset": 5.5}

        with patch.object(bc, "run_engine_parallel", _fake_engine):
            with patch.object(bc, "dispatch_asset_with_retry", _fake_retry):
                with patch.object(bc, "load_birth_data", _fake_load_birth):
                    with patch("pipeline.build_chart.emit_event"):
                        with patch("pipeline.build_chart.emit_step_event"):
                            with patch("pipeline.build_chart.update_build_status"):
                                with patch("asyncio.sleep", new_callable=AsyncMock):
                                    result = asyncio.run(
                                        bc.run_build("build-1", "chart-1", conn)
                                    )

        self.assertTrue(result)  # assertion 19

    def test_dispatch_asset_with_retry_called_for_non_a1_assets(self):
        """dispatch_asset_with_retry is called for every non-A1 asset (assertion 20)"""
        conn = _make_conn()
        fetchone_responses = [(["lahiri"],)] + [("running",)] * 14
        conn.cursor.return_value.fetchone.side_effect = fetchone_responses

        call_log: list[str] = []

        async def _fake_retry(asset_id, *args, **kwargs):
            call_log.append(asset_id)
            return 1, None

        async def _fake_engine(*args, **kwargs):
            return {"lahiri": {"stub": True}}

        def _fake_load_birth(*args, **kwargs):
            return {"birth_date": "1984-02-05", "birth_time": "10:43",
                    "lat": 20.27, "lon": 85.84, "tz_offset": 5.5}

        with patch.object(bc, "run_engine_parallel", _fake_engine):
            with patch.object(bc, "dispatch_asset_with_retry", _fake_retry):
                with patch.object(bc, "load_birth_data", _fake_load_birth):
                    with patch("pipeline.build_chart.emit_event"):
                        with patch("pipeline.build_chart.emit_step_event"):
                            with patch("pipeline.build_chart.update_build_status"):
                                with patch("asyncio.sleep", new_callable=AsyncMock):
                                    asyncio.run(bc.run_build("build-1", "chart-1", conn))

        expected_non_a1 = [a for a in bc.DAG_ORDER if a != "A1_engine"]
        self.assertEqual(call_log, expected_non_a1)  # assertion 20


if __name__ == "__main__":
    unittest.main()
