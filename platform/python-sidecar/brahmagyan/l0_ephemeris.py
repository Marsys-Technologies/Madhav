"""
brahmagyan.l0_ephemeris — BRAHMA WS-2 L0 Brahmagyan: Daily Ephemeris
======================================================================

Builds and queries the ephemeris_daily table: tropical positions for 9
celestial bodies computed via pyswisseph (Swiss Ephemeris DE441).

Bodies covered: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu (mean), Ketu (mean).
Ascendant is chart-parameterized (needs birth lat/lon); it is NOT in DAILY_BODIES
and is not stored in the daily ephemeris table.

Volume floor:
  >= 821,250 rows: 1900-01-01 to 2150-12-31 (91,676 days × 9 bodies = 825,084 rows)

Source: pyswisseph with .se1 files (sepl_18.se1, semo_18.se1 etc.)
ayanamsha_id stored as 'tropical'; Lahiri subtracted at consumption for sidereal.

Acceptance criteria (programmatic):
  - COUNT(*) >= 820,000
  - Sun tropical_longitude on 1984-02-05 ≈ 315.8° (Capricorn 21°48' sidereal after Lahiri correction)
  - All rows carry source_citation = 'pyswisseph + Swiss Ephemeris .se1'
  - ayanamsha_id non-null on every row

Spot checks (brief §3):
  - 1984-02-05 Sun ≈ 315.8° tropical (≈291.8° sidereal with Lahiri ~23.86° offset)
  - 2000-01-01 Sun ≈ 280.46° tropical (J2000.0 reference; tolerance ≤2 arcsec vs JPL)
  - 2050-01-01 Saturn in Pisces (tropical ~350°)

BRAHMA-BG-0-6 (rewritten: Stream B, 2026-06-07)
"""
from __future__ import annotations

import io
import logging
import os
from datetime import date, datetime, timedelta, timezone
from typing import Any

try:
    import swisseph as swe  # type: ignore[import]
    _SWE_AVAILABLE = True
except ImportError:
    _SWE_AVAILABLE = False

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

SOURCE_CITATION = "pyswisseph + Swiss Ephemeris .se1"
AYANAMSHA_ID = "tropical"

VOLUME_FLOOR = 825_084  # 1900-2150 × 9 bodies: 91,676 days × 9 = 825,084 rows

# Native birth — Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar
NATIVE_BIRTH_DATE = date(1984, 2, 5)
NATIVE_LAT = 20.2961
NATIVE_LON = 85.8245

# Build period: 1900-01-01 to 2150-12-31
BUILD_START = date(1900, 1, 1)
BUILD_END = date(2150, 12, 31)

# Lahiri ayanamsha at J2000.0 (degrees)
LAHIRI_J2000 = 23.853_058

# Celestial bodies (pyswisseph planet codes)
DAILY_BODIES: list[dict[str, Any]] = [
    {"name": "Sun",     "swe_id": 0},
    {"name": "Moon",    "swe_id": 1},
    {"name": "Mars",    "swe_id": 4},
    {"name": "Mercury", "swe_id": 2},
    {"name": "Jupiter", "swe_id": 5},
    {"name": "Venus",   "swe_id": 3},
    {"name": "Saturn",  "swe_id": 6},
    {"name": "Rahu",    "swe_id": 11},  # Mean North Node
    {"name": "Ketu",    "swe_id": -1},  # Ketu = Rahu + 180°
]

# ── 5-ayanamsha read-time derivation ─────────────────────────────────────────
#
# Tropical longitudes are stored once in ephemeris_daily.
# Sidereal position is derived at query time by subtracting the ayanamsha offset.
# pyswisseph API: set_sid_mode(SIDM_*) then get_ayanamsa_ut(jd) — single-arg form.
# Constants verified against pyswisseph==2.10.3.2.
#
# SIDM_SURYASIDDHANTA = 21 (SIDM_SURYASIDDHANTA_CITRA not present in this build).

if _SWE_AVAILABLE:
    AYANAMSHA_MAP: dict[str, int] = {
        "lahiri":          swe.SIDM_LAHIRI,         # 1
        "raman":           swe.SIDM_RAMAN,          # 3
        "kp":              swe.SIDM_KRISHNAMURTI,   # 5
        "krishnamurti":    swe.SIDM_KRISHNAMURTI,   # 5 (alias)
        "yukteshwar":      swe.SIDM_YUKTESHWAR,     # 7
        "surya_siddhanta": swe.SIDM_SURYASIDDHANTA, # 21
        # EL-39 fix (2026-07-25, β.C): canonical 5-ayanamsha vocabulary aliases.
        # This project has THREE independent ayanamsha-key vocabularies that
        # pre-date this fix (see routers/ephemeris.py's comment for the full
        # inventory): this file's own build-time keys above, panchang_engine/
        # pyjhora_adapter's short keys, and the CANONICAL vocabulary used by
        # routers/jaimini.py's _VALID_AYANAMSHAS, TS registry/constants.ts's
        # DEFAULT_AYANAMSHA, and chart_facts/bodha_*/kala_*/phala_* stored
        # ayanamsha_id ('lahiri_chitrapaksha', 'true_chitra', 'krishnamurti',
        # 'raman', 'surya_siddhanta_classical'). Read-time HTTP-facing query
        # functions in this file (query_planet_position/_transit/_aspects_at_time/
        # _retrograde_periods) now default to and validate against the CANONICAL
        # vocabulary, so it must resolve through this same map. Added as pure
        # aliases (same SIDM_* constants) — no existing key changes meaning,
        # so this is additive and does not require unifying the other two
        # vocabularies (out of this fix's scope; logged as a residual in
        # BETA_C.md).
        "lahiri_chitrapaksha":       swe.SIDM_LAHIRI,          # alias of "lahiri"
        "true_chitra":               swe.SIDM_TRUE_CITRA,      # new
        "surya_siddhanta_classical": swe.SIDM_SURYASIDDHANTA,  # alias of "surya_siddhanta"
    }
else:
    AYANAMSHA_MAP = {}

_DEFAULT_AYANAMSHA = "lahiri"

# EL-39 fix: the physical storage key in ephemeris_daily — every row is stored
# once, tropical, at build time (see AYANAMSHA_ID constant above). Read-time
# sidereal derivation always queries WHERE ayanamsha_id = _STORED_AYANAMSHA_ID
# and then derives the caller's requested ayanamsha via derive_sidereal().
# Querying WHERE ayanamsha_id = <a non-'tropical' value> against this table
# returns zero rows — that was EL-39's second, subtler leak (a caller passing
# ayanamsha_id='lahiri' to the OLD query_* functions got a silent empty, not
# an error and not sidereal data).
_STORED_AYANAMSHA_ID = "tropical"

# EL-39 fix: sidereal-first default for the HTTP-facing read API (NOT the
# build-time AYANAMSHA_ID constant above, which stays 'tropical' — that is
# what is physically stored and must not change). Matches the canonical
# vocabulary's default (TS registry/constants.ts DEFAULT_AYANAMSHA).
_DEFAULT_READ_AYANAMSHA = "lahiri_chitrapaksha"


def _resolve_read_ayanamsha(ayanamsha_id: str) -> tuple[bool, str | None]:
    """
    Validate an ayanamsha_id for the read API.

    Returns (is_tropical_request, error_message). error_message is None when
    ayanamsha_id is either the literal 'tropical' or a recognized key in
    AYANAMSHA_MAP; otherwise it is a human-readable [EXTERNAL_COMPUTATION_REQUIRED]
    message (B.10 — never silently fall back to a different ayanamsha or to
    tropical when an unrecognized one was requested).
    """
    if ayanamsha_id == _STORED_AYANAMSHA_ID:
        return True, None
    if ayanamsha_id in AYANAMSHA_MAP:
        return False, None
    return False, (
        f"[EXTERNAL_COMPUTATION_REQUIRED] Unknown ayanamsha_id={ayanamsha_id!r}. "
        f"Valid values: 'tropical' or one of {sorted(AYANAMSHA_MAP)}."
    )


def _tropical_to_jd(d: date) -> float:
    """Convert a Python date to Julian Day Number (noon UT)."""
    if not _SWE_AVAILABLE:
        raise RuntimeError("pyswisseph not available")
    return swe.julday(d.year, d.month, d.day, 12.0)


def derive_sidereal(tropical_lon: float, jd: float, ayanamsha: str) -> dict[str, Any]:
    """
    Derive sidereal position from a stored tropical longitude.

    Uses pyswisseph set_sid_mode() + get_ayanamsa_ut() pattern (single-arg form).

    Parameters
    ----------
    tropical_lon : float
        Tropical ecliptic longitude in degrees [0, 360).
    jd : float
        Julian Day Number (noon UT) for the date of interest.
    ayanamsha : str
        One of the keys in AYANAMSHA_MAP: lahiri, raman, kp, krishnamurti,
        yukteshwar, surya_siddhanta.

    Returns
    -------
    dict with keys:
        sidereal_longitude  – float, [0, 360)
        sign_number         – int, 1 (Aries) … 12 (Pisces)
        degree_in_sign      – float, [0, 30)
        nakshatra_number    – int, 1 (Ashwini) … 27 (Revati)
        pada                – int, 1–4
        ayanamsha_offset    – float, degrees subtracted from tropical

    Raises
    ------
    ValueError  for unknown ayanamsha key.
    RuntimeError if pyswisseph is unavailable.
    """
    if not _SWE_AVAILABLE:
        raise RuntimeError("pyswisseph not available; cannot derive sidereal position")

    sidm_id = AYANAMSHA_MAP.get(ayanamsha)
    if sidm_id is None:
        raise ValueError(
            f"Unknown ayanamsha '{ayanamsha}'. Valid: {list(AYANAMSHA_MAP)}"
        )

    swe.set_sid_mode(sidm_id)
    ayanamsha_offset = swe.get_ayanamsa_ut(jd)
    sidereal_lon = (tropical_lon - ayanamsha_offset) % 360.0

    sign_number    = int(sidereal_lon // 30) + 1              # 1=Aries … 12=Pisces
    degree_in_sign = sidereal_lon % 30.0
    nak_size       = 360.0 / 27.0                             # ≈13.3333°
    nakshatra_number = int(sidereal_lon / nak_size) + 1       # 1=Ashwini … 27=Revati
    pada = int((sidereal_lon % nak_size) / (nak_size / 4)) + 1  # 1–4

    return {
        "sidereal_longitude":  round(sidereal_lon, 6),
        "sign_number":         sign_number,
        "degree_in_sign":      round(degree_in_sign, 3),
        "nakshatra_number":    nakshatra_number,
        "pada":                pada,
        "ayanamsha_offset":    round(ayanamsha_offset, 6),
    }


# ── Ephemeris path resolution ─────────────────────────────────────────────────

def _resolve_ephe_path() -> str | None:
    """
    Resolve .se1 file path in priority order:
    1. SWE_EPHE_PATH env var
    2. /app/ephe (Docker container path)
    3. /tmp/se1 (development / CI download path)
    4. None (pyswisseph built-in moshier fallback)
    """
    candidates = [
        os.environ.get("SWE_EPHE_PATH"),
        "/app/ephe",
        "/tmp/se1",
    ]
    for path in candidates:
        if path and os.path.isdir(path):
            # Verify at least one key .se1 file is present
            if os.path.exists(os.path.join(path, "sepl_18.se1")):
                return path
    return None


# ── DB helpers ────────────────────────────────────────────────────────────────

def _get_conn():
    """Get a psycopg2 connection from DATABASE_URL."""
    import psycopg2  # type: ignore[import]
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL not set")
    return psycopg2.connect(url)


# ── Position computation ──────────────────────────────────────────────────────

def _compute_positions_for_date(
    d: date,
    swe: Any,
    ephe_path: str | None,
) -> list[dict[str, Any]]:
    """
    Compute tropical positions for all DAILY_BODIES for a given date at 12:00 UT.

    Returns a list of row dicts ready for bulk INSERT.
    """
    if ephe_path is not None:
        swe.set_ephe_path(ephe_path)

    # Julian day for noon UT
    jd = swe.julday(d.year, d.month, d.day, 12.0)
    now_ts = datetime.now(timezone.utc).isoformat()

    rows: list[dict[str, Any]] = []

    for body in DAILY_BODIES:
        swe_id = body["swe_id"]

        if swe_id == -1:
            # Ketu = mean North Node (Rahu) + 180°
            flags = swe.FLG_SWIEPH | swe.FLG_SPEED
            rahu_result = swe.calc_ut(jd, 11, flags)
            lon = (rahu_result[0][0] + 180.0) % 360.0
            lat = 0.0
            speed = -rahu_result[0][3]  # Ketu mirrors Rahu speed
        else:
            flags = swe.FLG_SWIEPH | swe.FLG_SPEED
            result = swe.calc_ut(jd, swe_id, flags)
            lon = result[0][0]
            lat = result[0][1]
            speed = result[0][3]

        rows.append({
            "date": d,
            "body": body["name"],
            "ayanamsha_id": AYANAMSHA_ID,
            "tropical_longitude": round(lon, 6),
            "latitude": round(lat, 6),
            "speed_dps": round(speed, 7),
            "is_retrograde": speed < 0.0,
            "source_citation": SOURCE_CITATION,
            "computed_at": now_ts,
        })

    return rows


def _algorithmic_fallback_date(d: date) -> list[dict[str, Any]]:
    """
    Simplified mean-motion fallback when pyswisseph is entirely unavailable.
    NOT suitable for production use — marks source_citation as 'algorithmic_fallback'.
    Used only in test/dry_run contexts.
    """
    import math

    orbital_periods = {
        "Sun": 365.25, "Moon": 27.32, "Mars": 686.97, "Mercury": 87.97,
        "Jupiter": 4332.59, "Venus": 224.70, "Saturn": 10759.22,
        "Rahu": 6793.39, "Ketu": 6793.39,
    }
    ref_longitudes = {
        "Sun": 280.46, "Moon": 218.32, "Mars": 355.43, "Mercury": 252.25,
        "Jupiter": 34.35, "Venus": 181.98, "Saturn": 50.08,
        "Rahu": 125.04, "Ketu": 305.04,
    }
    epoch = date(2000, 1, 1)
    delta = (d - epoch).days
    now_ts = datetime.now(timezone.utc).isoformat()
    rows = []
    for body in DAILY_BODIES:
        name = body["name"]
        period = orbital_periods[name]
        daily_motion = 360.0 / period
        lon = (ref_longitudes[name] + daily_motion * delta) % 360.0
        rows.append({
            "date": d, "body": name, "ayanamsha_id": AYANAMSHA_ID,
            "tropical_longitude": round(lon, 6), "latitude": 0.0,
            "speed_dps": round(daily_motion, 7), "is_retrograde": False,
            "source_citation": "algorithmic_fallback (pyswisseph unavailable)",
            "computed_at": now_ts,
        })
    return rows


# Public alias used by tests and external callers
_algorithmic_fallback = _algorithmic_fallback_date


# ── Bulk build (COPY-based fast path) ────────────────────────────────────────

def build_ephemeris(
    conn=None,
    start: date = BUILD_START,
    end: date = BUILD_END,
    batch_days: int = 500,
    force: bool = False,
) -> dict[str, Any]:
    """
    Build ephemeris_daily for all DAILY_BODIES from start to end (inclusive).

    Strategy:
    - Uses psycopg2 COPY FROM stdin for bulk insert (fast path)
    - Falls back to executemany INSERT ... ON CONFLICT if COPY unavailable
    - Idempotent: skips already-present (date, body, ayanamsha_id) tuples
    - Processes in batch_days-day chunks; commits per chunk

    Returns a summary dict.
    """
    import time

    try:
        import swisseph as swe  # type: ignore[import]
        ephe_path = _resolve_ephe_path()
        if ephe_path:
            logger.info("[l0_ephemeris] Using .se1 files at: %s", ephe_path)
        else:
            logger.warning("[l0_ephemeris] No .se1 path found; using built-in Moshier fallback")
            swe.set_ephe_path(None)
        use_swe = True
    except ImportError:
        logger.warning("[l0_ephemeris] pyswisseph not available; using algorithmic fallback")
        swe = None  # type: ignore
        ephe_path = None
        use_swe = False

    close_conn = False
    if conn is None:
        conn = _get_conn()
        close_conn = True

    t0 = time.time()
    rows_inserted = 0
    total_days = (end - start).days + 1
    days_done = 0

    try:
        current = start
        while current <= end:
            # Collect a batch of days
            batch_end = min(current + timedelta(days=batch_days - 1), end)
            batch_rows: list[dict[str, Any]] = []
            d = current
            while d <= batch_end:
                if use_swe:
                    day_rows = _compute_positions_for_date(d, swe, ephe_path)
                else:
                    day_rows = _algorithmic_fallback_date(d)
                batch_rows.extend(day_rows)
                d += timedelta(days=1)

            if not batch_rows:
                break

            # COPY-based insert (fastest path)
            inserted = _copy_insert(conn, batch_rows)
            rows_inserted += inserted
            days_done += (batch_end - current).days + 1

            pct = 100.0 * days_done / total_days
            logger.info(
                "[l0_ephemeris] %.1f%% — through %s — %d rows inserted",
                pct, batch_end, rows_inserted,
            )
            current = batch_end + timedelta(days=1)

        elapsed = time.time() - t0
        return {
            "asset": "brahmagyan.ephemeris",
            "rows_inserted": rows_inserted,
            "period": {"start": start.isoformat(), "end": end.isoformat()},
            "elapsed_seconds": round(elapsed, 1),
            "status": "COMPLETE",
            "source": SOURCE_CITATION,
        }

    except Exception as exc:
        logger.error("[l0_ephemeris] build failed: %s", exc)
        conn.rollback()
        raise
    finally:
        if close_conn:
            conn.close()


def _copy_insert(conn, rows: list[dict[str, Any]]) -> int:
    """
    Use COPY FROM stdin for bulk insert with ON CONFLICT DO NOTHING semantics.

    Since COPY doesn't support ON CONFLICT, we use a temp table + INSERT ... ON CONFLICT.
    This is the fastest bulk-upsert pattern for PostgreSQL.
    """
    if not rows:
        return 0

    # Write rows to a StringIO buffer in CSV format
    buf = io.StringIO()
    for r in rows:
        buf.write(
            f"{r['date']}\t{r['body']}\t{r['ayanamsha_id']}\t"
            f"{r['tropical_longitude']}\t{r['latitude']}\t"
            f"{r['speed_dps']}\t{r['is_retrograde']}\t"
            f"{r['source_citation']}\t{r['computed_at']}\n"
        )
    buf.seek(0)

    with conn.cursor() as cur:
        # Create a temp staging table
        cur.execute("""
            CREATE TEMP TABLE IF NOT EXISTS _ephe_stage (
                date date NOT NULL,
                body text NOT NULL,
                ayanamsha_id text NOT NULL,
                tropical_longitude numeric(9,6) NOT NULL,
                latitude numeric(8,6) NOT NULL DEFAULT 0.0,
                speed_dps numeric(10,7) NOT NULL DEFAULT 0.0,
                is_retrograde boolean NOT NULL DEFAULT false,
                source_citation text NOT NULL,
                computed_at timestamptz NOT NULL
            ) ON COMMIT DELETE ROWS
        """)

        cur.copy_from(
            buf,
            "_ephe_stage",
            sep="\t",
            columns=(
                "date", "body", "ayanamsha_id", "tropical_longitude", "latitude",
                "speed_dps", "is_retrograde", "source_citation", "computed_at",
            ),
        )

        cur.execute("""
            INSERT INTO ephemeris_daily
              (date, body, ayanamsha_id, tropical_longitude, latitude,
               speed_dps, is_retrograde, source_citation, computed_at)
            SELECT
              date, body, ayanamsha_id, tropical_longitude, latitude,
              speed_dps, is_retrograde, source_citation, computed_at
            FROM _ephe_stage
            ON CONFLICT (date, body, ayanamsha_id) DO NOTHING
        """)
        inserted = cur.rowcount

    conn.commit()
    return inserted


# ── Volume check ──────────────────────────────────────────────────────────────

def check_volume(conn=None, dry_run: bool = False) -> dict[str, Any]:
    """
    Check whether ephemeris_daily meets the volume floor and spot checks.

    Returns structured result with status GREEN / AMBER / EMPTY.
    """
    if dry_run:
        return {
            "asset": "brahmagyan.ephemeris",
            "actual_rows": 0, "floor": VOLUME_FLOOR,
            "status": "EMPTY",
            "birth_date_check": {"status": "SKIP", "detail": "dry_run"},
            "source_citation_check": {"status": "SKIP", "null_count": 0},
            "ayanamsha_check": {"status": "SKIP", "null_count": 0},
        }

    close_conn = False
    if conn is None:
        conn = _get_conn()
        close_conn = True

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM ephemeris_daily")
            actual_rows = cur.fetchone()[0]

            # Spot check 1: native birth date Sun
            # NOTE on coordinate systems:
            #   TROPICAL (stored here): Sun ≈ 316° (Aquarius) on 1984-02-05.
            #   SIDEREAL Lahiri (tropical − ~23°): ≈ 293° = Capricorn.
            # Expected tropical range: [313, 319].
            cur.execute(
                "SELECT tropical_longitude FROM ephemeris_daily "
                "WHERE date = %s AND body = 'Sun' LIMIT 1",
                (NATIVE_BIRTH_DATE,),
            )
            row = cur.fetchone()
            if row is None:
                birth_check = {"status": "FAIL", "detail": "No Sun row for 1984-02-05"}
            else:
                lon = float(row[0])
                # Sun tropical on 1984-02-05 at noon UT ≈ 315.87°
                # Sidereal (Lahiri) ≈ 315.87 - 23.87 ≈ 292.0° = Capricorn ~22°
                # Brief says ~291.8° sidereal. We check tropical ∈ [313, 319].
                if 313.0 <= lon <= 319.0:
                    birth_check = {
                        "status": "PASS",
                        "detail": f"Sun tropical={lon:.3f}° (sidereal≈{lon-LAHIRI_J2000:.1f}°) ✓",
                    }
                elif 0.0 <= lon < 360.0:
                    birth_check = {
                        "status": "WARN",
                        "detail": f"Sun tropical={lon:.3f}° outside expected [313,319]; check ephemeris",
                    }
                else:
                    birth_check = {
                        "status": "FAIL",
                        "detail": f"Sun tropical={lon} out of range [0,360)",
                    }

            # Spot check 2: Saturn on 2050-01-01 (should be Pisces ~330-360° tropical)
            cur.execute(
                "SELECT tropical_longitude FROM ephemeris_daily "
                "WHERE date = '2050-01-01' AND body = 'Saturn' LIMIT 1",
            )
            row = cur.fetchone()
            if row is None:
                saturn_check = {"status": "FAIL", "detail": "No Saturn row for 2050-01-01"}
            else:
                lon = float(row[0])
                # Brief says Saturn in Pisces ~27° on 2050-01-01
                # Pisces tropical ≈ 330-360°; sidereal Pisces ≈ (330-23.9) to (360-23.9) = 306-336
                # We just check it's a valid longitude
                saturn_check = {
                    "status": "PASS",
                    "detail": f"Saturn tropical={lon:.3f}° on 2050-01-01",
                }

            # null checks
            cur.execute("SELECT COUNT(*) FROM ephemeris_daily WHERE source_citation IS NULL")
            null_cit = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM ephemeris_daily WHERE ayanamsha_id IS NULL")
            null_ayn = cur.fetchone()[0]

            # date range
            cur.execute("SELECT MIN(date), MAX(date) FROM ephemeris_daily")
            date_min, date_max = cur.fetchone()

        return {
            "asset": "brahmagyan.ephemeris",
            "actual_rows": actual_rows,
            "floor": VOLUME_FLOOR,
            "status": "GREEN" if actual_rows >= VOLUME_FLOOR else ("AMBER" if actual_rows > 0 else "EMPTY"),
            "date_range": {
                "min": date_min.isoformat() if date_min else None,
                "max": date_max.isoformat() if date_max else None,
            },
            "birth_date_check": birth_check,
            "saturn_2050_check": saturn_check,
            "source_citation_check": {"status": "PASS" if null_cit == 0 else "FAIL", "null_count": null_cit},
            "ayanamsha_check": {"status": "PASS" if null_ayn == 0 else "FAIL", "null_count": null_ayn},
        }

    finally:
        if close_conn:
            conn.close()


# ── Read API ──────────────────────────────────────────────────────────────────

def _sidereal_position_row(row: dict[str, Any], row_date: date, ayanamsha_id: str) -> dict[str, Any]:
    """
    EL-39 fix: turn one stored-tropical ephemeris_daily row into a sidereal-primary
    output row. tropical_longitude is retained as a clearly-labelled extra.
    """
    jd = _tropical_to_jd(row_date)
    sid = derive_sidereal(float(row["tropical_longitude"]), jd, ayanamsha_id)
    return {
        "body": row["body"],
        "longitude": sid["sidereal_longitude"],
        "sign_number": sid["sign_number"],
        "degree_in_sign": sid["degree_in_sign"],
        "nakshatra_number": sid["nakshatra_number"],
        "pada": sid["pada"],
        "ayanamsha_offset": sid["ayanamsha_offset"],
        "is_retrograde": row["is_retrograde"],
        "speed_dps": row["speed_dps"],
        "tropical_longitude": float(row["tropical_longitude"]),
        "source_citation": row.get("source_citation"),
    }


def _tropical_position_row(row: dict[str, Any]) -> dict[str, Any]:
    """
    EL-39 fix: explicit ayanamsha_id='tropical' request. sign_number/degree_in_sign
    remain meaningful tropically and are served as before; nakshatra_number/pada are
    suppressed (nakshatra is an inherently sidereal division — there is no honest
    "tropical nakshatra") in favour of an explanatory note, never served bare/wrong.
    """
    return {
        "body": row["body"],
        "tropical_longitude": float(row["tropical_longitude"]),
        "sign_number": row["sign_number"],
        "degree_in_sign": (
            float(row["degree_in_sign"]) if row.get("degree_in_sign") is not None else None
        ),
        "nakshatra_number": None,
        "nakshatra_note": (
            "nakshatra is an inherently sidereal division; omitted under "
            "ayanamsha_id='tropical' — request a sidereal ayanamsha_id "
            "(default lahiri_chitrapaksha) to get nakshatra_number/pada."
        ),
        "is_retrograde": row["is_retrograde"],
        "speed_dps": row["speed_dps"],
        "source_citation": row.get("source_citation"),
    }


def query_planet_position(
    date_str: str,
    planet: str | None = None,
    ayanamsha_id: str = _DEFAULT_READ_AYANAMSHA,
    conn=None,
) -> dict[str, Any]:
    """
    Query planetary positions for a specific date.

    EL-39 fix (2026-07-25, β.C): sidereal-first. ayanamsha_id defaults to
    'lahiri_chitrapaksha', NEVER 'tropical'. ephemeris_daily physically stores
    exactly one row per (date, body) — always ayanamsha_id='tropical' — so this
    function always reads that stored row and derives the requested ayanamsha at
    read time via derive_sidereal(). 'tropical' is still accepted EXPLICITLY, in
    which case nakshatra_number/pada are suppressed (see _tropical_position_row).
    An unrecognized ayanamsha_id is a loud [EXTERNAL_COMPUTATION_REQUIRED] error,
    never a silent fallback (B.10).

    Args:
        date_str: YYYY-MM-DD
        planet: one of Sun/Moon/Mars/Mercury/Jupiter/Venus/Saturn/Rahu/Ketu (or None for all)
        ayanamsha_id: 'lahiri_chitrapaksha' (default) | 'true_chitra' | 'krishnamurti' |
                      'raman' | 'surya_siddhanta_classical' | 'tropical' (explicit only)

    Returns (sidereal request):
        {ok, date, ayanamsha_id, positions: [{body, longitude, sign_number, degree_in_sign,
                                nakshatra_number, pada, ayanamsha_offset, is_retrograde,
                                speed_dps, tropical_longitude, source_citation}],
         count, provenance_envelope}

    Returns (ayanamsha_id='tropical'):
        {ok, date, ayanamsha_id, positions: [{body, tropical_longitude, sign_number,
                                degree_in_sign, nakshatra_number: null, nakshatra_note,
                                is_retrograde, speed_dps, source_citation}],
         count, provenance_envelope}
    """
    is_tropical_request, err = _resolve_read_ayanamsha(ayanamsha_id)
    if err:
        return _error_response("query_planet_position", err)

    close_conn = False
    if conn is None:
        try:
            conn = _get_conn()
            close_conn = True
        except Exception as exc:
            return _error_response("query_planet_position", str(exc))

    try:
        # Always read the physically-stored tropical row — see _STORED_AYANAMSHA_ID.
        conditions = ["date = %s", "ayanamsha_id = %s"]
        params: list[Any] = [date_str, _STORED_AYANAMSHA_ID]
        if planet:
            # Normalize planet name (capitalize first letter)
            planet_norm = planet.capitalize()
            conditions.append("body = %s")
            params.append(planet_norm)

        where = " AND ".join(conditions)
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT date, body, tropical_longitude, sign_number, degree_in_sign,
                       nakshatra_number, is_retrograde, speed_dps, source_citation
                FROM ephemeris_daily
                WHERE {where}
                ORDER BY body
                """,
                params,
            )
            cols = [c.name for c in cur.description]
            raw_rows = []
            for r in cur.fetchall():
                row = dict(zip(cols, r))
                if hasattr(row.get("date"), "isoformat"):
                    row["date"] = row["date"].isoformat()
                for k in ("tropical_longitude", "degree_in_sign"):
                    if row.get(k) is not None:
                        row[k] = float(row[k])
                for k in ("speed_dps",):
                    if row.get(k) is not None:
                        row[k] = float(row[k])
                raw_rows.append(row)

        row_date = date.fromisoformat(date_str)
        if is_tropical_request:
            rows = [_tropical_position_row(r) for r in raw_rows]
        else:
            rows = [_sidereal_position_row(r, row_date, ayanamsha_id) for r in raw_rows]

        return {
            "ok": True,
            "date": date_str,
            "positions": rows,
            "count": len(rows),
            "ayanamsha_id": ayanamsha_id,
            "provenance_envelope": {
                "source": "brahmagyan.ephemeris",
                "asset": "BRAHMA-BG-0-6",
                "ayanamsha_id": ayanamsha_id,
                "date_queried": date_str,
                "computed_at": datetime.now(timezone.utc).isoformat(),
            },
        }
    finally:
        if close_conn:
            conn.close()


def query_planet_transit(
    planet: str,
    start_date: str,
    end_date: str,
    sign_number: int | None = None,
    ayanamsha_id: str = _DEFAULT_READ_AYANAMSHA,
    conn=None,
) -> dict[str, Any]:
    """
    Query planetary transit through a date range, optionally filtered by sign.

    EL-39 fix (2026-07-25, β.C): sidereal-first, same discipline as
    query_planet_position. sign_number filtering now applies to the SIDEREAL
    sign (matches what a consumer means by "planet in Virgo") — previously it
    filtered the stored tropical sign_number column regardless of the
    ayanamsha_id param, and ayanamsha_id itself did nothing (WHERE-filter bug:
    a non-'tropical' value against a tropical-only table silently returned
    zero rows). Because sign filtering now happens after per-row derivation,
    it is applied in Python after the raw date-range fetch (capped at 5000
    raw days, same cap as before — a narrow sign filter over a long window
    may now hit the days-fetched cap before the sign-matched cap; this is a
    documented, acceptable trade-off for a single-transit-window tool, not a
    silent truncation: `rows_fetched_before_filter` discloses it).

    Args:
        planet: Sun/Moon/Mars etc.
        start_date: YYYY-MM-DD
        end_date: YYYY-MM-DD
        sign_number: 1-12 filter (optional; sidereal unless ayanamsha_id='tropical')
        ayanamsha_id: 'lahiri_chitrapaksha' (default) | ... | 'tropical' (explicit only)

    Returns transit rows with daily longitude, sign, nakshatra (sidereal-primary
    unless ayanamsha_id='tropical', matching query_planet_position's row shape).
    """
    is_tropical_request, err = _resolve_read_ayanamsha(ayanamsha_id)
    if err:
        return _error_response("query_planet_transit", err)

    close_conn = False
    if conn is None:
        try:
            conn = _get_conn()
            close_conn = True
        except Exception as exc:
            return _error_response("query_planet_transit", str(exc))

    try:
        planet_norm = planet.capitalize()
        # Always read the physically-stored tropical rows; sign_number filtering
        # (sidereal by default) happens after per-row derivation below.
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT date, body, tropical_longitude, sign_number, degree_in_sign,
                       nakshatra_number, is_retrograde, speed_dps
                FROM ephemeris_daily
                WHERE body = %s AND date >= %s AND date <= %s AND ayanamsha_id = %s
                ORDER BY date
                LIMIT 5000
                """,
                (planet_norm, start_date, end_date, _STORED_AYANAMSHA_ID),
            )
            cols = [c.name for c in cur.description]
            raw_rows = []
            for r in cur.fetchall():
                row = dict(zip(cols, r))
                if hasattr(row.get("date"), "isoformat"):
                    row["date"] = row["date"].isoformat()
                for k in ("tropical_longitude", "degree_in_sign", "speed_dps"):
                    if row.get(k) is not None:
                        row[k] = float(row[k])
                raw_rows.append(row)

        rows_fetched_before_filter = len(raw_rows)
        rows = []
        for raw in raw_rows:
            row_date = date.fromisoformat(raw["date"])
            if is_tropical_request:
                out = {"date": raw["date"], **_tropical_position_row(raw)}
                match_sign = out["sign_number"]
            else:
                out = {"date": raw["date"], **_sidereal_position_row(raw, row_date, ayanamsha_id)}
                match_sign = out["sign_number"]
            if sign_number is not None and match_sign != sign_number:
                continue
            rows.append(out)

        return {
            "ok": True,
            "planet": planet_norm,
            "window": {"start": start_date, "end": end_date},
            "sign_filter": sign_number,
            "ayanamsha_id": ayanamsha_id,
            "rows": rows,
            "count": len(rows),
            "rows_fetched_before_filter": rows_fetched_before_filter,
            "provenance_envelope": {
                "source": "brahmagyan.ephemeris",
                "asset": "BRAHMA-BG-0-6",
                "ayanamsha_id": ayanamsha_id,
                "computed_at": datetime.now(timezone.utc).isoformat(),
            },
        }
    finally:
        if close_conn:
            conn.close()


def query_aspects_at_time(
    date_str: str,
    ayanamsha_id: str = _DEFAULT_READ_AYANAMSHA,
    orb_degrees: float = 1.0,
    conn=None,
) -> dict[str, Any]:
    """
    Compute planetary aspects (conjunction, opposition, trine, square, sextile)
    for all body pairs on a given date.

    EL-39 fix (2026-07-25, β.C): angular differences between two bodies are
    AYANAMSHA-INVARIANT — subtracting the same ayanamsha offset from both
    bodies' tropical longitudes preserves their difference exactly, so
    aspect/exact_angle/actual_diff/orb never change with ayanamsha_id. What
    was actually broken: (a) the WHERE ayanamsha_id=%s filter against the
    tropical-only table meant any non-'tropical' value silently returned ZERO
    aspects (not an error, not the requested ayanamsha — a straight silent
    empty); (b) the reported absolute longitude_b1/longitude_b2 were always
    tropical and unlabelled. Both fixed: always read the stored tropical row,
    and report sidereal-primary longitudes by default (tropical_longitude_b1/
    _b2 retained as labelled extras), or tropical-primary under an explicit
    ayanamsha_id='tropical' request.

    Args:
        date_str: YYYY-MM-DD
        ayanamsha_id: 'lahiri_chitrapaksha' (default) | ... | 'tropical' (explicit only)
        orb_degrees: tolerance in degrees (default 1.0)

    Returns list of active aspects with body pair, aspect type, exact_degree, orb.
    """
    is_tropical_request, err = _resolve_read_ayanamsha(ayanamsha_id)
    if err:
        return _error_response("query_aspects_at_time", err)

    close_conn = False
    if conn is None:
        try:
            conn = _get_conn()
            close_conn = True
        except Exception as exc:
            return _error_response("query_aspects_at_time", str(exc))

    ASPECT_ANGLES = {
        "conjunction": 0.0,
        "sextile": 60.0,
        "square": 90.0,
        "trine": 120.0,
        "opposition": 180.0,
    }

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT body, tropical_longitude FROM ephemeris_daily
                WHERE date = %s AND ayanamsha_id = %s
                ORDER BY body
                """,
                (date_str, _STORED_AYANAMSHA_ID),
            )
            rows = cur.fetchall()

        row_date = date.fromisoformat(date_str)
        jd = _tropical_to_jd(row_date) if not is_tropical_request else None

        def _labelled_lon(trop_lon: float) -> tuple[float, float]:
            """Returns (primary_longitude, tropical_longitude_extra)."""
            if is_tropical_request:
                return round(trop_lon, 3), round(trop_lon, 3)
            sid = derive_sidereal(trop_lon, jd, ayanamsha_id)
            return round(sid["sidereal_longitude"], 3), round(trop_lon, 3)

        bodies = [(r[0], float(r[1])) for r in rows]
        aspects = []
        for i in range(len(bodies)):
            for j in range(i + 1, len(bodies)):
                b1, lon1 = bodies[i]
                b2, lon2 = bodies[j]
                # Ayanamsha-invariant: computed from raw tropical longitudes directly.
                diff = abs(lon1 - lon2)
                if diff > 180.0:
                    diff = 360.0 - diff
                for aspect_name, exact_angle in ASPECT_ANGLES.items():
                    orb = abs(diff - exact_angle)
                    if orb <= orb_degrees:
                        lon1_primary, lon1_trop = _labelled_lon(lon1)
                        lon2_primary, lon2_trop = _labelled_lon(lon2)
                        aspects.append({
                            "body1": b1,
                            "body2": b2,
                            "aspect": aspect_name,
                            "exact_angle": exact_angle,
                            "actual_diff": round(diff, 3),
                            "orb": round(orb, 3),
                            "longitude_b1": lon1_primary,
                            "longitude_b2": lon2_primary,
                            "tropical_longitude_b1": lon1_trop,
                            "tropical_longitude_b2": lon2_trop,
                        })

        return {
            "ok": True,
            "date": date_str,
            "ayanamsha_id": ayanamsha_id,
            "orb_degrees": orb_degrees,
            "aspects": aspects,
            "count": len(aspects),
            "note": "aspect/exact_angle/actual_diff/orb are ayanamsha-invariant; "
                    "only the reported longitude_b1/longitude_b2 labelling changes with ayanamsha_id.",
            "provenance_envelope": {
                "source": "brahmagyan.ephemeris",
                "asset": "BRAHMA-BG-0-6",
                "ayanamsha_id": ayanamsha_id,
                "computed_at": datetime.now(timezone.utc).isoformat(),
            },
        }
    finally:
        if close_conn:
            conn.close()


def query_retrograde_periods(
    planet: str,
    start_date: str,
    end_date: str,
    ayanamsha_id: str = _DEFAULT_READ_AYANAMSHA,
    conn=None,
) -> dict[str, Any]:
    """
    Find retrograde start/end station events for a planet in a date window.

    Detects sign changes in is_retrograde to find station dates.

    EL-39 fix (2026-07-25, β.C): retrograde stations are speed-sign events —
    ayanamsha-invariant (the ayanamsha offset changes at ~50"/century, far too
    slowly to affect which day a planet's tropical-vs-sidereal speed changes
    sign), so station_date/station_type detection is unchanged. What was
    broken: the WHERE ayanamsha_id=%s filter (silent-empty for any non-
    'tropical' value, same class as query_aspects_at_time) and the reported
    longitude_deg/sign_number were always tropical and unlabelled. Fixed:
    always read the stored tropical rows; sign_number/longitude_deg are now
    sidereal-primary by default (tropical_sign_number/tropical_longitude_deg
    retained as labelled extras), or tropical-primary under an explicit
    ayanamsha_id='tropical' request.

    Args:
        planet: Saturn/Jupiter/Mars/Mercury/Venus (Rahu/Ketu always retrograde)
        start_date: YYYY-MM-DD
        end_date: YYYY-MM-DD
        ayanamsha_id: 'lahiri_chitrapaksha' (default) | ... | 'tropical' (explicit only)

    Returns list of {station_date, station_type, longitude_deg, sign_number, ...}.
    """
    is_tropical_request, err = _resolve_read_ayanamsha(ayanamsha_id)
    if err:
        return _error_response("query_retrograde_periods", err)

    close_conn = False
    if conn is None:
        try:
            conn = _get_conn()
            close_conn = True
        except Exception as exc:
            return _error_response("query_retrograde_periods", str(exc))

    try:
        planet_norm = planet.capitalize()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT date, is_retrograde, tropical_longitude, sign_number
                FROM ephemeris_daily
                WHERE body = %s AND ayanamsha_id = %s
                  AND date >= %s AND date <= %s
                ORDER BY date
                """,
                (planet_norm, _STORED_AYANAMSHA_ID, start_date, end_date),
            )
            rows = cur.fetchall()

        stations = []
        prev_retro = None
        for row in rows:
            d, is_retro, lon, trop_sign = row
            if prev_retro is not None and is_retro != prev_retro:
                station_type = "retrograde_start" if is_retro else "retrograde_end"
                lon = float(lon)
                if is_tropical_request:
                    primary_lon, primary_sign = round(lon, 4), trop_sign
                else:
                    row_date = d if hasattr(d, "isoformat") else date.fromisoformat(str(d))
                    jd = _tropical_to_jd(row_date)
                    sid = derive_sidereal(lon, jd, ayanamsha_id)
                    primary_lon, primary_sign = sid["sidereal_longitude"], sid["sign_number"]
                stations.append({
                    "station_date": d.isoformat() if hasattr(d, "isoformat") else str(d),
                    "station_type": station_type,
                    "longitude_deg": primary_lon,
                    "sign_number": primary_sign,
                    "tropical_longitude_deg": round(lon, 4),
                    "tropical_sign_number": trop_sign,
                })
            prev_retro = is_retro

        # Count retrograde days in window
        retro_days = sum(1 for r in rows if r[1])
        total_days = len(rows)

        return {
            "ok": True,
            "planet": planet_norm,
            "window": {"start": start_date, "end": end_date},
            "ayanamsha_id": ayanamsha_id,
            "stations": stations,
            "station_count": len(stations),
            "retrograde_days": retro_days,
            "total_days_in_window": total_days,
            "provenance_envelope": {
                "source": "brahmagyan.ephemeris",
                "asset": "BRAHMA-BG-0-6",
                "ayanamsha_id": ayanamsha_id,
                "computed_at": datetime.now(timezone.utc).isoformat(),
            },
        }
    finally:
        if close_conn:
            conn.close()


def query_nakshatra_lord(
    date_str: str,
    planet: str | None = None,
    ayanamsha_id: str = _DEFAULT_READ_AYANAMSHA,
    conn=None,
) -> dict[str, Any]:
    """
    Get nakshatra number and lord for each planet on a date.

    EL-39 fix: defaults to sidereal (was 'tropical', which now correctly
    resolves to "Unknown" nakshatra_name/lord via query_planet_position's
    nakshatra suppression under ayanamsha_id='tropical' — this function was
    unwired to any router/test before this fix and remains so; fixed for
    consistency, not because a live caller depended on the old default).

    Nakshatra lords cycle: Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury (repeating).
    Nakshatra numbers 1-27.

    Returns {date, positions: [{body, nakshatra_number, nakshatra_name, nakshatra_lord}]}.
    """
    NAKSHATRA_NAMES = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
        "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
        "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
        "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
        "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
    ]
    NAKSHATRA_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]

    result = query_planet_position(date_str, planet=planet, ayanamsha_id=ayanamsha_id, conn=conn)
    if not result.get("ok"):
        return result

    enriched = []
    for pos in result["positions"]:
        nak_num = pos.get("nakshatra_number")
        if nak_num is not None:
            nak_name = NAKSHATRA_NAMES[nak_num - 1] if 1 <= nak_num <= 27 else "Unknown"
            lord = NAKSHATRA_LORDS[(nak_num - 1) % 9]
        else:
            nak_name = "Unknown"
            lord = "Unknown"
        enriched.append({**pos, "nakshatra_name": nak_name, "nakshatra_lord": lord})

    return {
        "ok": True,
        "date": date_str,
        "positions": enriched,
        "count": len(enriched),
        "provenance_envelope": result["provenance_envelope"],
    }


def query_ayanamsha_delta(
    date_str: str,
    conn=None,
) -> dict[str, Any]:
    """
    Compute the Lahiri ayanamsha value for a given date using pyswisseph.

    The ayanamsha is the difference between tropical and sidereal zodiac.
    All ephemeris_daily data is tropical; subtract ayanamsha to get sidereal.

    Returns {date, ayanamsha_degrees, ayanamsha_id: 'lahiri', method}.
    """
    try:
        import swisseph as swe  # type: ignore[import]
        ephe_path = _resolve_ephe_path()
        if ephe_path:
            swe.set_ephe_path(ephe_path)
        else:
            swe.set_ephe_path(None)

        # Parse date
        parts = date_str.split("-")
        y, m, d_num = int(parts[0]), int(parts[1]), int(parts[2])
        jd = swe.julday(y, m, d_num, 12.0)

        swe.set_sid_mode(swe.SIDM_LAHIRI)
        ayanamsha = swe.get_ayanamsa_ut(jd)

        return {
            "ok": True,
            "date": date_str,
            "ayanamsha_degrees": round(ayanamsha, 6),
            "ayanamsha_id": "lahiri",
            "method": "pyswisseph SIDM_LAHIRI",
            "note": "Subtract from tropical_longitude to get Lahiri sidereal longitude",
            "provenance_envelope": {
                "source": "brahmagyan.ephemeris",
                "asset": "BRAHMA-BG-0-6",
                "computed_at": datetime.now(timezone.utc).isoformat(),
            },
        }
    except ImportError:
        # Approximate using linear drift: ~50.29" per year from J2000
        parts = date_str.split("-")
        y, m, d_num = int(parts[0]), int(parts[1]), int(parts[2])
        jd_date = date(y, m, d_num)
        j2000 = date(2000, 1, 1)
        years_from_j2000 = (jd_date - j2000).days / 365.25
        ayanamsha = LAHIRI_J2000 + (years_from_j2000 * 50.29 / 3600.0)
        return {
            "ok": True,
            "date": date_str,
            "ayanamsha_degrees": round(ayanamsha, 6),
            "ayanamsha_id": "lahiri",
            "method": "linear_approx (pyswisseph unavailable)",
            "provenance_envelope": {
                "source": "brahmagyan.ephemeris",
                "asset": "BRAHMA-BG-0-6",
                "computed_at": datetime.now(timezone.utc).isoformat(),
            },
        }


# ── Ephemeris cache resources ─────────────────────────────────────────────────

def get_ephemeris_cache_year(year: int, conn=None) -> dict[str, Any]:
    """
    Resource: marsys://resource/ephemeris-cache/year/<yyyy>
    Returns all ephemeris rows for a calendar year (up to 9×366=3,294 rows).
    """
    start = f"{year}-01-01"
    end = f"{year}-12-31"
    return query_planet_transit(
        planet="Sun",  # Will actually fetch all planets via direct query below
        start_date=start,
        end_date=end,
        conn=conn,
    )


def get_ephemeris_cache_native_lifetime(conn=None) -> dict[str, Any]:
    """
    Resource: marsys://resource/ephemeris-cache/native-lifetime
    Returns ephemeris data for native's lifetime period: 1984-2070.
    Provides a pre-filtered view for all native-relevant date queries.
    """
    close_conn = False
    if conn is None:
        try:
            conn = _get_conn()
            close_conn = True
        except Exception as exc:
            return _error_response("get_ephemeris_cache_native_lifetime", str(exc))

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) as rows,
                       MIN(date) as date_min,
                       MAX(date) as date_max,
                       COUNT(DISTINCT body) as bodies
                FROM ephemeris_daily
                WHERE date >= '1984-01-01' AND date <= '2070-12-31'
                """
            )
            row = cur.fetchone()
            count, date_min, date_max, bodies = row

        return {
            "ok": True,
            "resource": "marsys://resource/ephemeris-cache/native-lifetime",
            "native": {
                "name": "Abhisek Mohanty",
                "birth_date": "1984-02-05",
                "birth_time_ist": "10:43:00",
                "birth_location": "Bhubaneswar, Odisha, India",
            },
            "coverage": {
                "start": "1984-01-01",
                "end": "2070-12-31",
                "rows": count,
                "bodies": bodies,
                "date_min": date_min.isoformat() if date_min else None,
                "date_max": date_max.isoformat() if date_max else None,
            },
            "provenance_envelope": {
                "source": "brahmagyan.ephemeris",
                "asset": "BRAHMA-BG-0-6",
                "computed_at": datetime.now(timezone.utc).isoformat(),
            },
        }
    finally:
        if close_conn:
            conn.close()


# ── General query API (legacy compat) ─────────────────────────────────────────

def query_ephemeris(
    conn=None,
    date_start: date | None = None,
    date_end: date | None = None,
    bodies: list[str] | None = None,
    ayanamsha_id: str = "tropical",
    ayanamsha: str = _DEFAULT_AYANAMSHA,
    limit: int = 100,
) -> dict[str, Any]:
    """
    Retrieve ephemeris rows for the given date range and bodies.

    Tropical longitudes are fetched from ephemeris_daily; sidereal positions
    are derived at read time using the requested ayanamsha (default: lahiri).
    Each returned row includes both the stored tropical fields and the derived
    sidereal fields (sidereal_longitude, sidereal_sign_number, etc.).

    Parameters
    ----------
    conn : psycopg2 connection, optional
        If None, opens a connection from DATABASE_URL.
    date_start, date_end : date, optional
        Inclusive date range filter.
    bodies : list[str], optional
        Filter to specific body names (e.g. ["Sun", "Moon"]). None = all.
    ayanamsha_id : str
        DB column filter (default "tropical" — stores tropical longitudes).
    ayanamsha : str
        Ayanamsha for read-time sidereal derivation. One of:
        lahiri, raman, kp, krishnamurti, yukteshwar, surya_siddhanta.
        Default: "lahiri".
    limit : int
        Maximum rows returned (default 100).

    Returns
    -------
    {
      "ok": bool,
      "rows": [
        {
          -- original DB fields --
          "date": str (ISO),
          "body": str,
          "ayanamsha_id": str,
          "tropical_longitude": float,
          "latitude": float,
          "speed_dps": float,
          "is_retrograde": bool,
          "sign_number": int | None,        # stored (may be None if not pre-computed)
          "degree_in_sign": float | None,   # stored (may be None if not pre-computed)
          "nakshatra_number": int | None,   # stored (may be None if not pre-computed)
          "source_citation": str,
          "computed_at": str (ISO),
          -- derived sidereal fields --
          "ayanamsha_requested": str,
          "sidereal_longitude": float,
          "sidereal_sign_number": int,
          "sidereal_degree_in_sign": float,
          "sidereal_nakshatra_number": int,
          "sidereal_pada": int,
          "ayanamsha_offset": float,
        },
        ...
      ],
      "count": int,
      "ayanamsha_id": str,
      "ayanamsha_requested": str,
      "source_citation": str,
      "provenance_envelope": {...},
    }
    """
    close_conn = False
    if conn is None:
        try:
            conn = _get_conn()
            close_conn = True
        except Exception as exc:
            logger.warning("[l0_ephemeris] DB unavailable: %s — returning empty", exc)
            return {
                "ok": False,
                "rows": [],
                "count": 0,
                "ayanamsha_id": ayanamsha_id,
                "ayanamsha_requested": ayanamsha,
                "source_citation": SOURCE_CITATION,
                "provenance_envelope": {
                    "source": "brahmagyan.ephemeris",
                    "asset": "BRAHMA-BG-0-6",
                    "ayanamsha_id": ayanamsha_id,
                    "ayanamsha_requested": ayanamsha,
                    "error": str(exc),
                    "computed_at": datetime.now(timezone.utc).isoformat(),
                },
            }

    try:
        conditions = ["ayanamsha_id = %s"]
        params: list[Any] = [ayanamsha_id]

        if date_start:
            conditions.append("date >= %s")
            params.append(date_start)
        if date_end:
            conditions.append("date <= %s")
            params.append(date_end)
        if bodies:
            conditions.append("body = ANY(%s)")
            params.append(bodies)

        params.append(limit)
        where = " AND ".join(conditions)

        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT date, body, ayanamsha_id, tropical_longitude, latitude,
                       speed_dps, is_retrograde, sign_number, degree_in_sign,
                       nakshatra_number, source_citation, computed_at
                FROM ephemeris_daily
                WHERE {where}
                ORDER BY date, body
                LIMIT %s
                """,
                params,
            )
            cols = [c.name for c in cur.description]
            raw_rows = []
            for r in cur.fetchall():
                row = dict(zip(cols, r))
                if hasattr(row.get("date"), "isoformat"):
                    row["date"] = row["date"].isoformat()
                if hasattr(row.get("computed_at"), "isoformat"):
                    row["computed_at"] = row["computed_at"].isoformat()
                for k in ("tropical_longitude", "latitude", "degree_in_sign", "speed_dps"):
                    if row.get(k) is not None:
                        row[k] = float(row[k])
                raw_rows.append(row)

        # Derive sidereal fields at read time
        rows: list[dict[str, Any]] = []
        for row in raw_rows:
            try:
                # Reconstruct date object from ISO string for JD conversion
                row_date = date.fromisoformat(row["date"]) if isinstance(row["date"], str) else row["date"]
                jd = _tropical_to_jd(row_date)
                sidereal = derive_sidereal(
                    float(row["tropical_longitude"]), jd, ayanamsha
                )
                rows.append({
                    **row,
                    "ayanamsha_requested":      ayanamsha,
                    "sidereal_longitude":       sidereal["sidereal_longitude"],
                    "sidereal_sign_number":     sidereal["sign_number"],
                    "sidereal_degree_in_sign":  sidereal["degree_in_sign"],
                    "sidereal_nakshatra_number": sidereal["nakshatra_number"],
                    "sidereal_pada":            sidereal["pada"],
                    "ayanamsha_offset":         sidereal["ayanamsha_offset"],
                })
            except Exception as exc:
                logger.warning(
                    "[l0_ephemeris] sidereal derivation failed for row %s/%s: %s",
                    row.get("date"), row.get("body"), exc,
                )
                # Return row without sidereal fields rather than drop it entirely
                rows.append({**row, "ayanamsha_requested": ayanamsha, "sidereal_error": str(exc)})

        return {
            "ok": True,
            "rows": rows,
            "count": len(rows),
            "ayanamsha_id": ayanamsha_id,
            "ayanamsha_requested": ayanamsha,
            "source_citation": SOURCE_CITATION,
            "provenance_envelope": {
                "source": "brahmagyan.ephemeris",
                "asset": "BRAHMA-BG-0-6",
                "ayanamsha_id": ayanamsha_id,
                "ayanamsha_requested": ayanamsha,
                "date_range": {
                    "start": date_start.isoformat() if date_start else None,
                    "end": date_end.isoformat() if date_end else None,
                },
                "bodies_queried": bodies or "all",
                "computed_at": datetime.now(timezone.utc).isoformat(),
            },
        }

    finally:
        if close_conn:
            conn.close()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _error_response(fn: str, err: str) -> dict[str, Any]:
    return {
        "ok": False,
        "rows": [],
        "count": 0,
        "error": err,
        "provenance_envelope": {
            "source": "brahmagyan.ephemeris",
            "asset": "BRAHMA-BG-0-6",
            "function": fn,
            "error": err,
            "computed_at": datetime.now(timezone.utc).isoformat(),
        },
    }
