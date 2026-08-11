#!/usr/bin/env python3
"""
Direct runner for ka_sangam against prod DB (Cloud SQL Auth Proxy at 127.0.0.1:5433).
Bypasses the full orchestrator UI to run the writer standalone.

Pre-deletes phala_anchors rows referencing kala_convergence to avoid FK cascade
UniqueViolation on the natural-key index (phala_anchors_natural_key) that fires
when kala_convergence rows are deleted and convergence_id is SET NULL.

Usage:
    python run_ka_sangam_prod.py [--dry-run]
"""
import os, sys, uuid, logging, argparse
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger("ka_sangam_runner")
sys.path.insert(0, os.path.dirname(__file__))

import psycopg
from pipeline.orchestrator.writers import ContextSpec, _REGISTRY
import pipeline.orchestrator.writers.ka_sangam  # noqa: F401 — registers via @register

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
DB_URL   = os.environ.get("DATABASE_URL")
if not DB_URL:
    raise SystemExit("ERROR: DATABASE_URL env var required (e.g. postgresql://user:pass@127.0.0.1:5433/db via Cloud SQL Auth Proxy)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    writer_cls = _REGISTRY.get("ka_sangam")
    if writer_cls is None:
        print("ERROR: ka_sangam not in registry", file=sys.stderr)
        sys.exit(1)

    writer = writer_cls()
    build_id = str(uuid.uuid4())
    logger.info("build_id=%s chart_id=%s dry_run=%s", build_id, CHART_ID, args.dry_run)

    conn = psycopg.connect(DB_URL, prepare_threshold=None)
    conn.autocommit = False
    # PARIṢKĀRA MR-39: session-scoped SET (never ALTER DATABASE/ROLE) so this
    # build session cannot be killed by the server-side idle-in-transaction
    # timeout while ka_sangam's substeps compute with no DB traffic in between.
    with conn.cursor() as _mr39_cur:
        _mr39_cur.execute("SET idle_in_transaction_session_timeout = 0")
    conn.commit()

    # Pre-delete phala_anchors rows that reference kala_convergence to avoid
    # FK cascade + unique-index conflict when kala_convergence rows are deleted.
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM phala_anchors WHERE chart_id = %s AND anchor_source = %s",
            (CHART_ID, "convergence"),
        )
        logger.info("Pre-deleted %d phala_anchors rows (anchor_source=convergence)", cur.rowcount)
    conn.commit()

    ctx = ContextSpec(
        asset_id="ka_sangam",
        build_id=build_id,
        db_conn=conn,
        config={"chart_id": CHART_ID},
        dry_run=args.dry_run,
    )

    try:
        result = writer.run(ctx)
        conn.commit()
        logger.info("=== ka_sangam COMPLETE: rows_inserted=%d ===", result.rows_inserted)
    except Exception as exc:
        conn.rollback()
        import traceback; traceback.print_exc()
        logger.error("ka_sangam FAILED: %s", exc)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
