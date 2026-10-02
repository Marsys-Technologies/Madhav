"""
brahmagyan.l0_ephemeris_queries — the node-series-PINNED read API over `ephemeris_daily`
===========================================================================================

NODE-SERIES step 1 (SS decision N-68/N-69, design option B: DESIGN_L0_MEAN_NODE_SERIES_v1_0.md
sections 6 and 10). `ephemeris_daily` stores the TRUE node for Rahu/Ketu today (`node_mode = 'true'`;
the seven other bodies carry `node_mode` NULL). L0 is about to gain a second, MEAN, row set beside it.
Every reader must say WHICH series it reads, or the day the second set exists it silently reads both
(duplicate dated rows, a LIMIT consumed twice as fast, Rahu-vs-Rahu "conjunctions", doubled retrograde
days).

This module holds the pinned copies of the seven node-unsafe readers that live in
`brahmagyan/l0_ephemeris.py` (S1-S7 of REVIEW_OURS_READERS_STEP0_v1_0.md):

    query_planet_position      S1   (HTTP /planet_position)
    query_planet_transit       S2   (HTTP /planet_transit)
    query_aspects_at_time      S3   (HTTP /aspects)
    query_retrograde_periods   S4   (HTTP /retrograde_periods)
    get_ephemeris_cache_native_lifetime   S5
    query_ephemeris            S6
    check_volume               S7

Why a new module and not an edit of `l0_ephemeris.py`: that file is in the writer-digest closure of 48
writers (L0 5, ga_* 13, bo_* 23, ka_* 7); one byte changed there moves all 48 digests. The old functions
therefore stay in `l0_ephemeris.py` BYTE-IDENTICAL as dead, unpinned copies (listed under
`node_series_pin_baseline.json`; delete them the next time that file is edited for another reason).
`ephemeris_routes.py` (the only production caller of S1-S4) now imports from here.

BEHAVIOUR-NEUTRAL. Every function body below is copied verbatim from `l0_ephemeris.py` (an AST-range copy,
then a fixed list of exact-once edits); the ONLY differences are:

  * the SQL carries `NODE_SERIES_PREDICATE` (services/w2g/node_series.py, Pravaha's pinned module):
        (body NOT IN ('Rahu', 'Ketu') OR node_mode = 'true')
    NULL-safe: a bare `node_mode = 'true'` would silently drop the seven non-node bodies, whose
    node_mode is NULL. While the table holds only TRUE node rows this predicate is a no-op, so every
    read returns exactly what the unpinned read returns today (proved by the golden-equivalence tests);
  * `assert_one_row_per_date` runs on the fetched rows (it cannot fire under the pin while the table's
    key holds; it is the loud second line, never a merge);
  * `query_ephemeris` orders by `date, body, node_mode` (total order; node_mode is constant under the pin);
  * names of private helpers resolve through this module (`_get_conn` stays patchable via `l0_ephemeris`).

Zero-row behaviour (a deliberate split, stated per reader in the PR):
  * the served list-style readers above keep today's behaviour on an empty result (an out-of-range date
    or an unknown body is an honest `count: 0`, not an error) and never return a duplicate;
  * readers that REQUIRE the node rows (spline / engine / kota) call `require_node_rows` below, which
    raises `NodeSeriesError` on 0 rows (and, through `assert_one_row_per_date`, on 2).

Served rows do NOT yet carry a `node_mode` discriminator: adding a key changes served output and the
step-1 ruling is behaviour-neutral. Under the pin a node row can only be the TRUE one, so the label is
redundant until step 3 offers a choice; it is a tool-text wave 2 item.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Any, Iterable

from brahmagyan import l0_ephemeris as _l0
from brahmagyan.l0_ephemeris import (
    _DEFAULT_AYANAMSHA,
    _DEFAULT_READ_AYANAMSHA,
    _STORED_AYANAMSHA_ID,
    LAHIRI_J2000,
    NATIVE_BIRTH_DATE,
    SOURCE_CITATION,
    VOLUME_FLOOR,
    _error_response,
    _resolve_read_ayanamsha,
    _sidereal_position_row,
    _tropical_position_row,
    _tropical_to_jd,
    derive_sidereal,
)
from services.w2g.node_series import (  # Pravaha's pinned module: reused, never copied
    NODE_BODIES,
    NODE_SERIES_PREDICATE,
    SERIES_NODE_MODE,
    NodeSeriesError,
    assert_one_row_per_date,
)

logger = logging.getLogger(__name__)

__all__ = [
    "NODE_BODIES",
    "NODE_SERIES_PREDICATE",
    "SERIES_NODE_MODE",
    "NodeSeriesError",
    "assert_one_row_per_date",
    "require_node_rows",
    "check_volume",
    "get_ephemeris_cache_native_lifetime",
    "query_aspects_at_time",
    "query_ephemeris",
    "query_planet_position",
    "query_planet_transit",
    "query_retrograde_periods",
]


def _get_conn():
    """Resolved through `l0_ephemeris` at call time, so a patch of `l0_ephemeris._get_conn` still applies."""
    return _l0._get_conn()


def _body_date(row: Any) -> tuple[str, Any]:
    try:
        return str(row["body"]), row["date"]
    except (TypeError, KeyError, IndexError):
        return str(row[0]), row[1]


def require_node_rows(
    rows: Iterable[Any],
    *,
    context: str,
    bodies: Iterable[str] = NODE_BODIES,
    dates: Iterable[Any] | None = None,
) -> None:
    """LOUD refusal for readers that REQUIRE the node series: raise `NodeSeriesError` on 0 or 2 rows.

    * 2 rows for one (body, date) under the pin -> `assert_one_row_per_date` (Pravaha's check, reused).
    * 0 rows: every body in `bodies` must appear at least once in `rows`; and, when `dates` is given,
      every (body, date) in bodies x dates must be present (a spline, an engine day or a Kota window
      cannot be built over a hole, and a silent gap is how a MEAN row would later be substituted).

    `rows` are mappings or sequences exposing body and date as `row["body"]`/`row["date"]` or as the
    first two positions. Non-node rows in `rows` are ignored; `bodies` is normally the node bodies a
    caller asked for (`NODE_BODIES` by default).
    """
    materialised = list(rows)
    assert_one_row_per_date(materialised, context=context)
    wanted = [str(b) for b in bodies]
    present: set[tuple[str, Any]] = set()
    present_bodies: set[str] = set()
    for row in materialised:
        body, day = _body_date(row)
        present_bodies.add(body)
        present.add((body, day))
    for body in wanted:
        if body not in present_bodies:
            raise NodeSeriesError(
                f"{context}: no row for {body} under node_mode='{SERIES_NODE_MODE}' — the node series is "
                f"absent; refusing to substitute another series or an empty one"
            )
    if dates is not None:
        for day in dates:
            for body in wanted:
                if (body, day) not in present:
                    raise NodeSeriesError(
                        f"{context}: no row for ({body}, {day}) under node_mode='{SERIES_NODE_MODE}' — "
                        f"the node series has a hole; refusing to interpolate or substitute"
                    )


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
            cur.execute(f"SELECT COUNT(*) FROM ephemeris_daily WHERE {NODE_SERIES_PREDICATE}")
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
            cur.execute(f"SELECT COUNT(*) FROM ephemeris_daily WHERE source_citation IS NULL AND {NODE_SERIES_PREDICATE}")
            null_cit = cur.fetchone()[0]
            cur.execute(f"SELECT COUNT(*) FROM ephemeris_daily WHERE ayanamsha_id IS NULL AND {NODE_SERIES_PREDICATE}")
            null_ayn = cur.fetchone()[0]

            # date range
            cur.execute(f"SELECT MIN(date), MAX(date) FROM ephemeris_daily WHERE {NODE_SERIES_PREDICATE}")
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
                WHERE {where} AND {NODE_SERIES_PREDICATE}
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
        assert_one_row_per_date(raw_rows, context="query_planet_position")

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
                f"""
                SELECT date, body, tropical_longitude, sign_number, degree_in_sign,
                       nakshatra_number, is_retrograde, speed_dps
                FROM ephemeris_daily
                WHERE body = %s AND date >= %s AND date <= %s AND ayanamsha_id = %s
                  AND {NODE_SERIES_PREDICATE}
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
        assert_one_row_per_date(raw_rows, context="query_planet_transit")

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
                f"""
                SELECT body, tropical_longitude FROM ephemeris_daily
                WHERE date = %s AND ayanamsha_id = %s AND {NODE_SERIES_PREDICATE}
                ORDER BY body
                """,
                (date_str, _STORED_AYANAMSHA_ID),
            )
            rows = cur.fetchall()
        assert_one_row_per_date(
            [{"body": r[0], "date": date_str} for r in rows], context="query_aspects_at_time"
        )

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
                f"""
                SELECT date, is_retrograde, tropical_longitude, sign_number
                FROM ephemeris_daily
                WHERE body = %s AND ayanamsha_id = %s
                  AND date >= %s AND date <= %s
                  AND {NODE_SERIES_PREDICATE}
                ORDER BY date
                """,
                (planet_norm, _STORED_AYANAMSHA_ID, start_date, end_date),
            )
            rows = cur.fetchall()
        assert_one_row_per_date(
            [{"body": planet_norm, "date": r[0]} for r in rows], context="query_retrograde_periods"
        )

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
                f"""
                SELECT COUNT(*) as rows,
                       MIN(date) as date_min,
                       MAX(date) as date_max,
                       COUNT(DISTINCT body) as bodies
                FROM ephemeris_daily
                WHERE date >= '1984-01-01' AND date <= '2070-12-31'
                  AND {NODE_SERIES_PREDICATE}
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
                WHERE {where} AND {NODE_SERIES_PREDICATE}
                ORDER BY date, body, node_mode
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
        assert_one_row_per_date(raw_rows, context="query_ephemeris")

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
