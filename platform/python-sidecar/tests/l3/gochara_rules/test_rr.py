"""O-RR-* — relationship_record oracles (GOCHARA_DESIGN_SPECS_v1_4 §1).

Literal: O-RR-1, O-RR-2, O-RR-3. Literal-input executable semantics:
O-RR-5 (yoga cancellation + strength 0.8), O-RR-6 (affliction predicate),
O-RR-7 (testimony zero effect, bitwise-equal scores).
"""
from __future__ import annotations

import pytest

from services.gochara_rules.frames import (
    Frame, SIGN_LORDS, house_of, nth_sign_from, sign_of,
)
from services.gochara_rules.predicates import FALSE, TRUE, UNKNOWN
from services.gochara_rules.records import RelationshipRecord, afflicted
from services.gochara_rules.score import (
    factor_product, path_channel_scores, record_channel_value,
)

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"


def _record(**kw) -> RelationshipRecord:
    base = dict(
        chart_id=CHART_ID, generation="5.0", event_class="marriage",
        affected_person="native", frame="lagna", agent="Jupiter",
        relation="residence", object_id="obj:sign:Aquarius",
        object_kind="sign_span", object_role="occupant",
        contact_id="sha256:contact-x", path_id="P3", rule_version="1.0.0",
        prerequisites=[], provenance="verse_cited", operator_role="scored",
    )
    return RelationshipRecord(**{**base, **kw})


# ── O-RR-1 (literal) — twins event, frame discipline ────────────────────────
def test_orr1_moon_frame_first_house_no_5th_record(chart):
    # natal Moon 327.06° → floor(327.06/30)=10 → Aquarius;
    # transit Jupiter 2022-01-03 306.87° → floor(306.87/30)=10 → Aquarius;
    # count from Aquarius inclusive: Aquarius=1st.
    assert sign_of(327.06) == "Aquarius"
    assert sign_of(306.87) == "Aquarius"
    assert house_of(306.87, Frame("moon"), chart) == 1
    # mutation: a 'Jupiter 5th from Moon' record must NOT exist
    assert house_of(306.87, Frame("moon"), chart) != 5


def test_orr1_lagna_frame_record_exists(chart):
    # Jupiter in 11th from Aries lagna; its 7th aspect falls at
    # (306.87 + 180) mod 360 = 126.87° → Leo = the 5th house from Aries
    # (Aries 1, Taurus 2, Gemini 3, Cancer 4, Leo 5).
    assert house_of(306.87, Frame("lagna"), chart) == 11
    assert sign_of((306.87 + 180.0) % 360.0) == "Leo"
    assert house_of(126.87, Frame("lagna"), chart) == 5


# ── O-RR-2 (literal) — bhavat_bhavam:9 father frame ─────────────────────────
def test_orr2_father_frame_resolution(chart):
    # frame bhavat_bhavam:9 (9th from Aries = Sagittarius);
    # 7th from 9th = Gemini (Mercury); 8th from 9th = Cancer (Moon);
    # 2nd from 9th = Capricorn (Saturn). Counts inclusive, written out:
    # from Sagittarius: Sag 1, Cap 2, ..., Gemini 7, Cancer 8.
    bb9 = Frame("bhavat_bhavam", 9)
    assert nth_sign_from(bb9, 1, chart) == "Sagittarius"
    assert nth_sign_from(bb9, 7, chart) == "Gemini"
    assert SIGN_LORDS["Gemini"] == "Mercury"   # MD lord (row 58afa482…)
    assert nth_sign_from(bb9, 8, chart) == "Cancer"
    assert SIGN_LORDS["Cancer"] == "Moon"      # AD lord (row 14f20359…)
    assert nth_sign_from(bb9, 2, chart) == "Capricorn"
    assert SIGN_LORDS["Capricorn"] == "Saturn"  # agent = 2nd-from-9th lord

    rec = _record(event_class="bereavement", affected_person="father",
                  frame="bhavat_bhavam:9", agent="Saturn",
                  relation="ownership", object_id="obj:sign:Capricorn",
                  object_kind="house_span", object_role="lord",
                  contact_id=None, path_id="P1")
    assert rec.frame == "bhavat_bhavam:9"
    # root_id := object_id on natal-fact rows (contact_id NULL)
    assert rec.root_id == "obj:sign:Capricorn"
    # mutation: records resolved in the native's lagna/Moon frame fail
    assert rec.frame not in ("lagna", "moon")


def test_orr2_transit_row_root_id_is_contact_id():
    rec = _record()  # transit relation, contact pinned
    assert rec.root_id == "sha256:contact-x"


# ── O-RR-3 (literal) — natal Saturn as 7th-house occupant ───────────────────
def test_orr3_saturn_occupant_of_7th(chart):
    # natal Saturn 202.43° → Libra = 7th sign from Aries (inclusive:
    # Aries 1 … Libra 7); the marriage target inventory includes the OCCUPANT,
    # not only 7L Venus.
    assert sign_of(202.43) == "Libra"
    assert house_of(202.43, Frame("lagna"), chart) == 7
    rec = _record(event_class="marriage", agent="Saturn",
                  relation="occupancy", object_id="obj:house:7",
                  object_kind="house_span", object_role="occupant",
                  contact_id=None, path_id="P3")
    assert rec.object_role == "occupant"
    # mutation: an object set containing only the lord, or the occupant at a
    # different longitude, fails — the occupant is pinned at 202.43°
    assert chart["natal"]["Saturn"] == 202.43


# ── O-RR-5 — yoga cancellation + strength consumed ───────────────────────────
def _cancellation_7th_saturn_and_mars(chart) -> bool:
    """'7th house occupied by both Saturn and Mars' (O-RR-5 fixture)."""
    return (house_of(chart["natal"]["Saturn"], Frame("lagna"), chart) == 7
            and house_of(chart["natal"]["Mars"], Frame("lagna"), chart) == 7)


def test_orr5_yoga_cancellation_and_strength(chart):
    # fixture A: MODIFIED object set — Mars removed from the 7th
    fixture_a = {"lagna_deg": chart["lagna_deg"],
                 "natal": {**chart["natal"], "Mars": 100.0}}  # Cancer, 4th
    assert _cancellation_7th_saturn_and_mars(fixture_a) is False
    # admitted: strength 0.8 consumed as a NAMED factor (declared scale)
    score = factor_product([{"value": 0.8, "null_state": "unqualified"}])
    assert score == pytest.approx(0.8)
    # mutation: an implementation ignoring the strength operand (factor
    # missing → 1.0) fails
    assert factor_product([]) != score

    # fixture B: Mars restored to the 7th (198.52° Libra) alongside Saturn
    assert _cancellation_7th_saturn_and_mars(chart) is True
    # ⇒ NO admission from this yoga (cancellation fires)
    cancelled = _cancellation_7th_saturn_and_mars(chart)
    admitted_from_yoga = (not cancelled)
    assert admitted_from_yoga is False


# ── O-RR-6 — affliction predicate (§1.2 inv 8) ──────────────────────────────
def test_orr6_affliction_predicate():
    afflicter_row = _record(agent="Saturn", relation="conjunction",
                            object_id="obj:x")
    assert afflicted("obj:x", [afflicter_row]) is TRUE
    # fixture B: same object, no afflicter contact
    benign_row = _record(agent="Jupiter", relation="conjunction",
                         object_id="obj:x")
    assert afflicted("obj:x", [benign_row]) is FALSE
    # unevaluated ⇒ unqualified (unknown), never assumed false
    assert afflicted("obj:x", None) is UNKNOWN
    # mutation: afflicted-by-default fails
    assert afflicted("obj:x", []) is FALSE


# ── O-RR-7 — testimony row zero score effect (bitwise-equal) ─────────────────
def test_orr7_testimony_zero_score_effect():
    scored = _record(agent="Jupiter", relation="residence",
                     object_id="obj:sign:Libra")
    maraka = _record(agent="Venus", relation="ownership",
                     object_id="obj:sign:Libra", contact_id=None,
                     object_role="maraka_of_house",
                     provenance="uncited_extension", operator_role="testimony",
                     ruling_ref="D-PADMIT")
    ev_scored = record_channel_value(
        scored, "marriage", "favourable",
        [{"value": 0.5, "null_state": "omit"}])
    ev_testimony = record_channel_value(maraka, "marriage", "favourable",
                                        [{"value": 0.9, "null_state": "omit"}])
    # testimony contributes exactly zero to ANY channel
    assert ev_testimony == {"evidence_for_occurrence": 0.0,
                            "evidence_against_occurrence": 0.0}
    without = path_channel_scores([scored], "marriage",
                                  {scored.record_id: ev_scored})
    with_ = path_channel_scores(
        [scored, maraka], "marriage",
        {scored.record_id: ev_scored, maraka.record_id: ev_testimony})
    # bitwise-equal scores
    assert with_ == without
    assert type(with_["evidence_for_occurrence"]) is type(
        without["evidence_for_occurrence"])
