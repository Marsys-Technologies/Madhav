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
  4. Upsert into panchanga_daily_staging.

Idempotent via build_id (mirrors bootstrap_ephemeris.py pattern).

Usage:
    python -m pipeline.bootstrap_panchanga [--build-id ID] [--dry-run]
                                           [--start YYYY-MM-DD] [--end YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import uuid
from datetime import date, datetime, timedelta
from typing import Any, Iterator

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
    special_yogas, choghadiya, hora, inauspicious, auspicious
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
    %(special_yogas)s::jsonb, %(choghadiya)s::jsonb, %(hora)s::jsonb,
    %(inauspicious)s::jsonb, %(auspicious)s::jsonb
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
    choghadiya               = EXCLUDED.choghadiya,
    hora                     = EXCLUDED.hora,
    inauspicious             = EXCLUDED.inauspicious,
    auspicious               = EXCLUDED.auspicious;
"""


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


def _compute_day(swe: Any, sunrise_jd_utc: float, sunrise_utc: datetime, d: date) -> dict[str, Any]:
    """
    Compute Sun + Moon longitudes at sunrise, derive all 5 panchanga elements,
    then append enrichment data (special_yogas, choghadiya, hora, inauspicious,
    auspicious) by delegating to the panchang_engine — the same path the live UI
    uses — to guarantee parity between the precomputed cache and on-demand results.

    amrit_kalam / varjyam are known S1 stubs in the engine (return empty lists);
    they will appear as [] in the inauspicious/auspicious JSONB until a future
    engine version implements them. That is expected and documented in 4C-S1 notes.
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

    # Enrichment — delegate to the high-level engine entry point so bootstrap
    # output is byte-identical to what the live UI computes via compute_panchang().
    # IST = UTC+330 minutes.
    from panchang_engine import compute_panchang
    from panchang_engine.serialize import panchang_to_dict
    _pan = compute_panchang(d, OBSERVER_LAT, OBSERVER_LON, 330)
    _enr = panchang_to_dict(_pan)

    return {
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
        # Enrichment columns — serialized to JSON strings; SQL casts to JSONB.
        "special_yogas": json.dumps(_enr["special_yogas"]),
        "choghadiya":    json.dumps(_enr["choghadiya"]),
        "hora":          json.dumps(_enr["hora"]),
        "inauspicious":  json.dumps(_enr["inauspicious"]),
        "auspicious":    json.dumps(_enr["auspicious"]),
    }


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
                "SELECT DISTINCT build_id, COUNT(*) FROM panchanga_daily_staging GROUP BY build_id"
            )
            rows = cur.fetchall()

    if not rows:
        return None

    for existing_build_id, count in rows:
        if existing_build_id == build_id:
            logger.info(
                "panchanga_daily_staging already has %d rows for build_id=%s; skipping.",
                count, build_id,
            )
            return count
        raise RuntimeError(
            f"panchanga_daily_staging already has {count} rows for build_id={existing_build_id!r}. "
            f"Refusing to overwrite with build_id={build_id!r}. "
            "Truncate panchanga_daily_staging manually before re-running."
        )

    return None


def run(
    build_id: str,
    start: date = DATE_START,
    end: date = DATE_END,
    dry_run: bool = False,
) -> int:
    """
    Compute and write panchanga rows into staging. Returns total rows written.
    """
    swe = _init_swe()
    logger.info(
        "bootstrap_panchanga: build_id=%s start=%s end=%s dry_run=%s",
        build_id, start, end, dry_run,
    )

    total_days = (end - start).days + 1
    logger.info("Expected rows: %d days", total_days)

    if not dry_run:
        db_url = os.environ["DATABASE_URL"]
        existing = _check_existing_rows(db_url, build_id)
        if existing is not None:
            return existing

    # DB driver only needed for real writes; skip the import entirely in dry-run
    # so this script runs on machines without psycopg installed.
    _use_psycopg2: bool = False
    if not dry_run:
        try:
            import psycopg2
            import psycopg2.extras
            _use_psycopg2 = True
        except ImportError:
            import psycopg  # type: ignore[no-redef]
            _use_psycopg2 = False

    def _flush(batch: list[dict[str, Any]]) -> int:
        if dry_run or not batch:
            return len(batch)
        if _use_psycopg2:
            with psycopg2.connect(db_url) as conn:
                psycopg2.extras.execute_batch(conn.cursor(), _UPSERT_SQL, batch, page_size=500)
                conn.commit()
        else:
            with psycopg.connect(db_url) as conn:
                with conn.cursor() as cur:
                    for row in batch:
                        cur.execute(_UPSERT_SQL, row)
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

        row_data = _compute_day(swe, sunrise_jd_utc, sunrise_utc, d)
        row_data["date"] = d
        row_data["ayanamsha"] = AYANAMSHA
        row_data["observer_lat"] = OBSERVER_LAT
        row_data["observer_lon"] = OBSERVER_LON
        row_data["observer_alt_m"] = OBSERVER_ALT_M
        row_data["ephemeris_version"] = EPHEMERIS_VERSION
        row_data["build_id"] = build_id
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
        "bootstrap_panchanga complete: %d days, %d rows written, build_id=%s%s",
        day_count, total_written, build_id,
        " [DRY RUN]" if dry_run else "",
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
    args = parser.parse_args()

    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)
    count = run(build_id=args.build_id, start=start, end=end, dry_run=args.dry_run)
    print(f"Done: {count} rows processed.")


if __name__ == "__main__":
    main()
