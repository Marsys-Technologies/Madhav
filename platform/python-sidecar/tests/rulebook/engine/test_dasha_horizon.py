"""Per-family horizon inputs (SUR-RB-15): dasha_first_day, transit_first_day, and no extrapolation before the first stored daśā row.

The scorer builds each family's horizon from these fields; the engine itself never fills a day it has no stored input for.
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta, timezone

import pytest

from services.rulebook.engine import constants as K
from services.rulebook.engine import dayatom, driver
from services.rulebook.engine import units as U
from services.rulebook.engine.chart import chart_from_fixture, utc_to_jd
from services.rulebook.engine.sky import sky_from_fixture
from tests.rulebook import _cards as E1

from . import _cardkit as CK
from . import _world as W

FIRST, LAST = date(2002, 5, 25), date(2002, 6, 20)


def _rules():
    mix = CK.mk_card(  # dasha-plane rule with a natal conjunct that is always FALSE here (the fixture's Venus is direct)
        "SYN-MIX", "dasha", {"op": "AND", "args": [{"operand": "md"}, {"operand": "r"}]},
        [CK.op("md", "dasha_lord", "is_dasha_lord", "shukra"), CK.op("r", "natal_graha", "retrograde", "shukra")], polarity="obstructive",
    )
    ident = CK.mk_card("SYN-IDM", "dasha", {"operand": "md"}, [CK.op("md", "dasha_lord", "is_dasha_lord", "shukra")], polarity="promotive")
    sat = CK.saturn_transit("SYN-SATH", (3, 6, 11))
    natal = E1.natal_card()
    cards = {"R1": [mix], "R2": [ident], "R3": [sat], "R4": [natal]}
    meta = {"R1": ("dasha", "obstructive"), "R2": ("dasha", "promotive"), "R3": ("transit", "promotive"), "R4": ("natal_promise", "promotive")}
    final = CK.final_cards({k: {"category": c, "polarity": p} for k, (c, p) in meta.items()}, {})
    att = CK.attested_rules(cards)
    units, recs, _ = U.build_units(final, att)
    bundle = U.build_bundle(att, recs)
    bsha = hashlib.sha256(U.canonical_bytes(bundle)).hexdigest()
    return {"manifest_schema": K.MANIFEST_SCHEMA, "bundle_sha256": bsha, "units": units}, bundle, bsha


def _scan(dasha_start, saturn_first, birth="1990-03-04", birth_utc="1990-03-04T03:30:00Z", n_md=1):
    manifest, bundle, bsha = _rules()
    dasha = W.dasha_tables(dasha_start, "shukra", n_md)
    doc = W.chart_doc(birth_date=birth, birth_utc_s=birth_utc, dasha=dasha)
    sky = W.sky_doc(W.utc(2002, 1, 1), W.utc(2004, 1, 1))
    cut = utc_to_jd(saturn_first)
    sat = [  # Saturn's stored rows begin at ``saturn_first``: nothing is known before it
        {"id": 9001, "event_type": "ingress", "primary_body": "Saturn", "sign": "Aquarius", "event_jd": cut},
        {"id": 9002, "event_type": "ingress", "primary_body": "Saturn", "sign": "Pisces", "event_jd": cut + 900.0},
    ]
    sky["rows"] = [r for r in sky["rows"] if r["primary_body"] != "Saturn"] + sat
    prov = dayatom.TableSunrise(W.sunrise_table(date(1990, 3, 1), date(2002, 12, 31)))
    out = driver.scan(chart_from_fixture(doc), sky_from_fixture(sky), prov, FIRST, LAST, bundle, manifest, manifest_sha256="m" * 64, bundle_sha256=bsha)
    return out


def _decode(out, rid):
    n = out["range"]["days"]
    arr = ["?"] * n
    runs = out["members"][rid]["runs"] + [[n, "X"]]
    for (s, v), (e, _x) in zip(runs, runs[1:]):
        arr[s:e] = [v] * (e - s)
    return arr


def test_horizon_inputs_are_the_first_sunrise_at_or_after_the_first_stored_input():
    # rows begin 2002-06-10 01:00Z; sunrise is 00:30Z, so the first day the daśā exists at sunrise is 06-11
    out = _scan(W.utc(2002, 6, 10, 1, 0), W.utc(2002, 4, 10, 12, 0))
    h = out["horizon_inputs"]
    assert h["dasha_first_day"] == "2002-06-11"
    assert h["transit_first_day"] == "2002-04-11"  # Saturn (the latest body) is first known 2002-04-10 12:00Z
    assert h["horizon_start_12y"] == "2002-03-04" and h["dasha_starts_after_12th_birthday"] is True


def test_dasha_first_day_is_the_birth_day_when_rows_precede_birth_and_flag_is_false_when_rows_start_before_the_12th_birthday():
    out = _scan(W.utc(2001, 1, 1, 0, 0), W.utc(2002, 4, 10, 12, 0), n_md=2)
    h = out["horizon_inputs"]
    assert h["dasha_first_day"] == "2001-01-01"  # rows begin 00:00Z, sunrise 00:30Z the same day
    assert h["dasha_starts_after_12th_birthday"] is False  # 2001-01-01 is before the 12th birthday, 2002-03-04
    out2 = _scan(W.utc(1990, 3, 1), W.utc(2002, 4, 10, 12, 0))
    assert out2["horizon_inputs"]["dasha_first_day"] == "1990-03-05"  # rows predate birth (03:30Z on 03-04): first sunrise after the birth instant


def test_no_dasha_state_before_the_first_stored_row_even_when_a_natal_conjunct_is_false():
    out = _scan(W.utc(2002, 6, 10, 1, 0), W.utc(2002, 4, 10, 12, 0))
    n = out["range"]["days"]
    days = [FIRST + timedelta(days=i) for i in range(n)]
    mix, ident = _decode(out, "R1"), _decode(out, "R2")
    for d, a, b in zip(days, mix, ident):
        if d < date(2002, 6, 11):
            assert (a, b) == ("N", "N"), d  # not extrapolated, and not F from the natal conjunct alone
        else:
            assert (a, b) == ("F", "T"), d  # stored rows exist: ordinary Kleene result (natal conjunct FALSE, MD = Venus)
    # other planes are untouched by the dasha mask
    assert set(_decode(out, "R4")) == {"F"}
    assert set(_decode(out, "R3")) <= {"T", "F"}


def test_transit_rule_reads_not_assessed_before_its_bodys_first_stored_ingress():
    out = _scan(W.utc(2002, 6, 10, 1, 0), W.utc(2002, 6, 1, 12, 0))
    r3 = _decode(out, "R3")
    days = [FIRST + timedelta(days=i) for i in range(len(r3))]
    for d, v in zip(days, r3):
        assert (v == "N") == (d < date(2002, 6, 2)), (d, v)
    assert out["horizon_inputs"]["transit_first_day"] == "2002-06-02"


def test_chart_without_daśā_rows_has_no_dasha_first_day_and_flags_it():
    manifest, bundle, bsha = _rules()
    doc = W.chart_doc(birth_date="1990-03-04", birth_utc_s="1990-03-04T03:30:00Z", dasha={"mahadasha": [], "antardasha": []})
    sky = W.sky_doc(W.utc(2002, 1, 1), W.utc(2004, 1, 1))
    out = driver.scan(chart_from_fixture(doc), sky_from_fixture(sky), dayatom.TableSunrise(W.sunrise_table(date(1990, 3, 1), date(2002, 12, 31))),
                      FIRST, LAST, bundle, manifest, manifest_sha256="m" * 64, bundle_sha256=bsha)
    assert out["horizon_inputs"]["dasha_first_day"] is None and out["horizon_inputs"]["dasha_starts_after_12th_birthday"] is True
    assert set(_decode(out, "R1")) == {"N"} and set(_decode(out, "R2")) == {"N"}


def test_twelfth_birthday_handles_29_february():
    assert driver._twelfth_birthday(date(1992, 2, 29)) == date(2004, 2, 29)
    assert driver._twelfth_birthday(date(1996, 2, 29)) == date(2008, 2, 29)
    assert driver._twelfth_birthday(date(2000, 2, 29)) == date(2012, 2, 29)
    assert driver._twelfth_birthday(date(1988, 2, 29)) == date(2000, 2, 29)
    assert driver._twelfth_birthday(date(1900, 3, 1)) == date(1912, 3, 1)
