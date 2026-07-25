"""
test_l0_ephemeris_sidereal_first.py — EL-39 fix regression tests.

EL-39: ref_planet_position_get (and siblings) served TROPICAL only, with
ayanamsha_id accepted-but-ignored (WHERE-filter bug against a tropical-only
table meant any non-'tropical' value silently returned zero rows), and
nakshatra_number derived from the tropical longitude — wrong under every
ayanamsha, served unlabelled.

These tests reproduce the ORIGINAL recipe from ELEVATION_REGISTER_v1_0.md
EL-39 / the elevation campaign charter §5 β.C evidence block (Venus,
2026-08-15, tropical_longitude=188.565106) against a mocked DB connection —
no live DB required — and assert the fixed sidereal-first behavior.

Charter's exact acceptance bar: Venus 2026-08-15 sidereal Lahiri sign = Virgo,
with a correct sidereal nakshatra (not the old tropical-derived one).
"""
from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest

from brahmagyan import l0_ephemeris as mod


# ── Shared mock DB helpers ───────────────────────────────────────────────────

def _row_cursor(rows: list[tuple], cols: list[str]):
    """Build a mock cursor whose .description/.fetchall() serve the given rows."""
    cur = MagicMock()
    cur.description = [type("c", (), {"name": n})() for n in cols]
    cur.fetchall.return_value = rows
    cur.__enter__ = lambda s: cur
    cur.__exit__ = MagicMock(return_value=False)
    return cur


def _conn_with_cursor(cur):
    conn = MagicMock()
    conn.cursor.return_value = cur
    return conn


POSITION_COLS = [
    "date", "body", "tropical_longitude", "sign_number", "degree_in_sign",
    "nakshatra_number", "is_retrograde", "speed_dps", "source_citation",
]

# EL-39 evidence, verbatim: Venus 2026-08-15, tropical_longitude=188.565106,
# stored (tropical) sign_number=7 (Libra), stored nakshatra_number=15 (WRONG —
# tropical-derived).
VENUS_20260815_TROPICAL_ROW = (
    date(2026, 8, 15), "Venus", 188.565106, 7, 8.565106, 15, False, 1.18,
    "pyswisseph + Swiss Ephemeris .se1",
)


class TestQueryPlanetPositionSidereal:
    def test_default_ayanamsha_is_lahiri_chitrapaksha(self):
        assert mod._DEFAULT_READ_AYANAMSHA == "lahiri_chitrapaksha"

    def test_venus_20260815_sidereal_lahiri_is_virgo(self):
        """Charter's exact acceptance bar: sidereal Lahiri sign = Virgo (6)."""
        cur = _row_cursor([VENUS_20260815_TROPICAL_ROW], POSITION_COLS)
        conn = _conn_with_cursor(cur)
        result = mod.query_planet_position("2026-08-15", planet="Venus", conn=conn)
        assert result["ok"] is True
        assert result["ayanamsha_id"] == "lahiri_chitrapaksha"
        pos = result["positions"][0]
        assert pos["sign_number"] == 6, f"Expected Virgo (6), got {pos['sign_number']}"

    def test_venus_20260815_sidereal_nakshatra_not_the_old_tropical_one(self):
        """The old (buggy) tropical-derived nakshatra_number was 15. The sidereal
        derivation must NOT reproduce that wrong value."""
        cur = _row_cursor([VENUS_20260815_TROPICAL_ROW], POSITION_COLS)
        conn = _conn_with_cursor(cur)
        result = mod.query_planet_position("2026-08-15", planet="Venus", conn=conn)
        pos = result["positions"][0]
        assert pos["nakshatra_number"] != 15
        assert 1 <= pos["nakshatra_number"] <= 27
        assert 1 <= pos["pada"] <= 4

    def test_tropical_longitude_retained_as_labelled_extra(self):
        cur = _row_cursor([VENUS_20260815_TROPICAL_ROW], POSITION_COLS)
        conn = _conn_with_cursor(cur)
        result = mod.query_planet_position("2026-08-15", planet="Venus", conn=conn)
        pos = result["positions"][0]
        assert pos["tropical_longitude"] == pytest.approx(188.565106, abs=1e-6)
        # Primary field is sidereal, distinct from the tropical extra.
        assert pos["longitude"] != pytest.approx(pos["tropical_longitude"], abs=0.01)

    def test_explicit_tropical_request_suppresses_nakshatra(self):
        cur = _row_cursor([VENUS_20260815_TROPICAL_ROW], POSITION_COLS)
        conn = _conn_with_cursor(cur)
        result = mod.query_planet_position(
            "2026-08-15", planet="Venus", ayanamsha_id="tropical", conn=conn
        )
        pos = result["positions"][0]
        assert pos["sign_number"] == 7  # tropical Libra — legitimately tropical, kept
        assert pos["nakshatra_number"] is None
        assert "nakshatra_note" in pos and "sidereal" in pos["nakshatra_note"].lower()

    def test_explicit_tropical_request_never_serves_bare_nakshatra(self):
        """B.10: a tropical request must never serve a nakshatra number at all
        (bare or otherwise) — this was the exact unlabelled-wrong-value bug."""
        cur = _row_cursor([VENUS_20260815_TROPICAL_ROW], POSITION_COLS)
        conn = _conn_with_cursor(cur)
        result = mod.query_planet_position(
            "2026-08-15", planet="Venus", ayanamsha_id="tropical", conn=conn
        )
        pos = result["positions"][0]
        assert pos["nakshatra_number"] is None

    def test_unrecognized_ayanamsha_is_loud_error_not_silent_fallback(self):
        conn = MagicMock()
        result = mod.query_planet_position("2026-08-15", planet="Venus",
                                             ayanamsha_id="bogus_ayanamsha", conn=conn)
        assert result["ok"] is False
        assert "EXTERNAL_COMPUTATION_REQUIRED" in result["error"]
        # Must not have touched the DB at all.
        conn.cursor.assert_not_called()

    def test_non_tropical_ayanamsha_no_longer_silently_empty(self):
        """Pre-fix: WHERE ayanamsha_id=%s against a tropical-only table meant any
        non-'tropical' id returned zero rows. Post-fix: it must return the row,
        sidereal-derived."""
        cur = _row_cursor([VENUS_20260815_TROPICAL_ROW], POSITION_COLS)
        conn = _conn_with_cursor(cur)
        result = mod.query_planet_position(
            "2026-08-15", planet="Venus", ayanamsha_id="krishnamurti", conn=conn
        )
        assert result["ok"] is True
        assert result["count"] == 1
        assert result["positions"][0]["nakshatra_number"] is not None

    def test_all_five_canonical_ayanamshas_accepted(self):
        for ay in ("lahiri_chitrapaksha", "true_chitra", "krishnamurti",
                   "raman", "surya_siddhanta_classical"):
            cur = _row_cursor([VENUS_20260815_TROPICAL_ROW], POSITION_COLS)
            conn = _conn_with_cursor(cur)
            result = mod.query_planet_position("2026-08-15", planet="Venus",
                                                 ayanamsha_id=ay, conn=conn)
            assert result["ok"] is True, f"{ay} should be accepted"
            assert result["positions"][0]["sign_number"] is not None


TRANSIT_COLS = [
    "date", "body", "tropical_longitude", "sign_number", "degree_in_sign",
    "nakshatra_number", "is_retrograde", "speed_dps",
]


class TestQueryPlanetTransitSidereal:
    def test_sign_filter_matches_sidereal_sign_by_default(self):
        # Same Venus row: tropical sign=7 (Libra), sidereal sign=6 (Virgo).
        row = (date(2026, 8, 15), "Venus", 188.565106, 7, 8.565106, 15, False, 1.18)
        cur = _row_cursor([row], TRANSIT_COLS)
        conn = _conn_with_cursor(cur)
        # Filtering for sidereal Virgo (6) should match.
        result = mod.query_planet_transit(
            "Venus", "2026-08-15", "2026-08-15", sign_number=6, conn=conn
        )
        assert result["ok"] is True
        assert result["count"] == 1
        assert result["rows"][0]["sign_number"] == 6

    def test_sign_filter_tropical_sign_no_longer_matches_by_default(self):
        row = (date(2026, 8, 15), "Venus", 188.565106, 7, 8.565106, 15, False, 1.18)
        cur = _row_cursor([row], TRANSIT_COLS)
        conn = _conn_with_cursor(cur)
        # Filtering for the OLD tropical sign (7 = Libra) should NOT match now
        # that the filter is sidereal by default.
        result = mod.query_planet_transit(
            "Venus", "2026-08-15", "2026-08-15", sign_number=7, conn=conn
        )
        assert result["count"] == 0

    def test_unrecognized_ayanamsha_error(self):
        conn = MagicMock()
        result = mod.query_planet_transit(
            "Venus", "2026-08-15", "2026-08-15", ayanamsha_id="nope", conn=conn
        )
        assert result["ok"] is False
        assert "EXTERNAL_COMPUTATION_REQUIRED" in result["error"]


class TestQueryAspectsAtTimeSidereal:
    def test_aspect_geometry_ayanamsha_invariant(self):
        rows = [("Sun", 100.0), ("Moon", 190.0)]  # 90 degree square
        cur = _row_cursor(rows, ["body", "tropical_longitude"])
        conn = _conn_with_cursor(cur)
        r_sidereal = mod.query_aspects_at_time("2026-08-15", ayanamsha_id="lahiri_chitrapaksha",
                                                orb_degrees=1.0, conn=conn)
        cur2 = _row_cursor(rows, ["body", "tropical_longitude"])
        conn2 = _conn_with_cursor(cur2)
        r_tropical = mod.query_aspects_at_time("2026-08-15", ayanamsha_id="tropical",
                                                orb_degrees=1.0, conn=conn2)
        assert r_sidereal["ok"] and r_tropical["ok"]
        assert len(r_sidereal["aspects"]) == len(r_tropical["aspects"]) == 1
        a_sid, a_trop = r_sidereal["aspects"][0], r_tropical["aspects"][0]
        assert a_sid["aspect"] == a_trop["aspect"] == "square"
        assert a_sid["orb"] == a_trop["orb"]
        assert a_sid["actual_diff"] == a_trop["actual_diff"]
        # But the labelled absolute longitude differs (sidereal vs tropical).
        assert a_sid["longitude_b1"] != a_trop["longitude_b1"]
        assert a_trop["longitude_b1"] == a_trop["tropical_longitude_b1"]

    def test_non_tropical_ayanamsha_no_longer_silently_empty(self):
        rows = [("Sun", 100.0), ("Moon", 190.0)]
        cur = _row_cursor(rows, ["body", "tropical_longitude"])
        conn = _conn_with_cursor(cur)
        result = mod.query_aspects_at_time("2026-08-15", ayanamsha_id="raman", conn=conn)
        assert result["ok"] is True
        assert result["count"] == 1  # pre-fix this silently returned 0


class TestQueryRetrogradePeriodsSidereal:
    def test_station_dates_ayanamsha_invariant_but_sign_relabelled(self):
        rows = [
            (date(2026, 8, 1), False, 100.0, 4),
            (date(2026, 8, 2), True, 100.5, 4),  # station: retrograde_start
        ]
        cur = _row_cursor(rows, ["date", "is_retrograde", "tropical_longitude", "sign_number"])
        conn = _conn_with_cursor(cur)
        result = mod.query_retrograde_periods("Mercury", "2026-08-01", "2026-08-02", conn=conn)
        assert result["ok"] is True
        assert result["station_count"] == 1
        station = result["stations"][0]
        assert station["station_type"] == "retrograde_start"
        assert station["station_date"] == "2026-08-02"
        # sidereal-primary sign_number differs from the tropical extra (Virgo mean offset ~24deg
        # crosses at least one sign boundary from a tropical longitude of ~100deg).
        assert "tropical_sign_number" in station
        assert "tropical_longitude_deg" in station

    def test_unrecognized_ayanamsha_error(self):
        conn = MagicMock()
        result = mod.query_retrograde_periods(
            "Mercury", "2026-08-01", "2026-08-02", ayanamsha_id="nope", conn=conn
        )
        assert result["ok"] is False
        assert "EXTERNAL_COMPUTATION_REQUIRED" in result["error"]
