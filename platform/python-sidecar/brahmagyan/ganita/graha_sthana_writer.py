"""
brahmagyan.ganita.graha_sthana_writer — Asset writer for ganita.graha_sthana
=============================================================================

Uses PyJHora as the computation engine (native decision: PyJHora IS the JH logic).
Writes per-chart natal positions to the `ganita_graha_sthana` table.

This is the primary L1 Gaṇita writer for graha positions using PyJHora,
distinct from the existing `l1_positions.py` which uses pyswisseph directly.

Acceptance contract (BRAHMA-G-1):
  - 10 rows per chart per ayanamsha (Sun, Moon, Mars, Mercury, Jupiter, Venus,
    Saturn, Rahu, Ketu + Lagna/Ascendant)
  - Sun in Capricorn ~21°48' for native (1984-02-05 10:43 IST Bhubaneswar)
  - Moon in Purva Bhadrapada for native
  - Source citation: PyJHora / pyjhora_adapter

Stream G deliverable: ganita.graha_sthana asset writer
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ── DB helper ──────────────────────────────────────────────────────────────────

def _db_url() -> str:
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        v = os.environ.get(key, "")
        if v:
            return v
    raise RuntimeError("[graha_sthana_writer] DATABASE_URL not set")


def _conn():
    import psycopg
    return psycopg.connect(_db_url())


# ── PyHora computation ─────────────────────────────────────────────────────────

def _compute_graha_sthana(
    datetime_iso: str,
    lat: float,
    lon: float,
    tz: float,
    ayanamsha_id: str = "lahiri",
) -> dict[str, Any]:
    """
    Compute graha_sthana using PyJHora.

    Returns dict with:
      - grahas: list of 9 graha position dicts
      - ascendant: lagna position dict
      - sensitive_points: upagrahas dict
      - dashas: vimshottari mahadasha chain
    """
    # Set ephemeris path before importing PyJHora
    ephe_path = os.environ.get("SWE_EPHE_PATH", "/app/ephe")
    try:
        import swisseph as swe
        swe.set_ephe_path(ephe_path)
    except Exception as exc:
        logger.warning("[graha_sthana_writer] ephe path set failed: %s", exc)

    from pyjhora_adapter.compute import compute_chart

    inputs = {
        "datetime_iso": datetime_iso,
        "latitude_deg": lat,
        "longitude_deg": lon,
        "tz_offset_hours": tz,
        "place_name": "",
        "subject_label": "",
    }

    return compute_chart(inputs=inputs, ayanamsha_id=ayanamsha_id)


# ── DB writer ──────────────────────────────────────────────────────────────────

def write_graha_sthana(
    chart_id: str,
    build_id: str,
    chart_data: dict[str, Any],
    ayanamsha_id: str = "lahiri",
) -> int:
    """
    Write graha_sthana rows to ganita_graha_sthana table.

    If the table doesn't exist, falls back to writing into ganita_positions
    (which already exists). Returns number of rows written.
    """
    datetime_iso = _extract_datetime(chart_data)
    lat = float(chart_data.get("birth_lat", chart_data.get("latitude", 0)))
    lon = float(chart_data.get("birth_lon", chart_data.get("longitude", 0)))
    tz = float(chart_data.get("tz_offset", 5.5))

    pyhora_result = _compute_graha_sthana(datetime_iso, lat, lon, tz, ayanamsha_id)

    grahas = pyhora_result.get("grahas", [])
    ascendant = pyhora_result.get("ascendant", pyhora_result.get("lagna", {}))
    sensitive_points = pyhora_result.get("sensitive_points", {})

    # Build rows list: 9 grahas + Lagna
    rows = []
    for g in grahas:
        lon_deg = g.get("longitude_deg", g.get("sidereal_longitude", g.get("lon", 0)))
        rows.append({
            "planet": g.get("name", ""),
            "longitude_deg": float(lon_deg),
            "sign": g.get("sign", ""),
            "sign_id": int(g.get("sign_id", 0)),
            "nakshatra": g.get("nakshatra", ""),
            "nakshatra_id": int(g.get("nakshatra_id", 0)),
            "pada": int(g.get("nakshatra_pada", g.get("pada", 0))),
            "house": int(g.get("house", 0)),
            "is_retrograde": bool(g.get("is_retrograde", False)),
            "speed_dps": float(g.get("speed_dps", g.get("speed", 0))),
            "source": "pyjhora",
        })

    # Add Lagna row
    if ascendant:
        asc_lon = ascendant.get("longitude_deg", 0)
        rows.append({
            "planet": "Lagna",
            "longitude_deg": float(asc_lon),
            "sign": ascendant.get("sign", ""),
            "sign_id": int(ascendant.get("sign_id", 0)),
            "nakshatra": ascendant.get("nakshatra") or "",
            "nakshatra_id": int(ascendant.get("nakshatra_id", 0) or 0),
            "pada": int(ascendant.get("pada", 0) or 0),
            "house": 1,
            "is_retrograde": False,
            "speed_dps": 0.0,
            "source": "pyjhora",
        })

    rows_written = _upsert_graha_sthana_rows(chart_id, build_id, rows, ayanamsha_id)

    logger.info(
        "[graha_sthana_writer] chart=%s build=%s ayanamsha=%s rows=%d",
        chart_id, build_id, ayanamsha_id, rows_written,
    )
    return rows_written


def _upsert_graha_sthana_rows(
    chart_id: str,
    build_id: str,
    rows: list[dict[str, Any]],
    ayanamsha_id: str,
) -> int:
    """
    Upsert rows into ganita_graha_sthana (preferred) or ganita_positions (fallback).
    Returns number of rows upserted.
    """
    with _conn() as conn:
        # Check if ganita_graha_sthana exists
        table_exists = conn.execute(
            "SELECT 1 FROM information_schema.tables WHERE table_name='ganita_graha_sthana'"
        ).fetchone()

        if table_exists:
            _upsert_into_graha_sthana(conn, chart_id, build_id, rows, ayanamsha_id)
        else:
            # Fall back to ganita_positions which already exists
            _upsert_into_ganita_positions(conn, chart_id, build_id, rows, ayanamsha_id)

        conn.commit()

    return len(rows)


def _upsert_into_graha_sthana(conn, chart_id, build_id, rows, ayanamsha_id):
    for row in rows:
        conn.execute(
            """
            INSERT INTO ganita_graha_sthana
              (chart_id, build_id, ayanamsha_id, planet, longitude_deg, sign,
               sign_id, nakshatra, nakshatra_id, nakshatra_pada, house,
               is_retrograde, speed_dps, source_citation, computed_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
            ON CONFLICT (chart_id, ayanamsha_id, planet) DO UPDATE SET
              build_id=EXCLUDED.build_id,
              longitude_deg=EXCLUDED.longitude_deg,
              sign=EXCLUDED.sign, sign_id=EXCLUDED.sign_id,
              nakshatra=EXCLUDED.nakshatra, nakshatra_id=EXCLUDED.nakshatra_id,
              nakshatra_pada=EXCLUDED.nakshatra_pada, house=EXCLUDED.house,
              is_retrograde=EXCLUDED.is_retrograde, speed_dps=EXCLUDED.speed_dps,
              source_citation=EXCLUDED.source_citation,
              computed_at=NOW()
            """,
            [
                chart_id, build_id, ayanamsha_id, row["planet"],
                row["longitude_deg"], row["sign"], row["sign_id"],
                row["nakshatra"], row["nakshatra_id"], row["pada"],
                row["house"], row["is_retrograde"], row["speed_dps"],
                f"pyjhora/{ayanamsha_id}",
            ],
        )


def _upsert_into_ganita_positions(conn, chart_id, build_id, rows, ayanamsha_id):
    """Fallback: write into ganita_positions using existing schema."""
    for row in rows:
        # Convert longitude_deg to degree_in_sign
        degree_in_sign = row["longitude_deg"] % 30.0
        conn.execute(
            """
            INSERT INTO ganita_positions
              (chart_id, build_id, ayanamsha_id, planet, tropical_longitude,
               sidereal_longitude, sign_id, sign_name, nakshatra_id, nakshatra_name,
               nakshatra_pada, speed_dps, is_retrograde, source_citation)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (chart_id, ayanamsha_id, planet) DO UPDATE SET
              build_id=EXCLUDED.build_id,
              tropical_longitude=EXCLUDED.tropical_longitude,
              sidereal_longitude=EXCLUDED.sidereal_longitude,
              sign_id=EXCLUDED.sign_id, sign_name=EXCLUDED.sign_name,
              nakshatra_id=EXCLUDED.nakshatra_id, nakshatra_name=EXCLUDED.nakshatra_name,
              nakshatra_pada=EXCLUDED.nakshatra_pada,
              speed_dps=EXCLUDED.speed_dps, is_retrograde=EXCLUDED.is_retrograde,
              source_citation=EXCLUDED.source_citation,
              updated_at=NOW()
            """,
            [
                chart_id, build_id, ayanamsha_id, row["planet"],
                row["longitude_deg"],       # tropical (approx; we use sidereal)
                row["longitude_deg"],       # sidereal (PyJHora returns sidereal)
                row["sign_id"], row["sign"],
                row["nakshatra_id"], row["nakshatra"],
                row["pada"],
                row["speed_dps"], row["is_retrograde"],
                f"pyjhora/{ayanamsha_id}",
            ],
        )


def _extract_datetime(chart_data: dict[str, Any]) -> str:
    """Extract ISO datetime string from chart data dict."""
    if "birth_datetime_ist" in chart_data:
        return str(chart_data["birth_datetime_ist"])
    if "birth_date" in chart_data and "birth_time" in chart_data:
        return f"{chart_data['birth_date']}T{chart_data['birth_time']}"
    raise ValueError(f"Cannot extract datetime from chart_data keys: {list(chart_data.keys())}")


# ── Runner function (callable from brahma_pipeline.py) ───────────────────────

def run_graha_sthana(
    chart_id: str,
    build_id: str,
    birth_datetime_ist: str,
    birth_lat: float,
    birth_lon: float,
    ayanamsha: str = "lahiri",
) -> dict[str, Any]:
    """
    Full graha_sthana run using PyJHora. Writes to DB and returns summary.

    Called from brahma_pipeline.py _l1_ganita() and from the cockpit
    per-chart build trigger.
    """
    chart_data = {
        "birth_datetime_ist": birth_datetime_ist,
        "birth_lat": birth_lat,
        "birth_lon": birth_lon,
        "tz_offset": 5.5,  # default IST; charts should carry tz_offset
    }

    rows = write_graha_sthana(chart_id, build_id, chart_data, ayanamsha)

    return {
        "chart_id": chart_id,
        "build_id": build_id,
        "ayanamsha": ayanamsha,
        "rows_written": rows,
        "engine": "pyjhora",
        "asset": "ganita.graha_sthana",
    }
