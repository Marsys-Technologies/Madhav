"""
ascendant.py — Sidereal ascendant computation via pyswisseph.
"""

from __future__ import annotations

import swisseph as swe

from .positions import _lon_to_nakshatra, _lon_to_sign
from .schema import Ascendant


def compute_ascendant(jd_ut: float, latitude_deg: float, longitude_deg: float) -> Ascendant:
    """Sidereal ascendant. `set_ayanamsha(...)` must have been called.

    Uses Placidus by default. The ascendant value `ascmc[0]` is
    house-system-independent at moderate latitudes — verified identical
    across {P, E, W, A} at the native lat. At extreme latitudes (|lat| > 66.6°)
    Placidus throws; we fall back to 'A' (Equal-from-Asc, polar-safe) which
    still emits a valid ascendant.
    """
    try:
        cusps, ascmc = swe.houses_ex(
            jd_ut, latitude_deg, longitude_deg, b"P", swe.FLG_SIDEREAL
        )
    except swe.Error:
        # Polar fallback — Equal-from-Asc, robust at any latitude.
        cusps, ascmc = swe.houses_ex(
            jd_ut, latitude_deg, longitude_deg, b"A", swe.FLG_SIDEREAL
        )
    asc_lon = ascmc[0] % 360.0
    sign_id, sign_name = _lon_to_sign(asc_lon)
    nak_id, nak_name, pada = _lon_to_nakshatra(asc_lon)
    return Ascendant(
        longitude_deg=asc_lon,
        sign=sign_name,
        sign_id=sign_id,
        nakshatra=nak_name,
        nakshatra_id=nak_id,
        pada=pada,
    )
