"""
brahmagyan.ephemeris_routes — FastAPI router for L0 ephemeris HTTP endpoints.

Exposes the brahmagyan.l0_ephemeris query functions as REST GET endpoints,
callable by the Next.js platform via PYTHON_SIDECAR_URL.

Routes registered under prefix /brahmagyan/ephemeris in main.py:
  GET /brahmagyan/ephemeris/planet_position  — query_planet_position
  GET /brahmagyan/ephemeris/planet_transit   — query_planet_transit
  GET /brahmagyan/ephemeris/aspects          — query_aspects_at_time
  GET /brahmagyan/ephemeris/retrograde_periods — query_retrograde_periods
  GET /brahmagyan/ephemeris/all_bodies_range   — all bodies for a date window (used by cache_year)
  GET /brahmagyan/ephemeris/native_lifetime_meta — native lifetime coverage stats

L0FR Stream B — authored 2026-06-07
"""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from brahmagyan.l0_ephemeris import (
    query_planet_position,
    query_planet_transit,
    query_aspects_at_time,
    query_retrograde_periods,
    # EL-39 fix (2026-07-25, β.C) — reused here so /all_bodies_range (backs the
    # ref_ephemeris_year_get MCP tool via ephemeris_cache_year.ts) gets the same
    # sidereal-first fix as the other 4 routes, instead of the raw ad-hoc SQL
    # this route previously inlined (which had the identical WHERE
    # ayanamsha_id=%s-against-a-tropical-only-table leak).
    _DEFAULT_READ_AYANAMSHA,
    _STORED_AYANAMSHA_ID,
    _resolve_read_ayanamsha,
    _sidereal_position_row,
    _tropical_position_row,
)
from datetime import date as _DateType

router = APIRouter()


# ── 1. planet_position ────────────────────────────────────────────────────────

@router.get("/planet_position")
def get_planet_position(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    planet: Optional[str] = Query(None, description="Optional planet name (Sun, Moon, Mars, etc.)"),
    ayanamsha_id: str = Query(
        _DEFAULT_READ_AYANAMSHA,
        description=(
            "Ayanamsha for sidereal derivation (default 'lahiri_chitrapaksha' — SIDEREAL-FIRST, "
            "never tropical by default). One of lahiri_chitrapaksha|true_chitra|krishnamurti|"
            "raman|surya_siddhanta_classical, or 'tropical' to request tropical coordinates "
            "explicitly (nakshatra_number/pada are suppressed under 'tropical' — nakshatra is "
            "an inherently sidereal division)."
        ),
    ),
):
    """
    Query planetary positions for a specific date.

    EL-39 fix (2026-07-25, β.C): sidereal-first. Returns all 9 bodies (or a single
    body if planet= is specified) with sidereal longitude/sign/degree/nakshatra/pada
    as the primary fields; tropical_longitude is retained as a clearly-labelled
    extra. Request ayanamsha_id='tropical' explicitly for tropical coordinates.
    """
    try:
        result = query_planet_position(date_str=date, planet=planet, ayanamsha_id=ayanamsha_id)
        if not result.get("ok"):
            raise HTTPException(status_code=500, detail=result.get("error", "query failed"))
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── 2. planet_transit ─────────────────────────────────────────────────────────

@router.get("/planet_transit")
def get_planet_transit(
    planet: str = Query(..., description="Planet name (Sun, Moon, Mars, etc.)"),
    start_date: str = Query(..., description="Start date YYYY-MM-DD"),
    end_date: str = Query(..., description="End date YYYY-MM-DD"),
    sign_number: Optional[int] = Query(
        None, ge=1, le=12,
        description="Optional sign filter 1-12 — sidereal by default (see ayanamsha_id), "
                    "tropical only when ayanamsha_id='tropical'.",
    ),
    ayanamsha_id: str = Query(
        _DEFAULT_READ_AYANAMSHA,
        description="Ayanamsha for sidereal derivation (default 'lahiri_chitrapaksha'). "
                    "'tropical' requests tropical coordinates explicitly.",
    ),
):
    """
    Query a planet's daily transit series across a date window.

    EL-39 fix (2026-07-25, β.C): sign_number now filters the SIDEREAL sign by
    default (matches what "planet in Virgo" means to a consumer), and rows
    carry sidereal-primary longitude/sign/degree/nakshatra/pada. Returns up to
    5,000 raw days fetched before the sign filter is applied (see
    rows_fetched_before_filter in the response).
    """
    try:
        result = query_planet_transit(
            planet=planet,
            start_date=start_date,
            end_date=end_date,
            sign_number=sign_number,
            ayanamsha_id=ayanamsha_id,
        )
        if not result.get("ok"):
            raise HTTPException(status_code=500, detail=result.get("error", "query failed"))
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── 3. aspects ────────────────────────────────────────────────────────────────

@router.get("/aspects")
def get_aspects(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    orb_degrees: float = Query(1.0, ge=0.1, le=10.0, description="Orb tolerance in degrees"),
    ayanamsha_id: str = Query(
        _DEFAULT_READ_AYANAMSHA,
        description="Ayanamsha for the reported longitude_b1/longitude_b2 labelling (default "
                    "'lahiri_chitrapaksha'). Aspect/exact_angle/orb are ayanamsha-invariant.",
    ),
):
    """
    Compute active planetary aspects for all body pairs on a specific date.
    Returns conjunction/sextile/square/trine/opposition aspects within orb.

    EL-39 fix (2026-07-25, β.C): previously any ayanamsha_id other than
    'tropical' silently returned zero aspects (WHERE-filter bug against a
    tropical-only table). Aspect geometry is ayanamsha-invariant; what changes
    with ayanamsha_id is only the labelling of the reported absolute
    longitude_b1/longitude_b2 (sidereal-primary by default).
    """
    try:
        result = query_aspects_at_time(
            date_str=date,
            ayanamsha_id=ayanamsha_id,
            orb_degrees=orb_degrees,
        )
        if not result.get("ok"):
            raise HTTPException(status_code=500, detail=result.get("error", "query failed"))
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── 4. retrograde_periods ─────────────────────────────────────────────────────

@router.get("/retrograde_periods")
def get_retrograde_periods(
    planet: str = Query(..., description="Planet: Mercury, Venus, Mars, Jupiter, Saturn"),
    start_date: str = Query(..., description="Start date YYYY-MM-DD"),
    end_date: str = Query(..., description="End date YYYY-MM-DD"),
    ayanamsha_id: str = Query(
        _DEFAULT_READ_AYANAMSHA,
        description="Ayanamsha for the reported station longitude/sign labelling (default "
                    "'lahiri_chitrapaksha'). Station dates themselves are ayanamsha-invariant.",
    ),
):
    """
    Find retrograde station events for a planet in a date window.
    Returns station dates (retrograde_start / retrograde_end) with longitude and sign.

    EL-39 fix (2026-07-25, β.C): previously any ayanamsha_id other than
    'tropical' silently returned zero stations (same WHERE-filter bug as
    /aspects). Station detection is ayanamsha-invariant; the reported
    longitude_deg/sign_number are now sidereal-primary by default
    (tropical_longitude_deg/tropical_sign_number retained as labelled extras).
    """
    try:
        result = query_retrograde_periods(
            planet=planet,
            start_date=start_date,
            end_date=end_date,
            ayanamsha_id=ayanamsha_id,
        )
        if not result.get("ok"):
            raise HTTPException(status_code=500, detail=result.get("error", "query failed"))
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── 5. all_bodies_range (used by ephemeris_cache_year) ───────────────────────

@router.get("/all_bodies_range")
def get_all_bodies_range(
    start_date: str = Query(..., description="Start date YYYY-MM-DD"),
    end_date: str = Query(..., description="End date YYYY-MM-DD"),
    count_only: bool = Query(False, description="If true, return only count stats (no rows)"),
    ayanamsha_id: str = Query(
        _DEFAULT_READ_AYANAMSHA,
        description="Ayanamsha for sidereal derivation (default 'lahiri_chitrapaksha'). "
                    "'tropical' requests tropical coordinates explicitly.",
    ),
):
    """
    Fetch all 9 bodies for a date window — up to 3,285 rows per year.
    Used by ephemeris_cache_year resource (backs the ref_ephemeris_year_get MCP tool).

    EL-39 fix (2026-07-25, β.C): this route previously inlined its own ad-hoc SQL
    (bypassing brahmagyan.l0_ephemeris entirely) with the identical WHERE
    ayanamsha_id=%s-against-a-tropical-only-table leak as the other 4 routes —
    any non-'tropical' ayanamsha_id silently returned zero rows, and the
    default served a tropical-derived nakshatra_number unlabelled. Now reuses
    the same sidereal-derivation helpers as /planet_position for row shape
    parity across every ephemeris-backed route. Row COUNT is unaffected by
    ayanamsha_id (exactly one stored row per (date, body) regardless of which
    ayanamsha is requested for derivation) — count_only always counts the
    physically-stored tropical rows.
    """
    import os
    from datetime import datetime, timezone

    is_tropical_request, err = _resolve_read_ayanamsha(ayanamsha_id)
    if err:
        raise HTTPException(status_code=422, detail=err)

    try:
        import psycopg2
        url = os.environ.get("DATABASE_URL", "")
        if not url:
            raise HTTPException(status_code=503, detail="DATABASE_URL not configured")

        if count_only:
            # Fast count path — row count is ayanamsha-invariant (see docstring).
            conn = psycopg2.connect(url)
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT COUNT(*), MIN(date), MAX(date) FROM ephemeris_daily "
                        "WHERE date >= %s AND date <= %s AND ayanamsha_id = %s",
                        (start_date, end_date, _STORED_AYANAMSHA_ID),
                    )
                    row = cur.fetchone()
                    count, date_min, date_max = row[0], row[1], row[2]
            finally:
                conn.close()

            return {
                "ok": True,
                "count": count,
                "window": {"start": start_date, "end": end_date},
                "date_range": {
                    "min": date_min.isoformat() if date_min else None,
                    "max": date_max.isoformat() if date_max else None,
                },
                "ayanamsha_id": ayanamsha_id,
                "computed_at": datetime.now(timezone.utc).isoformat(),
            }

        # Full data path (cap at 10,000 raw rows fetched, same cap as before)
        conn = psycopg2.connect(url)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT date, body, tropical_longitude, sign_number, degree_in_sign,
                           nakshatra_number, is_retrograde, speed_dps, source_citation
                    FROM ephemeris_daily
                    WHERE date >= %s AND date <= %s AND ayanamsha_id = %s
                    ORDER BY date, body
                    LIMIT 10000
                    """,
                    (start_date, end_date, _STORED_AYANAMSHA_ID),
                )
                cols = [c.name for c in cur.description]
                raw_rows = []
                for r in cur.fetchall():
                    row_d = dict(zip(cols, r))
                    if hasattr(row_d.get("date"), "isoformat"):
                        row_d["date"] = row_d["date"].isoformat()
                    for k in ("tropical_longitude", "degree_in_sign", "speed_dps"):
                        if row_d.get(k) is not None:
                            row_d[k] = float(row_d[k])
                    raw_rows.append(row_d)
        finally:
            conn.close()

        rows = []
        for raw in raw_rows:
            row_date = _DateType.fromisoformat(raw["date"])
            if is_tropical_request:
                out = {"date": raw["date"], **_tropical_position_row(raw)}
            else:
                out = {"date": raw["date"], **_sidereal_position_row(raw, row_date, ayanamsha_id)}
            rows.append(out)

        return {
            "ok": True,
            "window": {"start": start_date, "end": end_date},
            "rows": rows,
            "count": len(rows),
            "ayanamsha_id": ayanamsha_id,
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── 6. native_lifetime_meta ───────────────────────────────────────────────────

NATIVE_LIFETIME_START = "1984-01-01"
NATIVE_LIFETIME_END = "2070-12-31"

@router.get("/native_lifetime_meta")
def get_native_lifetime_meta(
    start_date: str = Query(NATIVE_LIFETIME_START),
    end_date: str = Query(NATIVE_LIFETIME_END),
    count_only: bool = Query(False),
):
    """
    Ephemeris coverage statistics for the native's lifetime (1984-2070).
    Native: Abhisek Mohanty, born 1984-02-05 10:43 IST, Bhubaneswar, Odisha, India.
    Returns row count, date range, body count, and native birth chart context.

    NOT part of the EL-39 fix scope (not one of the 4 routes + /all_bodies_range
    named for audit) — noted as a found-but-parked residual in BETA_C.md rather
    than fixed here: `sun_sidereal_approx` uses a fixed linear-approximation
    ayanamsha constant (23.853058, J2000 epoch value) instead of derive_sidereal's
    proper per-date swisseph computation, and this route's own lat/lon constants
    (20.2735/85.8334) are a THIRD "Bhubaneswar" coordinate pair alongside
    l0_ephemeris.py's NATIVE_LAT/NATIVE_LON (20.2961/85.8245) and
    panchang_daily_reader.py's BHUBANESWAR_LAT/LON (20.27/85.84) — a pre-existing
    inconsistency this fix does not attempt to unify. Both fields are already
    honestly labelled ("_approx") — low severity, PARKED-HONEST.
    """
    import os
    from datetime import datetime, timezone

    try:
        import psycopg2
        url = os.environ.get("DATABASE_URL", "")
        if not url:
            raise HTTPException(status_code=503, detail="DATABASE_URL not configured")
        conn = psycopg2.connect(url)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*), MIN(date), MAX(date),
                           COUNT(DISTINCT body), COUNT(DISTINCT date)
                    FROM ephemeris_daily
                    WHERE date >= %s AND date <= %s AND ayanamsha_id = 'tropical'
                    """,
                    (start_date, end_date),
                )
                row = cur.fetchone()
                total_rows = row[0]
                date_min = row[1]
                date_max = row[2]
                body_count = row[3]
                day_count = row[4]

                # Native birth date Sun spot check
                cur.execute(
                    "SELECT tropical_longitude FROM ephemeris_daily "
                    "WHERE date = '1984-02-05' AND body = 'Sun' LIMIT 1"
                )
                sun_row = cur.fetchone()
                sun_lon = float(sun_row[0]) if sun_row else None
        finally:
            conn.close()

        return {
            "ok": True,
            "resource": "marsys://resource/ephemeris-cache/native-lifetime",
            "native": {
                "name": "Abhisek Mohanty",
                "birth_date": "1984-02-05",
                "birth_time_ist": "10:43:00",
                "birth_location": "Bhubaneswar, Odisha, India",
                "lat": 20.2735,
                "lon": 85.8334,
                "sun_tropical_1984_02_05": sun_lon,
                "sun_sidereal_approx": round(sun_lon - 23.853058, 3) if sun_lon else None,
                "sun_sign_sidereal": "Capricorn ~22°" if sun_lon and 289 <= (sun_lon - 23.853058) <= 295 else "check",
            },
            "coverage": {
                "requested_start": start_date,
                "requested_end": end_date,
                "actual_min": date_min.isoformat() if date_min else None,
                "actual_max": date_max.isoformat() if date_max else None,
                "total_rows": total_rows,
                "day_count": day_count,
                "body_count": body_count,
                "expected_rows": 157266,
                "coverage_pct": round(100.0 * total_rows / 157266, 1) if total_rows else 0,
            },
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
