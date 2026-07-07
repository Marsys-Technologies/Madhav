"""
test_mi_jivanaghatana.py — DB-path tests for the L5 Mīmāṃsā root writer.

The native-only LEL markdown branch was removed (native ruling: STRICT-ZERO
NATIVE_CHART_ID under brahmagyan/mimamsa + no markdown reads at runtime). The
chart-scoped `life_events` DB read (WHERE chart_id = $1) is now the ONLY source
path, so every chart — including the native — is sourced identically and no
chart can ingest another chart's events. These tests exercise that single path:
native ingestion, graceful empty, and the presence-based anti-masking guard.
"""
from __future__ import annotations

import logging

import pytest

from pipeline.orchestrator.writers.mi_jivanaghatana import MiJivanaghatanaWriter

# Chart ids are test-local literals (never sourced from the writer module).
NATIVE_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
NON_NATIVE_CHART_ID = "1c826d5a-0000-4000-8000-000000000000"


# ── DB-path fakes (model the queries run() issues) ───────────────────────────

class _FakeCursor:
    """Answers the life_events queries run() issues, incl. the presence COUNT.

    `count` overrides the reported chart-scoped count (defaults to the number of
    source rows). It can be set independently to exercise the defensive
    anti-masking guard (count > 0 while the source read returns 0)."""
    def __init__(self, life_events_rows, count=None):
        self._life_events_rows = life_events_rows
        self._count = count if count is not None else len(life_events_rows)
        self._result = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        if "information_schema.columns" in s:
            self._result = [{"column_name": "chart_id"}, {"column_name": "event_id"}]
        elif "COUNT(*)" in s.upper():
            self._result = [(self._count,)]
        elif "FROM life_events WHERE chart_id" in s:
            self._result = list(self._life_events_rows)
        else:
            self._result = []

    def fetchall(self):
        return list(self._result)

    def fetchone(self):
        return self._result[0] if self._result else None

    def executemany(self, sql, params_list):
        self._result = []


class _FakeConn:
    def __init__(self, life_events_rows=(), count=None):
        self._life_events_rows = list(life_events_rows)
        self._count = count

    def cursor(self, row_factory=None):
        return _FakeCursor(self._life_events_rows, self._count)


class _FakeCtx:
    def __init__(self, chart_id, db_conn, dry_run=False):
        self.config = {"chart_id": chart_id}
        self.db_conn = db_conn
        self.dry_run = dry_run


def _life_event_row(event_id="EVT.2020.01.01.01"):
    """A minimal life_events DB row shaped like the columns run() consumes."""
    return {
        "event_id": event_id,
        "event_date": "2020-01-01",
        "category": "career",
        "subcategory": "role_change",
        "magnitude": "significant",
        "disclosure_timing": "contemporaneous",
        "shaped_predictor": False,
    }


# ── DB-path behaviour ────────────────────────────────────────────────────────

def test_native_chart_sourced_from_db_ingests_events(monkeypatch):
    """The native chart is sourced from its own life_events DB rows (no markdown)."""
    monkeypatch.setattr(
        "pipeline.orchestrator.writers.mi_jivanaghatana._lookup_event_class",
        lambda conn, category, subcategory: None,
    )
    writer = MiJivanaghatanaWriter()
    ctx = _FakeCtx(NATIVE_CHART_ID, _FakeConn(life_events_rows=[_life_event_row()]))
    result = writer.run(ctx)

    assert result.rows_inserted == 1


def test_non_native_chart_sourced_from_db_ingests_events(monkeypatch):
    """A non-native chart is sourced identically from its own life_events rows."""
    monkeypatch.setattr(
        "pipeline.orchestrator.writers.mi_jivanaghatana._lookup_event_class",
        lambda conn, category, subcategory: None,
    )
    writer = MiJivanaghatanaWriter()
    ctx = _FakeCtx(
        NON_NATIVE_CHART_ID,
        _FakeConn(life_events_rows=[_life_event_row("EVT.2021.06.15.01")]),
    )
    result = writer.run(ctx)

    assert result.rows_inserted == 1


def test_zero_event_chart_is_success_not_exception():
    """A chart with no life_events rows builds zero provenance rows (never raises)."""
    writer = MiJivanaghatanaWriter()
    ctx = _FakeCtx(NON_NATIVE_CHART_ID, _FakeConn(life_events_rows=[]))
    result = writer.run(ctx)

    assert result.rows_inserted == 0
    assert "zero provenance rows" in result.notes


def test_genuinely_empty_chart_is_healthy_no_warning(caplog):
    """BA-P4 R2.2/W2.2 presence-branching: a chart with ZERO life_events rows
    (count 0) is a HEALTHY empty build — no anti-masking warning. This is the
    Abhinandan / pre-intake case: structural, not an error."""
    writer = MiJivanaghatanaWriter()
    ctx = _FakeCtx(NATIVE_CHART_ID, _FakeConn(life_events_rows=[], count=0))
    with caplog.at_level(logging.WARNING):
        result = writer.run(ctx)

    assert result.rows_inserted == 0
    assert not any("built ZERO" in rec.message for rec in caplog.records), \
        "a genuinely empty chart must NOT trigger the anti-masking warning"


def test_present_rows_but_zero_build_warns_presence_based(caplog):
    """Defensive anti-masking (presence, not identity): if a chart's life_events
    count is > 0 but the build sourced zero (a sourcing/packaging bug), warn
    loudly rather than silently succeed. Any chart, not just the native."""
    writer = MiJivanaghatanaWriter()
    # Inconsistent state the guard exists to catch: COUNT says 57, source read []
    ctx = _FakeCtx(NON_NATIVE_CHART_ID, _FakeConn(life_events_rows=[], count=57))
    with caplog.at_level(logging.WARNING):
        result = writer.run(ctx)

    assert result.rows_inserted == 0
    assert any(
        "has 57 life_events rows but" in rec.message and "ZERO" in rec.message
        for rec in caplog.records
    ), "a chart with rows present but a zero build must warn (presence-based anti-masking)"


def test_dry_run_reports_would_insert_without_writing(monkeypatch):
    """dry_run reports the sourced count without inserting."""
    writer = MiJivanaghatanaWriter()
    ctx = _FakeCtx(
        NATIVE_CHART_ID,
        _FakeConn(life_events_rows=[_life_event_row()]),
        dry_run=True,
    )
    result = writer.run(ctx)

    assert result.rows_inserted == 1
    assert "dry_run" in result.notes
