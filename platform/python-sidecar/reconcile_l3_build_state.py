#!/usr/bin/env python3
"""
reconcile_l3_build_state.py — one-time build-state reconciliation for L3 Kāla.

Context: The L3 writers ran via standalone run_ka_*_prod.py scripts that bypassed the
orchestrator. Rows are present in prod, but asset_throughput was never stamped (last_built_at
= NULL, state = dormant/absent). This script stamps asset_throughput directly so the cockpit
build tracker shows the correct lit state.

Per CLAUDECODE_BRIEF_L3_KALA_REMEDIATION_v1_0.md §A.2 (FINISH-2):
  "a one-time mark-fresh ... sets last_built_at = now() and build_state_stale = false"
  Document it as a reconcile, not a build. Do NOT have a writer self-stamp (§N.2 violation).

Usage (with Cloud SQL Auth Proxy running at 127.0.0.1:5433):
    python reconcile_l3_build_state.py [--dry-run]
"""
import os, sys, argparse, logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("l3_reconcile")

import psycopg2

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://amjis_app:50mii04kTKDUUu54CAKdS4Bv2gx1IoWy@127.0.0.1:5433/amjis",
)

# L3 artifact assets: asset_id → target_table (per-chart rows)
ARTIFACT_ASSETS = {
    "ka_yojaka":         "kala_activation_predicates",
    "ka_sangam":         "kala_convergence",
    "ka_kalasutra":      "kala_activation",
    "ka_vighnakara":     "kala_obstruction",
    "ka_kala_darshana":  "kala_darshana",
    "ka_jivana_parva":   "kala_jivana_parva",
    "ka_bhavishya_lekha": "kala_bhavishya",
}

# L3 service assets: no stored rows; cockpit stats route returns service_ok via asset_type='service'
# branch — asset_throughput not needed for them. Listed here for reference only.
SERVICE_ASSETS = ["ka_graha_sancara", "ka_dasha_kala", "ka_gochara", "ka_muhurta_seva", "ka_tulana"]


def main():
    parser = argparse.ArgumentParser(description="Reconcile L3 Kāla build-state in asset_throughput")
    parser.add_argument("--dry-run", action="store_true", help="Print SQL but do not execute")
    args = parser.parse_args()

    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False
    cur = conn.cursor()

    logger.info("=== L3 Kāla build-state reconciliation ===")
    logger.info("chart_id: %s  dry_run: %s", CHART_ID, args.dry_run)

    results = {}
    for asset_id, table in ARTIFACT_ASSETS.items():
        # 1. Count actual rows in the target table for this chart
        cur.execute(f"SELECT count(*) FROM {table} WHERE chart_id = %s", (CHART_ID,))
        actual_rows = cur.fetchone()[0]
        logger.info("  %s → %s: %d rows found", asset_id, table, actual_rows)

        if actual_rows == 0:
            logger.warning("  SKIP %s — no rows found; writer may not have run", asset_id)
            results[asset_id] = {"rows": 0, "action": "skipped"}
            continue

        # 2. Check current asset_throughput state
        cur.execute(
            "SELECT state, last_built_at FROM asset_throughput WHERE asset_id = %s AND chart_id IS NOT DISTINCT FROM %s",
            (asset_id, CHART_ID),
        )
        tp_row = cur.fetchone()
        current_state = tp_row[0] if tp_row else None
        current_last_built = tp_row[1] if tp_row else None
        logger.info("    throughput: state=%s  last_built_at=%s", current_state, current_last_built)

        if args.dry_run:
            logger.info("    [DRY-RUN] would upsert: state=lit, last_built_at=NOW(), rows_written=%d", actual_rows)
            results[asset_id] = {"rows": actual_rows, "action": "would_upsert"}
            continue

        if tp_row:
            cur.execute(
                """UPDATE asset_throughput
                   SET state = 'lit', last_built_at = NOW(), rows_written = %s, last_error = NULL
                   WHERE asset_id = %s AND chart_id IS NOT DISTINCT FROM %s""",
                (actual_rows, asset_id, CHART_ID),
            )
        else:
            cur.execute(
                """INSERT INTO asset_throughput (asset_id, chart_id, state, last_built_at, rows_written)
                   VALUES (%s, %s, 'lit', NOW(), %s)""",
                (asset_id, CHART_ID, actual_rows),
            )
        results[asset_id] = {"rows": actual_rows, "action": "updated"}
        logger.info("    ✓ stamped lit  rows_written=%d", actual_rows)

    if not args.dry_run:
        conn.commit()
        logger.info("Committed.")
    else:
        conn.rollback()

    cur.close()
    conn.close()

    logger.info("\n=== Summary ===")
    for asset_id, info in results.items():
        logger.info("  %-25s  rows=%-6d  action=%s", asset_id, info["rows"], info["action"])

    logger.info("\nService assets (no throughput needed — cockpit returns service_ok via asset_type):")
    for svc in SERVICE_ASSETS:
        logger.info("  %s", svc)

    logger.info("\nNext: verify cockpit at /api/cockpit/stats?chart_id=%s", CHART_ID)


if __name__ == "__main__":
    main()
