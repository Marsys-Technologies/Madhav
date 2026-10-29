"""Independent direct ephemeris computation for the foreign-birth detectors (SUR-RB-6).

Deliberately shares NO code with the engine or with L1: it imports only the standard library and
pyswisseph, and does its own arithmetic for the true UT, the sidereal (Lahiri) longitudes, the
ascendant and the Vimshottari start. ``ephe_path`` must hold the pinned .se1 files; there is no
Moshier fallback here (a different ephemeris would blur the comparison).
"""

from __future__ import annotations

from typing import Dict, Tuple

import swisseph as swe

BODIES = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN}
VIM_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
VIM_YEARS = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7, "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}


def true_ut_jd(y: int, mo: int, d: int, hh: int, mm: int, ss: int, offset_minutes: int) -> float:
    """Julian day (UT) of a LOCAL wall-clock time on the Gregorian calendar given its UT offset (minutes, east positive)."""
    jd_local_as_ut = swe.julday(y, mo, d, hh + mm / 60.0 + ss / 3600.0)
    return jd_local_as_ut - offset_minutes / 1440.0


def setup(ephe_path: str) -> None:
    swe.set_ephe_path(ephe_path)
    swe.set_sid_mode(swe.SIDM_LAHIRI)


def sidereal_longitudes(jd_ut: float) -> Dict[str, float]:
    # Geometric (true) positions, the convention L1's PyJHora path uses (it omits aberration/light-time): the Sun then
    # agrees to the last printed digit, whereas apparent positions would differ by ~20 arcsec for the Sun.
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_TRUEPOS
    out = {}
    for name, body in BODIES.items():
        pos, _ret = swe.calc_ut(jd_ut, body, flags)
        out[name] = pos[0] % 360.0
    return out


def sidereal_ascendant(jd_ut: float, lat: float, lon: float) -> float:
    _cusps, ascmc = swe.houses_ex(jd_ut, lat, lon, b"W", swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
    return ascmc[0] % 360.0


def vimshottari_start(moon_sidereal: float, jd_birth_ut: float) -> Tuple[str, float]:
    """(lord, start JD) of the mahadasha running at birth: elapsed fraction of the Moon's nakshatra x the lord's years (365.25 d)."""
    span = 360.0 / 27.0
    idx = int(moon_sidereal // span)
    lord = VIM_ORDER[idx % 9]
    frac = (moon_sidereal - idx * span) / span
    return lord, jd_birth_ut - frac * VIM_YEARS[lord] * 365.25
