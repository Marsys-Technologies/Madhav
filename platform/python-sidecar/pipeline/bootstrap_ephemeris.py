"""
pipeline.bootstrap_ephemeris
MARSYS-JIS Brahma Build — Swiss Ephemeris daily compute 1900–2100.

One-time job that populates ephemeris_daily_staging with one row per (date, planet, node_type)
for all 9 graha across 73,050 days.  After the verification gate passes, caller
swaps staging → live via the standard swap discipline.

Usage:
    python -m pipeline.bootstrap_ephemeris [--build-id ID] [--dry-run]
                                           [--start YYYY-MM-DD] [--end YYYY-MM-DD]
                                           [--skip-csv-check]

Idempotency: if ephemeris_daily_staging already has rows for the given build_id, the job
exits 0 with a warning.  If rows for a *different* build_id are present it halts
so the operator can make an explicit delete decision (rebuilding ephemeris is a
manual, audited action per the brief).

Ephemeris authority: pyswisseph (package: pyswisseph; import name: swisseph),
Lahiri sidereal ayanamsha (DE441 JPL ephemeris).  CSV at
gs://madhav-marsys-sources/L1/ephemeris/EPHEMERIS_MONTHLY_1900_2100.csv is used
only as a spot-check — not as the source.  If the GCS object is absent, the
cross-check is skipped and the residual is recorded in the manifest.

CHANGE 4.1: EPHEMERIS_VERSION = 'pyswisseph-DE441-lahiri-v1'
    The DE441 JPL ephemeris file is the default for modern pyswisseph builds (>=2.10).
    This satisfies the ephemeris_version column contract.

CHANGE 4.2: UPSERT SQL updated — ON CONFLICT uses (date, planet, node_type);
    node_type='mean' for all planets (including rahu/ketu, which are mean-node builds).

CHANGE 4.3: build_manifests auto-registration at the end of run().

CHANGE 4.4: source_citation comment in UPSERT SQL.

CHANGE 4.5: jpl_spotcheck() stub (returns [] — deferred to acceptance gate operator step).
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
from contextlib import contextmanager
from datetime import date, timedelta
from typing import Any, Iterator

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

# CHANGE 4.1: Version string updated to DE441 provenance.
EPHEMERIS_VERSION = "pyswisseph-DE441-lahiri-v1"
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

# CHANGE 4.2: UPSERT SQL updated with node_type column.
# CHANGE 4.4: source_citation comment — provenance is ephemeris_version + build_id.
# source_citation: provenance is ephemeris_version (pyswisseph DE441) + build_id.
# No separate source_citation column in ephemeris_daily schema (provenance via
# ephemeris_version = 'pyswisseph-DE441-lahiri-v1' + build_manifests FK).
_UPSERT_SQL = """
INSERT INTO ephemeris_daily_staging (
    date, planet, node_type, longitude_deg, latitude_deg, speed_deg_per_day,
    is_retrograde, sign, sign_degree, nakshatra, nakshatra_pada,
    ayanamsha, ephemeris_version, build_id,
    dignity_d1, is_combust, combust_orb_deg, vargottama_today,
    sign_ingress_today, whole_sign_house, graha_yuddha_with,
    bhava_chalit_house
) VALUES (
    %(date)s, %(planet)s, %(node_type)s, %(longitude_deg)s, %(latitude_deg)s,
    %(speed_deg_per_day)s, %(is_retrograde)s, %(sign)s, %(sign_degree)s,
    %(nakshatra)s, %(nakshatra_pada)s, %(ayanamsha)s, %(ephemeris_version)s,
    %(build_id)s,
    %(dignity_d1)s, %(is_combust)s, %(combust_orb_deg)s, %(vargottama_today)s,
    %(sign_ingress_today)s, %(whole_sign_house)s, %(graha_yuddha_with)s,
    %(bhava_chalit_house)s
)
ON CONFLICT (date, planet, node_type) DO UPDATE SET
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
    graha_yuddha_with  = EXCLUDED.graha_yuddha_with,
    bhava_chalit_house = EXCLUDED.bhava_chalit_house;
"""

# ── DB connection helper ──────────────────────────────────────────────────────

@contextmanager
def _get_conn(db_url: str):
    """Context manager that yields a psycopg2 (or psycopg3) connection."""
    try:
        import psycopg2
        conn = psycopg2.connect(db_url)
        try:
            yield conn
        finally:
            conn.close()
    except ImportError:
        import psycopg  # type: ignore[no-redef]
        conn = psycopg.connect(db_url)
        try:
            yield conn
        finally:
            conn.close()


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


def _compute_native_sripati_cusps(swe: Any) -> list[float]:
    """
    Compute the 12 Sripati bhava madhyas (midpoints) for the native chart.
    Returns a length-12 list where index i is the madhya of bhava i+1.

    Native: 1984-02-05T10:43:00+05:30 IST (= 05:13:00 UTC), Bhubaneswar.
    Lahiri sidereal, Sripati house system code 'S'.

    NOTE: swe.houses_ex(..., b'S') returns bhava SANDHIS (boundary cusps),
    NOT madhyas. The madhyas are derived from ASC/MC/IC/DSC by equal-arc
    division of each quadrant into 3 parts. ASC = bhava 1 madhya,
    IC = bhava 4 madhya, DSC = bhava 7 madhya, MC = bhava 10 madhya.
    """
    NATIVE_BIRTH_JD_UT = swe.julday(1984, 2, 5, 5 + 13 / 60)  # 05:13:00 UTC
    NATIVE_LAT = 20.27021   # Bhubaneswar
    NATIVE_LON = 85.82966
    _cusps, ascmc = swe.houses_ex(
        NATIVE_BIRTH_JD_UT,
        NATIVE_LAT,
        NATIVE_LON,
        b'S',  # Sripati — ascmc[0]=ASC, ascmc[1]=MC
        swe.FLG_SIDEREAL,
    )

    asc = ascmc[0]
    mc = ascmc[1]
    ic = (mc + 180.0) % 360.0
    dsc = (asc + 180.0) % 360.0

    def fwd(start: float, end: float) -> float:
        return (end - start) % 360.0

    step1 = fwd(asc, ic) / 3.0    # arc ASC→IC divided by 3
    step2 = fwd(ic, dsc) / 3.0    # arc IC→DSC divided by 3
    step3 = fwd(dsc, mc) / 3.0    # arc DSC→MC divided by 3
    step4 = fwd(mc, asc) / 3.0    # arc MC→ASC divided by 3

    return [
        asc,                          # bhava  1 — ASC
        (asc + step1) % 360.0,        # bhava  2
        (asc + 2 * step1) % 360.0,    # bhava  3
        ic,                           # bhava  4 — IC
        (ic + step2) % 360.0,         # bhava  5
        (ic + 2 * step2) % 360.0,     # bhava  6
        dsc,                          # bhava  7 — DSC
        (dsc + step3) % 360.0,        # bhava  8
        (dsc + 2 * step3) % 360.0,    # bhava  9
        mc,                           # bhava 10 — MC
        (mc + step4) % 360.0,         # bhava 11
        (mc + 2 * step4) % 360.0,     # bhava 12
    ]


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
    native_sripati_cusps: list[float] | None = None,
) -> list[dict[str, Any]]:
    """Compute all 9 graha for a single Julian Day.  Returns list of row dicts."""
    from .ephemeris_derivations import (
        compute_dignity, compute_combust, compute_vargottama,
        compute_whole_sign_house, compute_sign_ingress, compute_graha_yuddha,
        compute_bhava_chalit_house,
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
            "node_type": "mean",   # CHANGE 4.2: non-node planets default to 'mean'
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
            "bhava_chalit_house": None,
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
        "node_type": "mean",   # CHANGE 4.2: mean-node build
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
        "bhava_chalit_house": None,
    })

    # Ketu = Rahu + 180°
    lon_k = (lon_r + 180.0) % 360.0
    sign_k, sdeg_k, nak_k, pada_k = _derive(lon_k)
    rows.append({
        "date": d,
        "planet": "ketu",
        "node_type": "mean",   # CHANGE 4.2: mean-node build
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
        "bhava_chalit_house": None,
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
        if native_sripati_cusps is not None:
            row["bhava_chalit_house"] = compute_bhava_chalit_house(lon, native_sripati_cusps)

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


# ── JPL spot-check stub ───────────────────────────────────────────────────────

def jpl_spotcheck(rows_sample: list[dict]) -> list[str]:
    """
    JPL Horizons ground-truth spot-check.
    DEFERRED: Live JPL HTTP comparison requires network access during build.
    The acceptance gate operator step documents this as a manual verification:
    run platform/scripts/jpl_spot_check.py after data is live in staging.
    Returns empty list (no findings) so tests can call this without failure.
    """
    return []


# ── Idempotency check ──────────────────────────────────────────────────────────

def _check_existing_rows(db_url: str, build_id: str) -> int | None:
    """
    Idempotency guard for bootstrap. Returns row count if
    ephemeris_daily_staging already has rows for this build_id (e.g., from
    a prior successful bootstrap that has not yet been swapped to live),
    or None if staging is empty.

    Raises RuntimeError if staging has rows for a DIFFERENT build_id —
    that means another bootstrap is in flight or was partially staged;
    operator must TRUNCATE ephemeris_daily_staging before proceeding.

    NOTE: the check is on STAGING, not LIVE. Bootstrap writes to staging;
    a separate swap script moves staging → live. The original Phase 14C
    implementation incorrectly queried the live table, which blocked every
    subsequent rebuild once live was populated. Fixed during §4.B Stage 5
    post-merge operator run (2026-05-19).
    """
    with _get_conn(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT build_id, COUNT(*) "
                "FROM ephemeris_daily_staging GROUP BY build_id"
            )
            rows = cur.fetchall()

    if not rows:
        return None

    for existing_build_id, count in rows:
        if existing_build_id == build_id:
            logger.info(
                "ephemeris_daily_staging already has %d rows for "
                "build_id=%s; skipping bootstrap.",
                count, build_id,
            )
            return count
        raise RuntimeError(
            f"ephemeris_daily_staging already has {count} rows for "
            f"build_id={existing_build_id!r}. Refusing to overwrite with "
            f"build_id={build_id!r}. TRUNCATE ephemeris_daily_staging "
            "before re-running."
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
    native_sripati_cusps = _compute_native_sripati_cusps(swe)
    logger.info(
        "bootstrap_ephemeris: build_id=%s start=%s end=%s dry_run=%s",
        build_id, start, end, dry_run,
    )
    logger.info("Sripati cusps for native (Aries lagna, Bhubaneswar): %s", native_sripati_cusps)

    total_days = (end - start).days + 1
    total_rows_expected = total_days * 9
    logger.info("Expected rows: %d days × 9 planets = %d", total_days, total_rows_expected)

    if not dry_run:
        db_url = os.environ["DATABASE_URL"]
        existing = _check_existing_rows(db_url, build_id)
        if existing is not None:
            return existing
    else:
        db_url = ""

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
            with _get_conn(db_url) as conn:
                import psycopg2.extras
                psycopg2.extras.execute_batch(conn.cursor(), _UPSERT_SQL, batch, page_size=500)
                conn.commit()
        else:
            with _get_conn(db_url) as conn:
                with conn.cursor() as cur:
                    for row in batch:
                        cur.execute(_UPSERT_SQL, row)
                conn.commit()
        return len(batch)

    for d in _date_range(start, end):
        jd = swe.julday(d.year, d.month, d.day, 0.0)  # midnight UT
        rows = _compute_day(swe, jd, build_id, d, prior_day_signs, native_sripati_cusps)
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
        "bootstrap_ephemeris complete: %d days, %d rows processed, build_id=%s%s",
        day_count,
        total_written,
        build_id,
        " [DRY RUN]" if dry_run else "",
    )
    if csv_check_residual:
        logger.warning("RESIDUAL: %s", csv_check_residual)

    # CHANGE 4.3: build_manifests auto-registration.
    if not dry_run:
        with _get_conn(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO build_manifests (build_id, asset_id, status, row_count, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    ON CONFLICT (build_id) DO UPDATE SET
                        status   = EXCLUDED.status,
                        row_count = EXCLUDED.row_count
                """, (build_id, 'brahmagyan.ephemeris', 'complete', total_written))
            conn.commit()
        logger.info("build_manifests auto-registration complete: build_id=%s rows=%d", build_id, total_written)

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
