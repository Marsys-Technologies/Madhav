"""
service_probes.py — Health probe runners for service assets (asset_type='service').

A service asset's "build" = running its health probe. No rows written.
GREEN = all checks pass; degraded = partial; down = critical failure.

Each probe spec is stored in asset_registry.health_probe (JSONB) and references
a named probe type via the `probe_type` key. The dispatcher routes to the
appropriate implementation here.

Per UNIFIED_ASSET_REGISTRY_ARCHITECTURE_v1_0.md §D:
  GREEN when: (1) single canonical impl; (2) deterministic smoke; (3) FORENSIC-
  consistent where applicable; (4) endpoints reachable; (5) supported domain declared.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def run_health_probe(asset_id: str, probe_spec: dict | None) -> dict[str, Any]:
    """
    Dispatch to the named probe type for asset_id.
    Returns: {"status": "GREEN"|"degraded"|"down", "message": str, "checks": list}
    """
    if not probe_spec:
        return {"status": "down", "message": "no health_probe defined in asset_registry", "checks": []}

    probe_type = probe_spec.get("probe_type")
    if probe_type == "panchanga_engine":
        return _probe_panchanga_engine(probe_spec)
    elif probe_type == "ephemeris_engine":
        return _probe_ephemeris_engine(probe_spec)
    else:
        return {"status": "down", "message": f"unknown probe_type: {probe_type}", "checks": []}


# ── bg_panchanga probe ────────────────────────────────────────────────────────

_FORENSIC_BIRTH = {
    "instant": "1984-02-05T10:43:00",
    "lat": 20.27,
    "lon": 85.84,
    "tz_offset": 330,
    "expected": {
        "tithi": "Shukla Tritiya",
        "nakshatra": "Purva Bhadrapada",
        "yoga": "Shiva",
        "karana": "Garaja",
        "vara": "Ravivara",
    },
}


def _probe_panchanga_engine(probe_spec: dict) -> dict[str, Any]:
    checks: list[dict] = []
    failures: list[str] = []

    # Check 1: single canonical implementation importable
    try:
        from panchang_engine import panchanga_instant, panchanga_day  # noqa: F401
        checks.append({"check": "single_engine_importable", "passed": True})
    except ImportError as exc:
        checks.append({"check": "single_engine_importable", "passed": False, "error": str(exc)})
        failures.append(f"import failed: {exc}")

    # Check 2: deterministic FORENSIC smoke — panchanga_instant at birth
    try:
        from datetime import datetime
        from panchang_engine import panchanga_instant
        instant = datetime.fromisoformat(_FORENSIC_BIRTH["instant"])
        result = panchanga_instant(instant, _FORENSIC_BIRTH["lat"], _FORENSIC_BIRTH["lon"],
                                   _FORENSIC_BIRTH["tz_offset"])
        expected = _FORENSIC_BIRTH["expected"]
        mismatches = []
        for field, exp_val in expected.items():
            actual = getattr(result, field, None)
            actual_name = getattr(actual, "name", actual) if actual is not None else None
            if actual_name != exp_val:
                mismatches.append(f"{field}: got {actual_name!r}, expected {exp_val!r}")
        if mismatches:
            checks.append({"check": "forensic_birth_smoke", "passed": False, "mismatches": mismatches})
            failures.append(f"FORENSIC mismatch: {mismatches}")
        else:
            checks.append({"check": "forensic_birth_smoke", "passed": True})
    except Exception as exc:
        checks.append({"check": "forensic_birth_smoke", "passed": False, "error": str(exc)})
        failures.append(f"forensic smoke exception: {exc}")

    # Check 3: panchanga_day runs without error on birth date
    try:
        from datetime import date
        from panchang_engine import panchanga_day
        result = panchanga_day(date(1984, 2, 5), _FORENSIC_BIRTH["lat"],
                               _FORENSIC_BIRTH["lon"], _FORENSIC_BIRTH["tz_offset"])
        checks.append({"check": "panchanga_day_runs", "passed": result is not None})
    except Exception as exc:
        checks.append({"check": "panchanga_day_runs", "passed": False, "error": str(exc)})
        failures.append(f"panchanga_day exception: {exc}")

    status = "GREEN" if not failures else ("degraded" if len(failures) < len(checks) else "down")
    message = "All checks passed" if not failures else "; ".join(failures)
    return {"status": status, "message": message, "checks": checks}


# ── bg_ephemeris_engine probe ─────────────────────────────────────────────────

_FORENSIC_POSITION = {
    "jd": 2445701.948264,  # 1984-02-05 10:43 IST → UTC Julian Day
    "expected_sun_sign": 10,  # Makara (Capricorn) sidereal Lahiri
    "expected_mean_node_rahu_sign": 2,  # Vrishabha — Rahu mean node Feb 1984 (check: not Ketu)
}


def _probe_ephemeris_engine(probe_spec: dict) -> dict[str, Any]:
    checks: list[dict] = []
    failures: list[str] = []

    # Check 1: swisseph importable
    try:
        import swisseph as swe  # noqa: F401
        checks.append({"check": "swisseph_importable", "passed": True})
    except ImportError as exc:
        checks.append({"check": "swisseph_importable", "passed": False, "error": str(exc)})
        failures.append(f"swisseph import failed: {exc}")
        return {"status": "down", "message": str(exc), "checks": checks}

    # Check 2: DE441 path set, position query runs, AND Sun is in expected FORENSIC sign.
    # For 1984-02-05 tropical Sun must be in Capricorn (sign 10, tropical ~280–310°).
    # This is a real assertion, not just "no exception raised".
    # Tropical range for Capricorn: 270.0 <= lon < 300.0.  We allow a generous
    # ±15° window (255–315°) to absorb ayanamsha differences between callers, while
    # still catching a completely wrong body or Julian-day bug.
    _SUN_TROPICAL_LO = 255.0   # well south of Sagittarius start
    _SUN_TROPICAL_HI = 315.0   # well short of Aquarius start
    try:
        import swisseph as swe
        import os
        ephe_path = os.environ.get("SWISSEPH_PATH", "/app/ephe")
        swe.set_ephe_path(ephe_path)
        jd = _FORENSIC_POSITION["jd"]
        xx, _ = swe.calc_ut(jd, swe.SUN)
        sun_lon = xx[0]
        sun_in_range = _SUN_TROPICAL_LO <= sun_lon <= _SUN_TROPICAL_HI
        checks.append({
            "check": "de441_position_query",
            "passed": sun_in_range,
            "sun_lon": round(sun_lon, 4),
            "expected_range": f"{_SUN_TROPICAL_LO}–{_SUN_TROPICAL_HI}° (Capricorn tropical)",
        })
        if not sun_in_range:
            failures.append(
                f"Sun lon {sun_lon:.4f}° outside expected Capricorn range "
                f"[{_SUN_TROPICAL_LO}, {_SUN_TROPICAL_HI}] for 1984-02-05"
            )
    except Exception as exc:
        checks.append({"check": "de441_position_query", "passed": False, "error": str(exc)})
        failures.append(f"ephemeris position query failed: {exc}")

    # Check 3: MEAN_NODE-for-Rahu invariant.
    # Asserts Rahu is in Vrishabha (sign 2, ~30–60°) for Feb 1984 — a real FORENSIC
    # assertion, not the tautological "1 <= sign <= 12" which is always True for any
    # valid ephemeris output. Also verifies Ketu (true opposite) is in sign 8 (Vrischika).
    try:
        import swisseph as swe
        jd = _FORENSIC_POSITION["jd"]
        xx, _ = swe.calc_ut(jd, swe.MEAN_NODE)
        node_lon = xx[0]
        # Rahu mean node for Feb 1984 should be in Vrishabha (30° – 60°)
        rahu_sign = int(node_lon / 30) + 1
        expected_rahu_sign = _FORENSIC_POSITION["expected_mean_node_rahu_sign"]  # 2
        # Ketu is exactly opposite; swe.MEAN_NODE gives Rahu, Ketu = (Rahu + 180) % 360
        ketu_lon = (node_lon + 180.0) % 360.0
        ketu_sign = int(ketu_lon / 30) + 1
        expected_ketu_sign = ((expected_rahu_sign - 1 + 6) % 12) + 1  # 8 = Vrischika
        rahu_ok = rahu_sign == expected_rahu_sign
        ketu_ok = ketu_sign == expected_ketu_sign
        passed = rahu_ok and ketu_ok
        checks.append({
            "check": "mean_node_rahu_invariant",
            "passed": passed,
            "rahu_sign": rahu_sign,
            "rahu_lon": round(node_lon, 4),
            "ketu_sign": ketu_sign,
            "expected_rahu_sign": expected_rahu_sign,
            "expected_ketu_sign": expected_ketu_sign,
        })
        if not rahu_ok:
            failures.append(
                f"Rahu sign={rahu_sign} (lon={node_lon:.4f}°), "
                f"expected sign {expected_rahu_sign} (Vrishabha) for 1984-02-05"
            )
        if not ketu_ok:
            failures.append(
                f"Ketu sign={ketu_sign} (lon={ketu_lon:.4f}°), "
                f"expected sign {expected_ketu_sign} (Vrischika) for 1984-02-05"
            )
    except Exception as exc:
        checks.append({"check": "mean_node_rahu_invariant", "passed": False, "error": str(exc)})
        failures.append(f"MEAN_NODE check failed: {exc}")

    status = "GREEN" if not failures else ("degraded" if len(failures) < len(checks) else "down")
    message = "All checks passed" if not failures else "; ".join(failures)
    return {"status": status, "message": message, "checks": checks}
