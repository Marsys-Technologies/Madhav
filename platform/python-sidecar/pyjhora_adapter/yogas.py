"""
yogas.py — classical yoga detection.

Stub for now (returns an empty registry). PyJHora exposes a large yoga catalogue
(jhora.horoscope.chart.yoga) which can back a richer implementation later; the
build pipeline does not currently consume engine-side yoga output (the
yoga_register_writer derives its own), so an empty dict is a safe contract.
"""
from __future__ import annotations

from typing import Any


def compute_yogas(
    jd_ut: float,
    ayanamsha_id: str = "lahiri",
    *,
    lat: float = 0.0,
    lon: float = 0.0,
    tz: float = 0.0,
) -> dict[str, Any]:
    return {}
