from __future__ import annotations

import sys
from contextlib import contextmanager
from datetime import date
from types import SimpleNamespace

import pytest

from pipeline.orchestrator.writers import ContextSpec
from pipeline.orchestrator.writers.bg_ephemeris import BgEphemerisWriter


class _Cursor:
    rowcount = 0

    def executemany(self, *_args, **_kwargs):
        return None


class _Connection:
    @contextmanager
    def cursor(self):
        yield _Cursor()


def test_writer_fails_closed_when_swisseph_is_unavailable(monkeypatch):
    """Removing the required compute dependency must mark the build failed."""
    monkeypatch.setitem(sys.modules, "swisseph", None)

    with pytest.raises(RuntimeError, match="requires pyswisseph"):
        BgEphemerisWriter().run(ContextSpec(
            asset_id="bg_ephemeris",
            build_id="missing-swisseph",
            db_conn=_Connection(),
        ))


def test_writer_fails_closed_when_pinned_ephemeris_corpus_is_missing(monkeypatch):
    """Pyswisseph's analytic fallback is not an accepted build dependency."""
    from brahmagyan import l0_ephemeris

    monkeypatch.setitem(sys.modules, "swisseph", SimpleNamespace())
    monkeypatch.setattr(l0_ephemeris, "_resolve_ephe_path", lambda: None)

    with pytest.raises(RuntimeError, match="pinned Swiss Ephemeris"):
        BgEphemerisWriter().run(ContextSpec(
            asset_id="bg_ephemeris",
            build_id="missing-se1-corpus",
            db_conn=_Connection(),
        ))


def test_writer_propagates_partial_computation_failure(monkeypatch):
    """A compute failure after the writer starts must escape for rollback."""
    from brahmagyan import l0_ephemeris
    from pipeline.orchestrator.writers import bg_sky_calendar

    fake_swe = SimpleNamespace()
    monkeypatch.setitem(sys.modules, "swisseph", fake_swe)
    monkeypatch.setattr(l0_ephemeris, "_resolve_ephe_path", lambda: "/verified/se1")
    monkeypatch.setattr(bg_sky_calendar, "_require_swiss_file_backend", lambda *_args: None)
    monkeypatch.setattr(bg_sky_calendar, "_require_pinned_ephemeris_files", lambda *_args: None)
    monkeypatch.setattr(
        l0_ephemeris,
        "_compute_positions_for_date",
        lambda *_args: (_ for _ in ()).throw(ValueError("ephemeris computation exploded")),
    )

    with pytest.raises(ValueError, match="ephemeris computation exploded"):
        BgEphemerisWriter().run(ContextSpec(
            asset_id="bg_ephemeris",
            build_id="partial-computation",
            db_conn=_Connection(),
        ))


def test_writer_repairs_stale_rows_on_natural_key_conflict(monkeypatch):
    """A rerun must converge semantic columns, not preserve a stale row."""
    from brahmagyan import l0_ephemeris
    from pipeline.orchestrator.writers import bg_sky_calendar

    class RecordingCursor:
        rowcount = 1
        sql = ""

        def executemany(self, sql, _rows):
            self.sql = sql

    cursor = RecordingCursor()

    class RecordingConnection:
        @contextmanager
        def cursor(self):
            yield cursor

    monkeypatch.setitem(sys.modules, "swisseph", SimpleNamespace())
    monkeypatch.setattr(l0_ephemeris, "BUILD_START", date(2026, 8, 26))
    monkeypatch.setattr(l0_ephemeris, "BUILD_END", date(2026, 8, 26))
    monkeypatch.setattr(l0_ephemeris, "_resolve_ephe_path", lambda: "/verified/se1")
    monkeypatch.setattr(bg_sky_calendar, "_require_swiss_file_backend", lambda *_args: None)
    monkeypatch.setattr(bg_sky_calendar, "_require_pinned_ephemeris_files", lambda *_args: None)
    monkeypatch.setattr(
        l0_ephemeris,
        "_compute_positions_for_date",
        lambda *_args: [{"date": date(2026, 8, 26)}],
    )

    BgEphemerisWriter().run(ContextSpec(
        asset_id="bg_ephemeris",
        build_id="repair-stale-row",
        db_conn=RecordingConnection(),
    ))

    assert "DO UPDATE SET" in cursor.sql
    assert "tropical_longitude = EXCLUDED.tropical_longitude" in cursor.sql
    assert "ephemeris_daily.source_citation" in cursor.sql
    assert "IS DISTINCT FROM" in cursor.sql
