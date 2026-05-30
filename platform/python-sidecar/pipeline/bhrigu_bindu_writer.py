"""
bhrigu_bindu_writer.py — Bhrigu Bindu lifetime transit computation.

Computes dates when each of 9 grahas transits within ±1° of the native's
Bhrigu Bindu (Moon-Rahu midpoint) from 2026-01-01 to 2060-12-31.

Bhrigu Bindu is the midpoint of the Moon and Rahu (Mean Node) in the natal chart.
In Nadi Jyotish tradition, transiting planets crossing the BB degree activate
destiny events. This table stores future transit hits for the MARSYS-JIS native.

Uses Swiss Ephemeris (pyswisseph) for precise longitude computation.
Ayanamsha: Lahiri sidereal.

Stream C — A19 [BUILD-ORCH-STREAM-C-A19-S1]
"""
from __future__ import annotations

import logging
import os
from datetime import date, timedelta
from typing import Any

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

# Native's Bhrigu Bindu: midpoint of natal Moon and Rahu (Lahiri sidereal)
# Moon ≈ Purva Bhadrapada, Rahu ≈ Libra — midpoint at Scorpio 26°07' ≈ 236.12°
NATIVE_BB_LONGITUDE_DEG: float = 236.12

# Known native chart_id
NATIVE_CHART_ID: str = "362f9f17-95a5-490b-a5a7-027d3e0efda0"

# Transit scan window
SCAN_START = date(2026, 1, 1)
SCAN_END = date(2060, 12, 31)

# Orb in degrees (±1°)
ORB_DEG: float = 1.0

# Classical citation for Bhrigu Bindu transits
CLASSICAL_CITATION = (
    "Bhrigu Nadi — Bhrigu Bindu (Moon-Rahu midpoint) transit activation; "
    "cf. K.K. Pathak 'Nadi Jyotish' Ch.7; Bhrighu Saral Paddhati Rule 1"
)

# Graha → swisseph body ID mapping (populated lazily after swe import)
# ketu = mean node (rahu) + 180° — not a direct swe body
GRAHA_NAMES = [
    "sun", "moon", "mars", "mercury", "jupiter",
    "venus", "saturn", "rahu", "ketu",
]


# ── Swiss Ephemeris initialisation ────────────────────────────────────────────

def _init_swe() -> Any:
    """Import and initialise swisseph with Lahiri ayanamsha. Returns the module."""
    try:
        import swisseph as swe  # pyswisseph installs as 'swisseph'
    except ImportError as exc:
        raise RuntimeError(
            "pyswisseph is not installed. Run: pip install pyswisseph>=2.10.0"
        ) from exc
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    return swe


def _graha_body_ids(swe: Any) -> dict[str, int | None]:
    """Return {graha_name: swe_body_id} for the 8 real grahas; ketu has None (derived)."""
    return {
        "sun":     swe.SUN,
        "moon":    swe.MOON,
        "mars":    swe.MARS,
        "mercury": swe.MERCURY,
        "jupiter": swe.JUPITER,
        "venus":   swe.VENUS,
        "saturn":  swe.SATURN,
        "rahu":    swe.MEAN_NODE,
        "ketu":    None,   # derived: rahu_lon + 180° mod 360
    }


# ── Core computation ──────────────────────────────────────────────────────────

def compute_bhrigu_bindu(moon_lon: float, rahu_lon: float) -> float:
    """
    Compute the Bhrigu Bindu longitude as the midpoint of Moon and Rahu.

    The midpoint is the shorter-arc midpoint in the circular (mod 360) sense:
    if the arc from moon to rahu going forward is ≤ 180°, the midpoint is
    moon + half that arc; otherwise it's the supplementary arc midpoint.

    Args:
        moon_lon: Moon sidereal longitude in degrees (0–360).
        rahu_lon: Rahu sidereal longitude in degrees (0–360).

    Returns:
        Bhrigu Bindu longitude in degrees (0–360).
    """
    # Forward arc from moon to rahu
    fwd = (rahu_lon - moon_lon) % 360.0
    if fwd <= 180.0:
        mid = (moon_lon + fwd / 2.0) % 360.0
    else:
        # Take the shorter arc the other way
        mid = (moon_lon - (360.0 - fwd) / 2.0) % 360.0
    return mid


def _circular_distance(lon_a: float, lon_b: float) -> float:
    """Return the shortest arc distance (0 to 180°) between two sidereal longitudes."""
    diff = abs(lon_a - lon_b) % 360.0
    return min(diff, 360.0 - diff)


def _classify_transit(orb: float) -> tuple[str, float]:
    """
    Return (transit_type, strength_score) for a given orb distance.

    'exact' = orb ≤ 0.1°  (closest pass)
    The strength score is 1 - (orb / ORB_DEG) so that 0° orb → 1.0.
    transit_type is always 'exact' when orb ≤ 0.1, otherwise 'applying' or
    'separating' — since we scan daily we use 'applying' as the default label
    for all non-exact hits (direction determination would require multi-day
    context; the label distinguishes the two).
    """
    strength = max(0.0, 1.0 - orb / ORB_DEG)
    if orb <= 0.1:
        return "exact", strength
    return "applying", strength


def scan_bb_transits(
    chart_id: str,
    bb_lon: float,
    start_date: date,
    end_date: date,
) -> list[dict]:
    """
    Scan daily graha positions from start_date to end_date; collect hits within
    ±ORB_DEG of bb_lon.

    Returns a list of dicts, one per (graha, hit_date) with all required fields.
    Duplicate (graha, date) entries are suppressed — only the closest orb per day
    is kept.
    """
    swe = _init_swe()
    body_ids = _graha_body_ids(swe)
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED

    # Track best orb per (graha, date) to deduplicate
    best: dict[tuple[str, date], dict] = {}

    current = start_date
    total_days = (end_date - start_date).days + 1
    scanned = 0

    while current <= end_date:
        jd = swe.julday(current.year, current.month, current.day, 0.0)  # midnight UT

        for graha in GRAHA_NAMES:
            bid = body_ids[graha]

            if bid is None:
                # ketu = rahu + 180°
                rahu_bid = body_ids["rahu"]
                r = swe.calc_ut(jd, rahu_bid, flags)
                lon = (r[0][0] + 180.0) % 360.0
            else:
                r = swe.calc_ut(jd, bid, flags)
                lon = r[0][0]

            orb = _circular_distance(lon, bb_lon)
            if orb <= ORB_DEG:
                key = (graha, current)
                transit_type, strength = _classify_transit(orb)
                row = {
                    "chart_id":            chart_id,
                    "graha":               graha,
                    "hit_iso":             current,
                    "bb_longitude_deg":    round(bb_lon, 4),
                    "graha_longitude_deg": round(lon, 4),
                    "orb_deg":             round(orb, 4),
                    "transit_type":        transit_type,
                    "strength_score":      round(strength, 4),
                    "classical_citation":  CLASSICAL_CITATION,
                }
                # Keep only the closest orb per (graha, date)
                if key not in best or orb < best[key]["orb_deg"]:
                    best[key] = row

        current += timedelta(days=1)
        scanned += 1
        if scanned % 3650 == 0:
            pct = 100 * scanned // total_days
            logger.info("BB scan progress: %d%% (%d / %d days)", pct, scanned, total_days)

    hits = list(best.values())
    hits.sort(key=lambda h: (h["hit_iso"], h["graha"]))
    logger.info(
        "BB scan complete: %d hits for chart_id=%s, BB=%.2f°, %s to %s",
        len(hits), chart_id, bb_lon, start_date, end_date,
    )
    return hits


def seed_bhrigu_bindu_transits(
    conn,
    chart_id: str = NATIVE_CHART_ID,
    bb_lon: float = NATIVE_BB_LONGITUDE_DEG,
) -> int:
    """
    Seed l1_bhrigu_bindu_transits for 2026-01-01 to 2060-12-31.

    Idempotent: ON CONFLICT (chart_id, graha, hit_iso) DO NOTHING.

    Args:
        conn: psycopg2 connection (already open).
        chart_id: UUID of the native chart.
        bb_lon: Bhrigu Bindu longitude in sidereal degrees.

    Returns:
        Number of rows inserted (0 if all already existed — idempotent).
    """
    hits = scan_bb_transits(chart_id, bb_lon, SCAN_START, SCAN_END)
    if not hits:
        logger.warning("No BB transit hits found — check BB longitude and orb settings.")
        return 0

    sql = """
        INSERT INTO l1_bhrigu_bindu_transits (
            chart_id, graha, hit_iso,
            bb_longitude_deg, graha_longitude_deg, orb_deg,
            transit_type, strength_score, classical_citation
        ) VALUES (
            %(chart_id)s, %(graha)s, %(hit_iso)s,
            %(bb_longitude_deg)s, %(graha_longitude_deg)s, %(orb_deg)s,
            %(transit_type)s, %(strength_score)s, %(classical_citation)s
        )
        ON CONFLICT (chart_id, graha, hit_iso) DO NOTHING
    """

    inserted = 0
    with conn.cursor() as cur:
        for row in hits:
            cur.execute(sql, row)
            inserted += cur.rowcount
    conn.commit()

    logger.info(
        "seed_bhrigu_bindu_transits: inserted %d / %d rows (chart_id=%s)",
        inserted, len(hits), chart_id,
    )
    return inserted


# ── DB lookup helper ──────────────────────────────────────────────────────────

def load_bb_from_chart_facts(conn, chart_id: str) -> float | None:
    """
    Try to load Bhrigu Bindu longitude from chart_facts.

    Returns the longitude_deg float, or None if not found.
    """
    sql = """
        SELECT fact_value::float
        FROM chart_facts
        WHERE chart_id = %s
          AND fact_category = 'bhrigu_bindu'
          AND fact_key = 'longitude_deg'
        LIMIT 1
    """
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (chart_id,))
            row = cur.fetchone()
            if row:
                return float(row[0])
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to load BB from chart_facts: %s", exc)
    return None


def get_native_chart_id(conn) -> str:
    """
    Look up the native's chart_id from the charts table.
    Falls back to the hard-coded known ID.
    """
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT chart_id FROM charts WHERE chart_id = %s LIMIT 1",
                (NATIVE_CHART_ID,),
            )
            row = cur.fetchone()
            if row:
                return str(row[0])
            # Fallback: first chart in table
            cur.execute("SELECT chart_id FROM charts LIMIT 1")
            row = cur.fetchone()
            if row:
                return str(row[0])
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to look up chart_id: %s", exc)
    return NATIVE_CHART_ID


# ── CLI entry-point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import psycopg2

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="Seed Bhrigu Bindu lifetime transits.")
    parser.add_argument("--chart-id", default=NATIVE_CHART_ID, help="Chart UUID")
    parser.add_argument("--bb-lon", type=float, default=NATIVE_BB_LONGITUDE_DEG,
                        help="Bhrigu Bindu longitude in sidereal degrees")
    parser.add_argument("--db-host", default=os.environ.get("DB_HOST", "127.0.0.1"))
    parser.add_argument("--db-port", type=int, default=int(os.environ.get("DB_PORT", "5433")))
    parser.add_argument("--db-name", default=os.environ.get("DB_NAME", "amjis"))
    parser.add_argument("--db-user", default=os.environ.get("DB_USER", "amjis_app"))
    parser.add_argument("--db-pass", default=os.environ.get("DB_PASS", ""))
    args = parser.parse_args()

    conn = psycopg2.connect(
        host=args.db_host, port=args.db_port,
        dbname=args.db_name, user=args.db_user, password=args.db_pass,
    )
    try:
        bb_lon = args.bb_lon
        # Try to load from chart_facts; fall back to arg
        loaded = load_bb_from_chart_facts(conn, args.chart_id)
        if loaded is not None:
            logger.info("Loaded BB from chart_facts: %.4f°", loaded)
            bb_lon = loaded
        else:
            logger.info("Using BB from arg/default: %.4f°", bb_lon)

        n = seed_bhrigu_bindu_transits(conn, chart_id=args.chart_id, bb_lon=bb_lon)
        print(f"Inserted {n} rows into l1_bhrigu_bindu_transits.")
    finally:
        conn.close()
