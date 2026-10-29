"""E4 date-range driver: states per sunrise day against an independent plain-arithmetic expectation."""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import date, datetime, timedelta, timezone

import pytest

from services.rulebook.ast import Tri
from services.rulebook.compiler import compile_card
from services.rulebook.engine import constants as K
from services.rulebook.engine import dayatom, driver
from services.rulebook.engine import units as U
from services.rulebook.engine.chart import chart_from_fixture
from services.rulebook.engine.evaluator import card_outcome_at, tally_day
from services.rulebook.engine.irtree import operand_table
from services.rulebook.engine.plan import plan_card
from services.rulebook.engine.sky import sky_from_fixture
from tests.rulebook import _cards as E1

from . import _cardkit as CK
from . import _world as W

FIRST = date(2027, 2, 10)
LAST = date(2027, 3, 31)
BIRTH_UTC = "2020-02-15T03:30:00Z"


def _cards():
    sat = CK.saturn_transit("SYN-SAT", (3, 6, 11))
    ident = CK.mk_card(
        "SYN-ID",
        "dasha",
        {"op": "AND", "args": [{"operand": "md"}, {"operand": "ad"}]},
        [CK.op("md", "dasha_lord", "is_dasha_lord", "shukra"), CK.op("ad", "antardasha_lord", "is_antardasha_lord", "rahu")],
        polarity="obstructive",
    )
    natal = E1.natal_card()  # Venus retrograde (fixture: not retrograde)
    rahu = CK.saturn_transit("SYN-RAH", (5,), graha="rahu")
    return {"R1": [sat], "R2": [E1.dasha_card()], "R3": [ident], "R4": [natal], "R5": [rahu]}, {
        "R1": ("transit", "promotive"),
        "R2": ("dasha", "obstructive"),
        "R3": ("dasha", "obstructive"),
        "R4": ("natal_promise", "promotive"),
        "R5": ("transit", "promotive"),
    }


def _manifest_bundle():
    cards, meta = _cards()
    rows = {rid: {"category": c, "polarity": p} for rid, (c, p) in meta.items()}
    final = CK.final_cards(rows, {})
    att = CK.attested_rules(cards)
    units, recs, counts = U.build_units(final, att)
    bundle = U.build_bundle(att, recs)
    bsha = hashlib.sha256(U.canonical_bytes(bundle)).hexdigest()
    manifest = {"manifest_schema": K.MANIFEST_SCHEMA, "bundle_sha256": bsha, "units": units}
    return manifest, bundle, bsha


def _world(first=FIRST, last=LAST):
    dasha = W.dasha_tables(W.utc(2020, 1, 1), "shukra", 3)
    doc = W.chart_doc(birth_date="2020-02-15", birth_utc_s=BIRTH_UTC, dasha=dasha)
    sky = W.sky_doc(W.utc(2020, 1, 1), W.utc(2030, 1, 1))
    return doc, sky, dasha


def _scan(first=FIRST, last=LAST, doc=None, **kw):
    manifest, bundle, bsha = _manifest_bundle()
    d, sky, _ = _world()
    doc = doc or d
    prov = dayatom.TableSunrise(W.sunrise_table(first, last))
    return driver.scan(
        chart_from_fixture(doc), sky_from_fixture(sky), prov, first, last, bundle, manifest, manifest_sha256="m" * 64, bundle_sha256=bsha, **kw
    )


def _decode(entry, n):
    out = ["?"] * n
    runs = entry["runs"] + [[n, "X"]]
    for (s, v), (e, _x) in zip(runs, runs[1:]):
        for i in range(s, e):
            out[i] = v
    return out


def _lord_at(rows, t):
    for r in rows:
        a = datetime.strptime(r["start_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        b = datetime.strptime(r["end_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        if a <= t < b:
            return r["lord"]
    return None


def test_scan_states_equal_plain_arithmetic_for_every_day_and_member():
    out = _scan()
    doc, sky, dasha = _world()
    n = (LAST - FIRST).days + 1
    assert out["range"]["days"] == n and out["day_convention"] == K.DAY_CONVENTION_ID
    assert set(out["members"]) == {"R1", "R2", "R3", "R4"}  # R5 reads Rahu: excluded, absent
    signs = {g: v["sign"] for g, v in doc["graha"].items()}
    r1, r2, r3, r4 = (_decode(out["members"][k], n) for k in ("R1", "R2", "R3", "R4"))
    moon = signs["chandra"]
    seen_t = seen_f = set()
    na_r2 = 0
    for i in range(n):
        d = FIRST + timedelta(days=i)
        t = datetime(d.year, d.month, d.day, 0, 30, tzinfo=timezone.utc)
        jd = W.jd_of(t)
        # R1: Saturn transit house from the Moon sign
        s = W.expected_sign(sky, "Saturn", jd)
        want = "N" if s is None else ("T" if ((s - moon) % 12) + 1 in (3, 6, 11) else "F")
        assert r1[i] == want, (d, r1[i], want)
        md, ad = _lord_at(dasha["mahadasha"], t), _lord_at(dasha["antardasha"], t)
        # R3: MD Venus and AD Rahu: identity only, evaluated even though Rahu is a node
        assert r3[i] == ("N" if md is None or ad is None else ("T" if (md == "shukra" and ad == "rahu") else "F")), d
        # R2: AD lord 6th or 8th from the MD lord (generic: N when either lord is a node)
        if md is None or ad is None:
            w2 = "N"
        elif md in ("rahu", "ketu") or ad in ("rahu", "ketu"):
            w2 = "N"
        else:
            h = ((signs[ad] - signs[md]) % 12) + 1
            w2 = "T" if h in (6, 8) else "F"
        assert r2[i] == w2, (d, md, ad, r2[i], w2)
        na_r2 += w2 == "N"
        assert r4[i] == "F"  # Venus is direct in the fixture
    assert na_r2 > 0, "the window must include node-lord days"
    assert "T" in r3 and "F" in r3, "the window must cross the Rahu antardasha start"


def test_one_range_scan_equals_one_day_scans():
    whole = _scan()
    n = whole["range"]["days"]
    for k in ("R1", "R2", "R3"):
        full = _decode(whole["members"][k], n)
        for i in (0, 7, 18, 19, 20, 33, n - 1):
            d = FIRST + timedelta(days=i)
            one = _scan(d, d)
            assert _decode(one["members"][k], 1)[0] == full[i], (k, d)


def test_days_before_birth_are_not_assessed_even_inside_the_daśā_table():
    out = _scan(date(2020, 1, 20), date(2020, 3, 5))
    n = out["range"]["days"]
    r3 = _decode(out["members"]["R3"], n)
    r2 = _decode(out["members"]["R2"], n)
    birth_day_index = (date(2020, 2, 15) - date(2020, 1, 20)).days
    # sunrise 00:30Z precedes birth 03:30Z on 2020-02-15, so that date is also pre-birth
    assert set(r3[: birth_day_index + 1]) == {"N"} and set(r2[: birth_day_index + 1]) == {"N"}
    assert r3[birth_day_index + 1] in ("T", "F")


def test_a_non_ist_chart_raises_and_nothing_is_written():
    doc, _sky, _d = _world()
    bad = copy.deepcopy(doc)
    bad["birth"]["zone"] = "Asia/Dhaka"
    with pytest.raises(dayatom.TimeZoneNotSupported):
        _scan(doc=bad)
    bad["birth"]["zone"] = None
    with pytest.raises(dayatom.TimeZoneNotSupported):
        _scan(doc=bad)


def test_scan_refuses_a_bundle_the_manifest_does_not_name():
    manifest, bundle, bsha = _manifest_bundle()
    doc, sky, _ = _world()
    prov = dayatom.TableSunrise(W.sunrise_table(FIRST, LAST))
    with pytest.raises(driver.ScanRefused):
        driver.scan(chart_from_fixture(doc), sky_from_fixture(sky), prov, FIRST, LAST, bundle, manifest, manifest_sha256="m" * 64, bundle_sha256="f" * 64)
    tampered = copy.deepcopy(bundle)
    tampered["rules"]["R1"]["rule_sha256"] = "0" * 64
    with pytest.raises(driver.ScanRefused):
        driver.scan(chart_from_fixture(doc), sky_from_fixture(sky), prov, FIRST, LAST, tampered, manifest, manifest_sha256="m" * 64, bundle_sha256=bsha)


def test_output_is_deterministic_and_carries_the_pins():
    a, b = _scan(include_sunrise=True), _scan(include_sunrise=True)
    assert driver.compact_bytes(a) == driver.compact_bytes(b)
    assert a["manifest_sha256"] == "m" * 64 and a["node_policy"] == K.NODE_POLICY_ID and a["chart"]["zone"] == "Asia/Kolkata"
    assert a["chart"]["tzdb"] and a["coverage"]["sky_fingerprint_sha256"]
    assert len(a["sunrise"]["utc_epoch_seconds"]) == a["range"]["days"]
    assert a["members"]["R4"]["chart_level"] is True and len(a["members"]["R4"]["runs"]) == 1
    assert a["members"]["R1"]["chart_level"] is False


def test_saturation_is_a_report_not_a_gate():
    sat = _scan()["saturation"]
    assert sat["status"] == "report_only" and sat["gate"] is None
    c = sat["per_card"]["R1"]
    assert 0.0 <= c["duty"] <= 1.0 and c["days"] == c["true"] + c["false"] + c["not_assessed"]
    assert list(c["graha_occupancy"]) == ["shani@3,6,11"] and c["duty_minus_max_occupancy"] == pytest.approx(0.0)
    assert "shani/promotive" in sat["per_graha_polarity_union"]


def test_write_states_returns_the_file_hash(tmp_path):
    out = _scan()
    p = tmp_path / "s.json"
    sha = driver.write_states(out, str(p))
    assert hashlib.sha256(p.read_bytes()).hexdigest() == sha
    assert json.loads(p.read_text())["states_schema"] == K.STATES_SCHEMA


# ── N of 3: testimony never counts ──────────────────────────────────────
def _plan_of(card):
    res = compile_card(card)
    return plan_card(res.ir, operand_table(card))


def test_testimony_is_a_flagged_count_and_never_increments_n():
    verse = _plan_of(CK.saturn_transit("SYN-V", (3,)))
    tcard = CK.mk_card("SYN-T", "dasha", {"operand": "md"}, [CK.op("md", "dasha_lord", "is_dasha_lord", "guru")], provenance="commentarial_practice")
    tcard["commentarial_source"] = {"author": "Synthetic Author", "work": "Synthetic Commentary"}
    testi = _plan_of(tcard)
    outcomes = [card_outcome_at(verse, Tri.FALSE), card_outcome_at(testi, Tri.TRUE)]
    t = tally_day(outcomes, "promotive")
    assert t["categories_matched"] == 0 and t["categories"]["dasha"] == "not_assessed"  # testimony alone decides nothing
    assert t["testimony_matched_flagged"] == 1
    outcomes2 = [card_outcome_at(verse, Tri.TRUE), card_outcome_at(testi, Tri.TRUE)]
    assert tally_day(outcomes2, "promotive")["categories_matched"] == 1  # only the verse-cited transit card counted
    # promotive and obstructive are never summed
    assert "categories_matched" in tally_day(outcomes2, "obstructive") and tally_day(outcomes2, "obstructive")["categories_matched"] == 0
