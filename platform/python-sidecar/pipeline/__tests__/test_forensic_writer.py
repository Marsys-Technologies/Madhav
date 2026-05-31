"""
test_forensic_writer.py — Contract tests for A2_forensic_render writer.

STOP — ROOT CAUSE IDENTIFIED (Pariksha second-pass, 2026-06-01):

    forensic_writer.py is a STUB. The file explicitly states:
        "STUB: Emits build events but writes no data."
        "Real implementation in Stream F sessions F-01 through F-14."

    This is RC-001: the writer returns 0 by design. There is no silent
    exception, no guard clause, no UUID type mismatch — the stub is the
    entire implementation. Fixing this requires implementing A2 forensic
    render from scratch (Stream F, 14 sessions). This scope is outside
    the Pariksha second-pass boundary and must be operator-approved before
    any Stream F work begins.

    Issues that will self-resolve once Stream F is implemented:
        I-001 (A2_forensic_render 0 rows)
        I-002 (A5_sensitive_points 0 rows — likely a separate stub)
        I-003 (A8_t1_structural 0 rows — likely a separate stub)
        I-004 (A9_sade_sati 0 rows — likely a separate stub)
    Issues that cascade from these:
        I-005, I-006, I-008, I-010 (L2.5 sentinels — RC-002)

The tests below document the CONTRACT the real implementation must satisfy.
They will fail until Stream F is implemented. Mark them xfail so CI does not
go red but the gap is visible.
"""
from __future__ import annotations

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pipeline.writers.forensic_writer import write, ASSET_ID, ASSET_LABEL


# ---------------------------------------------------------------------------
# Current stub behaviour — these must remain stable
# ---------------------------------------------------------------------------

class TestForensicWriterStubBehaviour:
    """Pins the stub's observable contract so regressions are detectable."""

    def test_asset_id(self):
        assert ASSET_ID == "A2_forensic_render"

    def test_asset_label_is_not_empty(self):
        assert ASSET_LABEL

    def test_stub_returns_zero_rows(self):
        """Stub always returns 0 — this test documents the current (broken) state."""
        result = write(
            build_id="test-build",
            chart_id="test-chart",
            ayanamsha_id="lahiri",
            chart_output={"grahas": []},
            conn=None,
        )
        assert result == 0

    def test_stub_does_not_raise(self):
        """Stub must not raise even with minimal input."""
        write(
            build_id="test-build",
            chart_id="test-chart",
            ayanamsha_id="kp",
            chart_output={},
            conn=None,
        )


# ---------------------------------------------------------------------------
# Contract tests — what the real implementation MUST satisfy.
# These are marked xfail until Stream F delivers the real writer.
# ---------------------------------------------------------------------------

@pytest.mark.xfail(
    strict=True,
    reason="forensic_writer.py is a stub (Stream F not yet implemented). "
           "Remove xfail when real writer lands.",
)
class TestForensicWriterContract:

    def test_run_writes_non_zero_rows_for_real_chart(self):
        """
        Given a valid chart_output with planet positions, the writer must
        persist at least one row (planet/house/lagna category) to chart_facts.
        Currently fails because the stub always returns 0.
        """
        chart_output = {
            "grahas": [
                {"name": "SUN", "longitude_deg": 291.96, "sign": "Capricorn"},
                {"name": "MOON", "longitude_deg": 332.7, "sign": "Aquarius"},
            ],
            "lagna": {"longitude_deg": 50.0, "sign": "Taurus"},
        }
        result = write(
            build_id="stream-f-test-build",
            chart_id="362f9f17-95a5-490b-a5a7-027d3e0efda0",
            ayanamsha_id="lahiri",
            chart_output=chart_output,
            conn=None,
        )
        assert result > 0, (
            "forensic_writer.write() must return a positive row count when given "
            "valid planet data. Got 0 — stub has not been replaced."
        )

    def test_run_conn_none_is_dry_run_not_zero(self):
        """
        When conn=None the writer must behave as a dry-run: return the number
        of rows that WOULD have been written, without touching the DB.
        """
        chart_output = {
            "grahas": [{"name": "SUN", "longitude_deg": 291.96}],
        }
        result = write(
            build_id="dry-run-test",
            chart_id="test-chart",
            ayanamsha_id="lahiri",
            chart_output=chart_output,
            conn=None,
        )
        assert result > 0

    def test_run_does_not_silently_swallow_db_errors(self):
        """
        If the DB write fails, the writer must raise — not silently return 0.
        A bare `except: pass` is a critical anti-pattern that masked this bug.
        """
        import unittest.mock as mock
        bad_conn = mock.MagicMock()
        bad_conn.cursor.side_effect = RuntimeError("simulated DB error")

        with pytest.raises((RuntimeError, Exception)):
            write(
                build_id="error-test-build",
                chart_id="test-chart",
                ayanamsha_id="lahiri",
                chart_output={"grahas": [{"name": "SUN", "longitude_deg": 291.96}]},
                conn=bad_conn,
            )
