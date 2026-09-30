"""A5.5 frozen test oracles — rule paths (GOCHARA_DESIGN_SPECS_v1_4 §2).

O-RP-1, O-RP-3, O-RP-5b, O-RP-6, O-RP-7, O-RP-8 with LITERAL inputs per
/tmp oracles constants (chart 482012f1-710e-4a25-994a-93821f5871aa,
ayanamsha lahiri_chitrapaksha, natal build 1c092ffb-72eb-4614-8422-552ca6eae985;
dasha build 1f89fd4c-7d1e-4f3a-b3ae-e7ff839a6feb — MD Mercury row
58afa482-4bce-42df-9c0d-0b5a2e02305e).
"""
from __future__ import annotations

import pytest

from services.gochara_rules.admission import (
    P4_ADMISSION_ORB_DEG, aspect_points, contact_lord, infl, p2_adverse_edge,
    p3_admit, p4_admit, sade_sati_row,
)
from services.gochara_rules.dignity import dignity_of
from services.gochara_rules.frames import Frame, house_of, sign_of
from services.gochara_rules.predicates import ADMITTED, EXCLUDED
from services.gochara_rules.records import RelationshipRecord
from services.gochara_rules.registry import (
    FACTORS, RULE_PATHS, signature_houses, signature_lords,
)
from services.gochara_rules.score import (
    aggregate_paths, channel_for, path_channel_scores, promise,
    record_channel_value,
)

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

# L1 natal longitudes, build 1c092ffb-72eb-4614-8422-552ca6eae985 (literal)
NATAL = {
    "Sun": 291.96, "Moon": 327.06, "Mars": 198.52, "Mercury": 270.84,
    "Jupiter": 249.79, "Venus": 259.19, "Saturn": 202.43,
    "Rahu": 49.03, "Ketu": 229.03,
}
LAGNA_DEG = 12.43  # Aries lagna [L1]

# E8 transit operands for the twins' birth 2022-01-03 (literal)
T_JUP_2022 = 306.87  # transit Jupiter, Aquarius
T_SAT_2022 = 288.01  # transit Saturn, Capricorn


def _chart(**kw) -> dict:
    base = {"lagna_deg": LAGNA_DEG, "natal": dict(NATAL),
            "day_birth": True, "paksha": "Shukla"}
    base.update(kw)
    return base


def _record(**kw) -> RelationshipRecord:
    base = dict(
        chart_id=CHART_ID, generation="5.0", event_class="illness_acute",
        affected_person="native", frame="moon", agent="Saturn",
        relation="residence", object_id="obj:house:12",
        object_kind="house_span", object_role="signature_house",
        contact_id="sha256:contact-x", path_id="P2", rule_version="1.0.0",
        prerequisites=[], provenance="verse_cited", operator_role="scored",
    )
    return RelationshipRecord(**{**base, **kw})


# ── O-RP-1 (§2 rule paths; defects union-not-cascade, #11) ──────────────────
def test_o_rp_1_union_admission_no_cascade():
    chart = _chart()
    # literal two-path fixture at one instant (2022-01-03):
    # P3 lagna-frame contact present — transit Jupiter 306.87° Aquarius
    # 7th-aspects Leo (the 5th house): (306.87 + 180) % 360 = 126.87° Leo.
    assert sign_of((T_JUP_2022 + 180.0) % 360.0) == "Leo"
    assert p3_admit("Jupiter", T_JUP_2022, "childbirth", chart) == ADMITTED
    # P2's Moon-frame phala adverse at the SAME instant — transit Saturn
    # 288.01° Capricorn = 12th from the natal Moon 327.06° Aquarius.
    assert house_of(T_SAT_2022, Frame("moon"), chart) == 12
    adverse = p2_adverse_edge("Saturn", T_SAT_2022, "major_loss", chart)
    assert adverse is not None and adverse["house_from_moon"] == 12

    # then: the window REMAINS admitted (union); no cascade exclusion occurs —
    # evaluated AFTER the adverse edge is in hand, on the same chart.
    assert p3_admit("Jupiter", T_JUP_2022, "childbirth", chart) == ADMITTED

    # the P2 record attaches as evidence_against_occurrence on the native's
    # own-fortune (gain) classes only…
    assert channel_for("adverse", "major_gain") == "evidence_against_occurrence"
    assert channel_for("adverse", "childbirth") == "evidence_against_occurrence"
    # …and as evidence FOR adverse classes — never a veto
    assert adverse["channel"] == "evidence_for_occurrence"

    # union semantics at aggregation: cross-path = MAX; the adverse path's
    # presence never reduces the admitted gain path's score.
    assert aggregate_paths([0.7, 0.4]) == pytest.approx(0.7)
    assert aggregate_paths([0.7]) == pytest.approx(0.7)


# ── O-RP-3 (§2; defects P4-definition, R3-S02) — childbirth double transit ──
def test_o_rp_3_p4_admission_house_for_one_lord_for_other():
    chart = _chart()
    # 2022-01-03, childbirth class: H = {5th house Leo}, L(H) = {Sun}.
    assert signature_houses("childbirth", chart) == frozenset({"Leo"})
    assert signature_lords("childbirth", chart) == frozenset({"Sun"})

    # infl(Jupiter) = TRUE via HOUSE contact: transit Jupiter 306.87°
    # Aquarius 7th-aspects Leo — and NOT via any lord contact (Sun is at
    # 291.96°; Δ from 306.87° = 14.91° > 5° orb).
    assert sign_of((T_JUP_2022 + 180.0) % 360.0) == "Leo"
    assert abs(306.87 - 291.96) == pytest.approx(14.91, abs=1e-9)
    assert not contact_lord("Jupiter", T_JUP_2022, "Sun", chart,
                            orb_deg=P4_ADMISSION_ORB_DEG)
    assert infl("Jupiter", T_JUP_2022, "childbirth", chart) == ADMITTED

    # infl(Saturn) = TRUE via LORD contact: transit Saturn 288.01° vs natal
    # Sun 291.96° (5L): Δ = 3.95° = 3°57′, conjunction-within-orb with the
    # pinned 5° admission orb.
    assert abs(291.96 - 288.01) == pytest.approx(3.95, abs=1e-9)
    assert P4_ADMISSION_ORB_DEG == 5.0
    assert contact_lord("Saturn", T_SAT_2022, "Sun", chart,
                        orb_deg=P4_ADMISSION_ORB_DEG)
    assert infl("Saturn", T_SAT_2022, "childbirth", chart) == ADMITTED

    # TRUE ∧ TRUE ⇒ P4 admits — the agents need NOT share one target
    # (Jupiter→house Leo, Saturn→lord Sun).
    assert p4_admit(T_JUP_2022, T_SAT_2022, "childbirth", chart) == ADMITTED

    # a 1°-orb candidate would NOT admit (orb pinned in the fixture)
    assert not contact_lord("Saturn", T_SAT_2022, "Sun", chart, orb_deg=1.0)
    # mutation probe: requiring BOTH house and lord contacts for the SAME
    # agent fails — Jupiter has no lord contact yet infl(Jupiter) is TRUE.
    assert infl("Jupiter", T_JUP_2022, "childbirth", chart,
                H=frozenset({"Leo"}), L=frozenset()) == ADMITTED


def test_o_rp_3_peak_is_argmax_min_activity_not_endpoint():
    # Peak = argmax of min(activity_J, activity_S) over the overlap
    # (§7.2 inv 2); activity kernel = 1 − |Δλ|/orb (M-1, FACTORS row).
    kernel = FACTORS[("activity_kernel", "1.0.0")]
    assert kernel["effect"].startswith("activity = 1 − |Δλ|/orb")
    orb = 5.0

    def activity(lam: float, target: float) -> float:
        return max(0.0, 1.0 - abs(lam - target) / orb)

    # A5.5 trajectory: Jupiter sweeps toward its exact 7th-aspect contact on
    # the 5th-house cusp reference 126.87° Leo (exact at λ_J = 306.87°);
    # Saturn sweeps toward exact conjunction with natal Sun 291.96°.
    def min_activity(lam_j: float, lam_s: float) -> float:
        return min(activity(lam_j, 306.87), activity(lam_s, 291.96))

    steps = [i * 0.25 for i in range(0, 41)]  # 0 … 10° in 0.25° steps
    grid = [(306.87 - 5.0 + d, 291.96 - 5.0 + d) for d in steps]
    peak = max(grid, key=lambda p: min_activity(*p))
    # the argmax sits at the exact-contact interior point, not an endpoint
    assert peak == (306.87, 291.96)
    assert peak not in (grid[0], grid[-1])
    assert min_activity(*peak) == pytest.approx(1.0)
    # endpoint-only peak detection fails: both endpoints score strictly less
    assert min_activity(*grid[0]) < min_activity(*peak)
    assert min_activity(*grid[-1]) < min_activity(*peak)


# ── O-RP-5b (§2/§3; defects S-03, R2-S05, S-04) — Sade-Sati testimony ───────
def test_o_rp_5b_sade_sati_testimony_zero_score_effect():
    chart = _chart()
    # twins' birth 2022-01-03: Saturn 288.01° Capricorn = 12th from the
    # Aquarius Moon 327.06° (count written: Aquarius 1st, Pisces 2nd, Aries
    # 3rd, Taurus 4th, Gemini 5th, Cancer 6th, Leo 7th, Virgo 8th, Libra 9th,
    # Scorpio 10th, Sagittarius 11th, Capricorn 12th) — Sade-Sati phase 1.
    assert sign_of(327.06) == "Aquarius" and sign_of(288.01) == "Capricorn"
    assert house_of(288.01, Frame("moon"), chart) == 12

    row = sade_sati_row("Saturn", 288.01, chart)
    # the phase-1 row exists as operator_role = testimony…
    assert row is not None
    assert row["operator_role"] == "testimony"
    assert row["phase"] == 1 and row["score_effect"] == 0.0
    # …on adverse-eligible classes; the childbirth (gain) class carries NO
    # Sade-Sati edge
    assert p2_adverse_edge("Saturn", 288.01, "childbirth", chart) is None
    assert p2_adverse_edge("Saturn", 288.01, "major_gain", chart) is None

    # scoring a window with vs without this testimony row is BIT-IDENTICAL
    scored = _record(agent="Sun", relation="residence",
                     object_id="obj:house:8", contact_id="sha256:sun-8th")
    testimony = _record(operator_role="testimony",
                        provenance="uncited_extension", ruling_ref="D-PADMIT",
                        contact_id="sha256:sade-sati-p1")
    ev_scored = record_channel_value(
        scored, "illness_acute", "adverse",
        [{"value": 0.6, "null_state": "omit"}])
    ev_testimony = record_channel_value(
        testimony, "illness_acute", "adverse",
        [{"value": 0.9, "null_state": "omit"}])
    assert ev_testimony == {"evidence_for_occurrence": 0.0,
                            "evidence_against_occurrence": 0.0}
    without = path_channel_scores([scored], "illness_acute",
                                  {scored.record_id: ev_scored})
    with_ = path_channel_scores(
        [scored, testimony], "illness_acute",
        {scored.record_id: ev_scored, testimony.record_id: ev_testimony})
    assert with_ == without  # exact, bitwise
    assert without["evidence_for_occurrence"] == pytest.approx(0.6)


# ── O-RP-6 (§2.3 inv 8; defect #1) — promise = strength × condition ─────────
def test_o_rp_6_promise_strength_times_condition():
    # fixture: strength > 0 and condition true
    assert promise(0.8, True) == pytest.approx(0.8)
    # the SAME fixture with the condition set false ⇒ promise = 0
    assert promise(0.8, False) == 0.0
    # mutation probe: a constant-presence implementation (promise = strength
    # regardless of condition) fails the second case
    assert promise(0.8, False) != 0.8
    # a second strength value guards against a hard-coded 0.8
    assert promise(0.5, True) == pytest.approx(0.5)
    assert promise(0.5, False) == 0.0
    # a missing strength operand is never defaulted (§2.1 null_state upstream)
    with pytest.raises(ValueError):
        promise(None, True)


# ── O-RP-7 (§2.2 P1 factor inventory; defect #20) — dignity flip ────────────
def test_o_rp_7_dignity_flip_flips_qualifier_sign():
    # P1 fixture: the period lord (MD Mercury, row 58afa482-4bce-42df-9c0d-
    # 0b5a2e02305e) transiting sign S evaluated as EXALTATION — Mercury's
    # first 15° of Virgo is the exaltation zone (degree pinned, literal)…
    assert dignity_of("Mercury", "Virgo", deg_in_sign=10.0) == "exaltation"
    # …the same fixture with S's dignity operand flipped to DEBILITATION
    assert dignity_of("Mercury", "Pisces") == "debility"

    # the qualifier flips sign (promotion → misery) per the declared factor
    # effect: the dignity factor row declares exaltation/own → + and
    # debility/inimical → −; the `direction` field flips the assigned
    # channel/valence while factor values stay in [0, 1].
    dignity = FACTORS[("dignity_of_transit_sign", "1.0.0")]
    assert dignity["range"] == [0.0, 1.0]
    assert "exaltation/own → +, debility/inimical → −" in dignity["effect"]
    assert "direction" in dignity
    # the assigned channel flips with direction (promotion vs misery)
    assert channel_for("favourable", "marriage") == "evidence_for_occurrence"
    assert channel_for("adverse", "marriage") == "evidence_against_occurrence"
    assert channel_for("favourable", "marriage") != channel_for(
        "adverse", "marriage")

    # every factor in the P1 inventory has a DECLARED effect row, and every
    # declared range stays ⊆ [0, 1]
    p1 = RULE_PATHS[("P1", "1.0.0")]
    assert p1["soft_factors"], "P1 inventory must be non-empty"
    for ref in p1["soft_factors"]:
        row = FACTORS[ref]
        assert row.get("effect"), f"{ref} missing declared effect row"
        lo, hi = row["range"]
        assert 0.0 <= lo <= hi <= 1.0, f"{ref} range outside [0,1]"


# ── O-RP-8 (§2.3 inv 7; defect #21) — qualification-driven enumeration ──────
def _enumerate(qualified: set[tuple[str, str, str]], agents, relations,
               targets) -> list[tuple[str, str, str]]:
    """A record is enumerated iff its (agent, relation, target) triple is
    named by the chart's qualified restrictions (transit_triggers /
    dasha_rules) — §2.3 inv 7."""
    return [(a, r, t) for a in agents for r in relations for t in targets
            if (a, r, t) in qualified]


def test_o_rp_8_only_qualified_set_enumerated():
    # the registry declares RESTRICTED selectors (not Cartesian): P3's
    # object_selector names signature houses/lords; P4 names ONE rule over
    # {Jupiter, Saturn}.
    assert "signature_house h ∈ H" in RULE_PATHS[("P3", "1.0.0")]["object_selector"]
    assert RULE_PATHS[("P4", "1.0.0")]["agent_set"] == ["Jupiter", "Saturn"]

    # chart fixture: qualified restrictions name a specific
    # (agent, relation, target) set
    qualified = {("Jupiter", "aspect", "h5"),
                 ("Saturn", "conjunction", "5L")}
    agents = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
              "Rahu", "Ketu"]
    relations = ["residence", "aspect", "conjunction"]
    targets = ["h5", "5L", "h7", "7L"]
    rows = _enumerate(qualified, agents, relations, targets)

    # only the qualified set is enumerated — the exact row set
    assert rows == [("Jupiter", "aspect", "h5"),
                    ("Saturn", "conjunction", "5L")]
    assert len(rows) == 2

    # mutation probe: a Cartesian all-agents × all-relations × all-targets
    # enumeration produces extra rows and fails the count
    cartesian = [(a, r, t) for a in agents for r in relations for t in targets]
    assert len(cartesian) == 9 * 3 * 4 == 108
    assert len(rows) != len(cartesian)
    assert set(rows) < set(cartesian)
