"""
panchanga.py — tithi / vara / nakshatra (moon) / yoga / karana.

Restored in GA3 (feature/ga3-chart-facts-writer): this module was deleted in
Phase 0 (c78c0d45) but compute.py still imports it, breaking the entire
pyjhora_adapter. compute.py calls compute_panchanga(); the panchanga_instant
service (panchang_engine/) handles the production panchanga API — this file
serves the in-process chart computation pipeline only.

Uses PyJHora's drik panchanga functions and resolves the returned numeric
indices to canonical names via _names.
"""
from __future__ import annotations

from typing import Any

from . import _names
from ._ayanamsha import resolve_mode
from ._jhora import drik


def _place(lat: float, lon: float, tz: float):
    return drik.Place("subject", lat, lon, tz)


def compute_panchanga(
    jd_ut: float,
    ayanamsha_id: str = "lahiri",
    *,
    lat: float = 0.0,
    lon: float = 0.0,
    tz: float = 0.0,
) -> dict[str, Any]:
    """Compute birth-instant panchanga (tithi, vara, nakshatra, yoga, karana)."""
    mode, _sidm = resolve_mode(ayanamsha_id)
    drik.set_ayanamsa_mode(mode)
    place = _place(lat, lon, tz)

    nak = drik.nakshatra(jd_ut, place)        # [nak_1based, pada, ...]
    tith = drik.tithi(jd_ut, place)           # [tithi_1based, ...]
    yog = drik.yogam(jd_ut, place)            # [yoga_1based, ...]
    kar = drik.karana(jd_ut, place)           # (karana_1_to_60, ...)
    vaara = drik.vaara(jd_ut, place)          # 0=Sunday..6=Saturday

    nak_idx = int(nak[0])
    tithi_idx = int(tith[0])
    yoga_idx = int(yog[0])
    karana_idx = int(kar[0])
    vara_idx = int(vaara) % 7

    return {
        "tithi": _names.tithi_name(tithi_idx),
        "tithi_id": tithi_idx,
        "vara": _names.VARA_NAMES[vara_idx],
        "vara_id": vara_idx,
        "nakshatra": _names.nakshatra_name(nak_idx),
        "nakshatra_id": nak_idx,
        "nakshatra_pada": int(nak[1]) if len(nak) > 1 else None,
        "yoga": _names.YOGA_NAMES[yoga_idx] if 1 <= yoga_idx <= 27 else "",
        "yoga_id": yoga_idx,
        "karana": _names.karana_name(karana_idx),
        "karana_id": karana_idx,
    }
