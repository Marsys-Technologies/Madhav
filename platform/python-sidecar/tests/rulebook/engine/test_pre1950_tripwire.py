"""Explicit-offset Vimshottari tripwire for births BEFORE the stored window start (1950-01-01; SUR-RB-49).

No stored level-1 row can cover a pre-1950 birth, so the tripwire checks the FIRST stored row: its lord must equal the lord
of an independent 120-year walk that starts from the Moon's nakshatra fraction computed by DIRECT EPHEMERIS at the true UT
(never from L1 rows; year = 365.25 days), and its END must lie within 120 s of that walk's end after the SUR-RB-30
allowance for the L1-vs-ephemeris Moon difference. Post-1950 births keep the old path.
"""
from __future__ import annotations

import os
from datetime import date, datetime, timezone

import pytest

swe = pytest.importorskip("swisseph")
EPHE = os.environ.get("SE_EPHE_PATH")
pytestmark = pytest.mark.skipif(not EPHE, reason="SE_EPHE_PATH (pinned .se1 files) not set")

from services.rulebook.engine.birthcheck import (  # noqa: E402
    DASHA_WINDOW_START_JD, VIMSHOTTARI_ORDER, VIMSHOTTARI_YEARS, YEAR_DAYS, dasha_start_problems)
from services.rulebook.engine.chart import Birth, DashaLevel, DashaRow, GrahaFacts, NatalChart, utc_to_jd  # noqa: E402

BIRTH = datetime(1921, 3, 4, 5, 6, tzinfo=timezone.utc)
SPAN = 360.0 / 27.0


def eph_moon(jd):
    swe.set_ephe_path(EPHE)
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    return swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_TRUEPOS)[0][0] % 360.0


def walk(birth_jd, moon):
    idx = min(int(moon // SPAN), 26)
    frac = (moon - idx * SPAN) / SPAN
    i, s = idx % 9, birth_jd - frac * VIMSHOTTARI_YEARS[VIMSHOTTARI_ORDER[idx % 9]] * YEAR_DAYS
    out = []
    while s < birth_jd + 130 * YEAR_DAYS:
        lo = VIMSHOTTARI_ORDER[i % 9]
        e = s + VIMSHOTTARI_YEARS[lo] * YEAR_DAYS
        out.append((lo, s, e))
        s, i = e, i + 1
    return out


def chart_with(rows, l1_moon, when=BIRTH):
    b = Birth(birth_date=when.date(), birth_time_local=when.strftime("%H:%M:%S"), lat=0.0, lon=0.0, zone="UTC", birth_utc=when,
              utc_offset_minutes=0)
    return NatalChart(chart_key="t", birth=b, lagna_sign=1, grahas={"chandra": GrahaFacts(longitude=l1_moon)}, aspected_houses={},
                      house_lords={}, md=DashaLevel(rows), ad=DashaLevel([]))


def stored_rows(moon, when=BIRTH, shift_end_s=0.0, wrong_lord=False):
    """What L1 would store from a given Moon: the periods from 1950-01-01, the first one clipped there."""
    jd = utc_to_jd(when)
    rows = [DashaRow(lo, max(s, DASHA_WINDOW_START_JD), e) for lo, s, e in walk(jd, moon) if e > DASHA_WINDOW_START_JD]
    first = rows[0]
    lord = first.lord
    if wrong_lord:
        lord = next(x for x in VIMSHOTTARI_ORDER if x != first.lord)
    rows[0] = DashaRow(lord, first.start_jd, first.end_jd + shift_end_s / 86400.0)
    rows[1] = DashaRow(rows[1].lord, rows[1].start_jd + shift_end_s / 86400.0, rows[1].end_jd)
    return rows


def test_pre1950_birth_with_correct_first_stored_row_passes():
    m = eph_moon(utc_to_jd(BIRTH))
    assert dasha_start_problems(chart_with(stored_rows(m), m), utc_to_jd(BIRTH)) == []


def test_pre1950_l1_moon_a_hair_off_is_allowed_for():
    # L1's Moon 0.0005 degree from the ephemeris shifts every stored boundary consistently: the allowance absorbs it
    m = eph_moon(utc_to_jd(BIRTH)) + 0.0005
    assert dasha_start_problems(chart_with(stored_rows(m), m), utc_to_jd(BIRTH)) == []


def test_pre1950_wrong_first_lord_fails():
    m = eph_moon(utc_to_jd(BIRTH))
    assert dasha_start_problems(chart_with(stored_rows(m, wrong_lord=True), m), utc_to_jd(BIRTH))


def test_pre1950_first_row_end_off_by_more_than_120_s_fails():
    m = eph_moon(utc_to_jd(BIRTH))
    assert dasha_start_problems(chart_with(stored_rows(m, shift_end_s=300), m), utc_to_jd(BIRTH))
    assert dasha_start_problems(chart_with(stored_rows(m, shift_end_s=60), m), utc_to_jd(BIRTH)) == []


def test_pre1950_rows_built_from_a_wrong_instant_fail_even_if_l1_moon_agrees_with_them():
    # rows AND L1 Moon from a birth 3 hours late (a wrong UT): the direct ephemeris at the stated UT catches it
    late = utc_to_jd(BIRTH) + 3 / 24
    m_late = eph_moon(late)
    rows = [DashaRow(lo, max(s, DASHA_WINDOW_START_JD), e) for lo, s, e in walk(late, m_late) if e > DASHA_WINDOW_START_JD]
    assert dasha_start_problems(chart_with(rows, m_late), utc_to_jd(BIRTH))


def test_pre1950_without_stored_rows_fails():
    m = eph_moon(utc_to_jd(BIRTH))
    assert dasha_start_problems(chart_with([], m), utc_to_jd(BIRTH))


def test_post1950_birth_keeps_the_old_path():
    when = datetime(1975, 6, 1, 12, 0, tzinfo=timezone.utc)
    m = eph_moon(utc_to_jd(when))
    jd = utc_to_jd(when)
    rows = [DashaRow(lo, max(s, DASHA_WINDOW_START_JD), e) for lo, s, e in walk(jd, m) if e > DASHA_WINDOW_START_JD]
    assert dasha_start_problems(chart_with(rows, m, when), jd) == []
    rows[[i for i, r in enumerate(rows) if r.start_jd <= jd < r.end_jd][0]] = DashaRow("guru" if rows[0].lord != "guru" else "shani", rows[0].start_jd, rows[0].end_jd)
    assert dasha_start_problems(chart_with(rows, m, when), jd)
