"""WAVE-2 (L0 wave survey side finding): bg_ephemeris' INSERT must write every column its compute step emits.

Lives under tests/ (collected by the CI pytest step) rather than next to
pipeline/orchestrator/writers/tests/test_bg_ephemeris_writer.py, which no CI test selection collects.
"""
from __future__ import annotations

import sys
from contextlib import contextmanager
from datetime import date
from types import SimpleNamespace

import pytest

from pipeline.orchestrator.writers import ContextSpec
from pipeline.orchestrator.writers.bg_ephemeris import BgEphemerisWriter


# ── WAVE side finding (L0 wave survey 6): the INSERT must write every column it computes ──
#
# `_compute_positions_for_date` computes `node_mode` (Rahu/Ketu 'true' node, NULL for the other
# seven bodies) and `epoch_convention` on every row, and the legacy bootstrap COPY path stores
# both, but this writer's INSERT omitted them: a row inserted by a governed rebuild had NULL for
# both (`ephemeris_daily.epoch_convention` has no default) and an existing row could never be
# repaired because the conflict guard did not compare them either.

import os
import re

_WRITE_PLACEHOLDERS = re.compile(r"%\((\w+)\)s")


def _fake_swe():
    def calc_ut(_jd, swe_id, _flags):
        return ((100.0 + swe_id, 0.5, 1.0, 0.25 if swe_id != 11 else -0.05), 0)

    return SimpleNamespace(
        julday=lambda *_a: 2461278.0, calc_ut=calc_ut, set_ephe_path=lambda *_a: None,
        FLG_SWIEPH=2, FLG_SPEED=256,
    )


def _patched_writer_env(monkeypatch, cursor_cls, day=date(2026, 8, 26)):
    from brahmagyan import l0_ephemeris
    from pipeline.orchestrator.writers import bg_sky_calendar

    monkeypatch.setitem(sys.modules, "swisseph", _fake_swe())
    monkeypatch.setattr(l0_ephemeris, "BUILD_START", day)
    monkeypatch.setattr(l0_ephemeris, "BUILD_END", day)
    monkeypatch.setattr(l0_ephemeris, "_resolve_ephe_path", lambda: "/verified/se1")
    monkeypatch.setattr(bg_sky_calendar, "_require_swiss_file_backend", lambda *_a: None)
    monkeypatch.setattr(bg_sky_calendar, "_require_pinned_ephemeris_files", lambda *_a: None)

    class Conn:
        @contextmanager
        def cursor(self):
            yield cursor_cls

    return Conn()


def test_insert_writes_every_column_the_compute_step_emits(monkeypatch):
    class Rec:
        rowcount = 9
        sql = ""
        rows: list = []

        def executemany(self, sql, rows):
            Rec.sql, Rec.rows = sql, list(rows)

    conn = _patched_writer_env(monkeypatch, Rec())
    BgEphemerisWriter().run(ContextSpec(asset_id="bg_ephemeris", build_id="cols", db_conn=conn))

    computed = set(Rec.rows[0])
    placeholders = set(_WRITE_PLACEHOLDERS.findall(Rec.sql))
    assert {"node_mode", "epoch_convention"} <= computed          # the compute step does emit them
    assert placeholders == computed, (placeholders ^ computed)    # ...and the INSERT writes all of them
    insert_cols = re.search(r"INSERT INTO ephemeris_daily\s*\((.*?)\)\s*VALUES", Rec.sql, re.S).group(1)
    assert {c.strip() for c in insert_cols.split(",")} == computed
    by_body = {r["body"]: r for r in Rec.rows}
    assert by_body["Rahu"]["node_mode"] == by_body["Ketu"]["node_mode"] == "true"
    assert all(by_body[b]["node_mode"] is None for b in by_body if b not in ("Rahu", "Ketu"))
    assert {r["epoch_convention"] for r in Rec.rows} == {"noon_ut"}


def test_conflict_guard_repairs_a_row_whose_node_mode_or_epoch_is_wrong(monkeypatch):
    class Rec:
        rowcount = 0
        sql = ""

        def executemany(self, sql, _rows):
            Rec.sql = sql

    conn = _patched_writer_env(monkeypatch, Rec())
    BgEphemerisWriter().run(ContextSpec(asset_id="bg_ephemeris", build_id="guard", db_conn=conn))
    update_set = Rec.sql.split("DO UPDATE SET", 1)[1].split("WHERE ROW(", 1)[0]
    assert "node_mode = EXCLUDED.node_mode" in update_set
    assert "epoch_convention = EXCLUDED.epoch_convention" in update_set
    old, new = Rec.sql.split("WHERE ROW(", 1)[1].split(") IS DISTINCT FROM ROW(")
    for col in ("node_mode", "epoch_convention"):
        assert f"ephemeris_daily.{col}" in old
        assert f"EXCLUDED.{col}" in new


_PG = os.environ.get("EPHEMERIS_WRITER_TEST_DATABASE_URL")


@pytest.mark.skipif(not _PG, reason="EPHEMERIS_WRITER_TEST_DATABASE_URL not configured")
def test_real_postgres_stores_node_mode_and_epoch_and_repairs_old_rows(monkeypatch):
    import psycopg
    from psycopg.rows import dict_row

    assert _PG.rsplit("/", 1)[-1].endswith("_test"), "scratch database only (name must end _test)"
    with psycopg.connect(_PG, row_factory=dict_row) as conn:
        conn.execute("""
            DROP TABLE IF EXISTS ephemeris_daily;
            CREATE TABLE ephemeris_daily (
              id uuid DEFAULT gen_random_uuid(), date date NOT NULL, body text NOT NULL,
              ayanamsha_id text NOT NULL DEFAULT 'tropical', tropical_longitude double precision NOT NULL,
              latitude double precision NOT NULL DEFAULT 0, speed_dps double precision NOT NULL DEFAULT 0,
              is_retrograde boolean NOT NULL DEFAULT false, sign_number int, degree_in_sign double precision,
              nakshatra_number int, source_citation text NOT NULL DEFAULT 'x',
              computed_at timestamptz NOT NULL DEFAULT now(), node_mode text, epoch_convention text,
              PRIMARY KEY (date, body, ayanamsha_id));
        """)

        class Cur:  # adapt psycopg's cursor to the `with conn.cursor() as cur` shape and rowcount
            def __init__(self, c): self._c = c
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def executemany(self, sql, rows):
                self._c.executemany(sql, rows)
                self.rowcount = self._c.rowcount

        class Conn:
            def cursor(self): return Cur(conn.cursor())

        _patched_writer_env(monkeypatch, None)       # installs the fake swe + path guards
        run = lambda: BgEphemerisWriter().run(ContextSpec(asset_id="bg_ephemeris", build_id="pg", db_conn=Conn()))

        run()
        got = {r["body"]: (r["node_mode"], r["epoch_convention"]) for r in conn.execute("select * from ephemeris_daily")}
        assert got["Rahu"] == got["Ketu"] == ("true", "noon_ut")
        assert got["Sun"] == got["Saturn"] == (None, "noon_ut")

        # rows the OLD writer left behind: NULL node_mode / epoch -> a rerun repairs exactly those
        conn.execute("update ephemeris_daily set node_mode=null, epoch_convention=null where body in ('Rahu','Ketu','Sun')")
        assert run().rows_inserted == 3
        got = {r["body"]: (r["node_mode"], r["epoch_convention"]) for r in conn.execute("select * from ephemeris_daily")}
        assert got["Rahu"] == ("true", "noon_ut") and got["Sun"] == (None, "noon_ut")
        # converged: nothing left to write
        assert run().rows_inserted == 0
        conn.rollback()
