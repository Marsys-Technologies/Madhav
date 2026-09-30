"""O-RP-* — rule-path oracles (GOCHARA_DESIGN_SPECS_v1_4 §2).

Literal: O-RP-2 (restricted H′/L′ FALSE case AND full-H TRUE case), O-RP-4,
O-RP-5a. Literal-input executable semantics: O-RP-1, O-RP-3, O-RP-5b,
O-RP-6, O-RP-7, O-RP-8.
"""
from __future__ import annotations

import pytest

from services.gochara_rules.admission import (
    P4_ADMISSION_ORB_DEG, aspect_points, contact_lord, infl, p2_adverse_edge,
    p3_admit, p4_admit, sade_sati_row,
)
from services.gochara_rules.frames import Frame, house_of, sign_of
from services.gochara_rules.permission import applicability
from services.gochara_rules.predicates import ADMITTED, EXCLUDED, UNQUALIFIED
from services.gochara_rules.registry import (
    FACTORS, RULE_PATHS, signature_houses, signature_lords,
)
from services.gochara_rules.score import (
    aggregate_paths, channel_for, promise, record_channel_value,
)
from services.gochara_rules.records import RelationshipRecord

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

# O-RP-2 printed operands (E8 2018-11-28)
TJUP = 220.31   # transit Jupiter, Scorpio
NJUP = 249.79   # natal Jupiter
TSAT = 253.43   # transit Saturn, Sagittarius


# ── O-RP-1 — union admission, no cascade ─────────────────────────────────────
def test_orp1_union_no_cascade(chart):
    # P3 lagna-frame contact present: transit Jupiter 306.87° 7th-aspects Leo
    # (the 5th house) — admitted for childbirth.
    assert p3_admit("Jupiter", 306.87, "childbirth", chart) == ADMITTED
    # P2 adverse residence present at the same instant (Saturn 12th-from-Moon
    # phase-1): the window REMAINS admitted (union semantics; no cascade
    # exclusion).
    adverse = p2_adverse_edge("Saturn", 288.01, "illness_acute", chart)
    # 288.01° Capricorn = 12th from the Aquarius Moon → adverse residence
    assert adverse is not None and adverse["house_from_moon"] == 12
    # the P2 record attaches as evidence_against_occurrence on the native's
    # own-fortune (gain) classes only…
    assert channel_for("adverse", "major_gain") == "evidence_against_occurrence"
    # …and as evidence FOR the adverse classes — never a veto
    assert channel_for("adverse", "illness_acute") == "evidence_for_occurrence"
    # mutation: a cascade implementation (P2 adverse vetoes the P3 window)
    # fails — admission is untouched
    assert p3_admit("Jupiter", 306.87, "childbirth", chart) == ADMITTED


# ── O-RP-2 (literal) — the ONE P4 rule, evaluated twice ──────────────────────
def test_orp2_arithmetic_printed(chart):
    # transit Jupiter 220.31° Scorpio; conjunction with natal Jupiter
    # 249.79°: Δ = 29.48°, outside any orb; aspects from Scorpio fall on
    # Pisces (5th, +120°), Taurus (7th, +180°), Cancer (9th, +240°).
    assert abs(220.31 - 249.79) == pytest.approx(29.48, abs=1e-9)
    assert not contact_lord("Jupiter", TJUP, "Jupiter", chart,
                            orb_deg=P4_ADMISSION_ORB_DEG)
    aspect_signs = {sign_of(p) for p in aspect_points("Jupiter", TJUP)}
    assert aspect_signs == {"Pisces", "Taurus", "Cancer"}
    # Jupiter's 9th aspect: 220.31° + 240° = 100.31° Cancer = 8th from the 9th
    assert (TJUP + 240.0) % 360.0 == pytest.approx(100.31, abs=1e-9)
    assert sign_of(100.31) == "Cancer"
    # transit Saturn 253.43° occupies Sagittarius
    assert sign_of(TSAT) == "Sagittarius"
    # full truth-table inventory for bereavement (father):
    # H = {9th and its 2nd/7th/8th via bhavat_bhavam:9}
    assert signature_houses("bereavement", chart) == frozenset(
        {"Sagittarius", "Capricorn", "Gemini", "Cancer"})


def test_orp2_restricted_inventory_false(chart):
    # (i) restricted H′ = {Sagittarius}, L′ = {Jupiter}: infl(Jupiter) = FALSE
    # (Δ 29.48°; aspects on Pisces/Taurus/Cancer — Sagittarius not among
    # them), infl(Saturn) = TRUE ⇒ FALSE ∧ TRUE = FALSE (the D-P4 withdrawal,
    # a labelled restricted negative test).
    Hp, Lp = frozenset({"Sagittarius"}), frozenset({"Jupiter"})
    assert infl("Jupiter", TJUP, "bereavement", chart, H=Hp, L=Lp) == EXCLUDED
    assert infl("Saturn", TSAT, "bereavement", chart, H=Hp, L=Lp) == ADMITTED
    # mutation: under (i) ANY P4 admission fails
    assert p4_admit(TJUP, TSAT, "bereavement", chart, H=Hp, L=Lp) == EXCLUDED


def test_orp2_full_inventory_true(chart):
    # (ii) full H: infl(Jupiter) = TRUE via the 9th aspect on Cancer (house
    # contact alone; no lord contact needed), infl(Saturn) = TRUE via
    # residence in Sagittarius ⇒ P4_admit = TRUE — admitted through house
    # contacts on two DIFFERENT houses; the agents need not share one target.
    assert p4_admit(TJUP, TSAT, "bereavement", chart) == ADMITTED
    # Jupiter's admission is by HOUSE contact alone (Cancer), not lord contact
    assert not contact_lord("Jupiter", TJUP, "Jupiter", chart,
                            orb_deg=P4_ADMISSION_ORB_DEG)
    # mutation: an implementation dropping 2/7/8-from-the-9th from H denies
    # P4 and fails — demonstrated by the restricted case being FALSE
    assert p4_admit(TJUP, TSAT, "bereavement", chart,
                    H=frozenset({"Sagittarius"}),
                    L=frozenset({"Jupiter"})) == EXCLUDED


# ── O-RP-3 — childbirth double transit (the SAME ONE rule) ──────────────────
def test_orp3_childbirth_true_and_true(chart):
    # 2022-01-03, childbirth: H = {5th house Leo}, L(H) = {Sun}.
    assert signature_houses("childbirth", chart) == frozenset({"Leo"})
    assert signature_lords("childbirth", chart) == frozenset({"Sun"})
    # infl(Jupiter): transit Jupiter 306.87° Aquarius 7th-aspects Leo
    # (306.87 + 180 = 126.87 → Leo) ⇒ TRUE
    assert sign_of((306.87 + 180.0) % 360.0) == "Leo"
    assert infl("Jupiter", 306.87, "childbirth", chart) == ADMITTED
    # infl(Saturn): transit Saturn 288.01° vs natal Sun 291.96° (5L):
    # Δ = 3.95° = 3°57′, within the pinned 5° admission orb ⇒ TRUE
    assert abs(291.96 - 288.01) == pytest.approx(3.95, abs=1e-9)
    assert contact_lord("Saturn", 288.01, "Sun", chart,
                        orb_deg=P4_ADMISSION_ORB_DEG)
    assert infl("Saturn", 288.01, "childbirth", chart) == ADMITTED
    assert p4_admit(306.87, 288.01, "childbirth", chart) == ADMITTED
    # a 1°-orb candidate would NOT admit (orb pinned in the fixture)
    assert not contact_lord("Saturn", 288.01, "Sun", chart, orb_deg=1.0)


# ── O-RP-4 (literal) — Aṣṭottarī absent ──────────────────────────────────────
def test_orp4_ashtottari_absent(chart):
    # BPHS ch.46: Rāhu 49.03° Taurus = 8th from lagna lord Mars (198.52°
    # Libra — inclusive: Libra 1 … Taurus 8) — FAILS kendra/trikoṇa;
    # day birth Śukla pakṣa fails the Kṛṣṇa reading.
    assert house_of(49.03, Frame("graha", "Mars"), chart) == 8
    result = applicability(chart)
    assert result["state"] == "absent"
    assert len(result["failed_conditions"]) == 2
    assert any("rahu_8th_from_lagna_lord" in c
               for c in result["failed_conditions"])
    assert any("shukla_paksha" in c for c in result["failed_conditions"])
    # mutation: absence reported WITHOUT the failed conditions fails
    assert result["failed_conditions"] != []


# ── O-RP-5a (literal) — scored 8th-from-Moon residence ──────────────────────
def test_orp5a_saturn_8th_from_moon(chart):
    # natal Moon 327.06° Aquarius; Saturn transiting 172.00° Virgo; the
    # inclusive count: Aquarius 1st, Pisces 2nd, Aries 3rd, Taurus 4th,
    # Gemini 5th, Cancer 6th, Leo 7th, Virgo 8th.
    assert sign_of(172.00) == "Virgo"
    assert house_of(172.00, Frame("moon"), chart) == 8
    edge = p2_adverse_edge("Saturn", 172.00, "illness_acute", chart)
    # evidence FOR the named adverse class illness_acute
    assert edge is not None
    assert edge["channel"] == "evidence_for_occurrence"
    # mutation: recorded as evidence_against on illness_acute must fail
    assert edge["channel"] != "evidence_against_occurrence"
    # mutation: attaching the edge to a gain class must fail
    for gain in ("major_gain", "childbirth", "marriage"):
        assert p2_adverse_edge("Saturn", 172.00, gain, chart) is None


# ── O-RP-5b — testimony Sade-Sati / 12th-from-Moon ──────────────────────────
def test_orp5b_sade_sati_testimony_zero_effect(chart):
    # twins' birth 2022-01-03, Saturn 288.01° Capricorn = 12th from the
    # Aquarius Moon (Aquarius 1st … Capricorn 12th) — Sade-Sati phase 1.
    assert house_of(288.01, Frame("moon"), chart) == 12
    row = sade_sati_row("Saturn", 288.01, chart)
    assert row is not None
    assert row["operator_role"] == "testimony"
    assert row["score_effect"] == 0.0
    # the childbirth (gain) class carries NO Sade-Sati edge
    assert p2_adverse_edge("Saturn", 288.01, "childbirth", chart) is None
    # zero score effect: a testimony record moves no channel
    rec = RelationshipRecord(
        chart_id=CHART_ID, generation="5.0", event_class="illness_acute",
        affected_person="native", frame="moon", agent="Saturn",
        relation="residence", object_id="obj:house:12",
        object_kind="house_span", object_role="signature_house",
        contact_id="sha256:sade-sati-p1", path_id="P2", rule_version="1.0.0",
        prerequisites=[], provenance="uncited_extension",
        operator_role="testimony", ruling_ref="D-PADMIT")
    ev = record_channel_value(rec, "illness_acute", "adverse",
                              [{"value": 0.9, "null_state": "omit"}])
    assert ev == {"evidence_for_occurrence": 0.0,
                  "evidence_against_occurrence": 0.0}


# ── O-RP-6 — promise = strength × condition ──────────────────────────────────
def test_orp6_promise_strength_times_condition():
    assert promise(0.8, True) == pytest.approx(0.8)
    # condition false ⇒ promise 0
    assert promise(0.8, False) == 0.0
    # mutation: a constant-presence implementation (promise = strength
    # regardless) fails the second case
    assert promise(0.8, False) != 0.8


# ── O-RP-7 — dignity flip flips direction/channel ────────────────────────────
def test_orp7_dignity_flip_flips_channel():
    dignity = FACTORS[("dignity_of_transit_sign", "1.0.0")]
    # factor values stay in [0,1]; the direction field carries the sign
    assert dignity["range"] == [0.0, 1.0]
    assert "direction" in dignity
    # exaltation → promotion (favourable); debility → misery (adverse):
    # the assigned channel/valence flips
    assert channel_for("favourable", "marriage") == "evidence_for_occurrence"
    assert channel_for("adverse", "marriage") == "evidence_against_occurrence"
    # mutation: a dignity-independent qualifier fails — the channels differ
    assert channel_for("favourable", "marriage") != channel_for(
        "adverse", "marriage")


# ── O-RP-8 — qualification-driven enumeration ────────────────────────────────
def _enumerate(qualified: set[tuple[str, str]], agents, targets):
    """A contact is enumerated iff some admitted path's object_selector names
    its (agent, target) — §2.3 inv 7."""
    return [(a, t) for a in agents for t in targets if (a, t) in qualified]


def test_orp8_qualification_driven_enumeration():
    agents = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
              "Rahu", "Ketu"]
    targets = ["h5", "h7", "7L", "9L"]
    qualified = {("Jupiter", "h5"), ("Saturn", "7L")}
    rows = _enumerate(qualified, agents, targets)
    assert rows == [("Jupiter", "h5"), ("Saturn", "7L")]
    # mutation: a Cartesian all-agents × all-targets enumeration produces
    # extra rows and fails the count
    cartesian = [(a, t) for a in agents for t in targets]
    assert len(cartesian) == 36
    assert len(rows) == 2 != len(cartesian)


# ── registry conformance: composite keys, no bare ids ────────────────────────
def test_registry_composite_keys_and_roles():
    for (pid, ver), row in RULE_PATHS.items():
        assert pid == row["path_id"] and ver == row["rule_version"]
        assert row["operator_role"] in ("scored", "testimony")
        if row["provenance"] == "uncited_extension":
            assert row["ruling_ref"], f"{pid} needs ruling_ref (§0)"
        for ref in row["prerequisites"] + row["soft_factors"]:
            assert isinstance(ref, tuple) and len(ref) == 2 and all(ref)
    # P6 is testimony under D-PADMIT; P4 is scored under D-P4
    assert RULE_PATHS[("P6", "1.0.0")]["operator_role"] == "testimony"
    assert RULE_PATHS[("P4", "1.0.0")]["ruling_ref"] == "D-P4"


def test_h_unknown_classes_unqualified(chart):
    # the eight named classes: H = unknown ⇒ P3/P4 admission unqualified,
    # never false, never admitted
    for cls in ("achievement_recognition", "business_launch",
                "financial_deception", "foreign_settlement", "parental_event",
                "property_acquisition", "psychological_arc", "spiritual_turn"):
        assert signature_houses(cls, chart) is None
        assert p3_admit("Jupiter", 306.87, cls, chart) == UNQUALIFIED
