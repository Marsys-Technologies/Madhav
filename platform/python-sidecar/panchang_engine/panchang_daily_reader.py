"""
panchang_daily_reader.py — Read from panchanga_daily SQL cache for Muhurat scoring.

Phase: WRAPUP-S4 Packet C (F.1 Option A).

Provides:
  - is_bhubaneswar(lat, lon): haversine fence check (10 km radius)
  - fetch_panchanga_range(date_from, date_to, db_url): SQL-backed range reader

The module is a pure cache-read helper. Any exception (DB unreachable, missing
columns, schema drift) is swallowed and returns None so the caller falls back
to engine-direct compute_panchang(). This is intentional: cache miss ≠ error.

Performance goal: single SELECT replaces 90 × compute_panchang() calls for the
native (Bhubaneswar) use case. Per F1_MUHURAT_OVERLOAD_BRIEF_v1_0.md Option A.
"""
from __future__ import annotations

import json
import logging
import math
from datetime import date as DateType
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# DB driver — module-level import so tests can patch panchang_daily_reader.psycopg
# ---------------------------------------------------------------------------
# Use psycopg (v3) which is the sidecar standard; fall back to psycopg2.
# Both are imported at module level so that unittest.mock.patch can replace
# the module-level name during tests without a live DB.
try:
    import psycopg  # type: ignore[import]
except ImportError:
    try:
        import psycopg2 as psycopg  # type: ignore[import,no-redef]
    except ImportError:
        psycopg = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Native location constants
# ---------------------------------------------------------------------------

BHUBANESWAR_LAT: float = 20.2700
BHUBANESWAR_LON: float = 85.8400
LOCATION_FENCE_KM: float = 10.0

# ---------------------------------------------------------------------------
# Haversine location fence
# ---------------------------------------------------------------------------

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in kilometres between two lat/lon points."""
    R = 6371.0  # Earth radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def is_bhubaneswar(lat: float, lon: float) -> bool:
    """
    Return True if (lat, lon) is within LOCATION_FENCE_KM of Bhubaneswar.

    Args:
        lat: Latitude in decimal degrees (+N).
        lon: Longitude in decimal degrees (+E).

    Returns:
        True when distance from BHUBANESWAR_LAT/LON is <= LOCATION_FENCE_KM.
    """
    dist = _haversine_km(lat, lon, BHUBANESWAR_LAT, BHUBANESWAR_LON)
    return dist <= LOCATION_FENCE_KM


# ---------------------------------------------------------------------------
# JSONB deserialization helpers
# ---------------------------------------------------------------------------

def _ensure_dict(value) -> dict:
    """Return a dict, parsing from JSON string if necessary."""
    if isinstance(value, str):
        return json.loads(value)
    if isinstance(value, dict):
        return value
    return {}


def _ensure_list(value) -> list:
    """Return a list, parsing from JSON string if necessary."""
    if isinstance(value, str):
        return json.loads(value)
    if isinstance(value, list):
        return value
    return []


# ---------------------------------------------------------------------------
# DB range reader
# ---------------------------------------------------------------------------

_SQL = """
    SELECT
        date,
        tithi_id,
        nakshatra_id,
        vara_id,
        yoga_id,
        karana_id,
        sunrise_utc,
        sunset_utc,
        moon_phase,
        special_yogas,
        choghadiya,
        hora,
        inauspicious,
        auspicious
    FROM panchanga_daily
    WHERE date BETWEEN %s AND %s
    ORDER BY date
"""


def fetch_panchanga_range(
    date_from: DateType,
    date_to: DateType,
    db_url: str,
) -> Optional[list[dict]]:
    """
    Fetch panchanga_daily rows for [date_from, date_to] from the SQL cache.

    Returns:
        list[dict] with one entry per day if successful, or
        None if the DB is unavailable, the table is missing, or any other
        exception occurs — callers treat None as a cache miss and fall back
        to engine-direct compute.

    Each returned dict has the following keys and types:
        date: datetime.date
        tithi_id: int
        nakshatra_id: int
        vara_id: int
        yoga_id: int
        karana_id: int
        sunrise_utc: datetime.datetime (or ISO string — both handled by proxy)
        sunset_utc: datetime.datetime (or ISO string)
        moon_phase: float | None
        special_yogas: list[dict]   — e.g. [{"yoga": "Amrita", "strength": "auspicious", "stars": 4}]
        choghadiya: dict            — {"day": [...], "night": [...]}
        hora: list[dict]            — [{"label": "hora_sun", "start_utc": "...", "end_utc": "..."}]
        inauspicious: list[dict]    — [{"label": "rahu_kalam", ...}]
        auspicious: list[dict]      — [{"label": "abhijit", ...}]

    Note: psycopg3 (the sidecar standard) returns JSONB columns as Python dicts/lists
    automatically. psycopg2 returns them as strings; _ensure_list/_ensure_dict handle both.
    """
    if not db_url:
        return None

    if psycopg is None:
        logger.warning("panchanga_daily: no psycopg/psycopg2 available; skipping cache")
        return None

    try:
        rows: list[dict] = []

        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL, (date_from, date_to))
                col_names = [desc[0] for desc in cur.description]
                for raw_row in cur.fetchall():
                    row = dict(zip(col_names, raw_row))
                    # Deserialize JSONB columns defensively
                    row["special_yogas"] = _ensure_list(row.get("special_yogas"))
                    row["choghadiya"]    = _ensure_dict(row.get("choghadiya"))
                    row["hora"]          = _ensure_list(row.get("hora"))
                    row["inauspicious"]  = _ensure_list(row.get("inauspicious"))
                    row["auspicious"]    = _ensure_list(row.get("auspicious"))
                    rows.append(row)

        if not rows:
            # Cache is empty for this range — treat as miss so engine-direct runs
            logger.debug(
                "panchanga_daily: no rows for %s–%s; falling back to engine-direct",
                date_from, date_to,
            )
            return None

        logger.debug(
            "panchanga_daily: fetched %d rows for %s–%s",
            len(rows), date_from, date_to,
        )
        return rows

    except Exception as exc:  # noqa: BLE001
        # Cache miss — do not propagate; let the caller fall back
        logger.warning(
            "panchanga_daily fetch failed (%s: %s); will use engine-direct",
            type(exc).__name__, exc,
        )
        return None
