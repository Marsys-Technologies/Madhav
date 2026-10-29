"""Detector (SUR-RB-6, N.8): foreign births evaluated from a stated UT offset must reproduce a direct ephemeris at the TRUE UT.

Chain under test, per synthetic foreign birth: the source record's offset -> engine true UT ->
L1's own natal computation and Vimshottari start (fed that offset explicitly, so no IST fallback) ->
compared with an independent script that shares no code with either (independent_ephemeris.py).
The build fails on any mismatch. A negative control feeds the same births the IST fallback L1 would use
silently and must NOT match, so the detector demonstrably can fail.

Needs the pinned ephemeris (SE_EPHE_PATH) and PyJHora, as the L1 adapter itself does; skipped otherwise.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest

swe = pytest.importorskip("swisseph")
pytest.importorskip("jhora")
EPHE = os.environ.get("SE_EPHE_PATH") or os.environ.get("SWE_EPHE_PATH")
pytestmark = pytest.mark.skipif(not EPHE, reason="SE_EPHE_PATH (pinned .se1 files) not set")

from services.rulebook.engine import birthrecord as B  # noqa: E402

from . import independent_ephemeris as IE  # noqa: E402

# name, local date, local time, lat, lon, utc offset minutes (as the record would state it), IANA zone
BIRTHS = [
    ("los_angeles_pdt", "1990-07-04", "14:30:00", 34.05, -118.24, -420, "America/Los_Angeles"),
    ("new_york_est", "1985-01-15", "03:10:00", 40.71, -74.0, -300, "America/New_York"),
    ("london_bst", "1992-08-12", "22:45:00", 51.5, -0.12, 60, "Europe/London"),
    ("auckland_nzdt", "1998-01-20", "09:05:00", -36.85, 174.76, 780, "Pacific/Auckland"),
    ("kathmandu_345", "1987-03-03", "18:20:00", 27.7, 85.3, 345, "Asia/Kathmandu"),
    ("reykjavik_utc", "1995-06-21", "01:15:00", 64.15, -21.9, 0, "Atlantic/Reykjavik"),
    ("anchorage_akst", "1990-12-21", "12:00:00", 61.2, -149.9, -540, "America/Anchorage"),
    ("pago_pago_170w", "1999-09-09", "08:30:00", -14.28, -170.7, -660, "Pacific/Pago_Pago"),
    ("majuro_171e", "1993-11-05", "05:50:00", 7.1, 171.0, 720, "Pacific/Majuro"),
    ("sydney_aedt", "2001-02-01", "21:15:00", -33.87, 151.2, 660, "Australia/Sydney"),
]

LON_TOL_DEG = 0.0003  # about 1 arcsec; observed agreement is exact. A UT error of 2 s already moves the Moon more than this.
ASC_TOL_DEG = 0.001
START_TOL_S = 60.0


@pytest.fixture(scope="module", autouse=True)
def _ephemeris():
    IE.setup(EPHE)


def _angdiff(a, b):
    return abs((a - b + 180.0) % 360.0 - 180.0)


def _l1(rec, tz_hours):
    """What the L1 adapter produces for this birth when it is handed ``tz_hours`` (the explicit offset, or the IST fallback)."""
    from ga_writers import ga_dashas_writer as D
    from pyjhora_adapter.compute import compute_chart

    dt = f"{rec['date']}T{rec['time']}"
    chart = compute_chart(
        {"latitude_deg": rec["lat"], "longitude_deg": rec["lon"], "tz_offset_hours": tz_hours, "datetime_iso": dt, "place_name": "t", "subject_label": "t"},
        ayanamsha_id="lahiri_chitrapaksha",
    )
    lons = {b["name"]: b["longitude_deg"] for b in chart["grahas"] if b["name"] in IE.BODIES}
    asc = chart["ascendant"]["longitude_deg"]
    birth = {"datetime_iso": dt, "tz_offset_hours": tz_hours, "latitude_deg": rec["lat"], "longitude_deg": rec["lon"]}
    jd = D._birth_jd_utc(birth)
    cid = "00000000-0000-0000-0000-0000000000f1"
    D.set_karaka_roles(cid, "lahiri_chitrapaksha", {})  # the writer's DB-fed karaka lookup is irrelevant to dates
    rows = D.compute_vimshottari(lons["Moon"], jd, "lahiri_chitrapaksha", cid, "b")
    md = [r for r in rows if r["level_n"] == 1 and r["start_iso"] <= _iso(jd) < r["end_iso"]]
    assert len(md) == 1
    return lons, asc, jd, md[0]


def _iso(jd):
    return datetime.fromtimestamp((jd - 2440587.5) * 86400.0, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def _rec(row):
    name, d, t, lat, lon, off, zone = row
    return {"name": name, "date": d, "time": t, "lat": lat, "lon": lon, "off": off, "zone": zone}


def _independent(rec):
    y, mo, d = (int(x) for x in rec["date"].split("-"))
    hh, mm, ss = (int(x) for x in rec["time"].split(":"))
    jd = IE.true_ut_jd(y, mo, d, hh, mm, ss, rec["off"])
    lons = IE.sidereal_longitudes(jd)
    return jd, lons, IE.sidereal_ascendant(jd, rec["lat"], rec["lon"]), IE.vimshottari_start(lons["Moon"], jd)


@pytest.mark.parametrize("row", BIRTHS, ids=[b[0] for b in BIRTHS])
def test_engine_ut_and_l1_outputs_match_a_direct_ephemeris_at_the_true_ut(row):
    rec = _rec(row)
    resolved = B.resolve_birth(
        B.parse_birth_record(
            {"local_date": rec["date"], "local_time": rec["time"], "lat": rec["lat"], "lon": rec["lon"], "utc_offset_minutes": rec["off"], "tz_iana": rec["zone"]}
        )
    )
    jd_i, lons_i, asc_i, (lord_i, start_i) = _independent(rec)
    # (1) the engine's true UT is the independent one
    assert resolved.jd_ut == pytest.approx(jd_i, abs=1e-9)
    # (2) L1 fed the explicit offset reproduces the direct ephemeris at that UT
    lons, asc, jd_l1, md = _l1(rec, rec["off"] / 60.0)
    assert jd_l1 == pytest.approx(jd_i, abs=1e-9)
    for name, v in lons_i.items():
        assert _angdiff(lons[name], v) < LON_TOL_DEG, (rec["name"], name, lons[name], v)
    assert _angdiff(asc, asc_i) < ASC_TOL_DEG, (rec["name"], "lagna", asc, asc_i)
    # (3) Vimshottari start: same lord, same start instant
    assert md["lord_graha"] == lord_i, (rec["name"], md["lord_graha"], lord_i)
    start_l1 = datetime.fromisoformat(md["start_iso"]).timestamp()
    start_ind = (start_i - 2440587.5) * 86400.0
    assert abs(start_l1 - start_ind) < START_TOL_S, (rec["name"], start_l1 - start_ind)


def test_negative_control_the_ist_fallback_would_not_match():
    """If L1 silently used +5:30 (DF-04) the same births would fail the check above: the detector can fail."""
    caught = 0
    for row in BIRTHS:
        rec = _rec(row)
        if rec["off"] == 330:
            continue
        jd_i, lons_i, asc_i, _ = _independent(rec)
        lons, asc, jd_l1, md = _l1(rec, 5.5)
        bad = _angdiff(lons["Moon"], lons_i["Moon"]) >= LON_TOL_DEG or _angdiff(asc, asc_i) >= ASC_TOL_DEG or abs(jd_l1 - jd_i) > 1e-6
        caught += bad
    assert caught == len([b for b in BIRTHS if b[5] != 330])
