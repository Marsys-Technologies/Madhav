"""
enrich_ephemeris_daily — backfill the 6 derived columns onto existing
ephemeris_daily rows without re-running Swiss Ephemeris.

Idempotent: skips rows where dignity_d1 IS NOT NULL (already enriched).

Usage:
    python -m pipeline.enrich_ephemeris_daily [--dry-run] [--limit N]
        [--start YYYY-MM-DD] [--end YYYY-MM-DD]
"""
from __future__ import annotations
import argparse
import logging
import os
from itertools import groupby

import psycopg2
import psycopg2.extras

from .ephemeris_derivations import (
    compute_dignity,
    compute_combust,
    compute_vargottama,
    compute_whole_sign_house,
    compute_sign_ingress,
    compute_graha_yuddha,
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill derived ephemeris columns.")
    parser.add_argument("--start", default="1900-01-01")
    parser.add_argument("--end",   default="2100-12-31")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None, help="Stop after N rows (test slice).")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    db_url = os.environ["DATABASE_URL"]

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
