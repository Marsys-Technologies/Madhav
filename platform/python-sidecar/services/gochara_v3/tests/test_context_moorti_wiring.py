"""
test_context_moorti_wiring.py — F-MOORTI-2 (L3-W3, N3): ClassContext.fetch()
now threads real kala_moorti_nirnaya rows into context.moorti_rows, the
field services/gochara_v3/mechanisms/w22_moorti_nirnaya.py's own
_find_overlapping_moorti has read via getattr(context, "moorti_rows", None)
since it was authored — this closes the data-wiring gap, not the
admission/ablation decision (w22_moorti_nirnaya.yaml stays
admission_state: candidate; that is a separate, later step).

Two-layer convention, same as this session's migration tests:
  1. DB-free unit tests against _fetch_moorti_rows directly, using a minimal
     fake connection (autocommit=True bypasses savepoint_scope's SAVEPOINT
     machinery entirely — the simplest correct fake for this function's
     needs).
  2. @pytest.mark.integration: proves, against the REAL production DB, that
     ClassContext.fetch() populates moorti_rows with real rows for the
     canonical chart, AND that feeding that real context into
     w22_moorti_nirnaya.compute() produces a genuine, non-1.0 modifier for at
     least one real ingress window — the actual end-to-end proof this wiring
     exists to make possible. Read-only: SELECT only, no writes, no
     conn.commit()/rollback() (mirrors this session's other DB-reading tests).
"""
from __future__ import annotations

import os

import pytest

from services.gochara_v3.context import _fetch_moorti_rows


class _FakeCursor:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _FakeConn:
    """Minimal fake: autocommit=True short-circuits savepoint_scope entirely
    (see _dbutil.savepoint_scope), so this fake never needs to answer
    SAVEPOINT/RELEASE SAVEPOINT/ROLLBACK TO SAVEPOINT statements."""

    def __init__(self, rows=None, raise_on_execute=False):
        self.autocommit = True
        self._rows = rows or []
        self._raise = raise_on_execute
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        if self._raise:
            raise RuntimeError("simulated DB failure")
        return _FakeCursor(self._rows)


# ── DB-free unit tests ───────────────────────────────────────────────────────

def test_none_conn_returns_empty():
    assert _fetch_moorti_rows(None, "chart-1", "lahiri_chitrapaksha") == []


def test_query_failure_degrades_to_empty_not_raise():
    conn = _FakeConn(raise_on_execute=True)
    assert _fetch_moorti_rows(conn, "chart-1", "lahiri_chitrapaksha") == []


def test_no_rows_returns_empty_list():
    conn = _FakeConn(rows=[])
    assert _fetch_moorti_rows(conn, "chart-1", "lahiri_chitrapaksha") == []


def test_real_row_shape_matches_mechanism_contract():
    """The exact shape services/gochara_v3/mechanisms/w22_moorti_nirnaya.py's
    _find_overlapping_moorti already expects: window_start, window_end,
    moorti_name, moorti_computed — accessed via .get() on each row dict."""
    conn = _FakeConn(rows=[
        {"window_start": "2026-01-01", "window_end": "2026-01-20",
         "moorti_name": "svarna", "moorti_computed": True},
        {"window_start": "2026-01-21", "window_end": "2026-02-10",
         "moorti_name": None, "moorti_computed": False},
    ])
    rows = _fetch_moorti_rows(conn, "chart-1", "lahiri_chitrapaksha")
    assert len(rows) == 2
    assert rows[0] == {
        "window_start": "2026-01-01", "window_end": "2026-01-20",
        "moorti_name": "svarna", "moorti_computed": True,
    }
    assert rows[1]["moorti_computed"] is False
    assert rows[1]["moorti_name"] is None


def test_tuple_rows_are_zipped_correctly():
    """Guards the dict(zip(...)) fallback path for a non-dict cursor row
    (matches _fetch_vedha_rows's own tuple-row fallback)."""
    conn = _FakeConn(rows=[("2026-03-01", "2026-03-15", "loha", True)])
    rows = _fetch_moorti_rows(conn, "chart-1", "lahiri_chitrapaksha")
    assert rows == [{
        "window_start": "2026-03-01", "window_end": "2026-03-15",
        "moorti_name": "loha", "moorti_computed": True,
    }]


def test_query_is_scoped_by_chart_id_and_ayanamsha_id():
    conn = _FakeConn(rows=[])
    _fetch_moorti_rows(conn, "chart-xyz", "raman")
    assert len(conn.executed) == 1
    sql, params = conn.executed[0]
    assert "kala_moorti_nirnaya" in sql
    assert "chart_id = %s" in sql
    assert "ayanamsha_id = %s" in sql
    assert params == ["chart-xyz", "raman"]


# ── live integration (excluded by -m "not integration"; run manually) ──────

LIVE_DSN = os.environ.get("DATABASE_URL", "")
CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"


def _live_conn_or_skip():
    import psycopg

    try:
        conn = psycopg.connect(LIVE_DSN, connect_timeout=10, row_factory=psycopg.rows.dict_row)
    except Exception:
        pytest.skip("live Cloud SQL proxy (127.0.0.1:5433) not reachable in this environment")
    return conn


@pytest.mark.integration
def test_fetch_moorti_rows_returns_real_rows_live():
    conn = _live_conn_or_skip()
    try:
        rows = _fetch_moorti_rows(conn, CANONICAL_CHART_ID, "lahiri_chitrapaksha")
        if not rows:
            pytest.skip("kala_moorti_nirnaya has no rows for the canonical chart in this environment")
        assert all(
            set(r.keys()) == {"window_start", "window_end", "moorti_name", "moorti_computed"}
            for r in rows
        )
        assert any(r["moorti_computed"] for r in rows), (
            "expected at least one moorti_computed=true row for the canonical chart"
        )
    finally:
        conn.close()


@pytest.mark.integration
def test_moorti_mechanism_produces_a_real_modifier_end_to_end_live():
    """The actual proof this wiring exists to make possible: a genuinely
    fetched context, fed into the already-tested w22_moorti_nirnaya.compute(),
    produces a real (non-1.0) modifier for at least one covered instant —
    not just that the plumbing typechecks."""
    from services.gochara_v3.context import _fetch_moorti_rows
    from services.gochara_v3.mechanisms.w22_moorti_nirnaya import compute, _jd_to_date

    conn = _live_conn_or_skip()
    try:
        rows = _fetch_moorti_rows(conn, CANONICAL_CHART_ID, "lahiri_chitrapaksha")
        computed_rows = [r for r in rows if r["moorti_computed"]]
        if not computed_rows:
            pytest.skip("no moorti_computed=true rows for the canonical chart in this environment")

        class _Ctx:
            chart_id = CANONICAL_CHART_ID
            moorti_rows = rows

        from datetime import date

        # JD for the midpoint of a real computed window, so it definitely
        # falls inside it regardless of truncation at either end.
        target_row = computed_rows[0]
        start = date.fromisoformat(target_row["window_start"])
        end = date.fromisoformat(target_row["window_end"])
        mid = start + (end - start) // 2
        # Julian Day for `mid` at 00:00 UTC (inverse of w22's own _jd_to_date).
        t_jd = (mid - date(1970, 1, 1)).days + 2440587.5

        result = compute(_Ctx(), t_jd, enabled=True)
        assert result.detail.get("reason") == "moorti_quality_applied", result.detail
        assert result.modifier != 1.0, (
            "expected a real, non-neutral modifier once real moorti data is wired in"
        )
    finally:
        conn.close()
