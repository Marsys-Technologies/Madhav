"""One Kāla ayanāṃśa policy and per-instant Swiss offset.

The id is the L1 persisted convention, not panchang_engine's legacy `lahiri`
alias. Selection and offset calculation share the process-wide Swiss lock.
"""
from __future__ import annotations

from math import isfinite

from brahmagyan.l0_ephemeris import AYANAMSHA_MAP, _SWE_AVAILABLE, derive_sidereal
from panchang_engine.swiss_state import serialized_swiss_state


CANONICAL_AYANAMSHA = "lahiri_chitrapaksha"


@serialized_swiss_state
def sidereal_offset(jd_ut: float, ayanamsha_id: str = CANONICAL_AYANAMSHA) -> float:
    """Ayanāṃśa degrees at this UT Julian day, using L1's Swiss mode map."""
    if not isfinite(jd_ut):
        raise ValueError("jd_ut must be finite")
    if ayanamsha_id not in AYANAMSHA_MAP:
        raise ValueError(f"unknown L1 ayanamsha id: {ayanamsha_id!r}")
    if not _SWE_AVAILABLE:
        raise RuntimeError("pyswisseph is required for sidereal offsets")
    # Reuse L1's serialized Swiss owner and its canonical mode map. A new
    # swisseph call here would create a second state-operation owner.
    return float(derive_sidereal(0.0, jd_ut, ayanamsha_id)["ayanamsha_offset"])


def sidereal_longitude(tropical_longitude: float, jd_ut: float,
                       ayanamsha_id: str = CANONICAL_AYANAMSHA) -> float:
    """Convert a tropical longitude at its own instant; no epoch-wide offset."""
    if not isfinite(tropical_longitude):
        raise ValueError("tropical_longitude must be finite")
    return (tropical_longitude - sidereal_offset(jd_ut, ayanamsha_id)) % 360.0


__all__ = ["CANONICAL_AYANAMSHA", "sidereal_offset", "sidereal_longitude"]
