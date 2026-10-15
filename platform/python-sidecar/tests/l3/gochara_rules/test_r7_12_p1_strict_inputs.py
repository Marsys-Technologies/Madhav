"""Codex round 7 [12] — P1 strict wrappers over L1's pure rule functions.

Every assertion runs production code (`services.gochara_rules.p1_inputs`, which calls L1's `ga_writers.ga_condition_writer`). The
rows are the LITERAL L0 tables read-only from production 2026-10-02 (bg_combustion_orbs 8, bg_dignity_reference 9,
bg_graha_naisargika_friendship 72). The hazards being closed are demonstrated against L1's own functions first, so the tests show
what the wrapper stops, not only what it allows."""
import copy
import json
import pathlib

import pytest

from services.gochara_rules import p1_inputs as P
from services.gochara_rules.p1_inputs import StrictInputError

FIX = pathlib.Path(__file__).parent / "fixtures"
COMB = json.loads((FIX / "l0_combustion_orbs_2026_10_02.json").read_text())
DIG = json.loads((FIX / "l0_dignity_reference_2026_10_02.json").read_text())
NAIS = json.loads((FIX / "l0_naisargika_2026_10_02.json").read_text())
L1 = pytest.importorskip("ga_writers.ga_condition_writer")


def without(rows, **match):
    return [r for r in rows if not all(r.get(k) == v for k, v in match.items())]


def patched(rows, key, **change):
    out = copy.deepcopy(rows)
    for r in out:
        if r["graha"] == key:
            r.update(change)
    return out


# ── the L1 hazards, shown first ──────────────────────────────────────────────────────────────────────────────────
def test_the_l1_silent_defaults_exist_and_are_what_the_wrapper_must_not_reach():
    assert L1.check_combustion("Jupiter", 1.0, {}, False) == (False, False)                       # missing row => "not combust" (ga_condition_writer.py:389-394)
    assert L1.check_combustion("Jupiter", 1.0, {"Jupiter": {}}, False) == (False, False)          # missing numeric fields default to 0 (a Jupiter 1 degree from the Sun "not combust")
    assert L1.compute_panchadha_maitri("bogus", "friend") == "neutral"                            # unrecognised => neutral (:452)


# ── combustion ───────────────────────────────────────────────────────────────────────────────────────────────────
def test_combustion_uses_l1s_rule_over_validated_l0_rows_including_the_retrograde_switch():
    sun = 300.0
    # Mercury direct, arc 13: combust (limit 14); retrograde, arc 13: NOT (limit = deep 12) — M-19, via L1's own check
    d = P.combustion_state("Mercury", 313.0, sun, False, COMB)
    r = P.combustion_state("Mercury", 313.0, sun, True, COMB)
    assert d["is_combust"] is True and d["limit_deg"] == 14.0 and r["is_combust"] is False and r["limit_deg"] == 12.0
    assert r["arc_deg"] == pytest.approx(13.0)
    # seam-safe arc (L1's compute_combustion_arc): 359 vs 1 is 2 degrees
    assert P.combustion_state("Venus", 359.0, 1.0, False, COMB)["arc_deg"] == pytest.approx(2.0)
    # boundary is inclusive (L1: arc <= orb) and deep is its own bound
    j = P.combustion_state("Jupiter", sun + 11.0, sun, False, COMB)
    assert j["is_combust"] is True and j["is_deeply_combust"] is False
    assert P.combustion_state("Jupiter", sun + 9.0, sun, False, COMB)["is_deeply_combust"] is True
    assert P.combustion_state("Jupiter", sun + 11.5, sun, False, COMB)["is_combust"] is False


def test_sun_and_nodes_are_a_declared_non_applicability_not_a_missing_row():
    for g in ("Sun", "Rahu", "Ketu"):
        out = P.combustion_state(g, 10.0, 12.0, False, [])                 # no rows needed, none consulted
        assert out["applicable"] is False and out["reason"] == "never_combust_by_declaration" and out["is_combust"] is False


def test_a_missing_or_malformed_combustion_input_is_a_named_failure_never_not_combust():
    cases = [
        ("combustion_orbs_incomplete", dict(rows=without(COMB, graha="Jupiter"))),
        ("combustion_orbs_incomplete", dict(rows=[])),                                        # no literal fallback exists
        ("combustion_row_duplicate", dict(rows=COMB + [COMB[0]])),
        ("Jupiter_orb_degrees_missing_or_not_numeric", dict(rows=patched(COMB, "Jupiter", orb_degrees=None))),
        ("Jupiter_deep_orb_degrees_missing_or_not_numeric", dict(rows=patched(COMB, "Jupiter", deep_orb_degrees="9"))),
        ("Jupiter_orb_degrees_not_positive", dict(rows=patched(COMB, "Jupiter", orb_degrees=0))),
        ("Jupiter_orb_degrees_not_finite", dict(rows=patched(COMB, "Jupiter", orb_degrees=float("nan")))),
        ("combustion_deep_exceeds_orb", dict(rows=patched(COMB, "Jupiter", deep_orb_degrees=12))),
        ("combustion_row_graha_unknown", dict(rows=COMB + [{"graha": "Pluto", "orb_degrees": 1, "deep_orb_degrees": 1}])),
    ]
    for reason, kw in cases:
        with pytest.raises(StrictInputError) as e:
            P.combustion_state("Jupiter", 310.0, 300.0, False, kw["rows"])
        assert e.value.reason == reason, (reason, e.value.reason)
    for kwargs, reason in [(dict(is_retrograde=None), "motion_state_missing_or_not_boolean"), (dict(is_retrograde=0), "motion_state_missing_or_not_boolean"),
                           (dict(planet_longitude_deg=None), "planet_longitude_missing_or_not_numeric"),
                           (dict(planet_longitude_deg=360.0), "planet_longitude_out_of_range"),
                           (dict(sun_longitude_deg=-1.0), "sun_longitude_out_of_range"),
                           (dict(sun_longitude_deg=float("inf")), "sun_longitude_not_finite")]:
        args = dict(planet_longitude_deg=310.0, sun_longitude_deg=300.0, is_retrograde=False)
        args.update(kwargs)
        with pytest.raises(StrictInputError) as e:
            P.combustion_state("Jupiter", args["planet_longitude_deg"], args["sun_longitude_deg"], args["is_retrograde"], COMB)
        assert e.value.reason == reason
    with pytest.raises(StrictInputError, match="graha_unknown"):
        P.combustion_state("Pluto", 1.0, 2.0, False, COMB)


# ── maitrī ────────────────────────────────────────────────────────────────────────────────────────────────────────
MATRIX = {("friend", "friend"): "extreme_friend", ("friend", "enemy"): "neutral", ("neutral", "friend"): "friend",
          ("neutral", "enemy"): "enemy", ("enemy", "friend"): "neutral", ("enemy", "enemy"): "extreme_enemy"}
LORD = {"Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus",
        "Scorpio": "Mars", "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"}


def test_maitri_matches_an_independent_derivation_for_every_graha_sign_pair():
    """Independent oracle: naisargika from the literal L0 rows, tatkālika from the BPHS offset rule (2,3,4,10,11,12 from the graha's
    sign = friend), the six-cell matrix written out here — compared with the wrapper for all 9 grahas × 12 × 12 placements."""
    nais = {(r["graha"], r["other_graha"]): r["relation"] for r in NAIS}
    n = 0
    for g in P.GRAHAS:
        for gs in P.SIGNS:
            lord = LORD[gs]
            for ls in P.SIGNS:
                out = P.maitri_category(g, gs, ls, NAIS)
                if lord == g:
                    assert out == {"applicable": False, "reason": "own_sign", "category": None}
                    continue
                off = (P.SIGNS.index(ls) - P.SIGNS.index(gs)) % 12                      # the lord's sign counted from the graha's sign
                tat = "friend" if off in (1, 2, 3, 9, 10, 11) else "enemy"
                assert out["category"] == MATRIX[(nais[(g, lord)], tat)] and out["tatkalika"] == tat and out["naisargika"] == nais[(g, lord)], (g, gs, ls)
                n += 1
    assert n > 1000


def test_maitri_refuses_an_incomplete_or_malformed_naisargika_table_instead_of_defaulting_to_neutral():
    for rows, reason in [(without(NAIS, graha="Sun", other_graha="Moon"), "naisargika_table_incomplete"),
                         (NAIS + [NAIS[0]], "naisargika_row_duplicate"),
                         ([dict(r, relation="best_friend") if i == 0 else r for i, r in enumerate(NAIS)], "naisargika_relation_invalid"),
                         ([dict(r, other_graha=r["graha"]) if i == 0 else r for i, r in enumerate(NAIS)], "naisargika_row_graha_invalid"),
                         ([], "naisargika_table_incomplete")]:
        with pytest.raises(StrictInputError) as e:
            P.maitri_category("Mars", "Taurus", "Gemini", rows)
        assert e.value.reason == reason
    with pytest.raises(StrictInputError, match="sign_unknown"):
        P.maitri_category("Mars", "Taurus", "Nowhere", NAIS)


# ── dignity ───────────────────────────────────────────────────────────────────────────────────────────────────────
def test_dignity_boundaries_are_read_from_l0_and_returned_only_while_l1_classifier_agrees():
    for g in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        b = P.dignity_boundaries(g, DIG)
        row = next(r for r in DIG if r["graha"] == g)
        assert b == {"sign": row["moolatrikona_sign"], "from_deg": float(row["moolatrikona_from"]), "to_deg": float(row["moolatrikona_to"])}
    assert P.dignity_boundaries("Rahu", DIG) is None and P.dignity_boundaries("Ketu", DIG) is None


def test_a_boundary_divergence_between_l0_and_the_l1_classifier_is_refused_both_ways(monkeypatch):
    # L0 repaired, L1 constant not (the Mercury/Moon off-by-one referral): refuse until both agree
    with pytest.raises(StrictInputError, match="dignity_boundary_authority_divergence"):
        P.dignity_boundaries("Mercury", patched(DIG, "Mercury", moolatrikona_from=15))
    with pytest.raises(StrictInputError, match="dignity_boundary_authority_divergence"):
        P.dignity_category("Mercury", "Virgo", 15.5, patched(DIG, "Mercury", moolatrikona_from=15))
    # L1 repaired, L0 not: refuse as well
    monkeypatch.setitem(L1._MOOLATRIKONA_RANGE, "Mercury", (15, 20))
    with pytest.raises(StrictInputError, match="dignity_boundary_authority_divergence"):
        P.dignity_boundaries("Mercury", DIG)
    # both repaired: accepted, and the category follows the SAME range
    assert P.dignity_boundaries("Mercury", patched(DIG, "Mercury", moolatrikona_from=15))["from_deg"] == 15.0
    assert P.dignity_category("Mercury", "Virgo", 15.5, patched(DIG, "Mercury", moolatrikona_from=15)) == "moolatrikona"


def test_dignity_category_calls_l1_over_a_complete_row_and_refuses_incomplete_rows():
    assert P.dignity_category("Sun", "Leo", 10.0, DIG) == "moolatrikona"
    assert P.dignity_category("Sun", "Leo", 25.0, DIG) == "own"
    assert P.dignity_category("Sun", "Aries", 3.0, DIG) == "exalted" and P.dignity_category("Sun", "Libra", 3.0, DIG) == "debilitated"
    assert P.dignity_category("Rahu", "Taurus", 3.0, DIG) == "exalted"                       # nodes: sign-level, no mūlatrikoṇa
    for rows, reason in [(without(DIG, graha="Sun"), "dignity_row_missing_or_duplicate"),
                         (DIG + [DIG[0]], "dignity_row_missing_or_duplicate"),
                         (patched(DIG, "Sun", exaltation_sign=None), "dignity_exaltation_sign_invalid"),
                         (patched(DIG, "Sun", own_signs=[]), "dignity_own_signs_empty"),
                         (patched(DIG, "Sun", own_signs=["Leo", "Nowhere"]), "dignity_own_signs_invalid"),
                         (patched(DIG, "Sun", moolatrikona_sign=None), "dignity_moolatrikona_sign_invalid"),
                         (patched(DIG, "Sun", moolatrikona_from=None), "Sun_moolatrikona_from_missing_or_not_numeric"),
                         (patched(DIG, "Sun", moolatrikona_from=20, moolatrikona_to=0), "dignity_moolatrikona_range_inverted")]:
        with pytest.raises(StrictInputError) as e:
            P.dignity_category("Sun", "Leo", 10.0, rows)
        assert e.value.reason == reason, (reason, e.value.reason)
    for deg in (None, -0.1, 30.0, float("nan"), True):
        with pytest.raises(StrictInputError):
            P.dignity_category("Sun", "Leo", deg, DIG)
    with pytest.raises(StrictInputError, match="sign_unknown"):
        P.dignity_category("Sun", "Nowhere", 3.0, DIG)
