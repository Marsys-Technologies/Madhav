"""Frozen A5.5 test oracles — literal-input implementations.

Oracle set (GOCHARA_TEST_ORACLES_v1_4, given/when/then normative):
O-TV-1, O-TV-2, O-TV-3 (§3 valence); O-VI-1, O-VI-3, O-VI-5 (§5 vedha).

L1 pins (constants): chart 482012f1-710e-4a25-994a-93821f5871aa,
ayanamsha lahiri_chitrapaksha, natal build 1c092ffb-72eb-4614-8422-552ca6eae985;
AV extract v1_0 sha256 312de09e…88fe83 (96 BAV+SARVA rows, tier single_pass
verbatim; real SARVA per sign Aries 29, Taurus 29, Gemini 27, Cancer 32,
Leo 30, Virgo 26, Libra 34, Scorpio 32, Sagittarius 25, Capricorn 27,
Aquarius 23, Pisces 23). All operands are printed literals — no database is
queried. Synthetic rows are labelled synthetic (R3-S03).
"""
from __future__ import annotations

import pytest

from services.gochara_rules.admission import p3_admit
from services.gochara_rules.predicates import ADMITTED
from services.gochara_rules.valence import compute_valence
from services.gochara_rules.vedha import (
    VedhaInterval, attenuation_at, create_vedha_interval,
)

# L1 natal longitudes (build 1c092ffb), constants.natal verbatim.
NATAL_JUPITER = 249.79   # 9L, natal Jupiter
TRANSIT_SATURN = 253.43  # father-frame contact (E8)
LAGNA_DEG = 12.43        # Aries lagna


def test_o_tv_1_bereavement_valence_adverse(chart):
    # given: father frame — transit Saturn 253.43° vs natal Jupiter 249.79°
    # (9L): Δ = 3.64° = 3°38′24″, in the 9th.
    delta = TRANSIT_SATURN - NATAL_JUPITER
    assert delta == pytest.approx(3.64, abs=1e-9)
    assert delta * 3600 == pytest.approx(3 * 3600 + 38 * 60 + 24, abs=1e-6)
    # natal Jupiter 249.79° → sign floor(249.79/30) = 8 = Sagittarius, the
    # 9th from lagna Aries (12.43°).
    assert int(NATAL_JUPITER // 30) == 8          # Sagittarius
    assert int(LAGNA_DEG // 30) == 0              # Aries
    assert (8 - 0) % 12 + 1 == 9                  # house from lagna = 9
    # the P3 admission evaluator admits the father-frame contact (> 0) from
    # the literal longitudes (steward batch-1 note a).
    assert p3_admit("Saturn", TRANSIT_SATURN, "bereavement", chart) == ADMITTED
    # when/then: evidence_for_occurrence > 0 AND outcome adverse; the
    # all-favourable era table (E5) is the regression.
    v = compute_valence("bereavement", evidence_for=0.5, evidence_against=0.0)
    assert v.evidence_for_occurrence > 0
    assert v.outcome_valence_for_native == "adverse"
    assert v.outcome_valence_for_native != "favourable"  # mutation guard


# ── O-TV-2 — 2013-12 marriage: contested occurrence, outcome NOT mixed ───────
def test_o_tv_2_contested_occurrence_not_mixed():
    # given: P3+P4 evidence for occurrence (7th-occupant Saturn return,
    # Jupiter 5th aspect on Libra) AND evidence against (natal 7th affliction)
    # both > 0.
    v = compute_valence("marriage", evidence_for=0.7, evidence_against=0.3)
    # then: both fields STAND — occurrence contested, reported as such.
    assert v.evidence_for_occurrence > 0
    assert v.evidence_against_occurrence > 0
    assert v.evidence_for_occurrence == 0.7
    assert v.evidence_against_occurrence == 0.3
    assert v.occurrence == "contested"
    # outcome_valence_for_native = favourable (marriage class polarity) —
    # NOT 'mixed': contested occurrence does not relabel outcome valence.
    assert v.outcome_valence_for_native == "favourable"
    assert v.outcome_valence_for_native != "mixed"  # mutation guard


# ── O-TV-3 — unresolved AV operand ⇒ unqualified, operand named ──────────────
def test_o_tv_3_unresolved_operand_unqualified():
    # given: a window whose AV operand is unresolved (P5c donor matrix
    # absent — the current chart state pending the ga_strength rebuild).
    v = compute_valence("career_entry", evidence_for=0.4,
                        evidence_against=0.0,
                        unresolved_operand="P5c donor matrix")
    # then: valence contribution = unqualified and the breakdown names the
    # unresolved operand; no silent 1.0 and no favourable default.
    assert v.occurrence == "unqualified"
    assert v.outcome_valence_for_native == "unqualified"
    assert v.unresolved_operand == "P5c donor matrix"
    assert v.outcome_valence_for_native != "favourable"  # mutation guard


# ── O-VI-1 — inactive/cancelled overlap ⇒ factor exactly 1.0 ─────────────────
def _vi(state: str, vi_id: str, attenuation: float = 0.5) -> VedhaInterval:
    return VedhaInterval(vi_id=vi_id, rule_version="1.0.0",
                         primary_contact_id="sha256:venus-primary",
                         obstructor_body="Saturn", vedha_kind="occupation",
                         t_in="2025-01-01T00:00Z", t_out="2025-06-01T00:00Z",
                         state=state, attenuation=attenuation)


def test_o_vi_1_inactive_overlap_factor_one():
    # given: one inactive obstruction row and one cancelled row overlapping a
    # primary Venus transit, plus one ACTIVE obstruction row as the positive
    # control.
    t = "2025-02-01T00:00Z"  # inside all three intervals
    inactive = _vi("inactive", "vi-inactive")
    cancelled = _vi("cancelled_vipareeta", "vi-cancelled")
    active = _vi("active", "vi-active")
    # then: inactive/cancelled overlap ⇒ factor exactly 1.0, rows reported
    # with state.
    r_in = attenuation_at(t, [inactive])
    assert r_in["factor"] == 1.0
    assert r_in["rows"] == [{"vi_id": "vi-inactive", "state": "inactive"}]
    r_ca = attenuation_at(t, [cancelled])
    assert r_ca["factor"] == 1.0
    assert r_ca["rows"][0]["state"] == "cancelled_vipareeta"
    # mixed overlap (inactive + cancelled together) still exactly 1.0.
    assert attenuation_at(t, [inactive, cancelled])["factor"] == 1.0
    # positive control: the ACTIVE row attenuates — factor < 1.0 (an
    # always-1 implementation fails the control).
    r_act = attenuation_at(t, [active])
    assert r_act["state"] == "attenuated"
    assert r_act["factor"] < 1.0
    # mutation guard: attenuating on the inactive row fails.
    assert r_in["state"] == "clean"


# ── O-VI-3 — exception pairs create NO interval; Mars control does ───────────
def test_o_vi_3_exception_pairs_no_interval():
    span = dict(vedha_kind="occupation", t_in="2025-01-01T00:00Z",
                t_out="2025-02-01T00:00Z", attenuation=0.5)
    # given: Saturn occupying a Sun-primary's vedha house; Moon occupying a
    # Mercury-primary's (PG322/PG323 verse-cited exceptions).
    # then: NO interval for Sun↔Saturn or Moon↔Mercury.
    assert create_vedha_interval(
        vi_id="v-sun-sat", rule_version="1.0.0", primary_contact_id="c1",
        primary_body="Sun", obstructor_body="Saturn", **span) == []
    assert create_vedha_interval(
        vi_id="v-mer-moon", rule_version="1.0.0", primary_contact_id="c2",
        primary_body="Mercury", obstructor_body="Moon", **span) == []
    # non-exception control: Mars occupying a Sun-primary's vedha house ⇒ an
    # interval IS created (a never-obstruct implementation fails).
    control = create_vedha_interval(
        vi_id="v-sun-mars", rule_version="1.0.0", primary_contact_id="c3",
        primary_body="Sun", obstructor_body="Mars", **span)
    assert len(control) == 1
    assert control[0].state == "active"
    assert control[0].exception == "none"


# ── O-VI-5 — absent overlay coverage ⇒ unavailable, never factor 1.0 ─────────
def test_o_vi_5_absent_overlay_unavailable():
    # given: an evaluation instant where the vedha overlay was never computed
    # (no coverage row).
    r = attenuation_at("2025-02-01T00:00Z", None)
    # then: reads as unavailable with a coverage object; never as factor 1.0.
    assert r["state"] == "unavailable"
    assert r["factor"] is None
    assert r["coverage"] == {"overlay": "vedha", "computed": False}
    # mutation guard: default 1.0 on missing overlay fails.
    assert r["factor"] != 1.0
