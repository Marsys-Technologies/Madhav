"""
test_bo_pratijna_v4_engine.py — TDD unit suite for PRATIJÑĀ v4 Lane B2's
engine LIBRARY (`bo_pratijna_v4_engine.py`).

Pure-function tests only (no DB) — synthetic inputs, exact expected values
per `V4_RUBRIC_SPEC_v1_0.md`. The live-DB reproduction of RUNG_P3's
hand-worked numbers lives in `tests/test_bo_pratijna_v4_engine_live.py`
(mirrors `test_chart_reader_v4.py`'s DBURL-skip convention).
"""
from __future__ import annotations

from fractions import Fraction as F

import pytest

from pipeline.orchestrator.writers.bo_pratijna_karyatva import KaryatvaMap, KARYATVA_REGISTRY
from pipeline.orchestrator.writers.bo_pratijna_v4_engine import (
    BASE_WEIGHTS,
    DIGNITY_BAND,
    NAISARGIKA,
    aspect_fraction,
    check_denial_cfg1,
    check_denial_cfg3,
    compute_class_weights,
    condition_band,
    condition_score,
    dignity_of,
    dignity_of_with_positions,
    dusthana_connection,
    full_contact,
    house_distance,
    occurrence_band,
    verify_all_class_weights_sum_to_one,
    DignityResult,
    SlotWeight,
)


# ── §3.3 — 27/27 exact weight-sum regression (Fraction, no float drift) ────


def test_all_27_classes_weights_sum_to_exactly_one():
    sums = verify_all_class_weights_sum_to_one()
    assert len(sums) == 27, f"expected 27 classes, got {len(sums)}: {sorted(sums)}"
    for event_class_id, total in sums.items():
        assert total == F(1), f"{event_class_id} FAILED: sum={total}"


def test_marriage_weights_match_spec_table():
    weights = {w.item: w.weight for w in compute_class_weights(KARYATVA_REGISTRY["marriage"]) if w.slot == "house_lord"}
    assert weights["7"] == F(1, 2)
    karaka_weights = {w.item: w.weight for w in compute_class_weights(KARYATVA_REGISTRY["marriage"]) if w.slot == "karaka"}
    assert karaka_weights["Venus"] == F(1, 7)
    assert karaka_weights["Jupiter"] == F(1, 7)


def test_separation_weights_match_spec_table_5_slot_no_renorm():
    weights = compute_class_weights(KARYATVA_REGISTRY["separation"])
    by_slot_item = {(w.slot, w.item): w.weight for w in weights}
    assert by_slot_item[("house_lord", "7")] == F(35, 100)
    assert by_slot_item[("dusthana", "6")] == F(10, 100)
    assert by_slot_item[("dusthana", "8")] == F(10, 100)
    assert by_slot_item[("dusthana", "12")] == F(10, 100)
    assert by_slot_item[("karaka", "Saturn")] == F(10, 100)
    assert by_slot_item[("karaka", "Ketu")] == F(10, 100)
    assert by_slot_item[("divisional", "D9")] == F(10, 100)


def test_birth_anchor_2slot_provisional_weights_match_spec():
    weights = compute_class_weights(KARYATVA_REGISTRY["birth_anchor"])
    by_slot_item = {(w.slot, w.item): w.weight for w in weights}
    assert by_slot_item[("house_lord", "1")] == F(7, 11)
    assert by_slot_item[("karaka", "Sun")] == F(4, 11)
    # No divisional/yoga slots for a class with divisional=None, yoga_keywords=[].
    assert not any(w.slot in ("divisional", "yoga") for w in weights)


def test_no_two_classes_share_an_identical_populated_slot_set():
    """The exact career_entry≡career_change / marriage≡separation defect
    class this campaign exists to prevent, re-verified at the weight-table
    level (Lane B0's own property test covers the karyatva registry level;
    this is the engine-level analogue)."""
    signatures = {}
    for event_class_id, karyatva in KARYATVA_REGISTRY.items():
        sig = frozenset((w.slot, w.item) for w in compute_class_weights(karyatva))
        assert sig not in signatures.values(), (
            f"{event_class_id} has an identical populated factor set to "
            f"{[k for k, v in signatures.items() if v == sig]}"
        )
        signatures[event_class_id] = sig


# ── §2.1 — dignity band (pure states: exalted/debilitated/mula/own/node) ──


def _ref():
    return {
        "Venus": {"exaltation_sign": 12, "debilitation_sign": 6, "mooltrikona_sign": 7, "own_signs": [2, 7]},
        "Jupiter": {"exaltation_sign": 4, "debilitation_sign": 10, "mooltrikona_sign": 9, "own_signs": [9, 12]},
        "Saturn": {"exaltation_sign": 7, "debilitation_sign": 1, "mooltrikona_sign": 11, "own_signs": [10, 11]},
        "Sun": {"exaltation_sign": 1, "debilitation_sign": 7, "mooltrikona_sign": 5, "own_signs": [5]},
        "Mars": {"exaltation_sign": 10, "debilitation_sign": 4, "mooltrikona_sign": 1, "own_signs": [1, 8]},
        "Mercury": {"exaltation_sign": 6, "debilitation_sign": 12, "mooltrikona_sign": 6, "own_signs": [3, 6]},
        "Moon": {"exaltation_sign": 2, "debilitation_sign": 8, "mooltrikona_sign": 2, "own_signs": [4]},
        "Rahu": {"exaltation_sign": 2, "debilitation_sign": 8, "mooltrikona_sign": None, "own_signs": []},
        "Ketu": {"exaltation_sign": 8, "debilitation_sign": 2, "mooltrikona_sign": None, "own_signs": []},
    }


def test_dignity_exalted():
    r = dignity_of("Saturn", 7, None, _ref())
    assert r.state == "exalted" and r.band == 1.00


def test_dignity_debilitated():
    r = dignity_of("Venus", 6, None, _ref())
    assert r.state == "debilitated" and r.band == 0.00


def test_dignity_moolatrikona():
    r = dignity_of("Jupiter", 9, None, _ref())
    assert r.state == "moolatrikona" and r.band == 0.90


def test_dignity_own_sign():
    r = dignity_of("Saturn", 10, None, _ref())
    assert r.state == "own" and r.band == 0.80


def test_dignity_node_exalted():
    r = dignity_of("Ketu", 8, None, _ref())
    assert r.state == "exalted" and r.band == 1.00


def test_dignity_node_non_exalt_non_debil_is_neutral_only():
    r = dignity_of("Rahu", 5, None, _ref())
    assert r.state == "neutral" and r.band == 0.50


def test_dignity_compound_panchadha_maitri_matches_rung_p3_venus_enemy():
    """Venus @ Sagittarius(9), Jupiter (sign lord) also @ house 9 — RUNG_P3
    §0.3: naisargika neutral + tatkalika enemy (same house) -> enemy, 0.30."""
    r = dignity_of_with_positions("Venus", 9, 9, {"Jupiter": 9, "Venus": 9}, _ref())
    assert r.state == "enemy" and r.band == 0.30


def test_dignity_compound_panchadha_maitri_matches_rung_p3_sun_neutral():
    """Sun @ Capricorn(10), Saturn (sign lord) @ house 7 — RUNG_P3 §0.3:
    naisargika enemy + tatkalika friend -> neutral, 0.50."""
    r = dignity_of_with_positions("Sun", 10, 10, {"Saturn": 7, "Sun": 10}, _ref())
    assert r.state == "neutral" and r.band == 0.50


def test_dignity_compound_panchadha_maitri_matches_rung_p3_jupiter_friend_d7():
    """Jupiter @ Aquarius(11, D7 sign), D1 house 9; Saturn (sign lord of
    Aquarius) D1 house 7 — RUNG_P3 §0.3: naisargika neutral + tatkalika
    friend -> friend, 0.60."""
    r = dignity_of_with_positions("Jupiter", 11, 9, {"Saturn": 7, "Jupiter": 9}, _ref())
    assert r.state == "friend" and r.band == 0.60


# ── AMENDMENT F1 (R20 cycle 1, AMENDMENT_F1_SPEC_v1_0.md) — dispositor-
#    conjunction exception: graha conjunct its own dispositor reads
#    naisargika-only, tatkalika set aside, ONLY for that pair. ──────────────


def test_f1_default_off_v40_path_unchanged_venus_sag_enemy():
    """Both engines from one test, no amendment param: v4.0 (default,
    amendments unset) still yields Venus@Sag/Jupiter -> enemy/0.30, byte-
    identical to the pre-amendment RUNG_P3 acceptance number."""
    r = dignity_of_with_positions("Venus", 9, 9, {"Jupiter": 9, "Venus": 9}, _ref())
    assert r.state == "enemy" and r.band == 0.30


def test_f1_amendment_venus_sag_naisargika_only_neutral():
    """Same Venus@Sagittarius(9)/Jupiter-conjunct case, amendments={'F1'}:
    Venus's naisargika relationship to Jupiter is neutral (NAISARGIKA
    table) — with F1 active the tatkalika term (which alone produced the
    v4.0 'enemy' reading, same-house distance-1) is set aside for this
    dispositor pair, yielding neutral/0.50 per AMENDMENT_F1_SPEC_v1_0.md."""
    r = dignity_of_with_positions(
        "Venus", 9, 9, {"Jupiter": 9, "Venus": 9}, _ref(), amendments=frozenset({"F1"}),
    )
    assert r.state == "neutral" and r.band == 0.50


def test_f1_amendment_generalizes_mars_leo_sun_conjunct_friend():
    """A second, independently-constructed dispositor-conjunction pair
    (Mars@Leo(5), Sun as Leo's lord, both D1 house 5) — proves the rule is
    general, not hardcoded to the Venus/Jupiter case. Naisargika Mars->Sun
    = friend (0.60); v4.0's same-house tatkalika (enemy) compounds
    friend+enemy -> neutral/0.50; F1 gives naisargika-only friend/0.60."""
    ref = _ref()
    v40 = dignity_of_with_positions("Mars", 5, 5, {"Sun": 5, "Mars": 5}, ref)
    assert v40.state == "neutral" and v40.band == 0.50
    v41 = dignity_of_with_positions(
        "Mars", 5, 5, {"Sun": 5, "Mars": 5}, ref, amendments=frozenset({"F1"}),
    )
    assert v41.state == "friend" and v41.band == 0.60


@pytest.mark.parametrize(
    "graha,sign_number,graha_house_d1,d1_houses",
    [
        # Sun@Capricorn(10), Saturn(lord) @ house 7 — NOT conjunct.
        ("Sun", 10, 10, {"Saturn": 7, "Sun": 10}),
        # Jupiter@Aquarius(11, D7 sign), D1 house 9; Saturn(lord) D1 house 7 — NOT conjunct.
        ("Jupiter", 11, 9, {"Saturn": 7, "Jupiter": 9}),
    ],
)
def test_f1_surgical_scope_non_conjunct_pairs_identical_both_engines(
    graha, sign_number, graha_house_d1, d1_houses,
):
    """Property test (R13/mutation-proof surgical scope): for any
    graha/sign-lord pair that is NOT conjunct in D1, amendments={'F1'}
    must not change the dignity result at all — the amendment must not
    leak beyond the dispositor pair it names."""
    ref = _ref()
    v40 = dignity_of_with_positions(graha, sign_number, graha_house_d1, d1_houses, ref)
    v41 = dignity_of_with_positions(
        graha, sign_number, graha_house_d1, d1_houses, ref, amendments=frozenset({"F1"}),
    )
    assert v40 == v41


def test_f1_surgical_scope_non_dispositor_conjunction_unaffected():
    """A same-sign co-occupant that is NOT the sign's dispositor plays no
    role in dignity_of_with_positions at all (the function's only inputs
    are the scored graha and its OWN sign lord) — so a chart where some
    third graha shares Venus's sign but Jupiter (the true dispositor)
    does not, must score identically to the no-co-occupant case, with or
    without F1. This is the structural proof the amendment cannot fire on
    a same-sign pair that isn't the dispositor pair."""
    ref = _ref()
    # Jupiter (the real dispositor of Sagittarius) is NOT in house 9 here;
    # only a co-occupant (irrelevant to this function's signature) would be.
    d1_houses = {"Jupiter": 3, "Venus": 9}
    v40 = dignity_of_with_positions("Venus", 9, 9, d1_houses, ref)
    v41 = dignity_of_with_positions("Venus", 9, 9, d1_houses, ref, amendments=frozenset({"F1"}))
    assert v40 == v41
    # And it must NOT equal the naisargika-only reading (neutral) — proves
    # the amendment genuinely did not fire, not merely coincide.
    assert v40.state != "neutral"


def test_f1_amendment_scoped_by_name_other_amendment_ids_do_nothing():
    """Passing a non-'F1' amendment id must not trigger F1's behavior —
    the parameter is named-amendment-gated, not a bare boolean."""
    r = dignity_of_with_positions(
        "Venus", 9, 9, {"Jupiter": 9, "Venus": 9}, _ref(), amendments=frozenset({"F7"}),
    )
    assert r.state == "enemy" and r.band == 0.30  # unchanged v4.0 reading


# ── NAISARGIKA drift guard against ga_condition_writer.py's own copy ──────


def test_naisargika_matches_ga_condition_writer_source():
    import pathlib
    sidecar_root = pathlib.Path(__file__).resolve().parents[4]
    src_path = sidecar_root / "ga_writers" / "ga_condition_writer.py"
    src = src_path.read_text()
    start = src.index("_NAISARGIKA: dict[str, dict[str, str]] = {")
    start = src.index("{", start)
    # Balance braces to find the matching close.
    depth = 0
    end = start
    for i, ch in enumerate(src[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    literal = src[start:end]
    parsed = eval(literal)
    assert NAISARGIKA == parsed


# ── §2.7 — aspect fraction table ────────────────────────────────────────────


def test_aspect_conjunction():
    assert aspect_fraction("Saturn", 7, 7) == 1.00


def test_aspect_universal_7th():
    assert aspect_fraction("Venus", 1, 7) == 1.00


def test_aspect_mars_special_4th_8th():
    assert aspect_fraction("Mars", 1, 4) == 1.00
    assert aspect_fraction("Mars", 1, 8) == 1.00


def test_aspect_jupiter_special_5th_9th():
    assert aspect_fraction("Jupiter", 1, 5) == 1.00
    assert aspect_fraction("Jupiter", 1, 9) == 1.00


def test_aspect_saturn_special_3rd_10th():
    assert aspect_fraction("Saturn", 1, 3) == 1.00
    assert aspect_fraction("Saturn", 1, 10) == 1.00


def test_aspect_general_4th_8th_non_special_planet():
    assert aspect_fraction("Mercury", 1, 4) == 0.75
    assert aspect_fraction("Mercury", 1, 8) == 0.75


def test_aspect_general_5th_9th_non_special_planet():
    assert aspect_fraction("Venus", 1, 5) == 0.50


def test_aspect_general_3rd_10th_non_special_planet():
    assert aspect_fraction("Mercury", 1, 3) == 0.25


def test_aspect_saturn_4th_falls_to_general_not_special():
    """Saturn's SPECIAL aspects are 3rd/10th, not 4th/8th — a distance-4
    reach from Saturn is the general 0.75 tier, matching RUNG_P3 §3.3's
    childbirth condition table exactly (Saturn house7 -> Sun house10)."""
    assert aspect_fraction("Saturn", 7, 10) == 0.75


def test_aspect_nodal_specials_remain_v4_fractional_tiers():
    """The shared oracle knows nodal 5th/9th aspects, while the V4 rubric
    intentionally keeps those contacts in its existing general fractional
    scoring tiers rather than promoting them to a named full-contact tier."""
    assert aspect_fraction("Rahu", 1, 5) == 0.50
    assert aspect_fraction("ketu", 1, 9) == 0.50


def test_aspect_no_contact():
    assert aspect_fraction("Rahu", 2, 12) == 0.00


def test_full_contact_excludes_general_partial_tiers():
    assert full_contact("Mercury", 10, 7) is False  # distance 10, general 0.25 tier
    assert full_contact("Mars", 7, 7) is True         # conjunction


# ── §2.6 — dusthana connection ──────────────────────────────────────────────


def test_dusthana_connection_lord_in_house():
    conn = dusthana_connection(8, 7, "Venus", 8, 9, "Mars", 7, 10)
    assert conn.connected is True


def test_dusthana_connection_lord_full_contacts_core_house():
    conn = dusthana_connection(8, 7, "Venus", 9, 9, "Mars", 7, 10)
    assert conn.connected is True and "full-contacts core house" in conn.reason


def test_dusthana_connection_no_connection():
    conn = dusthana_connection(6, 7, "Venus", 9, 9, "Mercury", 10, 6)
    assert conn.connected is False


def test_dusthana_connection_parivartana():
    # Core lord Venus is in a sign ruled by Mars(house8's lord); house8's
    # lord Mars is in a sign ruled by Venus -> exchange.
    conn = dusthana_connection(8, 7, "Venus", 1, 8, "Mars", 5, 7)
    assert conn.connected is True and "parivartana" in conn.reason


# ── §5.2 — condition axis ───────────────────────────────────────────────────


def test_condition_score_matches_rung_p3_marriage():
    condition, ledger = condition_score(["Saturn", "Rahu", "Ketu"], 7, 9, {"Saturn": 7, "Rahu": 2, "Ketu": 8})
    assert condition == 5.83
    assert len(ledger) == 3


def test_condition_score_matches_rung_p3_separation():
    condition, _ = condition_score(["Mars", "Rahu"], 7, 9, {"Mars": 7, "Rahu": 2})
    assert condition == 8.75


def test_condition_score_matches_rung_p3_childbirth():
    condition, _ = condition_score(["Saturn", "Rahu"], 5, 10, {"Saturn": 7, "Rahu": 2})
    assert condition == 7.50


def test_condition_score_empty_malefics_is_zero():
    condition, ledger = condition_score([], 5, 10, {})
    assert condition == 0.0 and ledger == []


# ── §4 — denial configurations ──────────────────────────────────────────────


def test_cfg1_fires_when_both_debilitated_uncancelled():
    karyatva = KaryatvaMap(event_class_id="x", primary_bhava=[7], karaka_grahas=["Venus"])
    weights = [SlotWeight("house_lord", "7", F(1, 2)), SlotWeight("karaka", "Venus", F(1, 2))]
    dignities = {
        ("house_lord", "7"): DignityResult("Venus", 6, "debilitated", 0.0, "x"),
        ("karaka", "Venus"): DignityResult("Venus", 6, "debilitated", 0.0, "x"),
    }
    # Dispositor of Virgo(6) is Mercury; Mercury not kendra from lagna(1) or moon(1) -> no cancellation.
    d1_houses = {"Mercury": 6}
    result = check_denial_cfg1(karyatva, weights, dignities, 1, 1, d1_houses)
    assert result.fired is True
    assert result.deduction == F(1)


def test_cfg1_does_not_fire_with_neecha_bhanga_cancellation():
    karyatva = KaryatvaMap(event_class_id="x", primary_bhava=[7], karaka_grahas=["Venus"])
    weights = [SlotWeight("house_lord", "7", F(1, 2)), SlotWeight("karaka", "Venus", F(1, 2))]
    dignities = {
        ("house_lord", "7"): DignityResult("Venus", 6, "debilitated", 0.0, "x"),
        ("karaka", "Venus"): DignityResult("Venus", 6, "debilitated", 0.0, "x"),
    }
    # Dispositor of Virgo(6) is Mercury; Mercury IS kendra (house 4) from lagna(1) -> cancelled.
    d1_houses = {"Mercury": 4}
    result = check_denial_cfg1(karyatva, weights, dignities, 1, 1, d1_houses)
    assert result.fired is False


def test_cfg1_does_not_fire_when_only_one_debilitated():
    karyatva = KaryatvaMap(event_class_id="x", primary_bhava=[7], karaka_grahas=["Venus"])
    weights = [SlotWeight("house_lord", "7", F(1, 2)), SlotWeight("karaka", "Venus", F(1, 2))]
    dignities = {
        ("house_lord", "7"): DignityResult("Venus", 6, "debilitated", 0.0, "x"),
        ("karaka", "Venus"): DignityResult("Venus", 9, "moolatrikona", 0.9, "x"),
    }
    result = check_denial_cfg1(karyatva, weights, dignities, 1, 1, {})
    assert result.fired is False


def test_cfg3_fires_on_papakartari():
    karyatva = KaryatvaMap(event_class_id="x", primary_bhava=[5], karaka_grahas=["Jupiter"])
    weights = [SlotWeight("house_lord", "5", F(1))]
    occupants_by_house = {4: ["Saturn"], 6: ["Mars"]}
    ref = {
        "Saturn": {"natural_benefic": False}, "Mars": {"natural_benefic": False},
        "Jupiter": {"natural_benefic": True}, "Venus": {"natural_benefic": True},
        "Mercury": {"natural_benefic": True}, "Moon": {"natural_benefic": True},
        "Sun": {"natural_benefic": False}, "Rahu": {"natural_benefic": False}, "Ketu": {"natural_benefic": False},
    }
    result = check_denial_cfg3(karyatva, weights, 5, 5, occupants_by_house, ref)
    assert result.fired is True
    assert result.deduction == F(1)


def test_cfg3_does_not_fire_when_adjoining_houses_empty():
    karyatva = KaryatvaMap(event_class_id="x", primary_bhava=[5], karaka_grahas=["Jupiter"])
    weights = [SlotWeight("house_lord", "5", F(1))]
    ref = {"Jupiter": {"natural_benefic": True}}
    result = check_denial_cfg3(karyatva, weights, 5, 5, {}, ref)
    assert result.fired is False


# ── §6 — threshold bands ────────────────────────────────────────────────────


@pytest.mark.parametrize("value,label", [
    (0.0, "DENIED"), (0.19, "DENIED"), (0.20, "WEAK"), (0.321, "WEAK"),
    (0.40, "MODERATE"), (0.505, "MODERATE"), (0.593, "MODERATE"),
    (0.60, "STRONG"), (0.80, "VERY_STRONG"), (1.0, "VERY_STRONG"),
])
def test_occurrence_band(value, label):
    assert occurrence_band(value) == label


@pytest.mark.parametrize("value,label", [
    (0, "CLEAN"), (1.99, "CLEAN"), (2, "MILD"), (4, "MODERATE"),
    (5.83, "MODERATE"), (6, "SEVERE"), (7.50, "SEVERE"), (8, "CRITICAL"),
    (8.75, "CRITICAL"), (10, "CRITICAL"),
])
def test_condition_band(value, label):
    assert condition_band(value) == label


def test_house_distance_conjunction_and_opposition():
    assert house_distance(7, 7) == 1
    assert house_distance(1, 7) == 7


def test_base_weights_sum_to_one_fraction():
    assert sum(BASE_WEIGHTS.values()) == F(1)


def test_dignity_band_endpoints():
    assert DIGNITY_BAND["exalted"] == 1.00
    assert DIGNITY_BAND["debilitated"] == 0.00
