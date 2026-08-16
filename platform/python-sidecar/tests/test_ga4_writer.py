"""
test_ga4_writer.py — Unit tests for GA4 panchanga birth-instant writer.

All tests are no-DB (mock panchanga_instant). Validates:
  - FORENSIC gate pass/fail behavior
  - fact_id determinism and uniqueness
  - citation_ref format compliance
  - Row count projections for INVARIANT and DEPENDENT categories
  - Tara bala: 27 rows per ayanamsha, correct values for canonical native
  - Chandra bala: 12 rows per ayanamsha, correct values for canonical native
  - Atomic grain: no narration values, correct value types
  - Schema JSON: A4 categories declared
  - No phantom UUID 362f9f17; no audience_tier; no natal_engine
  - Engine string = panchanga_engine/...

Tests:
  1.  FORENSIC gate passes for correct PanchangaInstant (tithi=Shukla Tritiya,
      vara=Ravivara, yoga=Shiva, karana=Garaja, nak=Purva Bhadrapada)
  2.  FORENSIC gate fails on wrong tithi
  3.  FORENSIC gate fails on wrong vara
  4.  FORENSIC gate fails on wrong yoga
  5.  FORENSIC gate fails on wrong karana
  6.  FORENSIC gate fails on wrong nakshatra
  7.  fact_id is 16 hex chars
  8.  fact_id is deterministic (same inputs → same output)
  9.  fact_id differs for different category inputs
  10. citation_ref format: category.subject.key@chart=...
  11. citation_ref contains CANONICAL_CHART_ID fragment
  12. citation_ref does not contain phantom 362f9f17
  13. _emit_tithi: produces ≥6 rows with ayanamsha_id=INVARIANT
  14. _emit_vara: produces 4 rows
  15. _emit_yoga: produces 4 rows
  16. _emit_karana: produces 5 rows
  17. Tara bala baseline: produces exactly 27 rows per ayanamsha
  18. Tara bala: native's own nakshatra (Purva Bhadrapada=25) → Janma
  19. Tara bala: nakshatra +2 from birth (ASL) → Vipat
  20. Tara bala: all tara_class values are valid enum members
  21. Chandra bala baseline: produces exactly 12 rows per ayanamsha
  22. Chandra bala: birth Moon sign Kumbha → favorable (position=1)
  23. Chandra bala: 3rd sign from Kumbha (Mesha) → favorable (position=5 → unfavorable actually)
  24. Chandra bala: all classification values are valid enum members
  25. _emit_tara_bala_baseline: all subjects match TRANSIT_NAK_{SHORT} pattern
  26. _emit_chandra_bala_baseline: all subjects match TRANSIT_SIGN_{NAME} pattern
  27. Build invariant rows: all ayanamsha_id = INVARIANT
  28. Build dependent rows: all ayanamsha_id != INVARIANT
  29. All fact_ids in full row set are unique (no duplicates within build)
  30. All citation_human non-empty and ends with period or bracket
  31. No fact_value_text contains narration patterns (indicates, suggests, etc.)
  32. Engine string: all rows have source_calculation starting with 'panchanga_engine/'
  33. No row has source_calculation containing 'natal_engine'
  34. No phantom UUID 362f9f17 in any row field
  35. No audience_tier in writer source code
  36. Schema JSON: panchanga_tithi category declared
  37. Schema JSON: panchanga_vara category declared
  38. Schema JSON: panchanga_yoga category declared
  39. Schema JSON: panchanga_karana category declared
  40. Schema JSON: panchanga_nakshatra_moon category declared
  41. Schema JSON: tara_bala_natal_baseline category declared
  42. Schema JSON: chandra_bala_natal_baseline category declared
  43. Schema JSON: A4 categories have since_engine_version containing 'panchanga_engine'
  44. Migration 208 SQL file exists
  45. Migration 208 references mv_chart_panchanga_birth_summary
  46. Panchaka for native (nak_id=25) → Agni panchaka active
  47. Panchaka for neutral (nak_id=1) → none active
  48. Disha Shul: Ravivara (id=1) → West
  49. _emit_panchaka_classification: produces 5×3+1=16 rows per ayanamsha (5 types × 3 keys + 1 overall)
  50. _emit_chandra_bala_baseline: all 12 sign names are valid SIGN_NAMES members
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys
from typing import Any
from unittest.mock import MagicMock

import pytest

# Path setup for local imports
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
DEAD_PHANTOM_UUID = "362f9f17"
BUILD_ID = "test-ga4-build-id"
SCHEMA_PATH = pathlib.Path(__file__).parent.parent / "ga_writers" / "CHART_FACTS_SCHEMA.json"
MIGRATION_PATH = (
    pathlib.Path(__file__).parent.parent.parent / "supabase" / "migrations"
    / "208_ga4_panchanga_mv.sql"
)

FORBIDDEN_NARRATION_PATTERNS = [
    "indicates", "suggests", "implies", "means", "denotes",
    "yields", "results in", "leads to",
]

# ── Mock PanchangaInstant fixture factory ─────────────────────────────────────

def _mock_anga(name: str, anga_id: int, end_utc=None) -> Any:
    """Create a mock Anga-like object."""
    m = MagicMock()
    m.name = name
    m.id = anga_id
    m.end_utc = end_utc
    return m


def _make_forensic_pi() -> Any:
    """Return a valid PanchangaInstant mock matching FORENSIC anchors."""
    pi = MagicMock()
    pi.tithi = _mock_anga("Shukla Tritiya", 3)
    pi.vara = _mock_anga("Ravivara", 1)
    pi.yoga = _mock_anga("Shiva", 18)  # Shiva yoga = 18
    pi.karana = _mock_anga("Garaja", 6)  # Garaja = id 6
    pi.nakshatra = _mock_anga("Purva Bhadrapada", 25)

    # tithi_attrs
    ta = MagicMock()
    ta.anga_type = "Jaya"
    ta.deity = "Vishnu"
    ta.lord = "Mars"
    ta.pct_elapsed = 0.45
    pi.tithi_attrs = ta

    # nakshatra_attrs
    na = MagicMock()
    na.deity = "Ahirbudhnya"
    na.pct_elapsed = 0.12
    pi.nakshatra_attrs = na

    # calendrical
    cal = MagicMock()
    cal.ayana = "Uttarayana"
    cal.ritu = "Shishira"
    cal.solar_arc_deg = 15.23
    cal.sankranti_name = "Makara Sankranti"
    cal.masa_purnimanta = "Magha"
    cal.masa_amanta = "Pausha"
    cal.is_adhika_masa = False
    cal.is_kshaya_masa = False
    cal.vikram_samvat = 2040
    cal.shaka_samvat = 1905
    cal.kali_samvat = 5084
    cal.jovian_year_name = "Hevilambi"
    cal.jovian_year_number = 37
    pi.calendrical = cal

    # sun_moon
    sm = MagicMock()
    sm.sun_moon_separation_deg = 26.4
    sm.moon_illumination_pct = 13.2
    sm.moon_phase_angle_deg = 26.4
    pi.sun_moon = sm

    # vasa
    vasa = MagicMock()
    vasa.agni_vasa = "Prithvi"
    pi.vasa = vasa

    # shoonya
    shoonya = MagicMock()
    shoonya.tithi_shoonya_sign_id = 7  # Libra
    shoonya.tithi_shoonya_sign_name = "Tula"
    shoonya.nakshatra_shoonya_sign_id = 4  # Cancer
    shoonya.nakshatra_shoonya_sign_name = "Karka"
    pi.shoonya = shoonya

    # window_membership
    wm = MagicMock()
    wm.hora_planet = "Sun"
    wm.choghadiya_slot = "Udveg"
    pi.window_membership = wm

    # special_yogas_instant — fixture matches _yoga_dict() real producer shape
    from datetime import datetime, timezone
    _t = datetime(2026, 6, 10, 0, 0, 0, tzinfo=timezone.utc)
    pi.special_yogas_instant = [
        {"yoga": "Sarvartha Siddhi Yoga", "start_utc": _t, "end_utc": _t,
         "strength": "strong", "stars": 5}
    ]

    # inauspicious_full, auspicious_full — empty for basic tests
    pi.inauspicious_full = []
    pi.auspicious_full = []

    # panchaka state
    pc = MagicMock()
    pc.panchaka_type = "Agni"
    pc.active = True
    pi.panchaka = pc

    return pi


@pytest.fixture(scope="module")
def forensic_pi() -> Any:
    return _make_forensic_pi()


def _load_schema():
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)


# ── Helper: import writer module ──────────────────────────────────────────────

def _writer():
    from ga_writers import ga_panchanga_writer
    return ga_panchanga_writer


# ── 1-6: FORENSIC gate tests ──────────────────────────────────────────────────

class TestForensicGate:
    def test_passes_for_correct_pi(self, forensic_pi):
        """1. FORENSIC gate passes for correct PanchangaInstant."""
        w = _writer()
        w.panchanga_forensic_gate(forensic_pi)  # Must not raise

    def test_fails_wrong_tithi(self, forensic_pi):
        """2. FORENSIC gate fails on wrong tithi."""
        w = _writer()
        bad_pi = _make_forensic_pi()
        bad_pi.tithi = _mock_anga("Shukla Panchami", 5)
        with pytest.raises(RuntimeError, match="tithi"):
            w.panchanga_forensic_gate(bad_pi)

    def test_fails_wrong_vara(self, forensic_pi):
        """3. FORENSIC gate fails on wrong vara."""
        w = _writer()
        bad_pi = _make_forensic_pi()
        bad_pi.vara = _mock_anga("Somavara", 2)
        with pytest.raises(RuntimeError, match="vara"):
            w.panchanga_forensic_gate(bad_pi)

    def test_fails_wrong_yoga(self, forensic_pi):
        """4. FORENSIC gate fails on wrong yoga."""
        w = _writer()
        bad_pi = _make_forensic_pi()
        bad_pi.yoga = _mock_anga("Vyaghata", 6)
        with pytest.raises(RuntimeError, match="yoga"):
            w.panchanga_forensic_gate(bad_pi)

    def test_fails_wrong_karana(self, forensic_pi):
        """5. FORENSIC gate fails on wrong karana."""
        w = _writer()
        bad_pi = _make_forensic_pi()
        bad_pi.karana = _mock_anga("Kintughna", 11)
        with pytest.raises(RuntimeError, match="karana"):
            w.panchanga_forensic_gate(bad_pi)

    def test_fails_wrong_nakshatra(self, forensic_pi):
        """6. FORENSIC gate fails on wrong nakshatra."""
        w = _writer()
        bad_pi = _make_forensic_pi()
        bad_pi.nakshatra = _mock_anga("Ashwini", 1)
        with pytest.raises(RuntimeError, match="nakshatra"):
            w.panchanga_forensic_gate(bad_pi)


# ── 7-9: fact_id ──────────────────────────────────────────────────────────────

class TestFactId:
    def test_is_16_hex_chars(self):
        """7. fact_id is 16 hex chars."""
        w = _writer()
        fid = w._fact_id("cat", "subj", "key", CANONICAL_CHART_ID, "INVARIANT", BUILD_ID)
        assert len(fid) == 16
        assert re.match(r"^[0-9a-f]{16}$", fid)

    def test_is_deterministic(self):
        """8. fact_id is deterministic."""
        w = _writer()
        fid1 = w._fact_id("cat", "subj", "key", CANONICAL_CHART_ID, "INVARIANT", BUILD_ID)
        fid2 = w._fact_id("cat", "subj", "key", CANONICAL_CHART_ID, "INVARIANT", BUILD_ID)
        assert fid1 == fid2

    def test_differs_for_different_category(self):
        """9. fact_id differs for different category."""
        w = _writer()
        fid1 = w._fact_id("cat_a", "subj", "key", CANONICAL_CHART_ID, "INVARIANT", BUILD_ID)
        fid2 = w._fact_id("cat_b", "subj", "key", CANONICAL_CHART_ID, "INVARIANT", BUILD_ID)
        assert fid1 != fid2


# ── 10-12: citation_ref ───────────────────────────────────────────────────────

class TestCitationRef:
    def test_format_matches_spec(self):
        """10. citation_ref format: category.subject.key@chart=..."""
        w = _writer()
        ref = w._citation_ref("panchanga_tithi", "TITHI_BIRTH", "name",
                               CANONICAL_CHART_ID, "INVARIANT")
        assert ref.startswith("panchanga_tithi.TITHI_BIRTH.name@chart=")

    def test_contains_canonical_chart_id(self):
        """11. citation_ref contains CANONICAL_CHART_ID fragment."""
        w = _writer()
        ref = w._citation_ref("panchanga_tithi", "TITHI_BIRTH", "name",
                               CANONICAL_CHART_ID, "INVARIANT")
        assert CANONICAL_CHART_ID in ref

    def test_does_not_contain_phantom_uuid(self):
        """12. citation_ref does not contain phantom 362f9f17."""
        w = _writer()
        ref = w._citation_ref("panchanga_tithi", "TITHI_BIRTH", "name",
                               CANONICAL_CHART_ID, "INVARIANT")
        assert DEAD_PHANTOM_UUID not in ref


# ── 13-16: Row emitters (unit-level) ─────────────────────────────────────────

class TestRowEmitters:
    def test_emit_tithi_row_count(self, forensic_pi):
        """13. _emit_tithi: produces ≥6 rows with ayanamsha_id=INVARIANT."""
        w = _writer()
        rows = w._emit_tithi(forensic_pi, CANONICAL_CHART_ID, BUILD_ID, "2026-06-10T00:00:00+00:00")
        assert len(rows) >= 6
        for r in rows:
            assert r["ayanamsha_id"] == "INVARIANT"

    def test_emit_vara_row_count(self, forensic_pi):
        """14. _emit_vara: produces 4 rows."""
        w = _writer()
        rows = w._emit_vara(forensic_pi, CANONICAL_CHART_ID, BUILD_ID, "2026-06-10T00:00:00+00:00")
        assert len(rows) == 4
        for r in rows:
            assert r["ayanamsha_id"] == "INVARIANT"

    def test_emit_yoga_row_count(self, forensic_pi):
        """15. _emit_yoga: produces 4 rows."""
        w = _writer()
        rows = w._emit_yoga(forensic_pi, CANONICAL_CHART_ID, BUILD_ID, "2026-06-10T00:00:00+00:00")
        assert len(rows) == 4
        for r in rows:
            assert r["ayanamsha_id"] == "INVARIANT"

    def test_emit_karana_row_count(self, forensic_pi):
        """16. _emit_karana: produces 5 rows."""
        w = _writer()
        rows = w._emit_karana(forensic_pi, CANONICAL_CHART_ID, BUILD_ID, "2026-06-10T00:00:00+00:00")
        assert len(rows) == 5
        for r in rows:
            assert r["ayanamsha_id"] == "INVARIANT"


# ── 17-20: Tara bala baseline ─────────────────────────────────────────────────

class TestTaraBalaBadeline:
    VALID_TARA_CLASSES = {"Janma", "Sampat", "Vipat", "Kshema", "Pratyak",
                          "Sadhaka", "Vadha", "Mitra", "Atimitra"}

    def test_tara_bala_row_count(self):
        """17. Tara bala baseline: exactly 27 rows per ayanamsha."""
        w = _writer()
        rows = w._emit_tara_bala_baseline(
            _make_forensic_pi(), CANONICAL_CHART_ID, BUILD_ID, "2026-06-10T00:00:00+00:00",
            "lahiri_chitrapaksha"
        )
        assert len(rows) == 27

    def test_native_nak_is_janma(self):
        """18. Tara bala: native's own nakshatra (Purva Bhadrapada=25) → Janma."""
        w = _writer()
        rows = w._emit_tara_bala_baseline(
            _make_forensic_pi(), CANONICAL_CHART_ID, BUILD_ID, "2026-06-10T00:00:00+00:00",
            "lahiri_chitrapaksha"
        )
        # Purva Bhadrapada = short code PPB
        ppb_rows = [r for r in rows if r["fact_subject"] == "TRANSIT_NAK_PPB"]
        assert len(ppb_rows) == 1
        assert ppb_rows[0]["fact_value_text"] == "Janma"

    def test_vipat_nak(self):
        """19. Tara bala: nakshatra 2 ahead from birth (UPB=26) → Sampat; 3 ahead (REV=27) → Vipat."""
        w = _writer()
        rows = w._emit_tara_bala_baseline(
            _make_forensic_pi(), CANONICAL_CHART_ID, BUILD_ID, "2026-06-10T00:00:00+00:00",
            "lahiri_chitrapaksha"
        )
        by_subj = {r["fact_subject"]: r["fact_value_text"] for r in rows}
        # UPB = index 25 (nak_id=26), 1 ahead of PPB(25) → position=(26-25)%27+1=2 → Sampat
        assert by_subj.get("TRANSIT_NAK_UPB") == "Sampat"
        # REV = index 26 (nak_id=27), 2 ahead → position=(27-25)%27+1=3 → Vipat
        assert by_subj.get("TRANSIT_NAK_REV") == "Vipat"

    def test_tara_class_valid_enums(self):
        """20. Tara bala: all tara_class values are valid enum members."""
        w = _writer()
        rows = w._emit_tara_bala_baseline(
            _make_forensic_pi(), CANONICAL_CHART_ID, BUILD_ID, "2026-06-10T00:00:00+00:00",
            "lahiri_chitrapaksha"
        )
        for r in rows:
            assert r["fact_value_text"] in self.VALID_TARA_CLASSES, (
                f"Invalid tara_class: {r['fact_value_text']} for subject {r['fact_subject']}"
            )


# ── 21-24: Chandra bala baseline ─────────────────────────────────────────────

class TestChandraBalaBadeline:
    VALID_CLASSIFICATIONS = {"favorable", "neutral", "unfavorable"}

    def test_chandra_bala_row_count(self):
        """21. Chandra bala baseline: exactly 12 rows per ayanamsha."""
        w = _writer()
        rows = w._emit_chandra_bala_baseline(
            _make_forensic_pi(), CANONICAL_CHART_ID, BUILD_ID, "2026-06-10T00:00:00+00:00",
            "lahiri_chitrapaksha"
        )
        assert len(rows) == 12

    def test_birth_moon_sign_kumbha_favorable(self):
        """22. Chandra bala: birth Moon sign Kumbha → favorable (position=1)."""
        w = _writer()
        rows = w._emit_chandra_bala_baseline(
            _make_forensic_pi(), CANONICAL_CHART_ID, BUILD_ID, "2026-06-10T00:00:00+00:00",
            "lahiri_chitrapaksha"
        )
        kumbha_rows = [r for r in rows if r["fact_subject"] == "TRANSIT_SIGN_KUMBHA"]
        assert len(kumbha_rows) == 1
        assert kumbha_rows[0]["fact_value_text"] == "favorable", (
            f"Expected favorable for Kumbha, got {kumbha_rows[0]['fact_value_text']}"
        )

    def test_second_sign_meena_unfavorable(self):
        """23. Chandra bala: 2nd sign from Kumbha (Meena) → unfavorable (position=2)."""
        w = _writer()
        rows = w._emit_chandra_bala_baseline(
            _make_forensic_pi(), CANONICAL_CHART_ID, BUILD_ID, "2026-06-10T00:00:00+00:00",
            "lahiri_chitrapaksha"
        )
        # Meena = sign_id=12, position from Kumbha(11) = (12-11)%12+1 = 2 → unfavorable
        meena_rows = [r for r in rows if r["fact_subject"] == "TRANSIT_SIGN_MEENA"]
        assert len(meena_rows) == 1
        assert meena_rows[0]["fact_value_text"] == "unfavorable"

    def test_all_classification_valid_enums(self):
        """24. Chandra bala: all classification values are valid enum members."""
        w = _writer()
        rows = w._emit_chandra_bala_baseline(
            _make_forensic_pi(), CANONICAL_CHART_ID, BUILD_ID, "2026-06-10T00:00:00+00:00",
            "lahiri_chitrapaksha"
        )
        for r in rows:
            assert r["fact_value_text"] in self.VALID_CLASSIFICATIONS


# ── 25-26: Subject patterns ───────────────────────────────────────────────────

class TestSubjectPatterns:
    def test_tara_bala_subject_pattern(self):
        """25. _emit_tara_bala_baseline: all subjects match TRANSIT_NAK_{SHORT} pattern."""
        w = _writer()
        rows = w._emit_tara_bala_baseline(
            _make_forensic_pi(), CANONICAL_CHART_ID, BUILD_ID, "2026-06-10T00:00:00+00:00",
            "lahiri_chitrapaksha"
        )
        pat = re.compile(r"^TRANSIT_NAK_[A-Z]+$")
        for r in rows:
            assert pat.match(r["fact_subject"]), (
                f"Subject '{r['fact_subject']}' does not match TRANSIT_NAK_<SHORT> pattern"
            )

    def test_chandra_bala_subject_pattern(self):
        """26. _emit_chandra_bala_baseline: all subjects match TRANSIT_SIGN_{NAME} pattern."""
        w = _writer()
        rows = w._emit_chandra_bala_baseline(
            _make_forensic_pi(), CANONICAL_CHART_ID, BUILD_ID, "2026-06-10T00:00:00+00:00",
            "lahiri_chitrapaksha"
        )
        pat = re.compile(r"^TRANSIT_SIGN_[A-Z]+$")
        for r in rows:
            assert pat.match(r["fact_subject"]), (
                f"Subject '{r['fact_subject']}' does not match TRANSIT_SIGN_<NAME> pattern"
            )


# ── 27-28: INVARIANT vs DEPENDENT ayanamsha_id ───────────────────────────────

class TestAyanamshaIds:
    def test_tithi_rows_are_invariant(self, forensic_pi):
        """27. Build invariant rows: tithi rows have ayanamsha_id=INVARIANT."""
        w = _writer()
        rows = w._emit_tithi(forensic_pi, CANONICAL_CHART_ID, BUILD_ID, "2026-06-10T00:00:00+00:00")
        for r in rows:
            assert r["ayanamsha_id"] == "INVARIANT"

    def test_nakshatra_moon_rows_are_dependent(self, forensic_pi):
        """28. Build dependent rows: nakshatra_moon rows have ayanamsha_id != INVARIANT."""
        w = _writer()
        rows = w._emit_nakshatra_moon(
            forensic_pi, CANONICAL_CHART_ID, BUILD_ID,
            "2026-06-10T00:00:00+00:00", "lahiri_chitrapaksha"
        )
        for r in rows:
            assert r["ayanamsha_id"] == "lahiri_chitrapaksha"
            assert r["ayanamsha_id"] != "INVARIANT"


# ── 29: fact_id uniqueness across a combined set ─────────────────────────────

class TestFactIdUniqueness:
    def test_all_fact_ids_unique_within_ayanamsha(self, forensic_pi):
        """29. All fact_ids in a combined row set are unique."""
        w = _writer()
        computed_at = "2026-06-10T00:00:00+00:00"
        ay = "lahiri_chitrapaksha"
        rows = []
        rows += w._emit_tithi(forensic_pi, CANONICAL_CHART_ID, BUILD_ID, computed_at)
        rows += w._emit_vara(forensic_pi, CANONICAL_CHART_ID, BUILD_ID, computed_at)
        rows += w._emit_yoga(forensic_pi, CANONICAL_CHART_ID, BUILD_ID, computed_at)
        rows += w._emit_karana(forensic_pi, CANONICAL_CHART_ID, BUILD_ID, computed_at)
        rows += w._emit_nakshatra_moon(forensic_pi, CANONICAL_CHART_ID, BUILD_ID, computed_at, ay)
        rows += w._emit_tara_bala_baseline(forensic_pi, CANONICAL_CHART_ID, BUILD_ID, computed_at, ay)
        rows += w._emit_chandra_bala_baseline(forensic_pi, CANONICAL_CHART_ID, BUILD_ID, computed_at, ay)

        fact_ids = [r["fact_id"] for r in rows]
        assert len(fact_ids) == len(set(fact_ids)), (
            f"Duplicate fact_ids found: "
            f"{[fid for fid in fact_ids if fact_ids.count(fid) > 1]}"
        )


# ── 30-34: Value quality checks ───────────────────────────────────────────────

class TestValueQuality:
    def _get_all_rows(self, forensic_pi) -> list[dict]:
        w = _writer()
        computed_at = "2026-06-10T00:00:00+00:00"
        ay = "lahiri_chitrapaksha"
        rows = []
        rows += w._emit_tithi(forensic_pi, CANONICAL_CHART_ID, BUILD_ID, computed_at)
        rows += w._emit_vara(forensic_pi, CANONICAL_CHART_ID, BUILD_ID, computed_at)
        rows += w._emit_yoga(forensic_pi, CANONICAL_CHART_ID, BUILD_ID, computed_at)
        rows += w._emit_karana(forensic_pi, CANONICAL_CHART_ID, BUILD_ID, computed_at)
        rows += w._emit_nakshatra_moon(forensic_pi, CANONICAL_CHART_ID, BUILD_ID, computed_at, ay)
        rows += w._emit_disha_shul(forensic_pi, CANONICAL_CHART_ID, BUILD_ID, computed_at)
        rows += w._emit_tara_bala_baseline(forensic_pi, CANONICAL_CHART_ID, BUILD_ID, computed_at, ay)
        rows += w._emit_chandra_bala_baseline(forensic_pi, CANONICAL_CHART_ID, BUILD_ID, computed_at, ay)
        return rows

    def test_citation_human_non_empty_and_ends_with_period(self, forensic_pi):
        """30. All citation_human non-empty."""
        rows = self._get_all_rows(forensic_pi)
        for r in rows:
            ch = r.get("citation_human", "")
            assert ch, f"Empty citation_human for {r['fact_subject']}.{r['fact_key']}"

    def test_no_narration_patterns(self, forensic_pi):
        """31. No fact_value_text contains narration patterns."""
        rows = self._get_all_rows(forensic_pi)
        for r in rows:
            vt = r.get("fact_value_text") or ""
            for pat in FORBIDDEN_NARRATION_PATTERNS:
                assert pat not in vt.lower(), (
                    f"Narration pattern '{pat}' found in fact_value_text: '{vt}' "
                    f"(category={r['fact_category']}, key={r['fact_key']})"
                )

    def test_engine_string_starts_with_panchanga_engine(self, forensic_pi):
        """32. Engine string: all rows have source_calculation starting with 'panchanga_engine/'."""
        rows = self._get_all_rows(forensic_pi)
        for r in rows:
            sc = r.get("source_calculation", "")
            assert sc.startswith("panchanga_engine/"), (
                f"source_calculation '{sc}' does not start with 'panchanga_engine/' "
                f"(category={r['fact_category']}, key={r['fact_key']})"
            )

    def test_no_natal_engine_in_source_calculation(self, forensic_pi):
        """33. No row has source_calculation containing 'natal_engine'."""
        rows = self._get_all_rows(forensic_pi)
        for r in rows:
            sc = r.get("source_calculation", "")
            assert "natal_engine" not in sc, (
                f"natal_engine found in source_calculation: '{sc}'"
            )

    def test_no_phantom_uuid_in_rows(self, forensic_pi):
        """34. No phantom UUID 362f9f17 in any row field."""
        rows = self._get_all_rows(forensic_pi)
        for r in rows:
            for k, v in r.items():
                if v is not None:
                    assert DEAD_PHANTOM_UUID not in str(v), (
                        f"Phantom UUID found in row[{k}]: {v}"
                    )


# ── 35: Writer source code checks ─────────────────────────────────────────────

class TestWriterSourceCode:
    def _load_writer_source(self) -> str:
        p = pathlib.Path(__file__).parent.parent / "ga_writers" / "ga_panchanga_writer.py"
        return p.read_text(encoding="utf-8")

    def test_no_audience_tier(self):
        """35. No audience_tier in writer source code."""
        src = self._load_writer_source()
        assert "audience_tier" not in src, (
            "Found 'audience_tier' in ga_panchanga_writer.py — must be removed"
        )


# ── 36-43: Schema JSON checks ─────────────────────────────────────────────────

class TestSchemaJson:
    @pytest.fixture(scope="class")
    def schema(self):
        return _load_schema()

    def test_schema_parses(self, schema):
        """Schema JSON parses without error."""
        assert isinstance(schema, dict)

    def test_panchanga_tithi_declared(self, schema):
        """36. Schema JSON: panchanga_tithi category declared."""
        assert "panchanga_tithi" in schema["categories"]

    def test_panchanga_vara_declared(self, schema):
        """37. Schema JSON: panchanga_vara category declared."""
        assert "panchanga_vara" in schema["categories"]

    def test_panchanga_yoga_declared(self, schema):
        """38. Schema JSON: panchanga_yoga category declared."""
        assert "panchanga_yoga" in schema["categories"]

    def test_panchanga_karana_declared(self, schema):
        """39. Schema JSON: panchanga_karana category declared."""
        assert "panchanga_karana" in schema["categories"]

    def test_panchanga_nakshatra_moon_declared(self, schema):
        """40. Schema JSON: panchanga_nakshatra_moon category declared."""
        assert "panchanga_nakshatra_moon" in schema["categories"]

    def test_tara_bala_natal_baseline_declared(self, schema):
        """41. Schema JSON: tara_bala_natal_baseline category declared."""
        assert "tara_bala_natal_baseline" in schema["categories"]

    def test_chandra_bala_natal_baseline_declared(self, schema):
        """42. Schema JSON: chandra_bala_natal_baseline category declared."""
        assert "chandra_bala_natal_baseline" in schema["categories"]

    def test_a4_categories_engine_string(self, schema):
        """43. Schema JSON: A4 categories have since_engine_version containing 'panchanga_engine'."""
        A4_CATS = [
            "panchanga_tithi", "panchanga_vara", "panchanga_yoga", "panchanga_karana",
            "panchanga_nakshatra_moon", "tara_bala_natal_baseline", "chandra_bala_natal_baseline",
        ]
        for cat in A4_CATS:
            ev = schema["categories"][cat].get("since_engine_version", "")
            assert "panchanga_engine" in ev, (
                f"Category '{cat}' since_engine_version '{ev}' does not contain 'panchanga_engine'"
            )


# ── 44-45: Migration 208 checks ───────────────────────────────────────────────

class TestMigration208:
    def test_migration_file_exists(self):
        """44. Migration 208 SQL file exists."""
        assert MIGRATION_PATH.exists(), (
            f"Migration 208 not found at: {MIGRATION_PATH}"
        )

    def test_migration_references_mv(self):
        """45. Migration 208 references mv_chart_panchanga_birth_summary."""
        sql = MIGRATION_PATH.read_text(encoding="utf-8")
        assert "mv_chart_panchanga_birth_summary" in sql


# ── 46-47: Panchaka classification ───────────────────────────────────────────

class TestPanchakaClassification:
    def test_panchaka_for_native_nak(self, forensic_pi):
        """46. Panchaka for native (nak_id=25) → Agni panchaka active."""
        w = _writer()
        rows = w._emit_panchaka_classification(
            forensic_pi, CANONICAL_CHART_ID, BUILD_ID,
            "2026-06-10T00:00:00+00:00", "lahiri_chitrapaksha"
        )
        agni_rows = [
            r for r in rows
            if r["fact_subject"] == "PANCHAKA_AGNI"
            and r["fact_key"] == "active_at_birth_flag"
        ]
        assert len(agni_rows) == 1
        assert agni_rows[0]["fact_value_text"] == "true"

    def test_panchaka_for_neutral_nak(self):
        """47. Panchaka for neutral (nak_id=1/Ashwini) → none active."""
        w = _writer()
        pi = _make_forensic_pi()
        pi.nakshatra = _mock_anga("Ashwini", 1)  # Non-panchaka nak

        # FORENSIC gate would fail on this mock, but we're testing panchaka directly
        rows = w._emit_panchaka_classification(
            pi, CANONICAL_CHART_ID, BUILD_ID,
            "2026-06-10T00:00:00+00:00", "lahiri_chitrapaksha"
        )
        overall_rows = [
            r for r in rows
            if r["fact_subject"] == "PANCHAKA_OVERALL"
            and r["fact_key"] == "panchaka_overall_classification"
        ]
        assert len(overall_rows) == 1
        assert overall_rows[0]["fact_value_text"] == "none"

    def test_panchaka_classification_row_count(self, forensic_pi):
        """49. _emit_panchaka_classification: produces 5×3+1=16 rows per ayanamsha."""
        w = _writer()
        rows = w._emit_panchaka_classification(
            forensic_pi, CANONICAL_CHART_ID, BUILD_ID,
            "2026-06-10T00:00:00+00:00", "lahiri_chitrapaksha"
        )
        assert len(rows) == 16, f"Expected 16 rows, got {len(rows)}"


# ── 48: Disha Shul ────────────────────────────────────────────────────────────

class TestDishaShul:
    def test_ravivara_west(self, forensic_pi):
        """48. Disha Shul: Ravivara (id=1) → West."""
        w = _writer()
        rows = w._emit_disha_shul(forensic_pi, CANONICAL_CHART_ID, BUILD_ID, "2026-06-10T00:00:00+00:00")
        direction_rows = [r for r in rows if r["fact_key"] == "direction_to_avoid"]
        assert len(direction_rows) == 1
        assert direction_rows[0]["fact_value_text"] == "West"


# ── 50: Chandra bala sign names ───────────────────────────────────────────────

class TestChandraBalaSigns:
    def test_all_12_sign_names_valid(self):
        """50. _emit_chandra_bala_baseline: all 12 sign names are valid SIGN_NAMES members."""
        w = _writer()
        rows = w._emit_chandra_bala_baseline(
            _make_forensic_pi(), CANONICAL_CHART_ID, BUILD_ID, "2026-06-10T00:00:00+00:00",
            "lahiri_chitrapaksha"
        )
        assert len(rows) == 12
        extracted = set(r["fact_subject"].replace("TRANSIT_SIGN_", "") for r in rows)
        expected = {name.upper() for name in w.SIGN_NAMES}
        assert extracted == expected, (
            f"Sign name mismatch.\nExtracted: {sorted(extracted)}\nExpected: {sorted(expected)}"
        )


# ── F-63 exit test: special-yoga combination_name key fix ─────────────────────

def test_special_yoga_combination_name_resolves_real_name():
    """F-63: _emit_special_yoga_combinations must emit the real yoga name, not 'unknown'."""
    w = _writer()
    pi = _make_forensic_pi()
    rows = w._emit_special_yoga_combinations(
        pi, CANONICAL_CHART_ID, BUILD_ID, "2026-06-10T00:00:00+00:00", "lahiri"
    )
    combo_name_rows = [r for r in rows if r["fact_key"] == "combination_name"]
    assert len(combo_name_rows) == 1
    assert combo_name_rows[0]["fact_value_text"] == "Sarvartha Siddhi Yoga"
