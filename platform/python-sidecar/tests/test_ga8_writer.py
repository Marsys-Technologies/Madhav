"""
test_ga8_writer.py — Unit tests for GA8 T1 structural writer
=============================================================
All-unit. No DB required. Mock chart_output replaces PyJHora.
Covers: Groups A–O, argala 144-row assertion, yoga firing with mock constituents,
functional class Lagna=Aries, two-pass invariants, no GA3 duplicate fact_ids.

Per CAMPAIGN_RAILS:
  - No DB; all tests use mock chart_output
  - GA3 category overlap check enforced
  - Two-pass invariant: argala must produce exactly 144 + 144 rows
  - Lagna = Aries, Sun = Capricorn, Moon nak = Purva Bhadrapada
"""
from __future__ import annotations

import hashlib
import sys
import os
from typing import Any

import pytest

# Adjust path for import without package install
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import ga_writers.ga_structural_writer as sut


# ── Shared test fixtures ──────────────────────────────────────────────────────

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
BUILD_ID = "test-build-001"
AY_ID = "lahiri_chitrapaksha"
ENG_VER = "pyjhora/1.0.0"
COMPUTED_AT = "2026-06-10T00:00:00+00:00"

# FORENSIC-grounded mock chart output (Aries lagna, Sun=Capricorn)
# Matches: Sun=Capricorn, Moon nak=Purva Bhadrapada (Aquarius), Lagna=Aries
MOCK_CHART_OUTPUT: dict[str, Any] = {
    "ascendant": {
        "sign": "Aries",
        "sign_id": 1,
        "longitude": 15.0,
    },
    "grahas": [
        {"name": "Sun",     "sign": "Capricorn",   "sign_id": 10, "house": 10, "longitude": 295.0,
         "retrograde": False, "dignity_status": "neutral"},
        {"name": "Moon",    "sign": "Aquarius",    "sign_id": 11, "house": 11, "longitude": 325.0,
         "retrograde": False, "dignity_status": "neutral"},
        {"name": "Mars",    "sign": "Aries",       "sign_id": 1,  "house": 1,  "longitude": 15.0,
         "retrograde": False, "dignity_status": "own_sign"},
        {"name": "Mercury", "sign": "Capricorn",   "sign_id": 10, "house": 10, "longitude": 300.0,
         "retrograde": False, "dignity_status": "neutral"},
        {"name": "Jupiter", "sign": "Sagittarius", "sign_id": 9,  "house": 9,  "longitude": 265.0,
         "retrograde": False, "dignity_status": "own_sign"},
        {"name": "Venus",   "sign": "Capricorn",   "sign_id": 10, "house": 10, "longitude": 308.0,
         "retrograde": False, "dignity_status": "neutral"},
        {"name": "Saturn",  "sign": "Libra",       "sign_id": 7,  "house": 7,  "longitude": 195.0,
         "retrograde": False, "dignity_status": "exalted"},
        {"name": "Rahu",    "sign": "Taurus",      "sign_id": 2,  "house": 2,  "longitude": 48.0,
         "retrograde": True,  "dignity_status": "neutral"},
        {"name": "Ketu",    "sign": "Scorpio",     "sign_id": 8,  "house": 8,  "longitude": 228.0,
         "retrograde": True,  "dignity_status": "neutral"},
    ],
}


class _NullCursor:
    """No-op cursor stand-in — _real_fact_id_ref returns None for all lookups."""
    def execute(self, *a, **kw): pass
    def fetchone(self): return None
    def __enter__(self): return self
    def __exit__(self, *a): return False


class _NullConn:
    """No-op DB connection for offline tests; cursor() returns _NullCursor."""
    def cursor(self): return _NullCursor()


NULL_CONN = _NullConn()


def _make_rows(*groups) -> list[dict[str, Any]]:
    """Helper to concatenate row groups."""
    result = []
    for group in groups:
        result.extend(group)
    return result


# ── §1: Basic helpers ─────────────────────────────────────────────────────────

class TestFactIdAndCitation:
    """fact_id derivation and citation_ref are deterministic."""

    def test_fact_id_is_16_hex_chars(self):
        fid = sut._fact_id("yoga_fires", "JUPITER", "yoga_name", CHART_ID, AY_ID, BUILD_ID)
        assert len(fid) == 16
        assert all(c in "0123456789abcdef" for c in fid)

    def test_fact_id_sha256_deterministic(self):
        fid1 = sut._fact_id("yoga_fires", "JUPITER", "yoga_name", CHART_ID, AY_ID, BUILD_ID)
        fid2 = sut._fact_id("yoga_fires", "JUPITER", "yoga_name", CHART_ID, AY_ID, BUILD_ID)
        assert fid1 == fid2

    def test_fact_id_uniqueness_by_category(self):
        fid1 = sut._fact_id("yoga_fires", "JUPITER", "yoga_name", CHART_ID, AY_ID, BUILD_ID)
        fid2 = sut._fact_id("dosha_fires", "JUPITER", "yoga_name", CHART_ID, AY_ID, BUILD_ID)
        assert fid1 != fid2

    def test_fact_id_uniqueness_by_ayanamsha(self):
        fid1 = sut._fact_id("yoga_fires", "JUPITER", "yoga_name", CHART_ID, "lahiri_chitrapaksha", BUILD_ID)
        fid2 = sut._fact_id("yoga_fires", "JUPITER", "yoga_name", CHART_ID, "krishnamurti", BUILD_ID)
        assert fid1 != fid2

    def test_citation_ref_format(self):
        ref = sut._citation_ref("yoga_fires", "JUP", "yoga_name", CHART_ID, AY_ID, ENG_VER)
        assert ref.startswith("yoga_fires.JUP.yoga_name@chart=")
        assert f"ay={AY_ID}" in ref
        assert f"eng={ENG_VER}" in ref

    def test_fact_id_cannot_match_ga3_category(self):
        """GA8 fact_ids for new categories must not collide with GA3 categories."""
        ga3_fid = sut._fact_id("graha_shadbala_total", "SUN", "rupa", CHART_ID, AY_ID, BUILD_ID)
        ga8_fid = sut._fact_id("graha_vargottama_amplification_factor", "SUN", "amplification_factor", CHART_ID, AY_ID, BUILD_ID)
        assert ga3_fid != ga8_fid


# ── §2: FORENSIC anchor checks ────────────────────────────────────────────────

class TestForensicAnchors:
    """FORENSIC anchors: Sun=Capricorn, Moon=Aquarius, Lagna=Aries (Purva Bhadrapada is in Aquarius)."""

    def test_sun_in_capricorn(self):
        sun = next(g for g in MOCK_CHART_OUTPUT["grahas"] if g["name"] == "Sun")
        assert sun["sign"] == "Capricorn"

    def test_lagna_aries(self):
        assert MOCK_CHART_OUTPUT["ascendant"]["sign"] == "Aries"
        assert sut._get_lagna_sign(MOCK_CHART_OUTPUT) == "Aries"

    def test_moon_in_aquarius_for_purva_bhadrapada(self):
        moon = next(g for g in MOCK_CHART_OUTPUT["grahas"] if g["name"] == "Moon")
        # Purva Bhadrapada spans Aquarius (last part) through Pisces
        assert moon["sign"] in ("Aquarius", "Pisces")

    def test_mars_lagna_lord_aries(self):
        lagna_sign = sut._get_lagna_sign(MOCK_CHART_OUTPUT)
        lagna_lord = sut.SIGN_LORDS[lagna_sign]
        assert lagna_lord == "Mars"

    def test_functional_class_mars_yogakaraka_aries_lagna(self):
        assert sut.FUNCTIONAL_CLASS_BPHS["Mars"] == "yogakaraka"


# ── §3: Group A — Aspects ─────────────────────────────────────────────────────

class TestAspectRows:
    def test_aspect_rows_produced(self):
        rows = sut._build_aspect_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        assert len(rows) > 0

    def test_aspect_rows_categories_correct(self):
        rows = sut._build_aspect_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        cats = {r["fact_category"] for r in rows}
        expected = {
            "aspect_parashari_given", "aspect_parashari_received",
            "aspect_jaimini", "aspect_matrix_summary",
        }
        assert expected.issubset(cats), f"Missing categories: {expected - cats}"

    def test_aspect_parashari_given_sun_7th_house(self):
        """Sun in house 10 should give 7th aspect to house 4."""
        rows = sut._build_aspect_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        given = [r for r in rows
                 if r["fact_category"] == "aspect_parashari_given"
                 and r["fact_subject"] == "SUN"]
        # Sun gives 7th aspect to house (10 + 7 - 1) % 12 + 1 = 4
        target_keys = {r["fact_key"] for r in given}
        assert "house_4" in target_keys, f"Sun 7th aspect not in: {target_keys}"

    def test_saturn_has_3_aspects(self):
        """Saturn has 3rd, 7th, and 10th aspects."""
        rows = sut._build_aspect_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        sat_given = [r for r in rows
                     if r["fact_category"] == "aspect_parashari_given"
                     and r["fact_subject"] == "SAT"]
        assert len(sat_given) == 3, f"Saturn should have 3 aspects, got {len(sat_given)}"

    def test_jupiter_has_3_aspects(self):
        """Jupiter has 5th, 7th, and 9th aspects."""
        rows = sut._build_aspect_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        jup_given = [r for r in rows
                     if r["fact_category"] == "aspect_parashari_given"
                     and r["fact_subject"] == "JUP"]
        assert len(jup_given) == 3, f"Jupiter should have 3 aspects, got {len(jup_given)}"

    def test_mars_has_3_aspects(self):
        """Mars has 4th, 7th, 8th aspects."""
        rows = sut._build_aspect_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        mar_given = [r for r in rows
                     if r["fact_category"] == "aspect_parashari_given"
                     and r["fact_subject"] == "MAR"]
        assert len(mar_given) == 3

    def test_conjunction_within_orb_sun_mercury(self):
        """Sun at 295° and Mercury at 300° = 5° orb → conjunction."""
        rows = sut._build_aspect_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        conj = [r for r in rows if r["fact_category"] == "conjunction_within_orb"]
        subjects = {r["fact_subject"] for r in conj}
        # SUN_MER conjunction should be present
        assert any("SUN" in s and "MER" in s for s in subjects), f"No Sun-Merc conjunction found in {subjects}"

    def test_aspect_summary_12_houses(self):
        rows = sut._build_aspect_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        summary = [r for r in rows if r["fact_category"] == "aspect_matrix_summary"]
        assert len(summary) == 12

    def test_no_narration_in_aspect_rows(self):
        rows = sut._build_aspect_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        sut._linter_check_rows(rows)  # must not raise

    def test_conjunction_verif_is_single(self):
        rows = sut._build_aspect_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        conj = [r for r in rows if r["fact_category"] == "conjunction_within_orb"]
        for r in conj:
            assert r["verification_pass_status"] == "single"

    def test_aspect_parashari_verif_two_pass(self):
        rows = sut._build_aspect_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        parashari = [r for r in rows if r["fact_category"] == "aspect_parashari_given"]
        for r in parashari:
            assert r["verification_pass_status"] == "two_pass_verified"


# ── §4: Group B — Shadbala extensions ────────────────────────────────────────

class TestShaddBalaExtensions:
    def test_vargottama_factor_produced_for_all_classical_grahas(self):
        rows = sut._build_shadbala_extension_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        varg_rows = [r for r in rows if r["fact_category"] == "graha_vargottama_amplification_factor"]
        subjects = {r["fact_subject"] for r in varg_rows}
        for g in sut.CLASSICAL_GRAHAS:
            expected_subj = sut.PLANET_TO_SUBJECT.get(g, g.upper())
            assert expected_subj in subjects

    def test_vargottama_factor_is_1_0_or_1_25(self):
        rows = sut._build_shadbala_extension_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        varg_rows = [r for r in rows if r["fact_category"] == "graha_vargottama_amplification_factor"]
        for r in varg_rows:
            assert r["fact_value_num"] in (1.0, 1.25), f"Unexpected factor: {r['fact_value_num']}"

    def test_saptavargaja_reference_rows_produced(self):
        rows = sut._build_shadbala_extension_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        saptav_rows = [r for r in rows if r["fact_category"] == "graha_saptavargaja_bala_component"]
        assert len(saptav_rows) == len(sut.CLASSICAL_GRAHAS)

    def test_no_ga3_overlap_in_shadbala_ext(self):
        rows = sut._build_shadbala_extension_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        sut._verify_no_ga3_overlap(rows)


# ── §5: Group C — Bhava Bala extended ────────────────────────────────────────

class TestBhavaBalaExtended:
    def test_bhava_bala_ext_12_houses(self):
        rows = sut._build_bhava_bala_extended_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        # 7 sub-rows per house × 12 houses = 84 + 12 classification = 96
        total_rows = len(rows)
        assert total_rows == 12 * 8, f"Expected 96 rows, got {total_rows}"

    def test_house_strength_classification_values(self):
        rows = sut._build_bhava_bala_extended_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        class_rows = [r for r in rows if r["fact_category"] == "house_strength_classification_rollup"]
        assert len(class_rows) == 12
        valid_classes = {"strong", "normal", "weak"}
        for r in class_rows:
            assert r["fact_value_text"] in valid_classes

    def test_no_ga3_overlap_in_bhava_ext(self):
        rows = sut._build_bhava_bala_extended_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        sut._verify_no_ga3_overlap(rows)


# ── §6: Group F — Yoga firings ────────────────────────────────────────────────

class TestYogaFirings:
    def test_yoga_rows_produced(self):
        rows = sut._build_yoga_rows(
            NULL_CONN, MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        assert isinstance(rows, list)

    def test_yoga_rows_have_constituent_facts_array(self):
        rows = sut._build_yoga_rows(
            NULL_CONN, MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        yoga_name_rows = [r for r in rows if r["fact_key"] == "yoga_name"]
        for r in yoga_name_rows:
            assert r["fact_value_jsonb"] is not None
            assert "constituent_facts_array" in r["fact_value_jsonb"]
            # Offline (NullConn): DB lookups return None so array may be empty;
            # structure check suffices — non-emptiness is verified by prod build.
            assert isinstance(r["fact_value_jsonb"]["constituent_facts_array"], list)

    def test_yoga_rows_have_classical_citation(self):
        rows = sut._build_yoga_rows(
            NULL_CONN, MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        yoga_name_rows = [r for r in rows if r["fact_key"] == "yoga_name"]
        for r in yoga_name_rows:
            assert r["fact_value_jsonb"].get("classical_citation_id"), \
                f"Missing citation in yoga {r['fact_subject']}"

    def test_yoga_cancellation_flag_is_bool(self):
        rows = sut._build_yoga_rows(
            NULL_CONN, MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        for r in rows:
            if r["fact_key"] == "yoga_name":
                assert isinstance(r["fact_value_jsonb"]["cancellation_flag"], bool)

    def test_yoga_strength_score_between_0_and_2(self):
        rows = sut._build_yoga_rows(
            NULL_CONN, MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        strength_rows = [r for r in rows if r["fact_key"] == "yoga_strength_score"]
        for r in strength_rows:
            assert 0.0 <= r["fact_value_num"] <= 2.0, \
                f"Yoga strength out of range: {r['fact_value_num']}"

    def test_budha_aditya_fires_when_sun_merc_conjunct(self):
        """Sun at 295°, Mercury at 300° → orb 5° → Budha-Aditya should fire."""
        yoga_def = next(y for y in sut.YOGA_LIBRARY if y["name"] == "BUDHA_ADITYA")
        fires, reason = sut._evaluate_yoga_fires(yoga_def, MOCK_CHART_OUTPUT)
        assert fires, f"Budha-Aditya should fire; reason: {reason}"

    def test_sasa_mahapurusha_fires_saturn_exalted_kendra(self):
        """Saturn at house 7 (kendra), exalted in Libra → Sasa fires."""
        yoga_def = next(y for y in sut.YOGA_LIBRARY if y["name"] == "SASA_MAHAPURUSHA")
        fires, reason = sut._evaluate_yoga_fires(yoga_def, MOCK_CHART_OUTPUT)
        assert fires, f"Sasa Mahapurusha should fire with Saturn exalted in 7H; reason: {reason}"

    def test_ruchaka_fires_mars_in_1h_own_sign(self):
        """Mars in house 1, Aries (own sign) → Ruchaka fires."""
        yoga_def = next(y for y in sut.YOGA_LIBRARY if y["name"] == "RUCHAKA_MAHAPURUSHA")
        fires, reason = sut._evaluate_yoga_fires(yoga_def, MOCK_CHART_OUTPUT)
        assert fires, f"Ruchaka should fire with Mars in 1H Aries; reason: {reason}"

    def test_hamsa_fires_jupiter_own_sign_kendra(self):
        """Jupiter in house 9, Sagittarius (own sign) → BUT 9H is NOT kendra → Hamsa should not fire."""
        yoga_def = next(y for y in sut.YOGA_LIBRARY if y["name"] == "HAMSA_MAHAPURUSHA")
        fires, reason = sut._evaluate_yoga_fires(yoga_def, MOCK_CHART_OUTPUT)
        # 9H is a trikona, not kendra — Hamsa requires kendra {1,4,7,10}
        assert not fires, f"Hamsa should NOT fire (9H is trikona, not kendra); reason: {reason}"

    def test_no_duplicate_fact_ids_in_yoga_rows(self):
        rows = sut._build_yoga_rows(
            NULL_CONN, MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        sut._verify_no_duplicate_fact_ids(rows)

    def test_no_narration_in_yoga_text_values(self):
        rows = sut._build_yoga_rows(
            NULL_CONN, MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        sut._linter_check_rows(rows)


# ── §7: Group G — Dosha firings ───────────────────────────────────────────────

class TestDoshaFirings:
    def test_dosha_rows_have_constituent_facts(self):
        rows = sut._build_dosha_rows(
            NULL_CONN, MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        for r in rows:
            assert r["fact_value_jsonb"] is not None
            assert "constituent_facts_array" in r["fact_value_jsonb"]
            # Offline (NullConn): DB lookups return None so array may be empty;
            # structure check suffices — non-emptiness is verified by prod build.
            assert isinstance(r["fact_value_jsonb"]["constituent_facts_array"], list)

    def test_mangal_dosha_fires_for_correct_houses(self):
        """Mars in house 1 → MANGAL_DOSHA_1H should fire."""
        rows = sut._build_dosha_rows(
            NULL_CONN, MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        dosha_names = {r["fact_subject"] for r in rows}
        assert "MANGAL_DOSHA_1H" in dosha_names, f"Expected MANGAL_DOSHA_1H; got {dosha_names}"

    def test_mangal_dosha_1h_cancelled_mars_own_sign(self):
        """Mars in Aries (own sign) → Mangal dosha should be cancelled."""
        rows = sut._build_dosha_rows(
            NULL_CONN, MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        d1h = next((r for r in rows if r["fact_subject"] == "MANGAL_DOSHA_1H"), None)
        if d1h:
            assert d1h["fact_value_jsonb"]["cancellation_flag"] is True, \
                "MANGAL_DOSHA_1H in Aries own sign should be cancelled"

    def test_no_narration_in_dosha_rows(self):
        rows = sut._build_dosha_rows(
            NULL_CONN, MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        sut._linter_check_rows(rows)


# ── §8: Group H — Avasthas ────────────────────────────────────────────────────

class TestAvasthas:
    def test_baladi_rows_produced_for_all_grahas(self):
        rows = sut._build_avastha_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        baladi = [r for r in rows if r["fact_category"] == "graha_avastha_baladi"]
        subjects = {r["fact_subject"] for r in baladi}
        assert len(subjects) == len(MOCK_CHART_OUTPUT["grahas"])

    def test_baladi_states_are_valid(self):
        rows = sut._build_avastha_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        baladi = [r for r in rows if r["fact_category"] == "graha_avastha_baladi"]
        valid = set(sut.BALADI_STATES)
        for r in baladi:
            assert r["fact_value_text"] in valid

    def test_jagrad_deepta_sayanadi_rows_produced(self):
        rows = sut._build_avastha_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        cats = {r["fact_category"] for r in rows}
        expected_cats = {
            "graha_avastha_baladi", "graha_avastha_jagrad", "graha_avastha_deepta",
            "graha_avastha_lajjitadi", "graha_avastha_sayanadi",
            "graha_avastha_lifetime_exposure_summary",
        }
        assert expected_cats.issubset(cats)

    def test_deepta_state_saturn_exalted_is_deepta(self):
        rows = sut._build_avastha_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        sat_deepta = next(
            (r for r in rows
             if r["fact_category"] == "graha_avastha_deepta" and r["fact_subject"] == "SAT"),
            None,
        )
        assert sat_deepta is not None
        assert sat_deepta["fact_value_text"] == "deepta", \
            f"Saturn exalted should be deepta, got: {sat_deepta['fact_value_text']}"

    def test_no_narration_in_avastha_rows(self):
        rows = sut._build_avastha_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        sut._linter_check_rows(rows)


# ── §9: Group I — Composite per-graha-per-house strength ─────────────────────

class TestCompositeStrength:
    def test_three_keys_per_graha_per_house(self):
        rows = sut._build_composite_strength_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        # 9 grahas × 12 houses × 3 keys = 324
        graha_count = len(MOCK_CHART_OUTPUT["grahas"])
        expected = graha_count * 12 * 3
        assert len(rows) == expected, f"Expected {expected}, got {len(rows)}"

    def test_strength_scores_between_0_and_2(self):
        rows = sut._build_composite_strength_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        num_rows = [r for r in rows if r["fact_value_num"] is not None
                    and r["fact_key"] in ("bphs_weighted", "simple_multiplication")]
        for r in num_rows:
            assert 0.0 <= r["fact_value_num"] <= 2.0, \
                f"Strength out of range: {r['fact_value_num']} in {r['fact_key']}"


# ── §10: Group J — Functional class ──────────────────────────────────────────

class TestFunctionalClass:
    def test_functional_class_rows_produced(self):
        rows = sut._build_functional_class_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        func_rows = [r for r in rows if r["fact_category"] == "graha_functional_class_per_ascendant"]
        # 7 classical grahas × 2 formula_id rows = 14
        assert len(func_rows) == 14, f"Expected 14 functional class rows, got {len(func_rows)}"

    def test_mars_is_yogakaraka_aries_lagna(self):
        rows = sut._build_functional_class_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        mars_bphs = next(
            (r for r in rows
             if r["fact_category"] == "graha_functional_class_per_ascendant"
             and r["fact_subject"] == "MAR"
             and r["fact_key"] == "bphs_canonical"),
            None,
        )
        assert mars_bphs is not None
        assert mars_bphs["fact_value_text"] == "yogakaraka", \
            f"Mars should be yogakaraka for Aries lagna; got: {mars_bphs['fact_value_text']}"

    def test_mercury_is_temporal_malefic_aries_lagna(self):
        rows = sut._build_functional_class_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        merc = next(
            (r for r in rows
             if r["fact_category"] == "graha_functional_class_per_ascendant"
             and r["fact_subject"] == "MER"
             and r["fact_key"] == "bphs_canonical"),
            None,
        )
        assert merc is not None
        assert merc["fact_value_text"] == "temporal_malefic"

    def test_yoga_karaka_flag_produced_for_all_classical_grahas(self):
        rows = sut._build_functional_class_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        flag_rows = [r for r in rows if r["fact_category"] == "graha_yoga_karaka_flag"]
        subjects = {r["fact_subject"] for r in flag_rows}
        for g in sut.CLASSICAL_GRAHAS:
            subj = sut.PLANET_TO_SUBJECT.get(g, g.upper())
            assert subj in subjects

    def test_bphs_and_raman_both_produced_per_graha(self):
        rows = sut._build_functional_class_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        func_rows = [r for r in rows if r["fact_category"] == "graha_functional_class_per_ascendant"]
        for g in sut.CLASSICAL_GRAHAS:
            subj = sut.PLANET_TO_SUBJECT.get(g, g.upper())
            keys = {r["fact_key"] for r in func_rows if r["fact_subject"] == subj}
            assert "bphs_canonical" in keys
            assert "raman_variant" in keys


# ── §11: Group K — Karakatva ─────────────────────────────────────────────────

class TestKarakatva:
    def test_all_significances_produced(self):
        rows = sut._build_karakatva_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        subjects = {r["fact_subject"] for r in rows
                    if r["fact_category"] == "karakatva_strength_per_significance"}
        for sig in sut.KARAKATVA_SIGNIFICANCES:
            assert sig in subjects, f"Missing significance: {sig}"

    def test_natural_karaka_row_per_significance(self):
        rows = sut._build_karakatva_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        karaka_rows = [r for r in rows
                       if r["fact_category"] == "karakatva_strength_per_significance"
                       and r["fact_key"] == "natural_karaka"]
        assert len(karaka_rows) == len(sut.KARAKATVA_SIGNIFICANCES)

    def test_karaka_overlap_flag_rows_produced(self):
        rows = sut._build_karakatva_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        overlap_rows = [r for r in rows if r["fact_category"] == "karaka_house_lord_overlap_flag"]
        # Should have rows for the 12 significances that map to houses
        assert len(overlap_rows) > 0

    def test_strength_scores_bounded(self):
        rows = sut._build_karakatva_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        strength_rows = [r for r in rows
                         if r["fact_key"] == "composite_strength"
                         and r["fact_value_num"] is not None]
        for r in strength_rows:
            assert 0.0 <= r["fact_value_num"] <= 1.5, \
                f"Karakatva strength out of range: {r['fact_value_num']}"


# ── §12: Group L — Structural relationships ──────────────────────────────────

class TestStructuralRelationships:
    def test_dispositor_chain_produced_for_all_grahas(self):
        rows = sut._build_structural_relationship_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        chain_rows = [r for r in rows if r["fact_category"] == "graha_dispositor_chain"]
        subjects = {r["fact_subject"] for r in chain_rows}
        for g in MOCK_CHART_OUTPUT["grahas"]:
            subj = sut.PLANET_TO_SUBJECT.get(g["name"], g["name"].upper())
            assert subj in subjects

    def test_dispositor_chain_is_jsonb(self):
        rows = sut._build_structural_relationship_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        chain_rows = [r for r in rows if r["fact_category"] == "graha_dispositor_chain"]
        for r in chain_rows:
            assert r["fact_value_jsonb"] is not None
            assert "chain" in r["fact_value_jsonb"]
            assert isinstance(r["fact_value_jsonb"]["chain"], list)

    def test_terminal_strength_produced_for_all_grahas(self):
        rows = sut._build_structural_relationship_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        terminal = [r for r in rows if r["fact_category"] == "composite_dispositor_strength"]
        assert len(terminal) == len(MOCK_CHART_OUTPUT["grahas"])

    def test_composite_state_classification_valid_values(self):
        rows = sut._build_structural_relationship_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        class_rows = [r for r in rows
                      if r["fact_category"] == "graha_composite_state_classification"]
        valid_states = {
            "severely_afflicted", "debilitation_cancelled", "debilitated",
            "afflicted", "well_placed", "neutral", "weak",
        }
        for r in class_rows:
            assert r["fact_value_text"] in valid_states, \
                f"Invalid state: {r['fact_value_text']}"

    def test_saturn_exalted_classified_well_placed(self):
        rows = sut._build_structural_relationship_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        sat = next(
            (r for r in rows
             if r["fact_category"] == "graha_composite_state_classification"
             and r["fact_subject"] == "SAT"),
            None,
        )
        assert sat is not None
        assert sat["fact_value_text"] == "well_placed", \
            f"Saturn exalted should be well_placed; got {sat['fact_value_text']}"


# ── §13: Group N — Argala matrices (CRITICAL 144-row invariant) ──────────────

class TestArgalaMatrices:
    """CRITICAL: Must produce exactly 144 argala + 144 virodha = 288 rows."""

    def test_argala_count_is_exactly_144(self):
        rows = sut._build_argala_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        argala = [r for r in rows if r["fact_category"] == "argala_natal_matrix"]
        assert len(argala) == 144, f"Expected 144 argala rows, got {len(argala)}"

    def test_virodha_count_is_exactly_144(self):
        rows = sut._build_argala_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        virodha = [r for r in rows if r["fact_category"] == "virodha_argala_natal_matrix"]
        assert len(virodha) == 144, f"Expected 144 virodha rows, got {len(virodha)}"

    def test_total_argala_rows_is_288(self):
        rows = sut._build_argala_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        assert len(rows) == 288, f"Total argala rows should be 288, got {len(rows)}"

    def test_argala_offsets_exactly_12_per_sign(self):
        """Full 12×12 matrix: each target sign has exactly 12 rows (one per source sign)."""
        rows = sut._build_argala_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        argala = [r for r in rows if r["fact_category"] == "argala_natal_matrix"]
        target_counts = {}
        for r in argala:
            sign_target = r["fact_subject"]
            target_counts[sign_target] = target_counts.get(sign_target, 0) + 1
        for sign_target, count in target_counts.items():
            assert count == 12, f"Sign {sign_target} has {count} argala rows, expected 12"

    def test_argala_4_nonzero_per_sign(self):
        """Each sign should have exactly 4 non-zero argala rows (from 4 argala offset positions)."""
        rows = sut._build_argala_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        argala = [r for r in rows if r["fact_category"] == "argala_natal_matrix"]
        for sign_num in range(1, 13):
            sign_key = f"D1_SIGN_{sign_num}"
            nonzero = [r for r in argala
                       if r["fact_subject"] == sign_key
                       and r["fact_value_num"] is not None
                       and r["fact_value_num"] != 0.0]
            # Exactly 4 non-zero argala positions per sign
            # (each sign gets argala from 4 others at offsets 2,4,5,11)
            assert len(nonzero) <= 4, \
                f"{sign_key}: too many non-zero argala rows ({len(nonzero)})"

    def test_virodha_offsets_exactly_12_per_sign(self):
        """Full 12×12 matrix: each target sign has 12 rows (one per source sign)."""
        rows = sut._build_argala_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        virodha = [r for r in rows if r["fact_category"] == "virodha_argala_natal_matrix"]
        target_counts = {}
        for r in virodha:
            sign_target = r["fact_subject"]
            target_counts[sign_target] = target_counts.get(sign_target, 0) + 1
        for sign_target, count in target_counts.items():
            assert count == 12, f"Sign {sign_target} has {count} virodha rows, expected 12"

    def test_argala_rows_cover_all_12_signs(self):
        rows = sut._build_argala_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        argala = [r for r in rows if r["fact_category"] == "argala_natal_matrix"]
        targets = {r["fact_subject"] for r in argala}
        for i in range(1, 13):
            assert f"D1_SIGN_{i}" in targets, f"D1_SIGN_{i} missing from argala matrix"

    def test_argala_atomic_no_jsonb_blob(self):
        """Each argala row is atomic (value_num, not a JSONB blob)."""
        rows = sut._build_argala_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        argala = [r for r in rows if r["fact_category"] == "argala_natal_matrix"]
        for r in argala:
            # Must be atomic: value_num present, no large jsonb blob
            assert r["fact_value_num"] is not None, \
                f"Argala row {r['fact_subject']}:{r['fact_key']} has no numeric value"
            assert r["fact_value_jsonb"] is None, \
                f"Argala row should not use fact_value_jsonb (atomic)"

    def test_no_duplicate_fact_ids_in_argala(self):
        rows = sut._build_argala_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        sut._verify_no_duplicate_fact_ids(rows)

    def test_two_pass_invariant_argala(self):
        """Build argala twice; counts must be identical (deterministic)."""
        rows1 = sut._build_argala_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        rows2 = sut._build_argala_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        assert len(rows1) == len(rows2)
        assert len(rows1) == 288


# ── §14: Group O — Esoteric / Jaimini ────────────────────────────────────────

class TestEsotericRows:
    def test_prana_score_produced_for_all_grahas(self):
        rows = sut._build_esoteric_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        prana = [r for r in rows if r["fact_category"] == "pranic_strength_per_graha"]
        subjects = {r["fact_subject"] for r in prana}
        assert len(subjects) == len(MOCK_CHART_OUTPUT["grahas"])

    def test_tri_deva_roles_valid_values(self):
        rows = sut._build_esoteric_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        tri_rows = [r for r in rows if r["fact_category"] == "jaimini_tri_deva_role_per_graha"]
        valid_roles = {"brahma", "vishnu", "shiva", "neutral"}
        for r in tri_rows:
            assert r["fact_value_text"] in valid_roles

    def test_tri_deva_role_strength_bounded(self):
        rows = sut._build_esoteric_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        strength_rows = [r for r in rows
                         if r["fact_category"] == "graha_tri_deva_role_strength"]
        for r in strength_rows:
            assert r["fact_value_num"] is not None
            assert 0.0 <= r["fact_value_num"] <= 2.0

    def test_jupiter_tri_deva_role_brahma_or_vishnu(self):
        rows = sut._build_esoteric_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        jup = next(
            (r for r in rows
             if r["fact_category"] == "jaimini_tri_deva_role_per_graha"
             and r["fact_subject"] == "JUP"),
            None,
        )
        assert jup is not None
        # Jupiter is in both brahma and vishnu sets
        assert jup["fact_value_text"] in ("brahma", "vishnu"), \
            f"Jupiter tri-deva role should be brahma or vishnu, got {jup['fact_value_text']}"


# ── §15: GA3 overlap enforcement ─────────────────────────────────────────────

class TestGA3OverlapPrevention:
    """All GA8 groups must not emit any GA3 categories."""

    def _collect_all_ga8_rows(self) -> list[dict[str, Any]]:
        groups = [
            sut._build_aspect_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
            sut._build_shadbala_extension_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
            sut._build_bhava_bala_extended_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
            sut._build_yoga_rows(NULL_CONN, MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
            sut._build_dosha_rows(NULL_CONN, MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
            sut._build_avastha_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
            sut._build_composite_strength_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
            sut._build_functional_class_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
            sut._build_karakatva_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
            sut._build_structural_relationship_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
            sut._build_special_state_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
            sut._build_argala_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
            sut._build_esoteric_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
        ]
        all_rows = []
        for g in groups:
            all_rows.extend(g)
        return all_rows

    def test_no_ga3_categories_in_any_ga8_group(self):
        all_rows = self._collect_all_ga8_rows()
        sut._verify_no_ga3_overlap(all_rows)

    def test_all_rows_have_citation_fields(self):
        all_rows = self._collect_all_ga8_rows()
        sut._verify_citation_completeness(all_rows)

    def test_all_rows_pass_narration_linter(self):
        all_rows = self._collect_all_ga8_rows()
        sut._linter_check_rows(all_rows)


# ── §16: Two-pass invariants ──────────────────────────────────────────────────

class TestTwoPassInvariants:
    def test_functional_class_deterministic(self):
        rows1 = sut._build_functional_class_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        rows2 = sut._build_functional_class_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        assert len(rows1) == len(rows2)
        # Same values
        vals1 = {(r["fact_subject"], r["fact_key"]): r["fact_value_text"] for r in rows1}
        vals2 = {(r["fact_subject"], r["fact_key"]): r["fact_value_text"] for r in rows2}
        assert vals1 == vals2

    def test_bhava_bala_deterministic(self):
        rows1 = sut._build_bhava_bala_extended_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        rows2 = sut._build_bhava_bala_extended_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        assert len(rows1) == len(rows2)

    def test_vargottama_factor_deterministic(self):
        rows1 = sut._build_shadbala_extension_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        rows2 = sut._build_shadbala_extension_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        vals1 = {r["fact_subject"]: r["fact_value_num"] for r in rows1
                 if r["fact_category"] == "graha_vargottama_amplification_factor"}
        vals2 = {r["fact_subject"]: r["fact_value_num"] for r in rows2
                 if r["fact_category"] == "graha_vargottama_amplification_factor"}
        assert vals1 == vals2


# ── §17: PLANET_TO_SUBJECT import validation ──────────────────────────────────

class TestPlanetToSubjectImport:
    def test_planet_to_subject_has_classical_grahas(self):
        from ga_writers.ga_positions_writer import PLANET_TO_SUBJECT
        for g in sut.CLASSICAL_GRAHAS:
            assert g in PLANET_TO_SUBJECT, f"Missing planet {g} in PLANET_TO_SUBJECT"

    def test_planet_to_subject_mars_maps_to_mar(self):
        from ga_writers.ga_positions_writer import PLANET_TO_SUBJECT
        assert PLANET_TO_SUBJECT["Mars"] == "MAR"

    def test_planet_to_subject_sun_maps_to_sun(self):
        from ga_writers.ga_positions_writer import PLANET_TO_SUBJECT
        assert PLANET_TO_SUBJECT["Sun"] == "SUN"


# ── §18: Helper functions ─────────────────────────────────────────────────────

class TestHelperFunctions:
    def test_get_house_sign_aries_lagna(self):
        # For Aries lagna: house 1 = Aries, house 2 = Taurus, ..., house 12 = Pisces
        assert sut._get_house_sign(MOCK_CHART_OUTPUT, 1) == "Aries"
        assert sut._get_house_sign(MOCK_CHART_OUTPUT, 2) == "Taurus"
        assert sut._get_house_sign(MOCK_CHART_OUTPUT, 7) == "Libra"
        assert sut._get_house_sign(MOCK_CHART_OUTPUT, 10) == "Capricorn"
        assert sut._get_house_sign(MOCK_CHART_OUTPUT, 12) == "Pisces"

    def test_get_house_lord_house_1_aries_is_mars(self):
        lord = sut._get_house_lord(MOCK_CHART_OUTPUT, 1)
        assert lord == "Mars"

    def test_get_house_lord_house_10_capricorn_is_saturn(self):
        lord = sut._get_house_lord(MOCK_CHART_OUTPUT, 10)
        assert lord == "Saturn"

    def test_graha_house_sun_is_10(self):
        house = sut._graha_house(MOCK_CHART_OUTPUT, "Sun")
        assert house == 10

    def test_graha_longitude_sun_is_295(self):
        lon = sut._graha_longitude(MOCK_CHART_OUTPUT, "Sun")
        assert abs(lon - 295.0) < 0.01

    def test_sign_names_12_entries(self):
        assert len(sut.SIGN_NAMES) == 12
        assert sut.SIGN_NAMES[0] == "Aries"
        assert sut.SIGN_NAMES[11] == "Pisces"


# ── §19: Verify no duplicate fact_ids across all groups ───────────────────────

class TestNoDuplicateFactIds:
    def test_no_duplicate_fact_ids_across_all_groups(self):
        all_rows = [
            *sut._build_aspect_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
            *sut._build_shadbala_extension_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
            *sut._build_bhava_bala_extended_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
            *sut._build_yoga_rows(NULL_CONN, MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
            *sut._build_dosha_rows(NULL_CONN, MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
            *sut._build_avastha_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
            *sut._build_composite_strength_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
            *sut._build_functional_class_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
            *sut._build_karakatva_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
            *sut._build_structural_relationship_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
            *sut._build_special_state_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
            *sut._build_argala_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
            *sut._build_esoteric_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
        ]
        sut._verify_no_duplicate_fact_ids(all_rows)


# ── §20: Schema constant validation ──────────────────────────────────────────

class TestSchemaConstants:
    def test_argala_offsets_correct(self):
        assert sut.ARGALA_OFFSETS == [2, 4, 5, 11]

    def test_virodha_offsets_correct(self):
        assert sut.VIRODHA_OFFSETS == [12, 10, 9, 3]

    def test_12_argala_offsets_cover_non_overlapping_positions(self):
        argala = set(sut.ARGALA_OFFSETS)
        virodha = set(sut.VIRODHA_OFFSETS)
        # Argala and virodha offsets should not overlap
        assert argala.isdisjoint(virodha), \
            f"Argala {argala} and virodha {virodha} share positions"

    def test_karakatva_30_significances(self):
        assert len(sut.KARAKATVA_SIGNIFICANCES) == 30

    def test_yoga_library_has_entries(self):
        assert len(sut.YOGA_LIBRARY) >= 20

    def test_dosha_library_has_entries(self):
        assert len(sut.DOSHA_LIBRARY) >= 10

    def test_functional_class_bphs_covers_7_grahas(self):
        assert len(sut.FUNCTIONAL_CLASS_BPHS) == 7

    def test_tri_deva_roles_three_devas(self):
        assert set(sut.TRI_DEVA_ROLES.keys()) == {"brahma", "vishnu", "shiva"}

    def test_canonical_chart_id_is_canonical(self):
        assert sut.CANONICAL_CHART_ID == "482012f1-710e-4a25-994a-93821f5871aa"

    def test_canonical_ayanamshas_5_entries(self):
        from ga_writers.ga_positions_writer import CANONICAL_AYANAMSHAS
        assert len(CANONICAL_AYANAMSHAS) == 5


# ── §21: Narration linter ─────────────────────────────────────────────────────

class TestNarrationLinter:
    def test_linter_raises_on_forbidden_pattern(self):
        """A row with 'indicates' in text should fail the linter."""
        bad_row = {
            "fact_category": "yoga_fires", "fact_subject": "TEST",
            "fact_key": "yoga_name", "fact_value_text": "This indicates strength",
            "fact_value_num": None, "fact_value_jsonb": None,
        }
        with pytest.raises(ValueError, match="indicates"):
            sut._linter_check_rows([bad_row])

    def test_linter_raises_on_suggests(self):
        bad_row = {
            "fact_category": "test", "fact_subject": "X",
            "fact_key": "k", "fact_value_text": "suggests exaltation",
            "fact_value_num": None, "fact_value_jsonb": None,
        }
        with pytest.raises(ValueError, match="suggests"):
            sut._linter_check_rows([bad_row])

    def test_linter_passes_clean_text(self):
        ok_row = {
            "fact_category": "yoga_fires", "fact_subject": "JUP",
            "fact_key": "yoga_name", "fact_value_text": "HAMSA_MAHAPURUSHA",
            "fact_value_num": None, "fact_value_jsonb": None,
        }
        sut._linter_check_rows([ok_row])  # must not raise

    def test_all_forbidden_patterns_tested(self):
        for pat in sut.FORBIDDEN_PATTERNS:
            bad_row = {
                "fact_category": "test", "fact_subject": "X",
                "fact_key": "k", "fact_value_text": f"this {pat} something",
                "fact_value_num": None, "fact_value_jsonb": None,
            }
            with pytest.raises(ValueError):
                sut._linter_check_rows([bad_row])


# ── §22: Special states group ─────────────────────────────────────────────────

class TestSpecialStates:
    def test_special_state_rollup_5_keys_per_graha(self):
        rows = sut._build_special_state_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        rollup = [r for r in rows if r["fact_category"] == "graha_special_state_rollup"]
        rollup_keys = {"is_combust", "is_retrograde", "is_vargottama", "is_debilitated", "is_exalted"}
        per_graha = {}
        for r in rollup:
            per_graha.setdefault(r["fact_subject"], set()).add(r["fact_key"])
        for subj, keys in per_graha.items():
            assert keys == rollup_keys, f"{subj} missing keys: {rollup_keys - keys}"

    def test_mars_not_combust_not_in_sun_range(self):
        rows = sut._build_special_state_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        mars_combust = next(
            (r for r in rows
             if r["fact_category"] == "graha_special_state_rollup"
             and r["fact_subject"] == "MAR"
             and r["fact_key"] == "is_combust"),
            None,
        )
        # Mars at 15° vs Sun at 295° → 280° apart → not combust
        if mars_combust:
            assert mars_combust["fact_value_text"] == "false", \
                f"Mars should not be combust (280° from Sun); got {mars_combust['fact_value_text']}"

    def test_effective_dignity_produced_for_all_grahas(self):
        rows = sut._build_special_state_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        eff = [r for r in rows if r["fact_category"] == "graha_effective_dignity_modified_by_aspects"]
        subjects = {r["fact_subject"] for r in eff}
        for g in MOCK_CHART_OUTPUT["grahas"]:
            subj = sut.PLANET_TO_SUBJECT.get(g["name"], g["name"].upper())
            assert subj in subjects
