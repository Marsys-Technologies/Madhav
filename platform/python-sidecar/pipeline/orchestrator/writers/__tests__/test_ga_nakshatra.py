"""
Tests for ga_nakshatra — no DB connection required.
Tests compute algorithms and writer registration.
"""
import pytest
from ga_writers.ga_nakshatra_compute import (
    compute_kp_lords, compute_gandanta, compute_tara,
    compute_dispositor_chain, compute_center_of_gravity,
    PLANET_CYCLE, VIMSHOTTARI_YEARS, TARA_NAMES,
)


class TestKpLords:
    def test_returns_four_keys(self):
        kp = compute_kp_lords(0.0)
        assert set(kp) == {"star_lord", "sub_lord", "sub_sub_lord", "prana_lord"}

    def test_star_lord_is_valid_planet(self):
        kp = compute_kp_lords(45.0)
        assert kp["star_lord"] in PLANET_CYCLE

    def test_all_lords_are_valid_planets(self):
        for long in [0.0, 90.0, 180.0, 270.0, 359.99]:
            kp = compute_kp_lords(long)
            for key in ["star_lord", "sub_lord", "sub_sub_lord", "prana_lord"]:
                assert kp[key] in PLANET_CYCLE, f"Invalid lord '{kp[key]}' at long={long}"

    def test_ashwini_star_lord_is_ketu(self):
        # Ashwini: nak 1 (0-based idx 0 → Ketu in PLANET_CYCLE). At 6° star-lord=Ketu
        kp = compute_kp_lords(6.0)
        assert kp["star_lord"] == "Ketu"

    def test_rohini_star_lord_is_moon(self):
        # Rohini: nak 4 (0-based idx 3 → Moon). Span 4×13.333°=53.333°. At 45° → idx 3 → Moon
        kp = compute_kp_lords(45.0)
        assert kp["star_lord"] == "Moon"

    def test_forensic_pbp_star_lord_is_jupiter(self):
        # Purva Bhadrapada: nak 25 (0-based 24). 24 % 9 = 6 → PLANET_CYCLE[6] = Jupiter
        # PBP spans 24×13.333° = 320° to 333.333°. At 322° star=Jupiter
        kp = compute_kp_lords(322.0)
        assert kp["star_lord"] == "Jupiter", f"Expected Jupiter, got {kp['star_lord']}"

    def test_longitude_modulo_360(self):
        kp0   = compute_kp_lords(0.0)
        kp360 = compute_kp_lords(360.0)
        assert kp0 == kp360

    def test_vimshottari_years_total_120(self):
        assert sum(VIMSHOTTARI_YEARS.values()) == 120


class TestGandanta:
    def test_approaching_junction_0(self):
        g = compute_gandanta(359.5)  # 0.5° = 30 arcmin before 0°
        assert g["is_gandanta"] is True
        assert g["side"] == "approaching"
        assert g["junction_type"] == "water_fire_0"
        assert g["arc_minutes_from_junction"] == pytest.approx(30.0, abs=0.1)

    def test_departing_junction_0(self):
        g = compute_gandanta(0.5)
        assert g["is_gandanta"] is True
        assert g["side"] == "departing"

    def test_clear_of_junction(self):
        g = compute_gandanta(90.0)
        assert g["is_gandanta"] is False
        assert g["arc_minutes_from_junction"] is None

    def test_junction_120(self):
        g = compute_gandanta(119.6)  # 0.4° = 24 arcmin before 120°
        assert g["is_gandanta"] is True
        assert g["junction_type"] == "water_fire_120"

    def test_junction_240(self):
        g = compute_gandanta(240.5)
        assert g["is_gandanta"] is True
        assert g["junction_type"] == "water_fire_240"

    def test_returns_all_keys(self):
        g = compute_gandanta(90.0)
        assert set(g) == {"is_gandanta", "arc_minutes_from_junction", "junction_type", "side"}


class TestTaraBala:
    def test_body_in_same_nak_as_moon_is_janma(self):
        t = compute_tara(25, 25)
        assert t["tara_name"] == "Janma"
        assert t["tara_position"] == 1

    def test_body_one_nak_ahead_is_sampat(self):
        t = compute_tara(2, 1)
        assert t["tara_name"] == "Sampat"

    def test_tara_names_list_length(self):
        assert len(TARA_NAMES) == 9

    def test_wraps_at_27(self):
        t1 = compute_tara(2, 1)
        t2 = compute_tara(2 + 27, 1)
        assert t1["tara_name"] == t2["tara_name"]

    def test_tara_count_range(self):
        # count is always 1-27
        for body_nak in range(1, 28):
            t = compute_tara(body_nak, 1)
            assert 1 <= t["tara_count"] <= 27
            assert 1 <= t["tara_position"] <= 9


class TestDispositorGraph:
    def test_self_terminus(self):
        chain = compute_dispositor_chain("Moon", {"Moon": "Moon"})
        assert chain["terminus"] == "Moon"
        assert chain["is_cycle"] is False
        assert chain["chain_depth"] == 1

    def test_simple_chain(self):
        chain = compute_dispositor_chain("Sun", {"Sun": "Moon", "Moon": "Moon"})
        assert chain["terminus"] == "Moon"
        assert "Moon" in chain["chain"]
        assert chain["is_cycle"] is False

    def test_cycle_detection(self):
        chain = compute_dispositor_chain("Sun", {"Sun": "Moon", "Moon": "Sun"})
        assert chain["is_cycle"] is True

    def test_chain_includes_start(self):
        chain = compute_dispositor_chain("Sun", {"Sun": "Moon", "Moon": "Moon"})
        assert chain["chain"][0] == "Sun"

    def test_center_of_gravity_two_bodies_terminate_at_jupiter(self):
        chains = {
            "Sun":  {"terminus": "Jupiter", "is_cycle": False, "chain": ["Sun","Jupiter"], "chain_depth": 2},
            "Moon": {"terminus": "Jupiter", "is_cycle": False, "chain": ["Moon","Jupiter"], "chain_depth": 2},
            "Mars": {"terminus": "Mars",    "is_cycle": False, "chain": ["Mars"], "chain_depth": 1},
        }
        cog = compute_center_of_gravity(chains)
        assert cog["terminus_body"] == "Jupiter"
        assert cog["chain_count"] == 2

    def test_center_of_gravity_empty(self):
        cog = compute_center_of_gravity({})
        assert cog["terminus_body"] is None
        assert cog["chain_count"] == 0


class TestWriterRegistration:
    def test_ga_nakshatra_registered(self):
        from pipeline.orchestrator.writers import _REGISTRY
        import pipeline.orchestrator.writers.ga_nakshatra  # noqa: F401
        assert "ga_nakshatra" in _REGISTRY

    def test_asset_id(self):
        from pipeline.orchestrator.writers.ga_nakshatra import NakshatraWriter
        assert NakshatraWriter.asset_id == "ga_nakshatra"

    def test_has_plan_substeps_and_run_substep(self):
        from pipeline.orchestrator.writers.ga_nakshatra import NakshatraWriter
        assert hasattr(NakshatraWriter, "plan_substeps")
        assert hasattr(NakshatraWriter, "run_substep")

    def test_substep_count_is_6(self):
        from pipeline.orchestrator.writers.ga_nakshatra import NakshatraWriter
        from unittest.mock import MagicMock
        writer = NakshatraWriter()
        steps  = writer.plan_substeps(MagicMock())
        assert len(steps) == 6

    def test_substep_keys_include_all_ayanamshas(self):
        from pipeline.orchestrator.writers.ga_nakshatra import NakshatraWriter, CANONICAL_AYANAMSHAS
        from unittest.mock import MagicMock
        writer = NakshatraWriter()
        steps  = writer.plan_substeps(MagicMock())
        keys   = [s.key for s in steps]
        for ay in CANONICAL_AYANAMSHAS:
            assert f"ayanamsha:{ay}" in keys
        assert "cross_ayanamsha" in keys

    def test_has_substeps_flag_is_true(self):
        from pipeline.orchestrator.writers.ga_nakshatra import NakshatraWriter
        assert NakshatraWriter.has_substeps is True
