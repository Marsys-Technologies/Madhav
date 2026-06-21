#!/usr/bin/env python3
"""
Full L3 Kāla build runner (BUG-3 fix): runs ALL artifact writers in dependency order
against prod DB (Cloud SQL Auth Proxy at 127.0.0.1:5433).

Dependency order:
  1. ka_yojaka          — activation predicates (reads L2 bo_laksana)
  2. ka_sangam          — convergence engine (CF.L3.6 dasha prior wired)
  3. ka_kalasutra       — bounded activation artifact
  4. ka_vighnakara      — obstruction detector
  5. ka_kala_darshana   — display-ready temporal view
  6. ka_jivana_parva    — life-arc biographical chapter
  7. ka_bhavishya_lekha — probabilistic forward projections

Services (ka_graha_sancara, ka_dasha_kala, ka_gochara, ka_muhurta_seva) are
registered but have no run() writer — they are serve-time query engines.

Usage:
    python run_l3_full_prod.py [--dry-run] [--from ka_sangam]
"""
import os, sys, uuid, logging, argparse
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger("l3_full_runner")
sys.path.insert(0, os.path.dirname(__file__))

import psycopg2
from pipeline.orchestrator.writers import ContextSpec, _REGISTRY

# Import all writers to trigger @register
import pipeline.orchestrator.writers.ka_yojaka        # noqa: F401
import pipeline.orchestrator.writers.ka_sangam        # noqa: F401
import pipeline.orchestrator.writers.ka_kalasutra     # noqa: F401
import pipeline.orchestrator.writers.ka_vighnakara    # noqa: F401
import pipeline.orchestrator.writers.ka_kala_darshana # noqa: F401
import pipeline.orchestrator.writers.ka_jivana_parva  # noqa: F401
import pipeline.orchestrator.writers.ka_bhavishya_lekha  # noqa: F401

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
DB_URL   = os.environ.get("DATABASE_URL",
    "postgresql://amjis_app:50mii04kTKDUUu54CAKdS4Bv2gx1IoWy@127.0.0.1:5433/amjis")

BUILD_ORDER = [
    'ka_yojaka',
    'ka_sangam',
    'ka_kalasutra',
    'ka_vighnakara',
    'ka_kala_darshana',
    'ka_jivana_parva',
    'ka_bhavishya_lekha',
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--from", dest="start_from", default=None,
                        help="Resume from this asset_id (skip earlier assets)")
    args = parser.parse_args()

    order = BUILD_ORDER
    if args.start_from:
        try:
            idx = BUILD_ORDER.index(args.start_from)
            order = BUILD_ORDER[idx:]
            logger.info("Resuming from %s (%d assets)", args.start_from, len(order))
        except ValueError:
            logger.error("Unknown asset_id: %s. Valid: %s", args.start_from, BUILD_ORDER)
            sys.exit(1)

    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False

    total = 0
    for asset_id in order:
        writer_cls = _REGISTRY.get(asset_id)
        if writer_cls is None:
            logger.warning("SKIP: %s not in registry (service asset or not yet built)", asset_id)
            continue

        writer = writer_cls()
        build_id = str(uuid.uuid4())
        logger.info("=== RUNNING %s (build_id=%s) ===", asset_id, build_id)

        ctx = ContextSpec(
            asset_id=asset_id,
            build_id=build_id,
            db_conn=conn,
            config={"chart_id": CHART_ID},
            dry_run=args.dry_run,
        )

        try:
            result = writer.run(ctx)
            conn.commit()
            rows = getattr(result, 'rows_inserted', getattr(result, 'rows_written', 0)) or 0
            logger.info("DONE %s: %d rows written", asset_id, rows)
            total += rows
            print(f"  ✓ {asset_id}: {rows} rows")
        except Exception as exc:
            conn.rollback()
            logger.error("FAILED %s: %s", asset_id, exc, exc_info=True)
            print(f"  ✗ {asset_id}: FAILED — {exc}")
            sys.exit(1)

    conn.close()
    print(f"\nL3 full build complete: {total} total rows for chart {CHART_ID}")

if __name__ == "__main__":
    main()
