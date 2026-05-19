"""
planets.py — Planetary state computation for all 9 grahas.

All longitudes are sidereal (Lahiri ayanamsha, which must be set before calling).

CRITICAL: Always use swe.MEAN_NODE for Rahu. TRUE_NODE was the Phase 4B bug;
this module uses MEAN_NODE from day-1. An assertion guards against accidental
switch to TRUE_NODE. Ketu = Rahu + 180° (mod 360).

References:
- Parasara Hora Shastra (graha characteristics and combustion rules)
- Phaladeepika (Mantresvara) §4 — combustion orbs
- Phase 4B standard: MEAN_NODE for Rahu/Ketu throughout MARSYS-JIS
"""
import swisseph as swe
from .types import PlanetState
from .shastra_tables import (
    SIGN_NAMES, NAKSHATRA_NAMES, COMBUSTION_ORBS,
)

# swisseph flags for sidereal positions
_SWE_FLAGS = swe.FLG_SIDEREAL | swe.FLG_SWIEPH

# The 9 Vedic grahas (8 physical + Ketu derived from Rahu)
# Ketu is not in this list — it is computed as Rahu + 180°.
# CRITICAL: swe.MEAN_NODE for Rahu, NOT swe.TRUE_NODE (Phase 4B standard).
NINE_GRAHAS_SWE = [
    swe.SUN,        # Surya
    swe.MOON,       # Chandra
    swe.MARS,       # Mangala
    swe.MERCURY,    # Budha
    swe.JUPITER,    # Brihaspati/Guru
    swe.VENUS,      # Shukra
    swe.SATURN,     # Shani
    swe.MEAN_NODE,  # Rahu (MEAN_NODE — TRUE_NODE is explicitly forbidden per Phase 4B)
    # Ketu derived below as Rahu + 180° (mod 360)
]

# Human-readable names aligned with NINE_GRAHAS_SWE order
_GRAHA_NAMES = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu",
    # "Ketu" appended after derivation
]

_NAKSHATRA_SPAN = 360.0 / 27   # ≈ 13.333°
_PADA_SPAN = _NAKSHATRA_SPAN / 4  # ≈ 3.333°
_SIGN_SPAN = 30.0               # Each sign = 30°


def _lon_to_sign(lon: float) -> tuple[int, str]:
    """Return (sign_id 1..12, sign_name) for a sidereal longitude."""
    sign_idx = int(lon / _SIGN_SPAN) % 12
    return sign_idx + 1, SIGN_NAMES[sign_idx]


def _lon_to_nakshatra(lon: float) -> tuple[int, str, int]:
    """Return (nakshatra_id 1..27, nakshatra_name, pada 1..4) for a sidereal longitude."""
    nak_idx = int(lon / _NAKSHATRA_SPAN) % 27
    nak_id = nak_idx + 1
    nak_name = NAKSHATRA_NAMES[nak_idx]
    pos_in_nak = lon - nak_idx * _NAKSHATRA_SPAN
    pada = int(pos_in_nak / _PADA_SPAN) + 1
    if pada > 4:
        pada = 4
    return nak_id, nak_name, pada


def _angular_distance(a: float, b: float) -> float:
    """Shortest angular distance from b to a, always positive (0..180)."""
    diff = abs(a - b) % 360
    if diff > 180:
        diff = 360 - diff
    return diff


def _is_combust(planet_name: str, planet_lon: float, sun_lon: float,
                retrograde: bool) -> bool:
    """
    Return True if the planet is within its combustion orb of the Sun.
    Rahu and Ketu (shadow planets) are never combust — they have no physical body.
    Source: Phaladeepika §4; COMBUSTION_ORBS in shastra_tables.py.
    """
    if planet_name in ("Sun", "Rahu", "Ketu"):
        return False   # Sun cannot combust itself; shadow planets never combust

    orbs = COMBUSTION_ORBS.get(planet_name)
    if orbs is None:
        return False

    orb = orbs["retro"] if retrograde else orbs["direct"]
    if orb is None:
        return False

    dist = _angular_distance(planet_lon, sun_lon)
    return dist <= orb


def compute_planet_state(planet_id: int, jd_ut: float,
                         sun_lon: float | None = None,
                         planet_name: str | None = None) -> PlanetState:
    """
    Compute the sidereal state of a single graha at jd_ut.

    Args:
        planet_id: swisseph planet constant (e.g. swe.SUN, swe.MEAN_NODE).
                   Use swe.MEAN_NODE for Rahu — NEVER swe.TRUE_NODE (Phase 4B mandate).
        jd_ut: Julian Day (Universal Time)
        sun_lon: Sun's sidereal longitude (for combustion check). If None,
                 Sun is computed internally (slightly less efficient for batch calls).
        planet_name: Override name (used for Ketu which is derived, not directly computed).

    Returns:
        PlanetState with all fields populated.

    ASSERTION: If planet_id == swe.TRUE_NODE, raises AssertionError immediately.
               This guards against accidental switch away from the Phase 4B standard.
    """
    # Guard: TRUE_NODE is forbidden (Phase 4B bug prevention)
    assert planet_id != swe.TRUE_NODE, (
        "MEAN_NODE (not TRUE_NODE) is the Phase 4B standard for Rahu. "
        "Use swe.MEAN_NODE for Rahu and derive Ketu as Rahu+180°."
    )

    # Compute position
    result = swe.calc_ut(jd_ut, planet_id, _SWE_FLAGS)
    lon = result[0][0] % 360.0
    speed = result[0][3]   # degrees/day; negative = retrograde

    retrograde = speed < 0

    # Moon is never "retrograde" in the traditional sense (always prograde);
    # Sun is always prograde (speed never negative).
    if planet_id in (swe.SUN, swe.MOON):
        retrograde = False

    # Mean Node is always retrograde in the mean approximation
    if planet_id == swe.MEAN_NODE:
        retrograde = True

    sign_id, sign_name = _lon_to_sign(lon)
    nak_id, nak_name, pada = _lon_to_nakshatra(lon)

    # Determine name
    if planet_name is None:
        idx = NINE_GRAHAS_SWE.index(planet_id) if planet_id in NINE_GRAHAS_SWE else -1
        planet_name = _GRAHA_NAMES[idx] if idx >= 0 else f"Planet_{planet_id}"

    # Combustion check
    if sun_lon is None:
        sun_result = swe.calc_ut(jd_ut, swe.SUN, _SWE_FLAGS)
        sun_lon = sun_result[0][0] % 360.0

    combust = _is_combust(planet_name, lon, sun_lon, retrograde)

    return PlanetState(
        name=planet_name,
        longitude_sidereal=lon,
        sign_id=sign_id,
        sign_name=sign_name,
        nakshatra_id=nak_id,
        nakshatra_name=nak_name,
        nakshatra_pada=pada,
        retrograde=retrograde,
        combust=combust,
    )


def compute_all_grahas(jd_ut: float) -> list[PlanetState]:
    """
    Compute sidereal state for all 9 Vedic grahas at jd_ut.

    Returns a list of 9 PlanetState objects in order:
        Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu

    RAHU = swe.MEAN_NODE (Phase 4B mandate — TRUE_NODE is explicitly forbidden).
    KETU = Rahu longitude + 180° (mod 360), derived — not separately computed.

    Both Rahu and Ketu are never combust (shadow planets have no physical body).
    """
    # Compute Sun first (needed for combustion checks)
    sun_result = swe.calc_ut(jd_ut, swe.SUN, _SWE_FLAGS)
    sun_lon = sun_result[0][0] % 360.0

    states: list[PlanetState] = []

    # Compute the 8 non-Ketu grahas
    for planet_id, name in zip(NINE_GRAHAS_SWE, _GRAHA_NAMES):
        state = compute_planet_state(planet_id, jd_ut,
                                     sun_lon=sun_lon,
                                     planet_name=name)
        states.append(state)

    # Derive Ketu from Rahu (Rahu + 180° mod 360°)
    rahu_state = states[-1]   # Last in list = Rahu
    ketu_lon = (rahu_state.longitude_sidereal + 180.0) % 360.0
    ketu_sign_id, ketu_sign_name = _lon_to_sign(ketu_lon)
    ketu_nak_id, ketu_nak_name, ketu_pada = _lon_to_nakshatra(ketu_lon)

    ketu = PlanetState(
        name="Ketu",
        longitude_sidereal=ketu_lon,
        sign_id=ketu_sign_id,
        sign_name=ketu_sign_name,
        nakshatra_id=ketu_nak_id,
        nakshatra_name=ketu_nak_name,
        nakshatra_pada=ketu_pada,
        retrograde=True,   # Ketu is always retrograde (derived from Rahu)
        combust=False,     # Shadow planet — never combust
    )
    states.append(ketu)

    # Verify Rahu and Ketu are 180° apart (assertion for correctness)
    rahu_lon = rahu_state.longitude_sidereal
    separation = _angular_distance(rahu_lon, ketu_lon)
    assert abs(separation - 180.0) < 0.001, (
        f"Rahu-Ketu separation is {separation}°, expected 180°. "
        "This indicates a derivation error."
    )

    return states
