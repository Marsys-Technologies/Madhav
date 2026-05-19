"""
special_yogas.py — Special yoga detection for panchang_engine.
STUB this session (4C-1-S1). Implemented in 4C-1-S2.
"""
from .exceptions import PanchangEngineError


def compute_active_yogas(panchang) -> list:
    """
    Detect special yogas active on the given Panchang day.
    STUB — raises NotImplementedError. Implemented in 4C-1-S2.

    In S2 this will detect:
    - Sarvartha Siddhi Yoga (vara × nakshatra table)
    - Amrit Siddhi Yoga (vara × nakshatra table — subset of Sarvartha)
    - Ravi Yoga (vara × nakshatra table)
    - Siddha Yoga (vara × tithi table)
    - Dwidala Yoga (nakshatra transitions within day)
    - Pushkara Navamsha / Bhaga flags

    Returns list of dict with keys: name, type, quality, description, end_utc
    """
    raise NotImplementedError(
        "special_yogas.compute_active_yogas is implemented in 4C-1-S2. "
        "This session (4C-1-S1) returns [] from compute_panchang for special_yogas."
    )
