"""
Tests for pipeline.panchanga_derivations — pure-function panchanga computation.

All tests use known inputs with analytically deterministic expected outputs.
No external dependencies (no swisseph, no DB).
"""
import pytest
from datetime import datetime

from pipeline.panchanga_derivations import (
    compute_tithi,
    compute_vara,
    compute_moon_nakshatra,
    compute_yoga,
    compute_karana,
    TITHI_NAMES,
    NAKSHATRAS,
    VARA_NAMES,
    VARA_LORDS,
    YOGAS,
    MOVABLE_KARANAS,
    FIXED_KARANA_POSITIONS,
    TITHI_ARC_DEG,
    NAK_SPAN,
    YOGA_ARC_DEG,
)


# ── compute_tithi ──────────────────────────────────────────────────────────────

class TestComputeTithi:
    def test_tithi_amavasya_near_0deg_diff(self):
        """Near-zero elongation → tithi 30 (Amavasya), krishna paksha."""
        # diff = 0.5° → tithi_fraction = 0.5/12 ≈ 0.0417 → tithi_index = 1 = Shukla Pratipada
        # To get Amavasya (30), we need diff ≈ 358° (just under 360° - 12° = 348°..360°)
        # diff=354° → tithi_fraction=354/12=29.5 → int=29 → index=30
        sun_lon = 5.0
        moon_lon = (5.0 + 354.0) % 360.0
        tithi_idx, name, paksha, frac = compute_tithi(sun_lon, moon_lon)
        assert tithi_idx == 30
        assert name == "Krishna Amavasya"
        assert paksha == "krishna"
        assert 29.0 <= frac < 30.0

    def test_tithi_purnima_at_midpoint(self):
        """174° elongation (midpoint of tithi 15) → Purnima, shukla paksha.
        Note: diff=180° is the exact boundary → tithi 16 (Krishna Pratipada).
        Purnima covers elongation [168°, 180°) — use 174° for reliable midpoint test.
        """
        tithi_idx, name, paksha, frac = compute_tithi(0.0, 174.0)
        assert tithi_idx == 15
        assert name == "Shukla Purnima"
        assert paksha == "shukla"
        assert 14.0 <= frac < 15.0

    def test_tithi_shukla_pratipada_just_after_amavasya(self):
        """1° elongation → tithi 1 (Shukla Pratipada)."""
        tithi_idx, name, paksha, frac = compute_tithi(0.0, 1.0)
        assert tithi_idx == 1
        assert name == "Shukla Pratipada"
        assert paksha == "shukla"

    def test_tithi_name_canonical_ekadashi(self):
        """tithi_index=11 → 'Shukla Ekadashi'; tithi_index=26 → 'Krishna Ekadashi'."""
        # Shukla Ekadashi: diff = (11-1)*12 + 6 = 126° (midpoint of tithi 11)
        _, name_s, _, _ = compute_tithi(0.0, 126.0)
        assert name_s == "Shukla Ekadashi"
        # Krishna Ekadashi: diff = (26-1)*12 + 6 = 306°
        _, name_k, _, _ = compute_tithi(0.0, 306.0)
        assert name_k == "Krishna Ekadashi"

    def test_paksha_boundary_tithi_15_is_shukla(self):
        """tithi_index=15 → paksha 'shukla'."""
        tithi_idx, _, paksha, _ = compute_tithi(0.0, 174.0)  # 174/12=14.5 → idx=15
        assert tithi_idx == 15
        assert paksha == "shukla"

    def test_paksha_boundary_tithi_16_is_krishna(self):
        """tithi_index=16 → paksha 'krishna'."""
        tithi_idx, _, paksha, _ = compute_tithi(0.0, 184.0)  # 184/12≈15.33 → idx=16
        assert tithi_idx == 16
        assert paksha == "krishna"

    def test_tithi_fraction_monotone(self):
        """tithi_fraction increases as elongation increases."""
        _, _, _, frac_a = compute_tithi(0.0, 60.0)
        _, _, _, frac_b = compute_tithi(0.0, 120.0)
        assert frac_b > frac_a

    def test_tithi_wraps_correctly_at_360(self):
        """Elongation of 359.9° → Amavasya (tithi 30)."""
        tithi_idx, _, _, _ = compute_tithi(0.0, 359.9)
        assert tithi_idx == 30


# ── compute_vara ───────────────────────────────────────────────────────────────

class TestComputeVara:
    def test_sunday_is_ravivara(self):
        """IST sunrise on a Sunday → vara_index=0, Ravivara, lord=Sun."""
        sunday = datetime(2026, 5, 17, 6, 10, 0)   # 2026-05-17 is a Sunday
        vara_idx, vara_name, vara_lord = compute_vara(sunday)
        assert vara_idx == 0
        assert vara_name == "Ravivara"
        assert vara_lord == "Sun"

    def test_saturday_is_shanivara(self):
        """IST sunrise on a Saturday → vara_index=6, Shanivara, lord=Saturn."""
        saturday = datetime(2026, 5, 16, 6, 10, 0)  # 2026-05-16 is a Saturday
        vara_idx, vara_name, vara_lord = compute_vara(saturday)
        assert vara_idx == 6
        assert vara_name == "Shanivara"
        assert vara_lord == "Saturn"

    def test_monday_is_somavara(self):
        """IST sunrise on a Monday → vara_index=1, Somavara, lord=Moon."""
        monday = datetime(2026, 5, 18, 6, 8, 0)    # 2026-05-18 is a Monday
        vara_idx, vara_name, vara_lord = compute_vara(monday)
        assert vara_idx == 1
        assert vara_name == "Somavara"
        assert vara_lord == "Moon"

    def test_vara_names_complete(self):
        """All 7 VARA_NAMES and VARA_LORDS are present and ordered."""
        assert len(VARA_NAMES) == 7
        assert len(VARA_LORDS) == 7
        assert VARA_NAMES[0] == "Ravivara"
        assert VARA_LORDS[6] == "Saturn"


# ── compute_moon_nakshatra ─────────────────────────────────────────────────────

class TestComputeMoonNakshatra:
    def test_ashwini_at_0deg(self):
        """Moon at 0° sidereal → Ashwini, index=0, pada=1."""
        name, idx, pada = compute_moon_nakshatra(0.0)
        assert name == "Ashwini"
        assert idx == 0
        assert pada == 1

    def test_ashwini_pada_2(self):
        """Moon at 3.5° (past 3.333° boundary) → Ashwini pada 2."""
        _, _, pada = compute_moon_nakshatra(3.5)
        assert pada == 2

    def test_revati_just_below_360(self):
        """Moon at 359.9° → Revati, index=26, pada=4."""
        name, idx, pada = compute_moon_nakshatra(359.9)
        assert name == "Revati"
        assert idx == 26
        assert pada == 4

    def test_nakshatra_count(self):
        """27 nakshatras defined."""
        assert len(NAKSHATRAS) == 27
        assert NAKSHATRAS[0] == "Ashwini"
        assert NAKSHATRAS[26] == "Revati"

    def test_pada_boundary(self):
        """Each pada spans NAK_SPAN/4 ≈ 3.333°. Moon at exactly NAK_SPAN → second nakshatra pada 1."""
        name, idx, pada = compute_moon_nakshatra(NAK_SPAN)
        assert idx == 1           # second nakshatra
        assert pada == 1          # first pada of second nakshatra


# ── compute_yoga ──────────────────────────────────────────────────────────────

class TestComputeYoga:
    def test_vishkumbha_at_small_sum(self):
        """(Sun+Moon) % 360 = 5° → Vishkumbha (yoga 1)."""
        yoga_idx, yoga_name = compute_yoga(3.0, 2.0)
        assert yoga_idx == 1
        assert yoga_name == "Vishkumbha"

    def test_vaidhriti_just_below_360(self):
        """(Sun+Moon) % 360 ≈ 355° → Vaidhriti (yoga 27)."""
        yoga_idx, yoga_name = compute_yoga(200.0, 155.0)  # sum=355
        assert yoga_idx == 27
        assert yoga_name == "Vaidhriti"

    def test_priti_second_yoga(self):
        """Combined ≈ 14° → Priti (yoga 2)."""
        yoga_idx, yoga_name = compute_yoga(7.0, 7.5)   # sum=14.5
        assert yoga_idx == 2
        assert yoga_name == "Priti"

    def test_yoga_count(self):
        """27 yogas defined."""
        assert len(YOGAS) == 27
        assert YOGAS[0] == "Vishkumbha"
        assert YOGAS[26] == "Vaidhriti"

    def test_yoga_wraps_at_360(self):
        """Sum of exactly 360° wraps to yoga 1 (Vishkumbha)."""
        yoga_idx, _ = compute_yoga(180.0, 180.0)   # sum=360 % 360 = 0
        assert yoga_idx == 1


# ── compute_karana ─────────────────────────────────────────────────────────────

class TestComputeKarana:
    def test_kintughna_first_half_shukla_pratipada(self):
        """tithi_fraction=0.3 → position 0 → Kintughna (fixed)."""
        pos, name = compute_karana(0.3)
        assert pos == 0
        assert name == "Kintughna"

    def test_bava_second_half_shukla_pratipada(self):
        """tithi_fraction=0.7 → position 1 → Bava (first movable)."""
        pos, name = compute_karana(0.7)
        assert pos == 1
        assert name == "Bava"

    def test_shakuni_krishna_chaturdashi_second_half(self):
        """tithi_fraction=28.7 → position=int(28.7*2)=57 → Shakuni (fixed)."""
        pos, name = compute_karana(28.7)
        assert pos == 57
        assert name == "Shakuni"

    def test_catushpada_first_half_krishna_amavasya(self):
        """tithi_fraction=29.1 → position=int(29.1*2)=58 → Catushpada (fixed)."""
        pos, name = compute_karana(29.1)
        assert pos == 58
        assert name == "Catushpada"

    def test_naga_second_half_krishna_amavasya(self):
        """tithi_fraction=29.6 → position=int(29.6*2)=59 → Naga (fixed)."""
        pos, name = compute_karana(29.6)
        assert pos == 59
        assert name == "Naga"

    def test_movable_repeats_every_7(self):
        """Movable karanas cycle every 7. Position 8 = Bava (same as position 1)."""
        # position 8: (8-1)%7=0 → Bava
        pos, name = compute_karana(4.1)   # int(4.1*2)=8
        assert pos == 8
        assert name == "Bava"

    def test_movable_cycle_at_position_15(self):
        """Position 15: (15-1)%7=0 → Bava."""
        pos, name = compute_karana(7.6)   # int(7.6*2)=15
        assert pos == 15
        assert name == "Bava"

    def test_fixed_positions_complete(self):
        """All 4 fixed karana positions are defined."""
        assert set(FIXED_KARANA_POSITIONS.keys()) == {0, 57, 58, 59}

    def test_movable_karanas_count(self):
        """7 movable karanas defined."""
        assert len(MOVABLE_KARANAS) == 7
        assert MOVABLE_KARANAS[0] == "Bava"
        assert MOVABLE_KARANAS[6] == "Vishti"
