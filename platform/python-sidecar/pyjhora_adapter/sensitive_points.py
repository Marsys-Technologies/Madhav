"""
sensitive_points.py — Gulika, Maandi, and the kaala-group upagrahas.

PyJHora's upagraha_longitude(dob, tob, place, planet_index, upagraha_part)
returns [sign_idx, deg_in_sign]. We compute the six 'other' upagrahas
(kaala, mrityu, artha_prabhakara, yama, gulika, maandi) and return each as a
{sign, sign_id, longitude_deg} dict.
"""
from __future__ import annotations

from typing import Any

from . import _names
from ._ayanamsha import resolve_mode
from ._jhora import drik, utils

# (name, planet_index, upagraha_part) per PyJHora's upagraha_longitude doc.
_UPAGRAHAS = [
    ("kaala", 0, "middle"),
    ("mrityu", 2, "middle"),
    ("artha_prabhakara", 3, "middle"),
    ("yama", 4, "middle"),
    ("gulika", 6, "middle"),
    ("maandi", 6, "begin"),
]


def _place(lat: float, lon: float, tz: float):
    return drik.Place("subject", lat, lon, tz)


def compute_sensitive_points(
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

    y, m, d, frac = utils.jd_to_gregorian(jd_ut)
    hh = int(frac)
    mm = int((frac - hh) * 60)
    ss = int(round((((frac - hh) * 60) - mm) * 60))
    if ss >= 60:
        ss = 59
    dob = drik.Date(int(y), int(m), int(d))
    tob = (hh, mm, ss)

    out: dict[str, Any] = {}
    for name, pidx, part in _UPAGRAHAS:
        try:
            res = drik.upagraha_longitude(dob, tob, place, pidx, upagraha_part=part)
            sign_idx = int(res[0])
            deg = float(res[1])
            out[name] = {
                "sign": _names.sign_name(sign_idx),
                "sign_id": sign_idx + 1,  # 1-based per L2.5 contract
                "degree_in_sign": deg,
                "longitude_deg": sign_idx * 30.0 + deg,
            }
        except Exception as exc:  # noqa: BLE001
            out[name] = {"error": f"{name} failed: {exc!r}"}
    return out
