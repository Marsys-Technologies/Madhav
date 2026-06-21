#!/usr/bin/env python3
"""
Direct runner for ka_kala_darshana against prod DB (Cloud SQL Auth Proxy at 127.0.0.1:5433).
Depends on: ka_sangam + ka_vighnakara + ka_kalasutra.

Usage:
    python run_ka_kala_darshana_prod.py [--dry-run]
"""
import os, sys, uuid, logging, argparse
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger("ka_kala_darshana_runner")
sys.path.insert(0, os.path.dirname(__file__))

import psycopg2
from pipeline.orchestrator.writers import ContextSpec, _REGISTRY
import pipeline.orchestrator.writers.ka_kala_darshana  # noqa: F401 — registers via @register

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
DB_URL   = os.environ.get("DATABASE_URL",
    "postgresql://amjis_app:50mii04kTKDUUu54CAKdS4Bv2gx1IoWy@127.0.0.1:5433/amjis")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    writer_cls = _REGISTRY.get("ka_kala_darshana")
    if writer_cls is None:
        print("ERROR: ka_kala_darshana not in registry", file=sys.stderr)
        sys.exit(1)

    writer = writer_cls()
    build_id = str(uuid.uuid4())
    logger.info("build_id=%s chart_id=%s dry_run=%s", build_id, CHART_ID, args.dry_run)

    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False
    ctx = ContextSpec(
        asset_id="ka_kala_darshana",
        build_id=build_id,
        db_conn=conn,
        config={"chart_id": CHART_ID},
        dry_run=args.dry_run,
    )

    result = writer.run(ctx)
    conn.commit()
    conn.close()
    logger.info("Done: rows_inserted=%d", result.rows_inserted)
    print(f"ka_kala_darshana: {result.rows_inserted} rows written for chart {CHART_ID}")

if __name__ == "__main__":
    main()
