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


@pytest.mark.xfail(
    strict=True,
    reason="A5.5 FINDING (owner A5.5 trajectory/kernel): NO production "
           "function computes the oracle's peak = argmax over the overlap of "
           "min(activity_J, activity_S). The registry only DECLARES the rule "
           "(registry.py:550 score_rule string); gochara_kernel.peaks "
           "admit_peaks is episode trimming, not the min-activity argmax. "
           "spec §7.2 inv 2/O-RP-3.")
def test_o_rp_3_peak_is_argmax_min_activity_not_endpoint():
    # the activity-kernel factor row is declared in production…
    kernel = FACTORS[("activity_kernel", "1.0.0")]
    assert kernel["effect"].startswith("activity = 1 − |Δλ|/orb")
    # …but the oracle's peak requires a PRODUCTION peak finder evaluated on
    # the A5.5 trajectory: Jupiter sweeping to its exact 7th-aspect contact
    # (λ_J = 306.87°) while Saturn sweeps to exact conjunction with natal
    # Sun 291.96°. No such production function exists; call the name the
    # spec's score_rule implies and assert the interior argmax on its output.
    from services.gochara_rules import registry as _reg  # noqa: F401
    peak_fn = getattr(_reg, "peak_min_activity", None)
    assert callable(peak_fn), "no production peak = argmax min-activity"
    steps = [i * 0.25 for i in range(0, 41)]
    grid = [(306.87 - 5.0 + d, 291.96 - 5.0 + d) for d in steps]
    peak = peak_fn(grid, jupiter_target=306.87, saturn_target=291.96, orb=5.0)
    assert peak == (306.87, 291.96)
    assert peak not in (grid[0], grid[-1])


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


@pytest.mark.xfail(
    strict=True,
    reason="A5.5 FINDING (owner A5.2): NO production function composes the "
           "dignity operand into ONE P1 qualifier whose direction/valence "
           "flips. dignity_of() returns a bare string; qualify_transit "
           "(ashtakavarga.py:143) is the P5 AV-forms qualifier only; nothing "
           "on the P1 path consumes dignity into a direction. spec §2.2 "
           "P1/O-RP-7.")
def test_o_rp_7_one_production_qualifier_flips_with_dignity():
    # ONE production qualifier call on the SAME P1 fixture (MD Mercury
    # transiting sign S), evaluated twice — exaltation vs debility — whose
    # direction/valence OUTPUT flips.
    from services.gochara_rules import ashtakavarga as _av  # noqa: F401
    qualifier = getattr(_av, "p1_qualifier", None)
    assert callable(qualifier), "no production P1 qualifier composing dignity"
    exalted = qualifier("Mercury", "Virgo", deg_in_sign=10.0,
                        period_lord_row="58afa482-4bce-42df-9c0d-0b5a2e02305e")
    debilitated = qualifier("Mercury", "Pisces",
                            period_lord_row="58afa482-4bce-42df-9c0d-0b5a2e02305e")
    assert exalted["direction"] == "favourable"
    assert debilitated["direction"] == "adverse"
    assert exalted["direction"] != debilitated["direction"]


# ── O-RP-8 (§2.3 inv 7; defect #21) — qualification-driven enumeration ──────
def test_o_rp_8_only_qualified_set_enumerated():
    # the registry declares RESTRICTED selectors (not Cartesian): P3's
    # object_selector names signature houses/lords; P4 names ONE rule over
    # {Jupiter, Saturn}.
    assert "signature_house h ∈ H" in RULE_PATHS[("P3", "1.0.0")]["object_selector"]
    assert RULE_PATHS[("P4", "1.0.0")]["agent_set"] == ["Jupiter", "Saturn"]


@pytest.mark.xfail(
    strict=True,
    reason="A5.5 FINDING (owner A5.2): NO production record enumerator is "
           "driven by the chart's qualified restrictions (transit_triggers / "
           "dasha_rules). grep over services/gochara_rules + gochara_kernel "
           "finds no enumeration entry point; only the registry's selector "
           "STRINGS exist. spec §2.3 inv 7/O-RP-8.")
def test_o_rp_8_production_enumerator_row_count():
    # chart fixture: qualified restrictions name a specific
    # (agent, relation, target) set; the production enumerator must emit
    # exactly those rows, not the 9×3×4 = 108-row Cartesian product.
    chart = _chart()
    qualified = {("Jupiter", "aspect", "h5"),
                 ("Saturn", "conjunction", "5L")}
    from services.gochara_rules import records as _rec  # noqa: F401
    enumerator = getattr(_rec, "enumerate_records", None)
    assert callable(enumerator), "no production record enumerator"
    rows = enumerator(chart, qualified=qualified)
    assert len(rows) == 2
    assert {(r.agent, r.relation, r.object_id) for r in rows} == qualified
