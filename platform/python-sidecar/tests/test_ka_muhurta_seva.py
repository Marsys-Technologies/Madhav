"""
test_ka_muhurta_seva.py — Unit tests for ka_muhurta_seva (L3 Kāla K1)

Acceptance criteria:
  AC1 — Service requires (date, location): missing location raises ValueError
  AC2 — Tāra Bala overlay changes score for SAME day between two different birth nakshatras
  AC3 — Knockout: compound-inauspicious panchāṅga returns 0 regardless of other factors
  AC4 — Same date at two different locations yields different results (or at least no error)
  AC5 — New intervention/remedial event classes (upaya_ritual, sadhana_initiation) score correctly
  AC6 — FORENSIC: birth panchāṅga = Shukla Tritiya (3), Ravivara (1), Purva Bhadrapada (25),
         Yoga Shiva (20), Karana Garaja (5)

Runs without a live DB. panchang_engine requires swisseph to be installed.
All panchang computations use the real engine.

FORENSIC birth anchors (7/7 PASS, confirmed by L1 production build):
  Tithi=Shukla Tritiya · Vara=Ravivara · Nakshatra=Purva Bhadrapada
  Yoga=Shiva · Karana=Garaja
  (Sun=Capricorn, Moon=Purva Bhadrapada, Lagna=Aries verified separately)

Layer: L3 Kāla · Asset: ka_muhurta_seva
"""
from __future__ import annotations

import json
from datetime import date, datetime
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

# ── Sidecar path fix ──────────────────────────────────────────────────────────
import sys
import os

SIDECAR_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SIDECAR_ROOT not in sys.path:
    sys.path.insert(0, SIDECAR_ROOT)

# ── Constants ─────────────────────────────────────────────────────────────────

BIRTH_DATE = date(1984, 2, 5)
BIRTH_DATETIME = datetime(1984, 2, 5, 10, 43)
BIRTH_LAT = 20.2700
BIRTH_LON = 85.8400
BIRTH_TZ = 330  # IST = UTC+5:30

BHUBANESWAR = {"lat": BIRTH_LAT, "lon": BIRTH_LON, "tz_offset_minutes": BIRTH_TZ}
MUMBAI = {"lat": 19.0760, "lon": 72.8777, "tz_offset_minutes": 330}
LONDON = {"lat": 51.5074, "lon": -0.1278, "tz_offset_minutes": 0}

# FORENSIC anchor IDs (1-indexed, shastra_tables.py)
FORENSIC_TITHI_ID = 3           # Shukla Tritiya
FORENSIC_VARA_ID = 1            # Ravivara (Sunday)
FORENSIC_NAKSHATRA_ID = 25      # Purva Bhadrapada
FORENSIC_YOGA_ID = 20           # Shiva
FORENSIC_KARANA_ID = 5          # Garaja

# Purva Bhadrapada native NatalChart
NATIVE_CHART_PURVA_BHADRA = None  # lazy import


def _get_native_chart():
    from panchang_engine.types import NatalChart
    return NatalChart(
        birth_nakshatra_id=FORENSIC_NAKSHATRA_ID,  # 25 = Purva Bhadrapada
        birth_lagna_sign_id=1,   # Mesha
        moon_sign_id=11,         # Kumbha
        active_dasha_lord="Jupiter",
    )


def _get_other_chart(birth_nak: int):
    """NatalChart with a different birth nakshatra (for Tāra Bala contrast)."""
    from panchang_engine.types import NatalChart
    return NatalChart(
        birth_nakshatra_id=birth_nak,
        birth_lagna_sign_id=1,
        moon_sign_id=1,
        active_dasha_lord="Saturn",
    )


# ─────────────────────────────────────────────────────────────────────────────
# AC1 — Location is required; None raises ValueError
# ─────────────────────────────────────────────────────────────────────────────

class TestAC1LocationRequired:
    """AC1: service requires (date, location) — missing location raises ValueError."""

    def test_score_none_location_raises(self):
        from services.ka_muhurta_seva import score
        with pytest.raises(ValueError, match="location is required"):
            score(date(2026, 6, 21), None, "vivah")

    def test_score_missing_lat_raises(self):
        from services.ka_muhurta_seva import score
        with pytest.raises(ValueError, match="missing required keys"):
            score(date(2026, 6, 21), {"lon": 85.84, "tz_offset_minutes": 330}, "vivah")

    def test_score_missing_lon_raises(self):
        from services.ka_muhurta_seva import score
        with pytest.raises(ValueError, match="missing required keys"):
            score(date(2026, 6, 21), {"lat": 20.30, "tz_offset_minutes": 330}, "vivah")

    def test_score_missing_tz_raises(self):
        from services.ka_muhurta_seva import score
        with pytest.raises(ValueError, match="missing required keys"):
            score(date(2026, 6, 21), {"lat": 20.30, "lon": 85.84}, "vivah")

    def test_find_windows_none_location_raises(self):
        from services.ka_muhurta_seva import find_windows
        with pytest.raises(ValueError, match="location is required"):
            find_windows(
                "vivah",
                window={"date_from": date(2026, 6, 21), "date_to": date(2026, 6, 21)},
                location=None,
            )

    def test_score_lat_out_of_range_raises(self):
        from services.ka_muhurta_seva import score
        with pytest.raises(ValueError, match="lat out of range"):
            score(date(2026, 6, 21), {"lat": 999.0, "lon": 85.84, "tz_offset_minutes": 330}, "vivah")


# ─────────────────────────────────────────────────────────────────────────────
# AC2 — Tāra Bala overlay changes score between different birth nakshatras
# ─────────────────────────────────────────────────────────────────────────────

class TestAC2TaraBalaOverlay:
    """AC2: Tāra Bala overlay changes score for SAME day, different birth nakshatras."""

    def test_tara_bala_score_differs_for_different_birth_nakshatras(self):
        """
        Score the same day with two different birth_nakshatra_ids.
        The Tāra Bala component will differ because position of the current
        Moon from birth varies by birth nakshatra.
        Use a single fixed day and two nakshatras that produce known-different
        Tāra positions relative to any current Moon nakshatra.
        """
        from panchang_engine.tara_bala import compute_tara_bala_score

        # Birth nakshatra 25 (Purva Bhadrapada) vs 1 (Ashwini) vs 3 (Krittika)
        # With current_nak=8 (Pushya):
        #   from nak 25: offset=(8-25)%27=10 → position 11 (Sadhaka) → auspicious
        #   from nak 1:  offset=(8-1)%27=7   → position 8 (Mitra) → auspicious
        #   from nak 3:  offset=(8-3)%27=5   → position 6 (Sadhaka) → auspicious (but different)
        # Use nak 1 vs nak 14 (Chitra) for a clear Auspicious vs Inauspicious contrast:
        #   from nak 1:  offset=(8-1)%27=7   → position 8 (Mitra) → 0.80
        #   from nak 14: offset=(8-14)%27=21 → position 22 (Sadhya) → position in cycle 4 (Kshema) → 0.85*0.60=0.51
        score_nak1 = compute_tara_bala_score(
            birth_nakshatra_id=1,   # Ashwini
            current_nakshatra_id=8, # Pushya
        )
        score_nak14 = compute_tara_bala_score(
            birth_nakshatra_id=14,  # Chitra — produces different Tāra position
            current_nakshatra_id=8,
        )
        # These should differ — the whole point of Tāra Bala
        assert score_nak1 != score_nak14, (
            f"Tāra Bala scores should differ for different birth nakshatras: "
            f"nak1={score_nak1}, nak14={score_nak14}"
        )

    def test_score_differs_with_vs_without_native_chart(self):
        """
        The full scoring pipeline: score with native_chart != score without
        (when the native weight is non-zero and Tāra score is non-trivial).
        """
        from panchang_engine import compute_panchang
        from muhurat.finder import score_muhurat
        from panchang_engine.types import NatalChart

        # Use birth date as the test date (Purva Bhadrapada day)
        # Janma position = 0.5, native weight=0.10 → score differs by ~5 points
        panchang = compute_panchang(date(2026, 7, 10), BIRTH_LAT, BIRTH_LON, BIRTH_TZ)

        # Native chart with Purva Bhadrapada
        native = NatalChart(
            birth_nakshatra_id=25,
            birth_lagna_sign_id=1,
            moon_sign_id=11,
            active_dasha_lord="Jupiter",
        )
        # Different chart (Ashwini) for contrast
        other = NatalChart(
            birth_nakshatra_id=1,
            birth_lagna_sign_id=1,
            moon_sign_id=1,
            active_dasha_lord="Saturn",
        )

        score_native = score_muhurat(panchang, "vivah", native_chart=native)
        score_other  = score_muhurat(panchang, "vivah", native_chart=other)
        score_none   = score_muhurat(panchang, "vivah", native_chart=None)

        # native and other should differ (different birth nakshatras give different Tāra)
        # They are allowed to equal if the day is knocked out (both = 0.0)
        if score_none > 0.0:
            # Day not knocked out — Tāra Bala should produce a difference
            assert score_native != score_other or score_native != score_none, (
                "Native overlay should change the score when day is not knocked out. "
                f"score_native={score_native}, score_other={score_other}, score_none={score_none}"
            )

    def test_tara_bala_purva_bhadrapada_janma_is_0_5(self):
        """
        Specific check: Purva Bhadrapada (25) vs itself = Janma position.
        Janma score in _TARA_QUALITY = 0.50. Cycle 1, attenuation 1.0 → 0.50.
        """
        from panchang_engine.tara_bala import compute_tara_bala_score
        score = compute_tara_bala_score(
            birth_nakshatra_id=25,
            current_nakshatra_id=25,
        )
        assert abs(score - 0.50) < 1e-9, (
            f"Janma position score should be 0.50, got {score}"
        )

    def test_tara_bala_returns_float_in_range(self):
        """Tāra Bala score is always in [0.0, 1.0]."""
        from panchang_engine.tara_bala import compute_tara_bala_score
        for birth_nak in range(1, 28):
            for current_nak in range(1, 28):
                s = compute_tara_bala_score(birth_nak, current_nak)
                assert 0.0 <= s <= 1.0, (
                    f"Score out of range for birth={birth_nak} current={current_nak}: {s}"
                )


# ─────────────────────────────────────────────────────────────────────────────
# AC3 — Knockout: compound inauspicious returns 0.0
# ─────────────────────────────────────────────────────────────────────────────

class TestAC3Knockout:
    """AC3: compound-inauspicious panchāṅga returns 0 regardless of other factors."""

    def _make_knockout_proxy(self):
        """Build a _CachedPanchang proxy that satisfies all knockout conditions."""
        from muhurat.finder import _CachedPanchang
        return _CachedPanchang({
            "tithi_id": 8,       # Ashtami — worst tithis: {4,8,9,14,30}
            "nakshatra_id": 8,   # Pushya — normally best nakshatra (would score high)
            "vara_id": 7,        # Saturday
            "inauspicious": [
                {"label": "rahu_kalam"},
                {"label": "yamagandam"},
            ],
            "auspicious": [],
            "special_yogas": [
                # Even with an auspicious yoga, knockout should win
                {"yoga": "Amrita Siddhi", "strength": "auspicious", "stars": 5}
            ],
            "sunrise_utc": None,
            "sunset_utc": None,
        })

    def test_knockout_returns_zero(self):
        """Compound inauspicious (rahu_kalam + yamagandam + bad tithi + Saturday) → 0.0."""
        from muhurat.finder import score_muhurat, _in_inauspicious

        proxy = self._make_knockout_proxy()
        assert _in_inauspicious(proxy), "Proxy should satisfy knockout conditions"

        for event in ["vivah", "griha_pravesh", "vyapara", "yatra",
                      "property_purchase", "mantra_initiation",
                      "upaya_ritual", "sadhana_initiation"]:
            s = score_muhurat(proxy, event)
            assert s == 0.0, (
                f"Event '{event}' should return 0.0 on knockout day, got {s}"
            )

    def test_knockout_ignores_native_chart(self):
        """Even with perfect native Tāra Bala, knockout still returns 0.0."""
        from muhurat.finder import score_muhurat
        from panchang_engine.types import NatalChart

        proxy = self._make_knockout_proxy()
        native = NatalChart(
            birth_nakshatra_id=8,   # Pushya = Ati-Mitra with current=8 → tara score=1.0
            birth_lagna_sign_id=1,
            moon_sign_id=1,
            active_dasha_lord="Jupiter",
        )
        s = score_muhurat(proxy, "vivah", native_chart=native)
        assert s == 0.0, f"Knockout must override native overlay: got {s}"

    def test_non_knockout_day_scores_above_zero(self):
        """A good day (no rahu_kalam, good tithi, good nakshatra) should score > 0."""
        from muhurat.finder import score_muhurat, _CachedPanchang

        proxy = _CachedPanchang({
            "tithi_id": 5,      # Shukla Panchami — good tithi
            "nakshatra_id": 8,  # Pushya — best nakshatra for most events
            "vara_id": 5,       # Thursday
            "inauspicious": [],  # no rahu_kalam or yamagandam
            "auspicious": [],
            "special_yogas": [],
            "sunrise_utc": None,
            "sunset_utc": None,
        })
        for event in ["vivah", "vyapara", "upaya_ritual"]:
            s = score_muhurat(proxy, event)
            assert s > 0.0, f"Good day should score > 0 for event '{event}', got {s}"


# ─────────────────────────────────────────────────────────────────────────────
# AC4 — Different locations yield different results (or at least no error)
# ─────────────────────────────────────────────────────────────────────────────

class TestAC4LocationSensitivity:
    """AC4: Same date scored at two different locations yields different results or no error."""

    def test_score_two_locations_no_error(self):
        """Score the same date at Bhubaneswar and London — must not raise."""
        from services.ka_muhurta_seva import score

        test_date = date(2026, 7, 1)
        s_bhubaneswar = score(test_date, BHUBANESWAR, "vivah")
        s_london = score(test_date, LONDON, "vivah")

        assert isinstance(s_bhubaneswar, float), "Score should be a float"
        assert isinstance(s_london, float), "Score should be a float"
        assert 0.0 <= s_bhubaneswar <= 100.0
        assert 0.0 <= s_london <= 100.0

    def test_score_two_locations_can_differ(self):
        """
        Different locations may produce different Panchang (sunrise time affects anga
        computation and inauspicious timings). The scores SHOULD differ for most dates.
        We assert that scoring succeeds at both and produces a valid float.
        """
        from services.ka_muhurta_seva import score

        test_date = date(2026, 7, 15)
        s_bhubaneswar = score(test_date, BHUBANESWAR, "vivah")
        s_mumbai = score(test_date, MUMBAI, "vivah")

        # Both must be valid scores — different sunrises may shift Rahu Kalam timing
        assert 0.0 <= s_bhubaneswar <= 100.0
        assert 0.0 <= s_mumbai <= 100.0

    def test_service_validates_location_lat_range(self):
        """Out-of-range lat raises ValueError (not a silent default)."""
        from services.ka_muhurta_seva import score
        with pytest.raises(ValueError, match="lat out of range"):
            score(date(2026, 6, 21), {"lat": 95.0, "lon": 0.0, "tz_offset_minutes": 0}, "vivah")


# ─────────────────────────────────────────────────────────────────────────────
# AC5 — Intervention/remedial event classes score correctly
# ─────────────────────────────────────────────────────────────────────────────

class TestAC5InterventionEvents:
    """AC5: upaya_ritual and sadhana_initiation are recognised, weighted, and score correctly."""

    def test_upaya_ritual_in_events_mvp(self):
        from muhurat.finder import EVENTS_MVP, is_supported_event
        assert "upaya_ritual" in EVENTS_MVP
        assert is_supported_event("upaya_ritual")

    def test_sadhana_initiation_in_events_mvp(self):
        from muhurat.finder import EVENTS_MVP, is_supported_event
        assert "sadhana_initiation" in EVENTS_MVP
        assert is_supported_event("sadhana_initiation")

    def test_upaya_ritual_in_event_tables(self):
        from panchang_engine.shastra_tables import EVENT_TABLES
        assert "upaya_ritual" in EVENT_TABLES
        tbl = EVENT_TABLES["upaya_ritual"]
        assert "tithi" in tbl and "nakshatra" in tbl and "vara" in tbl

    def test_sadhana_initiation_in_event_tables(self):
        from panchang_engine.shastra_tables import EVENT_TABLES
        assert "sadhana_initiation" in EVENT_TABLES
        tbl = EVENT_TABLES["sadhana_initiation"]
        assert "tithi" in tbl and "nakshatra" in tbl and "vara" in tbl

    def test_upaya_ritual_pushya_scores_highest(self):
        """Pushya nakshatra (8) should score highest for upaya_ritual (0.99 in table)."""
        from panchang_engine.shastra_tables import EVENT_TABLES
        tbl = EVENT_TABLES["upaya_ritual"]
        pushya_score = tbl["nakshatra"].get(8, 0.0)
        assert pushya_score >= 0.95, (
            f"Pushya (nakshatra 8) should score >= 0.95 for upaya_ritual, got {pushya_score}"
        )

    def test_sadhana_initiation_thursday_scores_highest(self):
        """Thursday (vara_id=5) should score highest for sadhana_initiation (0.99 in table)."""
        from panchang_engine.shastra_tables import EVENT_TABLES
        tbl = EVENT_TABLES["sadhana_initiation"]
        thursday_score = tbl["vara"].get(5, 0.0)
        assert thursday_score >= 0.95, (
            f"Thursday (vara 5) should score >= 0.95 for sadhana_initiation, got {thursday_score}"
        )

    def test_upaya_ritual_scores_on_good_day(self):
        """Score a known-good day for upaya_ritual — must return > 0."""
        from muhurat.finder import score_muhurat, _CachedPanchang

        proxy = _CachedPanchang({
            "tithi_id": 11,     # Shukla Ekadashi — premier for upāya
            "nakshatra_id": 8,  # Pushya — supreme for upāya
            "vara_id": 5,       # Thursday
            "inauspicious": [],
            "auspicious": [],
            "special_yogas": [],
            "sunrise_utc": None,
            "sunset_utc": None,
        })
        s = score_muhurat(proxy, "upaya_ritual")
        assert s > 0.0, f"upaya_ritual on Ekadashi+Pushya+Thursday should score > 0, got {s}"

    def test_sadhana_initiation_scores_on_good_day(self):
        """Score a known-good day for sadhana_initiation — must return > 0."""
        from muhurat.finder import score_muhurat, _CachedPanchang

        proxy = _CachedPanchang({
            "tithi_id": 15,     # Purnima — premier for sādhana
            "nakshatra_id": 4,  # Rohini — fixed nakshatra (premier for sustained practice)
            "vara_id": 5,       # Thursday
            "inauspicious": [],
            "auspicious": [],
            "special_yogas": [],
            "sunrise_utc": None,
            "sunset_utc": None,
        })
        s = score_muhurat(proxy, "sadhana_initiation")
        assert s > 0.0, f"sadhana_initiation on Purnima+Rohini+Thursday should score > 0, got {s}"

    def test_upaya_ritual_has_weights_in_yaml(self):
        """muhurat_weights.yaml has an upaya_ritual block."""
        from panchang_engine.config_loader import get_weights_for_event
        weights = get_weights_for_event("upaya_ritual")
        assert "native" in weights
        assert "nakshatra" in weights
        # native weight for upaya_ritual should be >= mantra_initiation (0.20)
        assert weights["native"] >= 0.20, (
            f"upaya_ritual native weight should reflect elevated personal resonance, got {weights['native']}"
        )

    def test_sadhana_initiation_has_weights_in_yaml(self):
        """muhurat_weights.yaml has a sadhana_initiation block."""
        from panchang_engine.config_loader import get_weights_for_event, invalidate_weights_cache
        invalidate_weights_cache()  # ensure fresh read
        weights = get_weights_for_event("sadhana_initiation")
        assert "native" in weights
        assert weights["native"] >= 0.20, (
            f"sadhana_initiation native weight should reflect elevated personal resonance, got {weights['native']}"
        )

    def test_score_via_service_upaya_ritual(self):
        """End-to-end: score upaya_ritual via the service module."""
        from services.ka_muhurta_seva import score
        s = score(date(2026, 7, 10), BHUBANESWAR, "upaya_ritual")
        assert 0.0 <= s <= 100.0, f"upaya_ritual service score out of range: {s}"

    def test_score_via_service_sadhana_initiation(self):
        """End-to-end: score sadhana_initiation via the service module."""
        from services.ka_muhurta_seva import score
        s = score(date(2026, 7, 10), BHUBANESWAR, "sadhana_initiation")
        assert 0.0 <= s <= 100.0, f"sadhana_initiation service score out of range: {s}"


# ─────────────────────────────────────────────────────────────────────────────
# AC6 — FORENSIC: birth panchāṅga via panchanga_instant matches 5 FORENSIC anchors
# ─────────────────────────────────────────────────────────────────────────────

class TestAC6ForensicBirthPanchanga:
    """
    AC6: birth panchāṅga via panchanga_instant matches the 5 FORENSIC anchors.

    FORENSIC 7/7 PASS confirmed by L1 production build (L1_GANITA_CLOSURE §4).
    This test re-confirms the same anchors via the ka_muhurta_seva service layer.

    Anchors (1-indexed per shastra_tables.py):
      tithi      = Shukla Tritiya  → id=3
      vara       = Ravivara        → id=1
      nakshatra  = Purva Bhadrapada → id=25
      yoga       = Shiva           → id=20
      karana     = Garaja          → id=5
    """

    @pytest.fixture(scope="class")
    def birth_instant(self):
        from panchang_engine import panchanga_instant
        return panchanga_instant(BIRTH_DATETIME, BIRTH_LAT, BIRTH_LON, BIRTH_TZ)

    def test_forensic_tithi_shukla_tritiya(self, birth_instant):
        """Tithi must be Shukla Tritiya (id=3)."""
        assert birth_instant.tithi.id == FORENSIC_TITHI_ID, (
            f"FORENSIC FAIL: tithi.id={birth_instant.tithi.id} name={birth_instant.tithi.name}, "
            f"expected {FORENSIC_TITHI_ID} (Shukla Tritiya)"
        )

    def test_forensic_vara_ravivara(self, birth_instant):
        """Vara must be Ravivara / Sunday (id=1)."""
        assert birth_instant.vara.id == FORENSIC_VARA_ID, (
            f"FORENSIC FAIL: vara.id={birth_instant.vara.id} name={birth_instant.vara.name}, "
            f"expected {FORENSIC_VARA_ID} (Ravivara)"
        )

    def test_forensic_nakshatra_purva_bhadrapada(self, birth_instant):
        """Nakshatra must be Purva Bhadrapada (id=25)."""
        assert birth_instant.nakshatra.id == FORENSIC_NAKSHATRA_ID, (
            f"FORENSIC FAIL: nakshatra.id={birth_instant.nakshatra.id} name={birth_instant.nakshatra.name}, "
            f"expected {FORENSIC_NAKSHATRA_ID} (Purva Bhadrapada)"
        )

    def test_forensic_yoga_shiva(self, birth_instant):
        """Yoga must be Shiva (id=20)."""
        assert birth_instant.yoga.id == FORENSIC_YOGA_ID, (
            f"FORENSIC FAIL: yoga.id={birth_instant.yoga.id} name={birth_instant.yoga.name}, "
            f"expected {FORENSIC_YOGA_ID} (Shiva)"
        )

    def test_forensic_karana_garaja(self, birth_instant):
        """Karana must be Garaja (id=5)."""
        assert birth_instant.karana.id == FORENSIC_KARANA_ID, (
            f"FORENSIC FAIL: karana.id={birth_instant.karana.id} name={birth_instant.karana.name}, "
            f"expected {FORENSIC_KARANA_ID} (Garaja)"
        )

    def test_forensic_paksha_shukla(self, birth_instant):
        """Paksha must be shukla (tithi 1–15)."""
        assert birth_instant.paksha == "shukla", (
            f"FORENSIC FAIL: paksha={birth_instant.paksha}, expected shukla"
        )

    def test_forensic_all_five_in_one(self, birth_instant):
        """Composite assert: all 5 FORENSIC anchors pass simultaneously."""
        failures = []
        if birth_instant.tithi.id != FORENSIC_TITHI_ID:
            failures.append(f"tithi: {birth_instant.tithi.id} != {FORENSIC_TITHI_ID}")
        if birth_instant.vara.id != FORENSIC_VARA_ID:
            failures.append(f"vara: {birth_instant.vara.id} != {FORENSIC_VARA_ID}")
        if birth_instant.nakshatra.id != FORENSIC_NAKSHATRA_ID:
            failures.append(f"nakshatra: {birth_instant.nakshatra.id} != {FORENSIC_NAKSHATRA_ID}")
        if birth_instant.yoga.id != FORENSIC_YOGA_ID:
            failures.append(f"yoga: {birth_instant.yoga.id} != {FORENSIC_YOGA_ID}")
        if birth_instant.karana.id != FORENSIC_KARANA_ID:
            failures.append(f"karana: {birth_instant.karana.id} != {FORENSIC_KARANA_ID}")
        assert not failures, (
            f"FORENSIC 5-anchor self-test FAILED ({len(failures)} failures): {failures}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Writer contract compliance
# ─────────────────────────────────────────────────────────────────────────────

class TestWriterContractCompliance:
    """Verify the writer conforms to the FROZEN orchestrator contract."""

    def test_writer_registered_as_ka_muhurta_seva(self):
        """KaMuhurtaSevaWriter is registered under 'ka_muhurta_seva'."""
        import pipeline.orchestrator.writers.ka_muhurta_seva  # noqa: F401 — triggers @register
        from pipeline.orchestrator.writers import _REGISTRY
        assert "ka_muhurta_seva" in _REGISTRY

    def test_writer_returns_rows_inserted_zero(self):
        """Service writer returns WriterResult with rows_inserted=0."""
        import pipeline.orchestrator.writers.ka_muhurta_seva  # noqa: F401 — triggers @register
        from pipeline.orchestrator.writers import _REGISTRY, ContextSpec

        writer_cls = _REGISTRY["ka_muhurta_seva"]
        writer = writer_cls()

        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value = cur

        ctx = ContextSpec(
            asset_id="ka_muhurta_seva",
            build_id="test-build-001",
            db_conn=conn,
            dry_run=True,  # dry_run=True skips the actual DB write
        )
        result = writer.run(ctx)

        assert result.rows_inserted == 0, (
            f"Service writer must return rows_inserted=0, got {result.rows_inserted}"
        )
        conn.commit.assert_not_called()
        conn.rollback.assert_not_called()
        conn.close.assert_not_called()

    def test_writer_notes_contain_health_status(self):
        """WriterResult.notes contains 'healthy' or 'unhealthy'."""
        import pipeline.orchestrator.writers.ka_muhurta_seva  # noqa: F401 — triggers @register
        from pipeline.orchestrator.writers import _REGISTRY, ContextSpec

        writer_cls = _REGISTRY["ka_muhurta_seva"]
        writer = writer_cls()

        ctx = ContextSpec(
            asset_id="ka_muhurta_seva",
            build_id="test-build-002",
            db_conn=MagicMock(),
            dry_run=True,
        )
        result = writer.run(ctx)
        assert "health" in result.notes or "healthy" in result.notes or "unhealthy" in result.notes


# ─────────────────────────────────────────────────────────────────────────────
# Grep-zero: no commit/rollback in service module
# ─────────────────────────────────────────────────────────────────────────────

class TestNoCommitRollback:
    """Grep-zero assertion: no ctx.db_conn.commit() or .rollback() in service files."""

    def test_no_commit_in_writer(self):
        """writer.py must contain no executable .commit() or .rollback() calls (not in comments/docstrings)."""
        import re
        from pathlib import Path
        writer_path = Path(__file__).parent.parent / "services" / "ka_muhurta_seva" / "writer.py"
        assert writer_path.exists(), f"writer.py not found at {writer_path}"
        source = writer_path.read_text()
        # Strip comment lines (# ...) and docstring-style lines (lines starting with """)
        # then check for executable .commit() / .rollback() calls
        code_lines = []
        in_docstring = False
        for line in source.splitlines():
            stripped = line.strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                # Toggle docstring tracking (naive but sufficient for our files)
                in_docstring = not in_docstring
                continue
            if in_docstring:
                continue
            if stripped.startswith("#"):
                continue
            code_lines.append(line)

        code_only = "\n".join(code_lines)
        commit_calls = re.findall(r"\.commit\(\)", code_only)
        rollback_calls = re.findall(r"\.rollback\(\)", code_only)
        assert not commit_calls, f"writer.py must not call .commit() in executable code: found {commit_calls}"
        assert not rollback_calls, f"writer.py must not call .rollback() in executable code: found {rollback_calls}"

    def test_no_commit_in_service(self):
        """service.py must contain no executable .commit() or .rollback() calls."""
        import re
        from pathlib import Path
        service_path = Path(__file__).parent.parent / "services" / "ka_muhurta_seva" / "service.py"
        assert service_path.exists(), f"service.py not found at {service_path}"
        source = service_path.read_text()
        code_lines = []
        in_docstring = False
        for line in source.splitlines():
            stripped = line.strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                in_docstring = not in_docstring
                continue
            if in_docstring:
                continue
            if stripped.startswith("#"):
                continue
            code_lines.append(line)
        code_only = "\n".join(code_lines)
        commit_calls = re.findall(r"\.commit\(\)", code_only)
        rollback_calls = re.findall(r"\.rollback\(\)", code_only)
        assert not commit_calls, f"service.py must not call .commit() in executable code: found {commit_calls}"
        assert not rollback_calls, f"service.py must not call .rollback() in executable code: found {rollback_calls}"
