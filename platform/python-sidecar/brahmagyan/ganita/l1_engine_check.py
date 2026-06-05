"""
brahmagyan.ganita.l1_engine_check — ganita.engine smoke test + verification
=============================================================================

Verifies that the pyswisseph-backed engine can produce the FORENSIC v8.0 superset
for the native's birth data (1984-02-05, 10:43 IST, Bhubaneswar 20.2961N 85.8245E).

Key structural anchors (NOT external oracle checks — internal chart fingerprints):
  - Sun in Capricorn (sign_id = 10) under Lahiri ayanamsha
  - Moon in Purva Bhadrapada (nakshatra_id = 25) under Lahiri ayanamsha
  - Rahu and Ketu exactly 180° apart
  - 9 grahas produced (Sun through Ketu)
  - Dasha tree reachable to Pratyantardasha (PD) depth
  - Lagna (Ascendant) computable for Bhubaneswar coordinates

Status reporting:
  GREEN  — engine live, all structural anchors pass
  AMBER  — engine computation succeeds but a non-critical check fails
  RED    — engine import or computation fails entirely

BRAHMA-GA-1-1 / ganita.engine
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

# ── Native birth constants ─────────────────────────────────────────────────────

NATIVE_BIRTH_IST = "1984-02-05T10:43:00"   # IST = UTC+5:30
NATIVE_LAT = 20.2961                         # Bhubaneswar, Odisha, India
NATIVE_LON = 85.8245
NATIVE_TZ_OFFSET = 5.5                       # hours ahead of UTC

# FORENSIC-grounded structural anchors (from FORENSIC_ASTROLOGICAL_DATA_v8_0.md)
EXPECTED_SUN_SIGN = "Capricorn"              # Lahiri: Sun in Makara
EXPECTED_SUN_SIGN_ID = 10
EXPECTED_MOON_NAKSHATRA = "Purva Bhadrapada" # Lahiri: Moon in PBP (nak_id=25)
EXPECTED_MOON_NAKSHATRA_ID = 25
EXPECTED_LAGNA_SIGN = "Aries"               # Lahiri: Mesha lagna (FORENSIC v6.0 MET.LAGNA.SIGN)
EXPECTED_LAGNA_SIGN_ID = 1

ENGINE_VERSION = "pyswisseph-DE441/brahma-l1-v1.0"
SOURCE_CITATION = "pyswisseph DE441 via Swiss Ephemeris (Moshier kernel); ayanamsha: Lahiri (Chitrapaksha)"

# ── Engine status ──────────────────────────────────────────────────────────────

def _birth_jd_utc() -> float:
    """Return Julian Day for the native's birth moment (UTC)."""
    import swisseph as swe
    dt_ist = datetime.fromisoformat(NATIVE_BIRTH_IST)
    dt_utc = dt_ist - timedelta(hours=5, minutes=30)
    return swe.julday(
        dt_utc.year, dt_utc.month, dt_utc.day,
        dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0,
    )


def run_engine_smoke() -> dict[str, Any]:
    """
    Run a full smoke test of the pyswisseph engine for the native's birth data.

    Returns a dict with:
      status: "GREEN" | "AMBER" | "RED"
      engine_version: str
      checks: list of {id, desc, passed, value}
      positions: list of graha position dicts (if engine succeeded)
      lagna: ascendant dict (if computable)
      dasha_tree: summary of Vimshottari dasha tree (if computable)
      error: error message if RED
    """
    checks: list[dict] = []
    positions: list[dict] = []
    lagna: dict = {}
    dasha_summary: dict = {}

    # ── Engine import check ────────────────────────────────────────────────────
    try:
        import swisseph as swe
        checks.append({"id": "E1", "desc": "pyswisseph importable", "passed": True, "value": "ok"})
    except ImportError as exc:
        checks.append({"id": "E1", "desc": "pyswisseph importable", "passed": False, "value": str(exc)})
        return {"status": "RED", "engine_version": ENGINE_VERSION, "checks": checks,
                "positions": [], "lagna": {}, "dasha_tree": {},
                "error": f"pyswisseph import failed: {exc}"}

    # ── Compute JD ────────────────────────────────────────────────────────────
    try:
        jd = _birth_jd_utc()
        checks.append({"id": "E2", "desc": "Julian Day computation succeeds", "passed": True,
                        "value": round(jd, 6)})
    except Exception as exc:
        checks.append({"id": "E2", "desc": "Julian Day computation succeeds", "passed": False,
                        "value": str(exc)})
        return {"status": "RED", "engine_version": ENGINE_VERSION, "checks": checks,
                "positions": [], "lagna": {}, "dasha_tree": {},
                "error": f"JD computation failed: {exc}"}

    # ── Position computation ───────────────────────────────────────────────────
    try:
        from brahmagyan.ganita.engine import compute_positions
        positions = compute_positions(jd, "lahiri")
        checks.append({"id": "E3", "desc": "compute_positions returns result", "passed": True,
                        "value": f"{len(positions)} grahas"})
    except Exception as exc:
        checks.append({"id": "E3", "desc": "compute_positions returns result", "passed": False,
                        "value": str(exc)})
        return {"status": "RED", "engine_version": ENGINE_VERSION, "checks": checks,
                "positions": [], "lagna": {}, "dasha_tree": {},
                "error": f"compute_positions failed: {exc}"}

    by_name = {p["name"]: p for p in positions}

    # ── Structural checks ──────────────────────────────────────────────────────
    # E4: 9 grahas present
    checks.append({
        "id": "E4", "desc": "9 grahas present (Sun→Ketu)",
        "passed": len(positions) == 9,
        "value": [p["name"] for p in positions],
    })

    # E5: All sidereal longitudes in [0, 360)
    lon_ok = all(0.0 <= p["sidereal_longitude"] < 360.0 for p in positions)
    checks.append({
        "id": "E5", "desc": "All sidereal longitudes in [0, 360)",
        "passed": lon_ok,
        "value": "ok" if lon_ok else [p for p in positions if not (0.0 <= p["sidereal_longitude"] < 360.0)],
    })

    # E6: Rahu + Ketu = 180° apart
    if "Rahu" in by_name and "Ketu" in by_name:
        sep = abs(by_name["Rahu"]["sidereal_longitude"] - by_name["Ketu"]["sidereal_longitude"]) % 360.0
        sep = min(sep, 360.0 - sep)
        rk_ok = abs(sep - 180.0) < 0.5
    else:
        sep = 0.0
        rk_ok = False
    checks.append({
        "id": "E6", "desc": "Rahu-Ketu separation = 180° (±0.5°)",
        "passed": rk_ok,
        "value": round(sep, 4),
    })

    # E7: Sun in Capricorn (FORENSIC structural anchor, Lahiri)
    sun = by_name.get("Sun", {})
    sun_ok = sun.get("sign_id") == EXPECTED_SUN_SIGN_ID
    checks.append({
        "id": "E7", "desc": f"Sun in {EXPECTED_SUN_SIGN} (Lahiri — FORENSIC anchor)",
        "passed": sun_ok,
        "value": f"sign={sun.get('sign')} id={sun.get('sign_id')}",
    })

    # E8: Moon in Purva Bhadrapada (FORENSIC structural anchor, Lahiri)
    moon = by_name.get("Moon", {})
    moon_ok = moon.get("nakshatra_id") == EXPECTED_MOON_NAKSHATRA_ID
    checks.append({
        "id": "E8", "desc": f"Moon in {EXPECTED_MOON_NAKSHATRA} (Lahiri — FORENSIC anchor)",
        "passed": moon_ok,
        "value": f"nakshatra={moon.get('nakshatra')} id={moon.get('nakshatra_id')}",
    })

    # ── Ascendant (Lagna) computation ──────────────────────────────────────────
    try:
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
        aya_val = swe.get_ayanamsa_ut(jd)
        # compute_houses returns (cusps_tuple, ascmc_tuple)
        cusps, ascmc = swe.houses(jd, NATIVE_LAT, NATIVE_LON, b"P")
        asc_trop = ascmc[0]
        asc_sid = (asc_trop - aya_val) % 360.0
        asc_sign_idx = int(asc_sid / 30)
        from brahmagyan.ganita.engine import SIGN_NAMES, NAKSHATRA_NAMES
        asc_sign = SIGN_NAMES[asc_sign_idx]
        lagna = {
            "longitude_tropical": round(asc_trop, 6),
            "longitude_sidereal": round(asc_sid, 6),
            "sign_id": asc_sign_idx + 1,
            "sign": asc_sign,
        }
        lagna_ok = lagna["sign_id"] == EXPECTED_LAGNA_SIGN_ID
        checks.append({
            "id": "E9", "desc": f"Lagna (Ascendant) in {EXPECTED_LAGNA_SIGN} (Lahiri — FORENSIC v6.0 MET.LAGNA.SIGN anchor)",
            "passed": lagna_ok,
            "value": f"sign={asc_sign} id={asc_sign_idx+1} lon={round(asc_sid, 4)}",
        })
    except Exception as exc:
        checks.append({"id": "E9", "desc": "Ascendant computation", "passed": False, "value": str(exc)})
        lagna = {}

    # ── Dasha tree check ───────────────────────────────────────────────────────
    try:
        from brahmagyan.ganita.engine import compute_vimshottari, NAKSHATRA_NAMES
        moon_sid = moon.get("sidereal_longitude", 0.0)
        dasha_tree = compute_vimshottari(moon_sid, jd)
        has_pds = any(
            any(len(ad.get("pratyantardashas", [])) > 0 for ad in md["antardashas"])
            for md in dasha_tree.get("mahadashas", [])
        )
        dasha_summary = {
            "moon_nakshatra": dasha_tree.get("moon_nakshatra"),
            "moon_nakshatra_lord": dasha_tree.get("moon_nakshatra_lord"),
            "balance_years": round(dasha_tree.get("balance_years", 0), 4),
            "md_count": len(dasha_tree.get("mahadashas", [])),
            "has_pd_depth": has_pds,
        }
        checks.append({
            "id": "E10", "desc": "Vimshottari dasha tree reachable to PD depth",
            "passed": has_pds,
            "value": dasha_summary,
        })
    except Exception as exc:
        checks.append({"id": "E10", "desc": "Vimshottari dasha tree", "passed": False, "value": str(exc)})

    # ── Final status ───────────────────────────────────────────────────────────
    all_passed = all(c["passed"] for c in checks)
    critical_ids = {"E1", "E2", "E3", "E4", "E5", "E7", "E8"}
    critical_ok = all(c["passed"] for c in checks if c["id"] in critical_ids)

    if all_passed:
        status = "GREEN"
    elif critical_ok:
        status = "AMBER"
    else:
        status = "RED"

    logger.info("[l1_engine_check] status=%s checks=%d/%d",
                status, sum(1 for c in checks if c["passed"]), len(checks))

    return {
        "status": status,
        "engine_version": ENGINE_VERSION,
        "source_citation": SOURCE_CITATION,
        "native": {
            "birth_ist": NATIVE_BIRTH_IST,
            "lat": NATIVE_LAT,
            "lon": NATIVE_LON,
        },
        "checks": checks,
        "positions": positions,
        "lagna": lagna,
        "dasha_tree": dasha_summary,
        "provenance_envelope": {
            "source": "pyswisseph DE441",
            "ayanamsha": "lahiri",
            "citation": SOURCE_CITATION,
            "layer": "L1-ganita",
            "asset": "ganita.engine",
        },
    }


def check_volume() -> dict[str, Any]:
    """
    Volume check for ganita.engine.
    The engine is a computation engine (no DB rows), so volume is measured
    by the number of grahas it can produce per ayanamsha.

    Floor: 9 grahas × 5 ayanamshas = 45 position objects per chart.
    """
    VOLUME_FLOOR = 9  # minimum grahas per ayanamsha
    try:
        result = run_engine_smoke()
        actual = len(result.get("positions", []))
        vol_status = "GREEN" if actual >= VOLUME_FLOOR else "AMBER"
        return {
            "volume_floor": VOLUME_FLOOR,
            "actual": actual,
            "status": vol_status,
            "engine_status": result["status"],
            "source_citation": SOURCE_CITATION,
        }
    except Exception as exc:
        return {
            "volume_floor": VOLUME_FLOOR,
            "actual": 0,
            "status": "RED",
            "engine_status": "RED",
            "error": str(exc),
            "source_citation": SOURCE_CITATION,
        }
