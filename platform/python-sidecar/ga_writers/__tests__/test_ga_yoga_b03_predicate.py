"""B-03 golden tests — all_seven_planets_in_seven_consecutive_from predicate fix.

Tests the corrected predicate (len(placed)==7 AND one-per-house) against four
golden scenarios:

  T1 — 4-house cluster: 7 planets present but 4 share house 1 → must NOT fire.
  T2 — missing planet: only 6 planets placed, 6 in a 7-house window → must NOT fire
       (previous bug would have fired at >=5).
  T3 — Kedara still fires: all planets in fixed signs (separate elif branch) →
       must still fire after B-03 (B-03 must not touch that branch).
  T4 — valid consecutive 7: 7 planets, one per house, in 7 consecutive houses →
       must fire.

No live DB required — ChartState is constructed directly from synthetic fact dicts.
"""
from __future__ import annotations

import uuid

import pytest

from ga_writers.ga_yoga_writer import ChartState, _evaluate_yoga

# ── Helpers ────────────────────────────────────────────────────────────────────

def _fact(fact_id: str, category: str, subject: str, key: str,
          value_text: str | None = None, value_num: float | None = None) -> dict:
    return {
        "fact_id": fact_id,
        "fact_category": category,
        "fact_subject": subject,
        "fact_key": key,
        "fact_value_text": value_text,
        "fact_value_num": value_num,
        "fact_value_jsonb": None,
    }


# Sign names in order (1-based index matches SIGN_NAMES in the writer)
_SIGNS = [
    "aries", "taurus", "gemini", "cancer",
    "leo", "virgo", "libra", "scorpio",
    "sagittarius", "capricorn", "aquarius", "pisces",
]


def _sign_for_house(lagna_sign: str, house: int) -> str:
    """Return the sign name for a given lagna-relative house number."""
    lagna_idx = _SIGNS.index(lagna_sign)  # 0-based
    return _SIGNS[(lagna_idx + house - 1) % 12]


def _planet_facts(planet: str, sign: str, fid_prefix: str) -> list[dict]:
    """Two facts per planet: sign and house_d1 (we use sign only; house_d1 set
    to 1 as a dummy — ChartState builds lagna_house_planets from signs, not
    from house_d1 for the nabhasa akriti consecutive rule)."""
    return [
        _fact(f"{fid_prefix}_sign", "graha_position", planet, "sign", value_text=sign),
        _fact(f"{fid_prefix}_house", "graha_position", planet, "house_d1", value_num=1),
    ]


def _lagna_fact(sign: str) -> dict:
    return _fact("lagna_sign", "graha_position", "lagna", "sign", value_text=sign)


def _build_state(lagna_sign: str, planet_sign_map: dict[str, str]) -> ChartState:
    """Build a ChartState from a lagna sign and a {planet: sign} map."""
    facts: list[dict] = [_lagna_fact(lagna_sign)]
    for planet, sign in planet_sign_map.items():
        facts.extend(_planet_facts(planet, sign, f"{planet[:3]}_{sign[:3]}"))
    return ChartState(facts)


def _consecutive_7_yoga(start: int = 1) -> dict:
    """Minimal yoga dict for the all_seven_planets_in_seven_consecutive_from rule."""
    return {
        "canonical_id": "test_chatra",
        "category": "nabhasa_akriti",
        "formation_rule_jsonb": {
            "all_seven_planets_in_seven_consecutive_from": start
        },
        "cancellation_conditions": None,
        "classical_citations": None,
        "computed_strength_formula": None,
        "school": None,
        "rare": False,
    }


def _kedara_yoga() -> dict:
    """Kedara yoga: all planets in fixed signs (separate elif branch)."""
    return {
        "canonical_id": "kedara",
        "category": "nabhasa_ashraya",
        "formation_rule_jsonb": {"all_planets_in": "fixed_signs"},
        "cancellation_conditions": None,
        "classical_citations": None,
        "computed_strength_formula": None,
        "school": None,
        "rare": False,
    }


# ── T1: 4-house cluster does NOT fire ─────────────────────────────────────────

def test_t1_four_house_cluster_does_not_fire():
    """7 planets present but 4 share house 1 (Aries lagna).
    Planets: Sun, Moon, Mars, Mercury all in Aries (house 1);
    Jupiter in Taurus (house 2), Venus in Gemini (house 3),
    Saturn in Cancer (house 4).
    Window houses 1-7 contain all 7 planets but 4 occupy house 1 — not one-per-house.
    Must NOT fire."""
    lagna = "aries"
    planet_signs = {
        "sun":     "aries",    # house 1
        "moon":    "aries",    # house 1 — co-occupancy
        "mars":    "aries",    # house 1 — co-occupancy
        "mercury": "aries",    # house 1 — co-occupancy
        "jupiter": "taurus",   # house 2
        "venus":   "gemini",   # house 3
        "saturn":  "cancer",   # house 4
    }
    state = _build_state(lagna, planet_signs)
    yoga = _consecutive_7_yoga(start=1)

    result = _evaluate_yoga(yoga, state)
    assert result is None or result["fired"] is False, (
        "T1 FAIL: 4-planet co-occupancy in house 1 should not fire "
        f"all_seven_planets_in_seven_consecutive_from; got {result}"
    )


# ── T2: >=5 with missing planet does NOT fire ─────────────────────────────────

def test_t2_six_planets_does_not_fire():
    """Only 6 classical planets placed (Saturn absent from planet_sign).
    The previous bug would have fired at len(placed) >= 5.
    Must NOT fire."""
    lagna = "aries"
    planet_signs = {
        "sun":     "aries",    # house 1
        "moon":    "taurus",   # house 2
        "mars":    "gemini",   # house 3
        "mercury": "cancer",   # house 4
        "jupiter": "leo",      # house 5
        "venus":   "virgo",    # house 6
        # saturn deliberately absent
    }
    state = _build_state(lagna, planet_signs)
    yoga = _consecutive_7_yoga(start=1)

    result = _evaluate_yoga(yoga, state)
    assert result is None or result["fired"] is False, (
        "T2 FAIL: only 6 planets placed should not fire "
        f"all_seven_planets_in_seven_consecutive_from; got {result}"
    )


# ── T3: Kedara still fires (separate branch, must be unaffected) ──────────────

def test_t3_kedara_still_fires():
    """Kedara yoga: all 7 planets in fixed signs (Taurus/Leo/Scorpio/Aquarius).
    This is evaluated by the 'all_planets_in: fixed_signs' branch, which B-03
    must not touch.  Must still fire after the fix."""
    lagna = "aries"
    planet_signs = {
        "sun":     "taurus",
        "moon":    "taurus",
        "mars":    "leo",
        "mercury": "leo",
        "jupiter": "scorpio",
        "venus":   "scorpio",
        "saturn":  "aquarius",
    }
    state = _build_state(lagna, planet_signs)
    yoga = _kedara_yoga()

    result = _evaluate_yoga(yoga, state)
    assert result is not None and result["fired"] is True, (
        "T3 FAIL: Kedara (all planets in fixed signs) must still fire "
        f"after B-03; got {result}"
    )


# ── T4: Valid consecutive 7 fires ─────────────────────────────────────────────

def test_t4_valid_consecutive_7_fires():
    """7 planets, one per house, in houses 1-7 from lagna (Aries lagna).
    Sun in Aries(h1), Moon in Taurus(h2), Mars in Gemini(h3), Mercury in Cancer(h4),
    Jupiter in Leo(h5), Venus in Virgo(h6), Saturn in Libra(h7).
    Must fire."""
    lagna = "aries"
    planet_signs = {
        "sun":     "aries",    # house 1
        "moon":    "taurus",   # house 2
        "mars":    "gemini",   # house 3
        "mercury": "cancer",   # house 4
        "jupiter": "leo",      # house 5
        "venus":   "virgo",    # house 6
        "saturn":  "libra",    # house 7
    }
    state = _build_state(lagna, planet_signs)
    yoga = _consecutive_7_yoga(start=1)

    result = _evaluate_yoga(yoga, state)
    assert result is not None and result["fired"] is True, (
        "T4 FAIL: 7 planets in 7 consecutive houses (one per house) must fire; "
        f"got {result}"
    )
