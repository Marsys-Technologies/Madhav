"""
pipeline/writers/panchanga_writer.py
=====================================
Brahma GA-1-7: ganita.panchanga — birth-moment panchanga DB writer.

Reads the panchanga section of the ganita.engine JSONL output and writes
to the chart_panchanga table.  Idempotent: ON CONFLICT (chart_id, build_id)
DO UPDATE so repeated runs are safe.

Design:
  - Input: dict produced by natal_engine.compute_chart() (the 'panchanga' key)
            + the chart-level metadata (chart_id, build_id, graha positions for
            sun/moon longitudes).
  - Output: one row in chart_panchanga.
  - Sunrise: derived from panchanga_daily if available, else None (birth-moment
             computation does not require it for the 5 limbs).

Acceptance gate (FORENSIC spot-check for native 1984-02-05):
  tithi=Shukla Tritiya, vara=Ravivara, moon_nakshatra=Purva Bhadrapada,
  yoga=Shiva, karana=Garaja

Source: BRAHMA_L1_L5_REGISTRY_SEED_v1_0 §B ganita.panchanga (GA-1-7)
Author: Brahma swarm Śilpī, 2026-06-03
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

log = logging.getLogger(__name__)

# ── Canonical name tables ──────────────────────────────────────────────────────
# Source: panchang_engine/shastra_tables.py  (duplicate-free copy for portability)

TITHI_NAMES: dict[int, str] = {
    1: "Shukla Pratipada", 2: "Shukla Dvitiya", 3: "Shukla Tritiya",
    4: "Shukla Chaturthi", 5: "Shukla Panchami", 6: "Shukla Shashthi",
    7: "Shukla Saptami", 8: "Shukla Ashtami", 9: "Shukla Navami",
    10: "Shukla Dashami", 11: "Shukla Ekadashi", 12: "Shukla Dvadashi",
    13: "Shukla Trayodashi", 14: "Shukla Chaturdashi", 15: "Purnima",
    16: "Krishna Pratipada", 17: "Krishna Dvitiya", 18: "Krishna Tritiya",
    19: "Krishna Chaturthi", 20: "Krishna Panchami", 21: "Krishna Shashthi",
    22: "Krishna Saptami", 23: "Krishna Ashtami", 24: "Krishna Navami",
    25: "Krishna Dashami", 26: "Krishna Ekadashi", 27: "Krishna Dvadashi",
    28: "Krishna Trayodashi", 29: "Krishna Chaturdashi", 30: "Amavasya",
}

NAKSHATRA_NAMES: list[str] = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Moola", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

YOGA_NAMES: list[str] = [
    "Vishkamba", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda",
    "Sukarman", "Dhriti", "Shoola", "Ganda", "Vriddhi", "Dhruva", "Vyaghata",
    "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra", "Vaidhriti",
]

KARANA_NAMES: list[str] = [
    "Bava", "Balava", "Kaulava", "Taitila", "Garaja", "Vanija", "Vishti",
    "Shakuni", "Chatushpada", "Naga", "Kimstughna",
]

# Vara name mapping: PyJHora vara index → Sanskrit name
# PyJHora vara() returns 0=Sunday … 6=Saturday
VARA_NAMES: dict[int, str] = {
    0: "Ravivara",    # Sun
    1: "Somavara",    # Moon
    2: "Mangalavara", # Mars
    3: "Budhavara",   # Mercury
    4: "Guruvara",    # Jupiter
    5: "Shukravara",  # Venus
    6: "Shanivara",   # Saturn
}

SOURCE_CITATION = (
    "FORENSIC v8.0 §Panchanga; natal_engine GA-1-1 [BRAHMA]; "
    "MC §1-4 (Muhurta Chintamani); BS §2 (Brihat Samhita); "
    "PyJHora/pyswisseph DE441"
)
ENGINE_VERSION = "ganita.engine/1.0.0"


# ── Row builder ────────────────────────────────────────────────────────────────

def build_row(
    chart_id: str,
    build_id: str,
    panchanga: dict[str, Any],
    *,
    lahiri_grahas: dict[str, Any] | None = None,
    sunrise_utc: datetime | None = None,
    sunrise_ist: str | None = None,
) -> dict[str, Any]:
    """
    Build a chart_panchanga row dict from ganita.engine output.

    Args:
        chart_id: UUID string for the chart.
        build_id: Build provenance tag.
        panchanga: The 'panchanga' section from compute_chart() output.
                   Keys: tithi (dict), vara (dict), nakshatra (dict),
                         yoga (dict), karana (dict).
        lahiri_grahas: The 'grahas' sub-dict from per_ayanamsha['lahiri']
                       Used to extract sun/moon absolute longitudes.
        sunrise_utc: Optional sunrise UTC for birth date (from panchanga_daily).
        sunrise_ist: Optional 'HH:MM:SS' IST string for sunrise.

    Returns:
        dict ready for psycopg INSERT/UPDATE.

    Raises:
        ValueError: If any mandatory panchanga field is missing or malformed.
    """
    # ── Tithi ─────────────────────────────────────────────────────────────────
    tithi_raw = panchanga.get("tithi", {})
    if "error" in tithi_raw:
        raise ValueError(f"Tithi computation error: {tithi_raw['error']}")
    tithi_num = int(tithi_raw.get("index", 0))
    if not 1 <= tithi_num <= 30:
        raise ValueError(f"tithi_num out of range: {tithi_num}")
    tithi_name = TITHI_NAMES.get(tithi_num, tithi_raw.get("name", "Unknown"))
    paksha = "krishna" if tithi_num >= 16 else "shukla"
    # tithi_elapsed_pct: not always emitted; compute from fraction if available
    tithi_elapsed_pct: float | None = tithi_raw.get("elapsed_pct")

    # ── Vara ──────────────────────────────────────────────────────────────────
    vara_raw = panchanga.get("vara", {})
    if "error" in vara_raw:
        raise ValueError(f"Vara computation error: {vara_raw['error']}")
    vara_idx_raw = int(vara_raw.get("index", -1))
    # PyJHora vaara() returns a 1-based weekday (1=Sun..7=Sat) per some versions,
    # or 0-based (0=Sun..6=Sat) per others.  Normalise to 0-based.
    if vara_idx_raw in (1, 2, 3, 4, 5, 6, 7):
        vara_idx_0based = vara_idx_raw - 1    # 1-based → 0-based
    else:
        vara_idx_0based = vara_idx_raw % 7    # already 0-based or modulo
    vara_name = VARA_NAMES.get(vara_idx_0based, vara_raw.get("name", "Unknown"))
    # vara_num for storage: 1-based (1=Sun..7=Sat)
    vara_num = vara_idx_0based + 1

    # ── Nakshatra ─────────────────────────────────────────────────────────────
    nak_raw = panchanga.get("nakshatra", {})
    if "error" in nak_raw:
        raise ValueError(f"Nakshatra computation error: {nak_raw['error']}")
    nak_idx = int(nak_raw.get("index", 0))  # PyJHora 0-based
    nak_name = NAKSHATRA_NAMES[nak_idx] if 0 <= nak_idx < 27 else nak_raw.get("name", "Unknown")
    nak_pada = int(nak_raw.get("pada", 1))

    # ── Yoga ──────────────────────────────────────────────────────────────────
    yoga_raw = panchanga.get("yoga", {})
    if "error" in yoga_raw:
        raise ValueError(f"Yoga computation error: {yoga_raw['error']}")
    yoga_idx_raw = int(yoga_raw.get("index", 0))
    yoga_idx_0based = (yoga_idx_raw - 1) % 27 if yoga_idx_raw >= 1 else yoga_idx_raw % 27
    yoga_name = YOGA_NAMES[yoga_idx_0based] if 0 <= yoga_idx_0based < 27 else yoga_raw.get("name", "Unknown")
    yoga_num = yoga_idx_0based + 1

    # ── Karana ────────────────────────────────────────────────────────────────
    kar_raw = panchanga.get("karana", {})
    if "error" in kar_raw:
        raise ValueError(f"Karana computation error: {kar_raw['error']}")
    kar_idx_raw = int(kar_raw.get("index", 0))
    # PyJHora karana() returns 1-based index (1=Bava..11=Kimstughna).
    # Normalise to 0-based.  Both 1-based (1..11) and 0-based (0..10) are handled:
    # if the raw value is in [1..11] → treat as 1-based; else → treat as 0-based.
    if 1 <= kar_idx_raw <= 11:
        kar_idx_0based = kar_idx_raw - 1    # 1-based → 0-based
    else:
        kar_idx_0based = kar_idx_raw % 11   # 0-based or out-of-band; clamp via modulo
    karana_name = KARANA_NAMES[kar_idx_0based] if 0 <= kar_idx_0based < 11 else kar_raw.get("name", "Unknown")
    karana_num = kar_idx_0based + 1

    # ── Sun/Moon longitudes (Lahiri) ──────────────────────────────────────────
    sun_lon: float | None = None
    moon_lon: float | None = None
    if lahiri_grahas:
        sun_data = lahiri_grahas.get("Sun", {})
        moon_data = lahiri_grahas.get("Moon", {})
        sun_lon = sun_data.get("absolute_longitude")
        moon_lon = moon_data.get("absolute_longitude")

    return {
        "chart_id": chart_id,
        "build_id": build_id,
        "tithi_num": tithi_num,
        "tithi_name": tithi_name,
        "paksha": paksha,
        "tithi_elapsed_pct": tithi_elapsed_pct,
        "vara_num": vara_num,
        "vara_name": vara_name,
        "moon_nakshatra": nak_name,
        "moon_nakshatra_index": nak_idx,
        "moon_nakshatra_pada": nak_pada,
        "moon_longitude_deg": round(moon_lon, 8) if moon_lon is not None else None,
        "sun_longitude_deg": round(sun_lon, 8) if sun_lon is not None else None,
        "yoga_num": yoga_num,
        "yoga_name": yoga_name,
        "karana_num": karana_num,
        "karana_name": karana_name,
        "sunrise_ist": sunrise_ist,
        "sunrise_utc": sunrise_utc,
        "ayanamsha_id": "lahiri",
        "source_citation": SOURCE_CITATION,
        "engine_version": ENGINE_VERSION,
        "computed_at": datetime.now(timezone.utc),
    }


# ── DB upsert ─────────────────────────────────────────────────────────────────

_UPSERT_SQL = """
INSERT INTO chart_panchanga (
  chart_id, build_id,
  tithi_num, tithi_name, paksha, tithi_elapsed_pct,
  vara_num, vara_name,
  moon_nakshatra, moon_nakshatra_index, moon_nakshatra_pada,
  moon_longitude_deg, sun_longitude_deg,
  yoga_num, yoga_name,
  karana_num, karana_name,
  sunrise_ist, sunrise_utc,
  ayanamsha_id, source_citation, engine_version, computed_at
)
VALUES (
  %(chart_id)s, %(build_id)s,
  %(tithi_num)s, %(tithi_name)s, %(paksha)s, %(tithi_elapsed_pct)s,
  %(vara_num)s, %(vara_name)s,
  %(moon_nakshatra)s, %(moon_nakshatra_index)s, %(moon_nakshatra_pada)s,
  %(moon_longitude_deg)s, %(sun_longitude_deg)s,
  %(yoga_num)s, %(yoga_name)s,
  %(karana_num)s, %(karana_name)s,
  %(sunrise_ist)s, %(sunrise_utc)s,
  %(ayanamsha_id)s, %(source_citation)s, %(engine_version)s, %(computed_at)s
)
ON CONFLICT (chart_id, build_id) DO UPDATE SET
  tithi_num             = EXCLUDED.tithi_num,
  tithi_name            = EXCLUDED.tithi_name,
  paksha                = EXCLUDED.paksha,
  tithi_elapsed_pct     = EXCLUDED.tithi_elapsed_pct,
  vara_num              = EXCLUDED.vara_num,
  vara_name             = EXCLUDED.vara_name,
  moon_nakshatra        = EXCLUDED.moon_nakshatra,
  moon_nakshatra_index  = EXCLUDED.moon_nakshatra_index,
  moon_nakshatra_pada   = EXCLUDED.moon_nakshatra_pada,
  moon_longitude_deg    = EXCLUDED.moon_longitude_deg,
  sun_longitude_deg     = EXCLUDED.sun_longitude_deg,
  yoga_num              = EXCLUDED.yoga_num,
  yoga_name             = EXCLUDED.yoga_name,
  karana_num            = EXCLUDED.karana_num,
  karana_name           = EXCLUDED.karana_name,
  sunrise_ist           = EXCLUDED.sunrise_ist,
  sunrise_utc           = EXCLUDED.sunrise_utc,
  source_citation       = EXCLUDED.source_citation,
  engine_version        = EXCLUDED.engine_version,
  computed_at           = EXCLUDED.computed_at
"""


def write_panchanga(
    conn,
    chart_id: str,
    build_id: str,
    panchanga: dict[str, Any],
    *,
    lahiri_grahas: dict[str, Any] | None = None,
    sunrise_utc: datetime | None = None,
    sunrise_ist: str | None = None,
) -> dict[str, Any]:
    """
    Write (upsert) a single chart_panchanga row.

    Args:
        conn: Open psycopg connection (caller manages commit/rollback).
        chart_id: Chart UUID string.
        build_id: Build provenance tag.
        panchanga: 'panchanga' sub-dict from ganita.engine output.
        lahiri_grahas: Optional 'grahas' dict from per_ayanamsha['lahiri'].
        sunrise_utc: Optional sunrise UTC timestamp.
        sunrise_ist: Optional sunrise IST string ('HH:MM:SS').

    Returns:
        The built row dict (for logging / verification).
    """
    row = build_row(
        chart_id, build_id, panchanga,
        lahiri_grahas=lahiri_grahas,
        sunrise_utc=sunrise_utc,
        sunrise_ist=sunrise_ist,
    )
    with conn.cursor() as cur:
        cur.execute(_UPSERT_SQL, row)
    log.info(
        "chart_panchanga upserted: chart_id=%s tithi=%s vara=%s nak=%s yoga=%s karana=%s",
        chart_id, row["tithi_name"], row["vara_name"],
        row["moon_nakshatra"], row["yoga_name"], row["karana_name"],
    )
    return row


def write_from_engine_output(
    conn,
    engine_output: dict[str, Any],
    build_id: str,
    *,
    sunrise_utc: datetime | None = None,
    sunrise_ist: str | None = None,
) -> dict[str, Any]:
    """
    Convenience wrapper: accepts the full ganita.engine output dict and
    extracts chart_id, panchanga, and Lahiri grahas automatically.

    Args:
        conn: Open psycopg connection.
        engine_output: Dict returned by natal_engine.compute_chart().
        build_id: Build provenance tag.
        sunrise_utc: Optional sunrise UTC timestamp.
        sunrise_ist: Optional sunrise IST string.

    Returns:
        The built row dict.
    """
    chart_id = engine_output.get("chart_id")
    if not chart_id:
        raise ValueError("engine_output missing 'chart_id'")
    panchanga = engine_output.get("panchanga", {})
    lahiri_grahas = (
        engine_output.get("per_ayanamsha", {})
                     .get("lahiri", {})
                     .get("grahas")
    )
    return write_panchanga(
        conn, chart_id, build_id, panchanga,
        lahiri_grahas=lahiri_grahas,
        sunrise_utc=sunrise_utc,
        sunrise_ist=sunrise_ist,
    )


# ── CLI entry point ────────────────────────────────────────────────────────────

def _get_db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL env var not set")
    return url


def run_from_json(json_path: str, build_id: str) -> dict[str, Any]:
    """
    CLI helper: load engine output from a JSON file and write to DB.
    Usage: python -m pipeline.writers.panchanga_writer <engine_output.json> <build_id>
    """
    import json
    import psycopg

    with open(json_path) as f:
        engine_output = json.load(f)

    with psycopg.connect(_get_db_url()) as conn:
        row = write_from_engine_output(conn, engine_output, build_id)
        conn.commit()

    return row


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 3:
        print("Usage: python -m pipeline.writers.panchanga_writer <engine_output.json> <build_id>")
        sys.exit(1)

    result = run_from_json(sys.argv[1], sys.argv[2])
    print(json.dumps(
        {k: (str(v) if hasattr(v, 'isoformat') else v) for k, v in result.items()},
        indent=2
    ))
