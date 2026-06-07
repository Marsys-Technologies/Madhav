"""
strength.py — Shadbala (six-fold planetary strength).

Stub for now (returns an empty dict). The build pipeline's shadbala_writer
derives its own strength values; the engine does not need to surface Shadbala in
chart_output. PyJHora exposes jhora.horoscope.chart.strength for a future richer
implementation.
"""
from __future__ import annotations

from typing import Any


def compute_strength(
    jd_ut: float,
    ayanamsha_id: str = "lahiri",
    *,
    lat: float = 0.0,
    lon: float = 0.0,
    tz: float = 0.0,
) -> dict[str, Any]:
    return {}
