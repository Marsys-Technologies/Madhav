"""
test_nirmana_nir11_qualification_matrix.py — NIR-11 Jyotish Numerical Control Qualification Matrix
==================================================================================================
Fast, deterministic, offline (no DB) qualification suite directly exercising the real
production Python modules in `platform/python-sidecar/` across all 8 NIR-11 domains:

  1. Parāśari D10 (daśāṃśa) & D9 (navāṃśa) controls across all 12 signs & boundaries
  2. Pre-sunrise vs post-sunrise vāra (Vedic weekday) across IST/UTC/US-Pacific & 2020-02-29
  3. Yogakāraka across all 12 ascendants ({4,7,10} ∩ {5,9} vs 9+10) + Dharma-Karmādhipati + L1→Bodha trace
  4. All 10 tārā-graha Planetary War (graha-yuddha) pairs + non-tārā exclusion + JL-026/JL-027/PR #4016
  5. Śrīpati bhāva cusps, madhyas, sandhis, semi-arc trisection, and 360° circuit symmetry
  6. Sign-level Bhinna-Aṣṭakavarga (BAV) & Sarvāṣṭakavarga (SAV=337), prastara, & trikoṇa/ekādhipatya śodhana
  7. Hora Lagna (0.5°/min), Ghaṭī Lagna (1.25°/min), Bhava Lagna (0.25°/min), & classical sphuṭas
  8. Lunar nakṣatra/pāda (27×4) boundaries & Vimśottarī daśā balance + gap-free MD→AD contiguity
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from itertools import combinations
import json
from math import isclose
from unittest.mock import MagicMock

import pytest
import swisseph as swe

from bodha_writers.formulas import ResonanceInputs, resonance_score_v1
from brahmagyan.l0_yogas import YOGAS_CORE
from ga_writers import ga_condition_writer as gcw
from ga_writers import ga_dashas_writer as gdw
from ga_writers import ga_panchanga_writer as gpw
from ga_writers import ga_sade_sati_writer as gssw
from ga_writers import ga_sensitive_writer as gsens
from ga_writers import ga_strength_writer as gstr
from ga_writers import ga_structural_writer as gsw
from ga_writers import ga_vargas_writer as gvw
from ga_writers import ga_yoga_writer as gyw
from ga_writers._vimshottari_independent_verifier import derive_birth_nakshatra_period
from ga_writers.ga_nakshatra_compute import (
    PLANET_CYCLE,
    VIMSHOTTARI_YEARS,
    _nakshatra_0based,
    compute_kp_lords,
)
from panchang_engine import panchanga_instant
from panchang_engine.timings import compute_sunrise_sunset
from pipeline.orchestrator.writers import bo_laksana
from pyjhora_adapter._jhora import drik, utils
from pyjhora_adapter.houses import compute_ascendant, compute_bhava_chalit, compute_midheaven
from pyjhora_adapter.panchanga import compute_panchanga as pyjhora_compute_panchanga
from pyjhora_adapter.special_lagnas import (
    bhava_lagna,
    compute_special_lagnas,
    ghati_lagna,
    hora_lagna,
)
from pyjhora_adapter.strength import compute_ashtakavarga_shodhana
from pyjhora_adapter.vargas import compute_vargas, parashari_d10

CHART_ID = "00000000-0000-4000-8000-000000000011"
BUILD_ID = "nir11-qual-build-001"
AY_ID = "lahiri_chitrapaksha"
ENG_VER = "pyjhora_adapter/0.1.0"
COMPUTED_AT = "2026-11-21T00:00:00+00:00"

NATIVE_DOB = drik.Date(1984, 2, 5)
NATIVE_TOB = (10, 43, 0)
NATIVE_LAT = 20.27
NATIVE_LON = 85.84
NATIVE_TZ_HR = 5.5
NATIVE_JD_LOCAL = utils.julian_day_number(NATIVE_DOB, NATIVE_TOB)

SIGN_NAMES = gsw.SIGN_NAMES


def _arc_forward(a: float, b: float) -> float:
    return (b - a) % 360.0


def _arc_shortest(a: float, b: float) -> float:
    d = abs((a - b) % 360.0)
    return min(d, 360.0 - d)


# =============================================================================
# DOMAIN 1: Parāśari D10 (Daśāṃśa) & D9 (Navāṃśa) Controls
# =============================================================================


class TestDomain1ParashariD10AndD9Controls:
    """All 12 signs × 10 D10 parts + 9 D9 parts + exact boundaries + ephemeris integration."""

    @pytest.mark.parametrize("sign_idx", range(12))
    def test_d10_all_12_signs_all_10_parts_parashari_rule(self, sign_idx: int):
        # Classical 1-based odd signs (Aries=1, Gemini=3, ...) have even 0-based indices:
        # start from same sign; even signs (Taurus=2, ...) start from 9th therefrom (+8).
        is_classical_odd = (sign_idx % 2 == 0)
        expected_start = sign_idx if is_classical_odd else (sign_idx + 8) % 12

        for part in range(10):
            natal_deg = part * 3.0 + 1.5
            d10_sign, d10_deg = parashari_d10(sign_idx, natal_deg)
            assert d10_sign == (expected_start + part) % 12
            assert isclose(d10_deg, 15.0, abs_tol=1e-9)

    @pytest.mark.parametrize("sign_idx", range(12))
    @pytest.mark.parametrize(
        ("deg_in_sign", "expected_part", "expected_offset"),
        [
            (0.0, 0, 0.0),
            (2.999999, 0, 2.999999),
            (3.0, 1, 0.0),
            (15.0, 5, 0.0),
            (29.99, 9, 2.99),
            (30.0 - 1e-9, 9, 3.0 - 1e-9),
        ],
    )
    def test_d10_boundary_longitudes_across_all_signs(
        self, sign_idx: int, deg_in_sign: float, expected_part: int, expected_offset: float
    ):
        expected_start = sign_idx if (sign_idx % 2 == 0) else (sign_idx + 8) % 12
        d10_sign, d10_deg = parashari_d10(sign_idx, deg_in_sign)
        assert d10_sign == (expected_start + expected_part) % 12
        assert isclose(d10_deg, expected_offset * 10.0, abs_tol=1e-6)
        assert 0.0 <= d10_deg < 30.0

    def test_compute_vargas_d10_matches_parashari_d10_from_d1(self):
        vargas = compute_vargas(
            NATIVE_JD_LOCAL, "lahiri", lat=NATIVE_LAT, lon=NATIVE_LON, tz=NATIVE_TZ_HR
        )
        d1 = {row["name"]: row for row in vargas["D1"]}
        d10 = {row["name"]: row for row in vargas["D10"]}
        assert set(d1.keys()) == set(d10.keys())
        for body, d1_row in d1.items():
            exp_sign, exp_deg = parashari_d10(d1_row["sign_id"] - 1, d1_row["degree_in_sign"])
            assert d10[body]["sign_id"] == exp_sign + 1
            assert isclose(d10[body]["degree_in_sign"], exp_deg, abs_tol=1e-9)

    @pytest.mark.parametrize("sign_idx", range(12))
    def test_d9_navamsa_all_12_signs_all_9_parts_and_trikona_starts(self, sign_idx: int):
        # Movable (0,3,6,9)->Aries(0); Fixed (1,4,7,10)->Capricorn(9); Dual (2,5,8,11)->Cancer(3)
        expected_start = {0: 0, 1: 9, 2: 6, 3: 3}[sign_idx % 4]
        navamsa_span = 30.0 / 9.0
        for pada0 in range(9):
            lon = sign_idx * 30.0 + (pada0 + 0.5) * navamsa_span
            expected_sign = (expected_start + pada0) % 12
            assert gvw._compute_d9_navamsa(lon) == expected_sign
            assert gvw._compute_general_varga(lon, 9) == expected_sign

    @pytest.mark.parametrize("sign_idx", range(12))
    @pytest.mark.parametrize(
        ("deg_in_sign", "expected_pada0"),
        [
            (0.0, 0),
            (30.0 / 9.0 - 1e-7, 0),
            (30.0 / 9.0 + 1e-7, 1),
            (15.0, 4),
            (29.99, 8),
            (30.0 - 1e-9, 8),
        ],
    )
    def test_d9_boundary_longitudes_and_vargottama_positions(
        self, sign_idx: int, deg_in_sign: float, expected_pada0: int
    ):
        expected_start = {0: 0, 1: 9, 2: 6, 3: 3}[sign_idx % 4]
        lon = sign_idx * 30.0 + deg_in_sign
        assert gvw._compute_d9_navamsa(lon) == (expected_start + expected_pada0) % 12
        # Vargottama occurs in pada0 == 0 (movable), 4 (fixed), 8 (dual)
        vargottama_pada = {0: 0, 1: 4, 2: 8}[sign_idx % 3]
        varg_lon = sign_idx * 30.0 + (vargottama_pada + 0.5) * (30.0 / 9.0)
        assert gvw._compute_d9_navamsa(varg_lon) == sign_idx

    def test_compute_vargas_d9_matches_ga_vargas_writer_d9(self):
        vargas = compute_vargas(
            NATIVE_JD_LOCAL, "lahiri", lat=NATIVE_LAT, lon=NATIVE_LON, tz=NATIVE_TZ_HR
        )
        d1 = {row["name"]: row for row in vargas["D1"]}
        d9 = {row["name"]: row for row in vargas["D9"]}
        for body, d1_row in d1.items():
            lon = (d1_row["sign_id"] - 1) * 30.0 + d1_row["degree_in_sign"]
            assert d9[body]["sign_id"] == gvw._compute_d9_navamsa(lon) + 1


# =============================================================================
# DOMAIN 2: Pre-Sunrise vs Post-Sunrise Vāra (Vedic Weekday)
# =============================================================================


class TestDomain2PreVsPostSunriseVara:
    """Real ephemeris sunrise transitions across IST, UTC, US/Pacific, and 2020-02-29."""

    @pytest.mark.parametrize(
        ("label", "local_date", "lat", "lon", "tz_min", "expected_pre", "expected_post"),
        [
            ("IST_2024_05_19", date(2024, 5, 19), 20.27, 85.84, 330, "Shanivara", "Ravivara"),
            ("UTC_2024_05_19", date(2024, 5, 19), 51.5074, -0.1278, 0, "Shanivara", "Ravivara"),
            ("US_Pacific_PDT", date(2024, 5, 19), 37.7749, -122.4194, -420, "Shanivara", "Ravivara"),
            ("US_Pacific_PST", date(2024, 1, 15), 37.7749, -122.4194, -480, "Ravivara", "Somavara"),
            ("Leap_2020_02_29", date(2020, 2, 29), 20.27, 85.84, 330, "Shukravara", "Shanivara"),
            ("PostLeap_2020_03_01", date(2020, 3, 1), 20.27, 85.84, 330, "Shanivara", "Ravivara"),
        ],
    )
    def test_panchanga_instant_vara_transitions_across_sunrise_and_timezones(
        self,
        label: str,
        local_date: date,
        lat: float,
        lon: float,
        tz_min: int,
        expected_pre: str,
        expected_post: str,
    ):
        sr_utc, ss_utc = compute_sunrise_sunset(local_date, lat, lon, tz_min)
        assert sr_utc < ss_utc
        sr_local_naive = sr_utc.replace(tzinfo=None) + timedelta(minutes=tz_min)
        assert sr_local_naive.date() == local_date, f"{label}: local sunrise date drifted"

        # 2 seconds before vs 2 seconds after Drik sunrise
        pi_pre = panchanga_instant(sr_local_naive - timedelta(seconds=2), lat, lon, tz_min)
        pi_post = panchanga_instant(sr_local_naive + timedelta(seconds=2), lat, lon, tz_min)
        # Exactly at sunrise instant (inclusive >= sunrise_utc belongs to civil day)
        pi_at = panchanga_instant(sr_local_naive, lat, lon, tz_min)

        assert pi_pre.vara.name == expected_pre
        assert pi_post.vara.name == expected_post
        assert pi_at.vara.name == expected_post

        # Verify ga_panchanga_writer._emit_vara preserves the computed vara verbatim
        rows_pre = gpw._emit_vara(pi_pre, CHART_ID, BUILD_ID, COMPUTED_AT)
        rows_post = gpw._emit_vara(pi_post, CHART_ID, BUILD_ID, COMPUTED_AT)
        pre_map = {r["fact_key"]: r for r in rows_pre}
        post_map = {r["fact_key"]: r for r in rows_post}
        assert pre_map["name"]["fact_value_text"] == expected_pre
        assert post_map["name"]["fact_value_text"] == expected_post
        assert int(post_map["number"]["fact_value_num"]) == pi_post.vara.id

    def test_native_anchor_and_pyjhora_sunrise_vara_transition(self):
        # Canonical native birth: 1984-02-05 10:43 IST -> Ravivara (id=1)
        pi_native = panchanga_instant(
            datetime(1984, 2, 5, 10, 43, 0), NATIVE_LAT, NATIVE_LON, 330
        )
        assert pi_native.vara.name == "Ravivara"
        assert pi_native.vara.id == 1

        # Cross-check pyjhora_adapter.panchanga against drik.sunrise on leap day 2020-02-29
        place = drik.Place("Bhubaneswar", NATIVE_LAT, NATIVE_LON, NATIVE_TZ_HR)
        jd_noon = utils.julian_day_number(drik.Date(2020, 2, 29), (12, 0, 0))
        sr_hr = float(drik.sunrise(jd_noon, place)[0])
        sr_sec = int(round(sr_hr * 3600))
        sr_dt = datetime(2020, 2, 29) + timedelta(seconds=sr_sec)
        pre_dt = sr_dt - timedelta(seconds=10)
        post_dt = sr_dt + timedelta(seconds=10)

        jd_pre = utils.julian_day_number(
            drik.Date(pre_dt.year, pre_dt.month, pre_dt.day),
            (pre_dt.hour, pre_dt.minute, pre_dt.second),
        )
        jd_post = utils.julian_day_number(
            drik.Date(post_dt.year, post_dt.month, post_dt.day),
            (post_dt.hour, post_dt.minute, post_dt.second),
        )
        assert pyjhora_compute_panchanga(
            jd_pre, "lahiri", lat=NATIVE_LAT, lon=NATIVE_LON, tz=NATIVE_TZ_HR
        )["vara"] == "Shukravara"
        assert pyjhora_compute_panchanga(
            jd_post, "lahiri", lat=NATIVE_LAT, lon=NATIVE_LON, tz=NATIVE_TZ_HR
        )["vara"] == "Shanivara"


# =============================================================================
# DOMAIN 3: Yogakāraka Across All 12 Ascendants + L1 → Bodha Trace
# =============================================================================


class TestDomain3YogakarakaAll12AscendantsAndBodhaTrace:
    """Verify {4,7,10} ∩ {5,9} vs 9+10 vs Dharma-Karmādhipati and L1 -> Bodha MSR trace."""

    EXPECTED_KENDRA_TRIKONA_YOGAKARAKA = {
        "Aries": set(),
        "Taurus": {"SAT"},
        "Gemini": set(),
        "Cancer": {"MAR"},
        "Leo": {"MAR"},
        "Virgo": set(),
        "Libra": {"SAT"},
        "Scorpio": set(),
        "Sagittarius": set(),
        "Capricorn": {"VEN"},
        "Aquarius": {"VEN"},
        "Pisces": set(),
    }

    @pytest.mark.parametrize(("sign_idx", "lagna_sign"), list(enumerate(SIGN_NAMES)))
    def test_yogakaraka_all_12_ascendants_l1_and_sade_sati_consistency(
        self, sign_idx: int, lagna_sign: str
    ):
        expected = self.EXPECTED_KENDRA_TRIKONA_YOGAKARAKA[lagna_sign]
        chart_output = {"ascendant": {"sign_id": sign_idx + 1, "sign": lagna_sign}}
        rows = gsw._build_functional_class_rows(
            chart_output, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )

        # 1. {4,7,10} ∩ {5,9} flag: has_kendra_trikona_lordship
        kt_true = {
            r["fact_subject"]
            for r in rows
            if r["fact_key"] == "has_kendra_trikona_lordship" and r["fact_value_text"] == "true"
        }
        assert kt_true == expected

        # 2. Narrow 9+10 flag: is_yoga_karaka (only Taurus has lord_9 == lord_10 == Saturn)
        narrow_true = {
            r["fact_subject"]
            for r in rows
            if r["fact_key"] == "is_yoga_karaka" and r["fact_value_text"] == "true"
        }
        assert narrow_true == ({"SAT"} if lagna_sign == "Taurus" else set())

        # 3. BPHS dynamic functional class & Raman variant agree on the exact 6 yogakarakas
        dyn_yk = {
            gsw.PLANET_TO_SUBJECT[g]
            for g in gsw.CLASSICAL_GRAHAS
            if gsw._get_functional_class_dynamic(g, lagna_sign) == "yogakaraka"
        }
        raman_yk = {
            r["fact_subject"]
            for r in rows
            if r["fact_key"] == "raman_variant" and r["fact_value_text"] == "yogakaraka"
        }
        assert dyn_yk == expected
        assert raman_yk == expected

        # 4. ga_sade_sati_writer.YOGA_KARAKA_BY_LAGNA agrees 1:1
        ss_yk = gssw.YOGA_KARAKA_BY_LAGNA.get(lagna_sign)
        if expected:
            assert {gsw.PLANET_TO_SUBJECT[ss_yk]} == expected
        else:
            assert ss_yk is None

    def test_aries_has_no_single_yogakaraka_but_fires_9_plus_10_dharma_karmadhipati_pair(self):
        # Aries: 9th lord = Jupiter, 10th lord = Saturn -> two-planet Dharma-Karmadhipati yoga
        dk_catalog = next(y for y in YOGAS_CORE if y["canonical_id"] == "dharma_karmadhipati")

        def _make_state(placements: dict[str, str]) -> gyw.ChartState:
            facts = [{
                "fact_id": "f_lagna",
                "fact_subject": "lagna",
                "fact_category": "graha_position",
                "fact_key": "sign",
                "fact_value_text": "aries",
                "fact_value_num": None,
            }]
            for planet, sign in placements.items():
                sign_l = sign.lower()
                house = ((gyw.SIGN_NUMBERS[sign_l] - gyw.SIGN_NUMBERS["aries"]) % 12) + 1
                facts.append({
                    "fact_id": f"f_{planet}_h",
                    "fact_subject": planet,
                    "fact_category": "graha_position",
                    "fact_key": "house_d1",
                    "fact_value_num": house,
                    "fact_value_text": None,
                })
                facts.append({
                    "fact_id": f"f_{planet}_s",
                    "fact_subject": planet,
                    "fact_category": "graha_position",
                    "fact_key": "sign",
                    "fact_value_text": sign_l,
                    "fact_value_num": None,
                })
            return gyw.ChartState(facts)

        # Conjunction of 9th lord Jupiter and 10th lord Saturn in Sagittarius (H9)
        firing = gyw._evaluate_yoga(
            dk_catalog, _make_state({"jupiter": "Sagittarius", "saturn": "Sagittarius"})
        )
        assert firing is not None
        assert set(firing["constituent_planets"]) == {"jupiter", "saturn"}

        # Negative control: separated in Sagittarius (H9) and Taurus (H2) -> no association
        non_firing = gyw._evaluate_yoga(
            dk_catalog, _make_state({"jupiter": "Sagittarius", "saturn": "Taurus"})
        )
        assert non_firing is None

    def test_l1_to_bodha_bo_laksana_projection_and_resonance_amplification(self):
        # Project L1 Cancer Mars yogakaraka rows into L2 Bodha MSR via bo_laksana._build_signal_row
        chart_output = {"ascendant": {"sign_id": 4, "sign": "Cancer"}}
        l1_rows = gsw._build_functional_class_rows(
            chart_output, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        mars_kt_row = next(
            r for r in l1_rows
            if r["fact_subject"] == "MAR" and r["fact_key"] == "has_kendra_trikona_lordship"
        )
        mars_bphs_row = next(
            r for r in l1_rows
            if r["fact_subject"] == "MAR" and r["fact_key"] == "bphs_canonical"
        )
        valid_ids = {r["fact_id"] for r in l1_rows}

        sig_kt = bo_laksana._build_signal_row(
            mars_kt_row,
            CHART_ID,
            BUILD_ID,
            strength_lookup={"MAR": 1.1},
            dignity_lookup={"MAR": 0.7},
            av_lookup={"MAR": 5},
            now=COMPUTED_AT,
            valid_fact_ids=valid_ids,
        )
        sig_bphs = bo_laksana._build_signal_row(
            mars_bphs_row,
            CHART_ID,
            BUILD_ID,
            strength_lookup={"MAR": 1.1},
            dignity_lookup={"MAR": 0.7},
            av_lookup={"MAR": 5},
            now=COMPUTED_AT,
            valid_fact_ids=valid_ids,
        )

        assert sig_kt["signal_type_id"] == "graha_yoga_karaka_flag:has_kendra_trikona_lordship"
        assert sig_kt["fact_kind"] == "configuration"
        assert sig_kt["valence"] == "benefic"
        assert mars_kt_row["fact_id"] in sig_kt["constituent_facts_array"]
        assert sig_bphs["signal_type_id"] == "graha_functional_class_per_ascendant:bphs_canonical"
        cfg_bphs = json.loads(sig_bphs["configuration_jsonb"])
        assert cfg_bphs["fact_value_text"] == "yogakaraka"
        assert mars_bphs_row["fact_id"] in sig_bphs["constituent_facts_array"]

        # Verify resonance_score_v1 applies exact 1.20x yogakaraka amplifier
        base = resonance_score_v1(ResonanceInputs(shadbala_normalized=0.4, is_yoga_karaka=False))
        amped = resonance_score_v1(ResonanceInputs(shadbala_normalized=0.4, is_yoga_karaka=True))
        assert isclose(amped["resonance_score"], base["resonance_score"] * 1.20, rel_tol=1e-5)


# =============================================================================
# DOMAIN 4: All 10 Tārā-Graha Planetary War Pairs + Non-Tārā / Legacy Retirement
# =============================================================================


class TestDomain4GrahaYuddhaAll10PairsAndExclusions:
    """Test C(5,2)=10 tara-graha pairs, <=1° orb, Sun/Moon/Rahu/Ketu exclusion, PR #4016, JL-026/027."""

    TARA_GRAHAS = ("Mars", "Mercury", "Jupiter", "Venus", "Saturn")

    def _cluster_chart(self, sign: str = "Capricorn", sign_id: int = 10, base_lon: float = 280.0):
        # Place all 5 tara-grahas within 0.8° of each other in the same sign
        offsets = {"Mars": 0.0, "Mercury": 0.2, "Jupiter": 0.4, "Venus": 0.6, "Saturn": 0.8}
        grahas = [
            {
                "name": name,
                "sign": sign,
                "sign_id": sign_id,
                "degree_in_sign": (base_lon % 30.0) + off,
                "longitude": base_lon + off,
            }
            for name, off in offsets.items()
        ]
        # Place Sun, Moon, Rahu, Ketu right on top too (within 0.5°) to verify non-tara exclusion
        for non_tara, off in [("Sun", 0.1), ("Moon", 0.3), ("Rahu", 0.5), ("Ketu", 0.7)]:
            grahas.append({
                "name": non_tara,
                "sign": sign,
                "sign_id": sign_id,
                "degree_in_sign": (base_lon % 30.0) + off,
                "longitude": base_lon + off,
            })
        return {"ascendant": {"sign": "Aries", "sign_id": 1}, "grahas": grahas}

    def test_all_10_tara_graha_pairs_detected_in_d1_divisional_and_condition(self):
        chart = self._cluster_chart()

        # 1. D1 ga_structural_writer._build_graha_yuddha_rows: exactly 10 pairs × 3 keys = 30 rows
        d1_rows = gsw._build_graha_yuddha_rows(
            chart, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        assert len(d1_rows) == 30
        d1_subjects = {r["fact_subject"] for r in d1_rows}
        assert len(d1_subjects) == 10
        for r in d1_rows:
            # Never Sun, Moon, Rahu, Ketu
            assert not any(bad in r["fact_subject"] for bad in ("SUN", "MOON", "RAH", "KET"))
            # JL-027 winner/loser rule remains floored
            if r["fact_key"] in ("winner", "loser"):
                assert r["fact_value_text"] is None
                assert r["fact_value_jsonb"]["floored"] is True
                assert r["fact_value_jsonb"]["reason"] == "no_ratified_classical_rule"
            elif r["fact_key"] == "orb_deg":
                assert 0.0 < r["fact_value_num"] <= 1.0

        # 2. Divisional / D10 per-varga rows (PR #4016 0dca4f511): exactly 10 pairs
        vstate = {
            g["name"]: {"sign_num": g["sign_id"], "degree": g["degree_in_sign"]}
            for g in chart["grahas"]
        }
        for varga_id in ("D1", "D10"):
            v_rows = gsw._build_graha_yuddha_per_varga_rows(
                vstate, varga_id, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
            )
            assert len(v_rows) == 10
            pairs = {frozenset((r["fact_value_jsonb"]["graha1"], r["fact_value_jsonb"]["graha2"])) for r in v_rows}
            expected_pairs = {frozenset(p) for p in combinations(self.TARA_GRAHAS, 2)}
            assert pairs == expected_pairs

        # 3. ga_condition_writer._detect_graha_yuddha excludes Sun/Moon/Rahu/Ketu & floors result
        pos_map = {g["name"]: g for g in chart["grahas"]}
        # In a 5-way cluster each planet matches multiple opponents, last wins in dict;
        # test each of the 10 pairs individually to verify every single pair fires cleanly.
        for g1, g2 in combinations(self.TARA_GRAHAS, 2):
            pair_map = {g1: pos_map[g1], g2: pos_map[g2]}
            res = gcw._detect_graha_yuddha(pair_map)
            assert res == {g1: (g2, None), g2: (g1, None)}

    def test_exact_1_deg_orb_boundary_and_non_tara_isolation(self):
        # 1.0° emits; 1.01° does not
        for orb, should_fire in [(1.0, True), (1.01, False)]:
            chart = {
                "ascendant": {"sign": "Aries", "sign_id": 1},
                "grahas": [
                    {"name": "Mars", "sign": "Aries", "sign_id": 1, "degree_in_sign": 10.0, "longitude": 10.0},
                    {"name": "Venus", "sign": "Aries", "sign_id": 1, "degree_in_sign": 10.0 + orb, "longitude": 10.0 + orb},
                ],
            }
            d1_rows = gsw._build_graha_yuddha_rows(
                chart, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
            )
            assert (len(d1_rows) == 3) is should_fire

        # Non-tara only within 0.2° produces 0 rows across all 3 functions
        non_tara_only = {
            "ascendant": {"sign": "Aries", "sign_id": 1},
            "grahas": [
                {"name": "Sun", "sign": "Aries", "sign_id": 1, "degree_in_sign": 5.0, "longitude": 5.0},
                {"name": "Moon", "sign": "Aries", "sign_id": 1, "degree_in_sign": 5.1, "longitude": 5.1},
                {"name": "Rahu", "sign": "Aries", "sign_id": 1, "degree_in_sign": 5.2, "longitude": 5.2},
                {"name": "Ketu", "sign": "Aries", "sign_id": 1, "degree_in_sign": 5.3, "longitude": 5.3},
            ],
        }
        assert gsw._build_graha_yuddha_rows(
            non_tara_only, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        ) == []
        assert gcw._detect_graha_yuddha({g["name"]: g for g in non_tara_only["grahas"]}) == {}
        vstate = {
            g["name"]: {"sign_num": g["sign_id"], "degree": g["degree_in_sign"]}
            for g in non_tara_only["grahas"]
        }
        assert gsw._build_graha_yuddha_per_varga_rows(
            vstate, "D10", CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        ) == []

    def test_jl026_legacy_graha_yuddha_facts_retired_from_ga_condition_writer(self):
        # Verify ga_condition_writer no longer emits chart_facts rows with fact_category == "graha_yuddha"
        chart = self._cluster_chart()
        pos_map = {
            g["name"]: {
                "longitude": g["longitude"],
                "sign": g["sign"],
                "house": 10,
                "dignity": "neutral",
                "retrograde": False,
            }
            for g in chart["grahas"]
        }
        yuddha_map = gcw._detect_graha_yuddha(pos_map)
        assert set(yuddha_map.keys()) <= set(self.TARA_GRAHAS)
        # No luminary/node present in yuddha_map
        assert not (set(yuddha_map.keys()) & {"Sun", "Moon", "Rahu", "Ketu"})


# =============================================================================
# DOMAIN 5: Śrīpati Bhāva Cusps & Sandhis
# =============================================================================


class TestDomain5SripatiBhavaCuspsAndSandhis:
    """Verify real Sripati madhyas, quadrant semi-arc trisection, sandhis, and 360° circuit."""

    @pytest.mark.parametrize(
        ("dob", "tob", "lat", "lon", "tz"),
        [
            (NATIVE_DOB, NATIVE_TOB, NATIVE_LAT, NATIVE_LON, NATIVE_TZ_HR),
            # High-latitude location (London) where semi-arcs deviate strongly from 30°
            (drik.Date(2024, 6, 21), (8, 15, 0), 51.5074, -0.1278, 1.0),
        ],
    )
    def test_sripati_madhya_trisection_sandhi_midpoints_and_360_circuit(
        self, dob, tob, lat: float, lon: float, tz: float
    ):
        jd = utils.julian_day_number(dob, tob)
        asc = compute_ascendant(jd, "lahiri", lat=lat, lon=lon, tz=tz)
        mc = compute_midheaven(jd, "lahiri", lat=lat, lon=lon, tz=tz)
        chalit = compute_bhava_chalit(jd, "lahiri", lat=lat, lon=lon, tz=tz)

        mad = chalit["sripati"]["madhyas"]
        cusps = chalit["sripati"]["cusps"]
        assert len(mad) == 12
        assert len(cusps) == 12

        # Angles: H1 madhya == Asc, H10 madhya == MC, H7 == Asc+180, H4 == MC+180
        assert _arc_shortest(mad[0], asc["longitude_deg"]) < 1e-4
        assert _arc_shortest(mad[9], mc["longitude_deg"]) < 1e-4
        assert _arc_shortest(mad[6], (mad[0] + 180.0) % 360.0) < 1e-6
        assert _arc_shortest(mad[3], (mad[9] + 180.0) % 360.0) < 1e-6

        # Quadrant semi-arc trisection: each 3-house quadrant divides its angle-to-angle arc into 3 equal spans
        for start_h in (0, 3, 6, 9):
            q_arc = _arc_forward(mad[start_h], mad[(start_h + 3) % 12])
            step = q_arc / 3.0
            for k in (1, 2):
                assert isclose(
                    _arc_forward(mad[start_h], mad[(start_h + k) % 12]),
                    k * step,
                    abs_tol=1e-4,
                )

        # Contiguous sandhi midpoints and exact 360° sum
        spans = []
        for h in range(12):
            c = cusps[h]
            next_c = cusps[(h + 1) % 12]
            prev_mad = mad[(h - 1) % 12]
            next_mad = mad[(h + 1) % 12]
            exp_start = (prev_mad + _arc_forward(prev_mad, mad[h]) / 2.0) % 360.0
            exp_end = (mad[h] + _arc_forward(mad[h], next_mad) / 2.0) % 360.0
            assert isclose(_arc_shortest(c["start"], exp_start), 0.0, abs_tol=1e-6)
            assert isclose(_arc_shortest(c["end"], exp_end), 0.0, abs_tol=1e-6)
            assert isclose(_arc_shortest(c["end"], next_c["start"]), 0.0, abs_tol=1e-9)
            # Opposite house symmetry
            opp = cusps[(h + 6) % 12]
            assert _arc_shortest(opp["madhya"], (c["madhya"] + 180.0) % 360.0) < 1e-6
            spans.append(_arc_forward(c["start"], c["end"]))

        assert all(s > 0.0 for s in spans)
        assert isclose(sum(spans), 360.0, abs_tol=1e-8)

    def test_sripati_sandhi_detection_flags_boundary_orb_and_wholesign_divergence(self):
        chalit_base = compute_bhava_chalit(
            NATIVE_JD_LOCAL, "lahiri", lat=NATIVE_LAT, lon=NATIVE_LON, tz=NATIVE_TZ_HR
        )
        cusp1 = chalit_base["sripati"]["cusps"][0]
        # Place synthetic body 1.0° inside H1 start boundary and another right on H1 madhya
        probe_grahas = [
            {"name": "BoundaryBody", "longitude_deg": (cusp1["start"] + 1.0) % 360.0, "house": 1},
            {"name": "CenterBody", "longitude_deg": cusp1["madhya"], "house": 1},
        ]
        chalit = compute_bhava_chalit(
            NATIVE_JD_LOCAL, "lahiri", lat=NATIVE_LAT, lon=NATIVE_LON, tz=NATIVE_TZ_HR, grahas=probe_grahas
        )
        assert chalit["graha_chalit"]["BoundaryBody"]["sandhi_flag"] is True
        assert "within_boundary_orb" in chalit["graha_chalit"]["BoundaryBody"]["sandhi_reasons"]
        assert chalit["graha_chalit"]["CenterBody"]["chalit_house"] == 1
        assert chalit["graha_chalit"]["CenterBody"]["dist_to_madhya_deg"] < 1e-6


# =============================================================================
# DOMAIN 6: Sign-Level Bhinna-Aṣṭakavarga & Sarvāṣṭakavarga Invariants
# =============================================================================


class TestDomain6AshtakavargaAndShodhanaInvariants:
    """Verify SAV=337, canonical BAV totals, prastara sums, trikona/ekadhipatya shodhana."""

    CANONICAL_BAV_TOTALS = {
        "Sun": 48,
        "Moon": 49,
        "Mars": 39,
        "Mercury": 54,
        "Jupiter": 56,
        "Venus": 52,
        "Saturn": 39,
    }

    @pytest.mark.parametrize(
        ("dob", "tob", "ayanamsha_id"),
        [
            (NATIVE_DOB, NATIVE_TOB, "lahiri"),
            (NATIVE_DOB, NATIVE_TOB, "raman"),
            (drik.Date(2000, 1, 1), (12, 0, 0), "lahiri"),
        ],
    )
    def test_bav_sav_337_prastara_and_shodhana_invariants(self, dob, tob, ayanamsha_id: str):
        jd = utils.julian_day_number(dob, tob)
        av = compute_ashtakavarga_shodhana(
            jd, ayanamsha_id, lat=NATIVE_LAT, lon=NATIVE_LON, tz=NATIVE_TZ_HR
        )
        bindus = av["bindus"]
        pinda = av["pinda"]

        # 1. Canonical per-graha totals and SAV=337
        for graha, expected_total in self.CANONICAL_BAV_TOTALS.items():
            assert len(bindus[graha]) == 12
            assert sum(bindus[graha]) == expected_total
        assert sum(bindus["SARVA"]) == 337
        assert sum(self.CANONICAL_BAV_TOTALS.values()) == 337

        # 2. Sign-wise SARVA == sum of 7 classical BAVs
        for s in range(12):
            assert bindus["SARVA"][s] == sum(bindus[g][s] for g in self.CANONICAL_BAV_TOTALS)
        assert gstr._verify_ashtakavarga(bindus) == "classical_match"

        # 3. Prastara (8 contributors: 7 grahas + Lagna) sums exactly to raw BAV
        prastara = gstr._derive_ashtakavarga_prastara(
            jd, ayanamsha_id, lat=NATIVE_LAT, lon=NATIVE_LON, tz=NATIVE_TZ_HR
        )
        for graha in self.CANONICAL_BAV_TOTALS:
            for s in range(12):
                contrib_vals = [prastara[graha][c][s] for c in prastara[graha]]
                assert all(v in (0, 1) for v in contrib_vals)
                assert sum(contrib_vals) == bindus[graha][s]

        # 4. Trikona & Ekādhipatya śodhana invariants
        grids = gstr._derive_ashtakavarga_shodhana_grids(
            jd, ayanamsha_id, lat=NATIVE_LAT, lon=NATIVE_LON, tz=NATIVE_TZ_HR
        )
        tri = grids["trikona"]
        eka = grids["ekadhipatya"]
        for graha in self.CANONICAL_BAV_TOTALS:
            for s in range(12):
                assert 0 <= eka[graha][s] <= tri[graha][s] <= bindus[graha][s]
            # Within each trikona triad ({0,4,8}, {1,5,9}, {2,6,10}, {3,7,11}):
            # if all 3 signs are equal after trikona reduction, all become 0; otherwise min == 0
            for base in range(4):
                triad = [tri[graha][base + 4 * k] for k in range(3)]
                assert min(triad) == 0
            assert pinda[graha]["sodhya"] == pinda[graha]["raasi"] + pinda[graha]["graha"]

    def test_verify_ashtakavarga_rejects_corrupted_sav_and_sign_rows_build_cleanly(self):
        av = compute_ashtakavarga_shodhana(
            NATIVE_JD_LOCAL, "lahiri", lat=NATIVE_LAT, lon=NATIVE_LON, tz=NATIVE_TZ_HR
        )
        grids = gstr._derive_ashtakavarga_shodhana_grids(
            NATIVE_JD_LOCAL, "lahiri", lat=NATIVE_LAT, lon=NATIVE_LON, tz=NATIVE_TZ_HR
        )
        prastara = gstr._derive_ashtakavarga_prastara(
            NATIVE_JD_LOCAL, "lahiri", lat=NATIVE_LAT, lon=NATIVE_LON, tz=NATIVE_TZ_HR
        )
        rows = gstr._build_ashtakavarga_rows(
            av["bindus"], av["pinda"], CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER,
            "classical_match", grids=grids, prastara=prastara,
        )
        sign_rows = [r for r in rows if r["fact_category"] == "ashtakavarga_bindu_sign"]
        sarva_sign_rows = [r for r in sign_rows if r["fact_subject"].startswith("SARVA-SIGN_")]
        assert len(sarva_sign_rows) == 12
        assert sum(int(r["fact_value_num"]) for r in sarva_sign_rows) == 337

        # Test ga_structural_writer._build_anubindu_rows rotates sign-keyed ekadhipatya to houses
        conn = MagicMock()
        cur = conn.cursor.return_value.__enter__.return_value
        cur.fetchall.return_value = [
            (f"{gsw.PLANET_TO_SUBJECT[g]}-SIGN_{s + 1}", grids["ekadhipatya"][g][s], f"fid-{g}-{s}")
            for g in self.CANONICAL_BAV_TOTALS
            for s in range(12)
        ]
        anubindu_rows = gsw._build_anubindu_rows(
            conn, {"ascendant": {"sign_id": 1}}, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
        )
        assert len(anubindu_rows) == 84

        # Corruption probe: shifting SARVA by 5 (> tolerance=2) must raise TwoPassVerificationError
        bad_bav = {k: list(v) for k, v in av["bindus"].items()}
        bad_bav["SARVA"][0] += 5
        with pytest.raises(gstr.TwoPassVerificationError):
            gstr._verify_ashtakavarga(bad_bav)


# =============================================================================
# DOMAIN 7: Hora Lagna, Ghaṭī Lagna, & Classical Sphuṭas
# =============================================================================


class TestDomain7HoraGhatiLagnaAndClassicalSphutas:
    """Verify sunrise-based Hora/Ghati/Bhava Lagna progression rates and classical sphuṭas."""

    def test_hora_ghati_bhava_lagna_progression_rates_from_sunrise(self):
        place = drik.Place("Bhubaneswar", NATIVE_LAT, NATIVE_LON, NATIVE_TZ_HR)
        jd_0 = utils.julian_day_number(NATIVE_DOB, (7, 0, 0))   # shortly after sunrise
        jd_24 = utils.julian_day_number(NATIVE_DOB, (7, 24, 0))  # +1 ghatika (24 min)
        jd_60 = utils.julian_day_number(NATIVE_DOB, (8, 0, 0))   # +60 min (1 hora)

        def _lon(res):
            return float(res[0]) * 30.0 + float(res[1])

        # +24 min (1 ghatika): HL advances 12°, GL advances 30° (1 sign), BL advances 6°
        assert isclose(_arc_forward(_lon(hora_lagna(jd_0, place)), _lon(hora_lagna(jd_24, place))), 12.0, abs_tol=1e-4)
        assert isclose(_arc_forward(_lon(ghati_lagna(jd_0, place)), _lon(ghati_lagna(jd_24, place))), 30.0, abs_tol=1e-4)
        assert isclose(_arc_forward(_lon(bhava_lagna(jd_0, place)), _lon(bhava_lagna(jd_24, place))), 6.0, abs_tol=1e-4)

        # +60 min (1 hora): HL advances 30° (1 sign), GL advances 75°, BL advances 15°
        assert isclose(_arc_forward(_lon(hora_lagna(jd_0, place)), _lon(hora_lagna(jd_60, place))), 30.0, abs_tol=1e-4)
        assert isclose(_arc_forward(_lon(ghati_lagna(jd_0, place)), _lon(ghati_lagna(jd_60, place))), 75.0, abs_tol=1e-4)
        assert isclose(_arc_forward(_lon(bhava_lagna(jd_0, place)), _lon(bhava_lagna(jd_60, place))), 15.0, abs_tol=1e-4)

        # Pre-sunrise instant (04:30 IST) uses previous day's sunrise seamlessly
        jd_pre = utils.julian_day_number(NATIVE_DOB, (4, 30, 0))
        hl_pre = _lon(hora_lagna(jd_pre, place))
        gl_pre = _lon(ghati_lagna(jd_pre, place))
        assert 0.0 <= hl_pre < 360.0
        assert 0.0 <= gl_pre < 360.0

    def test_classical_sphutas_bhrigu_yogi_avayogi_trisphuta_and_pranapada(self):
        sl = compute_special_lagnas(
            NATIVE_JD_LOCAL, NATIVE_DOB, NATIVE_TOB, "lahiri",
            lat=NATIVE_LAT, lon=NATIVE_LON, tz=NATIVE_TZ_HR,
        )
        all_longs = {
            "LAGNA": 12.4311,
            "SUN": 292.12,
            "MOON": 325.50,
            "SAT": 202.30,
            "RAH_MEAN": 50.00,
        }

        # 1. Bhrigu Bindu in ga_sensitive_writer (_midpoint(Moon, Rahu))
        bb_rows = gsens._build_bhrigu_bindu_rows(all_longs, CHART_ID, AY_ID, BUILD_ID, ENG_VER)
        bb_lon = next(r["fact_value_num"] for r in bb_rows if r["fact_key"] == "longitude_sidereal")
        assert isclose(bb_lon, gsens._midpoint(all_longs["MOON"], all_longs["RAH_MEAN"]), abs_tol=1e-6)
        assert "bhrigu_bindhu_lagna" in sl and "longitude_deg" in sl["bhrigu_bindhu_lagna"]

        # 2. Yogi / Avayogi (BPHS 93°20' and alt 96°40')
        yogi_rows = gsens._build_yogi_avayogi_rows(all_longs, CHART_ID, AY_ID, BUILD_ID, ENG_VER)
        yogi_bphs = next(
            r["fact_value_num"] for r in yogi_rows
            if r["fact_category"] == "esoteric_point_yogi"
            and r["formula_id"] == "bphs_93_20"
            and r["fact_key"] == "longitude_sidereal"
        )
        avayogi_bphs = next(
            r["fact_value_num"] for r in yogi_rows
            if r["fact_category"] == "esoteric_point_avayogi"
            and r["formula_id"] == "bphs_93_20"
            and r["fact_key"] == "longitude_sidereal"
        )
        assert isclose(yogi_bphs, (all_longs["SUN"] + all_longs["MOON"] + 93.3333333) % 360.0, abs_tol=1e-5)
        assert isclose(avayogi_bphs, (yogi_bphs + 186.6666667) % 360.0, abs_tol=1e-5)

        # 3. Tri-sphuṭa / Chatus-sphuṭa / Pancha-sphuṭa driven by sunrise-based Hora Lagna
        hl_lon = sl["hora_lagna"]["longitude_deg"]
        tri_rows = gsens._build_trisphuta_family_rows(
            all_longs, CHART_ID, AY_ID, BUILD_ID, ENG_VER, hora_lagna=hl_lon
        )
        tri_by_cat = {
            r["fact_category"]: r["fact_value_num"]
            for r in tri_rows
            if r["fact_key"] == "longitude_sidereal" and r.get("formula_id") in (None, "with_saturn")
        }
        exp_tri = (all_longs["LAGNA"] + all_longs["MOON"] + hl_lon) % 360.0
        exp_chat = (exp_tri + all_longs["SUN"]) % 360.0
        exp_panch = (exp_chat + all_longs["SAT"]) % 360.0
        assert isclose(tri_by_cat["esoteric_point_trisphuta"], exp_tri, abs_tol=1e-5)
        assert isclose(tri_by_cat["esoteric_point_chatushphuta"], exp_chat, abs_tol=1e-5)
        assert isclose(tri_by_cat["esoteric_point_panchasphuta"], exp_panch, abs_tol=1e-5)

        # 4. Pranapada uses PyJHora drik.pranapada_lagna; floors cleanly when absent
        pp_rows = gsens._build_pranapada_rows(
            {"special_lagnas": sl}, all_longs, CHART_ID, AY_ID, BUILD_ID, ENG_VER
        )
        pp_lon = next(r["fact_value_num"] for r in pp_rows if r["fact_key"] == "longitude_sidereal")
        assert isclose(pp_lon, sl["pranapada_lagna"]["longitude_deg"], abs_tol=1e-6)
        pp_floored = gsens._build_pranapada_rows(
            {"special_lagnas": {}}, all_longs, CHART_ID, AY_ID, BUILD_ID, ENG_VER
        )
        assert len(pp_floored) == 1
        assert pp_floored[0]["verification_pass_status"] == gsens.FLOORED
        assert pp_floored[0]["fact_value_num"] is None


# =============================================================================
# DOMAIN 8: Lunar Nakṣatra / Pāda Boundaries & Vimśottarī Daśā Balance + Contiguity
# =============================================================================


class TestDomain8NakshatraPadaAndVimshottariContiguity:
    """Verify 27×4 nakṣatra-pāda grid, 120y cycle, balance formula, & MD→AD contiguity."""

    EXPECTED_CYCLE_YEARS = (
        ("Ketu", 7),
        ("Venus", 20),
        ("Sun", 6),
        ("Moon", 10),
        ("Mars", 7),
        ("Rahu", 18),
        ("Jupiter", 16),
        ("Saturn", 19),
        ("Mercury", 17),
    )

    def test_all_27_nakshatras_4_padas_boundaries_and_120_year_proportions(self):
        assert sum(VIMSHOTTARI_YEARS.values()) == 120
        assert tuple((p, VIMSHOTTARI_YEARS[p]) for p in PLANET_CYCLE) == self.EXPECTED_CYCLE_YEARS

        nak_span = 360.0 / 27.0   # 13°20'
        pada_span = 360.0 / 108.0  # 3°20'
        for nak0 in range(27):
            expected_lord = self.EXPECTED_CYCLE_YEARS[nak0 % 9][0]
            for pada in range(1, 5):
                lon = nak0 * nak_span + (pada - 0.5) * pada_span
                assert _nakshatra_0based(lon) == nak0
                nak_name, nak_lord, got_pada = gsens._long_to_nakshatra_pada(lon)
                assert got_pada == pada
                assert nak_lord == expected_lord
                idx1, d_nak_name, d_lord = gdw._get_moon_nakshatra_lord(lon)
                assert idx1 == nak0 + 1
                assert d_lord == expected_lord
                kp = compute_kp_lords(lon)
                assert kp["star_lord"] == expected_lord

            # Exact nakshatra start & just-before-end boundary
            if nak0 > 0:
                start_lon = nak0 * nak_span
                assert _nakshatra_0based(start_lon - 1e-6) == nak0 - 1
                assert _nakshatra_0based(start_lon + 1e-6) == nak0

    @pytest.mark.parametrize("fraction", [1e-6, 0.25, 0.5, 0.75, 0.999])
    def test_vimshottari_balance_formula_and_md_ad_gap_free_contiguity(
        self, fraction: float
    ):
        # Moon in Purva Bhadrapada (nak0=24, lord=Jupiter, 16y)
        nak_span = 360.0 / 27.0
        moon_lon = 24 * nak_span + fraction * nak_span
        birth_jd = swe.julday(1984, 2, 5, 5.216667)

        lord, nak0, elapsed, balance = derive_birth_nakshatra_period(moon_lon)
        assert lord == "Jupiter"
        assert nak0 == 24
        assert isclose(elapsed + balance, 16.0, abs_tol=1e-9)
        assert isclose(balance, 16.0 * (1.0 - fraction), abs_tol=1e-9)

        # Seed karaka roles for direct compute_vimshottari call
        saved_roles = dict(gdw._KARAKA_ROLE_CACHE)
        gdw.set_karaka_roles(
            CHART_ID,
            "lahiri",
            {
                "Moon": "AK", "Saturn": "AmK", "Sun": "BK", "Venus": "MK",
                "Mars": "PiK", "Rahu": "PK", "Jupiter": "GK", "Mercury": "DK",
            },
        )
        try:
            rows = gdw.compute_vimshottari(moon_lon, birth_jd, "lahiri", CHART_ID, BUILD_ID)
        finally:
            gdw._KARAKA_ROLE_CACHE.clear()
            gdw._KARAKA_ROLE_CACHE.update(saved_roles)

        mds = sorted(
            [r for r in rows if r["level_n"] == 1],
            key=lambda r: datetime.fromisoformat(r["start_iso"]),
        )
        ads = sorted(
            [r for r in rows if r["level_n"] == 2],
            key=lambda r: datetime.fromisoformat(r["start_iso"]),
        )
        assert len(mds) >= 8
        assert len(ads) >= 60

        # Birth Mahādaśā must end at birth_dt + balance * 365.25 days (within 2s)
        birth_dt = datetime.fromisoformat(gdw._jd_to_iso_utc(birth_jd))
        birth_md = next(
            r for r in mds
            if datetime.fromisoformat(r["start_iso"]) <= birth_dt < datetime.fromisoformat(r["end_iso"])
        )
        assert birth_md["lord_graha"] == "Jupiter"
        expected_end_dt = datetime.fromisoformat(gdw._jd_to_iso_utc(birth_jd + balance * 365.25))
        assert abs((datetime.fromisoformat(birth_md["end_iso"]) - expected_end_dt).total_seconds()) <= 2.0

        # Gap-free Mahādaśā contiguity
        for prev_md, next_md in zip(mds, mds[1:]):
            assert prev_md["end_iso"] == next_md["start_iso"]

        # Gap-free Antardaśā contiguity + exact parent MD span coverage (for unclipped interior MDs)
        for prev_ad, next_ad in zip(ads, ads[1:]):
            assert prev_ad["end_iso"] == next_ad["start_iso"]

        for md in mds[1:-1]:
            child_ads = [a for a in ads if a["parent_row_id"] == md["dasha_row_id"]]
            assert len(child_ads) == 9
            assert child_ads[0]["start_iso"] == md["start_iso"]
            assert child_ads[-1]["end_iso"] == md["end_iso"]
            md_secs = (
                datetime.fromisoformat(md["end_iso"]) - datetime.fromisoformat(md["start_iso"])
            ).total_seconds()
            child_secs = sum(
                (datetime.fromisoformat(a["end_iso"]) - datetime.fromisoformat(a["start_iso"])).total_seconds()
                for a in child_ads
            )
            assert isclose(child_secs, md_secs, abs_tol=2.0)

        # Cross-verify entire tree via independent verifier
        verified_count = gdw._apply_vimshottari_independent_verification(rows, moon_lon, birth_jd)
        assert verified_count == len(rows)
        assert {r["verification_pass_status"] for r in rows} == {"two_pass_verified"}
