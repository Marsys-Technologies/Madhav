"""
houses.py — Lagna (ascendant) + 12 whole-sign houses.

Whole-sign is the default house system for this instrument: house 1 = the sign
the Lagna falls in,
houses 2..12 follow in zodiacal order.
"""
from __future__ import annotations

from typing import Any

from . import _names
from ._ayanamsha import resolve_mode
from ._jhora import drik


def _place(lat: float, lon: float, tz: float):
    return drik.Place("subject", lat, lon, tz)


def compute_ascendant(
    jd_ut: float,
    ayanamsha_id: str = "lahiri",
    *,
    lat: float = 0.0,
    lon: float = 0.0,
    tz: float = 0.0,
) -> dict[str, Any]:
    # jd_ut MUST be a LOCAL-time Julian Day (utils.julian_day_number(date, local_tob)).
    # Passing a UTC-based JD (swe.julday with UT hours) gives a ~9-sign error for IST
    # births because drik.ascendant does its own UT conversion using the Place timezone.
    mode, _sidm = resolve_mode(ayanamsha_id)
    drik.set_ayanamsa_mode(mode)
    place = _place(lat, lon, tz)
    asc = drik.ascendant(jd_ut, place)
    # ascendant -> [sign_idx, deg_in_sign, nak_idx, pada]
    sign_idx = int(asc[0])
    deg_in_sign = float(asc[1])
    full_long = sign_idx * 30.0 + deg_in_sign
    nak = int(asc[2]) if len(asc) > 2 else 0
    pada = int(asc[3]) if len(asc) > 3 else 0
    return {
        "longitude_deg": full_long,
        "degree_in_sign": deg_in_sign,
        "sign": _names.sign_name(sign_idx),
        "sign_id": sign_idx + 1,  # 1-based per L2.5 contract
        "sign_lord": _names.sign_lord(sign_idx),
        "nakshatra": _names.nakshatra_name(nak) if nak else None,
        "nakshatra_id": nak,
        "pada": pada,
    }


def compute_midheaven(
    jd_ut: float,
    ayanamsha_id: str = "lahiri",
    *,
    lat: float = 0.0,
    lon: float = 0.0,
    tz: float = 0.0,
) -> dict[str, Any]:
    """
    D-9 fix (R6 1d-sensitive lane, 2026-07-10): real MC (Midheaven) from
    Swiss Ephemeris, replacing the previous `Lagna + 270°` computable
    substitute (a non-canonical approximation banned by canonical-or-floor —
    true MC diverges from Lagna+270 by several degrees at this birth
    latitude/longitude).

    Mirrors drik.ascendant() exactly (drik.py:1667-1684) but reads
    ascmc[1] (MC) instead of ascmc[0] (Asc) from the same swe.houses_ex()
    call, using the same ayanamsha/sidereal flags so MC and Lagna are
    computed from the identical ephemeris state.
    """
    mode, _sidm = resolve_mode(ayanamsha_id)
    drik.set_ayanamsa_mode(mode)
    place = _place(lat, lon, tz)
    _, plat, plon, ptz = place
    jd_utc = jd_ut - (ptz / 24.0)
    swe = drik.swe
    if drik.const._TROPICAL_MODE:
        flags = swe.FLG_SWIEPH
    else:
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | drik._rise_flags
    ascmc = swe.houses_ex(jd_utc, plat, plon, flags=flags)[1]
    nirayana_mc = drik.utils.norm360(ascmc[1])
    sign_idx = int(nirayana_mc / 30.0)
    deg_in_sign = nirayana_mc - sign_idx * 30.0
    nak_no, pada, _ = drik.nakshatra_pada(nirayana_mc)
    return {
        "longitude_deg": nirayana_mc,
        "degree_in_sign": deg_in_sign,
        "sign": _names.sign_name(sign_idx),
        "sign_id": sign_idx + 1,
        "sign_lord": _names.sign_lord(sign_idx),
        "nakshatra": _names.nakshatra_name(nak_no) if nak_no else None,
        "nakshatra_id": nak_no,
        "pada": pada,
    }


def compute_houses(ascendant: dict[str, Any]) -> list[dict[str, Any]]:
    """12 whole-sign houses starting from the Lagna sign."""
    # ascendant['sign_id'] is 1-based; convert to 0-based for arithmetic.
    asc_sign0 = int(ascendant["sign_id"]) - 1
    houses: list[dict[str, Any]] = []
    for h in range(12):
        sign_idx = (asc_sign0 + h) % 12
        houses.append({
            "house_number": h + 1,
            "house_num": h + 1,  # alias for l25_builder
            "sign": _names.sign_name(sign_idx),
            "sign_id": sign_idx + 1,  # 1-based per L2.5 contract
            "sign_lord": _names.sign_lord(sign_idx),
        })
    return houses
