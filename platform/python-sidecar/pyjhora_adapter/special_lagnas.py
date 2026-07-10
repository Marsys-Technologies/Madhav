"""
special_lagnas.py — Bhava/Hora/Ghati/Vighati/Indu/Sree/Pranapada/Bhrigu-Bindhu/
Kunda/Varnada Lagna, delegated entirely to PyJHora (jhora.panchanga.drik +
jhora.horoscope.chart.charts).

M-9 + M-10 fix (R6 1d-sensitive lane, 2026-07-10): the prior ga_sensitive_writer
computed Bhava/Hora/Ghati Lagna and "Pranapada Sphuta" as hand-rolled proxies
using the Sun's within-sign degree as a crude time-since-sunrise stand-in
(HL = Lagna + (Sun%30)*2, GL = Lagna + (Sun%30)*12, BL = 2*Sun - Lagna + 180,
Pranapada = Moon + (Lagna-Sun)*4 falsely cited "BPHS"). These are non-classical
approximations. PyJHora computes all of these correctly from the real
time-elapsed-since-sunrise (ghatis) at the birth place/moment via
`drik.special_ascendant()` (Bhava/Hora/Ghati/Vighati Lagna) and
`drik.pranapada_lagna()` (real BPHS Pranapada: ghatis-since-sunrise x4,
+ Sun's sign-category offset 0/120/240 for movable/dual/fixed) — see
drik.py:1959-2140.

Indu Lagna, Sree Lagna, Bhrigu Bindhu Lagna, Kunda Lagna, and Varnada Lagna
were previously absent entirely from this writer; added here via direct
PyJHora delegation per the M-10 fix instruction ("delegate to PyJHora's
implementations rather than in-house approximations").
"""
from __future__ import annotations

from typing import Any

from . import _names
from ._ayanamsha import resolve_mode
from ._jhora import drik


def _place(lat: float, lon: float, tz: float):
    return drik.Place("subject", lat, lon, tz)


def _to_dict(sign_idx: int, deg: float) -> dict[str, Any]:
    sign_idx = int(sign_idx)
    deg = float(deg)
    return {
        "sign": _names.sign_name(sign_idx),
        "sign_id": sign_idx + 1,
        "degree_in_sign": deg,
        "longitude_deg": sign_idx * 30.0 + deg,
    }


def compute_special_lagnas(
    jd_ut: float,
    dob: Any,
    tob: tuple[int, int, int],
    ayanamsha_id: str = "lahiri",
    *,
    lat: float = 0.0,
    lon: float = 0.0,
    tz: float = 0.0,
) -> dict[str, Any]:
    """
    Returns a dict of {name: {sign, sign_id, degree_in_sign, longitude_deg}}
    for: bhava_lagna, hora_lagna, ghati_lagna, vighati_lagna, indu_lagna,
    sree_lagna, pranapada_lagna, bhrigu_bindhu_lagna, kunda_lagna,
    varnada_lagna. On failure for any single lagna, that entry carries
    {"error": ...} rather than aborting the whole batch.
    """
    mode, _sidm = resolve_mode(ayanamsha_id)
    drik.set_ayanamsa_mode(mode)
    place = _place(lat, lon, tz)

    out: dict[str, Any] = {}

    # jd-only special ascendants (drik.py:1959-1988, 2107-2281)
    _jd_only = [
        ("bhava_lagna", drik.bhava_lagna),
        ("hora_lagna", drik.hora_lagna),
        ("ghati_lagna", drik.ghati_lagna),
        ("vighati_lagna", drik.vighati_lagna),
        ("indu_lagna", drik.indu_lagna),
        ("sree_lagna", drik.sree_lagna),
        ("pranapada_lagna", drik.pranapada_lagna),
        ("bhrigu_bindhu_lagna", drik.bhrigu_bindhu_lagna),
        ("kunda_lagna", drik.kunda_lagna),
    ]
    for name, fn in _jd_only:
        try:
            sign_idx, deg = fn(jd_ut, place)
            out[name] = _to_dict(sign_idx, deg)
        except Exception as exc:  # noqa: BLE001
            out[name] = {"error": f"{name} failed: {exc!r}"}

    # Varnada Lagna needs (dob, tob, place) not jd (charts.py:1749) — BV Raman
    # method (varnada_method=1), house_index=1 (Varnada of the Lagna itself).
    try:
        from jhora.horoscope.chart import charts as _charts
        sign_idx, deg = _charts.varnada_lagna(dob, tob, place, house_index=1, varnada_method=1)
        out["varnada_lagna"] = _to_dict(sign_idx, deg)
    except Exception as exc:  # noqa: BLE001
        out["varnada_lagna"] = {"error": f"varnada_lagna failed: {exc!r}"}

    return out
