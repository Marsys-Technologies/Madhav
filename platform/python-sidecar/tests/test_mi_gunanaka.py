"""
test_mi_gunanaka.py — hermetic test for mi_gunanaka's SV-6 fix
(ŚUDDHA-VĀCA parked finding, fixed by NIḤŚEṢA Track B).

`_publish_snapshot`'s snapshot_id construction sliced `chart_id[:8]` directly.
`chart_id` is annotated `str`, but the value actually delivered via
`ctx.config["chart_id"]` is not guaranteed to already be a plain `str` at the
call site — a `uuid.UUID` instance reaches here in practice for some callers.
`uuid.UUID` does not support subscripting, so that slice raised `'UUID' object
is not subscriptable`, caught non-fatally by `_publish_snapshot`'s own
try/except and logged as a warning — silently skipping the versioned
calibration snapshot publish for the affected chart every time it occurred,
with no build failure to surface it.

This test drives `_publish_snapshot` directly with a `uuid.UUID` chart_id and
asserts the INSERT actually executes (no swallowed exception, no
warning-only no-op) — the fix (`str(chart_id)[:8]`) makes the slice work for
both input shapes.
"""
from __future__ import annotations

import uuid

from pipeline.orchestrator.writers.mi_gunanaka import _publish_snapshot

NATIVE_CHART_ID_STR = "482012f1-710e-4a25-994a-93821f5871aa"


class _FakeCursor:
    def __init__(self, conn):
        self._conn = conn

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        if s.startswith("SAVEPOINT") or s.startswith("RELEASE SAVEPOINT") or s.startswith("ROLLBACK TO"):
            return
        if "INSERT INTO mimamsa_calibration_snapshot" in s:
            self._conn.inserted.append(params)


class _FakeConn:
    def __init__(self):
        self.inserted: list[tuple] = []

    def cursor(self, row_factory=None):
        return _FakeCursor(self)


def test_publish_snapshot_accepts_uuid_chart_id():
    """The SV-6 regression: a uuid.UUID chart_id (not a plain str) must not
    raise, and must still insert the snapshot row — the defect silently
    skipped this via a caught-and-logged TypeError."""
    conn = _FakeConn()
    chart_id = uuid.UUID(NATIVE_CHART_ID_STR)

    _publish_snapshot(
        conn, chart_id, cells=[{"family": "graha", "weight": 1.0}],
        formula_version="mi_gunanaka_v2.0",
    )

    assert len(conn.inserted) == 1
    snapshot_id, inserted_chart_id = conn.inserted[0][0], conn.inserted[0][1]
    assert snapshot_id.startswith("snap_482012f1_")
    assert inserted_chart_id == chart_id


def test_publish_snapshot_accepts_str_chart_id():
    """Regression cover: the ordinary str chart_id path must still behave
    identically after the str() normalization."""
    conn = _FakeConn()

    _publish_snapshot(
        conn, NATIVE_CHART_ID_STR, cells=[], formula_version="mi_gunanaka_v2.0",
    )

    assert len(conn.inserted) == 1
    snapshot_id = conn.inserted[0][0]
    assert snapshot_id.startswith("snap_482012f1_")
