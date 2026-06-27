"""
test_b1_forensic_gate.py — BLOCKING GATE for the B1 native-birth elimination PR.

Wave 0 gate: must PASS before Wave 1 agents may merge.

Asserts:
1. fetch_birth_params() returns the correct birth data for the native from public.charts.
2. panchanga_instant() with that DB-sourced data passes all 7 FORENSIC anchors.
3. resolve_birth_params() raises ValueError for ANY chart (native included) with falsy params.

FORENSIC anchors (7/7 required):
  Sun in Makara (Capricorn)
  Moon in Purva Bhadrapada nakshatra
  Lagna in Mesha (Aries)            — invariant across all 5 ayanamshas
  Tithi = Shukla Tritiya
  Vara  = Ravivara (Sunday)
  Yoga  = Shiva
  Karana = Garaja

These values are the FORENSIC 7/7 PASS confirmed by the L1 production build.
Any deviation halts the PR — do NOT delete the constant without a passing gate.
"""
from __future__ import annotations

import os
import sys
import pathlib
import pytest
from datetime import date, time, datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_NATIVE_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
_NON_NATIVE = "00000000-0000-0000-0000-000000000001"

# Expected values after B1 elimination (sourced from public.charts → _to_birth_params)
_EXPECTED_DATETIME_ISO = "1984-02-05T10:43:00"
# Bhubaneswar: accept any value in a generous 1-degree band around the canonical
# centre — the exact value in public.charts may be slightly more precise than the
# original NATIVE_BIRTH constant (20.27°N, 85.84°E) but both pass FORENSIC.
_EXPECTED_LAT_MIN = 19.5
_EXPECTED_LAT_MAX = 21.0
_EXPECTED_LNG_MIN = 85.0
_EXPECTED_LNG_MAX = 86.5
_EXPECTED_TZ_HOURS = 5.5

# FORENSIC 7/7 anchors
_FORENSIC = {
    "tithi_name":    "Shukla Tritiya",
    "vara_name":     "Ravivara",
    "yoga_name":     "Shiva",
    "karana_name":   "Garaja",
    "nakshatra_name": "Purva Bhadrapada",
    "lagna_sign":    "Mesha",
    "sun_sign":      "Makara",
}


# ---------------------------------------------------------------------------
# DB connection helper (uses DATABASE_URL from env or .env.local)
# ---------------------------------------------------------------------------

def _get_conn():
    """Return a live psycopg connection.  Skips if no DB URL available."""
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        # Try loading from .env.local (local dev convenience)
        env_file = pathlib.Path(__file__).resolve().parents[3] / "platform" / ".env.local"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line.startswith("DATABASE_URL=") and not line.startswith("#"):
                    db_url = line.split("=", 1)[1].strip()
                    break
    if not db_url:
        pytest.skip("DATABASE_URL not set — skipping live DB gate test")
    import psycopg
    return psycopg.connect(db_url)


# ---------------------------------------------------------------------------
# Gate Test 1: fetch_birth_params produces correct native birth data from DB
# ---------------------------------------------------------------------------

def test_fetch_birth_params_native_returns_correct_data():
    """Gate 1: fetch_birth_params(conn, native_chart_id) returns the FORENSIC-correct
    birth data from public.charts — not None, not hardcoded fallback.

    After B1 elimination, fetch_birth_params treats the native like any other chart.
    The DB row must have birth_date=1984-02-05, birth_time=10:43, birth_lat=20.27,
    birth_lng=85.84, timezone_id=Asia/Kolkata.
    """
    from pipeline.orchestrator.birth_params import fetch_birth_params

    conn = _get_conn()
    try:
        bp = fetch_birth_params(conn, _NATIVE_CHART_ID)
    finally:
        conn.close()

    assert bp is not None, "fetch_birth_params must return a dict for the native (not None)"
    assert isinstance(bp, dict), f"Expected dict, got {type(bp)}"
    assert bp["datetime_iso"] == _EXPECTED_DATETIME_ISO, (
        f"datetime_iso mismatch: got {bp['datetime_iso']!r}, "
        f"expected {_EXPECTED_DATETIME_ISO!r}"
    )
    lat = float(bp["latitude_deg"])
    lng = float(bp["longitude_deg"])
    assert _EXPECTED_LAT_MIN <= lat <= _EXPECTED_LAT_MAX, (
        f"latitude_deg {lat} is outside Bhubaneswar band [{_EXPECTED_LAT_MIN}, {_EXPECTED_LAT_MAX}]"
    )
    assert _EXPECTED_LNG_MIN <= lng <= _EXPECTED_LNG_MAX, (
        f"longitude_deg {lng} is outside Bhubaneswar band [{_EXPECTED_LNG_MIN}, {_EXPECTED_LNG_MAX}]"
    )
    assert bp["tz_offset_hours"] == _EXPECTED_TZ_HOURS, (
        f"tz_offset_hours mismatch: got {bp['tz_offset_hours']}, expected {_EXPECTED_TZ_HOURS}"
    )


# ---------------------------------------------------------------------------
# Gate Test 2: FORENSIC 7/7 pass with DB-sourced birth params
# ---------------------------------------------------------------------------

def test_forensic_7_7_with_db_sourced_birth_params():
    """Gate 2: panchanga_instant() with DB-sourced native birth params passes all 7
    FORENSIC anchors.  This is the hard gate — if it fails, the B1 elimination is
    broken and the PR must NOT merge.
    """
    from pipeline.orchestrator.birth_params import fetch_birth_params

    conn = _get_conn()
    try:
        bp = fetch_birth_params(conn, _NATIVE_CHART_ID)
    finally:
        conn.close()

    # Parse the DB-sourced birth params
    birth_dt = datetime.fromisoformat(bp["datetime_iso"])
    lat = float(bp["latitude_deg"])
    lng = float(bp["longitude_deg"])
    tz_min = int(round(bp["tz_offset_hours"] * 60))

    # Import panchanga engine
    try:
        from panchang_engine import panchanga_instant
    except ImportError:
        pytest.skip("panchang_engine not available in this environment")

    pi = panchanga_instant(birth_dt, lat, lng, tz_min)

    # --- Invariant angas (ayanamsha-independent) ---
    failures = []

    tithi = pi.tithi.name if hasattr(pi.tithi, "name") else str(pi.tithi)
    if tithi != _FORENSIC["tithi_name"]:
        failures.append(f"Tithi: got {tithi!r}, expected {_FORENSIC['tithi_name']!r}")

    vara = pi.vara.name if hasattr(pi.vara, "name") else str(pi.vara)
    if vara != _FORENSIC["vara_name"]:
        failures.append(f"Vara: got {vara!r}, expected {_FORENSIC['vara_name']!r}")

    yoga = pi.yoga.name if hasattr(pi.yoga, "name") else str(pi.yoga)
    if yoga != _FORENSIC["yoga_name"]:
        failures.append(f"Yoga: got {yoga!r}, expected {_FORENSIC['yoga_name']!r}")

    karana = pi.karana.name if hasattr(pi.karana, "name") else str(pi.karana)
    if karana != _FORENSIC["karana_name"]:
        failures.append(f"Karana: got {karana!r}, expected {_FORENSIC['karana_name']!r}")

    nakshatra = pi.nakshatra.name if hasattr(pi.nakshatra, "name") else str(pi.nakshatra)
    if nakshatra != _FORENSIC["nakshatra_name"]:
        failures.append(f"Nakshatra: got {nakshatra!r}, expected {_FORENSIC['nakshatra_name']!r}")

    # --- Lagna (Ascendant) ---
    if hasattr(pi, "lagna") and pi.lagna is not None:
        lagna_sign = (
            pi.lagna.ascendant_sign_name
            if hasattr(pi.lagna, "ascendant_sign_name")
            else str(pi.lagna)
        )
        if lagna_sign != _FORENSIC["lagna_sign"]:
            failures.append(f"Lagna: got {lagna_sign!r}, expected {_FORENSIC['lagna_sign']!r}")
    else:
        failures.append("Lagna: not computed (missing from PanchangaInstant)")

    # --- Sun sign ---
    sun = next((p for p in pi.planets if p.name == "Sun"), None)
    if sun is None:
        failures.append("Sun: not found in planets list")
    else:
        sun_sign = sun.sign_name if hasattr(sun, "sign_name") else str(sun)
        if sun_sign != _FORENSIC["sun_sign"]:
            failures.append(f"Sun sign: got {sun_sign!r}, expected {_FORENSIC['sun_sign']!r}")

    assert not failures, (
        "FORENSIC 7/7 GATE FAILED with DB-sourced native birth params.\n"
        "This means public.charts has wrong birth data for the native. "
        "Fix the DB row before merging the B1 elimination PR.\n"
        "Failures:\n" + "\n".join(f"  - {f}" for f in failures)
    )


# ---------------------------------------------------------------------------
# Gate Test 3: resolve_birth_params raises for ANY chart with falsy params
# ---------------------------------------------------------------------------

def test_resolve_birth_params_raises_for_native_with_none():
    """Gate 3a: B1 elimination — resolve_birth_params raises for the native chart
    with None birth_params (no NATIVE_BIRTH fallback)."""
    from pipeline.orchestrator.birth_params import resolve_birth_params

    with pytest.raises(ValueError):
        resolve_birth_params(_NATIVE_CHART_ID, None)


def test_resolve_birth_params_raises_for_native_with_empty_dict():
    """Gate 3b: resolve_birth_params raises for native + empty dict."""
    from pipeline.orchestrator.birth_params import resolve_birth_params

    with pytest.raises(ValueError):
        resolve_birth_params(_NATIVE_CHART_ID, {})


def test_resolve_birth_params_raises_for_non_native_with_none():
    """Gate 3c: resolve_birth_params raises for non-native + None."""
    from pipeline.orchestrator.birth_params import resolve_birth_params

    with pytest.raises(ValueError):
        resolve_birth_params(_NON_NATIVE, None)


def test_resolve_birth_params_returns_dict_when_truthy():
    """Gate 3d: resolve_birth_params returns dict unchanged when truthy (for both charts)."""
    from pipeline.orchestrator.birth_params import resolve_birth_params

    params = {
        "datetime_iso": "1984-02-05T10:43:00",
        "latitude_deg": 20.27,
        "longitude_deg": 85.84,
        "tz_offset_hours": 5.5,
    }
    # Both native and non-native: truthy params pass through
    assert resolve_birth_params(_NATIVE_CHART_ID, params) is params
    assert resolve_birth_params(_NON_NATIVE, params) is params
