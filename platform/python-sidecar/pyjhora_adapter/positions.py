"""
positions.py — 9 graha sidereal longitudes via PyJHora drik.dhasavarga (D1).

We call drik.dhasavarga(..., set_rahu_ketu_as_true_nodes=False) DIRECTLY rather
than charts.rasi_chart, because charts.rasi_chart hardcodes the osculating TRUE
node (swe.TRUE_NODE), which (a) diverges from the project's MEAN_NODE convention
and (b) fails under some ayanamshas (TRUE_CITRA) with a swisseph Moshier
out-of-range error since no planetary .se1 ephemeris files ship with the wheel.
Forcing MEAN nodes keeps Rahu/Ketu exactly 180 deg apart and ephemeris-free.
"""
from __future__ import annotations

from typing import Any

from . import _names
from ._ayanamsha import resolve_mode
from ._jhora import drik

# Use mean nodes (swe.MEAN_NODE) for Rahu/Ketu — matches natal_engine.
_USE_TRUE_NODES = False


def _place(lat: float, lon: float, tz: float):
    return drik.Place("subject", lat, lon, tz)


def _set_ayanamsha(ayanamsha_id: str, jd_ut: float) -> float:
    mode, _sidm = resolve_mode(ayanamsha_id)
    drik.set_ayanamsa_mode(mode)
    return float(drik.get_ayanamsa_value(jd_ut))


def _nakshatra_for_long(full_long: float) -> tuple[int, int]:
    """Return (nakshatra_1based, pada_1based) for a full sidereal longitude."""
    np_res = drik.nakshatra_pada(full_long)
    nak = int(np_res[0])
    pada = int(np_res[1])
    return nak, pada


def compute_positions(
    jd_ut: float,
    ayanamsha_id: str = "lahiri",
    *,
    lat: float = 0.0,
    lon: float = 0.0,
    tz: float = 0.0,
) -> list[dict[str, Any]]:
    """Compute the 9 grahas (Sun..Ketu) for the given jd + ayanamsha."""
    place = _place(lat, lon, tz)
    _set_ayanamsha(ayanamsha_id, jd_ut)

    # dhasavarga returns [[planet_id, (rasi, deg_in_sign)], ...] for the 9
    # grahas (NO ascendant). Mean nodes forced.
    pp = drik.dhasavarga(
        jd_ut, place, divisional_chart_factor=1,
        set_rahu_ketu_as_true_nodes=_USE_TRUE_NODES,
    )
    retro_ids = set(drik.planets_in_retrograde(jd_ut, place))

    by_id = {int(row[0]): row for row in pp}
    grahas: list[dict[str, Any]] = []
    for pid in _names.GRAHA_ORDER:
        row = by_id.get(pid)
        if row is None:
            continue
        sign_idx = int(row[1][0])
        deg_in_sign = float(row[1][1])
        full_long = sign_idx * 30.0 + deg_in_sign
        nak, pada = _nakshatra_for_long(full_long)
        name = _names.PLANET_NAMES.get(pid, f"P{pid}")
        is_retro = pid in retro_ids
        grahas.append({
            "name": name,
            "planet_id": pid,
            "longitude_deg": full_long,
            "longitude": full_long,
            "lon": full_long,
            "degree_in_sign": deg_in_sign,
            "sign": _names.sign_name(sign_idx),
            "sign_id": sign_idx + 1,  # 1-based (Aries=1..Pisces=12) per L2.5 contract
            "sign_lord": _names.sign_lord(sign_idx),
            "nakshatra": _names.nakshatra_name(nak),
            "nakshatra_id": nak,
            "nakshatra_num": nak,
            "nakshatra_pada": pada,
            "pada": pada,
            "nakshatra_lord": _names.nakshatra_lord(nak),
            "retrograde": bool(is_retro),
            "combust": False,  # refined in dignities.refine
        })
    return grahas
