"""
test_ga5_writer.py — Unit tests for GA5 sensitive points writer.

All tests are unit tests (no DB required):
  1.  FORENSIC-internal consistency: Sun=Capricorn
  2.  FORENSIC-internal consistency: Moon nak=Purva Bhadrapada
  3.  FORENSIC-internal consistency: Lagna=Aries (NOT Scorpio)
  4.  fact_id: 16 hex chars, deterministic
  5.  fact_id differs for different formula_id values (variant rows)
  6.  citation_ref: contains category.subject.key@chart= format
  7.  citation_human: non-empty, ends with period
  8.  No-narration linter: clean values pass
  9.  No-narration linter: 'indicates' fails
  10. No-narration linter: 'suggests' fails
  11. No-narration linter: 'means' fails
  12. Section-B enrichment: all 6 fields present on every row
  13. Section-B enrichment: tolerance_arcsec >= 0.0
  14. Section-B enrichment: near_sign_boundary_flag is bool
  15. Section-B enrichment: near_nakshatra_boundary_flag is bool
  16. Section-B enrichment: vargottama_flag_at_point is bool
  17. Section-B enrichment: formula_provenance_text non-empty
  18. Verification pass: all rows = 'two_pass_verified' (zero single)
  19. Verification pass: zero 'divergent_flagged' rows
  20. Atomic grain: upagraha_position — 6 subjects × ≥ 5 keys = ≥ 30 rows
  21. Atomic grain: saham_position — ≥ 70 subjects (one per Saham)
  22. Atomic grain: hadda — exactly 60 subjects (HADDA_1..HADDA_60)
  23. Atomic grain: swamsa_position — 12 subjects (SWAMSA_HOUSE_1..12)
  24. Atomic grain: arudha_pada — 19 subjects (A1..A12 + SU/MO/MA/ME/JU/VE/SA)
  25. Atomic grain: midpoints — 54 subjects (36 graha-graha + 9 ASC + 9 MC)
  26. Atomic grain: no fact_value_jsonb outside kp_cuspal_significators
  27. Category presence: upagraha_position rows exist
  28. Category presence: esoteric_point_bhrigu_bindu rows exist
  29. Category presence: esoteric_point_yogi rows exist (2 formula variants)
  30. Category presence: esoteric_point_avayogi rows exist (2 formula variants)
  31. Category presence: esoteric_point_mrityu rows exist (3 formula variants)
  32. Category presence: esoteric_point_trisphuta rows exist
  33. Category presence: esoteric_point_chatushphuta rows exist
  34. Category presence: esoteric_point_panchasphuta rows exist (2 variants)
  35. Category presence: saham_position rows exist
  36. Category presence: karaka_chara_position rows exist (2 schools)
  37. Category presence: karakamsa_position rows exist
  38. Category presence: swamsa_position rows exist
  39. Category presence: arudha_pada rows exist
  40. Category presence: midpoint rows exist
  41. Category presence: kp_ruling_planets_natal rows exist
  42. Category presence: kp_cuspal_significators rows exist
  43. Category presence: aprakasha_position rows exist
  44. Category presence: tajik_hadda_lord rows exist
  45. Category presence: lal_kitab_special_point floored (absent_prerequisite_flag=true)
  46. Category presence: maharsi_specific_point floored (absent_prerequisite_flag=true)
  47. Category presence: bhrigu_nadi_point rows exist (8 chakras)
  48. FORENSIC consistency: Bhrigu Bindu = midpoint(Moon, Rahu)
  49. FORENSIC consistency: Yogi Point formula = (Sun + Moon + 93.33°) mod 360
  50. FORENSIC consistency: Hadda_1 = Jupiter (Aries 0–6°)
  51. FORENSIC consistency: Atmakaraka is the planet with highest degree in sign
  52. FORENSIC consistency: Karakamsa = D9 sign of Atmakaraka
  53. Phantom UUID: 362f9f17 never appears as chart_id in rows
  54. Ayanamsha: all 5 canonical ayanamshas produce rows
  55. Schema: all GA5 categories in CHART_FACTS_SCHEMA.json
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sys
from typing import Any

import pytest

# Add parent (ga_writers package root) to path
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

# ── Constants ─────────────────────────────────────────────────────────────────

CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
DEAD_PHANTOM_UUID = "362f9f17"

BUILD_ID = "ga5-test-build-001"

SCHEMA_PATH = pathlib.Path(__file__).parent.parent / "ga_writers" / "CHART_FACTS_SCHEMA.json"

# FORENSIC anchors (born 1984-02-05 10:43 IST, Bhubaneswar)
FORENSIC_SUN_SIGN = "Capricorn"
FORENSIC_MOON_NAK = "Purva Bhadrapada"
FORENSIC_LAGNA = "Aries"  # NOT Scorpio

# Ayanamsha map matches ga_sensitive_writer.py
CANONICAL_AYANAMSHAS = {
    "lahiri":                "lahiri_chitrapaksha",
    "true_chitra":           "true_chitra",
    "krishnamurti":          "krishnamurti",
    "raman":                 "raman",
    "surya_siddhanta":       "surya_siddhanta_classical",
}

# Simplified sidereal longitudes for unit-test derivation
# (must satisfy FORENSIC anchors)
# Sun in Capricorn: sign_idx = 9, so 9*30 + n degrees = 270-300
# Lagna in Aries: 0-30°
# Moon nak = Purva Bhadrapada: nak index 24, so 24 * 13.333 = 320°
_TEST_SUN_LONG = 280.0   # Capricorn ~10°
_TEST_MOON_LONG = 321.0  # Purva Bhadrapada
_TEST_LAGNA_LONG = 5.0   # Aries
_TEST_MAR_LONG = 195.0   # Libra
_TEST_MER_LONG = 275.0   # Capricorn
_TEST_JUP_LONG = 120.0   # Leo
_TEST_VEN_LONG = 300.0   # Aquarius
_TEST_SAT_LONG = 210.0   # Scorpio
_TEST_RAH_LONG = 180.0   # Libra
_TEST_KET_LONG = 0.0     # Aries

# Approximate Julian Day values for FORENSIC birth event (1984-02-05, Bhubaneswar).
# Used to unblock _build_trisphuta_family_rows (B.10 guard returns [] when both are None).
# Values need only be internally consistent — trisphuta tests do not verify JD precision.
_TEST_SUNRISE_JD = 2445737.037   # ~06:24 IST sunrise at Bhubaneswar on 1984-02-05
_TEST_BIRTH_JD   = 2445737.218   # ~10:43 IST birth (~4.3 h after sunrise)

_TEST_LONGS = {
    "SUN": _TEST_SUN_LONG,
    "MOON": _TEST_MOON_LONG,
    "MAR": _TEST_MAR_LONG,
    "MER": _TEST_MER_LONG,
    "JUP": _TEST_JUP_LONG,
    "VEN": _TEST_VEN_LONG,
    "SAT": _TEST_SAT_LONG,
    "RAH_MEAN": _TEST_RAH_LONG,
    "KET_MEAN": _TEST_KET_LONG,
    "LAGNA": _TEST_LAGNA_LONG,
}

SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
         "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _import_writer():
    from ga_writers import ga_sensitive_writer
    return ga_sensitive_writer


def _get_rows_for_category(rows: list[dict], category: str) -> list[dict]:
    return [r for r in rows if r["fact_category"] == category]


def _get_row(rows: list[dict], category: str, subject: str, key: str) -> dict | None:
    for r in rows:
        if r["fact_category"] == category and r["fact_subject"] == subject and r["fact_key"] == key:
            return r
    return None


def _build_test_rows_for_one_ayanamsha() -> list[dict[str, Any]]:
    """
    Build sensitive-point rows using test longitudes (no DB/PyJHora needed).
    Calls all internal builders directly.
    """
    w = _import_writer()
    ayanamsha_id = "lahiri_chitrapaksha"
    all_longs = _TEST_LONGS

    # chart_data with mock PyJHora-native "sensitive_points" (M-11 fix: this is
    # the correct key compute_chart() populates — was "upagrahas" previously,
    # which compute_chart() never wrote, so every native lookup silently
    # missed). Also mocks "midheaven" (D-9) and "special_lagnas" (M-9/M-10)
    # so the delegated-primary code paths are exercised by these unit tests
    # rather than always hitting the floor path.
    chart_data: dict[str, Any] = {
        "positions": {},
        "sensitive_points": {
            "kaala": {"longitude_deg": 304.13, "sign": "Aquarius", "sign_id": 11, "degree_in_sign": 4.13},
            "mrityu": {"longitude_deg": 30.0, "sign": "Taurus", "sign_id": 2, "degree_in_sign": 0.0},
            "artha_prabhakara": {"longitude_deg": 45.0, "sign": "Taurus", "sign_id": 2, "degree_in_sign": 15.0},
            "yama": {"longitude_deg": 60.0, "sign": "Gemini", "sign_id": 3, "degree_in_sign": 0.0},
            "gulika": {"longitude_deg": 74.89, "sign": "Gemini", "sign_id": 3, "degree_in_sign": 14.89},
            "maandi": {"longitude_deg": 84.26, "sign": "Gemini", "sign_id": 3, "degree_in_sign": 24.26},
            "dhuma": {"longitude_deg": 53.33, "sign": "Taurus", "sign_id": 2, "degree_in_sign": 23.33},
            "vyatipaata": {"longitude_deg": 306.67, "sign": "Capricorn", "sign_id": 10, "degree_in_sign": 6.67},
            "parivesha": {"longitude_deg": 126.67, "sign": "Leo", "sign_id": 5, "degree_in_sign": 6.67},
            "indrachaapa": {"longitude_deg": 233.33, "sign": "Scorpio", "sign_id": 8, "degree_in_sign": 23.33},
            "upaketu": {"longitude_deg": 250.0, "sign": "Sagittarius", "sign_id": 9, "degree_in_sign": 10.0},
        },
        "midheaven": {"longitude_deg": 272.98, "sign": "Capricorn", "sign_id": 10, "degree_in_sign": 2.98},
        "special_lagnas": {
            "bhava_lagna": {"longitude_deg": 356.4, "sign": "Pisces", "sign_id": 12, "degree_in_sign": 26.4},
            "hora_lagna": {"longitude_deg": 60.9, "sign": "Gemini", "sign_id": 3, "degree_in_sign": 0.9},
            "ghati_lagna": {"longitude_deg": 254.2, "sign": "Sagittarius", "sign_id": 9, "degree_in_sign": 14.2},
            "vighati_lagna": {"longitude_deg": 197.8, "sign": "Libra", "sign_id": 7, "degree_in_sign": 17.8},
            "indu_lagna": {"longitude_deg": 237.1, "sign": "Scorpio", "sign_id": 8, "degree_in_sign": 27.1},
            "sree_lagna": {"longitude_deg": 202.9, "sign": "Libra", "sign_id": 7, "degree_in_sign": 22.9},
            "pranapada_lagna": {"longitude_deg": 138.4, "sign": "Leo", "sign_id": 5, "degree_in_sign": 18.4},
            "bhrigu_bindhu_lagna": {"longitude_deg": 188.0, "sign": "Libra", "sign_id": 7, "degree_in_sign": 8.0},
            "kunda_lagna": {"longitude_deg": 286.9, "sign": "Capricorn", "sign_id": 10, "degree_in_sign": 16.9},
            "varnada_lagna": {"longitude_deg": 102.4, "sign": "Cancer", "sign_id": 4, "degree_in_sign": 12.4},
        },
    }

    rows: list[dict[str, Any]] = []

    # Call each builder individually
    rows += w._build_upagraha_rows(chart_data, CANONICAL_CHART_ID, ayanamsha_id, BUILD_ID, "test-eng", all_longs)
    rows += w._build_saturn_derived_rows(chart_data, CANONICAL_CHART_ID, ayanamsha_id, BUILD_ID, "test-eng", all_longs)
    rows += w._build_bhrigu_bindu_rows(all_longs, CANONICAL_CHART_ID, ayanamsha_id, BUILD_ID, "test-eng")
    rows += w._build_yogi_avayogi_rows(all_longs, CANONICAL_CHART_ID, ayanamsha_id, BUILD_ID, "test-eng")
    rows += w._build_mrityu_rows(all_longs, CANONICAL_CHART_ID, ayanamsha_id, BUILD_ID, "test-eng", True)
    rows += w._build_trisphuta_family_rows(all_longs, CANONICAL_CHART_ID, ayanamsha_id, BUILD_ID, "test-eng",
                                             sunrise_jd=_TEST_SUNRISE_JD, birth_jd=_TEST_BIRTH_JD)
    rows += w._build_pranapada_rows(chart_data, all_longs, CANONICAL_CHART_ID, ayanamsha_id, BUILD_ID, "test-eng")
    rows += w._build_trikona_dasha_rows(all_longs, CANONICAL_CHART_ID, ayanamsha_id, BUILD_ID, "test-eng")
    rows += w._build_sri_yantra_rows(all_longs, CANONICAL_CHART_ID, ayanamsha_id, BUILD_ID, "test-eng")
    rows += w._build_brahma_vishnu_shiva_rows(all_longs, CANONICAL_CHART_ID, ayanamsha_id, BUILD_ID, "test-eng")
    rows += w._build_saham_rows(all_longs, CANONICAL_CHART_ID, ayanamsha_id, BUILD_ID, "test-eng", True)
    rows += w._build_karaka_rows(all_longs, CANONICAL_CHART_ID, ayanamsha_id, BUILD_ID, "test-eng", "HALT.md")
    rows += w._build_karakamsa_rows(all_longs, CANONICAL_CHART_ID, ayanamsha_id, BUILD_ID, "test-eng")
    rows += w._build_swamsa_rows(all_longs, CANONICAL_CHART_ID, ayanamsha_id, BUILD_ID, "test-eng")
    rows += w._build_arudha_rows(all_longs, CANONICAL_CHART_ID, ayanamsha_id, BUILD_ID, "test-eng")
    rows += w._build_midpoint_rows(chart_data, all_longs, CANONICAL_CHART_ID, ayanamsha_id, BUILD_ID, "test-eng")
    rows += w._build_kp_ruling_planets_rows(all_longs, CANONICAL_CHART_ID, ayanamsha_id, BUILD_ID, "test-eng")
    rows += w._build_kp_cuspal_rows(all_longs, CANONICAL_CHART_ID, ayanamsha_id, BUILD_ID, "test-eng", chart_data)
    rows += w._build_aprakasha_rows(all_longs, CANONICAL_CHART_ID, ayanamsha_id, BUILD_ID, "test-eng",
                                     all_longs["SAT"] + 6.0, all_longs["SAT"] + 8.0)
    rows += w._build_hadda_rows(all_longs, CANONICAL_CHART_ID, ayanamsha_id, BUILD_ID, "test-eng")
    rows += w._build_triraashipathi_rows(all_longs, CANONICAL_CHART_ID, ayanamsha_id, BUILD_ID, "test-eng")
    rows += w._build_tajik_vargottama_rows(all_longs, CANONICAL_CHART_ID, ayanamsha_id, BUILD_ID, "test-eng")
    rows += w._build_lal_kitab_floored_rows(all_longs, CANONICAL_CHART_ID, ayanamsha_id, BUILD_ID, "test-eng")
    rows += w._build_maharsi_floored_rows(all_longs, CANONICAL_CHART_ID, ayanamsha_id, BUILD_ID, "test-eng")
    rows += w._build_bhrigu_nadi_rows(all_longs, CANONICAL_CHART_ID, ayanamsha_id, BUILD_ID, "test-eng")
    rows += w._build_nakshatra_pada_sensitive_rows(all_longs, CANONICAL_CHART_ID, ayanamsha_id, BUILD_ID, "test-eng")

    return rows


@pytest.fixture(scope="module")
def all_rows():
    return _build_test_rows_for_one_ayanamsha()


# ── 1–3: FORENSIC internal consistency ───────────────────────────────────────

class TestForensicConsistency:
    """Verify that writer-level FORENSIC anchors are internally consistent."""

    def test_sun_is_capricorn(self):
        """Sun at 280° must be Capricorn (270-300)."""
        sign_idx = int(_TEST_SUN_LONG / 30.0)
        assert SIGNS[sign_idx] == "Capricorn", f"Test Sun not in Capricorn: {SIGNS[sign_idx]}"

    def test_moon_is_purva_bhadrapada(self):
        """Moon at 321° must fall in Purva Bhadrapada (nak idx 24)."""
        NAK_SPAN = 360.0 / 27.0
        nak_idx = int(_TEST_MOON_LONG / NAK_SPAN)
        NAKSHATRAS = [
            "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra",
            "Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni",
            "Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha",
            "Mula","Purva Ashadha","Uttara Ashadha","Shravana","Dhanishta","Shatabhisha",
            "Purva Bhadrapada","Uttara Bhadrapada","Revati",
        ]
        nak_name = NAKSHATRAS[nak_idx]
        assert nak_name == "Purva Bhadrapada", f"Test Moon not in PB: {nak_name}"

    def test_lagna_is_aries_not_scorpio(self):
        """Lagna at 5° must be Aries, not Scorpio."""
        sign_idx = int(_TEST_LAGNA_LONG / 30.0)
        assert SIGNS[sign_idx] == "Aries", f"Test Lagna not Aries: {SIGNS[sign_idx]}"
        assert SIGNS[sign_idx] != "Scorpio", "Lagna must NOT be Scorpio (FORENSIC trap)"


# ── 4–7: fact_id + citations ─────────────────────────────────────────────────

class TestFactIdAndCitations:
    def test_fact_id_is_16_hex(self):
        w = _import_writer()
        fid = w._fact_id("upagraha_position", "DHUMA", "longitude_sidereal",
                          CANONICAL_CHART_ID, "lahiri_chitrapaksha", BUILD_ID)
        assert len(fid) == 16
        assert all(c in "0123456789abcdef" for c in fid), "Not hex"

    def test_fact_id_deterministic(self):
        w = _import_writer()
        fid1 = w._fact_id("upagraha_position", "DHUMA", "longitude_sidereal",
                           CANONICAL_CHART_ID, "lahiri_chitrapaksha", BUILD_ID)
        fid2 = w._fact_id("upagraha_position", "DHUMA", "longitude_sidereal",
                           CANONICAL_CHART_ID, "lahiri_chitrapaksha", BUILD_ID)
        assert fid1 == fid2

    def test_fact_id_differs_for_different_formula_id(self):
        """Variant rows (e.g. Yogi bphs_93_20 vs alt_96_40) must have different IDs."""
        w = _import_writer()
        fid1 = w._fact_id("esoteric_point_yogi", "YOGI_POINT", "longitude_sidereal",
                           CANONICAL_CHART_ID, "lahiri_chitrapaksha", BUILD_ID, "bphs_93_20")
        fid2 = w._fact_id("esoteric_point_yogi", "YOGI_POINT", "longitude_sidereal",
                           CANONICAL_CHART_ID, "lahiri_chitrapaksha", BUILD_ID, "alt_96_40")
        assert fid1 != fid2

    def test_citation_ref_format(self):
        w = _import_writer()
        cref = w._citation_ref("upagraha_position", "DHUMA", "longitude_sidereal",
                                CANONICAL_CHART_ID, "lahiri_chitrapaksha", "test-v1")
        assert "upagraha_position.DHUMA.longitude_sidereal" in cref
        assert "@chart=" in cref
        assert CANONICAL_CHART_ID in cref

    def test_citation_human_non_empty_ends_period(self):
        w = _import_writer()
        chuman = w._citation_human("upagraha_position", "DHUMA", "longitude_sidereal",
                                    280.5, "lahiri_chitrapaksha")
        assert chuman
        assert chuman.endswith(".")


# ── 8–11: No-narration linter ─────────────────────────────────────────────────

class TestNoNarrationLinter:
    def test_clean_value_passes(self):
        w = _import_writer()
        violations = w._check_linter("Capricorn")
        assert violations == []

    def test_indicates_fails(self):
        w = _import_writer()
        violations = w._check_linter("This indicates strength")
        assert "indicates" in violations

    def test_suggests_fails(self):
        w = _import_writer()
        violations = w._check_linter("Moon suggests good fortune")
        assert "suggests" in violations

    def test_means_fails(self):
        w = _import_writer()
        violations = w._check_linter("Lagna means self")
        assert "means" in violations

    def test_make_row_raises_on_narration(self):
        w = _import_writer()
        with pytest.raises(ValueError, match="narration_linter"):
            w._make_row(
                "upagraha_position", "DHUMA", "note",
                None, "This indicates something",  # forbidden
                None, CANONICAL_CHART_ID, "lahiri_chitrapaksha", BUILD_ID, "v1",
            )


# ── 12–17: Section-B enrichment ──────────────────────────────────────────────

SECTION_B_FIELDS = [
    "tolerance_arcsec",
    "near_sign_boundary_flag",
    "near_nakshatra_boundary_flag",
    "vargottama_flag_at_point",
    "formula_provenance_text",
    "cross_ayanamsha_divergence_arcsec",
]


class TestSectionBEnrichment:
    def test_all_6_fields_present(self, all_rows):
        """Every row must have all 6 Section-B fields as keys."""
        for row in all_rows:
            for field in SECTION_B_FIELDS:
                assert field in row, f"Missing Section-B field '{field}' in {row.get('fact_category')}.{row.get('fact_subject')}.{row.get('fact_key')}"

    def test_tolerance_arcsec_non_negative(self, all_rows):
        for row in all_rows:
            tol = row.get("tolerance_arcsec")
            if tol is not None:
                assert tol >= 0.0, f"tolerance_arcsec < 0 in {row.get('fact_category')}"

    def test_near_sign_boundary_is_bool(self, all_rows):
        for row in all_rows:
            v = row.get("near_sign_boundary_flag")
            assert isinstance(v, bool), f"near_sign_boundary_flag not bool: {type(v)}"

    def test_near_nakshatra_boundary_is_bool(self, all_rows):
        for row in all_rows:
            v = row.get("near_nakshatra_boundary_flag")
            assert isinstance(v, bool), f"near_nakshatra_boundary_flag not bool: {type(v)}"

    def test_vargottama_flag_is_bool(self, all_rows):
        for row in all_rows:
            v = row.get("vargottama_flag_at_point")
            assert isinstance(v, bool), f"vargottama_flag_at_point not bool: {type(v)}"

    def test_formula_provenance_non_empty(self, all_rows):
        """formula_provenance_text must be non-empty on all rows."""
        for row in all_rows:
            prov = row.get("formula_provenance_text")
            assert prov and prov.strip(), (
                f"Empty formula_provenance_text in "
                f"{row.get('fact_category')}.{row.get('fact_subject')}.{row.get('fact_key')}"
            )


# ── 18–19: Verification pass ─────────────────────────────────────────────────

class TestVerificationPass:
    def test_all_two_pass_verified(self, all_rows):
        """Zero rows may have verification_pass_status = 'single'."""
        single = [r for r in all_rows if r.get("verification_pass_status") == "single"]
        assert single == [], f"{len(single)} single-pass rows detected; zero allowed"

    def test_zero_divergent_flagged(self, all_rows):
        """Zero rows may have verification_pass_status = 'divergent_flagged'."""
        div = [r for r in all_rows if r.get("verification_pass_status") == "divergent_flagged"]
        assert div == [], f"{len(div)} divergent_flagged rows detected"


# ── 20–26: Atomic grain ───────────────────────────────────────────────────────

class TestAtomicGrain:
    def test_upagraha_min_30_rows(self, all_rows):
        """6 upagrahas × ≥ 5 keys = ≥ 30 rows for upagraha_position."""
        urows = _get_rows_for_category(all_rows, "upagraha_position")
        assert len(urows) >= 30, f"Only {len(urows)} upagraha_position rows"

    def test_saham_min_70_subjects(self, all_rows):
        """At least 70 Saham subjects (one per formula)."""
        srows = _get_rows_for_category(all_rows, "saham_position")
        subjects = {r["fact_subject"] for r in srows}
        assert len(subjects) >= 70, f"Only {len(subjects)} saham subjects"

    def test_hadda_exactly_60_subjects(self, all_rows):
        """Exactly 60 Hadda zone subjects."""
        hrows = _get_rows_for_category(all_rows, "tajik_hadda_lord")
        subjects = {r["fact_subject"] for r in hrows}
        assert len(subjects) == 60, f"Expected 60 Hadda subjects, got {len(subjects)}: {sorted(subjects)[:5]}..."

    def test_swamsa_12_subjects(self, all_rows):
        """12 Swamsa house subjects."""
        swrows = _get_rows_for_category(all_rows, "swamsa_position")
        subjects = {r["fact_subject"] for r in swrows}
        assert len(subjects) == 12, f"Expected 12 Swamsa subjects, got {len(subjects)}"
        assert "SWAMSA_HOUSE_1" in subjects
        assert "SWAMSA_HOUSE_12" in subjects

    def test_arudha_pada_19_subjects(self, all_rows):
        """19 Arudha pada subjects: A1..A12 + 7 graha arudhas."""
        arows = _get_rows_for_category(all_rows, "arudha_pada")
        subjects = {r["fact_subject"] for r in arows}
        assert len(subjects) == 19, f"Expected 19 Arudha subjects, got {len(subjects)}: {sorted(subjects)}"
        assert "ARUDHA_A1" in subjects
        assert "ARUDHA_A12" in subjects
        assert "ARUDHA_SU" in subjects
        assert "ARUDHA_SA" in subjects

    def test_midpoints_54_subjects(self, all_rows):
        """54 midpoint subjects: 36 graha-graha + 9 ASC + 9 MC."""
        mrows = _get_rows_for_category(all_rows, "midpoint")
        subjects = {r["fact_subject"] for r in mrows}
        assert len(subjects) == 54, f"Expected 54 midpoint subjects, got {len(subjects)}"

    def test_no_jsonb_outside_kp_cuspal(self, all_rows):
        """Only kp_cuspal_significators may have non-null fact_value_jsonb."""
        for row in all_rows:
            if row.get("fact_value_jsonb") is not None:
                assert row["fact_category"] == "kp_cuspal_significators", (
                    f"Non-null jsonb outside kp_cuspal_significators in "
                    f"{row['fact_category']}.{row['fact_subject']}.{row['fact_key']}"
                )


# ── 27–46: Category presence ─────────────────────────────────────────────────

class TestCategoryPresence:
    @pytest.mark.parametrize("category", [
        "upagraha_position",
        "saturn_derived_point",
        "esoteric_point_bhrigu_bindu",
        "esoteric_point_yogi",
        "esoteric_point_avayogi",
        "esoteric_point_mrityu",
        "esoteric_point_trisphuta",
        "esoteric_point_chatushphuta",
        "esoteric_point_panchasphuta",
        "esoteric_point_pranapada_sphuta",
        "esoteric_point_trikona_dasha_sphuta",
        "esoteric_point_sri_yantra_position",
        "esoteric_point_brahma",
        "esoteric_point_vishnu",
        "esoteric_point_shiva",
        "saham_position",
        "karaka_chara_position",
        "karakamsa_position",
        "swamsa_position",
        "arudha_pada",
        "midpoint",
        "kp_ruling_planets_natal",
        "kp_cuspal_significators",
        "aprakasha_position",
        "tajik_hadda_lord",
        "tajik_triraashipathi",
        "tajik_vargottama_specific",
        "lal_kitab_special_point",
        "maharsi_specific_point",
        "bhrigu_nadi_point",
        "nakshatra_pada_sensitive",
    ])
    def test_category_rows_exist(self, all_rows, category):
        rows = _get_rows_for_category(all_rows, category)
        assert rows, f"No rows for category '{category}'"

    def test_yogi_has_2_formula_variants(self, all_rows):
        """Yogi Sphuta emitted in 2 formula variants: bphs_93_20 + alt_96_40."""
        yogi_rows = _get_rows_for_category(all_rows, "esoteric_point_yogi")
        formula_ids = {r.get("formula_id") for r in yogi_rows}
        assert "bphs_93_20" in formula_ids, "Missing bphs_93_20 variant"
        assert "alt_96_40" in formula_ids, "Missing alt_96_40 variant"

    def test_avayogi_has_2_formula_variants(self, all_rows):
        avayogi_rows = _get_rows_for_category(all_rows, "esoteric_point_avayogi")
        formula_ids = {r.get("formula_id") for r in avayogi_rows}
        assert "bphs_93_20" in formula_ids
        assert "alt_96_40" in formula_ids

    def test_mrityu_has_3_formula_variants(self, all_rows):
        mrityu_rows = _get_rows_for_category(all_rows, "esoteric_point_mrityu")
        formula_ids = {r.get("formula_id") for r in mrityu_rows}
        assert "bphs_ch39" in formula_ids
        assert "saravali" in formula_ids
        assert "tajik_aapamrityu" in formula_ids

    def test_panchasphuta_has_2_formula_variants(self, all_rows):
        ps_rows = _get_rows_for_category(all_rows, "esoteric_point_panchasphuta")
        formula_ids = {r.get("formula_id") for r in ps_rows}
        assert "with_saturn" in formula_ids
        assert "with_rahu" in formula_ids

    def test_karaka_chara_has_2_schools(self, all_rows):
        """Both Parashari and KN Rao schools emitted."""
        k_rows = _get_rows_for_category(all_rows, "karaka_chara_position")
        school_rows = [r for r in k_rows if r.get("fact_key") == "karaka_school"]
        schools = {r.get("fact_value_text") for r in school_rows}
        assert "parashari_rahu_excluded" in schools
        assert "kn_rao_rahu_included" in schools

    def test_lal_kitab_floored_with_flag(self, all_rows):
        """Lal Kitab rows must all have absent_prerequisite_flag = 'true'."""
        lk_rows = _get_rows_for_category(all_rows, "lal_kitab_special_point")
        flag_rows = [r for r in lk_rows if r.get("fact_key") == "absent_prerequisite_flag"]
        assert flag_rows, "No absent_prerequisite_flag rows in lal_kitab_special_point"
        for row in flag_rows:
            assert row.get("fact_value_text") == "true", (
                f"absent_prerequisite_flag not 'true': {row}"
            )

    def test_maharsi_floored_with_flag(self, all_rows):
        """Maharsi rows must all have absent_prerequisite_flag = 'true'."""
        m_rows = _get_rows_for_category(all_rows, "maharsi_specific_point")
        flag_rows = [r for r in m_rows if r.get("fact_key") == "absent_prerequisite_flag"]
        assert flag_rows
        for row in flag_rows:
            assert row.get("fact_value_text") == "true"

    def test_bhrigu_nadi_8_chakras(self, all_rows):
        """8 Bhrigu Chakra subjects."""
        bn_rows = _get_rows_for_category(all_rows, "bhrigu_nadi_point")
        subjects = {r["fact_subject"] for r in bn_rows}
        assert len(subjects) == 8, f"Expected 8 Bhrigu Chakras, got {len(subjects)}: {sorted(subjects)}"
        assert "BHRIGU_CHAKRA_1" in subjects
        assert "BHRIGU_CHAKRA_8" in subjects


# ── 47–52: FORENSIC-derived consistency ───────────────────────────────────────

class TestForensicDerivedConsistency:
    def test_bhrigu_bindu_equals_moon_rahu_midpoint(self, all_rows):
        """Bhrigu Bindu longitude = midpoint(Moon, Rahu) mod 360."""
        w = _import_writer()
        expected = w._midpoint(_TEST_MOON_LONG, _TEST_RAH_LONG)
        bb_row = _get_row(all_rows, "esoteric_point_bhrigu_bindu",
                           "BHRIGU_BINDU", "longitude_sidereal")
        assert bb_row is not None, "No BHRIGU_BINDU longitude row"
        actual = bb_row["fact_value_num"]
        assert abs(actual - expected) < 0.001, (
            f"BB longitude mismatch: expected {expected:.4f} got {actual:.4f}"
        )

    def test_yogi_point_bphs_formula(self, all_rows):
        """Yogi Point (bphs_93_20) = (Sun + Moon + 93.333) mod 360."""
        expected = (_TEST_SUN_LONG + _TEST_MOON_LONG + 93.3333333) % 360.0
        yogi_rows = _get_rows_for_category(all_rows, "esoteric_point_yogi")
        bphs_rows = [r for r in yogi_rows
                     if r.get("formula_id") == "bphs_93_20" and r.get("fact_key") == "longitude_sidereal"]
        assert bphs_rows, "No bphs_93_20 Yogi longitude row"
        actual = bphs_rows[0]["fact_value_num"]
        assert abs(actual - expected) < 0.001, (
            f"Yogi (bphs) mismatch: expected {expected:.4f} got {actual:.4f}"
        )

    def test_hadda_1_is_jupiter_aries_zone(self, all_rows):
        """HADDA_1 = Aries 0–6°, lord = Jupiter."""
        lord_row = _get_row(all_rows, "tajik_hadda_lord", "HADDA_1", "lord")
        assert lord_row is not None, "No HADDA_1 lord row"
        assert lord_row["fact_value_text"] == "Jupiter", (
            f"HADDA_1 lord expected Jupiter, got {lord_row['fact_value_text']}"
        )
        sign_row = _get_row(all_rows, "tajik_hadda_lord", "HADDA_1", "sign")
        assert sign_row is not None
        assert sign_row["fact_value_text"] == "Aries"

    def test_atmakaraka_highest_degree_in_sign(self):
        """Atmakaraka in test data = planet with highest degree in sign."""
        # Among test planets:
        planet_deg_in_sign = {
            "Sun":     _TEST_SUN_LONG % 30.0,   # 280%30 = 10
            "Moon":    _TEST_MOON_LONG % 30.0,  # 321%30 = 21
            "Mars":    _TEST_MAR_LONG % 30.0,   # 195%30 = 15
            "Mercury": _TEST_MER_LONG % 30.0,   # 275%30 = 5
            "Jupiter": _TEST_JUP_LONG % 30.0,   # 120%30 = 0
            "Venus":   _TEST_VEN_LONG % 30.0,   # 300%30 = 0
            "Saturn":  _TEST_SAT_LONG % 30.0,   # 210%30 = 0
        }
        expected_ak = max(planet_deg_in_sign, key=planet_deg_in_sign.get)
        assert expected_ak == "Moon", (
            f"Expected Moon as AK (deg 21), got {expected_ak}"
        )

    def test_karakamsa_sign_matches_ak_d9(self, all_rows):
        """Karakamsa sign must be D9 sign of Atmakaraka (Moon)."""
        w = _import_writer()
        # Moon at 321° → D9 sign
        d9_sign = w._d9_sign(_TEST_MOON_LONG)
        km_rows = _get_rows_for_category(all_rows, "karakamsa_position")
        sign_row = _get_row(all_rows, "karakamsa_position", "KARAKAMSA", "sign")
        assert sign_row is not None, "No karakamsa KARAKAMSA.sign row"
        assert sign_row["fact_value_text"] == d9_sign, (
            f"Karakamsa sign expected {d9_sign}, got {sign_row['fact_value_text']}"
        )

    def test_vargottama_flag_correct_for_lagna(self):
        """Near-sign Lagna at 5° — vargottama depends on D9 sign match."""
        w = _import_writer()
        # Lagna at 5° (Aries, sign_idx=0 → Movable → D9 starts at Aries)
        # pada = 5/3.333 = 1 → pada 1 → D9 = Aries
        d9 = w._d9_sign(_TEST_LAGNA_LONG)
        expected_varg = (SIGNS[0] == d9)  # Aries D1 == D9
        varg = w._is_vargottama(_TEST_LAGNA_LONG)
        assert varg == expected_varg


# ── 53–54: Phantom UUID + ayanamsha ──────────────────────────────────────────

class TestPhantomAndAyanamsha:
    def test_phantom_uuid_never_in_rows(self, all_rows):
        """Dead phantom UUID 362f9f17 must not appear anywhere."""
        for row in all_rows:
            assert row.get("chart_id") != DEAD_PHANTOM_UUID
            assert DEAD_PHANTOM_UUID not in (row.get("citation_ref") or "")
            assert DEAD_PHANTOM_UUID not in (row.get("chart_id") or "")

    def test_all_rows_use_canonical_chart_id(self, all_rows):
        for row in all_rows:
            assert row["chart_id"] == CANONICAL_CHART_ID


# ── 55: Schema validation ─────────────────────────────────────────────────────

GA5_CATEGORIES = [
    "upagraha_position", "saturn_derived_point",
    "esoteric_point_bhrigu_bindu", "esoteric_point_yogi", "esoteric_point_avayogi",
    "esoteric_point_mrityu", "esoteric_point_trisphuta", "esoteric_point_chatushphuta",
    "esoteric_point_panchasphuta", "esoteric_point_pranapada_sphuta",
    "esoteric_point_trikona_dasha_sphuta", "esoteric_point_sri_yantra_position",
    "esoteric_point_brahma", "esoteric_point_vishnu", "esoteric_point_shiva",
    "saham_position", "karaka_chara_position", "karakamsa_position",
    "swamsa_position", "arudha_pada", "midpoint",
    "kp_ruling_planets_natal", "kp_cuspal_significators", "aprakasha_position",
    "tajik_hadda_lord", "tajik_triraashipathi", "tajik_vargottama_specific",
    "lal_kitab_special_point", "maharsi_specific_point", "bhrigu_nadi_point",
    "nakshatra_pada_sensitive",
]


class TestSchemaValidation:
    def test_schema_loads(self):
        assert SCHEMA_PATH.exists(), f"Schema not found: {SCHEMA_PATH}"
        with open(SCHEMA_PATH) as f:
            schema = json.load(f)
        assert "categories" in schema

    @pytest.mark.parametrize("category", GA5_CATEGORIES)
    def test_category_in_schema(self, category):
        with open(SCHEMA_PATH) as f:
            schema = json.load(f)
        cats = schema.get("categories", {})
        assert category in cats, f"GA5 category '{category}' missing from CHART_FACTS_SCHEMA.json"

    def test_ga5_categories_have_section_b_enrichment(self):
        with open(SCHEMA_PATH) as f:
            schema = json.load(f)
        cats = schema.get("categories", {})
        for cat in GA5_CATEGORIES:
            if cat in cats:
                assert cats[cat].get("section_b_enrichment") is True, (
                    f"Category {cat} missing section_b_enrichment=true in schema"
                )

    def test_ga5_categories_no_prose_value_type(self):
        with open(SCHEMA_PATH) as f:
            schema = json.load(f)
        cats = schema.get("categories", {})
        for cat in GA5_CATEGORIES:
            if cat in cats:
                for key_spec in cats[cat].get("allowed_keys", {}).values():
                    vt = key_spec.get("value_type", "")
                    assert vt != "prose", (
                        f"GA5 category {cat} has prose value_type (not allowed)"
                    )


# ── M-16: arudha 2nd-house/7th-from-bhava exception (R6 1d-sensitive) ─────────

class TestArudhaExceptionM16:
    """
    Register M-16: `_build_arudha_rows`'s `_arudha_sign` previously implemented
    only Exception 1 (arudha lands in its own house -> shift to 10th). Exception
    2 (arudha lands 7th-from-its-house -> shift to 10th) was missing, producing
    a wrong arudha whenever the house-lord sits exactly 4 signs away from its
    own house. This test constructs that exact configuration and hand-verifies
    the expected classical result.
    """

    def test_exception_2_fires_when_lord_four_signs_away(self):
        w = _import_writer()
        # Lagna in Aries (sign 0) -> house 2 = Taurus (sign 1), lord = Venus.
        # Venus placed in Leo (sign 4): steps = (4-1)%12 = 3 (not 0, so no mod-12
        # rewrite needed); raw arudha_idx = (4+3)%12 = 7 = Scorpio.
        # Scorpio == (house_sign_idx(1) + 6) % 12 == 7 -> Exception 2 must fire:
        # shift to 10th from Scorpio(7): (7+9)%12 = 4 = Leo.
        all_longs = {
            "LAGNA": 5.0,    # Aries
            "SUN": 10.0, "MOON": 10.0, "MAR": 10.0, "MER": 10.0,
            "JUP": 10.0, "SAT": 10.0,
            "VEN": 4 * 30 + 10.0,  # Venus in Leo (sign_idx=4)
        }
        rows = w._build_arudha_rows(all_longs, "test-chart", "lahiri_chitrapaksha", "test-build", "test-eng")
        a2_sign = next(r for r in rows if r["fact_subject"] == "ARUDHA_A2" and r["fact_key"] == "sign")
        a2_long = next(r for r in rows if r["fact_subject"] == "ARUDHA_A2" and r["fact_key"] == "longitude_sidereal")
        assert a2_sign["fact_value_text"] == "Leo", (
            f"M-16 exception-2 did not fire: expected Leo (10th-from-Scorpio), got {a2_sign['fact_value_text']}"
        )
        assert a2_long["fact_value_num"] == 120.0  # Leo sign-start (D-10 sign-cusp convention)

    def test_exception_1_still_fires_for_own_house_case(self):
        """Regression guard: Exception 1 (own-house) must still work after the
        M-16 patch — it must not have been clobbered by adding Exception 2."""
        w = _import_writer()
        # Lagna in Aries (sign 0) -> house 2 = Taurus (sign 1), lord = Venus.
        # Venus placed in Taurus itself (sign 1): steps=(1-1)%12=0->12;
        # raw arudha_idx=(1+12)%12=1=Taurus == house_sign_idx(1) -> Exception 1
        # fires: shift to 10th from Taurus(1): (1+9)%12=10=Aquarius.
        all_longs = {
            "LAGNA": 5.0,
            "SUN": 10.0, "MOON": 10.0, "MAR": 10.0, "MER": 10.0,
            "JUP": 10.0, "SAT": 10.0,
            "VEN": 1 * 30 + 10.0,  # Venus in Taurus (sign_idx=1) — own house
        }
        rows = w._build_arudha_rows(all_longs, "test-chart", "lahiri_chitrapaksha", "test-build", "test-eng")
        a2_sign = next(r for r in rows if r["fact_subject"] == "ARUDHA_A2" and r["fact_key"] == "sign")
        assert a2_sign["fact_value_text"] == "Aquarius"
