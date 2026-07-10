"""
dignities.py — exaltation / debilitation / own-sign / combustion refinement.

Operates on the graha dicts produced by positions.compute_positions and adds:
  - dignity_status: 'exalted' | 'debilitated' | 'own_sign' | 'neutral'
  - combust: bool (planet within combustion orb of the Sun)

Exaltation/debilitation signs are classical fixed constants.
"""
from __future__ import annotations

from typing import Any

# Exaltation sign index (0=Aries..11=Pisces) per graha.
_EXALT_SIGN = {
    "Sun": 0,      # Aries
    "Moon": 1,     # Taurus
    "Mars": 9,     # Capricorn
    "Mercury": 5,  # Virgo
    "Jupiter": 3,  # Cancer
    "Venus": 11,   # Pisces
    "Saturn": 6,   # Libra
}
# Debilitation is 180 deg (6 signs) from exaltation.
_DEBIL_SIGN = {p: (s + 6) % 12 for p, s in _EXALT_SIGN.items()}

# Own signs per graha (sign indices ruled).
_OWN_SIGNS = {
    "Sun": {4},          # Leo
    "Moon": {3},         # Cancer
    "Mars": {0, 7},      # Aries, Scorpio
    "Mercury": {2, 5},   # Gemini, Virgo
    "Jupiter": {8, 11},  # Sagittarius, Pisces
    "Venus": {1, 6},     # Taurus, Libra
    "Saturn": {9, 10},   # Capricorn, Aquarius
}

# Combustion orb (degrees from Sun) per graha — classical values.
_COMBUST_ORB = {
    "Moon": 12.0, "Mars": 17.0, "Mercury": 14.0,
    "Jupiter": 11.0, "Venus": 10.0, "Saturn": 15.0,
}


def _dignity_for(name: str, sign_id: int) -> str:
    """
    D-3 fix: `sign_id` arrives 1-based (Aries=1..Pisces=12) — see
    positions.py:81 ("1-based (Aries=1..Pisces=12) per L2.5 contract") —
    but _EXALT_SIGN / _DEBIL_SIGN / _OWN_SIGNS above are all 0-based
    (Aries=0..Pisces=11). Comparing the raw 1-based sign_id against these
    0-based tables was silently off-by-one for every graha, and for two of
    them the collision was exact and classically backwards: Jupiter's real
    own-sign Sagittarius (1-based 9) numerically equals Jupiter's 0-based
    debilitation index (Capricorn=9), so Jupiter — genuinely in its OWN
    sign — was misclassified "debilitated" (then "debilitation_cancelled"
    after the neecha-bhanga check downstream); Saturn's real exaltation
    sign Libra (1-based 7) never equals Saturn's 0-based exaltation index
    (6), so deeply-exalted Saturn fell through every branch to "neutral".
    This is D-3's root cause (register evidence: Jupiter own-sign Sagittarius
    → wrongly "debilitation_cancelled"; Saturn Libra exaltation → wrongly
    "neutral"; 8/9 grahas "neutral", a near-degenerate distribution).
    Converting to 0-based here (once, at the boundary) fixes every
    downstream consumer of dignity_status without touching the locked
    1-based L2.5 sign_id contract itself.
    """
    sign_idx_0based = (sign_id - 1) % 12
    if name in _EXALT_SIGN and sign_idx_0based == _EXALT_SIGN[name]:
        return "exalted"
    if name in _DEBIL_SIGN and sign_idx_0based == _DEBIL_SIGN[name]:
        return "debilitated"
    if name in _OWN_SIGNS and sign_idx_0based in _OWN_SIGNS[name]:
        return "own_sign"
    return "neutral"


def _ang_sep(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def refine(grahas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sun_long = next(
        (g["longitude_deg"] for g in grahas if g["name"] == "Sun"), None
    )
    for g in grahas:
        g["dignity_status"] = _dignity_for(g["name"], int(g["sign_id"]))
        if sun_long is not None and g["name"] in _COMBUST_ORB:
            sep = _ang_sep(float(g["longitude_deg"]), float(sun_long))
            g["combust"] = sep <= _COMBUST_ORB[g["name"]]
        else:
            g.setdefault("combust", False)
    return grahas
