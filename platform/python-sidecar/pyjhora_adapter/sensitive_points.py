"""
sensitive_points.py — Gulika, Maandi, the kaala-group upagrahas, and the
Sun-derived (solar) upagrahas (Dhuma/Vyatipata/Parivesha/Indrachapa/Upaketu).

PyJHora's upagraha_longitude(dob, tob, place, planet_index, upagraha_part)
returns [sign_idx, deg_in_sign]. We compute the six 'other' upagrahas
(kaala, mrityu, artha_prabhakara, yama, gulika, maandi) and return each as a
{sign, sign_id, longitude_deg} dict.

M-11/V-6/V-7 fix (R6 1d-sensitive lane, 2026-07-10): the (name, planet_index,
upagraha_part) assignment for gulika/maandi below previously had 'begin' and
'middle' SWAPPED relative to PyJHora's own canonical lambdas
(jhora.panchanga.drik.gulika_longitude uses upagraha_part='begin';
drik.maandi_longitude uses upagraha_part='middle' — see drik.py:1877-1887).
Corrected here to match PyJHora's own definitions exactly (delegate, don't
reimplement).

Solar upagrahas (dhuma/vyatipaata/parivesha/indrachaapa/upaketu) delegate to
PyJHora's own `drik.solar_upagraha_longitudes()`, which implements the BPHS
Ch.3 lambdas at drik.py:1826-1831 — this replaces the previous ga_sensitive_writer
hand-rolled re-derivation of the same formulas (which had an Upaketu bug:
Upaketu = Dhuma + 180° does NOT match PyJHora's canonical
Upaketu = Sun - 30°, and fails the classical identity Upaketu + 30° = Sun; see
register V-6).
"""
from __future__ import annotations

from typing import Any

from . import _names
from ._ayanamsha import resolve_mode
from ._jhora import drik, utils

# (name, planet_index, upagraha_part) per PyJHora's upagraha_longitude doc.
# NOTE: gulika='begin', maandi='middle' — matches drik.gulika_longitude /
# drik.maandi_longitude exactly (drik.py:1876-1887). Do not swap these.
_UPAGRAHAS = [
    ("kaala", 0, "middle"),
    ("mrityu", 2, "middle"),
    ("artha_prabhakara", 3, "middle"),
    ("yama", 4, "middle"),
    ("gulika", 6, "begin"),
    ("maandi", 6, "middle"),
]

# PyJHora's solar-upagraha names (const._solar_upagraha_list); each is a lambda
# of Sun's sidereal longitude only (drik.py:1826-1837).
_SOLAR_UPAGRAHAS = ["dhuma", "vyatipaata", "parivesha", "indrachaapa", "upaketu"]


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


def compute_solar_upagrahas(sun_longitude_sidereal: float) -> dict[str, Any]:
    """
    Dhuma, Vyatipata, Parivesha, Indrachapa, Upaketu — delegated to PyJHora's
    own `drik.solar_upagraha_longitudes(solar_longitude, upagraha)` (BPHS Ch.3
    lambdas at drik.py:1826-1837). Takes the SIDEREAL Sun longitude already
    computed for this chart's ayanamsha (caller passes it in — no separate
    ephemeris call needed since these are pure functions of Sun's longitude).
    """
    out: dict[str, Any] = {}
    for name in _SOLAR_UPAGRAHAS:
        try:
            sign_idx, deg = drik.solar_upagraha_longitudes(sun_longitude_sidereal, name)
            sign_idx = int(sign_idx)
            deg = float(deg)
            out[name] = {
                "sign": _names.sign_name(sign_idx),
                "sign_id": sign_idx + 1,
                "degree_in_sign": deg,
                "longitude_deg": sign_idx * 30.0 + deg,
            }
        except Exception as exc:  # noqa: BLE001
            out[name] = {"error": f"{name} failed: {exc!r}"}
    return out
