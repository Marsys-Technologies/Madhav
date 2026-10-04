"""
test_q03_tiers_nakshatra_kp.py -- Q03 / SS N-62 honest tiers: ga_nakshatra attribution rows
(TS-NAK: `single` on agreement, never TPV or classical_match: the second pass is the same floor division
over the same exported longitude and compares no reference table -- SS tier rule, S-L1 follow-up;
a disagreement is `divergent_flagged`) and the KP significator star/sub-lord rows (TS-KP: keep
`two_pass_verified`, but only because the two paths can genuinely disagree).

Spec: AUDIT_L1_TIERS_PER_EMITTER_v1_0.md v1.1 §2.2 / §5.
"""
from __future__ import annotations

import copy
from fractions import Fraction

import pytest

from brahmagyan import verification_tiers as T
from brahmagyan.l0_kp_sublord_division import build_divisions, lookup_division
from ga_writers import ga_kp_significators as KP
from ga_writers.ga_kp_significators import PLANET_SIGNIFICATIONS_CATEGORY, emit_kp_significators
from pipeline.orchestrator.writers import ga_nakshatra as N

# ── TS-NAK ────────────────────────────────────────────────────────────────────


def _chart(lon: float, nak: int, pada: int) -> dict:
    return {
        "grahas": [{"name": "Moon", "longitude_deg": lon, "nakshatra_id": nak, "pada": pada}],
        "ascendant": {},
    }


def test_nak_agreeing_attribution_is_single_not_classical_match_or_tpv():
    # 326.0 deg = Purva Bhadrapada (25), pada 2.
    v = N._nakshatra_pada_verdicts(_chart(326.0, 25, 2))["MOON"]
    assert v == {"nakshatra": T.SINGLE, "pada": T.SINGLE}
    assert not {T.TWO_PASS_VERIFIED, T.CLASSICAL_MATCH} & set(v.values())


def test_nak_engine_perturbed_by_one_is_divergent_flagged():
    v = N._nakshatra_pada_verdicts(_chart(326.0, 26, 2))["MOON"]  # nakshatra off by one
    assert v["nakshatra"] == T.DIVERGENT_FLAGGED and v["pada"] == T.SINGLE
    v = N._nakshatra_pada_verdicts(_chart(326.0, 25, 3))["MOON"]  # pada off by one
    assert v["pada"] == T.DIVERGENT_FLAGGED and v["nakshatra"] == T.SINGLE


def test_nak_no_longitude_means_no_check_ran_so_single():
    v = N._nakshatra_pada_verdicts(
        {"grahas": [{"name": "Moon", "nakshatra_id": 25, "pada": 2}], "ascendant": {}}
    )["MOON"]
    assert v == {"nakshatra": T.SINGLE, "pada": T.SINGLE}


def test_nak_check_is_actually_run_the_tier_depends_on_it(monkeypatch):
    """Spy: the re-derivation is called once per body, and its return value decides whether a
    divergence is flagged. MUTANT (return a verdict without calling `_derive_nakshatra_pada`) -> the
    spy count is 0 and a shifted derivation does not flip the verdict: both assertions below fail."""
    calls: list[float] = []
    real = N._derive_nakshatra_pada

    def spy(lon):
        calls.append(lon)
        return real(lon)

    monkeypatch.setattr(N, "_derive_nakshatra_pada", spy)
    assert N._nakshatra_pada_verdicts(_chart(326.0, 25, 2))["MOON"]["nakshatra"] == T.SINGLE
    assert calls == [326.0]

    monkeypatch.setattr(N, "_derive_nakshatra_pada", lambda lon: (real(lon)[0] + 1, real(lon)[1]))
    assert N._nakshatra_pada_verdicts(_chart(326.0, 25, 2))["MOON"]["nakshatra"] == T.DIVERGENT_FLAGGED


def test_mutant_nak_classical_match_stamp_is_visible(monkeypatch):
    """MUTANT (the pre-ruling behaviour): a verdict function stamping classical_match on agreement is
    exactly what the single-tier tests above reject (they would FAIL on it)."""
    monkeypatch.setattr(N, "_nakshatra_pada_verdicts",
                        lambda co: {"MOON": {"nakshatra": T.CLASSICAL_MATCH, "pada": T.CLASSICAL_MATCH}})
    v = N._nakshatra_pada_verdicts(_chart(326.0, 25, 2))["MOON"]
    assert v != {"nakshatra": T.SINGLE, "pada": T.SINGLE}


def test_nak_rows_through_enrich_are_all_single_when_the_check_agrees():
    rows = [
        {"chart_id": "c", "ayanamsha_id": "a", "build_id": "b", "fact_subject": "MOON",
         "fact_category": "graha_nakshatra_join", "fact_key": "nakshatra_id_ref", "fact_value_num": 25.0},
        {"chart_id": "c", "ayanamsha_id": "a", "build_id": "b", "fact_subject": "MOON",
         "fact_category": "graha_pada_join", "fact_key": "pada_number_ref", "fact_value_num": 2.0},
        {"chart_id": "c", "ayanamsha_id": "a", "build_id": "b", "fact_subject": "MOON",
         "fact_category": "graha_nakshatra_join", "fact_key": "gana", "fact_value_text": "Deva"},
    ]
    out = N._enrich_rows(rows, "e", "t", N._nakshatra_pada_verdicts(_chart(326.0, 25, 2)))
    assert [r["verification_pass_status"] for r in out] == [T.SINGLE, T.SINGLE, T.SINGLE]


# ── TS-KP ─────────────────────────────────────────────────────────────────────

SIGN_LORDS = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury",
    7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter",
}
SUN_LON = 5.0


def _kp_chart() -> dict:
    return {
        "grahas": [{"name": "Sun", "longitude_deg": SUN_LON, "house": 1}],
        "ascendant": {"longitude_deg": 0.0, "sign_id": 1},
        "bhava_chalit": {"placidus": {
            "cusp_boundaries": [h * 30.0 for h in range(12)],
            "cusps": [{"house": h + 1, "start": h * 30.0, "madhya": h * 30.0 + 15.0,
                       "end": (h + 1) * 30.0 % 360.0} for h in range(12)],
        }},
    }


def _sun_lord_rows(divisions) -> dict[str, str]:
    rows = emit_kp_significators("c", "krishnamurti", "b", _kp_chart(), divisions, SIGN_LORDS)
    return {r["fact_key"]: r["verification_pass_status"] for r in rows
            if r["fact_category"] == PLANET_SIGNIFICATIONS_CATEGORY and r["fact_subject"] == "SUN"
            and r["fact_key"] in ("star_lord", "sub_lord")}


@pytest.fixture(scope="module")
def divisions():
    return build_divisions()


def _perturb_boundary(divisions, lon: float):
    """Move the division boundary that brackets `lon` so lookup_division lands in the
    NEIGHBOURING division while compute_kp_lords (float walk) does not move."""
    divs = copy.deepcopy(divisions)
    idx = next(i for i, d in enumerate(divs) if d["_start_exact"] <= Fraction(lon) < d["_end_exact"])
    shifted = Fraction(lon) - Fraction(1, 10**6)
    divs[idx]["_end_exact"] = shifted
    divs[idx + 1]["_start_exact"] = shifted
    return divs, idx


def test_kp_agreement_keeps_two_pass_verified(divisions):
    assert _sun_lord_rows(divisions) == {"star_lord": T.TWO_PASS_VERIFIED,
                                         "sub_lord": T.TWO_PASS_VERIFIED}


def test_kp_perturbed_boundary_is_divergent_flagged(divisions):
    divs, idx = _perturb_boundary(divisions, SUN_LON)
    # sanity: the perturbation really changes what the table says for this longitude
    # (if neighbouring divisions shared both lords the test would be vacuous)
    assert (lookup_division(SUN_LON, divs)["star_lord"], lookup_division(SUN_LON, divs)["sub_lord"]) != (
        lookup_division(SUN_LON, divisions)["star_lord"], lookup_division(SUN_LON, divisions)["sub_lord"]
    )
    got = _sun_lord_rows(divs)
    assert T.DIVERGENT_FLAGGED in got.values()
    assert T.TWO_PASS_VERIFIED not in got.values()


def test_kp_mutant_second_path_replaced_by_first_masks_the_divergence(divisions, monkeypatch):
    """MUTANT: `live = div` (the second path replaced by the first). The perturbed case then
    returns two_pass_verified, i.e. test_kp_perturbed_boundary_is_divergent_flagged FAILS on
    this mutant. We run the mutant and assert it masks the divergence."""
    divs, _ = _perturb_boundary(divisions, SUN_LON)
    monkeypatch.setattr(
        KP, "compute_kp_lords",
        lambda lon: {k: lookup_division(lon, divs)[k] for k in ("star_lord", "sub_lord")},
    )
    assert _sun_lord_rows(divs) == {"star_lord": T.TWO_PASS_VERIFIED, "sub_lord": T.TWO_PASS_VERIFIED}
