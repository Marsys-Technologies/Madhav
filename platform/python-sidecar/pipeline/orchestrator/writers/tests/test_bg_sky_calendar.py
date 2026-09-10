"""Tests for the bg_sky_calendar writer.

Two tiers, matching the project's test-writer convention (see
test_bg_cohort.py):

1. Offline (always runs, no DB required; swisseph IS required and is a
   project dependency — same as every other L0 astronomical writer's tests):
   proves the horizon function is a pure, deterministic transform, and that
   the four event-family scan functions produce well-formed, internally
   consistent events over a small real window.
2. Live (skipped unless DATABASE_URL is set): runs the writer against a real
   DB connection and asserts row counts, idempotency, and schema shape.
"""
from __future__ import annotations

import os
import uuid
from datetime import date

import pytest
import psycopg

from pipeline.orchestrator.writers.bg_sky_calendar import (
    BgSkyCalendarWriter,
    DOUBLE_TRANSIT_PAIRS,
    FORWARD_HORIZON_YEARS,
    HISTORY_START,
    INGRESS_PLANETS,
    STATION_PLANETS,
    compute_horizon,
    scan_double_transits,
    scan_eclipses,
    scan_ingresses,
    scan_stations,
)
from pipeline.orchestrator.writers import ContextSpec

swe = pytest.importorskip("swisseph", reason="swisseph is a project dependency; skip only if truly absent")


# ── Offline tests: compute_horizon (pure function) ────────────────────────────

def test_compute_horizon_is_deterministic():
    a = compute_horizon(today=date(2026, 7, 29))
    b = compute_horizon(today=date(2026, 7, 29))
    assert a == b


def test_compute_horizon_history_start_fixed():
    start, _ = compute_horizon(today=date(2026, 7, 29))
    assert start == HISTORY_START == date(1900, 1, 1)


def test_compute_horizon_forward_is_today_plus_n_years():
    start, end = compute_horizon(today=date(2026, 7, 29))
    assert end.year == 2026 + FORWARD_HORIZON_YEARS
    assert end.month == 7
    assert end.day == 29


def test_compute_horizon_rolls_forward_with_today():
    """A later 'today' must produce a later forward edge -- this is the
    'rolling horizon, re-runnable to extend' property from the module
    docstring."""
    _, end_2026 = compute_horizon(today=date(2026, 7, 29))
    _, end_2028 = compute_horizon(today=date(2028, 7, 29))
    assert end_2028 > end_2026


def test_compute_horizon_leap_day_edge_case():
    """Feb 29 -> a non-leap target year must not raise."""
    start, end = compute_horizon(today=date(2024, 2, 29))
    assert end.day in (28, 29)


# ── Offline tests: event-family scope constants ───────────────────────────────

def test_ingress_planets_are_the_nine_grahas():
    assert set(INGRESS_PLANETS) == {
        "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
    }


def test_station_planets_exclude_luminaries_and_nodes():
    """Sun/Moon never station; Rahu/Ketu are deliberately excluded (module
    docstring 'Rahu/Ketu decision')."""
    assert set(STATION_PLANETS) == {"Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
    assert "Sun" not in STATION_PLANETS
    assert "Moon" not in STATION_PLANETS
    assert "Rahu" not in STATION_PLANETS
    assert "Ketu" not in STATION_PLANETS


def test_double_transit_pairs_include_jupiter_saturn():
    """The brief's own paradigm case ('Guru-Śani double-transit')."""
    assert ("Jupiter", "Saturn") in DOUBLE_TRANSIT_PAIRS


# ── Offline tests: real swisseph scans over a small window ───────────────────
# These call real pyswisseph (via pipeline.transit_search) over a short window
# so they run fast without a DB. This is the same "real computation, no DB"
# tier bg_cohort's compute_synthetic_positions tests use.

@pytest.fixture(scope="module")
def small_window():
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    start_jd = swe.julday(2020, 1, 1, 0.0)
    end_jd = swe.julday(2022, 1, 1, 0.0)  # 2 years -- enough for fast-planet ingresses
    return start_jd, end_jd


def test_scan_ingresses_moon_produces_many_events(small_window):
    """Moon crosses a sign roughly every ~2.25 days -- 2 years must yield
    on the order of a few hundred Moon ingress events."""
    start_jd, end_jd = small_window
    rows = scan_ingresses(swe, start_jd, end_jd)
    moon_rows = [r for r in rows if r.primary_body == "Moon"]
    assert len(moon_rows) > 100, f"expected >100 Moon ingresses in 2y, got {len(moon_rows)}"
    for r in moon_rows:
        assert r.event_type == "ingress"
        assert r.sign in (
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
        )
        assert r.secondary_body is None


def test_scan_ingresses_events_sorted_and_signs_progress(small_window):
    """Consecutive Sun ingresses over a short window must be in increasing
    sign order (mod 12) -- a basic sanity check that the scan isn't
    fabricating or misordering events.

    Uses `sign` (== the loop's own `target_sign`, per the writer's fix for
    the find_ingress_events floating-point boundary artifact documented in
    scan_ingresses' docstring) rather than re-deriving from the bisected
    longitude, which is the exact field this test would otherwise be
    vulnerable to false-failing on."""
    start_jd, end_jd = small_window
    rows = scan_ingresses(swe, start_jd, end_jd)
    sun_rows = sorted([r for r in rows if r.primary_body == "Sun"], key=lambda r: r.event_jd)
    assert len(sun_rows) >= 20  # ~24 solar ingresses over 2 years
    signs = (
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    )
    for a, b in zip(sun_rows, sun_rows[1:]):
        idx_a, idx_b = signs.index(a.sign), signs.index(b.sign)
        assert (idx_b - idx_a) % 12 == 1, "Sun must move to the NEXT sign each ingress"


def test_scan_ingresses_sign_always_matches_target_sign(small_window):
    """Regression test for the find_ingress_events boundary artifact: `sign`
    must always equal `detail['target_sign']` (this is what the writer's fix
    guarantees, sidestepping the re-derived-from-longitude field)."""
    start_jd, end_jd = small_window
    rows = scan_ingresses(swe, start_jd, end_jd)
    assert rows, "expected at least one ingress event in the 2-year window"
    for r in rows:
        assert r.sign == r.detail["target_sign"], (
            f"sign {r.sign!r} != target_sign {r.detail['target_sign']!r} for "
            f"{r.primary_body} at jd={r.event_jd}"
        )


def test_scan_stations_only_the_five_classical_planets(small_window):
    start_jd, end_jd = small_window
    rows = scan_stations(swe, start_jd, end_jd)
    bodies = {r.primary_body for r in rows}
    assert bodies.issubset(set(STATION_PLANETS))
    for r in rows:
        assert r.event_type == "station"
        assert r.detail["station_type"] in ("retrograde", "direct")


def test_scan_eclipses_over_two_years_finds_solar_and_lunar(small_window):
    start_jd, end_jd = small_window
    rows = scan_eclipses(swe, start_jd, end_jd)
    solar = [r for r in rows if r.event_type == "eclipse_solar"]
    lunar = [r for r in rows if r.event_type == "eclipse_lunar"]
    # Roughly 4-5 eclipses/year combined -> ~8-10 in 2 years; assert loosely.
    assert len(solar) >= 2, f"expected >=2 solar eclipses in 2y, got {len(solar)}"
    assert len(lunar) >= 2, f"expected >=2 lunar eclipses in 2y, got {len(lunar)}"
    for r in solar:
        assert r.primary_body == "Sun" and r.secondary_body == "Moon"
        assert r.detail["eclipse_type"] in ("total", "annular", "partial", "annular_total", "unknown")
    for r in lunar:
        assert r.primary_body == "Moon" and r.secondary_body == "Sun"
        assert r.detail["eclipse_type"] in ("total", "partial", "penumbral", "unknown")


def test_scan_double_transits_jupiter_saturn(small_window):
    """Jupiter-Saturn conjunction is rare (~20y cycle) -- a 2y window may or
    may not contain one; assert the function runs cleanly and any returned
    event is well-formed."""
    start_jd, end_jd = small_window
    rows = scan_double_transits(swe, start_jd, end_jd)
    for r in rows:
        assert r.event_type == "double_transit"
        assert r.primary_body == "Jupiter"
        assert r.secondary_body == "Saturn"


def test_scan_double_transits_finds_the_2020_great_conjunction():
    """The Dec 21, 2020 Jupiter-Saturn conjunction is a well-known real
    event -- a positive-control check that this isn't a no-op scan."""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    start_jd = swe.julday(2020, 1, 1, 0.0)
    end_jd = swe.julday(2021, 1, 1, 0.0)
    rows = scan_double_transits(swe, start_jd, end_jd)
    assert len(rows) >= 1, "expected the 2020 Jupiter-Saturn conjunction to be found"


# ── Offline: writer registration + dry_run ────────────────────────────────────

def test_writer_registered():
    """bg_sky_calendar must be discoverable via @register('bg_sky_calendar')."""
    from pipeline.orchestrator.writers import get_writer
    writer_cls = get_writer("bg_sky_calendar")
    assert writer_cls is BgSkyCalendarWriter
    assert writer_cls.asset_id == "bg_sky_calendar"


def test_writer_dry_run_no_db_needed():
    """dry_run=True must short-circuit before any DB/swisseph work — no live
    conn required."""
    writer = BgSkyCalendarWriter()
    ctx = ContextSpec(
        asset_id="bg_sky_calendar", build_id=str(uuid.uuid4()), db_conn=None, dry_run=True,
    )
    result = writer.run(ctx)
    assert result.asset_id == "bg_sky_calendar"
    assert result.rows_inserted == 0
    assert result.notes == "dry_run"


def test_writer_fails_closed_before_scanning_without_swiss_ephemeris_files(monkeypatch):
    """Removing the production .se1 path must raise, not compute with Moshier
    while persisting rows that still claim Swiss-file provenance."""
    import brahmagyan.l0_ephemeris as l0_ephemeris
    import pipeline.orchestrator.writers.bg_sky_calendar as sky_calendar

    monkeypatch.setattr(l0_ephemeris, "_resolve_ephe_path", lambda: None)

    def scan_must_not_run(*_args, **_kwargs):
        raise AssertionError("sky scan reached after the required .se1 path was absent")

    monkeypatch.setattr(sky_calendar, "scan_ingresses", scan_must_not_run)

    ctx = ContextSpec(
        asset_id="bg_sky_calendar",
        build_id=str(uuid.uuid4()),
        db_conn=None,
    )
    with pytest.raises(RuntimeError, match=r"Swiss Ephemeris .*\.se1"):
        BgSkyCalendarWriter().run(ctx)


def test_writer_fails_closed_when_swisseph_reports_moshier_fallback(monkeypatch):
    """A directory name is not provenance: the position probe must confirm
    that Swiss files, rather than the silent Moshier fallback, served it."""
    import sys
    import brahmagyan.l0_ephemeris as l0_ephemeris
    import pipeline.orchestrator.writers.bg_sky_calendar as sky_calendar

    class MoshierSwe:
        SIDM_LAHIRI = 1
        FLG_SWIEPH = 2
        FLG_MOSEPH = 4
        FLG_SIDEREAL = 64 * 1024
        FLG_SPEED = 256
        SUN = 0

        version = "test"

        @staticmethod
        def set_ephe_path(_path):
            return None

        @staticmethod
        def set_sid_mode(_mode):
            return None

        @staticmethod
        def julday(*_args):
            return 2_451_544.5

        @staticmethod
        def calc_ut(*_args):
            return ((280.0, 0.0, 1.0, 1.0, 0.0, 0.0), MoshierSwe.FLG_MOSEPH)

    monkeypatch.setattr(l0_ephemeris, "_resolve_ephe_path", lambda: "/fake/se1")
    monkeypatch.setitem(sys.modules, "swisseph", MoshierSwe)

    def scan_must_not_run(*_args, **_kwargs):
        raise AssertionError("sky scan reached after Moshier served the backend probe")

    monkeypatch.setattr(sky_calendar, "scan_ingresses", scan_must_not_run)

    ctx = ContextSpec(
        asset_id="bg_sky_calendar",
        build_id=str(uuid.uuid4()),
        db_conn=None,
    )
    with pytest.raises(RuntimeError, match="Moshier"):
        BgSkyCalendarWriter().run(ctx)


def test_writer_fails_closed_outside_pinned_linux_x86_runtime(monkeypatch):
    """Station roots differ by one persisted quantum between arm64/macOS and
    the production runtime, so writes from an unpinned runtime must halt."""
    import platform
    import sys
    import brahmagyan.l0_ephemeris as l0_ephemeris
    import pipeline.orchestrator.writers.bg_sky_calendar as sky_calendar

    class SwissFileSwe:
        SIDM_LAHIRI = 1
        FLG_SWIEPH = 2
        FLG_MOSEPH = 4
        FLG_SIDEREAL = 64 * 1024
        FLG_SPEED = 256
        SUN = 0
        version = "2.10.03"

        @staticmethod
        def set_ephe_path(_path):
            return None

        @staticmethod
        def set_sid_mode(_mode):
            return None

        @staticmethod
        def julday(*_args):
            return 2_451_544.5

        @staticmethod
        def calc_ut(*_args):
            return ((280.0, 0.0, 1.0, 1.0, 0.0, 0.0), SwissFileSwe.FLG_SWIEPH)

    monkeypatch.setattr(l0_ephemeris, "_resolve_ephe_path", lambda: "/fake/se1")
    monkeypatch.setitem(sys.modules, "swisseph", SwissFileSwe)
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    monkeypatch.setattr(platform, "machine", lambda: "arm64")

    def scan_must_not_run(*_args, **_kwargs):
        raise AssertionError("sky scan reached outside the pinned write runtime")

    monkeypatch.setattr(sky_calendar, "scan_ingresses", scan_must_not_run)

    ctx = ContextSpec(
        asset_id="bg_sky_calendar",
        build_id=str(uuid.uuid4()),
        db_conn=None,
    )
    with pytest.raises(RuntimeError, match=r"Linux/x86_64"):
        BgSkyCalendarWriter().run(ctx)


def test_writer_fails_closed_when_ephemeris_file_digest_drifts(monkeypatch, tmp_path):
    """A different Swiss-file corpus must not inherit the pinned production
    provenance merely because it uses the same three filenames."""
    import platform
    import sys
    import brahmagyan.l0_ephemeris as l0_ephemeris
    import pipeline.orchestrator.writers.bg_sky_calendar as sky_calendar

    for filename in ("sepl_18.se1", "semo_18.se1", "seas_18.se1"):
        (tmp_path / filename).write_bytes(b"not-the-pinned-ephemeris")

    class SwissFileSwe:
        SIDM_LAHIRI = 1
        FLG_SWIEPH = 2
        FLG_MOSEPH = 4
        FLG_SIDEREAL = 64 * 1024
        FLG_SPEED = 256
        SUN = 0
        version = "2.10.03"

        @staticmethod
        def set_ephe_path(_path):
            return None

        @staticmethod
        def set_sid_mode(_mode):
            return None

        @staticmethod
        def julday(*_args):
            return 2_451_544.5

        @staticmethod
        def calc_ut(*_args):
            return ((280.0, 0.0, 1.0, 1.0, 0.0, 0.0), SwissFileSwe.FLG_SWIEPH)

    monkeypatch.setattr(l0_ephemeris, "_resolve_ephe_path", lambda: str(tmp_path))
    monkeypatch.setitem(sys.modules, "swisseph", SwissFileSwe)
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    monkeypatch.setattr(platform, "machine", lambda: "x86_64")

    def scan_must_not_run(*_args, **_kwargs):
        raise AssertionError("sky scan reached with unpinned ephemeris bytes")

    monkeypatch.setattr(sky_calendar, "scan_ingresses", scan_must_not_run)
    ctx = ContextSpec(
        asset_id="bg_sky_calendar",
        build_id=str(uuid.uuid4()),
        db_conn=None,
    )
    with pytest.raises(RuntimeError, match="digest"):
        BgSkyCalendarWriter().run(ctx)


def test_writer_propagates_scan_failure_to_the_orchestrator(monkeypatch):
    """A failed global scan must not return a zero-row success result, because
    the orchestrator classifies zero-row global writers as complete."""
    import brahmagyan.l0_ephemeris as l0_ephemeris
    import pipeline.orchestrator.writers.bg_sky_calendar as sky_calendar

    monkeypatch.setattr(l0_ephemeris, "_resolve_ephe_path", lambda: "/verified/se1")
    monkeypatch.setattr(sky_calendar, "_require_swiss_file_backend", lambda *_args: None)
    monkeypatch.setattr(sky_calendar, "_require_reproducible_write_runtime", lambda: None)
    monkeypatch.setattr(sky_calendar, "_require_pinned_ephemeris_files", lambda *_args: None)

    def broken_scan(*_args, **_kwargs):
        raise ValueError("deterministic scan exploded")

    monkeypatch.setattr(sky_calendar, "scan_ingresses", broken_scan)
    ctx = ContextSpec(
        asset_id="bg_sky_calendar",
        build_id=str(uuid.uuid4()),
        db_conn=None,
    )
    with pytest.raises(ValueError, match="deterministic scan exploded"):
        BgSkyCalendarWriter().run(ctx)


def test_writer_propagates_insert_failure_to_the_orchestrator(monkeypatch):
    """A DB write failure must escape the writer so its savepoint is rolled
    back and the asset is marked error instead of complete-with-partial rows."""
    from datetime import datetime
    import brahmagyan.l0_ephemeris as l0_ephemeris
    import pipeline.orchestrator.writers.bg_sky_calendar as sky_calendar

    monkeypatch.setattr(l0_ephemeris, "_resolve_ephe_path", lambda: "/verified/se1")
    monkeypatch.setattr(sky_calendar, "_require_swiss_file_backend", lambda *_args: None)
    monkeypatch.setattr(sky_calendar, "_require_reproducible_write_runtime", lambda: None)
    monkeypatch.setattr(sky_calendar, "_require_pinned_ephemeris_files", lambda *_args: None)
    one_row = sky_calendar._Row(
        event_type="ingress",
        primary_body="Sun",
        secondary_body=None,
        event_jd=2_451_544.5,
        event_datetime_utc=datetime(2000, 1, 1),
        sign="Capricorn",
        nakshatra="Uttara Ashadha",
        longitude_deg=280.0,
        speed_dps=1.0,
        detail={"target_sign": "Capricorn"},
    )
    monkeypatch.setattr(sky_calendar, "scan_ingresses", lambda *_args: [one_row])
    monkeypatch.setattr(sky_calendar, "scan_stations", lambda *_args: [])
    monkeypatch.setattr(sky_calendar, "scan_eclipses", lambda *_args: [])
    monkeypatch.setattr(sky_calendar, "scan_double_transits", lambda *_args: [])

    def broken_flush(*_args, **_kwargs):
        raise RuntimeError("database insert exploded")

    monkeypatch.setattr(BgSkyCalendarWriter, "_flush_batch", staticmethod(broken_flush))

    class CursorContext:
        def __enter__(self):
            return object()

        def __exit__(self, *_args):
            return False

    class Connection:
        @staticmethod
        def cursor():
            return CursorContext()

    ctx = ContextSpec(
        asset_id="bg_sky_calendar",
        build_id=str(uuid.uuid4()),
        db_conn=Connection(),
    )
    with pytest.raises(RuntimeError, match="database insert exploded"):
        BgSkyCalendarWriter().run(ctx)


def test_flush_batch_targets_the_post_migration_canonical_table():
    class RecordingCursor:
        rowcount = 1
        sql = ""

        def executemany(self, sql, _batch):
            self.sql = sql

    cursor = RecordingCursor()
    written = BgSkyCalendarWriter._flush_batch(cursor, [{}])
    assert written == 1
    assert "INSERT INTO bg_sky_calendar" in cursor.sql
    assert "INSERT INTO bg_sky_events" not in cursor.sql
    assert "DO UPDATE SET" in cursor.sql
    assert "event_datetime_utc = EXCLUDED.event_datetime_utc" in cursor.sql
    assert "bg_sky_calendar.source_citation" in cursor.sql
    assert "IS DISTINCT FROM" in cursor.sql


# ── Live tests (require DATABASE_URL; skipped otherwise) ─────────────────────

@pytest.fixture(scope="module")
def db_conn():
    url = os.environ.get("DATABASE_URL") or os.environ.get("PROD_DB_URL")
    if not url:
        pytest.skip("DATABASE_URL not set")
    conn = psycopg.connect(url, row_factory=psycopg.rows.dict_row)
    yield conn
    conn.rollback()
    conn.close()


def test_bg_sky_calendar_writer_runs(db_conn):
    writer = BgSkyCalendarWriter()
    ctx = ContextSpec(asset_id="bg_sky_calendar", build_id=str(uuid.uuid4()), db_conn=db_conn)
    result = writer.run(ctx)
    db_conn.commit()
    assert result.asset_id == "bg_sky_calendar"
    assert result.rows_inserted >= 0


def test_bg_sky_calendar_event_types_present(db_conn):
    cur = db_conn.cursor()
    cur.execute("SELECT DISTINCT event_type FROM bg_sky_calendar")
    types = {r["event_type"] for r in cur.fetchall()}
    # ingress must be present (dense, guaranteed over any multi-decade horizon).
    assert "ingress" in types


def test_bg_sky_calendar_no_null_citations(db_conn):
    cur = db_conn.cursor()
    cur.execute("SELECT count(*) AS n FROM bg_sky_calendar WHERE source_citation IS NULL")
    n = cur.fetchone()["n"]
    assert n == 0, f"bg_sky_calendar has {n} rows with NULL source_citation"


def test_bg_sky_calendar_writer_idempotent(db_conn):
    """Running the writer twice leaves bg_sky_calendar row count identical
    (same horizon -> same 'today' within the same test run -> same
    computed forward edge -> ON CONFLICT DO NOTHING dedupes every row)."""
    cur = db_conn.cursor()
    cur.execute("SELECT count(*) AS n FROM bg_sky_calendar")
    count_before = cur.fetchone()["n"]

    writer = BgSkyCalendarWriter()
    ctx = ContextSpec(asset_id="bg_sky_calendar", build_id=str(uuid.uuid4()), db_conn=db_conn)
    result = writer.run(ctx)
    db_conn.commit()

    cur.execute("SELECT count(*) AS n FROM bg_sky_calendar")
    count_after = cur.fetchone()["n"]

    assert count_before == count_after, f"Idempotency broken: {count_before} -> {count_after}"
    if count_before > 0:
        assert result.rows_inserted == 0, f"Expected 0 rows_inserted on re-run, got {result.rows_inserted}"
