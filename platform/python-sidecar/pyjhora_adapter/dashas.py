"""
dashas.py — Vimshottari mahadasha chain.

Returns {'mahadasha_sequence': [{lord, lord_id, start_iso, start_jd}, ...]} so
the L2.5 builder (which reads dashas['mahadasha_sequence'][0]['lord']) and the
downstream dashas_writer both find what they expect.

PyJHora's vimsottari_mahadasa returns an OrderedDict {planet_id: jd_start}; we
convert each start JD to an ISO date and resolve the planet id to a name.
"""
from __future__ import annotations

from typing import Any

from . import _names
from ._ayanamsha import resolve_mode
from ._jhora import drik, get_vimsottari, utils

# Vimshottari mahadasha lengths (years) by planet id.
_VIMSHOTTARI_YEARS = {
    0: 6, 1: 10, 2: 7, 3: 17, 4: 16, 5: 20, 6: 19, 7: 18, 8: 7,
}


def _place(lat: float, lon: float, tz: float):
    return drik.Place("subject", lat, lon, tz)


def _jd_to_iso(jd: float) -> str:
    y, m, d, frac = utils.jd_to_gregorian(jd)
    hh = int(frac)
    mm = int((frac - hh) * 60)
    ss = int(round((((frac - hh) * 60) - mm) * 60))
    if ss >= 60:
        ss = 59
    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}T{hh:02d}:{mm:02d}:{ss:02d}"


def compute_dashas(
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
    vimsottari = get_vimsottari()

    md = vimsottari.vimsottari_mahadasa(jd_ut, place)
    items = list(md.items())  # [(lord_id, jd_start), ...] in dasha order

    sequence: list[dict[str, Any]] = []
    for idx, (lord_id, jd_start) in enumerate(items):
        lid = int(lord_id)
        years = _VIMSHOTTARI_YEARS.get(lid)
        start_iso = _jd_to_iso(jd_start)
        # end = next item's start, else start + years
        if idx + 1 < len(items):
            end_iso = _jd_to_iso(items[idx + 1][1])
        else:
            end_iso = _jd_to_iso(jd_start + (years or 0) * 365.2425)
        sequence.append({
            "lord": _names.PLANET_NAMES.get(lid, f"P{lid}"),
            "planet": _names.PLANET_NAMES.get(lid, f"P{lid}"),
            "lord_id": lid,
            "years": years,
            "start_jd": float(jd_start),
            "start_iso": start_iso,
            "end_iso": end_iso,
        })

    return {
        "system": "vimshottari",
        "mahadasha_sequence": sequence,
    }
