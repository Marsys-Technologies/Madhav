"""
pipeline.bootstrap_panchanga
MARSYS-JIS Phase 4C — Sunrise-anchored panchanga precompute for Bhubaneswar observer.

One-shot job that populates panchanga_daily_staging with one row per calendar date
across 1900-01-01 → 2100-12-31 (73,050 rows). After verification, operator swaps
staging → live per RUNBOOK_EPHEMERIS_REBUILD_v1_0.md §4.

For each date:
  1. Compute sunrise JD UTC via swe.rise_trans starting at midnight IST.
  2. Compute Sun + Moon sidereal Lahiri longitudes at the sunrise JD.
  3. Derive tithi / vara / moon nakshatra / yoga / karana via panchanga_derivations.
  4. (PSHIP-S3H, migration 069) Compute 5 enrichment columns via panchang_engine:
     special_yogas, inauspicious, auspicious, choghadiya, hora.
  5. Upsert into panchanga_daily_staging.

Idempotent via build_id (mirrors bootstrap_ephemeris.py pattern).

Usage:
    python -m pipeline.bootstrap_panchanga [--build-id ID] [--dry-run]
                                           [--start YYYY-MM-DD] [--end YYYY-MM-DD]
                                           [--rebuild]  # backfill enrichment cols on existing rows
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterator, Optional

logger = logging.getLogger(__name__)

# ── Observer constants ─────────────────────────────────────────────────────────
OBSERVER_LAT = 20.27021     # Bhubaneswar, Odisha (native birth location)
OBSERVER_LON = 85.82966
OBSERVER_ALT_M = 45.0
IST_OFFSET_HOURS = 5.5      # UTC + 5:30

EPHEMERIS_VERSION = "pyswisseph-2.10.03.2+4C-panchanga-v1"
AYANAMSHA = "lahiri"
BATCH_SIZE = 5_000

DATE_START = date(1900, 1, 1)
DATE_END = date(2100, 12, 31)

_UPSERT_SQL = """
INSERT INTO panchanga_daily_staging (
    date, sunrise_utc, sunrise_jd, sunrise_ist,
    tithi, tithi_name, paksha, tithi_fraction,
    vara, vara_lord, vara_index,
    moon_nakshatra, moon_nakshatra_index, moon_nakshatra_pada,
    moon_longitude_deg, sun_longitude_deg,
    yoga, yoga_index,
    karana, karana_position_in_month,
    ayanamsha, observer_lat, observer_lon, observer_alt_m,
    ephemeris_version, build_id,
    special_yogas, inauspicious, auspicious, choghadiya, hora
) VALUES (
    %(date)s, %(sunrise_utc)s, %(sunrise_jd)s, %(sunrise_ist)s,
    %(tithi)s, %(tithi_name)s, %(paksha)s, %(tithi_fraction)s,
    %(vara)s, %(vara_lord)s, %(vara_index)s,
    %(moon_nakshatra)s, %(moon_nakshatra_index)s, %(moon_nakshatra_pada)s,
    %(moon_longitude_deg)s, %(sun_longitude_deg)s,
    %(yoga)s, %(yoga_index)s,
    %(karana)s, %(karana_position_in_month)s,
    %(ayanamsha)s, %(observer_lat)s, %(observer_lon)s, %(observer_alt_m)s,
    %(ephemeris_version)s, %(build_id)s,
    %(special_yogas)s, %(inauspicious)s, %(auspicious)s, %(choghadiya)s, %(hora)s
)
ON CONFLICT (date) DO UPDATE SET
    sunrise_utc              = EXCLUDED.sunrise_utc,
    sunrise_jd               = EXCLUDED.sunrise_jd,
    sunrise_ist              = EXCLUDED.sunrise_ist,
    tithi                    = EXCLUDED.tithi,
    tithi_name               = EXCLUDED.tithi_name,
    paksha                   = EXCLUDED.paksha,
    tithi_fraction           = EXCLUDED.tithi_fraction,
    vara                     = EXCLUDED.vara,
    vara_lord                = EXCLUDED.vara_lord,
    vara_index               = EXCLUDED.vara_index,
    moon_nakshatra           = EXCLUDED.moon_nakshatra,
    moon_nakshatra_index     = EXCLUDED.moon_nakshatra_index,
    moon_nakshatra_pada      = EXCLUDED.moon_nakshatra_pada,
    moon_longitude_deg       = EXCLUDED.moon_longitude_deg,
    sun_longitude_deg        = EXCLUDED.sun_longitude_deg,
    yoga                     = EXCLUDED.yoga,
    yoga_index               = EXCLUDED.yoga_index,
    karana                   = EXCLUDED.karana,
    karana_position_in_month = EXCLUDED.karana_position_in_month,
    ayanamsha                = EXCLUDED.ayanamsha,
    observer_lat             = EXCLUDED.observer_lat,
    observer_lon             = EXCLUDED.observer_lon,
    observer_alt_m           = EXCLUDED.observer_alt_m,
    ephemeris_version        = EXCLUDED.ephemeris_version,
    build_id                 = EXCLUDED.build_id,
    special_yogas            = EXCLUDED.special_yogas,
    inauspicious             = EXCLUDED.inauspicious,
    auspicious               = EXCLUDED.auspicious,
    choghadiya               = EXCLUDED.choghadiya,
    hora                     = EXCLUDED.hora;
"""

# Enrichment-only UPDATE SQL: backfill the 5 JSONB columns for existing rows
# (used by --rebuild flag to populate migration 069 columns on pre-existing rows)
_ENRICH_UPDATE_SQL = """
UPDATE panchanga_daily
SET
    special_yogas = %(special_yogas)s,
    inauspicious  = %(inauspicious)s,
    auspicious    = %(auspicious)s,
    choghadiya    = %(choghadiya)s,
    hora          = %(hora)s,
    build_id      = %(build_id)s
WHERE date = %(date)s;
"""


def _dt_to_iso(dt: Optional[datetime]) -> Optional[str]:
    """Serialize a datetime (UTC-aware or naive) to ISO 8601 string, or None."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _timing_to_dict(t: Any) -> Optional[dict]:
    """Convert a Timing dataclass (or None) to a JSON-serializable dict."""
    if t is None:
        return None
    return {
        "label": t.label,
        "start_utc": _dt_to_iso(t.start_utc),
        "end_utc": _dt_to_iso(t.end_utc),
    }


def _yoga_to_dict(y: dict) -> dict:
    """Convert a special-yoga dict (from detect_all_special_yogas) to JSON-serializable form."""
    return {
        "yoga": y["yoga"],
        "start_utc": _dt_to_iso(y["start_utc"]),
        "end_utc": _dt_to_iso(y["end_utc"]),
        "strength": y.get("strength", ""),
        "stars": y.get("stars", 0),
    }


def _compute_enrichment(
    swe: Any,
    sunrise_utc: datetime,
    sunrise_jd_utc: float,
    d: date,
    vara_index: int,
    moon_nakshatra_index: int,
    tithi: int,
    yoga_index: int,
    karana_name: str,
    karana_position_in_month: int,
    moon_longitude_deg: float,
) -> dict[str, str]:
    """
    Compute the 5 enrichment JSONB columns for migration 069:
      special_yogas, inauspicious, auspicious, choghadiya, hora.

    Calls panchang_engine's detect_all_special_yogas(), compute_inauspicious_timings(),
    compute_auspicious_timings(), compute_choghadiya(), and compute_hora().

    The bootstrap already has sunrise_jd_utc. We compute sunset by calling
    swe.rise_trans for CALC_SET (reusing the same swe instance already initialised).

    Returns a dict with keys: 'special_yogas', 'inauspicious', 'auspicious',
    'choghadiya', 'hora' — values are JSON strings (ready for psycopg JSONB params).
    """
    # ── 1. Compute sunset and next-sunrise ─────────────────────────────────────
    # Sunset: search from shortly after current sunrise
    geopos = [OBSERVER_LON, OBSERVER_LAT, OBSERVER_ALT_M]
    flags = swe.FLG_SWIEPH

    # Sunset
    sunset_flag, sunset_ret = swe.rise_trans(
        sunrise_jd_utc + 0.1, swe.SUN, swe.CALC_SET, geopos, 0, 0, flags=flags
    )
    if sunset_flag < 0:
        raise RuntimeError(f"swe.rise_trans (sunset) failed for {d}: flag={sunset_flag}")
    sunset_jd = sunset_ret[0]
    sy, sm_, sd, sh_dec = swe.revjul(sunset_jd)
    shour = int(sh_dec); smin = int((sh_dec - shour) * 60); ssec = int(((sh_dec - shour)*60 - smin)*60)
    sunset_utc = datetime(sy, sm_, sd, shour, smin, ssec, tzinfo=timezone.utc)

    # Next-day sunrise (for choghadiya night + hora 24-hr cycle)
    next_jd_midnight_ist = swe.julday(d.year, d.month, d.day + 1 if d.day < 28 else (d + timedelta(days=1)).day,
                                       -IST_OFFSET_HOURS)
    # Use timedelta to get next date safely
    next_date = d + timedelta(days=1)
    next_jd_midnight_ist = swe.julday(next_date.year, next_date.month, next_date.day, -IST_OFFSET_HOURS)
    rsmi = swe.CALC_RISE | swe.BIT_DISC_CENTER
    next_flag, next_ret = swe.rise_trans(
        next_jd_midnight_ist, swe.SUN, rsmi, geopos, 0, 0, flags=flags
    )
    if next_flag < 0:
        raise RuntimeError(f"swe.rise_trans (next sunrise) failed for {next_date}: flag={next_flag}")
    next_sunrise_jd = next_ret[0]
    ny, nm_, nd, nh_dec = swe.revjul(next_sunrise_jd)
    nhour = int(nh_dec); nmin = int((nh_dec - nhour)*60); nsec = int(((nh_dec - nhour)*60 - nmin)*60)
    next_sunrise_utc = datetime(ny, nm_, nd, nhour, nmin, nsec, tzinfo=timezone.utc)

    # Ensure sunrise is UTC-aware
    sr_utc = sunrise_utc if sunrise_utc.tzinfo is not None else sunrise_utc.replace(tzinfo=timezone.utc)

    # ── 2. Build Anga objects needed by detect_all_special_yogas ──────────────
    # The panchang_engine Anga dataclass needs (id, name, end_utc).
    # For bootstrap purposes end_utc is set to next_sunrise_utc (conservative:
    # the yoga window is clipped by the detect_* functions themselves).
    from panchang_engine.types import Anga
    from panchang_engine.special_yogas import detect_all_special_yogas
    from panchang_engine.timings import (
        compute_inauspicious_timings,
        compute_auspicious_timings,
        compute_choghadiya,
        compute_hora,
    )
    from pipeline.panchanga_derivations import (
        NAKSHATRAS, YOGAS, TITHI_NAMES, VARA_NAMES,
        MOVABLE_KARANAS, FIXED_KARANA_POSITIONS,
    )

    # vara Anga: vara_index from bootstrap is 0-based (Python weekday-derived; Vedic Sun=0..Sat=6)
    # panchang_engine Anga.id for vara uses 1-based (Sun=1..Sat=7)
    vara_id_1based = vara_index + 1  # vara_index stored as 0..6 in bootstrap

    # Nakshatra Anga — moon_nakshatra_index is stored 0-based in bootstrap (from compute_moon_nakshatra)
    # but panchang_engine uses 1-based. Detect which convention is in use:
    # panchanga_derivations.compute_moon_nakshatra returns nak_idx as 0..26 (0-based).
    # The bootstrap stores it as moon_nakshatra_index (which is 0-based from compute_moon_nakshatra).
    nak_idx_0based = moon_nakshatra_index  # 0..26
    nak_name = NAKSHATRAS[nak_idx_0based] if 0 <= nak_idx_0based <= 26 else "Unknown"
    nak_anga = Anga(id=nak_idx_0based + 1, name=nak_name, end_utc=next_sunrise_utc)

    # Yoga Anga (yoga_index is 1-based from compute_yoga; panchang_engine Anga.id 1-based)
    yoga_name_val = YOGAS[yoga_index - 1] if 1 <= yoga_index <= 27 else "Unknown"
    yoga_anga = Anga(id=yoga_index, name=yoga_name_val, end_utc=next_sunrise_utc)

    # Tithi Anga (1-based)
    tithi_name_val = TITHI_NAMES[tithi - 1] if 1 <= tithi <= 30 else "Unknown"
    tithi_anga = Anga(id=tithi, name=tithi_name_val, end_utc=next_sunrise_utc)

    # Vara Anga
    vara_anga = Anga(id=vara_id_1based, name=VARA_NAMES[vara_index], end_utc=next_sunrise_utc)

    # Karana Angas — the bootstrap stores karana_name (single, sunrise-active) + position.
    # For detect_all_special_yogas we need karana_first/karana_second as Anga objects.
    # Build a canonical list of all 11 karana names (4 fixed + 7 movable) to derive id.
    # Order: Kintughna(1), Bava(2)..Vishti(8), Shakuni(9), Catushpada(10), Naga(11).
    _ALL_KARANAS = ["Kintughna"] + MOVABLE_KARANAS + ["Shakuni", "Catushpada", "Naga"]
    karana_id = (_ALL_KARANAS.index(karana_name) + 1) if karana_name in _ALL_KARANAS else 1
    karana_first = Anga(id=karana_id, name=karana_name, end_utc=next_sunrise_utc)
    # karana_second: next karana in the cycle (wraps within 1..11)
    karana_second_id = (karana_id % 11) + 1
    karana_second_name = _ALL_KARANAS[karana_second_id - 1]
    karana_second = Anga(id=karana_second_id, name=karana_second_name, end_utc=next_sunrise_utc)

    # ── 3. Compute special yogas ───────────────────────────────────────────────
    special_yogas_raw = detect_all_special_yogas(
        sunrise_utc=sr_utc,
        sunset_utc=sunset_utc,
        next_sunrise_utc=next_sunrise_utc,
        tithi=tithi_anga,
        nakshatra=nak_anga,
        yoga=yoga_anga,
        karana_first=karana_first,
        karana_second=karana_second,
        vara=vara_anga,
    )
    special_yogas_json = json.dumps([_yoga_to_dict(y) for y in special_yogas_raw])

    # ── 4. Compute inauspicious timings ────────────────────────────────────────
    inausp_raw = compute_inauspicious_timings(sr_utc, sunset_utc, vara_id_1based)
    inausp_dict = {k: _timing_to_dict(v) for k, v in inausp_raw.items()}
    inauspicious_json = json.dumps(inausp_dict)

    # ── 5. Compute auspicious timings ─────────────────────────────────────────
    ausp_raw = compute_auspicious_timings(
        sr_utc, sunset_utc, vara_id_1based,
        tithi_id=tithi,
        nakshatra_id=moon_nakshatra_index,
    )
    ausp_dict = {k: _timing_to_dict(v) for k, v in ausp_raw.items()}
    auspicious_json = json.dumps(ausp_dict)

    # ── 6. Compute Choghadiya ─────────────────────────────────────────────────
    chog_raw = compute_choghadiya(sr_utc, sunset_utc, next_sunrise_utc, vara_id_1based)
    chog_dict = {
        "day": [_timing_to_dict(t) for t in chog_raw.get("day", [])],
        "night": [_timing_to_dict(t) for t in chog_raw.get("night", [])],
    }
    choghadiya_json = json.dumps(chog_dict)

    # ── 7. Compute Hora ───────────────────────────────────────────────────────
    hora_raw = compute_hora(sr_utc, next_sunrise_utc, vara_id_1based)
    hora_json = json.dumps([_timing_to_dict(t) for t in hora_raw])

    return {
        "special_yogas": special_yogas_json,
        "inauspicious": inauspicious_json,
        "auspicious": auspicious_json,
        "choghadiya": choghadiya_json,
        "hora": hora_json,
    }


def _init_swe() -> Any:
    try:
        import swisseph as swe
    except ImportError as exc:
        raise RuntimeError(
            "pyswisseph is not installed. Add 'pyswisseph>=2.10.0' to requirements.txt."
        ) from exc
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    return swe


def _compute_sunrise(swe: Any, year: int, month: int, day: int) -> tuple[float, datetime]:
    """
    Return (sunrise_jd_utc, sunrise_datetime_utc).
    Search starts at midnight IST of the requested IST date, which is
    (year, month, day, -5.5h UT) = 18:30 UT of the prior calendar day.
    This ensures the returned sunrise is unambiguously the sunrise OF
    date Y-M-D in IST.
    """
    jd_midnight_ist = swe.julday(year, month, day, -IST_OFFSET_HOURS)
    geopos = [OBSERVER_LON, OBSERVER_LAT, OBSERVER_ALT_M]
    flags = swe.FLG_SWIEPH
    rsmi = swe.CALC_RISE | swe.BIT_DISC_CENTER
    retflag, tret = swe.rise_trans(
        jd_midnight_ist, swe.SUN, rsmi, geopos, 0, 0, flags=flags
    )
    if retflag < 0:
        raise RuntimeError(
            f"swe.rise_trans returned error {retflag} for {year}-{month:02d}-{day:02d}"
        )
    sunrise_jd_utc = tret[0]
    y, m, d, h_dec = swe.revjul(sunrise_jd_utc)
    hour = int(h_dec)
    minute = int((h_dec - hour) * 60)
    second = int(((h_dec - hour) * 60 - minute) * 60)
    sunrise_utc = datetime(y, m, d, hour, minute, second)
    return sunrise_jd_utc, sunrise_utc


def _compute_day(
    swe: Any,
    sunrise_jd_utc: float,
    sunrise_utc: datetime,
    d: date,
    enrich: bool = True,
) -> dict[str, Any]:
    """
    Compute Sun + Moon longitudes at sunrise, derive all 5 panchanga elements.
    When enrich=True (PSHIP-S3H default), also computes the 5 JSONB enrichment columns.
    Returns dict matching panchanga_daily schema (excluding date, build_id, provenance).
    """
    flags = swe.FLG_SIDEREAL | swe.FLG_SWIEPH
    sun_pos, _ = swe.calc_ut(sunrise_jd_utc, swe.SUN, flags)
    moon_pos, _ = swe.calc_ut(sunrise_jd_utc, swe.MOON, flags)
    sun_lon = sun_pos[0] % 360.0
    moon_lon = moon_pos[0] % 360.0

    from .panchanga_derivations import (
        compute_tithi, compute_vara, compute_moon_nakshatra,
        compute_yoga, compute_karana,
    )

    tithi_idx, tithi_name, paksha, tithi_frac = compute_tithi(sun_lon, moon_lon)

    # Vara is determined by the weekday at sunrise in IST (not UTC).
    sunrise_ist = sunrise_utc + timedelta(hours=IST_OFFSET_HOURS)
    vara_idx, vara_name, vara_lord = compute_vara(sunrise_ist)

    nak_name, nak_idx, pada = compute_moon_nakshatra(moon_lon)
    yoga_idx, yoga_name = compute_yoga(sun_lon, moon_lon)
    karana_pos, karana_name = compute_karana(tithi_frac)

    row: dict[str, Any] = {
        "sunrise_utc": sunrise_utc.isoformat(sep=" "),
        "sunrise_jd": sunrise_jd_utc,
        "sunrise_ist": sunrise_ist.time().isoformat(),
        "tithi": tithi_idx,
        "tithi_name": tithi_name,
        "paksha": paksha,
        "tithi_fraction": tithi_frac,
        "vara": vara_name,
        "vara_lord": vara_lord,
        "vara_index": vara_idx,
        "moon_nakshatra": nak_name,
        "moon_nakshatra_index": nak_idx,
        "moon_nakshatra_pada": pada,
        "moon_longitude_deg": round(moon_lon, 7),
        "sun_longitude_deg": round(sun_lon, 7),
        "yoga": yoga_name,
        "yoga_index": yoga_idx,
        "karana": karana_name,
        "karana_position_in_month": karana_pos,
    }

    if enrich:
        try:
            enrichment = _compute_enrichment(
                swe=swe,
                sunrise_utc=sunrise_utc,
                sunrise_jd_utc=sunrise_jd_utc,
                d=d,
                vara_index=vara_idx,
                moon_nakshatra_index=nak_idx,
                tithi=tithi_idx,
                yoga_index=yoga_idx,
                karana_name=karana_name,
                karana_position_in_month=karana_pos,
                moon_longitude_deg=round(moon_lon, 7),
            )
            row.update(enrichment)
        except Exception as exc:
            logger.warning("Enrichment failed for %s: %s — storing NULL for 5 JSONB cols", d, exc)
            row.update({
                "special_yogas": None,
                "inauspicious": None,
                "auspicious": None,
                "choghadiya": None,
                "hora": None,
            })
    else:
        row.update({
            "special_yogas": None,
            "inauspicious": None,
            "auspicious": None,
            "choghadiya": None,
            "hora": None,
        })

    return row


def _date_range(start: date, end: date) -> Iterator[date]:
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def _check_existing_rows(db_url: str, build_id: str) -> int | None:
    try:
        import psycopg2
    except ImportError:
        import psycopg as psycopg2  # type: ignore[no-redef]

    with psycopg2.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT build_id, COUNT(*) FROM panchanga_daily GROUP BY build_id"
            )
            rows = cur.fetchall()

    if not rows:
        return None

    for existing_build_id, count in rows:
        if existing_build_id == build_id:
            logger.info(
                "panchanga_daily already has %d rows for build_id=%s; skipping.",
                count, build_id,
            )
            return count
        raise RuntimeError(
            f"panchanga_daily already has {count} rows for build_id={existing_build_id!r}. "
            f"Refusing to overwrite with build_id={build_id!r}. "
            "Delete the existing rows manually before re-running."
        )

    return None


def run(
    build_id: str,
    start: date = DATE_START,
    end: date = DATE_END,
    dry_run: bool = False,
    enrich: bool = True,
    rebuild: bool = False,
) -> int:
    """
    Compute and write panchanga rows into staging (or live for --rebuild).
    Returns total rows written.

    rebuild=True: backfill enrichment columns on panchanga_daily (not staging).
    enrich=True (default): compute all 5 JSONB columns per row.
    dry_run=True: compute but do not write to DB.
    """
    swe = _init_swe()
    logger.info(
        "bootstrap_panchanga: build_id=%s start=%s end=%s dry_run=%s enrich=%s rebuild=%s",
        build_id, start, end, dry_run, enrich, rebuild,
    )

    total_days = (end - start).days + 1
    logger.info("Expected rows: %d days", total_days)

    if not dry_run:
        db_url = os.environ["DATABASE_URL"]
        if not rebuild:
            existing = _check_existing_rows(db_url, build_id)
            if existing is not None:
                return existing

    try:
        import psycopg2
        import psycopg2.extras
        _use_psycopg2 = True
    except ImportError:
        import psycopg  # type: ignore[no-redef]
        _use_psycopg2 = False

    # For --rebuild, use direct UPDATE on panchanga_daily; otherwise UPSERT into staging.
    _sql = _ENRICH_UPDATE_SQL if rebuild else _UPSERT_SQL

    def _flush(batch: list[dict[str, Any]]) -> int:
        if dry_run or not batch:
            return len(batch)
        if _use_psycopg2:
            with psycopg2.connect(db_url) as conn:
                psycopg2.extras.execute_batch(conn.cursor(), _sql, batch, page_size=500)
                conn.commit()
        else:
            with psycopg.connect(db_url) as conn:
                with conn.cursor() as cur:
                    for row in batch:
                        cur.execute(_sql, row)
                conn.commit()
        return len(batch)

    batch: list[dict[str, Any]] = []
    total_written = 0
    day_count = 0

    for d in _date_range(start, end):
        try:
            sunrise_jd_utc, sunrise_utc = _compute_sunrise(swe, d.year, d.month, d.day)
        except RuntimeError as exc:
            logger.warning("Sunrise compute failed for %s: %s — skipping", d, exc)
            continue

        row_data = _compute_day(swe, sunrise_jd_utc, sunrise_utc, d=d, enrich=enrich)
        row_data["date"] = d
        row_data["ayanamsha"] = AYANAMSHA
        row_data["observer_lat"] = OBSERVER_LAT
        row_data["observer_lon"] = OBSERVER_LON
        row_data["observer_alt_m"] = OBSERVER_ALT_M
        row_data["ephemeris_version"] = EPHEMERIS_VERSION
        row_data["build_id"] = build_id

        if rebuild:
            # For --rebuild, only need the enrichment columns + date + build_id
            rebuild_row = {
                "date": row_data["date"],
                "build_id": build_id,
                "special_yogas": row_data.get("special_yogas"),
                "inauspicious": row_data.get("inauspicious"),
                "auspicious": row_data.get("auspicious"),
                "choghadiya": row_data.get("choghadiya"),
                "hora": row_data.get("hora"),
            }
            batch.append(rebuild_row)
        else:
            batch.append(row_data)

        day_count += 1

        if len(batch) >= BATCH_SIZE:
            written = _flush(batch)
            total_written += written
            batch = []
            if day_count % 5000 == 0:
                logger.info(
                    "Progress: %d / %d days (%d rows written)",
                    day_count, total_days, total_written,
                )

    total_written += _flush(batch)
    logger.info(
        "bootstrap_panchanga complete: %d days, %d rows written, build_id=%s%s%s",
        day_count, total_written, build_id,
        " [DRY RUN]" if dry_run else "",
        " [REBUILD]" if rebuild else "",
    )
    return total_written


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(
        description="Bootstrap panchanga_daily_staging via Swiss Ephemeris sunrise compute"
    )
    parser.add_argument("--build-id", default=str(uuid.uuid4()), help="Build ID for provenance")
    parser.add_argument("--start", default=str(DATE_START), help="Start date YYYY-MM-DD")
    parser.add_argument("--end", default=str(DATE_END), help="End date YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true", help="Compute but do not write to DB")
    parser.add_argument(
        "--no-enrich",
        action="store_true",
        help="Skip enrichment columns (special_yogas etc.); stores NULL for the 5 JSONB cols",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help=(
            "Backfill migration 069 enrichment columns on panchanga_daily (live table, not staging). "
            "Run after applying migration 069 to populate the 5 new JSONB cols. ~60min for full 73K rows. "
            "Command: DATABASE_URL=$DB python -m pipeline.bootstrap_panchanga --rebuild"
        ),
    )
    args = parser.parse_args()

    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)
    count = run(
        build_id=args.build_id,
        start=start,
        end=end,
        dry_run=args.dry_run,
        enrich=not args.no_enrich,
        rebuild=args.rebuild,
    )
    print(f"Done: {count} rows processed.")


if __name__ == "__main__":
    main()
