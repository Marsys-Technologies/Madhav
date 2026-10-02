"""
services/ka_graha_sancara/engine_pinned.py — the node-series-PINNED ephemeris-at-T read (NODE-SERIES step 1, P8/P9)
====================================================================================================================

SS N-68/N-69. `engine._read_from_bg_ephemeris` (PATH-A) reads one day of `ephemeris_daily` and builds `body_map[body]`
LAST-ROW-WINS. With a second (MEAN) Rahu/Ketu row set beside the TRUE one, Rahu/Ketu would be TRUE or MEAN by PHYSICAL ROW
ORDER and nothing would fail (the writer self-test only checks non-null). This module holds the pinned copy of
`_read_from_bg_ephemeris` and of `get_ephemeris` (which calls it); both are copied VERBATIM from `engine.py` by AST range,
with exactly these differences:

  * the PATH-A statement carries NODE_SERIES_PREDICATE (services/w2g/node_series.py, Pravaha's pinned module): the node bodies
    read the TRUE series, the series PATH-B computes (compute_transits.py / transit_search.py: swe.TRUE_NODE), so BOTH engine
    paths stay on the SAME node at step 1. MEAN only together with PATH-B in step 3 (one REVIEW to SS, with the list of rows
    that change);
  * two rows for one (node, date), or a day that has rows for other bodies but none for a node, raise NodeSeriesError. The
    raise sits OUTSIDE the `try` that turns every database error into None (None = "fall through to live compute"), so a
    refusal is never swallowed into a quiet fallback. A day with no row at all, a missing NON-node body and a database
    error keep the designed fallback to PATH-B (live Swiss, the same TRUE series);
  * `get_ephemeris` here calls the pinned `_read_from_bg_ephemeris` and reaches PATH-B through `engine._compute_live`.

Why a new module and not an edit of `engine.py`: that file is in the writer-digest closure of 43 writers (L1 `ga_*` 13, L2
`bo_*` 23, L3 7: asset_runner.py and service_probes.py import it), measured by regenerating the provenance inventory after a
one-line edit. The unpinned `engine._read_from_bg_ephemeris` / `engine.get_ephemeris` therefore stay BYTE-IDENTICAL as dead
copies (listed in `node_series_pin_baseline.json`; delete them the next time `engine.py` is edited for another reason). The
callers that matter re-point here: `brahmagyan/phala/muhurta.py` (P9, the gochara grading) and the `ka_graha_sancara` writer.
The probe in `pipeline/orchestrator/service_probes.py` reaches `engine.get_ephemeris` on the live path and is untouched.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from pathlib import Path  # noqa: F401  (kept for parity with engine.py; get_ephemeris does not use it)
from typing import Any

from services.ka_graha_sancara import engine as _engine
from services.ka_graha_sancara.engine import (
    ALL_GRAHAS,
    BG_EPHEMERIS_END,
    BG_EPHEMERIS_START,
    NAK_SIZE_DEG,
    NAKSHATRAS,
    SIGN_SIZE_DEG,
    SIGNS,
    SUPPORTED_AYANAMSHAS,
    EphemerisResult,
    GrahaState,
    _EphemerisCache,
)
from services.w2g.node_series import NODE_BODIES, NODE_SERIES_PREDICATE, NodeSeriesError, assert_one_row_per_date

logger = logging.getLogger(__name__)

__all__ = ["get_ephemeris", "_read_from_bg_ephemeris"]



def _read_from_bg_ephemeris(
    d: date,
    ayanamsha: str,
    db_conn: Any,
) -> dict[str, GrahaState] | None:
    """
    Read tropical longitudes from ephemeris_daily for the given date,
    apply ayanamsha derivation, return dict of GrahaState objects.

    Returns None if the table is unavailable or no rows found.
    """
    try:
        from brahmagyan.l0_ephemeris import derive_sidereal, _tropical_to_jd
    except ImportError as exc:
        logger.warning("brahmagyan.l0_ephemeris not available: %s", exc)
        return None

    try:
        jd = _tropical_to_jd(d)
    except RuntimeError:
        # pyswisseph not available for ayanamsha derivation even for stored rows
        return None

    # NIRMĀṆA L3-W3 finding M3 (§N.8) — defect 1 of 2.
    #
    # This block used to open a bare `db_conn.cursor()` and then index the rows POSITIONALLY
    # (`row[0]`…`row[3]`). The orchestrator's connection is created with
    # `row_factory=dict_row` (`pipeline/orchestrator/db.py:57`), so every row arrived as a dict
    # and `row[0]` raised `KeyError: 0` — which is literally what `asset_registry.selftest_detail`
    # recorded for this asset: "ephemeris computation failed: 0", i.e. `str(KeyError(0))`.
    #
    # The same trap is documented elsewhere in this repo from the other side:
    # `brahmagyan/phala/muhurta.py` opens a DELIBERATE tuple-row connection because its helper
    # indexes positionally and "dict_row would break it" — a previous author hit this and worked
    # around it rather than fixing it.
    #
    # Fixed by pinning the row factory AT THE CURSOR and reading by column name, so this function
    # no longer depends on the caller's connection default in either direction. That coupling was
    # the actual defect; positional indexing was only how it showed.
    try:
        import psycopg.rows

        with db_conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                f"""
                SELECT body, tropical_longitude, speed_dps, is_retrograde
                FROM ephemeris_daily
                WHERE date = %s AND ayanamsha_id = 'tropical'
                  AND {NODE_SERIES_PREDICATE}
                ORDER BY body
                """,
                (d,),
            )
            rows = cur.fetchall()
    except Exception as exc:
        logger.warning("bg_ephemeris read failed for %s: %s", d, exc)
        return None

    if not rows:
        logger.debug("bg_ephemeris: no rows for %s", d)
        return None

    # NODE-SERIES step 1 (P8): an ambiguous or holed node series is refused LOUDLY. This sits OUTSIDE the try above, which
    # turns every exception into None (and None means "fall through to live compute"): a refusal must not be swallowed
    # into a quiet fallback. Before this pin the loop below was last-row-wins, so Rahu/Ketu would have been TRUE or MEAN by
    # physical row order. A date with NO row at all keeps the designed PATH-A -> PATH-B fallback (same TRUE series).
    assert_one_row_per_date(
        [{"body": row["body"], "date": d} for row in rows],     # the statement is one date: key every row to it
        context="ka_graha_sancara.engine_pinned._read_from_bg_ephemeris",
    )
    _present = {row["body"] for row in rows}
    _absent_nodes = [n for n in NODE_BODIES if n not in _present]
    if _absent_nodes and (_present - set(NODE_BODIES)):
        raise NodeSeriesError(
            f"ka_graha_sancara.engine_pinned._read_from_bg_ephemeris: {d} has rows for other bodies but none for "
            f"{'/'.join(_absent_nodes)} under node_mode='true' — the node series has a hole; refusing to fall back "
            f"to another series or to a partial day"
        )

    # Build a body→row map
    body_map: dict[str, tuple[float, float, bool]] = {}
    for row in rows:
        body = row["body"]
        trop_lon = float(row["tropical_longitude"])
        speed = float(row["speed_dps"])
        is_retro = bool(row["is_retrograde"])
        body_map[body] = (trop_lon, speed, is_retro)

    grahas: dict[str, GrahaState] = {}

    for graha in ALL_GRAHAS:
        if graha not in body_map:
            logger.debug("bg_ephemeris missing body %s for %s", graha, d)
            return None  # incomplete — fall through to live compute

        trop_lon, speed_dps, is_retro_stored = body_map[graha]

        try:
            sid = derive_sidereal(trop_lon, jd, ayanamsha)
        except (ValueError, RuntimeError) as exc:
            logger.warning("derive_sidereal failed for %s/%s: %s", graha, ayanamsha, exc)
            return None

        sid_lon = sid["sidereal_longitude"]
        sign_idx = int(sid_lon // SIGN_SIZE_DEG)
        nak_idx = int(sid_lon // NAK_SIZE_DEG)

        # Retrograde: use stored flag for planets (Sun/Moon/Rahu/Ketu never retrograde)
        is_retro = is_retro_stored if graha not in ("Sun", "Moon", "Rahu", "Ketu") else False

        grahas[graha] = GrahaState(
            name=graha,
            sidereal_lon_deg=sid_lon,
            sign=SIGNS[sign_idx % 12],
            sign_idx=sign_idx % 12,
            nakshatra=NAKSHATRAS[nak_idx % 27],
            nakshatra_idx=nak_idx % 27,
            degrees_in_sign=sid_lon % SIGN_SIZE_DEG,
            degrees_in_nakshatra=sid_lon % NAK_SIZE_DEG,
            speed_dps=speed_dps,
            is_retrograde=is_retro,
            source="bg_ephemeris",
        )

    return grahas


def get_ephemeris(
    dt: datetime,
    ayanamsha: str = "lahiri",
    db_conn: Any = None,
    *,
    force_live: bool = False,
    _cache: _EphemerisCache | None = None,
) -> EphemerisResult:
    """
    Compute or retrieve ephemeris for all 9 grahas at datetime dt.

    Parameters
    ----------
    dt : datetime
        The instant of interest (timezone-aware preferred; naive treated as IST).
    ayanamsha : str
        Ayanamsha to use.  Default: 'lahiri'.
        Multi-ayanamsha (raman/kp/yukteshwar/surya_siddhanta) requires PATH-A
        (bg_ephemeris) — live path only supports lahiri.
    db_conn : psycopg connection | None
        If provided, PATH-A (bg_ephemeris read) is attempted first for dates
        within 1900-2150.  If None or PATH-A fails, PATH-B (live compute) is used.
    force_live : bool
        Skip PATH-A and always use PATH-B (swisseph live compute).
    _cache : _EphemerisCache | None
        Optional caller-supplied cache (used internally and in tests to verify
        single-compute behaviour).  If None, a fresh cache is created per call.

    Returns
    -------
    EphemerisResult with all 9 GrahaState objects.
    """
    if ayanamsha not in SUPPORTED_AYANAMSHAS:
        raise ValueError(
            f"Unknown ayanamsha '{ayanamsha}'. Supported: {sorted(SUPPORTED_AYANAMSHAS)}"
        )

    # Ensure dt is timezone-aware (assume IST if naive)
    if dt.tzinfo is None:
        from datetime import timezone as _tz
        import zoneinfo
        try:
            ist = zoneinfo.ZoneInfo("Asia/Kolkata")
            dt = dt.replace(tzinfo=ist)
        except Exception:
            # Fallback: offset-based IST
            from datetime import timedelta
            dt = dt.replace(tzinfo=timezone(timedelta(hours=5, minutes=30)))

    q_date = dt.date()

    # Use caller-supplied cache or fresh per-call cache
    cache = _cache if _cache is not None else _EphemerisCache()

    # Check cache
    cached = cache.get(q_date, ayanamsha)
    if cached is not None:
        logger.debug("ephemeris cache hit for (%s, %s)", q_date, ayanamsha)
        return EphemerisResult(
            query_dt=dt,
            ayanamsha=ayanamsha,
            source=cached["_source"],
            grahas=cached["grahas"],
        )

    # ── PATH-A: bg_ephemeris (cheap read) ──
    grahas: dict[str, GrahaState] | None = None
    source = "swisseph_live"

    if (
        not force_live
        and db_conn is not None
        and BG_EPHEMERIS_START <= q_date <= BG_EPHEMERIS_END
    ):
        logger.debug("ephemeris PATH-A: bg_ephemeris for %s/%s", q_date, ayanamsha)
        grahas = _read_from_bg_ephemeris(q_date, ayanamsha, db_conn)
        if grahas is not None:
            source = "bg_ephemeris"
            logger.debug("ephemeris PATH-A: success — %d grahas", len(grahas))

    # ── PATH-B: live swisseph ──
    if grahas is None:
        logger.debug("ephemeris PATH-B: live swisseph for %s/%s", q_date, ayanamsha)
        grahas = _engine._compute_live(dt, ayanamsha)
        source = "swisseph_live"

    # Store in cache
    cache.put(q_date, ayanamsha, {"grahas": grahas, "_source": source})

    return EphemerisResult(
        query_dt=dt,
        ayanamsha=ayanamsha,
        source=source,
        grahas=grahas,
    )
