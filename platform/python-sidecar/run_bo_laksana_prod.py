#!/usr/bin/env python3
"""
Direct runner for bo_laksana against prod DB (Cloud SQL Auth Proxy at 127.0.0.1:5433).
Bypasses the full orchestrator UI to run the writer standalone.

Usage:
    python run_bo_laksana_prod.py [--dry-run]
"""
import os, sys, uuid, logging, argparse
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger("bo_laksana_runner")
sys.path.insert(0, os.path.dirname(__file__))

import psycopg
from pipeline.orchestrator.writers import ContextSpec, _REGISTRY
# Import the writer module directly — avoids discover_all()/get_writer() which both
# call _auto_discover() and hard-fail on ga_nakshatra (jhora not installed in this venv).
import pipeline.orchestrator.writers.bo_laksana  # noqa: F401 — registers via @register

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
DB_URL   = os.environ.get("DATABASE_URL",
    "postgresql://amjis_app:50mii04kTKDUUu54CAKdS4Bv2gx1IoWy@127.0.0.1:5433/amjis")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    writer_cls = _REGISTRY.get("bo_laksana")
    if writer_cls is None:
        print("ERROR: bo_laksana not in registry", file=sys.stderr)
        sys.exit(1)

    writer = writer_cls()
    build_id = str(uuid.uuid4())
    logger.info("build_id=%s chart_id=%s dry_run=%s", build_id, CHART_ID, args.dry_run)

    # prepare_threshold=None disables psycopg3's automatic statement preparation,
    # which interacts badly with ::jsonb inline casts over large row counts.
    conn = psycopg.connect(DB_URL, prepare_threshold=None)
    conn.autocommit = False
    ctx = ContextSpec(
        asset_id="bo_laksana",
        build_id=build_id,
        db_conn=conn,
        config={"chart_id": CHART_ID},
        dry_run=args.dry_run,
    )

    substeps = writer.plan_substeps(ctx)
    logger.info("Planned %d substeps: %s", len(substeps), [s.key for s in substeps])

    total_inserted = 0
    for step in substeps:
        logger.info("=== Running substep: %s ===", step.label)
        try:
            result = writer.run_substep(ctx, step)
            total_inserted += result.rows_inserted
            logger.info("  → inserted=%d notes=%s", result.rows_inserted, result.notes)
        except Exception as exc:
            logger.error("  SUBSTEP FAILED: %s: %s", type(exc).__name__, exc)
            import traceback; traceback.print_exc()
            raise

    conn.commit()
    conn.close()
    logger.info("=== bo_laksana COMPLETE: total_inserted=%d ===", total_inserted)

if __name__ == "__main__":
    main()
