"""Detector (SUR-RB-15, N.8): the Vimshottari periods running on the FIRST STORED DAY (1950-01-01) of a pre-1950 birth.

The stored L1 window starts 1950-01-01, so for a chart born earlier the first stored mahadasha and antardasha are
clipped rows. Whether the lords on that first day are RIGHT depends on the true birth moment. Per synthetic birth
(1902, 1912, 1930, 1938, 1949, two of them foreign with an explicit offset):

  engine true UT (from the stated offset)  ->  L1 compute_vimshottari rows (what would be stored)
  ->  mahadasha and antardasha on 1950-01-01   ==   an independent walk of the 120-year cycle from the true birth
      moment (independent_ephemeris.py: swisseph + arithmetic only, no engine, no L1, no stored table).

The first stored row must also begin on 1950-01-01 (clipped), and the engine's own day-start logic must report that
as the daśā first day. Needs the pinned ephemeris (SE_EPHE_PATH) like the L1 adapter; skipped otherwise.
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone

import pytest

swe = pytest.importorskip("swisseph")
pytest.importorskip("jhora")
EPHE = os.environ.get("SE_EPHE_PATH") or os.environ.get("SWE_EPHE_PATH")
pytestmark = pytest.mark.skipif(not EPHE, reason="SE_EPHE_PATH (pinned .se1 files) not set")

from services.rulebook.engine import birthrecord as B  # noqa: E402
from services.rulebook.engine import constants as K  # noqa: E402
from services.rulebook.engine import dayatom, driver  # noqa: E402
from services.rulebook.engine.chart import DashaLevel, DashaRow, NatalChart, utc_to_jd  # noqa: E402

from . import _world as W  # noqa: E402
from . import independent_ephemeris as IE  # noqa: E402

# name, local date, local time, lat, lon, stated offset (minutes east)
BIRTHS = [
    ("india_1902", "1902-03-15", "06:10:00", 20.27, 85.84, 330),
    ("london_1912", "1912-11-02", "22:40:00", 51.5, -0.12, 0),
    ("pago_pago_1930_foreign", "1930-06-21", "08:30:00", -14.28, -170.7, -660),
    ("new_york_1938_foreign", "1938-02-14", "03:20:00", 40.71, -74.0, -300),
    ("india_1949_dec31", "1949-12-31", "23:10:00", 20.27, 85.84, 330),
    ("india_1949_jan01", "1949-01-01", "00:20:00", 20.27, 85.84, 330),
]
FIRST_STORED = "1950-01-01T00:00:00+00:00"


@pytest.fixture(scope="module", autouse=True)
def _ephemeris():
    IE.setup(EPHE)


def _l1_rows(row):
    from ga_writers import ga_dashas_writer as D
    from pyjhora_adapter.compute import compute_chart

    name, d, t, lat, lon, off = row
    dt = f"{d}T{t}"
    chart = compute_chart(
        {"latitude_deg": lat, "longitude_deg": lon, "tz_offset_hours": off / 60.0, "datetime_iso": dt, "place_name": "t", "subject_label": "t"},
        ayanamsha_id="lahiri_chitrapaksha",
    )
    moon = [g["longitude_deg"] for g in chart["grahas"] if g["name"] == "Moon"][0]
    jd = D._birth_jd_utc({"datetime_iso": dt, "tz_offset_hours": off / 60.0, "latitude_deg": lat, "longitude_deg": lon})
    cid = "00000000-0000-0000-0000-0000000000f2"
    D.set_karaka_roles(cid, "lahiri_chitrapaksha", {})
    return D.compute_vimshottari(moon, jd, "lahiri_chitrapaksha", cid, "b"), moon, jd


def _covering(rows, level, iso):
    hit = [r for r in rows if r["level_n"] == level and r["start_iso"] <= iso < r["end_iso"]]
    assert len(hit) == 1, (level, iso, len(hit))
    return hit[0]


@pytest.mark.parametrize("row", BIRTHS, ids=[b[0] for b in BIRTHS])
def test_running_mahadasa_and_antardasa_on_the_first_stored_day_match_an_independent_computation(row):
    name, d, t, lat, lon, off = row
    y, mo, dd = (int(x) for x in d.split("-"))
    hh, mm, ss = (int(x) for x in t.split(":"))
    rec = B.parse_birth_record({"local_date": d, "local_time": t, "lat": lat, "lon": lon, "utc_offset_minutes": off})
    jd_engine = utc_to_jd(B.ut_of(rec))  # the engine's true UT (stated offset only; the tz cross-check is not the subject here)
    jd_ind = IE.true_ut_jd(y, mo, dd, hh, mm, ss, off)
    assert jd_engine == pytest.approx(jd_ind, abs=1e-9)

    rows, moon_l1, jd_l1 = _l1_rows(row)
    assert jd_l1 == pytest.approx(jd_ind, abs=1e-9)
    moon_ind = IE.sidereal_longitudes(jd_ind)["Moon"]
    jd_first = swe.julday(1950, 1, 1, 0.0)
    md_i, ad_i, _a0, margin = IE.vimshottari_running(moon_ind, jd_ind, jd_first)
    assert margin > 0.5, f"{name}: first stored day is within {margin * 24:.1f} h of a period boundary; pick another birth"

    md = _covering(rows, 1, FIRST_STORED)
    ad = _covering(rows, 2, FIRST_STORED)
    assert (md["lord_graha"], ad["lord_graha"]) == (md_i, ad_i), (name, md["lord_graha"], ad["lord_graha"], md_i, ad_i)
    # the stored window opens on 1950-01-01: the first row of each level begins exactly there (clipped), nothing earlier is stored
    for level in (1, 2):
        first = min((r for r in rows if r["level_n"] == level), key=lambda r: r["start_iso"])
        assert first["start_iso"] == FIRST_STORED, (name, level, first["start_iso"])


@pytest.mark.parametrize("row", BIRTHS, ids=[b[0] for b in BIRTHS])
def test_engine_reads_the_same_lords_and_reports_1950_01_01_as_the_dasha_first_day(row):
    name, d, t, lat, lon, off = row
    rec = B.parse_birth_record({"local_date": d, "local_time": t, "lat": lat, "lon": lon, "utc_offset_minutes": off})
    rows, _moon, _jd = _l1_rows(row)
    to_jd = lambda iso: utc_to_jd(datetime.fromisoformat(iso))
    lv = lambda n: DashaLevel([DashaRow(K.CARD_GRAHA_BY_L0_BODY[r["lord_graha"]], to_jd(r["start_iso"]), to_jd(r["end_iso"])) for r in rows if r["level_n"] == n])
    chart = NatalChart(
        chart_key=name, birth=B.ResolvedBirth(rec, B.ut_of(rec), 0.0, "-", "-").birth(), lagna_sign=1, grahas={}, aspected_houses={}, house_lords={},
        md=lv(1), ad=lv(2),
    )
    prov = dayatom.TableSunrise(W.sunrise_table(date(1948, 12, 25), date(1950, 1, 10)))  # 00:30Z each day
    sky = type("S", (), {"first_jd": staticmethod(lambda body: 2415000.0)})()  # transit side is not the subject here
    h = driver.horizon_inputs(chart, sky, prov)
    assert h["dasha_first_day"] == "1950-01-01", (name, h)
    # the engine's lord on that first day is the independent lord
    y, mo, dd = (int(x) for x in d.split("-"))
    hh, mm, ss = (int(x) for x in t.split(":"))
    jd_ind = IE.true_ut_jd(y, mo, dd, hh, mm, ss, off)
    moon_ind = IE.sidereal_longitudes(jd_ind)["Moon"]
    t_sun = utc_to_jd(datetime(1950, 1, 1, 0, 30, tzinfo=timezone.utc))
    md_i, ad_i, _a0, _m = IE.vimshottari_running(moon_ind, jd_ind, t_sun)
    assert K.L0_BODY[chart.md.lord_at(t_sun)] == md_i and K.L0_BODY[chart.ad.lord_at(t_sun)] == ad_i


def test_negative_control_a_wrong_birth_moment_gives_different_lords_for_some_births():
    """The detector can fail: shift each true birth by 7 hours (a plausible offset slip) and count the births whose
    independent first-day lords change. If none changed, the comparison above would be blind to UT errors."""
    changed = 0
    for name, d, t, lat, lon, off in BIRTHS:
        y, mo, dd = (int(x) for x in d.split("-"))
        hh, mm, ss = (int(x) for x in t.split(":"))
        jd = IE.true_ut_jd(y, mo, dd, hh, mm, ss, off)
        jd_first = swe.julday(1950, 1, 1, 0.0)
        a = IE.vimshottari_running(IE.sidereal_longitudes(jd)["Moon"], jd, jd_first)[:2]
        jd2 = jd + 7.0 / 24.0
        b = IE.vimshottari_running(IE.sidereal_longitudes(jd2)["Moon"], jd2, jd_first)[:2]
        changed += a != b
    assert changed >= 1
