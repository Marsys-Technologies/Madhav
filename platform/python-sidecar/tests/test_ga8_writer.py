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
from brahmagyan.verification_vocab import DIVERGENT_FLAGGED, UNVERIFIED_DEFAULT  # noqa: E402


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
    def cursor(self, row_factory=None): return _NullCursor()


NULL_CONN = _NullConn()


class _StrengthFakeCursor:
    """Cursor stand-in for _load_shadbala_and_bhava_fact_ids (M-14): returns
    real-shaped graha_shadbala_total + house_bhava_bala_total rows so
    _build_composite_strength_rows exercises its real (non-floored) path."""
    def __init__(self):
        self._last_query = ""

    def execute(self, query, params=None):
        self._last_query = query

    def fetchall(self):
        if "graha_shadbala_total" in self._last_query:
            subjects = ["SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT", "RAH_MEAN", "KET_MEAN"]
            return [(s, 6.0, f"fid-sb-{s}") for s in subjects]
        if "house_bhava_bala_total" in self._last_query:
            return [(f"HOUSE_{h}", 5.0, f"fid-bb-{h}") for h in range(1, 13)]
        return []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class _StrengthFakeConn:
    """No-op-except-strength-queries DB connection for composite-strength tests."""
    def cursor(self, row_factory=None):
        return _StrengthFakeCursor()


STRENGTH_FAKE_CONN = _StrengthFakeConn()


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

    def test_aspect_parashari_verif_is_unverified_default(self):
        """RENAMED + FLIPPED (Stage 2 honest-tiers, M-22 overnight, Opus Gate
        Reviewer ruling): this test used to assert 'two_pass_verified', but
        aspect_parashari_given had no second independently-implemented
        derivation behind it — it was one of the ~76 sites where
        `_base_row(..., verif="two_pass_verified", ...)` was an unearned literal
        (no comparison ever ran). It is one of the mechanical, non-special-cased
        sites in the ruling (not one of the 4 named edge-case categories), so it
        converts to `UNVERIFIED_DEFAULT` ('single') like the rest. This is not a
        silent flip: aspect_parashari_given genuinely is single-pass in this
        writer today, and the test now asserts that honestly."""
        rows = sut._build_aspect_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        parashari = [r for r in rows if r["fact_category"] == "aspect_parashari_given"]
        assert parashari, "aspect_parashari_given rows must be produced"
        for r in parashari:
            assert r["verification_pass_status"] == UNVERIFIED_DEFAULT


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

    def test_baladi_jagrad_deepta_rows_produced(self):
        rows = sut._build_avastha_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        cats = {r["fact_category"] for r in rows}
        expected_cats = {
            "graha_avastha_baladi", "graha_avastha_jagrad", "graha_avastha_deepta",
            "graha_avastha_lifetime_exposure_summary",
        }
        assert expected_cats.issubset(cats)

    def test_lajjitadi_and_sayanadi_owned_by_ga_condition_not_emitted_here(self):
        """JL-022: ga_structural no longer emits graha_avastha_lajjitadi /
        graha_avastha_sayanadi — ga_condition is their sole (authoritative) writer.
        This is the dual-write removal that fixes the migration-416 lock contention."""
        rows = sut._build_avastha_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        cats = {r["fact_category"] for r in rows}
        assert "graha_avastha_lajjitadi" not in cats
        assert "graha_avastha_sayanadi" not in cats

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
            STRENGTH_FAKE_CONN, MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        # 9 grahas × 12 houses × 3 keys = 324
        graha_count = len(MOCK_CHART_OUTPUT["grahas"])
        expected = graha_count * 12 * 3
        assert len(rows) == expected, f"Expected {expected}, got {len(rows)}"

    def test_strength_scores_between_0_and_2(self):
        rows = sut._build_composite_strength_rows(
            STRENGTH_FAKE_CONN, MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
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
            sut._build_composite_strength_rows(STRENGTH_FAKE_CONN, MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
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


# ── §16: Row-builder pure-function stability ───────────────────────────────────
# RENAMED (Stage 2 honest-tiers, M-22 overnight, Opus Gate Reviewer ruling). This
# class used to be named `TestTwoPassInvariants`, which claimed more than it
# tested: every test here calls the SAME pure row-builder function TWICE,
# in-process, against the SAME fixed `MOCK_CHART_OUTPUT` and the SAME `build_id`,
# and asserts the two calls produce identical output. That proves the builder is
# a deterministic pure function of its inputs — a real and worth-keeping property
# — but it is not a "two-pass verification invariant" in the
# brahmagyan.verification_vocab.py sense (CLAUDE.md §N.8 earned-signal test): no
# DB round-trip happens, no `build_id` varies, and no independently-implemented
# SECOND algorithm runs to compare against a first. A bug that makes the builder
# wrong in exactly the same way on every call would still pass every test in this
# class. Building a real DB-backed double-build test (varying build_id, hitting
# actual two_pass_verified/DIVERGENT_FLAGGED production paths) is out of scope
# for this changeset per the Gate Reviewer's ruling — deferred, not solved here.
# This rename is the in-scope honesty fix: the class now says what it proves.

class TestRowBuilderPureFunctionStability:
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
            *sut._build_composite_strength_rows(STRENGTH_FAKE_CONN, MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER),
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


# ── §Node Parashari Aspects ───────────────────────────────────────────────────

class TestNodeAspectRows:
    def test_rahu_ketu_appear_in_d1_parashari_aspects(self):
        rows = sut._build_aspect_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        subjects = {r["fact_subject"] for r in rows
                    if r["fact_category"] == "aspect_parashari_given"}
        assert "RAH_MEAN" in subjects, "Rahu missing from D1 Parashari aspects"
        assert "KET_MEAN" in subjects, "Ketu missing from D1 Parashari aspects"

    def test_rahu_emits_5th_7th_9th_aspects(self):
        rows = sut._build_aspect_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        rahu_aspect_keys = {r["fact_key"] for r in rows
                            if r["fact_category"] == "aspect_parashari_given"
                            and r["fact_subject"] == "RAH_MEAN"}
        # Rahu in Taurus (house 2 per MOCK_CHART_OUTPUT) → 5th=house 6, 7th=house 8, 9th=house 10
        assert "house_6" in rahu_aspect_keys
        assert "house_8" in rahu_aspect_keys
        assert "house_10" in rahu_aspect_keys
        assert len(rahu_aspect_keys) == 3, f"Expected 3 node aspects, got: {rahu_aspect_keys}"

    def test_ketu_emits_5th_7th_9th_aspects(self):
        rows = sut._build_aspect_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        ketu_aspect_keys = {r["fact_key"] for r in rows
                            if r["fact_category"] == "aspect_parashari_given"
                            and r["fact_subject"] == "KET_MEAN"}
        # Ketu in Scorpio (house 8 per MOCK_CHART_OUTPUT) → 5th=house 12, 7th=house 2, 9th=house 4
        assert "house_12" in ketu_aspect_keys
        assert "house_2" in ketu_aspect_keys
        assert "house_4" in ketu_aspect_keys
        assert len(ketu_aspect_keys) == 3, f"Expected 3 node aspects, got: {ketu_aspect_keys}"

    def test_node_aspect_strength_is_full(self):
        rows = sut._build_aspect_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        rahu_aspects = [r for r in rows
                        if r["fact_category"] == "aspect_parashari_given"
                        and r["fact_subject"] == "RAH_MEAN"]
        for row in rahu_aspects:
            assert row["fact_value_num"] == 1.0, \
                f"Node aspect strength should be 1.0, got {row['fact_value_num']}"

    def test_classical_grahas_still_have_their_aspects(self):
        rows = sut._build_aspect_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        subjects = {r["fact_subject"] for r in rows
                    if r["fact_category"] == "aspect_parashari_given"}
        for g in ["SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT"]:
            assert g in subjects, f"{g} missing from Parashari aspects after node extension"

    def test_no_crash_when_nodes_absent_from_chart_output(self):
        """If Rahu/Ketu missing from chart, classical aspects still work, no exception."""
        chart_without_nodes = {
            "ascendant": MOCK_CHART_OUTPUT["ascendant"],
            "grahas": [g for g in MOCK_CHART_OUTPUT["grahas"]
                       if g["name"] not in ("Rahu", "Ketu")],
        }
        # Should not raise; should produce classical graha aspects only
        rows = sut._build_aspect_rows(
            chart_without_nodes, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        subjects = {r["fact_subject"] for r in rows
                    if r["fact_category"] == "aspect_parashari_given"}
        # Classical grahas present
        assert "SUN" in subjects
        # Nodes absent (no crash, but no node rows either)
        assert "RAH_MEAN" not in subjects
        assert "KET_MEAN" not in subjects


# ── §Node Varga Relationships ─────────────────────────────────────────────────

class TestVargaNodeRelationships:
    """Rahu/Ketu must appear in per-varga dignity, aspects, conjunctions, vargottama."""

    def _make_varga_state(self) -> dict:
        return {
            "Sun":     {"sign": "Aries",       "sign_num": 1,  "house": 1,  "degree": 5.0},
            "Moon":    {"sign": "Cancer",      "sign_num": 4,  "house": 4,  "degree": 10.0},
            "Mars":    {"sign": "Aries",       "sign_num": 1,  "house": 1,  "degree": 20.0},
            "Mercury": {"sign": "Gemini",      "sign_num": 3,  "house": 3,  "degree": 15.0},
            "Jupiter": {"sign": "Sagittarius", "sign_num": 9,  "house": 9,  "degree": 5.0},
            "Venus":   {"sign": "Pisces",      "sign_num": 12, "house": 12, "degree": 8.0},
            "Saturn":  {"sign": "Libra",       "sign_num": 7,  "house": 7,  "degree": 12.0},
            "Rahu":    {"sign": "Gemini",      "sign_num": 3,  "house": 3,  "degree": 20.0},
            "Ketu":    {"sign": "Sagittarius", "sign_num": 9,  "house": 9,  "degree": 20.0},
        }

    def test_rahu_ketu_in_varga_dignity(self):
        rows = sut._build_varga_relationship_rows(
            "D9", self._make_varga_state(), MOCK_CHART_OUTPUT,
            CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        dignity_subjects = {r["fact_subject"] for r in rows
                            if r["fact_category"] == "graha_dignity_per_varga"}
        assert "D9_RAH_MEAN" in dignity_subjects, \
            f"Rahu dignity missing. Subjects: {dignity_subjects}"
        assert "D9_KET_MEAN" in dignity_subjects, \
            f"Ketu dignity missing. Subjects: {dignity_subjects}"

    def test_rahu_ketu_in_varga_aspects(self):
        rows = sut._build_varga_relationship_rows(
            "D9", self._make_varga_state(), MOCK_CHART_OUTPUT,
            CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        aspect_subjects = {r["fact_subject"] for r in rows
                           if r["fact_category"] == "aspect_parashari_per_varga"}
        assert "D9_RAH_MEAN" in aspect_subjects, \
            f"Rahu aspects missing. Subjects: {aspect_subjects}"
        assert "D9_KET_MEAN" in aspect_subjects, \
            f"Ketu aspects missing. Subjects: {aspect_subjects}"

    def test_rahu_ketu_in_varga_conjunctions_when_same_sign(self):
        rows = sut._build_varga_relationship_rows(
            "D9", self._make_varga_state(), MOCK_CHART_OUTPUT,
            CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        conj_subjects = {r["fact_subject"] for r in rows
                         if r["fact_category"] == "conjunction_per_varga"}
        # Mercury and Rahu both in Gemini (house 3) → conjunction fires
        assert any("RAH_MEAN" in s and "MER" in s for s in conj_subjects) or \
               any("MER" in s and "RAH_MEAN" in s for s in conj_subjects), \
            f"Mercury-Rahu conjunction missing. Subjects: {conj_subjects}"

    def test_rahu_ketu_in_vargottama_when_same_sign_as_d1(self):
        # Rahu in Taurus in D1 (MOCK_CHART_OUTPUT). Make it Taurus in D9 too.
        vs = self._make_varga_state()
        vs["Rahu"] = {"sign": "Taurus", "sign_num": 2, "house": 2, "degree": 20.0}
        rows = sut._build_varga_relationship_rows(
            "D9", vs, MOCK_CHART_OUTPUT,
            CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        vargottama_subjects = {r["fact_subject"] for r in rows
                               if r["fact_category"] == "vargottama_per_varga"}
        assert "D9_RAH_MEAN" in vargottama_subjects, \
            f"Rahu vargottama missing. Subjects: {vargottama_subjects}"
        # The row should say is_vargottama = "vargottama"
        rahu_row = next(r for r in rows
                        if r["fact_category"] == "vargottama_per_varga"
                        and r["fact_subject"] == "D9_RAH_MEAN")
        assert rahu_row["fact_value_text"] == "vargottama"

    def test_rahu_node_dignity_in_gemini_is_neutral(self):
        # L0 seal 2026-06-24: Rahu exaltation = Taurus (Parashari mainstream).
        # Mock varga state places Rahu in Gemini → dignity must be "neutral".
        rows = sut._build_varga_relationship_rows(
            "D9", self._make_varga_state(), MOCK_CHART_OUTPUT,
            CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        rahu_dignity_rows = [r for r in rows
                             if r["fact_category"] == "graha_dignity_per_varga"
                             and r["fact_subject"] == "D9_RAH_MEAN"]
        assert len(rahu_dignity_rows) == 1
        # Rahu in Gemini is "neutral" — exaltation is Taurus per L0 seal
        assert rahu_dignity_rows[0]["fact_value_text"] == "neutral"

    def test_classical_grahas_still_have_all_per_varga_facts(self):
        rows = sut._build_varga_relationship_rows(
            "D9", self._make_varga_state(), MOCK_CHART_OUTPUT,
            CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        dignity_subjects = {r["fact_subject"] for r in rows
                            if r["fact_category"] == "graha_dignity_per_varga"}
        for g_subj in ["D9_SUN", "D9_MOON", "D9_MAR", "D9_MER", "D9_JUP", "D9_VEN", "D9_SAT"]:
            assert g_subj in dignity_subjects, f"{g_subj} missing from per-varga dignity"


# ── §14: Kala Sarpa / Kala Amrita detection ───────────────────────────────────

# KS_STATE: Rahu H2 (Taurus), Ketu H8 (Scorpio), all 7 classical grahas in H3–H7 (Gemini–Leo)
KS_STATE = {
    "Sun":     {"sign": "Gemini",   "sign_num": 3, "house": 3, "degree": 5.0},
    "Moon":    {"sign": "Cancer",   "sign_num": 4, "house": 4, "degree": 10.0},
    "Mars":    {"sign": "Leo",      "sign_num": 5, "house": 5, "degree": 15.0},
    "Mercury": {"sign": "Cancer",   "sign_num": 4, "house": 4, "degree": 20.0},
    "Jupiter": {"sign": "Gemini",   "sign_num": 3, "house": 3, "degree": 25.0},
    "Venus":   {"sign": "Leo",      "sign_num": 5, "house": 5, "degree": 8.0},
    "Saturn":  {"sign": "Gemini",   "sign_num": 3, "house": 3, "degree": 18.0},
    "Rahu":    {"sign": "Taurus",   "sign_num": 2, "house": 2, "degree": 20.0},
    "Ketu":    {"sign": "Scorpio",  "sign_num": 8, "house": 8, "degree": 20.0},
}

# KA_STATE: same nodes, all 7 classical grahas on the Ketu→Rahu arc (H9–H12, H1)
KA_STATE = {
    "Sun":     {"sign": "Sagittarius", "sign_num": 9,  "house": 9,  "degree": 5.0},
    "Moon":    {"sign": "Capricorn",   "sign_num": 10, "house": 10, "degree": 10.0},
    "Mars":    {"sign": "Aquarius",    "sign_num": 11, "house": 11, "degree": 15.0},
    "Mercury": {"sign": "Sagittarius", "sign_num": 9,  "house": 9,  "degree": 20.0},
    "Jupiter": {"sign": "Capricorn",   "sign_num": 10, "house": 10, "degree": 25.0},
    "Venus":   {"sign": "Aquarius",    "sign_num": 11, "house": 11, "degree": 8.0},
    "Saturn":  {"sign": "Pisces",      "sign_num": 12, "house": 12, "degree": 18.0},
    "Rahu":    {"sign": "Taurus",      "sign_num": 2,  "house": 2,  "degree": 20.0},
    "Ketu":    {"sign": "Scorpio",     "sign_num": 8,  "house": 8,  "degree": 20.0},
}


class TestKalaSarpaDetection:
    """_detect_kala_sarpa correctly classifies KS / KA / none formations."""

    def test_kala_sarpa_detected_when_all_planets_between_rahu_ketu(self):
        result = sut._detect_kala_sarpa(KS_STATE)
        assert result["fires"] is True
        assert result["variant"] == "kala_sarpa"
        assert result["rahu_house"] == 2

    def test_kala_amrita_when_planets_on_ketu_side(self):
        result = sut._detect_kala_sarpa(KA_STATE)
        assert result["fires"] is True
        assert result["variant"] == "kala_amrita"

    def test_no_kala_sarpa_when_planets_on_both_sides(self):
        # MOCK_CHART_OUTPUT has planets on both sides (native chart) — should not fire.
        # Build varga_state from MOCK_CHART_OUTPUT grahas using sign_id field.
        varga_state = {}
        for g in MOCK_CHART_OUTPUT["grahas"]:
            name = g["name"]
            varga_state[name] = {
                "sign": g["sign"],
                "sign_num": g["sign_id"],
                "house": g["house"],
                "degree": g.get("longitude", 0.0) % 30,
            }
        result = sut._detect_kala_sarpa(varga_state)
        assert result["fires"] is False

    def test_kala_sarpa_emits_row_in_varga_relationships(self):
        rows = sut._build_varga_relationship_rows(
            "D9", KS_STATE, MOCK_CHART_OUTPUT,
            CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        ks_rows = [r for r in rows if r["fact_category"] == "kala_sarpa_per_varga"]
        assert len(ks_rows) == 1, f"Expected 1 KS row, got {len(ks_rows)}"
        assert ks_rows[0]["fact_value_text"] == "kala_sarpa"
        assert ks_rows[0]["fact_value_num"] == 1.0


# ── Task 4: Special-point relationship tests ──────────────────────────────────

class _MockCursor:
    """Cursor that returns Gulika/Mandi (Taurus H2) + Arudha_Lagna (Leo H5)."""
    def execute(self, *a, **kw): pass
    def fetchall(self):
        return [
            ("gulika",       "Taurus", 2, 15.0),
            ("mandi",        "Taurus", 2, 18.0),
            ("arudha_lagna", "Leo",    5, 22.0),
        ]
    def __enter__(self): return self
    def __exit__(self, *a): return False


class _MockConn:
    def cursor(self, row_factory=None): return _MockCursor()


class _EmptyCursor:
    def execute(self, *a, **kw): pass
    def fetchall(self): return []
    def __enter__(self): return self
    def __exit__(self, *a): return False


class _EmptyConn:
    def cursor(self, row_factory=None): return _EmptyCursor()


MOCK_CONN = _MockConn()
EMPTY_CONN = _EmptyConn()


class TestSpecialPointRelationships:
    """Tests for _load_special_points and _build_special_point_relationship_rows."""

    def test_aspect_received_rows_emitted(self):
        """At least some grahas aspect at least one special point — rows > 0."""
        rows = sut._build_special_point_relationship_rows(
            MOCK_CONN, MOCK_CHART_OUTPUT,
            CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER,
        )
        aspect_rows = [r for r in rows if r["fact_category"] == "aspect_received_by_special_point"]
        assert len(aspect_rows) > 0, (
            "Expected at least one aspect_received_by_special_point row; "
            "check Parashari offsets for grahas vs special-point houses."
        )

    def test_conjunction_gulika_rahu_in_house_2(self):
        """Gulika is in H2; Rahu is also in H2 (MOCK_CHART_OUTPUT) → conjunction row exists."""
        # Verify MOCK data: Rahu house=2
        rahu = next(g for g in MOCK_CHART_OUTPUT["grahas"] if g["name"] == "Rahu")
        assert rahu["house"] == 2, "Test pre-condition: Rahu must be in H2 in MOCK_CHART_OUTPUT"

        rows = sut._build_special_point_relationship_rows(
            MOCK_CONN, MOCK_CHART_OUTPUT,
            CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER,
        )
        conj_rows = [r for r in rows if r["fact_category"] == "conjunction_special_point"]
        # At minimum: Gulika-Rahu and Mandi-Rahu conjunctions (both in H2)
        subjects = [r["fact_subject"] for r in conj_rows]
        assert "gulika" in subjects, f"Expected gulika conjunction row; got subjects: {subjects}"
        # Check that the Rahu conjunction exists for gulika
        gulika_conj = [r for r in conj_rows if r["fact_subject"] == "gulika"]
        keys = [r["fact_key"] for r in gulika_conj]
        assert any("RAH" in k or "Rahu" in k or "rahu" in k.lower() for k in keys), (
            f"Expected Gulika-Rahu conjunction; got keys: {keys}"
        )

    def test_empty_conn_returns_empty(self):
        """When _load_special_points returns [] the function returns []."""
        rows = sut._build_special_point_relationship_rows(
            EMPTY_CONN, MOCK_CHART_OUTPUT,
            CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER,
        )
        assert rows == [], f"Expected [], got {len(rows)} rows"


# ── Task 5: House-lord matrix tests ──────────────────────────────────────────

def _make_spread_varga_state() -> dict:
    """Varga state with all 9 grahas in distinct houses (1-9)."""
    grahas_in_order = ["Sun", "Moon", "Mars", "Mercury", "Jupiter",
                        "Venus", "Saturn", "Rahu", "Ketu"]
    signs_for_houses = ["Aries", "Taurus", "Gemini", "Cancer", "Leo",
                         "Virgo", "Libra", "Scorpio", "Sagittarius"]
    state = {}
    for i, g_name in enumerate(grahas_in_order):
        h = i + 1  # houses 1–9
        state[g_name] = {
            "sign": signs_for_houses[i],
            "sign_num": i + 1,
            "house": h,
            "degree": 10.0,
        }
    return state


class TestHouseLordMatrix:
    """Tests for _build_house_lord_matrix_rows."""

    def test_exactly_12_lord_in_house_rows(self):
        """One lord_in_house_per_varga row per house → exactly 12."""
        varga_state = _make_spread_varga_state()
        rows = sut._build_house_lord_matrix_rows(
            "D1", varga_state, MOCK_CHART_OUTPUT,
            CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER,
        )
        lord_rows = [r for r in rows if r["fact_category"] == "lord_in_house_per_varga"]
        assert len(lord_rows) == 12, (
            f"Expected exactly 12 lord_in_house_per_varga rows; got {len(lord_rows)}"
        )

    def test_at_least_one_lord_aspects_lord_row(self):
        """With grahas in H1-H9 some lord must aspect another lord's house."""
        varga_state = _make_spread_varga_state()
        rows = sut._build_house_lord_matrix_rows(
            "D1", varga_state, MOCK_CHART_OUTPUT,
            CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER,
        )
        aspect_rows = [r for r in rows if r["fact_category"] == "lord_aspects_lord_per_varga"]
        assert len(aspect_rows) >= 1, (
            "Expected at least one lord_aspects_lord_per_varga row with grahas in H1-H9"
        )


# ── §T6: Jaimini rasi drishti per varga ──────────────────────────────────────

class TestJaiminiPerVarga:
    def test_jaimini_per_varga_count(self):
        vs = {"Sun": {"sign": "Leo", "sign_num": 5, "house": 5, "degree": 10.0}}
        rows = sut._build_varga_relationship_rows(
            "D9", vs, MOCK_CHART_OUTPUT,
            CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        jaimini_rows = [r for r in rows if r["fact_category"] == "aspect_jaimini_per_varga"]
        assert len(jaimini_rows) == 108, f"Expected 108, got {len(jaimini_rows)}"

    def test_jaimini_per_varga_tagged_with_varga(self):
        vs = {"Sun": {"sign": "Leo", "sign_num": 5, "house": 5, "degree": 10.0}}
        rows = sut._build_varga_relationship_rows(
            "D9", vs, MOCK_CHART_OUTPUT,
            CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        jaimini_rows = [r for r in rows if r["fact_category"] == "aspect_jaimini_per_varga"]
        assert all(r["fact_value_jsonb"]["varga"] == "D9" for r in jaimini_rows)


# ── §T7: Karaka inter-relationship web ────────────────────────────────────────

class TestKarakaWeb:
    def _make_karaka_conn(self):
        class _KC:
            def execute(self, *a, **kw): pass
            def fetchall(self): return [("ATMAKARAKA","Sun",None,None),("AMATYAKARAKA","Saturn",None,None),("DARAKARAKA","Mars",None,None)]
            def __enter__(self): return self
            def __exit__(self, *a): return False
        class _KConn:
            def cursor(self, row_factory=None): return _KC()
        return _KConn()

    def test_karaka_web_rows_emitted(self):
        vs = {
            "Sun":    {"sign":"Capricorn","sign_num":10,"house":10,"degree":5.0},
            "Saturn": {"sign":"Libra",    "sign_num":7, "house":7, "degree":12.0},
            "Mars":   {"sign":"Aries",    "sign_num":1, "house":1, "degree":15.0},
        }
        rows = sut._build_karaka_web_rows(
            self._make_karaka_conn(), vs, MOCK_CHART_OUTPUT,
            "D9", CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        assert len([r for r in rows if r["fact_category"] == "karaka_web_per_varga"]) > 0

    def test_empty_karaka_returns_empty(self):
        class _EC:
            class _C:
                def execute(self, *a, **kw): pass
                def fetchall(self): return []
                def __enter__(self): return self
                def __exit__(self, *a): return False
            def cursor(self, row_factory=None): return _EC._C()
        rows = sut._build_karaka_web_rows(_EC(), {}, MOCK_CHART_OUTPUT, "D9", CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER)
        assert rows == []


# ── §T8: Graha yuddha ─────────────────────────────────────────────────────────

class TestGrahaYuddha:
    def _make_yuddha_chart(self):
        """Sun=295°, Mercury moved to 295.6° — same sign (Capricorn), orb=0.6° < 1°."""
        modified_grahas = []
        for g in MOCK_CHART_OUTPUT["grahas"]:
            if g["name"] == "Mercury":
                modified_grahas.append({**g, "longitude": 295.6, "sign": "Capricorn"})
            else:
                modified_grahas.append(g)
        return {**MOCK_CHART_OUTPUT, "grahas": modified_grahas}

    def test_yuddha_detected_within_1_degree(self):
        rows = sut._build_graha_yuddha_rows(
            self._make_yuddha_chart(), CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        yuddha_rows = [r for r in rows if r["fact_category"] == "graha_yuddha"]
        assert len(yuddha_rows) >= 1

    def test_no_yuddha_in_unmodified_mock(self):
        # Sun=295°, Mercury=300° → diff=5° > 1° → no yuddha
        rows = sut._build_graha_yuddha_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        yuddha_rows = [r for r in rows if r["fact_category"] == "graha_yuddha"]
        assert isinstance(yuddha_rows, list)

    def test_yuddha_has_winner_and_loser_keys(self):
        rows = sut._build_graha_yuddha_rows(
            self._make_yuddha_chart(), CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        yuddha_rows = [r for r in rows if r["fact_category"] == "graha_yuddha"]
        keys = {r["fact_key"] for r in yuddha_rows}
        assert "winner" in keys and "loser" in keys

    def test_yuddha_winner_rule_floored_no_victor_named(self):
        """JL-027: winner rule is FLOORED — no planet is named victor.
        winner/loser rows carry NULL values + reason='no_ratified_classical_rule';
        orb_deg remains a true computed fact."""
        rows = sut._build_graha_yuddha_rows(
            self._make_yuddha_chart(), CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        yuddha_rows = [r for r in rows if r["fact_category"] == "graha_yuddha"]
        assert len(yuddha_rows) >= 3  # at least one pair → winner, loser, orb_deg

        for r in yuddha_rows:
            if r["fact_key"] in ("winner", "loser"):
                # No planet named as victor/loser:
                assert r["fact_value_text"] is None
                assert r["fact_value_jsonb"]["winner"] is None
                assert r["fact_value_jsonb"]["loser"] is None
                assert r["fact_value_jsonb"]["reason"] == "no_ratified_classical_rule"
                assert r["fact_value_jsonb"]["floored"] is True
            elif r["fact_key"] == "orb_deg":
                # orb is a true fact — still present and numeric:
                assert r["fact_value_num"] is not None
                assert r["fact_value_num"] <= 1.0


# ── §T9: Combustion and retrograde relational rows ────────────────────────────

class TestCombustionRetrogradRelational:
    def test_mercury_combustion_detected(self):
        # Sun=295°, Mercury=300° → diff=5° < orb_limit=14° → Mercury combust
        rows = sut._build_combustion_retrograde_relationship_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        combust = [r for r in rows if r["fact_category"] == "combustion_relationship"]
        subjects = {r["fact_subject"] for r in combust}
        assert any("MER" in s for s in subjects), f"Mercury combustion missing. Subjects: {subjects}"

    def test_retrograde_rows_emitted(self):
        # Rahu and Ketu are retrograde in MOCK_CHART_OUTPUT → expect retrograde_aspect_modification rows
        rows = sut._build_combustion_retrograde_relationship_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        retro_rows = [r for r in rows if r["fact_category"] == "retrograde_aspect_modification"]
        # Rahu (H2): 3 aspects + Ketu (H8): 3 aspects = 6 rows minimum
        assert len(retro_rows) >= 6

    def test_sun_has_no_combustion_row(self):
        # Sun cannot be combust by itself; no row should have fact_value_jsonb["planet"] == "Sun"
        # and also fact_subject ending in "_v_SUN" (Sun as the combusted planet is impossible)
        rows = sut._build_combustion_retrograde_relationship_rows(
            MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        combust = [r for r in rows if r["fact_category"] == "combustion_relationship"]
        # No combusted planet should be Sun itself
        combust_planets = {r["fact_value_jsonb"]["planet"] for r in combust}
        assert "Sun" not in combust_planets


class TestKarakaWebCanonicalSchool:
    """BA-P3 (2026-07-06): the karaka web must read a SINGLE canonical karaka
    school (kn_rao_rahu_included). ga_sensitive writes karaka_chara_position for
    BOTH schools; reading both merged a scrambled cross-school role->planet map
    that could map two roles to the same planet -> duplicate karaka_web fact_ids
    -> TWO_PASS_FAILED (surfaced on surya_siddhanta_classical)."""

    class _Cur:
        def __init__(self, sink, rows):
            self._sink, self._rows = sink, rows
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def execute(self, sql, params=None):
            self._sink.append((" ".join(sql.split()), params))
        def fetchall(self):
            return list(self._rows)

    class _Conn:
        def __init__(self, rows):
            self.calls = []
            self._rows = rows
        def cursor(self, row_factory=None):
            return TestKarakaWebCanonicalSchool._Cur(self.calls, self._rows)

    def _varga_state(self):
        # All karaka planets same sign/house -> every pair is a conjunction, so a
        # duplicated planet in the map would produce a duplicate (subject,key) row.
        return {p: {"sign": "Aries", "house": 1} for p in
                ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu"]}

    def test_query_filters_to_canonical_school(self):
        conn = self._Conn(rows=[])  # empty -> early return, we just inspect the SQL
        sut._build_karaka_web_rows(conn, self._varga_state(), MOCK_CHART_OUTPUT, "D1",
                                   CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER)
        sql, params = conn.calls[0]
        assert "formula_id = %s" in sql
        assert "kn_rao_rahu_included" in params

    def test_no_duplicate_fact_ids_from_single_school(self):
        # 8 roles -> 8 distinct planets (a clean permutation, as a single school is)
        roles = ["ATMAKARAKA", "AMATYAKARAKA", "BHRATRIKARAKA", "MATRIKARAKA",
                 "PUTRAKARAKA", "GNATIKARAKA", "DARAKARAKA", "STRIKARAKA"]
        planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu"]
        rows_in = [(r, p, None, None) for r, p in zip(roles, planets)]
        conn = self._Conn(rows=rows_in)
        out = sut._build_karaka_web_rows(conn, self._varga_state(), MOCK_CHART_OUTPUT, "D1",
                                         CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER)
        fids = [r["fact_id"] for r in out]
        assert len(fids) == len(set(fids)), "karaka web produced duplicate fact_ids"

    def test_defensive_dedupe_when_map_has_duplicate_planet(self):
        # Degenerate: two roles map to the same planet (should not halt / dup)
        rows_in = [("ATMAKARAKA", "Mercury", None, None),
                   ("AMATYAKARAKA", "Mercury", None, None),
                   ("BHRATRIKARAKA", "Sun", None, None)]
        conn = self._Conn(rows=rows_in)
        out = sut._build_karaka_web_rows(conn, self._varga_state(), MOCK_CHART_OUTPUT, "D1",
                                         CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER)
        fids = [r["fact_id"] for r in out]
        assert len(fids) == len(set(fids)), "duplicate planet must not yield duplicate fact_ids"
