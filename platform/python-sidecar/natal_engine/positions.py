"""
positions.py — Graha longitude computation via pyswisseph.

This is the load-bearing astronomical primitive. All other modules
(houses, dignities, vargas, dashas, sensitive_points) consume the graha
states this module produces.

Conventions (must not drift):
- Sidereal zodiac; ayanamsha set via `swe.set_sid_mode(...)` per the
  configured `ayanamsha_config_id` (default: Lahiri / SIDM_LAHIRI).
- `swe.MEAN_NODE` for Rahu — TRUE_NODE is forbidden (Phase 4B standard,
  see panchang_engine/planets.py).
- Ketu derived as `(Rahu + 180.0) mod 360`.
- 9 grahas total: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu.

This module is pure: no I/O, no LLM, no DB.
"""

from __future__ import annotations

import swisseph as swe

from .schema import GrahaState

# Sign + nakshatra naming. Mirror of panchang_engine/shastra_tables.py to keep
# the natal_engine self-contained (no cross-module reach during scaffold phase).
SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

# Dignity scaffold — exaltation/debilitation/own signs per BPHS. Friend/enemy
# tables are stubbed for the scaffold; unit 1.2 fills in the temporal-friendship
# refinements per JH parity.
_EXALTATION = {
    "Sun": 1,        # Aries
    "Moon": 2,       # Taurus
    "Mars": 10,      # Capricorn
    "Mercury": 6,    # Virgo
    "Jupiter": 4,    # Cancer
    "Venus": 12,     # Pisces
    "Saturn": 7,     # Libra
    "Rahu": 3,       # Gemini (most schools)
    "Ketu": 9,       # Sagittarius (most schools)
}
_DEBILITATION = {n: ((s - 1 + 6) % 12) + 1 for n, s in _EXALTATION.items()}

# Own signs per BPHS Ch.3
_OWN_SIGNS: dict[str, set[int]] = {
    "Sun": {5},
    "Moon": {4},
    "Mars": {1, 8},
    "Mercury": {3, 6},
    "Jupiter": {9, 12},
    "Venus": {2, 7},
    "Saturn": {10, 11},
    "Rahu": set(),  # no traditional own-sign; left empty for scaffold
    "Ketu": set(),
}

# swisseph graha codes — Rahu uses MEAN_NODE (Phase 4B standard).
NINE_GRAHAS_SWE: list[tuple[str, int]] = [
    ("Sun", swe.SUN),
    ("Moon", swe.MOON),
    ("Mars", swe.MARS),
    ("Mercury", swe.MERCURY),
    ("Jupiter", swe.JUPITER),
    ("Venus", swe.VENUS),
    ("Saturn", swe.SATURN),
    ("Rahu", swe.MEAN_NODE),
]

_NAKSHATRA_SPAN = 360.0 / 27.0
_PADA_SPAN = _NAKSHATRA_SPAN / 4.0
_SIGN_SPAN = 30.0

_SWE_FLAGS = swe.FLG_SIDEREAL | swe.FLG_SWIEPH | swe.FLG_SPEED


def _lon_to_sign(lon: float) -> tuple[int, str]:
    sign_idx = int(lon // _SIGN_SPAN) % 12
    return sign_idx + 1, SIGN_NAMES[sign_idx]


def _lon_to_nakshatra(lon: float) -> tuple[int, str, int]:
    nak_idx = int(lon // _NAKSHATRA_SPAN) % 27
    pada = int((lon - nak_idx * _NAKSHATRA_SPAN) // _PADA_SPAN) + 1
    pada = max(1, min(4, pada))
    return nak_idx + 1, NAKSHATRA_NAMES[nak_idx], pada


def _dignity_for(name: str, sign_id: int) -> str:
    if _EXALTATION.get(name) == sign_id:
        return "exalted"
    if _DEBILITATION.get(name) == sign_id:
        return "debilitated"
    if sign_id in _OWN_SIGNS.get(name, set()):
        return "own"
    # friend / enemy / neutral refinement deferred to unit 1.2
    return "unknown"


def set_ayanamsha(ayanamsha_config_id: str) -> None:
    """Configure swisseph's sidereal mode by config id.

    Accepted ids (extensible — add more in unit 1.2 as needed):
    - 'lahiri'                   → swe.SIDM_LAHIRI (default)
    - 'lahiri-chitrapaksha-true' → swe.SIDM_LAHIRI (alias, same backend)
    - 'raman'                    → swe.SIDM_RAMAN
    - 'krishnamurti'             → swe.SIDM_KRISHNAMURTI
    """
    config = ayanamsha_config_id.lower()
    if config in ("lahiri", "lahiri-chitrapaksha-true"):
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    elif config == "raman":
        swe.set_sid_mode(swe.SIDM_RAMAN, 0, 0)
    elif config == "krishnamurti":
        swe.set_sid_mode(swe.SIDM_KRISHNAMURTI, 0, 0)
    else:
        raise ValueError(f"Unknown ayanamsha_config_id: {ayanamsha_config_id!r}")


def compute_graha_states(jd_ut: float) -> list[GrahaState]:
    """Compute the 9 graha states at the given Julian Day (UT).

    Caller must have already invoked `set_ayanamsha(...)`.
    """
    states: list[GrahaState] = []
    for name, swe_code in NINE_GRAHAS_SWE:
        result, _ = swe.calc_ut(jd_ut, swe_code, _SWE_FLAGS)
        lon = result[0] % 360.0
        speed = result[3]
        retrograde = speed < 0.0
        sign_id, sign_name = _lon_to_sign(lon)
        nak_id, nak_name, pada = _lon_to_nakshatra(lon)
        states.append(
            GrahaState(
                name=name,
                longitude_deg=lon,
                sign=sign_name,
                sign_id=sign_id,
                nakshatra=nak_name,
                nakshatra_id=nak_id,
                pada=pada,
                retrograde=retrograde,
                speed_deg_per_day=speed,
                dignity_status=_dignity_for(name, sign_id),
            )
        )

    # Ketu = Rahu + 180° mod 360. Speed = -Rahu.speed (counter-node).
    rahu = next(s for s in states if s.name == "Rahu")
    ketu_lon = (rahu.longitude_deg + 180.0) % 360.0
    ketu_sign_id, ketu_sign_name = _lon_to_sign(ketu_lon)
    ketu_nak_id, ketu_nak_name, ketu_pada = _lon_to_nakshatra(ketu_lon)
    states.append(
        GrahaState(
            name="Ketu",
            longitude_deg=ketu_lon,
            sign=ketu_sign_name,
            sign_id=ketu_sign_id,
            nakshatra=ketu_nak_name,
            nakshatra_id=ketu_nak_id,
            pada=ketu_pada,
            retrograde=True,  # nodes are always retrograde in mean-node convention
            speed_deg_per_day=-rahu.speed_deg_per_day,
            dignity_status=_dignity_for("Ketu", ketu_sign_id),
        )
    )

    return states
