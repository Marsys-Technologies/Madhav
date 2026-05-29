"""
test_vargas_writer.py — Unit tests for vargas_writer A6-S1/S2/S3

Covers compute_varga_sign_id() and is_vargottama() without any DB connection.
Minimum 25 assertions per specification.

Classical references verified against BPHS Ch. 6–7 and varga_formulas.py.
"""
from __future__ import annotations

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pipeline.writers.vargas_writer import (
    compute_varga_sign_id,
    is_vargottama,
    sign_name,
    sign_lord,
    write,
    ALL_VARGAS,
    PARASHARI_VARGAS,
    SUPPLEMENTARY_VARGAS,
    NADI_VARGAS,
    ASSET_ID,
    ASSET_LABEL,
)


# ---------------------------------------------------------------------------
# Sign helpers
# ---------------------------------------------------------------------------

class TestSignHelpers:

    def test_sign_name_aries(self):
        assert sign_name(1) == "Aries"

    def test_sign_name_pisces(self):
        assert sign_name(12) == "Pisces"

    def test_sign_name_capricorn(self):
        assert sign_name(10) == "Capricorn"

    def test_sign_name_wrap(self):
        # 13 wraps to 1 = Aries
        assert sign_name(13) == "Aries"

    def test_sign_lord_aries_is_mars(self):
        assert sign_lord(1) == "Mars"

    def test_sign_lord_leo_is_sun(self):
        assert sign_lord(5) == "Sun"

    def test_sign_lord_capricorn_is_saturn(self):
        assert sign_lord(10) == "Saturn"

    def test_sign_lord_pisces_is_jupiter(self):
        assert sign_lord(12) == "Jupiter"


# ---------------------------------------------------------------------------
# D1 — Rasi (natal sign identity)
# ---------------------------------------------------------------------------

class TestD1Rasi:

    def test_aries_0_deg(self):
        """0.0° is Aries (1)."""
        assert compute_varga_sign_id(0.0, 1) == 1

    def test_aries_29_deg(self):
        """29.9° is still Aries (1)."""
        assert compute_varga_sign_id(29.9, 1) == 1

    def test_taurus_start(self):
        """30.0° is Taurus (2)."""
        assert compute_varga_sign_id(30.0, 1) == 2

    def test_capricorn(self):
        """Sun at 291.96° → Capricorn (10); int(291.96/30)+1=10."""
        assert compute_varga_sign_id(291.96, 1) == 10

    def test_pisces_end(self):
        """359.0° is Pisces (12)."""
        assert compute_varga_sign_id(359.0, 1) == 12


# ---------------------------------------------------------------------------
# D2 — Hora
# ---------------------------------------------------------------------------

class TestD2Hora:

    def test_aries_0_to_15_is_leo(self):
        """Aries (odd sign) 0–15° → Leo (5)."""
        assert compute_varga_sign_id(5.0, 2) == 5    # 5° in Aries

    def test_aries_15_to_30_is_cancer(self):
        """Aries (odd sign) 15–30° → Cancer (4)."""
        assert compute_varga_sign_id(20.0, 2) == 4   # 20° in Aries

    def test_taurus_0_to_15_is_cancer(self):
        """Taurus (even sign) 0–15° → Cancer (4)."""
        assert compute_varga_sign_id(35.0, 2) == 4   # 5° in Taurus

    def test_taurus_15_to_30_is_leo(self):
        """Taurus (even sign) 15–30° → Leo (5)."""
        assert compute_varga_sign_id(50.0, 2) == 5   # 20° in Taurus

    def test_result_always_cancer_or_leo(self):
        """D2 result is always Cancer(4) or Leo(5)."""
        for lon in [0, 7.5, 15, 22.5, 30, 37.5, 45, 52.5, 60]:
            result = compute_varga_sign_id(float(lon), 2)
            assert result in (4, 5), f"D2 for {lon}° gave {result}, expected 4 or 5"


# ---------------------------------------------------------------------------
# D3 — Drekkana (triplicity)
# ---------------------------------------------------------------------------

class TestD3Drekkana:

    def test_aries_5deg_same_sign(self):
        """Aries 5° → section 0 → Aries (1)."""
        assert compute_varga_sign_id(5.0, 3) == 1

    def test_aries_15deg_is_leo(self):
        """Aries 10–20° → 5th from Aries = Leo (5); 0-indexed: (0+1*4)%12=4 → +1=5."""
        assert compute_varga_sign_id(15.0, 3) == 5

    def test_aries_25deg_is_sagittarius(self):
        """Aries 20–30° → 9th from Aries = Sagittarius (9); (0+2*4)%12=8 → +1=9."""
        assert compute_varga_sign_id(25.0, 3) == 9

    def test_cancer_0deg_is_cancer(self):
        """Cancer 0° → same sign = Cancer (4); rasi_idx=3, (3+0)%12+1=4."""
        assert compute_varga_sign_id(90.0, 3) == 4

    def test_cancer_15deg_is_scorpio(self):
        """Cancer 10–20° → Scorpio (8); (3+1*4)%12+1=8."""
        assert compute_varga_sign_id(105.0, 3) == 8

    def test_cancer_25deg_is_pisces(self):
        """Cancer 20–30° → Pisces (12); (3+2*4)%12+1=12."""
        assert compute_varga_sign_id(115.0, 3) == 12


# ---------------------------------------------------------------------------
# D9 — Navamsa (element-based cycle)
# ---------------------------------------------------------------------------

class TestD9Navamsa:

    def test_sun_capricorn_21deg_is_cancer(self):
        """
        Sun at 291.96° → Capricorn (idx=9, earth), degree_in_sign≈21.96°.
        Earth starts from Capricorn (9, 0-indexed).
        section = int(21.96 / 3.333) = 6; (9+6)%12=3 → +1=4 = Cancer.
        """
        assert compute_varga_sign_id(291.96, 9) == 4

    def test_aries_0_navamsa_is_aries(self):
        """Aries 0° (fire, section=0) → Aries navamsa (1)."""
        assert compute_varga_sign_id(0.0, 9) == 1

    def test_aries_3deg20_navamsa_is_taurus(self):
        """Aries ~3.33° (section=1) → Taurus (2)."""
        # 3.333... is exactly 10/3
        assert compute_varga_sign_id(10.0 / 3, 9) == 2

    def test_taurus_0_navamsa_is_capricorn(self):
        """Taurus 0° (earth, section=0) → Capricorn (10)."""
        assert compute_varga_sign_id(30.0, 9) == 10

    def test_gemini_0_navamsa_is_libra(self):
        """Gemini 0° (air, section=0) → Libra (7)."""
        assert compute_varga_sign_id(60.0, 9) == 7

    def test_cancer_0_navamsa_is_cancer(self):
        """Cancer 0° (water, section=0) → Cancer (4)."""
        assert compute_varga_sign_id(90.0, 9) == 4

    def test_leo_0_navamsa_is_aries(self):
        """Leo 0° (fire, section=0) → Aries (1)."""
        assert compute_varga_sign_id(120.0, 9) == 1

    def test_sagittarius_0_navamsa_is_aries(self):
        """Sagittarius 0° (fire, section=0) → Aries (1)."""
        assert compute_varga_sign_id(240.0, 9) == 1

    def test_capricorn_0_navamsa_is_capricorn(self):
        """Capricorn 0° (earth, section=0) → Capricorn (10)."""
        assert compute_varga_sign_id(270.0, 9) == 10

    def test_scorpio_0_navamsa_is_cancer(self):
        """Scorpio 0° (water, section=0) → Cancer (4)."""
        assert compute_varga_sign_id(210.0, 9) == 4

    def test_navamsa_result_always_1_to_12(self):
        """D9 result is always in range 1–12 for various longitudes."""
        for lon in [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 359.9]:
            result = compute_varga_sign_id(float(lon), 9)
            assert 1 <= result <= 12, f"D9 for {lon}° out of range: {result}"


# ---------------------------------------------------------------------------
# D10 — Dasamsa
# ---------------------------------------------------------------------------

class TestD10Dasamsa:

    def test_aries_0deg_is_aries(self):
        """Aries (odd sign) 0° → Aries (1)."""
        assert compute_varga_sign_id(0.0, 10) == 1

    def test_taurus_0deg_is_capricorn(self):
        """Taurus (even sign) 0° → Capricorn (10)."""
        assert compute_varga_sign_id(30.0, 10) == 10

    def test_aries_15deg(self):
        """Aries 15° → part=5 → (0+5)%12+1=6 = Virgo."""
        assert compute_varga_sign_id(15.0, 10) == 6


# ---------------------------------------------------------------------------
# D12 — Dvadasamsa
# ---------------------------------------------------------------------------

class TestD12Dvadasamsa:

    def test_aries_0deg_is_aries(self):
        """Aries 0° → part=0 → Aries (1)."""
        assert compute_varga_sign_id(0.0, 12) == 1

    def test_aries_2deg5_is_taurus(self):
        """Aries 2.5° → part=1 → Taurus (2)."""
        assert compute_varga_sign_id(2.5, 12) == 2

    def test_taurus_0deg_is_taurus(self):
        """Taurus 0° → rasi_idx=1, part=0 → (1+0)%12+1=2 = Taurus."""
        assert compute_varga_sign_id(30.0, 12) == 2

    def test_taurus_2deg5_is_gemini(self):
        """Taurus 2.5° → part=1 → (1+1)%12+1=3 = Gemini."""
        assert compute_varga_sign_id(32.5, 12) == 3


# ---------------------------------------------------------------------------
# Vargottama
# ---------------------------------------------------------------------------

class TestVargottama:

    def test_aries_0deg_is_vargottama(self):
        """
        Aries 0° → D1=Aries(1), D9=Aries(1) → vargottama=True.
        (Fire sign, section 0 → Aries navamsa.)
        """
        assert is_vargottama(0.0) is True

    def test_aries_3deg35_not_vargottama(self):
        """
        Aries 3.5° → D1=Aries(1), D9=Taurus(2) → vargottama=False.
        """
        assert is_vargottama(3.5) is False

    def test_taurus_0deg_is_vargottama(self):
        """
        Taurus 0° → D1=Taurus(2), D9=Capricorn(10) → not vargottama.
        """
        assert is_vargottama(30.0) is False

    def test_capricorn_0deg_is_vargottama(self):
        """
        Capricorn 0° → D1=Capricorn(10), D9=Capricorn(10) → vargottama=True.
        Earth sign starts D9 from Capricorn, section 0 → Capricorn(10).
        """
        assert is_vargottama(270.0) is True

    def test_cancer_0deg_is_vargottama(self):
        """
        Cancer 0° → D1=Cancer(4), D9=Cancer(4) → vargottama=True.
        Water sign starts D9 from Cancer, section 0 → Cancer(4).
        """
        assert is_vargottama(90.0) is True

    def test_libra_0deg_is_vargottama(self):
        """
        Libra 0° → D1=Libra(7), D9=Libra(7) → vargottama=True.
        Air sign starts D9 from Libra, section 0 → Libra(7).
        """
        assert is_vargottama(180.0) is True


# ---------------------------------------------------------------------------
# Other vargas: range correctness
# ---------------------------------------------------------------------------

class TestVargaRangeCorrectness:

    @pytest.mark.parametrize("divisor", ALL_VARGAS)
    def test_result_in_range_1_to_12(self, divisor):
        """For all vargas and sample longitudes, result must be 1–12."""
        test_lons = [0.0, 15.0, 30.0, 45.5, 90.0, 150.7, 180.0, 270.0, 291.96, 359.0]
        for lon in test_lons:
            result = compute_varga_sign_id(lon, divisor)
            assert 1 <= result <= 12, (
                f"D{divisor} for lon={lon} returned {result} (out of 1–12)"
            )

    @pytest.mark.parametrize("divisor", SUPPLEMENTARY_VARGAS)
    def test_supplementary_vargas_not_constant(self, divisor):
        """Supplementary vargas should produce different results for different signs."""
        results = {compute_varga_sign_id(float(s * 30), divisor) for s in range(12)}
        assert len(results) > 1, (
            f"D{divisor} returns same value for all sign starts — likely a bug"
        )

    @pytest.mark.parametrize("divisor", NADI_VARGAS)
    def test_nadi_vargas_in_range(self, divisor):
        """Nadi vargas (D108, D150, D2700) stay in 1–12."""
        for lon in [0.0, 90.0, 180.0, 270.0, 0.01, 29.99]:
            result = compute_varga_sign_id(lon, divisor)
            assert 1 <= result <= 12, (
                f"D{divisor} for lon={lon} returned {result}"
            )


# ---------------------------------------------------------------------------
# D6 Shashtamsa
# ---------------------------------------------------------------------------

class TestD6Shashtamsa:

    def test_aries_0deg_is_aries(self):
        """Aries (odd) 0° → part=0, start=Aries(0) → Aries(1)."""
        assert compute_varga_sign_id(0.0, 6) == 1

    def test_taurus_0deg_is_libra(self):
        """Taurus (even) 0° → part=0, start=Libra(6) → Libra(7)."""
        assert compute_varga_sign_id(30.0, 6) == 7


# ---------------------------------------------------------------------------
# D30 Trimsamsa (unequal divisions)
# ---------------------------------------------------------------------------

class TestD30Trimsamsa:

    def test_aries_3deg_is_aries(self):
        """Aries (odd sign) 3° → Mars → Aries(1)."""
        assert compute_varga_sign_id(3.0, 30) == 1

    def test_aries_7deg_is_aquarius(self):
        """Aries (odd sign) 7° → Saturn → Aquarius(11)."""
        assert compute_varga_sign_id(7.0, 30) == 11

    def test_aries_14deg_is_sagittarius(self):
        """Aries (odd sign) 14° → Jupiter → Sagittarius(9)."""
        assert compute_varga_sign_id(14.0, 30) == 9

    def test_aries_20deg_is_gemini(self):
        """Aries (odd sign) 20° → Mercury → Gemini(3)."""
        assert compute_varga_sign_id(20.0, 30) == 3

    def test_aries_27deg_is_libra(self):
        """Aries (odd sign) 27° → Venus → Libra(7)."""
        assert compute_varga_sign_id(27.0, 30) == 7

    def test_taurus_3deg_is_taurus(self):
        """Taurus (even sign) 3° → Venus → Taurus(2)."""
        assert compute_varga_sign_id(33.0, 30) == 2

    def test_taurus_8deg_is_virgo(self):
        """Taurus (even sign) 8° → Mercury → Virgo(6)."""
        assert compute_varga_sign_id(38.0, 30) == 6


# ---------------------------------------------------------------------------
# write() row-count smoke (conn=None → dry-run returns rows, not 0)
# ---------------------------------------------------------------------------

class TestWriteRowCount:

    def _make_chart_output(self, n_grahas: int = 9) -> dict:
        grahas = []
        planet_names = [
            "Sun", "Moon", "Mars", "Mercury", "Jupiter",
            "Venus", "Saturn", "Rahu", "Ketu",
        ]
        for i in range(n_grahas):
            lon = float(i * 30 + 5)  # spread across signs
            grahas.append({
                "name": planet_names[i],
                "longitude_deg": lon,
                "sign": sign_name(int(lon / 30) + 1),
                "sign_id": int(lon / 30) + 1,
                "varga_position": {},
            })
        return {"grahas": grahas}

    def test_empty_chart_returns_zero(self):
        result = write(
            build_id="test-build",
            chart_id="test-chart",
            ayanamsha_id="lahiri",
            chart_output={},
            conn=None,
        )
        assert result == 0

    def test_empty_grahas_returns_zero(self):
        result = write(
            build_id="test-build",
            chart_id="test-chart",
            ayanamsha_id="lahiri",
            chart_output={"grahas": []},
            conn=None,
        )
        assert result == 0

    def test_9_grahas_row_count(self):
        """
        9 grahas × 30 vargas × 3 base facts = 270
        + 9 vargottama rows (D9 only) = 9
        Total expected = 279
        """
        chart_output = self._make_chart_output(9)
        result = write(
            build_id="test-build",
            chart_id="test-chart-uuid-1234",
            ayanamsha_id="lahiri",
            chart_output=chart_output,
            conn=None,
        )
        expected = 9 * 30 * 3 + 9  # 270 + 9 = 279
        assert result == expected, f"Expected {expected} rows, got {result}"

    def test_1_graha_row_count(self):
        """1 graha × 30 vargas × 3 facts + 1 vargottama = 91."""
        chart_output = self._make_chart_output(1)
        result = write(
            build_id="test-build",
            chart_id="test-chart-uuid-0001",
            ayanamsha_id="lahiri",
            chart_output=chart_output,
            conn=None,
        )
        expected = 1 * 30 * 3 + 1  # 90 + 1 = 91
        assert result == expected, f"Expected {expected} rows, got {result}"

    def test_extra_kwarg_accepted(self):
        """write() accepts optional extra kwarg without raising."""
        chart_output = self._make_chart_output(1)
        result = write(
            build_id="test-build",
            chart_id="test-chart-extra",
            ayanamsha_id="kp",
            chart_output=chart_output,
            conn=None,
            extra={"context": "test"},
        )
        assert result > 0


# ---------------------------------------------------------------------------
# Module constants
# ---------------------------------------------------------------------------

class TestModuleConstants:

    def test_asset_id(self):
        assert ASSET_ID == "A6_vargas"

    def test_asset_label(self):
        assert ASSET_LABEL == "Varga Divisional Charts"

    def test_all_vargas_length(self):
        """16 Parashari + 11 supplementary + 3 Nadi = 30."""
        assert len(ALL_VARGAS) == 30

    def test_parashari_vargas_count(self):
        assert len(PARASHARI_VARGAS) == 16

    def test_supplementary_vargas_count(self):
        assert len(SUPPLEMENTARY_VARGAS) == 11

    def test_nadi_vargas_count(self):
        assert len(NADI_VARGAS) == 3

    def test_d9_in_parashari(self):
        assert 9 in PARASHARI_VARGAS

    def test_d30_in_parashari(self):
        assert 30 in PARASHARI_VARGAS

    def test_d108_in_nadi(self):
        assert 108 in NADI_VARGAS

    def test_d2700_in_nadi(self):
        assert 2700 in NADI_VARGAS
