"""
enrich_ephemeris_daily — backfill derived columns onto existing
ephemeris_daily rows without re-running Swiss Ephemeris.

Modes:
  Default: backfills the 6 dignity/combust/vargottama/ingress/yuddha/house columns.
           Idempotent: skips rows where dignity_d1 IS NOT NULL.

  --backfill-bhava-chalit: backfills the bhava_chalit_house column only.
           Idempotent: patches rows where bhava_chalit_house IS NULL.
           Pure-Python derivation against existing longitude_deg.
           ~5-10 min for 660K rows (no Swiss Ephemeris recompute).

Usage:
    python -m pipeline.enrich_ephemeris_daily [--dry-run] [--limit N]
        [--start YYYY-MM-DD] [--end YYYY-MM-DD]
    python -m pipeline.enrich_ephemeris_daily --backfill-bhava-chalit [--dry-run]
"""
from __future__ import annotations
import argparse
import logging
import os
from itertools import groupby
from typing import Any

import psycopg2
import psycopg2.extras

from .ephemeris_derivations import (
    compute_dignity,
    compute_combust,
    compute_vargottama,
    compute_whole_sign_house,
    compute_sign_ingress,
    compute_graha_yuddha,
    compute_bhava_chalit_house,
)

logger = logging.getLogger(__name__)

# Fetch all rows in range with LAG-windowed prior_sign for ingress detection.
# The WHERE clause skips already-enriched rows to make the script idempotent.
_SELECT_DAY_SQL = """
    SELECT date, planet, longitude_deg::float8 AS longitude_deg,
           sign, sign_degree::float8 AS sign_degree, is_retrograde,
           LAG(sign) OVER (PARTITION BY planet ORDER BY date) AS prior_sign
    FROM ephemeris_daily
    WHERE date >= %(start)s AND date <= %(end)s
      AND dignity_d1 IS NULL
    ORDER BY date ASC, planet ASC
"""

_UPDATE_SQL = """
    UPDATE ephemeris_daily SET
      dignity_d1         = %(dignity_d1)s,
      is_combust         = %(is_combust)s,
      combust_orb_deg    = %(combust_orb_deg)s,
      vargottama_today   = %(vargottama_today)s,
      sign_ingress_today = %(sign_ingress_today)s,
      whole_sign_house   = %(whole_sign_house)s,
      graha_yuddha_with  = %(graha_yuddha_with)s
    WHERE date = %(date)s AND planet = %(planet)s
"""


_UPDATE_BHAVA_SQL = """
    UPDATE ephemeris_daily
    SET bhava_chalit_house = %(bhava)s
    WHERE id = %(id)s
"""


def _flush_bhava_updates(conn: Any, updates: list[dict], dry_run: bool) -> int:
    if dry_run or not updates:
        return len(updates)
    with conn.cursor() as cur:
        psycopg2.extras.execute_batch(cur, _UPDATE_BHAVA_SQL, updates, page_size=500)
    conn.commit()
    return len(updates)


def backfill_bhava_chalit(db_url: str, batch_size: int = 5000, dry_run: bool = False) -> int:
    """Backfill bhava_chalit_house for all ephemeris_daily rows where it is NULL.

    Idempotent: only patches rows where bhava_chalit_house IS NULL.
    Pure-Python derivation — no Swiss Ephemeris recompute needed.
    """
    from .bootstrap_ephemeris import _init_swe, _compute_native_sripati_cusps

    swe = _init_swe()
    cusps = _compute_native_sripati_cusps(swe)
    logger.info("Sripati cusps for native (Aries lagna, Bhubaneswar): %s", cusps)

    conn = psycopg2.connect(db_url)
    conn.autocommit = False

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT id, longitude_deg
            FROM ephemeris_daily
            WHERE bhava_chalit_house IS NULL
            ORDER BY id
        """)
        rows = cur.fetchall()

    logger.info("Backfilling %d rows with bhava_chalit_house", len(rows))

    if dry_run:
        logger.info("DRY RUN — first 3 rows would be patched: %s", rows[:3])
        conn.close()
        return len(rows)

    total = 0
    updates: list[dict] = []
    for r in rows:
        bhava = compute_bhava_chalit_house(float(r["longitude_deg"]), cusps)
        updates.append({"id": r["id"], "bhava": bhava})
        if len(updates) >= batch_size:
            total += _flush_bhava_updates(conn, updates, dry_run=False)
            updates = []
    total += _flush_bhava_updates(conn, updates, dry_run=False)

    conn.close()
    logger.info("backfill_bhava_chalit complete: %d rows updated", total)
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill derived ephemeris columns.")
    parser.add_argument("--start", default="1900-01-01")
    parser.add_argument("--end",   default="2100-12-31")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None, help="Stop after N rows (test slice).")
    parser.add_argument(
        "--backfill-bhava-chalit",
        action="store_true",
        help="Backfill bhava_chalit_house column only (idempotent, patches NULL rows).",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    db_url = os.environ["DATABASE_URL"]

    if getattr(args, "backfill_bhava_chalit", False):
        count = backfill_bhava_chalit(db_url, dry_run=args.dry_run)
        print(f"Done: {count} rows processed.")
        return

    # Stream rows ordered by (date, planet) so we can build per-day groups in
    # one pass and use the windowed prior_sign for ingress detection.
    with psycopg2.connect(db_url) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(_SELECT_DAY_SQL, {"start": args.start, "end": args.end})
            rows = cur.fetchall()
            logger.info("Read %d unenriched ephemeris rows", len(rows))

    # Group by date so we can compute graha-yuddha + combust within each day.
    updates: list[dict] = []
    for d, planet_rows_iter in groupby(rows, key=lambda r: r["date"]):
        planet_rows = list(planet_rows_iter)
        positions = {r["planet"]: r["longitude_deg"] for r in planet_rows}
        sun_lon = positions.get("sun")
        if sun_lon is None:
            logger.warning("Day %s missing sun row; skipping derived calc", d)
            continue
        for r in planet_rows:
            dignity = compute_dignity(r["planet"], r["sign"], r["sign_degree"])
            is_comb, comb_orb = compute_combust(
                r["planet"], r["longitude_deg"], sun_lon, r["is_retrograde"]
            )
            vargottama = compute_vargottama(r["sign"], r["sign_degree"])
            ws_house = compute_whole_sign_house(r["sign"])
            ingress = compute_sign_ingress(r["sign"], r["prior_sign"])
            yuddha = compute_graha_yuddha(r["planet"], r["longitude_deg"], positions)

            updates.append({
                "date": r["date"], "planet": r["planet"],
                "dignity_d1": dignity,
                "is_combust": is_comb,
                "combust_orb_deg": comb_orb,
                "vargottama_today": vargottama,
                "sign_ingress_today": ingress,
                "whole_sign_house": ws_house,
                "graha_yuddha_with": yuddha,
            })
            if args.limit and len(updates) >= args.limit:
                break
        if args.limit and len(updates) >= args.limit:
            break

    logger.info("Computed %d row updates", len(updates))

    if args.dry_run:
        logger.info("DRY RUN — first 3 updates:")
        for u in updates[:3]:
            logger.info("  %s", u)
        return

    with psycopg2.connect(db_url) as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_batch(cur, _UPDATE_SQL, updates, page_size=500)
        conn.commit()
    logger.info("Wrote %d updates", len(updates))


if __name__ == "__main__":
    main()
