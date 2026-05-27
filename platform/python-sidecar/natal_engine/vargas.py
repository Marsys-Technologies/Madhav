"""
vargas.py — Divisional chart computation (D1 .. D60).

Scaffold scope: emit at least D1 (rashi) and D9 (navamsha) so the schema
shape is satisfied. Full Shodashavarga (16 vargas) is unit 1.2.

Each varga returns a dict: graha_name -> {"sign_id": int, "sign": str}.
The vargas top-level dict is: varga_code -> per-graha dict.
"""

from __future__ import annotations

from typing import Any

from .positions import SIGN_NAMES
from .schema import GrahaState


def _sign_of(lon: float) -> tuple[int, str]:
    sign_idx = int(lon // 30.0) % 12
    return sign_idx + 1, SIGN_NAMES[sign_idx]


def _d1_sign(graha: GrahaState) -> tuple[int, str]:
    return graha.sign_id, graha.sign


def _d9_sign(graha: GrahaState) -> tuple[int, str]:
    """Standard Parashari navamsha (D9).

    Each sign is split into 9 navamsha arcs of 3°20'. Starting sign of the
    navamsha cycle depends on the element of the natal sign:
      - movable (1,4,7,10): starts from itself
      - fixed (2,5,8,11):   starts from 9th sign
      - dual (3,6,9,12):    starts from 5th sign
    """
    lon = graha.longitude_deg
    sign_id = graha.sign_id  # 1..12
    deg_in_sign = lon - (sign_id - 1) * 30.0
    nav_idx = int(deg_in_sign // (30.0 / 9.0))  # 0..8

    quality = (sign_id - 1) % 3  # 0 movable, 1 fixed, 2 dual
    if quality == 0:
        start = sign_id
    elif quality == 1:
        start = ((sign_id - 1 + 8) % 12) + 1  # 9th from itself
    else:
        start = ((sign_id - 1 + 4) % 12) + 1  # 5th from itself

    final_sign_id = ((start - 1 + nav_idx) % 12) + 1
    return final_sign_id, SIGN_NAMES[final_sign_id - 1]


def compute_vargas(
    grahas: list[GrahaState], ascendant_lon: float | None = None
) -> dict[str, dict[str, dict[str, Any]]]:
    """Compute D1 + D9 placements. Other vargas land in unit 1.2.

    Returned dict structure satisfies CHART_OUTPUT_SCHEMA.vargas.
    """
    out: dict[str, dict[str, dict[str, Any]]] = {"D1": {}, "D9": {}}
    for g in grahas:
        s_id, s_name = _d1_sign(g)
        out["D1"][g.name] = {"sign_id": s_id, "sign": s_name}
        s_id, s_name = _d9_sign(g)
        out["D9"][g.name] = {"sign_id": s_id, "sign": s_name}
    return out
