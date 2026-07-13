"""
test_lane3_detector_registry.py — Night-1 Lane 3: detector registry
(house-lord yoga family, per-varga NBRY grounds ledger, budha_aditya
cancellation).

Covers the brief's §4 fixture list:
  - Dhana: 2L+9L (dhana-family pair, both wealth-house lords) conjunct in an
    auspicious meeting house fires; the same pair meeting in a dusthana does
    not; a combust constituent lord demotes (bhanga_active=True).
  - Budha-Aditya: non-combust fires with bhanga_active=False; combust cancels
    (bhanga_active=True, bhanga_rule_fired="mercury_combust").
  - Vipareeta: 8th lord in the 12th fires; the same configuration with a
    non-dusthana lord conjunct records dilution (bhanga_active=True).
  - NBRY D9: the CR-59 Saturn + Venus specimens both fire via the existing
    rule engine (verify-first task); the new grounds ledger records
    per-rule checked/fired booleans for both.
  - Kemadruma x Anapha mutual exclusion is covered by the existing R6A yoga
    engine (test_l0_rules_yoga.py) — not duplicated here (Lane 3 scope is
    the NEW detector registry + NBRY grounds; dosha cancellation gating in
    ga_structural_writer is Deliverable C, HELD per the brief's own Lane-1
    collision fallback — see this lane's handback report).
  - Registry hygiene: every YOGA_DETECTORS entry has a non-None cancellation
    callable; every DETECTOR_INSERT_IDS entry has a matching
    brahma_yoga_catalog seed row in the Lane-3 migration.

Pure deterministic functions — no DB, no LLM, no chart writes.
"""
from __future__ import annotations

import pathlib
import re

import pytest

from ga_writers.ga_yoga_writer import (
    DETECTOR_INSERT_IDS,
    SIGN_NUMBERS,
    YOGA_DETECTORS,
    ChartState,
    _nbry_grounds_ledger,
    detect_neecha_bhanga,
    evaluate_bhanga,
    evaluate_nbry,
)

MIGRATION_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / ".."
    / "supabase"
    / "migrations"
    / "434_lane3_detector_registry_yogas.sql"
).resolve()


# ── Helpers (mirrors test_r6a2_house_lord_yogas.py's _state builder) ──────────

def _state(lagna_sign: str, placements: dict[str, str]) -> ChartState:
    facts: list[dict] = [{
        "fact_id": "f_lagna_sign",
        "fact_subject": "lagna",
        "fact_category": "graha_position",
        "fact_key": "sign",
        "fact_value_text": lagna_sign,
        "fact_value_num": None,
    }]
    lagna_num = SIGN_NUMBERS[lagna_sign]
    for planet, sign in placements.items():
        house = ((SIGN_NUMBERS[sign] - lagna_num) % 12) + 1
        facts.append({
            "fact_id": f"f_{planet}_house", "fact_subject": planet,
            "fact_category": "graha_position", "fact_key": "house_d1",
            "fact_value_num": house, "fact_value_text": None,
        })
        facts.append({
            "fact_id": f"f_{planet}_sign", "fact_subject": planet,
            "fact_category": "graha_position", "fact_key": "sign",
            "fact_value_text": sign, "fact_value_num": None,
        })
    return ChartState(facts)


# All fixtures below use an Aries lagna. Parashari sign lords (from
# NB_SIGN_LORDS): H1 Aries/Mars, H2 Taurus/Venus, H3 Gemini/Mercury,
# H4 Cancer/Moon, H5 Leo/Sun, H6 Virgo/Mercury, H7 Libra/Venus,
# H8 Scorpio/Mars, H9 Sagittarius/Jupiter, H10 Capricorn/Saturn,
# H11 Aquarius/Saturn, H12 Pisces/Jupiter.
#
# Fixtures deliberately place ONLY the grahas needed for each assertion —
# `_check_house_lord_association` requires a resolvable position for BOTH
# lords in a candidate pair, so any lord left unplaced safely contributes no
# incidental association (no accidental noise from opposite-house 7th-aspect
# universality, which bit an earlier draft of these tests).


# ── Dhana (house-lord family): 2nd lord Venus, 9th lord Jupiter ──────────────

class TestDhanaYogaHouseLords:
    def test_fires_2l_9l_conjunction_in_auspicious_house(self):
        # Venus (2L) and Jupiter (9L) conjunct in Leo (H5, a trikona — not
        # a dusthana). No other graha placed, so no other pair can fire.
        state = _state("aries", {"venus": "leo", "jupiter": "leo"})
        finding = YOGA_DETECTORS["dhana_yoga_house_lords"].detect(state, {})
        assert finding is not None
        assert set(finding["constituent_planets"]) == {"venus", "jupiter"}
        assert finding["constituent_houses"] == [5]

    def test_does_not_fire_when_meeting_house_is_dusthana(self):
        # Same 2L/9L pair, conjoined in Scorpio (H8) — a dusthana.
        state = _state("aries", {"venus": "scorpio", "jupiter": "scorpio"})
        finding = YOGA_DETECTORS["dhana_yoga_house_lords"].detect(state, {})
        assert finding is None

    def test_combust_lord_demotes_bhanga_active_true(self):
        state = _state("aries", {"venus": "leo", "jupiter": "leo"})
        finding = YOGA_DETECTORS["dhana_yoga_house_lords"].detect(state, {})
        assert finding is not None
        special_states = {"venus": {"is_combust": True}}
        verdict = YOGA_DETECTORS["dhana_yoga_house_lords"].cancellation(
            finding, state, special_states, [],
        )
        assert verdict["bhanga_active"] is True
        assert "venus" in verdict["bhanga_rule_fired"]

    def test_no_affliction_bhanga_active_false(self):
        state = _state("aries", {"venus": "leo", "jupiter": "leo"})
        finding = YOGA_DETECTORS["dhana_yoga_house_lords"].detect(state, {})
        verdict = YOGA_DETECTORS["dhana_yoga_house_lords"].cancellation(
            finding, state, {}, [],
        )
        assert verdict["bhanga_active"] is False


# ── Raja Yoga kendra-trikona detector: 10th lord Saturn, 9th lord Jupiter ────

class TestRajaYogaKendraTrikona:
    def test_fires_and_cancellation_callable_present(self):
        spec = YOGA_DETECTORS["raja_yoga_kendra_trikona"]
        assert spec.cancellation is not None
        # Saturn (10L, kendra) and Jupiter (9L, trikona) conjunct in
        # Capricorn (H10 — Saturn's own sign, not a dusthana).
        state = _state("aries", {"saturn": "capricorn", "jupiter": "capricorn"})
        finding = spec.detect(state, {})
        assert finding is not None
        assert set(finding["constituent_planets"]) == {"saturn", "jupiter"}
        verdict = spec.cancellation(finding, state, {}, [])
        assert verdict["bhanga_active"] is False


# ── Budha-Aditya (cancellation-only integration) ───────────────────────────────

class TestBudhaAdityaCancellation:
    def test_detect_fires_on_conjunction(self):
        state = _state("aries", {"mercury": "capricorn", "sun": "capricorn"})
        finding = YOGA_DETECTORS["budha_aditya"].detect(state, {})
        assert finding is not None
        assert set(finding["constituent_planets"]) == {"sun", "mercury"}

    def test_non_combust_bhanga_active_false(self):
        verdict = YOGA_DETECTORS["budha_aditya"].cancellation(
            {}, None, {"mercury": {"is_combust": False}}, [],
        )
        assert verdict["bhanga_active"] is False

    def test_combust_cancels_via_bhanga_evaluators_registry(self):
        # This is the ACTUAL integration path used at build time: the main
        # catalog loop calls evaluate_bhanga("budha_aditya", ...), which now
        # routes to the registered handler (module-level side effect of
        # importing ga_writers.ga_yoga_writer).
        out = evaluate_bhanga(
            "budha_aditya", d1_positions={}, special_states={"mercury": {"is_combust": True}},
        )
        assert out["bhanga_active"] is True
        assert out["bhanga_rule_fired"] == "mercury_combust"

    def test_non_combust_via_bhanga_evaluators_registry(self):
        out = evaluate_bhanga(
            "budha_aditya", d1_positions={}, special_states={"mercury": {"is_combust": False}},
        )
        assert out["bhanga_active"] is False


# ── Vipareeta Raja Yoga detector ────────────────────────────────────────────────

class TestVipareetaRajaYoga:
    # Aries lagna: 8th lord = Mars (Scorpio). Non-dusthana lords include
    # Saturn (10th/11th, Capricorn/Aquarius) — safe to conjoin without
    # itself being a dusthana lord (dusthana lords are Mercury [3rd/6th],
    # Mars [1st/8th], Jupiter [9th/12th]).
    def test_fires_8th_lord_in_12th(self):
        # Mars placed in the 12th (Pisces) — a dusthana placement of a
        # dusthana lord. Nothing else placed, so no incidental noise.
        state = _state("aries", {"mars": "pisces"})
        finding = YOGA_DETECTORS["vipareeta_raja_yoga"].detect(state, {})
        assert finding is not None
        assert "mars" in finding["constituent_planets"]

    def test_conjunct_non_dusthana_lord_records_dilution(self):
        # Saturn (non-dusthana lord) conjunct with Mars in Pisces (H12).
        state = _state("aries", {"mars": "pisces", "saturn": "pisces"})
        finding = YOGA_DETECTORS["vipareeta_raja_yoga"].detect(state, {})
        assert finding is not None
        verdict = YOGA_DETECTORS["vipareeta_raja_yoga"].cancellation(finding, state, {}, [])
        assert verdict["bhanga_active"] is True
        assert "saturn" in verdict["bhanga_rule_fired"]

    def test_undiluted_bhanga_active_false(self):
        state = _state("aries", {"mars": "pisces"})
        finding = YOGA_DETECTORS["vipareeta_raja_yoga"].detect(state, {})
        verdict = YOGA_DETECTORS["vipareeta_raja_yoga"].cancellation(finding, state, {}, [])
        assert verdict["bhanga_active"] is False


# ── NBRY D9 — CR-59 verify-first task ──────────────────────────────────────────

class TestNbryD9VerifyFirst:
    """CR-59 specimen: Saturn debilitated in D9 (Aries), redeemed by rule 2
    (exaltation-lord Sun in D9 kendra-from-lagna, house 1); Venus debilitated
    in D9 (Virgo), redeemed by rule 1 (dispositor Mercury in D9 kendra,
    house 7). Both per the brief's cited facts (f764a762/4814c825/856875fd).
    """

    def _d9_positions(self) -> dict[str, dict]:
        return {
            "saturn": {"sign": "aries", "house": 5},       # debilitated in D9
            "sun": {"sign": "cancer", "house": 1},         # exaltation-lord of Aries, D9 kendra (H1)
            "venus": {"sign": "virgo", "house": 3},        # debilitated in D9
            "mercury": {"sign": "capricorn", "house": 7},  # dispositor of Virgo, D9 kendra (H7)
        }

    def test_saturn_and_venus_d9_nbry_both_fire(self):
        d9 = self._d9_positions()
        findings = detect_neecha_bhanga(d9, varga="D9")
        planets_fired = {f["planet"] for f in findings}
        assert "saturn" in planets_fired, "Saturn-D9 NBRY should fire per CR-59 (rule 2, Sun in D9 kendra)"
        assert "venus" in planets_fired, "Venus-D9 NBRY should fire per CR-59 (rule 1, Mercury in D9 kendra)"

        saturn_finding = next(f for f in findings if f["planet"] == "saturn")
        assert any(r["rule_id"] == "nbry_rule_2_exaltation_lord_kendra" for r in saturn_finding["rules_fired"])

        venus_finding = next(f for f in findings if f["planet"] == "venus")
        assert any(r["rule_id"] == "nbry_rule_1_dispositor_kendra" for r in venus_finding["rules_fired"])

    def test_grounds_ledger_records_checked_and_fired_for_both(self):
        d9 = self._d9_positions()
        ledger = _nbry_grounds_ledger(d9, "D9")
        by_planet = {g["planet"]: g for g in ledger}
        assert "saturn" in by_planet and "venus" in by_planet

        saturn_grounds = by_planet["saturn"]["grounds"]
        # 4 real rules + the floored rule 5 = 5 grounds entries, all checked=True
        assert len(saturn_grounds) == 5
        assert all(g["checked"] is True for g in saturn_grounds)
        rule2 = next(g for g in saturn_grounds if g["rule_id"] == "nbry_rule_2_exaltation_lord_kendra")
        assert rule2["fired"] is True

        venus_grounds = by_planet["venus"]["grounds"]
        rule1 = next(g for g in venus_grounds if g["rule_id"] == "nbry_rule_1_dispositor_kendra")
        assert rule1["fired"] is True
        # Rule 5 is always checked, never fires (honest floor).
        rule5 = next(g for g in venus_grounds if g["rule_id"] == "nbry_rule_5_mutual_kendra")
        assert rule5["fired"] is False
        assert rule5["detail"]["floored"] is True

    def test_grounds_ledger_records_non_fired_checks_too(self):
        # A debilitated graha with NO firing rule still gets a full grounds
        # ledger (checked=True, fired=False for every rule) — the CR-59
        # visibility bar: "any NBRY verdict served downstream must be
        # traceable to its checked grounds", including the non-fired case.
        d1 = {
            "mars": {"sign": "cancer", "house": 1},  # Mars debilitated, isolated (no redeeming placements)
        }
        ledger = _nbry_grounds_ledger(d1, "D1")
        assert len(ledger) == 1
        mars_grounds = ledger[0]["grounds"]
        assert len(mars_grounds) == 5
        assert all(g["checked"] is True for g in mars_grounds)
        assert all(g["fired"] is False for g in mars_grounds)


# ── Registry hygiene ────────────────────────────────────────────────────────────

class TestRegistryHygiene:
    def test_every_detector_has_a_non_none_cancellation_callable(self):
        for det_id, spec in YOGA_DETECTORS.items():
            assert spec.cancellation is not None, det_id
            assert callable(spec.cancellation), det_id
            assert callable(spec.detect), det_id

    def test_every_detector_insert_id_has_a_migration_seed_row(self):
        sql = MIGRATION_PATH.read_text()
        for det_id in DETECTOR_INSERT_IDS:
            assert re.search(rf"'{det_id}'", sql), (
                f"{det_id} has no seed row in {MIGRATION_PATH.name}"
            )

    def test_budha_aditya_and_lakshmi_yoga_documented_as_pre_existing(self):
        # These two collide with pre-existing catalog canonical_ids (see
        # migration 434's header) and are handled via different mechanisms
        # (cancellation-only registration / independent-insert-on-floored-
        # path respectively) — both are still present in YOGA_DETECTORS.
        assert "budha_aditya" in YOGA_DETECTORS
        assert "lakshmi_yoga" in YOGA_DETECTORS
        assert "budha_aditya" not in DETECTOR_INSERT_IDS
        assert "lakshmi_yoga" in DETECTOR_INSERT_IDS


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
