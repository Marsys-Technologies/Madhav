#!/usr/bin/env python3
"""
Direct runner for ph_pratikara against prod DB (Cloud SQL Auth Proxy at 127.0.0.1:5433).
Bypasses the full orchestrator UI to run the writer standalone.

ph_pratikara writes phala_mitigation (delete-then-insert per chart_id).
No FK cascade issues — safe to run directly after ka_sangam rebuild.

Usage:
    python run_ph_pratikara_prod.py [--dry-run]
"""
import os, sys, uuid, logging, argparse
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger("ph_pratikara_runner")
sys.path.insert(0, os.path.dirname(__file__))

import psycopg
from pipeline.orchestrator.writers import ContextSpec, _REGISTRY
import pipeline.orchestrator.writers.ph_pratikara  # noqa: F401 — registers via @register

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
DB_URL   = os.environ.get("DATABASE_URL")
if not DB_URL:
    raise SystemExit("ERROR: DATABASE_URL env var required (e.g. postgresql://user:pass@127.0.0.1:5433/db via Cloud SQL Auth Proxy)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    writer_cls = _REGISTRY.get("ph_pratikara")
    if writer_cls is None:
        print("ERROR: ph_pratikara not in registry", file=sys.stderr)
        sys.exit(1)

    writer = writer_cls()
    build_id = str(uuid.uuid4())
    logger.info("build_id=%s chart_id=%s dry_run=%s", build_id, CHART_ID, args.dry_run)

    conn = psycopg.connect(DB_URL, prepare_threshold=None)
    conn.autocommit = False
    # PARIṢKĀRA MR-39: session-scoped SET (never ALTER DATABASE/ROLE) so this
    # build session cannot be killed by the server-side idle-in-transaction
    # timeout while the writer computes with no DB traffic in between.
    with conn.cursor() as _mr39_cur:
        _mr39_cur.execute("SET idle_in_transaction_session_timeout = 0")
    conn.commit()

    ctx = ContextSpec(
        asset_id="ph_pratikara",
        build_id=build_id,
        db_conn=conn,
        config={"chart_id": CHART_ID},
        dry_run=args.dry_run,
    )

    try:
        result = writer.run(ctx)
        conn.commit()
        logger.info("=== ph_pratikara COMPLETE: rows_inserted=%d ===", result.rows_inserted)
    except Exception as exc:
        conn.rollback()
        import traceback; traceback.print_exc()
        logger.error("ph_pratikara FAILED: %s", exc)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
