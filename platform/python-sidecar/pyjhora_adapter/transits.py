"""
transits.py — current transit (gochara) positions.

Stub for now (returns an empty dict). Natal chart builds do not consume
transit positions; transit work is a separate pipeline. When needed this can
read positions.compute_positions(jd_now, ...) for the current instant.
"""
from __future__ import annotations

from typing import Any


def compute_transits(
    jd_ut: float,
    ayanamsha_id: str = "lahiri",
    *,
    lat: float = 0.0,
    lon: float = 0.0,
    tz: float = 0.0,
) -> dict[str, Any]:
    return {}
