#!/usr/bin/env python3
"""Standalone runner for bo_sangati against prod DB."""
import os, sys, uuid, logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger("bo_sangati_runner")
sys.path.insert(0, os.path.dirname(__file__))

import psycopg
from pipeline.orchestrator.writers import discover_all, get_writer, ContextSpec

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
DB_URL   = os.environ.get("DATABASE_URL",
    "postgresql://amjis_app:50mii04kTKDUUu54CAKdS4Bv2gx1IoWy@127.0.0.1:5433/amjis")

def main():
    discover_all()
    writer_cls = get_writer("bo_sangati")
    writer = writer_cls()
    build_id = str(uuid.uuid4())
    logger.info("build_id=%s chart_id=%s", build_id, CHART_ID)

    conn = psycopg.connect(DB_URL, prepare_threshold=None)
    conn.autocommit = False
    ctx = ContextSpec(asset_id="bo_sangati", build_id=build_id, db_conn=conn,
                      config={"chart_id": CHART_ID}, dry_run=False)
    result = writer.run(ctx)
    conn.commit()
    conn.close()
    logger.info("bo_sangati COMPLETE: rows_inserted=%d notes=%s", result.rows_inserted, result.notes)

if __name__ == "__main__":
    main()
