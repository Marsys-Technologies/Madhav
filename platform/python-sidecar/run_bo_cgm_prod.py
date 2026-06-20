#!/usr/bin/env python3
"""Standalone runner for bo_bimba (CGM nodes) then bo_karanajala (CGM edges)."""
import os, sys, uuid, logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger("bo_cgm_runner")
sys.path.insert(0, os.path.dirname(__file__))

import psycopg
from pipeline.orchestrator.writers import discover_all, get_writer, ContextSpec

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
DB_URL   = os.environ.get("DATABASE_URL",
    "postgresql://amjis_app:50mii04kTKDUUu54CAKdS4Bv2gx1IoWy@127.0.0.1:5433/amjis")

def run_writer(asset_id: str, build_id: str):
    writer_cls = get_writer(asset_id)
    writer = writer_cls()
    conn = psycopg.connect(DB_URL, prepare_threshold=None)
    conn.autocommit = False
    ctx = ContextSpec(asset_id=asset_id, build_id=build_id, db_conn=conn,
                      config={"chart_id": CHART_ID}, dry_run=False)
    try:
        result = writer.run(ctx)
        conn.commit()
        logger.info("%s COMPLETE: rows_inserted=%d notes=%s", asset_id, result.rows_inserted, result.notes)
    except Exception as exc:
        conn.rollback()
        logger.error("%s FAILED: %s", asset_id, exc)
        import traceback; traceback.print_exc()
        raise
    finally:
        conn.close()

def main():
    discover_all()
    build_id = str(uuid.uuid4())
    logger.info("build_id=%s chart_id=%s", build_id, CHART_ID)
    # bo_bimba (nodes) must precede bo_karanajala (edges reference nodes)
    run_writer("bo_bimba", build_id)
    run_writer("bo_karanajala", build_id)

if __name__ == "__main__":
    main()
