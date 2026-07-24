"""
test_cr130_karakamsha_yogas.py — SARVA-SIDDHI W-4 / CR-130.

The Jaimini karakāṃśa planet-yoga family (jaimini_karakamsha_{sun,moon,mars,
jupiter,venus,saturn,rahu}) previously existed as an L0 catalog definition with
ZERO L1 firing logic. This suite pins the new detector
(ga_yoga_writer._build_karakamsha_firings and its helpers):

  1. Jaimini chara-rāśi-dṛṣṭi (_jaimini_rasi_aspects) is correct and symmetric.
  2. A graha OCCUPYING the karakāṃśa sign in D1 fires (mode='occupation').
  3. A graha ASPECTING the karakāṃśa by Jaimini sign-aspect fires (mode='aspect').
  4. Rahu is occupation-only (no or_aspect clause in its catalog row).
  5. ChartState reads the karakāṃśa sign from karakamsa_position chart_facts
     (§N.5 L1-authority — never recomputed).
  6. Two-chart guard: the native (482012f1) and the control (1c826d5a) fire
     DIFFERENT karakāṃśa yogas under their real placements — the detector is
     neither always-true nor always-false.
  7. Catalog coverage: every KARAKAMSHA_YOGAS id has a matching seed row in
     migration 465, and Mercury (uncatalogued) is intentionally absent.

Pure deterministic functions — no DB, no LLM, no chart writes.
"""
from __future__ import annotations

import pathlib
import re

from ga_writers.ga_yoga_writer import (
    DUAL_SIGNS,
    FIXED_SIGNS,
    KARAKAMSHA_YOGAS,
    MOVABLE_SIGNS,
    SIGN_NUMBERS,
    ChartState,
    _build_karakamsha_firings,  # noqa: F401 — imported to assert it exists/imports
    _jaimini_rasi_aspects,
    _karakamsha_reaches,
)

MIGRATION_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / ".."
    / "supabase"
    / "migrations"
    / "465_cr130_jaimini_karakamsha_yogas.sql"
).resolve()


# ── Chart-state builder (mirrors test_lane3_detector_registry._state) ─────────

def _state(lagna_sign: str, placements: dict[str, str], karakamsha_sign: str | None) -> ChartState:
    facts: list[dict] = [{
        "fact_id": "f_lagna_sign", "fact_subject": "lagna",
        "fact_category": "graha_position", "fact_key": "sign",
        "fact_value_text": lagna_sign, "fact_value_num": None,
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
    if karakamsha_sign is not None:
        facts.append({
            "fact_id": "f_karakamsa_sign", "fact_subject": "KARAKAMSA",
            "fact_category": "karakamsa_position", "fact_key": "sign",
            "fact_value_text": karakamsha_sign, "fact_value_num": None,
        })
    return ChartState(facts)


# Real placements verified live 2026-07-24 (lahiri_chitrapaksha ayanamsha).
NATIVE_PLACEMENTS = {
    "sun": "capricorn", "moon": "aquarius", "mars": "libra", "mercury": "capricorn",
    "jupiter": "sagittarius", "venus": "sagittarius", "saturn": "libra", "rahu": "taurus",
}
CONTROL_PLACEMENTS = {
    "sun": "aquarius", "moon": "gemini", "mars": "pisces", "mercury": "aquarius",
    "jupiter": "capricorn", "venus": "pisces", "saturn": "scorpio", "rahu": "aries",
}


def _fires(placements: dict[str, str], karakamsha_sign: str) -> dict[str, str]:
    """Return {planet: mode} for every karakāṃśa yoga that fires."""
    out: dict[str, str] = {}
    for cid, (planet, allow_aspect) in KARAKAMSHA_YOGAS.items():
        mode = _karakamsha_reaches(placements[planet], karakamsha_sign, allow_aspect)
        if mode:
            out[planet] = mode
    return out


# ── 1. Jaimini chara-rāśi-dṛṣṭi correctness + symmetry ────────────────────────

class TestJaiminiRasiAspects:
    def test_movable_aspects_fixed_except_adjacent(self):
        # Aries (movable) aspects Leo/Scorpio/Aquarius, NOT the adjacent Taurus.
        assert _jaimini_rasi_aspects("aries") == {"leo", "scorpio", "aquarius"}

    def test_fixed_aspects_movable_except_adjacent(self):
        # Taurus (fixed) aspects Cancer/Libra/Capricorn, NOT the adjacent Aries.
        assert _jaimini_rasi_aspects("taurus") == {"cancer", "libra", "capricorn"}

    def test_dual_aspects_other_duals(self):
        assert _jaimini_rasi_aspects("gemini") == {"virgo", "sagittarius", "pisces"}

    def test_aspect_is_symmetric(self):
        # If A aspects B then B aspects A (classical Jaimini rāśi-dṛṣṭi property).
        signs = list(SIGN_NUMBERS)
        for a in signs:
            for b in _jaimini_rasi_aspects(a):
                assert a in _jaimini_rasi_aspects(b), f"{a}->{b} not reciprocated"

    def test_no_sign_aspects_itself(self):
        for s in SIGN_NUMBERS:
            assert s not in _jaimini_rasi_aspects(s)

    def test_sign_type_partition(self):
        # The three sign-type sets partition the zodiac (sanity guard).
        assert MOVABLE_SIGNS | FIXED_SIGNS | DUAL_SIGNS == set(SIGN_NUMBERS)
        assert not (MOVABLE_SIGNS & FIXED_SIGNS)


# ── 2/3/4. Occupation vs aspect vs Rahu-occupation-only ───────────────────────

class TestKarakamshaReaches:
    def test_occupation_fires(self):
        assert _karakamsha_reaches("aries", "aries", True) == "occupation"

    def test_aspect_fires_when_allowed(self):
        # Aquarius (fixed) aspects Aries (movable) → Moon aspecting karakāṃśa Aries.
        assert _karakamsha_reaches("aquarius", "aries", True) == "aspect"

    def test_no_reach_when_neither(self):
        # Capricorn (movable) aspects fixed signs, not Aries.
        assert _karakamsha_reaches("capricorn", "aries", True) is None

    def test_rahu_occupation_only_ignores_aspect(self):
        # allow_aspect=False: an aspecting-but-not-occupying position does NOT fire.
        assert _karakamsha_reaches("aquarius", "aries", False) is None
        assert _karakamsha_reaches("aries", "aries", False) == "occupation"


# ── 5. ChartState reads karakāṃśa from chart_facts (L1 authority) ─────────────

class TestChartStateKarakamsha:
    def test_reads_karakamsha_sign_and_fact_id(self):
        state = _state("aries", {"sun": "capricorn"}, karakamsha_sign="Aries")
        assert state.karakamsha_sign == "aries"
        assert state.karakamsha_fact_id == "f_karakamsa_sign"

    def test_absent_karakamsha_is_none(self):
        state = _state("aries", {"sun": "capricorn"}, karakamsha_sign=None)
        assert state.karakamsha_sign is None
        assert state.karakamsha_fact_id is None


# ── 6. Two-chart guard: native vs control fire different yogas ────────────────

class TestTwoChartGuard:
    def test_native_fires_only_moon_by_aspect(self):
        # Native karakāṃśa = Aries (AK=Moon). Only the Moon (from Aquarius)
        # aspects Aries; the "spiritual family" Sun/Jupiter/Venus are correct
        # NEGATIVES (consistent with the CR-130 brief's pravrajya precedent).
        fired = _fires(NATIVE_PLACEMENTS, "aries")
        assert fired == {"moon": "aspect"}
        assert "sun" not in fired and "jupiter" not in fired and "venus" not in fired

    def test_control_fires_sun_saturn_rahu(self):
        # Control karakāṃśa = Aries (AK=Mercury). Sun+Saturn aspect Aries;
        # Rahu occupies it. Distinct from the native → detector responds to
        # chart configuration (not always-true / always-false).
        fired = _fires(CONTROL_PLACEMENTS, "aries")
        assert fired == {"sun": "aspect", "saturn": "aspect", "rahu": "occupation"}

    def test_native_and_control_differ(self):
        assert _fires(NATIVE_PLACEMENTS, "aries") != _fires(CONTROL_PLACEMENTS, "aries")


# ── 7. Catalog coverage + Mercury intentional absence ─────────────────────────

class TestCatalogCoverage:
    def test_family_members(self):
        assert set(KARAKAMSHA_YOGAS) == {
            f"jaimini_karakamsha_{p}"
            for p in ("sun", "moon", "mars", "jupiter", "venus", "saturn", "rahu")
        }
        # Mercury is intentionally NOT a member (no l0_yogas.py catalog row).
        assert "jaimini_karakamsha_mercury" not in KARAKAMSHA_YOGAS

    def test_only_rahu_is_occupation_only(self):
        for cid, (_planet, allow_aspect) in KARAKAMSHA_YOGAS.items():
            expected = cid != "jaimini_karakamsha_rahu"
            assert allow_aspect is expected

    def test_migration_seeds_every_family_member(self):
        sql = MIGRATION_PATH.read_text(encoding="utf-8")
        for cid in KARAKAMSHA_YOGAS:
            assert re.search(rf"'{cid}'", sql), f"{cid} missing from migration 465"
        assert "jaimini_karakamsha_mercury" not in sql
        assert "ON CONFLICT (canonical_id) DO NOTHING" in sql
