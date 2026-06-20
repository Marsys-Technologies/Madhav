#!/usr/bin/env python3
"""
Standalone runner for bo_sangati against prod DB (Cloud SQL Auth Proxy at 127.0.0.1:5433).
Bypasses the full orchestrator UI to run the writer standalone.

Usage:
    python run_bo_sangati_prod.py [--dry-run]
"""
import os, sys, uuid, logging, argparse
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger("bo_sangati_runner")
sys.path.insert(0, os.path.dirname(__file__))

import psycopg
from pipeline.orchestrator.writers import ContextSpec, _REGISTRY
# Import the writer module directly — avoids discover_all()/get_writer() which both
# call _auto_discover() and hard-fail on ga_nakshatra (jhora not installed in this venv).
import pipeline.orchestrator.writers.bo_sangati  # noqa: F401 — registers via @register

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
DB_URL   = os.environ.get("DATABASE_URL",
    "postgresql://amjis_app:50mii04kTKDUUu54CAKdS4Bv2gx1IoWy@127.0.0.1:5433/amjis")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    writer_cls = _REGISTRY.get("bo_sangati")
    if writer_cls is None:
        print("ERROR: bo_sangati not in registry", file=sys.stderr)
        sys.exit(1)

    writer = writer_cls()
    build_id = str(uuid.uuid4())
    logger.info("build_id=%s chart_id=%s dry_run=%s", build_id, CHART_ID, args.dry_run)

    # prepare_threshold=None disables psycopg3's automatic statement preparation,
    # which interacts badly with ::jsonb inline casts over large row counts.
    conn = psycopg.connect(DB_URL, prepare_threshold=None)
    conn.autocommit = False
    ctx = ContextSpec(
        asset_id="bo_sangati",
        build_id=build_id,
        db_conn=conn,
        config={"chart_id": CHART_ID},
        dry_run=args.dry_run,
    )
    result = writer.run(ctx)
    conn.commit()
    conn.close()
    logger.info("bo_sangati COMPLETE: rows_inserted=%d notes=%s", result.rows_inserted, result.notes)

if __name__ == "__main__":
    main()
