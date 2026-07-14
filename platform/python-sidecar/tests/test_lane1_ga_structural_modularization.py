"""
test_lane1_ga_structural_modularization.py — LANE 1 (Doctrine Campaign D-1 / Night-1)
======================================================================================
Covers the three new test obligations from
00_ARCHITECTURE/llm_consumption_audit/briefs/night1/LANE1_GA_STRUCTURAL_MODULARIZATION.md §3:

  1. Registry completeness — every `_build_*_rows` family function in
     ga_structural_writer.py is present in STRUCTURAL_SUB_BUILDERS exactly once
     (reflection over the module).
  2. Refactor row-parity — for a fixture chart state, the (fact_category,
     fact_subject, fact_key) multiset produced by each top-level family is
     byte-stable versus the pre-refactor implementation, for every family
     EXCEPT graha_effective_dignity_modified_by_aspects. The pre-refactor
     fixture (count + sha256 digest of the sorted key multiset) was captured
     from the pre-lane1 commit (see brief §3 "cheapest honest form") using the
     MOCK_CHART_OUTPUT fixture already used by test_ga8_writer.py, and is
     embedded below as _PRE_REFACTOR_FIXTURE.

     Scope note: this covers every top_level family that is exercisable
     offline with the mock-conn fixtures already established by
     test_ga8_writer.py (17 of 23 top_level families). `vimsopaka_ext`,
     `varga_aspect`, `nakshatra_relationship`, `nakshatra_dispositor_chain`,
     `bhava_chalit_divergence`, and `contradiction_pair` require real
     chart_divisionals/chart_dashas-shaped DB fixtures that no existing
     ga_structural test constructs; they are out of scope for this offline
     parity check (§3 "whatever fixture pattern the existing ga_structural
     tests use" — none exists for these six). Lane 1 made NO code changes to
     any of these six functions' bodies (mechanical-refactor discipline —
     move code, don't edit it), so behavior preservation for them rests on
     that discipline plus the full-suite zero-new-failures acceptance gate.
  3. effective_dignity v2 — Parashari-aspect + functional-class formula.
"""
from __future__ import annotations

import hashlib
import importlib.util
import inspect
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

import ga_writers.ga_structural_writer as sut
from test_ga8_writer import (
    MOCK_CHART_OUTPUT,
    CHART_ID,
    BUILD_ID,
    AY_ID,
    ENG_VER,
    COMPUTED_AT,
    NULL_CONN,
    STRENGTH_FAKE_CONN,
    EMPTY_CONN,
)

EFFECTIVE_DIGNITY_CATEGORY = "graha_effective_dignity_modified_by_aspects"


# ── §1: Registry completeness ─────────────────────────────────────────────────

class TestRegistryCompleteness:
    def test_every_build_rows_function_registered_exactly_once(self):
        module_build_fns = {
            name
            for name, fn in inspect.getmembers(sut, inspect.isfunction)
            if name.startswith("_build_") and name.endswith("_rows")
        }
        registry_names = [entry[0] for entry in sut.STRUCTURAL_SUB_BUILDERS]
        registry_fns = [entry[1].__name__ for entry in sut.STRUCTURAL_SUB_BUILDERS]

        # No duplicate family keys, no duplicate function references
        assert len(registry_names) == len(set(registry_names)), "duplicate family_key in STRUCTURAL_SUB_BUILDERS"
        assert len(registry_fns) == len(set(registry_fns)), "a _build_*_rows function is registered more than once"

        registered_fn_set = set(registry_fns)
        missing = module_build_fns - registered_fn_set
        assert not missing, f"_build_*_rows functions missing from STRUCTURAL_SUB_BUILDERS: {missing}"

        extra = registered_fn_set - module_build_fns
        assert not extra, f"STRUCTURAL_SUB_BUILDERS references functions not in the module: {extra}"

    def test_every_entry_has_valid_kind_and_parent(self):
        family_keys = {entry[0] for entry in sut.STRUCTURAL_SUB_BUILDERS}
        for family_key, fn, kind, parent in sut.STRUCTURAL_SUB_BUILDERS:
            assert callable(fn)
            assert kind in ("top_level", "nested")
            if kind == "top_level":
                assert parent is None
            else:
                assert parent in family_keys, f"{family_key}: parent {parent!r} is not itself a registered family_key"

    def test_driver_iterates_top_level_registry_entries_in_order(self):
        """build_ga_structural_substep dispatches every 'top_level' registry
        entry (in registered order) — verified indirectly via the per-family
        row-parity test below, which exercises the same top_level families
        the driver iterates. This test just pins the top_level ordering."""
        top_level_keys = [e[0] for e in sut.STRUCTURAL_SUB_BUILDERS if e[2] == "top_level"]
        assert top_level_keys[0] == "aspects"
        assert top_level_keys[-1] == "contradiction_pair"
        assert "varga_aspect" in top_level_keys
        assert "special_state" in top_level_keys


# ── §2: Refactor row-parity ───────────────────────────────────────────────────

# Captured from the pre-lane1 commit (git HEAD at lane-1 start) via
# `_build_*_rows(MOCK_CHART_OUTPUT, ...)` using MOCK_CHART_OUTPUT + the mock
# conns already defined in test_ga8_writer.py. digest = sha256 of the sorted
# "fact_category|fact_subject|fact_key" multiset, joined by "\n".
# graha_effective_dignity_modified_by_aspects rows are excluded from
# `special_state`'s multiset (that family is allowed — required — to change).
_PRE_REFACTOR_FIXTURE = {
    "aspects": {"count": 167, "digest": "590e39371467c81fd998b3db868c81eff964f4fe6abf789dd1371abe29a8fcfc"},
    "shadbala_extension": {"count": 14, "digest": "951ccaa2754aee533d0a2cd673a164c49ebbe0f1761a7f8c8fbee29629c3d6ee"},
    "bhava_bala_extended": {"count": 96, "digest": "e0f62b80f42a00af259559d59224f79be66a9e004eee3db48a07e59df83cb487"},
    "anubindu": {"count": 0, "digest": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"},
    "yoga": {"count": 6, "digest": "ed0ebd7f288fdf302642def82fa39be1b4663794afc82a7bc4f8a1dda61fab4f"},
    "dosha": {"count": 2, "digest": "0c469d239bc0aa5cf6e77bd4de47f4378c537cb16eaf0644a135d9c9145cbcab"},
    "avastha": {"count": 36, "digest": "64e5d41fc3d19692bc4e2f066413ea7b53e307f565938869a85092d7fc2724ba"},
    "composite_strength": {"count": 324, "digest": "b2737f55513a251d4484c1fb7bb536202531a249a76556aadf0d7faff39a4468"},
    "functional_class": {"count": 21, "digest": "02a82e9544b8caba0063b93a528a07dece40c0c87f7f3e41929a6b24378060f7"},
    "karakatva": {"count": 72, "digest": "7d82ec3837e811abb0ef9e63c0a52fb93bbe00b65339bd16c339ee9c64249762"},
    "structural_relationship": {"count": 28, "digest": "412dd8ee3a376f92966e588c2741618568e409a89cc8f04949cf63f0ec60ae88"},
    "special_state": {"count": 45, "digest": "f03043723826a48e475f4477a130dfb883fb042d0f49945070b1f3313d473838"},
    "esoteric": {"count": 27, "digest": "86565048a4f926378f4b2da803e6cef3f3c9dc36e515f39ef0841dfa10415c3f"},
    "special_point_relationship": {"count": 0, "digest": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"},
    "graha_yuddha": {"count": 0, "digest": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"},
    "combustion_retrograde_relationship": {"count": 7, "digest": "bcdb12dd63e65e470861f5c1d0987b32b89c3d7d8290af389ac5f878dff37e87"},
    "significator_path": {"count": 72, "digest": "d5ca8a1969e227b2eb690c6ee9e4a8599d04f7b6c1c8e447ca7ecbf9db46c8a2"},
}


def _digest(rows):
    keys = sorted(f'{r["fact_category"]}|{r["fact_subject"]}|{r["fact_key"]}' for r in rows)
    return len(keys), hashlib.sha256("\n".join(keys).encode()).hexdigest()


def _d1_varga_state():
    return sut._extract_chart_state(MOCK_CHART_OUTPUT)


def _current_family_calls():
    d1_varga_state = _d1_varga_state()
    return {
        "aspects": lambda: sut._build_aspect_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
        "shadbala_extension": lambda: sut._build_shadbala_extension_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
        "bhava_bala_extended": lambda: sut._build_bhava_bala_extended_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
        "anubindu": lambda: sut._build_anubindu_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
        "yoga": lambda: sut._build_yoga_rows(NULL_CONN, MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
        "dosha": lambda: sut._build_dosha_rows(NULL_CONN, MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
        "avastha": lambda: sut._build_avastha_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
        "composite_strength": lambda: sut._build_composite_strength_rows(STRENGTH_FAKE_CONN, MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
        "functional_class": lambda: sut._build_functional_class_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
        "karakatva": lambda: sut._build_karakatva_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
        "structural_relationship": lambda: sut._build_structural_relationship_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
        "special_state": lambda: [
            r for r in sut._build_special_state_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER)
            if r["fact_category"] != EFFECTIVE_DIGNITY_CATEGORY
        ],
        "esoteric": lambda: sut._build_esoteric_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
        "special_point_relationship": lambda: sut._build_special_point_relationship_rows(EMPTY_CONN, MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
        "graha_yuddha": lambda: sut._build_graha_yuddha_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
        "combustion_retrograde_relationship": lambda: sut._build_combustion_retrograde_relationship_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
        "significator_path": lambda: sut._build_significator_path_rows(MOCK_CHART_OUTPUT, d1_varga_state, "D1", CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
    }


class TestRowParity:
    @pytest.mark.parametrize("family_key", sorted(_PRE_REFACTOR_FIXTURE.keys()))
    def test_family_byte_stable_vs_pre_refactor(self, family_key):
        expected = _PRE_REFACTOR_FIXTURE[family_key]
        current_rows = _current_family_calls()[family_key]()
        count, digest = _digest(current_rows)
        assert count == expected["count"], (
            f"{family_key}: row count changed ({count} vs pre-refactor {expected['count']})"
        )
        assert digest == expected["digest"], (
            f"{family_key}: (fact_category, fact_subject, fact_key) multiset changed vs pre-refactor"
        )

    def test_all_top_level_offline_families_covered(self):
        # Guard against silently narrowing fixture coverage over time.
        assert set(_PRE_REFACTOR_FIXTURE.keys()) == set(_current_family_calls().keys())


# ── §3: effective_dignity v2 ──────────────────────────────────────────────────

def _eff_rows(chart_output):
    rows = sut._build_special_state_rows(chart_output, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER)
    return [r for r in rows if r["fact_category"] == EFFECTIVE_DIGNITY_CATEGORY]


def _eff_for(chart_output, planet_name):
    subject = sut.PLANET_TO_SUBJECT.get(planet_name, planet_name.upper())
    rows = _eff_rows(chart_output)
    match = next(r for r in rows if r["fact_subject"] == subject)
    return match


class TestEffectiveDignityV2:
    def test_functional_malefic_full_aspect_lowers_score_by_0_025(self):
        # Aries lagna (MOCK_CHART_OUTPUT). Saturn = temporal_malefic (FUNCTIONAL_CLASS_BPHS).
        # House pair (Saturn house 1 -> Mars house 10) is asserted, via the shared
        # `_graha_aspects_house` helper this fix is required to use (design §10c —
        # "the file's OWN Parashari model"), to be a full-strength (1.0) aspect;
        # this lane does not alter that helper (mechanical-refactor discipline).
        #
        # A7/CR-87 fix note (D-1.5a Lane A-gamma): this fixture previously used
        # house 8 as the target, asserting `_graha_aspects_house("Saturn", 1, 8)
        # == 1.0`. That was itself an artifact of the `_graha_aspects_house`
        # off-by-one bug (raw house-difference used instead of the inclusive
        # count PARASHARI_ASPECTS is keyed on) — house 8 from house 1 is NOT one
        # of Saturn's true special aspects (3rd/7th/10th inclusive); it only
        # "worked" because the old buggy offset (raw diff=7) collided with
        # Saturn's redundant generic-7th-aspect key. Now that the offset bug is
        # fixed, house 8 correctly returns 0.0. Retargeted to house 10 — Saturn's
        # genuine 10th-house special aspect (inclusive count 10, raw diff=9) —
        # to keep testing a real full-strength special aspect.
        assert sut._graha_aspects_house("Saturn", 1, 10) == 1.0
        assert sut._graha_aspects_house("Saturn", 1, 8) == 0.0  # no longer a false-positive aspect
        chart = {
            "ascendant": {"sign": "Aries", "sign_id": 1, "longitude": 15.0},
            "grahas": [
                {"name": "Mars", "sign": "Scorpio", "sign_id": 8, "house": 10, "longitude": 225.0,
                 "retrograde": False, "dignity_status": "own_sign"},
                {"name": "Saturn", "sign": "Libra", "sign_id": 7, "house": 1, "longitude": 195.0,
                 "retrograde": False, "dignity_status": "neutral"},
            ],
        }
        row = _eff_for(chart, "Mars")
        base = 0.75  # own_sign
        # net_modification accumulates raw ±0.25×aspect_strength contributions;
        # the single ×0.1 scaling is applied once to the summed net_modification.
        expected = round(base + (-0.25 * 1.0) * 0.1, 4)  # Saturn = temporal_malefic, full-strength aspect
        assert row["fact_value_num"] == expected
        contribs = row["fact_value_jsonb"]["contributions"]
        saturn_contrib = next(c for c in contribs if c["graha"] == "Saturn")
        assert saturn_contrib["functional_class"] == "temporal_malefic"
        assert saturn_contrib["aspect_strength"] == 1.0
        assert saturn_contrib["delta"] == -0.25

    def test_graha_with_no_parashari_aspect_contributes_zero_even_at_close_longitude(self):
        # Mercury at house 2 (10° from Mars at house 1 in the OLD longitude-orb
        # model — well within the retired 15° orb) casts NO Parashari aspect on
        # house 1 (only 7th, and for non-special-aspect grahas that's the only one).
        chart = {
            "ascendant": {"sign": "Aries", "sign_id": 1, "longitude": 15.0},
            "grahas": [
                {"name": "Mars", "sign": "Aries", "sign_id": 1, "house": 1, "longitude": 15.0,
                 "retrograde": False, "dignity_status": "own_sign"},
                {"name": "Mercury", "sign": "Taurus", "sign_id": 2, "house": 2, "longitude": 25.0,
                 "retrograde": False, "dignity_status": "neutral"},
            ],
        }
        row = _eff_for(chart, "Mars")
        # Mercury (house 2) does not cast a Parashari aspect on house 1 (offset 12 -> 0 strength)
        # and is not same-house -> contributes 0, must be absent from `contributions`.
        contribs = row["fact_value_jsonb"]["contributions"]
        assert not any(c["graha"] == "Mercury" for c in contribs)
        assert row["fact_value_num"] == 0.75  # own_sign base, unmodified

    def test_score_clamps_to_0_1_range(self):
        # Stack multiple full-strength functional-malefic aspects onto a debilitated graha.
        chart = {
            "ascendant": {"sign": "Aries", "sign_id": 1, "longitude": 15.0},
            "grahas": [
                {"name": "Moon", "sign": "Aries", "sign_id": 1, "house": 1, "longitude": 10.0,
                 "retrograde": False, "dignity_status": "debilitated"},
                {"name": "Saturn", "sign": "Libra", "sign_id": 7, "house": 7, "longitude": 195.0,
                 "retrograde": False, "dignity_status": "neutral"},
                {"name": "Mercury", "sign": "Aries", "sign_id": 1, "house": 1, "longitude": 20.0,
                 "retrograde": False, "dignity_status": "neutral"},  # same-house, functional_malefic
            ],
        }
        row = _eff_for(chart, "Moon")
        assert 0.0 <= row["fact_value_num"] <= 1.0

    def test_formula_version_stamped(self):
        row = _eff_for(MOCK_CHART_OUTPUT, "Mars")
        assert row["fact_value_jsonb"]["formula"] == "parashari_aspect_functional_v2"
        assert row["source_calculation"].startswith("ga_structural.effective_dignity_v2/")

    def test_same_house_conjunction_counts_as_full_strength_association(self):
        chart = {
            "ascendant": {"sign": "Aries", "sign_id": 1, "longitude": 15.0},
            "grahas": [
                {"name": "Mars", "sign": "Aries", "sign_id": 1, "house": 1, "longitude": 15.0,
                 "retrograde": False, "dignity_status": "own_sign"},
                {"name": "Jupiter", "sign": "Aries", "sign_id": 1, "house": 1, "longitude": 20.0,
                 "retrograde": False, "dignity_status": "neutral"},  # same house, functional_benefic
            ],
        }
        row = _eff_for(chart, "Mars")
        contribs = row["fact_value_jsonb"]["contributions"]
        jup_contrib = next(c for c in contribs if c["graha"] == "Jupiter")
        assert jup_contrib["aspect_strength"] == 1.0
        assert jup_contrib["functional_class"] == "temporal_benefic"
        assert jup_contrib["delta"] == 0.25


# ── §4: A7 — `_graha_aspects_house` off-by-one fix (D-1.5a Lane A-gamma) ────
#
# CR-87-adjacent, Lane-1-flagged pre-existing bug: the offset formula used the
# RAW house difference (target_h - source_h) instead of the INCLUSIVE house
# count PARASHARI_ASPECTS is keyed on (the source house itself counts as "1").
# Every 7th-house/opposition aspect (raw diff = 6) looked up key 6 in a table
# that only has key 7 for the universal aspect — silently returning 0.0
# instead of 1.0. The same off-by-one also broke every special aspect
# (Saturn 3rd/10th, Jupiter 5th/9th, Mars 4th/8th).
#
# Concrete example (planet in house 1 aspecting house 7 — opposition):
#   BEFORE fix: offset = ((7-1) % 12) or 12          = 6  -> PARASHARI_ASPECTS["all"].get(6) = None -> 0.0 (BUG)
#   AFTER  fix: offset = ((7-1) % 12) + 1             = 7  -> PARASHARI_ASPECTS["all"].get(7) = 1.0  -> 1.0 (CORRECT)

class TestA7GrahaAspectsHouseOffByOne:

    @pytest.mark.parametrize("source_h", list(range(1, 13)))
    def test_planet_in_house_n_aspects_house_n_plus_6_opposition(self, source_h):
        """Every planet (via the universal 7th-house aspect) must register a
        full-strength (1.0) aspect on the house 6 away (i.e. the classical
        7th-house count) — opposition. Swept across all 12 possible source
        houses (wraparound included, e.g. source house 8 -> target house 2)."""
        target_h = ((source_h - 1 + 6) % 12) + 1  # house N+6, wrapping 1..12
        for aspector in ("Sun", "Moon", "Mercury", "Venus"):  # no special aspects
            assert sut._graha_aspects_house(aspector, source_h, target_h) == 1.0, (
                f"{aspector} in house {source_h} must fully aspect house {target_h} "
                f"(opposition) — got 0.0, the CR-87-adjacent off-by-one regression."
            )

    def test_concrete_house_1_aspects_house_7(self):
        """The exact worked example from the A7 fix note: planet in house 1
        aspecting house 7."""
        assert sut._graha_aspects_house("Sun", 1, 7) == 1.0
        # Sanity: the OLD buggy formula would have produced offset=6 here.
        old_buggy_offset = ((7 - 1) % 12) or 12
        assert old_buggy_offset == 6  # confirms what the bug computed
        new_correct_offset = ((7 - 1) % 12) + 1
        assert new_correct_offset == 7  # confirms the fix's inclusive count

    @pytest.mark.parametrize("aspector,source_h,target_h", [
        ("Saturn", 1, 3),    # Saturn special: 3rd house (inclusive count 3)
        ("Saturn", 1, 7),    # Saturn special: 7th house (universal, inclusive count 7)
        ("Saturn", 1, 10),   # Saturn special: 10th house (inclusive count 10)
        ("Jupiter", 1, 5),   # Jupiter special: 5th house (inclusive count 5)
        ("Jupiter", 1, 9),   # Jupiter special: 9th house (inclusive count 9)
        ("Mars", 1, 4),      # Mars special: 4th house (inclusive count 4)
        ("Mars", 1, 8),      # Mars special: 8th house (inclusive count 8)
        ("Rahu", 1, 5),      # Node special: 5th house
        ("Rahu", 1, 9),      # Node special: 9th house
        ("Ketu", 1, 5),      # Node special: 5th house
    ])
    def test_all_special_aspects_register_at_full_strength(self, aspector, source_h, target_h):
        assert sut._graha_aspects_house(aspector, source_h, target_h) == 1.0

    @pytest.mark.parametrize("aspector,source_h,target_h", [
        ("Saturn", 1, 8),    # NOT a Saturn special aspect (was a false positive pre-fix)
        ("Jupiter", 1, 4),   # NOT a Jupiter special aspect (raw diff=3 collided with Mars's key pre-fix logic)
        ("Mars", 1, 5),      # NOT a Mars special aspect
        ("Mercury", 1, 3),   # Mercury has no special aspects at all outside the 7th
    ])
    def test_non_special_house_pairs_correctly_return_zero(self, aspector, source_h, target_h):
        assert sut._graha_aspects_house(aspector, source_h, target_h) == 0.0
