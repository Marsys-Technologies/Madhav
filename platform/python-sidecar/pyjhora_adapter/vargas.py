"""
vargas.py — divisional (varga) charts D1..D60.

Computes the standard Shodasavarga set (the 16 classical divisional charts).
Uses drik.dhasavarga(..., set_rahu_ketu_as_true_nodes=False) directly (mean
nodes) for the 9 grahas, plus the Lagna's varga via drik.dasavarga_from_long.
Each varga is a list of {name, sign, sign_id, degree_in_sign} rows (Lagna first).
"""
from __future__ import annotations

from typing import Any

from . import _names
from ._ayanamsha import resolve_mode
from ._jhora import drik

# Standard Shodasavarga factors (classical 16-fold).
VARGA_FACTORS = [1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]
_USE_TRUE_NODES = False


def _place(lat: float, lon: float, tz: float):
    return drik.Place("subject", lat, lon, tz)


def _planet_row(pid: Any, sign_idx: int, deg: float) -> dict[str, Any]:
    name = "Lagna" if pid == "L" else _names.PLANET_NAMES.get(int(pid), str(pid))
    return {
        "name": name,
        "sign": _names.sign_name(sign_idx),
        "sign_id": sign_idx + 1,  # 1-based per L2.5 contract
        "degree_in_sign": deg,
    }


def compute_vargas(
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

    # Lagna full sidereal longitude (D1) for varga derivation.
    asc = drik.ascendant(jd_ut, place)
    asc_full_long = int(asc[0]) * 30.0 + float(asc[1])

    out: dict[str, Any] = {}
    for f in VARGA_FACTORS:
        try:
            rows: list[dict[str, Any]] = []
            # Lagna varga
            l_sign, l_deg = drik.dasavarga_from_long(asc_full_long, f)
            rows.append(_planet_row("L", int(l_sign), float(l_deg)))
            # Planet vargas (mean nodes)
            pp = drik.dhasavarga(
                jd_ut, place, divisional_chart_factor=f,
                set_rahu_ketu_as_true_nodes=_USE_TRUE_NODES,
            )
            for row in pp:
                rows.append(_planet_row(int(row[0]), int(row[1][0]), float(row[1][1])))
            out[f"D{f}"] = rows
        except Exception as exc:  # noqa: BLE001
            out[f"D{f}"] = {"error": f"varga D{f} failed: {exc!r}"}
    return out
