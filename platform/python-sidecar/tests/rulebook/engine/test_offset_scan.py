"""End to end for a FOREIGN birth: record -> true UT -> consistency tripwires -> solar-day sunrise -> per-day states."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta, timezone

import pytest

pytest.importorskip("swisseph")

from services.rulebook.engine import birthrecord as B  # noqa: E402
from services.rulebook.engine import cli, constants as K, dayatom, driver  # noqa: E402
from services.rulebook.engine import units as U  # noqa: E402
from services.rulebook.engine.birthcheck import dasha_start_problems, sky_sign_problems, utc_consistency_problems  # noqa: E402
from services.rulebook.engine.chart import chart_from_fixture, utc_to_jd  # noqa: E402
from services.rulebook.engine.sky import sky_from_fixture  # noqa: E402

from . import _cardkit as CK  # noqa: E402
from . import _world as W  # noqa: E402
from .test_solar_sunrise import noaa_sunrise_utc  # noqa: E402

LAT, LON = -36.85, 174.76  # Auckland-like: far east
RECORD = {"local_date": "1999-05-20", "local_time": "06:40:00", "lat": LAT, "lon": LON, "utc_offset_minutes": 720, "tz_iana": "Pacific/Auckland", "source_zone_code": "NZST", "dst_applied": False}
SIGNS12 = W.SIGNS
VIM = ["ketu", "shukra", "surya", "chandra", "mangala", "rahu", "guru", "shani", "budha"]
YEARS = {"ketu": 7, "shukra": 20, "surya": 6, "chandra": 10, "mangala": 7, "rahu": 18, "guru": 16, "shani": 19, "budha": 17}
LONGS = {"surya": 59.0, "chandra": 100.0, "mangala": 200.0, "budha": 70.0, "guru": 250.0, "shukra": 40.0, "shani": 330.0, "rahu": 10.0, "ketu": 190.0}
BODY = {"surya": "Sun", "chandra": "Moon", "mangala": "Mars", "budha": "Mercury", "guru": "Jupiter", "shukra": "Venus", "shani": "Saturn"}


def sign_of(lon):
    return int(lon // 30) + 1


def _chart_and_sky(extra_rows=None, ut_error_hours=0.0, moon_lon=None):
    """Synthetic L1 facts + L0 sky for RECORD, consistent with its true UT (optionally built for a wrong UT)."""
    resolved = B.resolve_birth(B.parse_birth_record(RECORD))
    jd_true = resolved.jd_ut
    jd_l1 = jd_true + ut_error_hours / 24.0  # the instant L1 believed in
    longs = dict(LONGS)
    if moon_lon is not None:
        longs["chandra"] = moon_lon
    moon = longs["chandra"]
    span = 360.0 / 27.0
    idx = int(moon // span)
    lord = VIM[idx % 9]
    frac = (moon - idx * span) / span
    start = datetime.fromtimestamp((jd_l1 - 2440587.5) * 86400 - frac * YEARS[lord] * 365.25 * 86400, tz=timezone.utc)
    end = start + timedelta(days=YEARS[lord] * 365.25)
    nxt = VIM[(idx % 9 + 1) % 9]
    doc = W.chart_doc(
        birth_date=RECORD["local_date"],
        birth_utc_s=W.iso(resolved.utc),
        dasha={
            "mahadasha": [
                {"lord": lord, "start_utc": W.iso(start), "end_utc": W.iso(end)},
                {"lord": nxt, "start_utc": W.iso(end), "end_utc": W.iso(end + timedelta(days=YEARS[nxt] * 365.25))},
            ],
            "antardasha": [{"lord": lord, "start_utc": W.iso(start), "end_utc": W.iso(end)}],
        },
    )
    doc["birth"].update(lat=LAT, lon=LON, zone="Pacific/Auckland", utc_offset_minutes=720)
    for g, lon_deg in longs.items():
        doc["graha"][g]["sign"] = sign_of(lon_deg)
        doc["graha"][g]["longitude"] = lon_deg
    doc["lagna_sign"] = 1
    # sky: each body entered its natal sign 3 days before the instant L1 used; the previous sign before that
    rows, rid = [], 1
    for g, body in BODY.items():
        s = sign_of(longs[g])
        rows.append({"id": rid, "event_type": "ingress", "primary_body": body, "sign": SIGNS12[(s - 2) % 12], "event_jd": jd_true - 400.0}); rid += 1
        rows.append({"id": rid, "event_type": "ingress", "primary_body": body, "sign": SIGNS12[s - 1], "event_jd": jd_l1 - 3.0}); rid += 1
        # a later ingress so the table runs past the scan window (Moon is replaced by the test rows below when given)
        if g != "chandra":
            rows.append({"id": rid, "event_type": "ingress", "primary_body": body, "sign": SIGNS12[s % 12], "event_jd": jd_true + 4000.0}); rid += 1
    return doc, rows, resolved


def _bundle_manifest():
    card = CK.mk_card("SYN-MOON2", "transit", {"operand": "t"}, [CK.op("t", "transiting_graha", "transits", "chandra", target_bhavas=[2])], frame="chandra_lagna")
    final = CK.final_cards({"R1": {"category": "transit", "polarity": "promotive"}}, {})
    att = CK.attested_rules({"R1": [card]})
    units, recs, _ = U.build_units(final, att)
    bundle = U.build_bundle(att, recs)
    bsha = hashlib.sha256(U.canonical_bytes(bundle)).hexdigest()
    return {"manifest_schema": K.MANIFEST_SCHEMA, "bundle_sha256": bsha, "units": units}, bundle, bsha


def _scan(doc, rows, resolved, first, last, **kw):
    manifest, bundle, bsha = _bundle_manifest()
    chart = chart_from_fixture(doc)
    chart.birth = resolved.birth()
    return driver.scan(
        chart,
        sky_from_fixture({"rows": rows, "coverage_end_jd": utc_to_jd(datetime(2005, 1, 1, tzinfo=timezone.utc))}),
        dayatom.SolarSunrise(LAT, LON),
        first,
        last,
        bundle,
        manifest,
        manifest_sha256="m" * 64,
        bundle_sha256=bsha,
        **kw,
    )


def _runs(doc, n):
    out = ["?"] * n
    runs = doc["members"]["R1"]["runs"] + [[n, "X"]]
    for (s, v), (e, _x) in zip(runs, runs[1:]):
        out[s:e] = [v] * (e - s)
    return out


def _with_moon_window(rows, d, natal_moon_sign):
    """Moon: natal sign until s(D)+12h, then natal+1 until s(D+1)+12h, then natal+2. T (house 2) only on civil date D+1."""
    s1, s2 = noaa_sunrise_utc(d, LAT, LON), noaa_sunrise_utc(d + timedelta(days=1), LAT, LON)
    rows = [r for r in rows if r["primary_body"] != "Moon" or r["event_jd"] < utc_to_jd(datetime(2003, 1, 1, tzinfo=timezone.utc))]
    rows += [
        {"id": 5001, "event_type": "ingress", "primary_body": "Moon", "sign": SIGNS12[natal_moon_sign % 12], "event_jd": utc_to_jd(s1) + 0.5},
        {"id": 5002, "event_type": "ingress", "primary_body": "Moon", "sign": SIGNS12[(natal_moon_sign + 1) % 12], "event_jd": utc_to_jd(s2) + 0.5},
    ]
    return rows


def test_far_east_birth_day_mapping_state_flips_exactly_on_the_solar_day_after_the_ingress():
    doc, rows, resolved = _chart_and_sky()
    d = date(2003, 6, 10)
    moon_sign = sign_of(LONGS["chandra"])
    rows = _with_moon_window(rows, d, moon_sign)
    out = _scan(doc, rows, resolved, d - timedelta(days=2), d + timedelta(days=3))
    st = _runs(out, out["range"]["days"])
    # civil dates: D-2 D-1 D D+1 D+2 D+3  ->  house 1,1,1,2,3,3(NA/F): only D+1 has the Moon in house 2 at sunrise
    assert st[:5] == ["F", "F", "F", "T", "F"], st
    assert out["chart"]["birth_instant_source"] == "explicit_utc_offset_from_source_record" and out["chart"]["utc_offset_minutes"] == 720
    assert out["birth_consistency_problems"] == [] and out["sunrise"]["provider"].startswith("swisseph.rise_trans@local-solar-date")
    assert out["chart"]["birth_utc"].startswith("1999-05-19T18:40:00")  # 06:40 NZST minus 12 h = previous UT day


def test_wrong_ut_in_the_stored_facts_excludes_the_chart():
    # facts built as if the birth were 5.5 h later (an IST-fallback style slip): the sky/dasha tripwires must object
    doc, rows, resolved = _chart_and_sky(ut_error_hours=-6.5, moon_lon=100.0)
    chart = chart_from_fixture(doc)
    chart.birth = resolved.birth()
    sky = sky_from_fixture({"rows": rows, "coverage_end_jd": utc_to_jd(datetime(2005, 1, 1, tzinfo=timezone.utc))})
    problems = utc_consistency_problems(chart, sky)
    assert problems and any("Vimshottari" in p or "daśā" in p or "sky" in p for p in problems)
    with pytest.raises(B.ChartExcluded) as e:
        _scan(doc, rows, resolved, date(2003, 6, 8), date(2003, 6, 12))
    assert e.value.code == B.L1_UT_MISMATCH


def test_consistent_facts_pass_both_tripwires():
    doc, rows, resolved = _chart_and_sky()
    chart = chart_from_fixture(doc)
    chart.birth = resolved.birth()
    sky = sky_from_fixture({"rows": rows, "coverage_end_jd": utc_to_jd(datetime(2005, 1, 1, tzinfo=timezone.utc))})
    assert sky_sign_problems(chart, sky, utc_to_jd(resolved.utc)) == []
    assert dasha_start_problems(chart, utc_to_jd(resolved.utc)) == []


def test_sky_sign_tripwire_excuses_a_hair_from_the_boundary_but_not_more():
    doc, rows, resolved = _chart_and_sky(moon_lon=100.0)
    chart = chart_from_fixture(doc)
    chart.birth = resolved.birth()
    sky = sky_from_fixture({"rows": rows, "coverage_end_jd": utc_to_jd(datetime(2005, 1, 1, tzinfo=timezone.utc))})
    jd = utc_to_jd(resolved.utc)
    chart.grahas["chandra"].sign = sign_of(100.0) + 1  # L1 says the next sign
    chart.grahas["chandra"].longitude = 120.005  # 0.005 degree past a boundary: excused
    assert sky_sign_problems(chart, sky, jd) == []
    chart.grahas["chandra"].longitude = 125.0  # nowhere near a boundary: a real disagreement
    assert any("chandra" in p for p in sky_sign_problems(chart, sky, jd))


def test_dasha_start_tripwire_ignores_a_row_clipped_at_the_stored_window_start():
    doc, rows, resolved = _chart_and_sky()
    chart = chart_from_fixture(doc)
    chart.birth = resolved.birth()
    jd = utc_to_jd(resolved.utc)
    md = chart.md.rows[0]
    md.start_jd = 2433282.5  # clipped at 1950-01-01: the true start is not stored, only the lord can be checked
    assert dasha_start_problems(chart, jd) == []
    md.lord = "guru"
    assert dasha_start_problems(chart, jd)


def test_ist_path_is_unchanged_and_non_ist_without_an_offset_still_raises():
    doc, _rows, _res = _chart_and_sky()
    chart = chart_from_fixture(doc)
    chart.birth = type(chart.birth)(chart.birth.birth_date, chart.birth.birth_time_local, LAT, LON, "Pacific/Auckland", None, None)
    with pytest.raises(dayatom.TimeZoneNotSupported):
        driver.prepare_chart(chart, date(2003, 1, 1), date(2003, 1, 2))


def test_inconsistent_offset_instant_is_refused():
    doc, _rows, resolved = _chart_and_sky()
    chart = chart_from_fixture(doc)
    chart.birth = type(chart.birth)(resolved.record.local_date, resolved.record.local_time, LAT, LON, "x", resolved.utc + timedelta(hours=1), 720)
    with pytest.raises(B.ChartRefused):
        driver.prepare_chart(chart, date(2003, 1, 1), date(2003, 1, 2))


# ── CLI: the exit status and the reported reason ─────────────────────────────────────────
def _files(tmp_path, record):
    manifest, bundle, bsha = _bundle_manifest()
    doc, rows, _res = _chart_and_sky()
    (tmp_path / "m.json").write_text(json.dumps(manifest))
    (tmp_path / "b.json").write_bytes(U.canonical_bytes(bundle))
    (tmp_path / "chart.json").write_text(json.dumps(doc))
    (tmp_path / "sky.json").write_text(json.dumps({"rows": rows, "coverage_end_jd": utc_to_jd(datetime(2005, 1, 1, tzinfo=timezone.utc))}))
    (tmp_path / "rec.json").write_text(json.dumps(record))
    return ["scan", "--manifest", str(tmp_path / "m.json"), "--bundle", str(tmp_path / "b.json"), "--fixture", str(tmp_path / "chart.json"),
            "--sky-fixture", str(tmp_path / "sky.json"), "--birth-record", str(tmp_path / "rec.json"), "--first", "2003-06-08", "--last", "2003-06-12",
            "--out", str(tmp_path / "out.json")]


def test_cli_refuses_a_record_without_an_offset(tmp_path, capsys):
    rec = {k: v for k, v in RECORD.items() if k != "utc_offset_minutes"}
    assert cli.main(_files(tmp_path, rec)) == 3
    out = json.loads(capsys.readouterr().out)
    assert out == {"chart": "not_evaluated", "detail": out["detail"], "kind": "ChartRefused", "reason": B.OFFSET_MISSING}
    assert not (tmp_path / "out.json").exists()


def test_cli_excludes_a_tz_database_disagreement_and_writes_nothing(tmp_path, capsys):
    assert cli.main(_files(tmp_path, dict(RECORD, utc_offset_minutes=330))) == 3
    out = json.loads(capsys.readouterr().out)
    assert out["reason"] == B.TZ_DISAGREEMENT and out["kind"] == "ChartExcluded"
    assert not (tmp_path / "out.json").exists()


def test_cli_evaluates_a_good_record_and_resolve_births_reports_the_counts(tmp_path, capsys):
    assert cli.main(_files(tmp_path, RECORD)) == 0
    res = json.loads((tmp_path / "out.json").read_text())
    assert res["chart"]["utc_offset_minutes"] == 720 and res["members"]["R1"]["chart_level"] is False
    capsys.readouterr()
    (tmp_path / "recs.json").write_text(json.dumps([RECORD, dict(RECORD, utc_offset_minutes=None), dict(RECORD, utc_offset_minutes=330)]))
    assert cli.main(["resolve-births", "--records", str(tmp_path / "recs.json"), "--out", str(tmp_path / "r.json")]) == 0
    tally = json.loads(capsys.readouterr().out)
    assert tally["accepted"] == 1 and tally["refused"] == 1 and tally["excluded"] == 1
    assert tally["refused_by_reason"] == {B.OFFSET_MISSING: 1} and tally["excluded_by_reason"] == {B.TZ_DISAGREEMENT: 1}
