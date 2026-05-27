"""
ascendant.py — Sidereal ascendant computation via pyswisseph.
"""

from __future__ import annotations

import swisseph as swe

from .positions import _lon_to_nakshatra, _lon_to_sign
from .schema import Ascendant


def compute_ascendant(jd_ut: float, latitude_deg: float, longitude_deg: float) -> Ascendant:
    """Sidereal ascendant. `set_ayanamsha(...)` must have been called."""
    # 'P' = Placidus (cusps not used for sidereal lagna but houses() needs a system)
    cusps, ascmc = swe.houses_ex(
        jd_ut, latitude_deg, longitude_deg, b"P", swe.FLG_SIDEREAL
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
