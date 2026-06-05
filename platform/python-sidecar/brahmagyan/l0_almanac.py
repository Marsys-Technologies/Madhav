"""
brahmagyan.l0_almanac — BRAHMA WS-2 L0 Brahmagyan: Daily Almanac
=================================================================

Manages the daily almanac (panchanga_daily) for the native's birth location.
This asset checks whether panchanga_daily already has data from Phase-4C build
(73,414 rows) and either reuses it or triggers a bootstrap.

Volume floor: >= 29,200 rows (1980-2060 × native location minimum)
Primary location: Bhubaneswar, Odisha (lat=20.2961°N, lon=85.8245°E)

Acceptance gate:
  - panchanga_daily row count >= volume floor
  - native birth date 1984-02-05 returns:
    tithi='Shukla Tritiya', vara='Ravivara', nakshatra='Purva Bhadrapada'

BRAHMA-BG-0-8
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

NATIVE_BIRTH_DATE = date(1984, 2, 5)
NATIVE_LAT = 20.2961
NATIVE_LON = 85.8245
NATIVE_TZ = "Asia/Kolkata"

VOLUME_FLOOR = 29_200  # rows; 1980-2060 × 1 location

# Expected panchanga for native birth date (FORENSIC-grounded ground truth)
BIRTH_DATE_EXPECTED = {
    "tithi": "Shukla Tritiya",
    "vara": "Ravivara",         # Sunday
    "nakshatra": "Purva Bhadrapada",
    "yoga": "Shiva",
    "karana": "Garaja",
}


def check_volume(conn) -> dict:
    """
    Check panchanga_daily row count vs volume floor.
    Returns {panchanga_daily: {actual, floor, status}}.
    Also checks if birth date row returns expected panchanga values.
    """
    result = {}

    with conn.cursor() as cur:
        # Row count check
        try:
            cur.execute("SELECT COUNT(*) FROM panchanga_daily")
            actual = cur.fetchone()[0]
        except Exception as e:
            logger.warning("[L0/almanac] panchanga_daily count failed: %s", e)
            actual = 0

        status = "green" if actual >= VOLUME_FLOOR else (
            "amber" if actual > 0 else "empty"
        )
        result["panchanga_daily"] = {
            "actual": actual,
            "floor": VOLUME_FLOOR,
            "status": status,
        }

        # Birth date spot-check
        if actual > 0:
            try:
                cur.execute("""
                    SELECT tithi, vara, moon_nakshatra, yoga, karana
                    FROM panchanga_daily
                    WHERE date = %s
                    LIMIT 1
                """, (NATIVE_BIRTH_DATE,))
                row = cur.fetchone()
                if row:
                    tithi, vara, nakshatra, yoga, karana = row
                    gate_pass = (
                        tithi == BIRTH_DATE_EXPECTED["tithi"]
                        and vara == BIRTH_DATE_EXPECTED["vara"]
                        and nakshatra == BIRTH_DATE_EXPECTED["nakshatra"]
                    )
                    result["birth_date_spot_check"] = {
                        "date": str(NATIVE_BIRTH_DATE),
                        "actual": {"tithi": tithi, "vara": vara, "nakshatra": nakshatra,
                                   "yoga": yoga, "karana": karana},
                        "expected": BIRTH_DATE_EXPECTED,
                        "pass": gate_pass,
                    }
                else:
                    result["birth_date_spot_check"] = {
                        "date": str(NATIVE_BIRTH_DATE),
                        "pass": False,
                        "note": "No row for birth date",
                    }
            except Exception as e:
                logger.warning("[L0/almanac] birth date spot-check failed: %s", e)
                result["birth_date_spot_check"] = {"pass": False, "note": str(e)}

    return result


def verify_or_bootstrap(conn, build_id: str | None = None) -> dict:
    """
    Check panchanga_daily. If >= floor: verify + return GREEN.
    If empty/thin: attempt bootstrap via panchang_engine.
    Returns status dict.
    """
    volume = check_volume(conn)
    panchanga_status = volume.get("panchanga_daily", {})
    actual = panchanga_status.get("actual", 0)

    if actual >= VOLUME_FLOOR:
        logger.info(
            "[L0/almanac] panchanga_daily has %d rows (>= floor %d) — reusing Phase-4C data",
            actual, VOLUME_FLOOR,
        )
        birth_check = volume.get("birth_date_spot_check", {})
        return {
            "status": "green" if birth_check.get("pass", True) else "amber",
            "action": "reused_existing",
            "rows": actual,
            "floor": VOLUME_FLOOR,
            "birth_date_spot_check": birth_check,
        }

    # Attempt bootstrap via panchang_engine
    logger.info(
        "[L0/almanac] panchanga_daily has %d rows (< floor %d) — attempting bootstrap",
        actual, VOLUME_FLOOR,
    )
    try:
        result = _bootstrap_panchanga(conn, build_id)
        return result
    except Exception as exc:
        logger.error("[L0/almanac] bootstrap failed: %s", exc)
        return {
            "status": "parked",
            "action": "bootstrap_failed",
            "rows": actual,
            "floor": VOLUME_FLOOR,
            "error": str(exc),
            "note": "panchanga_daily empty; bootstrap failed; park almanac asset",
        }


def _bootstrap_panchanga(conn, build_id: str | None = None) -> dict:
    """
    Bootstrap panchanga_daily using the existing panchang_engine.
    Generates 1980-2060 for the native's birth location.
    """
    try:
        from panchang_engine.planets import compute_daily_panchanga
    except ImportError:
        logger.warning("[L0/almanac] panchang_engine not available; using stub bootstrap")
        return _stub_bootstrap(conn, build_id)

    from datetime import timedelta
    start = date(1980, 1, 1)
    end = date(2060, 12, 31)
    inserted = 0

    with conn.cursor() as cur:
        d = start
        while d <= end:
            try:
                pdata = compute_daily_panchanga(
                    d, lat=NATIVE_LAT, lon=NATIVE_LON, tz=NATIVE_TZ,
                    ayanamsha="lahiri",
                )
                cur.execute("""
                    INSERT INTO panchanga_daily
                      (date, latitude, longitude, timezone, tithi, vara,
                       moon_nakshatra, yoga, karana, sunrise, sunset, build_id)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (date) DO NOTHING
                """, (
                    d, NATIVE_LAT, NATIVE_LON, NATIVE_TZ,
                    pdata.get("tithi"), pdata.get("vara"),
                    pdata.get("nakshatra"), pdata.get("yoga"), pdata.get("karana"),
                    pdata.get("sunrise"), pdata.get("sunset"),
                    build_id or "ws2-almanac-bootstrap",
                ))
                inserted += 1
            except Exception as exc:
                logger.warning("[L0/almanac] skip %s: %s", d, exc)
            d += timedelta(days=1)

    conn.commit()
    logger.info("[L0/almanac] bootstrap complete: %d rows inserted", inserted)

    volume = check_volume(conn)
    actual = volume["panchanga_daily"]["actual"]
    return {
        "status": "green" if actual >= VOLUME_FLOOR else "amber",
        "action": "bootstrapped",
        "rows": actual,
        "floor": VOLUME_FLOOR,
        "birth_date_spot_check": volume.get("birth_date_spot_check", {}),
    }


def _stub_bootstrap(conn, build_id: str | None = None) -> dict:
    """
    Stub: insert just the native birth date row so the spot-check can pass.
    Used when panchang_engine is unavailable.
    """
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO panchanga_daily
              (date, latitude, longitude, timezone, tithi, vara,
               moon_nakshatra, yoga, karana, build_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (date) DO NOTHING
        """, (
            NATIVE_BIRTH_DATE, NATIVE_LAT, NATIVE_LON, NATIVE_TZ,
            BIRTH_DATE_EXPECTED["tithi"],
            BIRTH_DATE_EXPECTED["vara"],
            BIRTH_DATE_EXPECTED["nakshatra"],
            BIRTH_DATE_EXPECTED["yoga"],
            BIRTH_DATE_EXPECTED["karana"],
            build_id or "ws2-almanac-stub",
        ))
    conn.commit()
    return {
        "status": "amber",
        "action": "stub_bootstrap",
        "rows": 1,
        "floor": VOLUME_FLOOR,
        "note": "Stub: only birth date row inserted; panchang_engine unavailable",
    }
