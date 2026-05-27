"""
houses.py — Whole-sign house computation (Vedic standard).

Whole-sign: house 1 = ascendant's sign; houses 2..12 = subsequent signs.
Each cusp_deg is set at 0° of the corresponding sign (mid-cusp convention is
explicitly NOT used at the scaffold; switch can come in unit 1.2 if JH parity
demands it).
"""

from __future__ import annotations

from .positions import SIGN_NAMES
from .schema import Ascendant, House


def compute_houses_whole_sign(ascendant: Ascendant) -> list[House]:
    asc_sign_idx = ascendant.sign_id - 1  # 0-based
    houses: list[House] = []
    for i in range(12):
        sign_idx = (asc_sign_idx + i) % 12
        houses.append(
            House(
                house_num=i + 1,
                cusp_deg=float(sign_idx * 30),
                sign=SIGN_NAMES[sign_idx],
                sign_id=sign_idx + 1,
            )
        )
    return houses
