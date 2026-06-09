"""
FORENSIC panchang tests — repointed to panchanga_instant (P2 re-arch, 2026-06-09).

Previously tested pyjhora_adapter.panchanga; that module is retired (single-engine rule).
The canonical panchang engine is panchang_engine.panchanga_instant (swisseph, Drik-parity).
These tests guard the same FORENSIC invariant: native birth angas must match exactly.
"""
from __future__ import annotations

from datetime import datetime

_ANGAS = ["tithi", "vara", "nakshatra", "yoga", "karana"]

# Native birth — Abhisek Mohanty, 1984-02-05 10:43 IST, Bhubaneswar
_BIRTH = {
    "instant": datetime(1984, 2, 5, 10, 43, 0),
    "lat": 20.2961,
    "lon": 85.8245,
    "tz_offset": 330,  # IST = +05:30 = +330 minutes
}


def test_panchanga_all_angas_nonempty():
    from panchang_engine import panchanga_instant
    result = panchanga_instant(
        _BIRTH["instant"], _BIRTH["lat"], _BIRTH["lon"], _BIRTH["tz_offset"]
    )
    assert result.tithi is not None and result.tithi.name.strip() != ""
    assert result.nakshatra is not None and result.nakshatra.name.strip() != ""
    assert result.yoga is not None and result.yoga.name.strip() != ""
    assert result.karana is not None and result.karana.name.strip() != ""
    assert result.vara is not None and result.vara.name.strip() != ""


def test_native_panchanga_values():
    """FORENSIC gate: native birth angas under Lahiri/swisseph must match exactly."""
    from panchang_engine import panchanga_instant
    result = panchanga_instant(
        _BIRTH["instant"], _BIRTH["lat"], _BIRTH["lon"], _BIRTH["tz_offset"]
    )
    assert result.tithi.name == "Shukla Tritiya",   f"tithi: {result.tithi.name!r}"
    assert result.vara.name == "Ravivara",           f"vara: {result.vara.name!r}"
    assert result.nakshatra.name == "Purva Bhadrapada", f"nakshatra: {result.nakshatra.name!r}"
    assert result.yoga.name == "Shiva",             f"yoga: {result.yoga.name!r}"
    assert result.karana.name == "Garaja",          f"karana: {result.karana.name!r}"
