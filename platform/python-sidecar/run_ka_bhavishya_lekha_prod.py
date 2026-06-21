#!/usr/bin/env python3
"""
Direct runner for ka_bhavishya_lekha against prod DB (Cloud SQL Auth Proxy at 127.0.0.1:5433).
Depends on: ka_kala_darshana + ka_vighnakara.

Usage:
    python run_ka_bhavishya_lekha_prod.py [--dry-run]
"""
import os, sys, uuid, logging, argparse
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger("ka_bhavishya_lekha_runner")
sys.path.insert(0, os.path.dirname(__file__))

import psycopg2
from pipeline.orchestrator.writers import ContextSpec, _REGISTRY
import pipeline.orchestrator.writers.ka_bhavishya_lekha  # noqa: F401 — registers via @register

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
DB_URL   = os.environ.get("DATABASE_URL",
    "postgresql://amjis_app:50mii04kTKDUUu54CAKdS4Bv2gx1IoWy@127.0.0.1:5433/amjis")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    writer_cls = _REGISTRY.get("ka_bhavishya_lekha")
    if writer_cls is None:
        print("ERROR: ka_bhavishya_lekha not in registry", file=sys.stderr)
        sys.exit(1)

    writer = writer_cls()
    build_id = str(uuid.uuid4())
    logger.info("build_id=%s chart_id=%s dry_run=%s", build_id, CHART_ID, args.dry_run)

    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False
    ctx = ContextSpec(
        asset_id="ka_bhavishya_lekha",
        build_id=build_id,
        db_conn=conn,
        config={"chart_id": CHART_ID},
        dry_run=args.dry_run,
    )

    result = writer.run(ctx)
    conn.commit()
    conn.close()
    logger.info("Done: rows_written=%s", getattr(result, 'rows_written', getattr(result, 'rows_inserted', 'n/a')))
    print(f"ka_bhavishya_lekha: rows written for chart {CHART_ID}")

if __name__ == "__main__":
    main()
