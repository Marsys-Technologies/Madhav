"""Day atom, zone fail-closed (DF-04), sky table, chart assembly, read-only guard."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from services.rulebook.engine import constants as K
from services.rulebook.engine import dayatom, dbload
from services.rulebook.engine.chart import Birth, ChartDataError, DashaLevel, DashaRow, chart_from_fixture, house_from
from services.rulebook.engine.sky import SkyDataError, SkyTable

from . import _world as W


# ── zone ──────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("zone", [None, "", "UTC", "Asia/Dhaka", "Asia/Kathmandu", "Asia/Colombo", "America/New_York"])
def test_non_ist_zone_raises_never_falls_back(zone):
    with pytest.raises(dayatom.TimeZoneNotSupported):
        dayatom.require_ist(zone, date(2000, 1, 1), date(2001, 1, 1))


def test_ist_zone_names_accepted_and_pre_1955_offsets_refused():
    dayatom.require_ist("Asia/Kolkata", date(1990, 1, 1), date(2030, 12, 31))
    dayatom.require_ist("Asia/Calcutta", date(1990, 1, 1), date(1992, 1, 1))
    with pytest.raises(dayatom.TimeZoneNotSupported):
        dayatom.require_ist("Asia/Kolkata", date(1942, 1, 1), date(1946, 1, 1))  # +06:30 wartime


def test_sunrise_provider_refuses_non_ist_offset():
    with pytest.raises(dayatom.TimeZoneNotSupported):
        dayatom.PanchangEngineSunrise(20.3, 85.8, tz_offset_minutes=360)


def test_birth_utc_is_local_minus_five_thirty_and_ist_only():
    b = Birth(date(2000, 3, 4), "09:00:00", 20.3, 85.8, "Asia/Kolkata")
    assert dayatom.birth_utc(b) == datetime(2000, 3, 4, 3, 30, tzinfo=timezone.utc)
    with pytest.raises(dayatom.TimeZoneNotSupported):
        dayatom.birth_utc(Birth(date(2000, 3, 4), "09:00:00", 20.3, 85.8, "Asia/Dhaka"))


def test_grid_is_strictly_increasing_one_sunrise_per_date():
    prov = dayatom.TableSunrise(W.sunrise_table(date(2024, 1, 1), date(2024, 1, 10)))
    g = dayatom.build_grid(date(2024, 1, 1), date(2024, 1, 10), prov)
    assert g.n == 10 and g.date_at(3) == date(2024, 1, 4) and g.last == date(2024, 1, 10)
    assert all(b - a == pytest.approx(1.0) for a, b in zip(g.sunrise_jd, g.sunrise_jd[1:]))
    with pytest.raises(ChartDataError):
        dayatom.build_grid(date(2024, 1, 1), date(2024, 1, 11), prov)  # no instant supplied for the 11th


def test_panchang_engine_sunrise_matches_a_stored_panchanga_row():
    """panchanga_daily (Bhubaneswar) holds sunrise 2026-07-08T23:42:55Z for civil date 2026-07-09."""
    pytest.importorskip("swisseph")
    got = dayatom.PanchangEngineSunrise(20.27, 85.84).sunrise_utc(date(2026, 7, 9))
    assert got == datetime(2026, 7, 8, 23, 42, 55, tzinfo=timezone.utc)


# ── houses ────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("ref,sign,house", [(1, 1, 1), (1, 12, 12), (12, 1, 2), (7, 6, 12), (3, 3, 1), (11, 2, 4)])
def test_house_from_is_inclusive_whole_sign(ref, sign, house):
    assert house_from(ref, sign) == house
    assert house_from(None, sign) is None and house_from(ref, None) is None


# ── sky ───────────────────────────────────────────────────────────────────
def _rows(*spec):
    return [{"id": i, "event_type": "ingress", "primary_body": b, "sign": s, "event_jd": jd} for i, (b, s, jd) in enumerate(spec)]


def test_sky_sign_is_latest_ingress_at_or_before_instant():
    sky = SkyTable(_rows(("Moon", "Aries", 100.0), ("Moon", "Taurus", 102.0), ("Moon", "Gemini", 104.0)), coverage_end_jd=104.0)
    assert sky.sign_at("Moon", 99.9) is None  # before first row
    assert sky.sign_at("Moon", 100.0) == 1  # an ingress AT the instant has happened
    assert sky.sign_at("Moon", 101.999) == 1 and sky.sign_at("Moon", 102.0) == 2
    assert sky.sign_at("Moon", 104.0) == 3 and sky.sign_at("Moon", 104.001) is None  # beyond coverage
    assert sky.sign_at("Sun", 101.0) is None  # no rows


def test_sky_retrograde_reentry_is_one_sign_back_and_a_skipped_ingress_breaks_the_interval():
    ok = SkyTable(_rows(("Mars", "Leo", 10.0), ("Mars", "Virgo", 20.0), ("Mars", "Leo", 30.0)), coverage_end_jd=40.0)
    assert ok.sign_at("Mars", 25.0) == 6 and ok.sign_at("Mars", 35.0) == 5 and ok.chain_defects["Mars"] == 0
    bad = SkyTable(_rows(("Mars", "Leo", 10.0), ("Mars", "Libra", 20.0)), coverage_end_jd=40.0)  # Virgo missing
    assert bad.chain_defects["Mars"] == 1
    assert bad.sign_at("Mars", 15.0) is None  # the interval that hides an ingress is unknown
    assert bad.sign_at("Mars", 25.0) == 7


def test_sky_rejects_duplicate_instants_and_unknown_signs():
    with pytest.raises(SkyDataError):
        SkyTable(_rows(("Mars", "Leo", 10.0), ("Mars", "Virgo", 10.0)))
    with pytest.raises(SkyDataError):
        SkyTable(_rows(("Mars", "Ophiuchus", 10.0)))


def test_sky_fingerprint_is_stable_and_sensitive():
    a = SkyTable(_rows(("Moon", "Aries", 1.0), ("Moon", "Taurus", 3.0)), 5.0)
    b = SkyTable(_rows(("Moon", "Aries", 1.0), ("Moon", "Taurus", 3.0)), 5.0)
    c = SkyTable(_rows(("Moon", "Aries", 1.0), ("Moon", "Taurus", 3.00001)), 5.0)
    assert a.fingerprint() == b.fingerprint() != c.fingerprint()


# ── chart assembly from fact rows (the DB loader's pure half) ─────────────
def _fact(i, cat, subj, key, text=None, js=None):
    return (f"f{i}", cat, subj, key, text, None, js)


def _facts():
    f, i = [], 0
    signs = {"SUN": "Leo", "MOON": "Taurus", "MAR": "Gemini", "MER": "Aries", "JUP": "Sagittarius", "VEN": "Pisces", "SAT": "Aquarius", "RAH_MEAN": "Libra", "KET_MEAN": "Aries", "LAGNA": "Aries"}
    for subj, sg in signs.items():
        i += 1
        f.append(_fact(i, "graha_position", subj, "sign", sg))
        if subj != "LAGNA":
            i += 1
            f.append(_fact(i, "graha_position", subj, "retrograde_flag", "direct"))
    for h in range(1, 13):
        i += 1
        f.append(_fact(i, "lord_in_house_per_varga", f"D1_H{h}", "lord_placement", f"x_in_H{h}", {"lord": ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"][h - 1]}))
    return f, i


def test_build_chart_reads_vocabulary_and_marks_duplicates_and_unknowns_missing():
    facts, i = _facts()
    facts.append(_fact(i + 1, "graha_position", "SUN", "sign", "Virgo"))  # a second sign row for the Sun: non-unique
    facts[:] = [r for r in facts if not (r[2] == "MER" and r[3] == "retrograde_flag")]
    facts.append(_fact(i + 2, "graha_position", "MER", "retrograde_flag", "stationary"))  # outside the vocabulary
    b = Birth(date(2000, 3, 4), "09:00:00", 20.3, 85.8, "Asia/Kolkata")
    ch = dbload.build_chart("k", b, facts, [])
    assert ch.lagna_sign == 1 and ch.sign_of("chandra") == 2 and ch.sign_of("rahu") == 7
    assert ch.sign_of("surya") is None  # two rows -> missing, never an ORDER BY winner
    assert ch.graha("budha").retrograde is None
    assert ch.graha("guru").retrograde is False
    assert ch.diagnostics["non_unique_fact"] == 1 and ch.diagnostics["unknown_retrograde_vocabulary"] == 1
    assert ch.sign_lord(5) == "surya" and ch.sign_lord(1) == "mangala"  # lords from the chart's own D1 rows
    assert ch.aspected_signs("surya") is None  # no aspect rows -> unknown


def test_daśā_levels_reject_overlap_count_gaps_and_use_half_open_intervals():
    jd = lambda x: 2460000.0 + x
    lvl = DashaLevel([DashaRow("guru", jd(0), jd(10)), DashaRow("shani", jd(10), jd(20)), DashaRow("budha", jd(25), jd(30))])
    assert lvl.defects == 1
    assert lvl.lord_at(jd(0)) == "guru" and lvl.lord_at(jd(9.999)) == "guru" and lvl.lord_at(jd(10)) == "shani"
    assert lvl.lord_at(jd(20)) is None and lvl.lord_at(jd(22)) is None and lvl.lord_at(jd(-1)) is None
    with pytest.raises(ChartDataError):
        DashaLevel([DashaRow("guru", jd(0), jd(10)), DashaRow("shani", jd(9), jd(20))])


def test_read_only_cursor_refuses_anything_but_select():
    class Cur:
        def execute(self, sql, params=None):
            self.last = sql

        def close(self):
            pass

    cur = dbload._ReadOnlyCursor(Cur())
    cur.execute("SELECT 1")
    cur.execute("  with x as (select 1) select * from x")
    for bad in ("UPDATE t SET a=1", "insert into t values (1)", "DELETE FROM t", "create table t(a int)", "drop table t", ""):
        with pytest.raises(dbload.ReadOnlyViolation):
            cur.execute(bad)


def test_fixture_reader_requires_its_schema_and_rejects_bad_signs():
    doc = W.chart_doc()
    assert chart_from_fixture(doc).lagna_sign == 1
    bad = dict(doc, fixture_schema="x")
    with pytest.raises(ChartDataError):
        chart_from_fixture(bad)
    bad2 = dict(doc, lagna_sign=13)
    with pytest.raises(ChartDataError):
        chart_from_fixture(bad2)


def test_readiness_lists_what_will_read_as_not_assessed():
    from services.rulebook.engine.chart import readiness

    full = chart_from_fixture(W.chart_doc())
    assert readiness(full) == []
    doc = W.chart_doc()
    doc["lagna_sign"] = None
    doc["graha"]["guru"]["sign"] = None
    doc["house_lord"]["4"] = None
    doc["aspected_houses"]["mangala"] = None
    doc["dasha"] = {"mahadasha": [], "antardasha": []}
    probs = readiness(chart_from_fixture(doc))
    for needle in ("lagna sign missing", "guru: natal sign missing", "house 4: D1 lord missing", "mangala: aspect rows missing", "no Vimshottari level-1 rows"):
        assert needle in probs
