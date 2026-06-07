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
