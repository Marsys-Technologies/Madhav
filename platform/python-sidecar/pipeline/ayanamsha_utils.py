"""
ayanamsha_utils.py — Multi-ayanamsha computation utilities
BUILD-ORCH-A-01 | G20 multi-ayanamsha support

Provides ayanamsha_value(jd, ayanamsha_id) using swisseph.
Supported ayanamsha_ids: lahiri, true_chitra, kp, raman, surya_siddhanta
"""

from __future__ import annotations

import swisseph as swe

# Map from canonical ayanamsha_id to swisseph SIDM constant
_AYANAMSHA_MAP: dict[str, int] = {
    "lahiri": swe.SIDM_LAHIRI,
    "true_chitra": swe.SIDM_TRUE_CITRA,
    "kp": swe.SIDM_KRISHNAMURTI,
    "raman": swe.SIDM_RAMAN,
    "surya_siddhanta": swe.SIDM_SURYASIDDHANTA,
}

SUPPORTED_AYANAMSHAS = list(_AYANAMSHA_MAP.keys())


def ayanamsha_value(jd: float, ayanamsha_id: str) -> float:
    """
    Compute the ayanamsha value (in degrees) at a given Julian Day using swisseph.

    Args:
        jd: Julian Day Number (e.g. 2445337.0 for 1984-02-05)
        ayanamsha_id: One of 'lahiri', 'true_chitra', 'kp', 'raman', 'surya_siddhanta'

    Returns:
        Ayanamsha value in decimal degrees (typically 20–30 for modern dates)

    Raises:
        ValueError: If ayanamsha_id is not recognised
    """
    if ayanamsha_id not in _AYANAMSHA_MAP:
        raise ValueError(
            f"Unknown ayanamsha_id '{ayanamsha_id}'. "
            f"Supported values: {SUPPORTED_AYANAMSHAS}"
        )

    sidm_flag = _AYANAMSHA_MAP[ayanamsha_id]
    swe.set_sid_mode(sidm_flag)
    value = swe.get_ayanamsa(jd)
    return float(value)


def all_ayanamsha_values(jd: float) -> dict[str, float]:
    """
    Compute ayanamsha values for all 5 canonical ayanamshas at a given Julian Day.

    Args:
        jd: Julian Day Number

    Returns:
        Dict mapping ayanamsha_id -> value in degrees
    """
    return {aid: ayanamsha_value(jd, aid) for aid in SUPPORTED_AYANAMSHAS}
