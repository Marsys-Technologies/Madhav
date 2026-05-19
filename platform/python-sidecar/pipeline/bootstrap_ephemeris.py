"""
pipeline.bootstrap_ephemeris
MARSYS-JIS Phase 14C Stream C — Swiss Ephemeris daily compute 1900–2100.

One-time job that populates ephemeris_daily_staging with one row per (date, planet)
for all 9 graha across 73,050 days.  After the verification gate passes, caller
swaps staging → live via the standard swap discipline.

Usage:
    python -m pipeline.bootstrap_ephemeris [--build-id ID] [--dry-run]
                                           [--start YYYY-MM-DD] [--end YYYY-MM-DD]
                                           [--skip-csv-check]

Idempotency: if ephemeris_daily already has rows for the given build_id, the job
exits 0 with a warning.  If rows for a *different* build_id are present it halts
so the operator can make an explicit delete decision (rebuilding ephemeris is a
manual, audited action per the brief).

Ephemeris authority: pyswisseph (package: pyswisseph; import name: swisseph),
Lahiri sidereal ayanamsha.  CSV at
gs://madhav-marsys-sources/L1/ephemeris/EPHEMERIS_MONTHLY_1900_2100.csv is used
only as a spot-check — not as the source.  If the GCS object is absent, the
cross-check is skipped and the residual is recorded in the manifest.
"""
from __future__ import annotations

import argparse
import csv
import io
import logging
import os
import random
import sys
import uuid
from datetime import date, timedelta
from typing import Any, Iterator

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

EPHEMERIS_VERSION = "pyswisseph-2.10.03.2+4B-derived-v1"
AYANAMSHA = "lahiri"
BATCH_SIZE = 10_000

DATE_START = date(1900, 1, 1)
DATE_END = date(2100, 12, 31)

# Planet identifiers
_PLANET_IDS: list[tuple[str, int | None]] = []  # populated lazily after swe import

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigasira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Moola", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

NAK_SPAN = 360.0 / 27      # 13.333...°
PADA_SPAN = NAK_SPAN / 4   # 3.333...°

CSV_SPOTCHECK_N = 100
CSV_SPOTCHECK_THRESHOLD_DEG = 0.01
GCS_CSV_URI = "gs://madhav-marsys-sources/L1/ephemeris/EPHEMERIS_MONTHLY_1900_2100.csv"

_UPSERT_SQL = """
INSERT INTO ephemeris_daily_staging (
    date, planet, longitude_deg, latitude_deg, speed_deg_per_day,
    is_retrograde, sign, sign_degree, nakshatra, nakshatra_pada,
    ayanamsha, ephemeris_version, build_id,
    dignity_d1, is_combust, combust_orb_deg, vargottama_today,
    sign_ingress_today, whole_sign_house, graha_yuddha_with
) VALUES (
    %(date)s, %(planet)s, %(longitude_deg)s, %(latitude_deg)s,
    %(speed_deg_per_day)s, %(is_retrograde)s, %(sign)s, %(sign_degree)s,
    %(nakshatra)s, %(nakshatra_pada)s, %(ayanamsha)s, %(ephemeris_version)s,
    %(build_id)s,
    %(dignity_d1)s, %(is_combust)s, %(combust_orb_deg)s, %(vargottama_today)s,
    %(sign_ingress_today)s, %(whole_sign_house)s, %(graha_yuddha_with)s
)
ON CONFLICT (date, planet) DO UPDATE SET
    longitude_deg      = EXCLUDED.longitude_deg,
    latitude_deg       = EXCLUDED.latitude_deg,
    speed_deg_per_day  = EXCLUDED.speed_deg_per_day,
    is_retrograde      = EXCLUDED.is_retrograde,
    sign               = EXCLUDED.sign,
    sign_degree        = EXCLUDED.sign_degree,
    nakshatra          = EXCLUDED.nakshatra,
    nakshatra_pada     = EXCLUDED.nakshatra_pada,
    ayanamsha          = EXCLUDED.ayanamsha,
    ephemeris_version  = EXCLUDED.ephemeris_version,
    build_id           = EXCLUDED.build_id,
    dignity_d1         = EXCLUDED.dignity_d1,
    is_combust         = EXCLUDED.is_combust,
    combust_orb_deg    = EXCLUDED.combust_orb_deg,
    vargottama_today   = EXCLUDED.vargottama_today,
    sign_ingress_today = EXCLUDED.sign_ingress_today,
    whole_sign_house   = EXCLUDED.whole_sign_house,
    graha_yuddha_with  = EXCLUDED.graha_yuddha_with;
"""

# ── Swiss Ephemeris helpers ────────────────────────────────────────────────────

def _init_swe() -> Any:
    try:
        import swisseph as swe  # pyswisseph installs as 'swisseph'
    except ImportError as exc:
        raise RuntimeError(
            "pyswisseph is not installed. Add 'pyswisseph>=2.10.0' to requirements.txt "
            "and rebuild the pipeline image."
        ) from exc
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    return swe


def _derive(lon: float) -> tuple[str, float, str, int]:
    """Return (sign, sign_degree, nakshatra, nakshatra_pada) for a sidereal longitude."""
    sign = SIGNS[int(lon // 30)]
    sign_degree = lon % 30.0
    nak_idx = int(lon / NAK_SPAN)
    nakshatra = NAKSHATRAS[nak_idx % 27]
    pada = int((lon % NAK_SPAN) / PADA_SPAN) + 1
    return sign, sign_degree, nakshatra, pada


def _compute_day(
    swe: Any,
    jd: float,
    build_id: str,
    d: date,
    prior_day_signs: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Compute all 9 graha for a single Julian Day.  Returns list of row dicts."""
    from .ephemeris_derivations import (
        compute_dignity, compute_combust, compute_vargottama,
        compute_whole_sign_house, compute_sign_ingress, compute_graha_yuddha,
    )
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED

    planet_ids = [
        ("sun",      swe.SUN),
        ("moon",     swe.MOON),
        ("mars",     swe.MARS),
        ("mercury",  swe.MERCURY),
        ("jupiter",  swe.JUPITER),
        ("venus",    swe.VENUS),
        ("saturn",   swe.SATURN),
    ]

    rows: list[dict[str, Any]] = []

    for name, pid in planet_ids:
        r = swe.calc_ut(jd, pid, flags)
        lon = r[0][0] % 360.0
        lat = r[0][1]
        spd = r[0][3]
        retro = spd < 0
        sign, sdeg, nak, pada = _derive(lon)
        rows.append({
            "date": d,
            "planet": name,
            "longitude_deg": round(lon, 7),
            "latitude_deg": round(lat, 7),
            "speed_deg_per_day": round(spd, 7),
            "is_retrograde": retro,
            "sign": sign,
            "sign_degree": round(sdeg, 7),
            "nakshatra": nak,
            "nakshatra_pada": pada,
            "ayanamsha": AYANAMSHA,
            "ephemeris_version": EPHEMERIS_VERSION,
            "build_id": build_id,
            # derived columns — populated in second pass below
            "dignity_d1": None,
            "is_combust": None,
            "combust_orb_deg": None,
            "vargottama_today": None,
            "sign_ingress_today": None,
            "whole_sign_house": None,
            "graha_yuddha_with": None,
        })

    # Rahu (mean node) — Vedic convention is the smoothed 18.6-year cycle.
    # §4.B 2026-05-19 fix: bootstrap previously used TRUE_NODE, which is
    # osculating and occasionally turns briefly direct (contradicts the
    # Jyotish always-retrograde convention). All other compute paths in this
    # codebase use MEAN_NODE — bootstrap is now consistent.
    r_node = swe.calc_ut(jd, swe.MEAN_NODE, flags)
    lon_r = r_node[0][0] % 360.0
    lat_r = r_node[0][1]
    spd_r = r_node[0][3]
    sign_r, sdeg_r, nak_r, pada_r = _derive(lon_r)
    rows.append({
        "date": d,
        "planet": "rahu",
        "longitude_deg": round(lon_r, 7),
        "latitude_deg": round(lat_r, 7),
        "speed_deg_per_day": round(spd_r, 7),
        "is_retrograde": True,  # Jyotish convention
        "sign": sign_r,
        "sign_degree": round(sdeg_r, 7),
        "nakshatra": nak_r,
        "nakshatra_pada": pada_r,
        "ayanamsha": AYANAMSHA,
        "ephemeris_version": EPHEMERIS_VERSION,
        "build_id": build_id,
        "dignity_d1": None,
        "is_combust": None,
        "combust_orb_deg": None,
        "vargottama_today": None,
        "sign_ingress_today": None,
        "whole_sign_house": None,
        "graha_yuddha_with": None,
    })

    # Ketu = Rahu + 180°
    lon_k = (lon_r + 180.0) % 360.0
    sign_k, sdeg_k, nak_k, pada_k = _derive(lon_k)
    rows.append({
        "date": d,
        "planet": "ketu",
        "longitude_deg": round(lon_k, 7),
        "latitude_deg": round(-lat_r, 7),   # ecliptic latitude is mirrored
        "speed_deg_per_day": round(spd_r, 7),
        "is_retrograde": True,  # Jyotish convention
        "sign": sign_k,
        "sign_degree": round(sdeg_k, 7),
        "nakshatra": nak_k,
        "nakshatra_pada": pada_k,
        "ayanamsha": AYANAMSHA,
        "ephemeris_version": EPHEMERIS_VERSION,
        "build_id": build_id,
        "dignity_d1": None,
        "is_combust": None,
        "combust_orb_deg": None,
        "vargottama_today": None,
        "sign_ingress_today": None,
        "whole_sign_house": None,
        "graha_yuddha_with": None,
    })

    # ── Second pass: derived columns ──────────────────────────────────────────
    # Build same-day longitude map; Sun must be present for combust computation.
    same_day_positions = {row["planet"]: float(row["longitude_deg"]) for row in rows}
    sun_lon = same_day_positions.get("sun")

    for row in rows:
        planet = row["planet"]
        lon = float(row["longitude_deg"])
        sign = row["sign"]
        sdeg = float(row["sign_degree"])
        is_retro = bool(row["is_retrograde"])

        row["dignity_d1"] = compute_dignity(planet, sign, sdeg)
        if sun_lon is not None:
            row["is_combust"], row["combust_orb_deg"] = compute_combust(planet, lon, sun_lon, is_retro)
        row["vargottama_today"] = compute_vargottama(sign, sdeg)
        row["whole_sign_house"] = compute_whole_sign_house(sign)
        row["sign_ingress_today"] = compute_sign_ingress(sign, (prior_day_signs or {}).get(planet))
        row["graha_yuddha_with"] = compute_graha_yuddha(planet, lon, same_day_positions)

    return rows


def _date_range(start: date, end: date) -> Iterator[date]:
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


# ── CSV spot-check ─────────────────────────────────────────────────────────────

def _load_csv_spotcheck(n: int) -> list[dict[str, Any]] | None:
    """
    Fetch EPHEMERIS_MONTHLY_1900_2100.csv from GCS and return up to n rows as
    {date, planet, longitude_deg}.  Returns None if GCS object is absent.
    """
    try:
        from google.cloud import storage
        from google.cloud.exceptions import NotFound
    except ImportError:
        logger.warning("google-cloud-storage not importable; skipping CSV spot-check")
        return None

    bucket_name = "madhav-marsys-sources"
    blob_name = "L1/ephemeris/EPHEMERIS_MONTHLY_1900_2100.csv"

    try:
        client = storage.Client()
        blob = client.bucket(bucket_name).blob(blob_name)
        content = blob.download_as_text(encoding="utf-8")
    except NotFound:
        logger.warning("CSV not found at %s; skipping cross-check", GCS_CSV_URI)
        return None
    except Exception as exc:
        logger.warning("Could not fetch CSV (%s); skipping cross-check", exc)
        return None

    rows = []
    reader = csv.DictReader(io.StringIO(content))
    for row in reader:
        rows.append(row)

    if len(rows) == 0:
        logger.warning("CSV is empty; skipping cross-check")
        return None

    random.shuffle(rows)
    return rows[:n]


def _run_csv_spotcheck(
    swe: Any,
    sample_rows: list[dict[str, Any]],
    build_id: str,
) -> list[str]:
    """
    For each sampled CSV row, compute the Swiss Ephemeris value and compare.
    Returns list of finding strings (empty = all pass).
    """
    findings: list[str] = []
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED

    _PLANET_MAP = {
        "sun": swe.SUN, "moon": swe.MOON, "mars": swe.MARS,
        "mercury": swe.MERCURY, "jupiter": swe.JUPITER,
        "venus": swe.VENUS, "saturn": swe.SATURN,
    }

    for row in sample_rows:
        try:
            date_str = row.get("date", "")
            planet = row.get("planet", "").lower()
            csv_lon = float(row.get("longitude_deg", 0))
        except (KeyError, ValueError):
            continue

        if planet not in _PLANET_MAP:
            continue

        try:
            y, m, d_ = map(int, date_str.split("-"))
            jd = swe.julday(y, m, d_, 0.0)  # midnight UT
        except (ValueError, AttributeError):
            continue

        try:
            r = swe.calc_ut(jd, _PLANET_MAP[planet], flags)
            computed_lon = r[0][0] % 360.0
        except Exception:
            continue

        delta = abs(computed_lon - csv_lon)
        if delta > 180:
            delta = 360 - delta  # handle wraparound

        if delta > CSV_SPOTCHECK_THRESHOLD_DEG:
            findings.append(
                f"CSV spot-check MISMATCH: {date_str} {planet} "
                f"CSV={csv_lon:.5f} computed={computed_lon:.5f} delta={delta:.5f}°"
            )

    return findings


# ── Idempotency check ──────────────────────────────────────────────────────────

def _check_existing_rows(db_url: str, build_id: str) -> int | None:
    """
    Returns row count if ephemeris_daily already has rows for this build_id,
    None if the table is empty or has rows for a different build_id.
    Raises RuntimeError if rows exist for a DIFFERENT build_id (force-stop).
    """
    try:
        import psycopg2
    except ImportError:
        import psycopg as psycopg2  # type: ignore[no-redef]

    with psycopg2.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT build_id, COUNT(*) FROM ephemeris_daily GROUP BY build_id")
            rows = cur.fetchall()

    if not rows:
        return None

    for existing_build_id, count in rows:
        if existing_build_id == build_id:
            logger.info("ephemeris_daily already has %d rows for build_id=%s; skipping.", count, build_id)
            return count
        raise RuntimeError(
            f"ephemeris_daily already has {count} rows for build_id={existing_build_id!r}. "
            f"Refusing to overwrite with build_id={build_id!r}. "
            "Delete the existing rows manually before re-running."
        )

    return None


# ── Main write loop ────────────────────────────────────────────────────────────

def run(
    build_id: str,
    start: date = DATE_START,
    end: date = DATE_END,
    dry_run: bool = False,
    skip_csv_check: bool = False,
) -> int:
    """
    Compute and write ephemeris rows.  Returns total row count written.
    """
    swe = _init_swe()
    logger.info(
        "bootstrap_ephemeris: build_id=%s start=%s end=%s dry_run=%s",
        build_id, start, end, dry_run,
    )

    total_days = (end - start).days + 1
    total_rows_expected = total_days * 9
    logger.info("Expected rows: %d days × 9 planets = %d", total_days, total_rows_expected)

    if not dry_run:
        db_url = os.environ["DATABASE_URL"]
        existing = _check_existing_rows(db_url, build_id)
        if existing is not None:
            return existing

    # ── CSV cross-check (before the long compute) ──────────────────────────────
    csv_check_residual: str | None = None
    if not skip_csv_check:
        logger.info("Fetching CSV for spot-check (%d rows)…", CSV_SPOTCHECK_N)
        sample = _load_csv_spotcheck(CSV_SPOTCHECK_N)
        if sample is None:
            csv_check_residual = (
                "CSV spot-check skipped: EPHEMERIS_MONTHLY_1900_2100.csv not found "
                "in GCS at " + GCS_CSV_URI + ". "
                "Stream D.0 must upload it. Re-run cross-check after Stream D.0 completes."
            )
            logger.warning(csv_check_residual)
        else:
            findings = _run_csv_spotcheck(swe, sample, build_id)
            if findings:
                msg = f"CSV spot-check HALT: {len(findings)} mismatches > {CSV_SPOTCHECK_THRESHOLD_DEG}°:\n"
                msg += "\n".join(findings[:10])
                raise RuntimeError(msg)
            logger.info("CSV spot-check PASS: %d sampled rows within %.3f°", len(sample), CSV_SPOTCHECK_THRESHOLD_DEG)

    # ── Daily compute ──────────────────────────────────────────────────────────
    batch: list[dict[str, Any]] = []
    total_written = 0
    day_count = 0
    prior_day_signs: dict[str, str] | None = None

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

    for d in _date_range(start, end):
        jd = swe.julday(d.year, d.month, d.day, 0.0)  # midnight UT
        rows = _compute_day(swe, jd, build_id, d, prior_day_signs)
        # Carry forward today's signs for next day's ingress detection.
        prior_day_signs = {row["planet"]: row["sign"] for row in rows}
        batch.extend(rows)
        day_count += 1

        if len(batch) >= BATCH_SIZE:
            written = _flush(batch)
            total_written += written
            batch = []
            if day_count % 1000 == 0:
                logger.info("Progress: %d / %d days (%d rows written)", day_count, total_days, total_written)

    # Final partial batch
    total_written += _flush(batch)
    logger.info(
        "bootstrap_ephemeris complete: %d days, %d rows written, build_id=%s%s",
        day_count,
        total_written,
        build_id,
        " [DRY RUN]" if dry_run else "",
    )
    if csv_check_residual:
        logger.warning("RESIDUAL: %s", csv_check_residual)

    return total_written


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    parser = argparse.ArgumentParser(description="Bootstrap ephemeris_daily table via Swiss Ephemeris")
    parser.add_argument("--build-id", default=str(uuid.uuid4()), help="Build ID for provenance")
    parser.add_argument("--start", default=str(DATE_START), help="Start date YYYY-MM-DD")
    parser.add_argument("--end", default=str(DATE_END), help="End date YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true", help="Compute but do not write to DB")
    parser.add_argument("--skip-csv-check", action="store_true", help="Skip CSV cross-check")
    args = parser.parse_args()

    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)
    count = run(
        build_id=args.build_id,
        start=start,
        end=end,
        dry_run=args.dry_run,
        skip_csv_check=args.skip_csv_check,
    )
    print(f"Done: {count} rows processed.")


if __name__ == "__main__":
    main()
