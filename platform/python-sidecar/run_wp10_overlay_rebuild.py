#!/usr/bin/env python3
"""
run_wp10_overlay_rebuild.py — WP10 tranche 2, Link 1: §12.9 production overlay
fingerprint rebuild (E-018 item ii), per the REVIEW_REQUEST_PRODUCTION_APPLICATION_SET
packet (Link 1).

Runs the registered writers ka_vedha_gochara and ka_moorti_nirnaya for ONE
chart against the given DSN, in ONE transaction (both writers' per-chart
delete-then-insert commit or roll back together), and verifies the §12.9
freshness gate before and after. The rebuild recomputes both upstream
fingerprints from the live rule sources and re-stamps every overlay row; the
writers' own honesty guarantees (citation-derived uncited_extension, M-8 rows,
WP9 stamp columns) apply.

Direct-runner precedent: run_ph_pratikara_prod.py / run_ka_sangam_prod.py
(writer + ContextSpec, orchestrator bypassed). The writers never commit; this
runner owns the transaction.

Guard: refuses to run unless PRODUCTION_TRANCHE_2_AUTHORIZED=true is set in
the environment (Link 1 is a tranche-2 production write).

Usage:
    PRODUCTION_TRANCHE_2_AUTHORIZED=true \
    python3 run_wp10_overlay_rebuild.py --dsn postgresql://... --chart-id <uuid>

Exit codes: 0 rebuilt + fresh; 3 cannot proceed (guard/precheck failed);
1 writer failure (rolled back).
"""
import argparse
import json
import logging
import os
import sys
import uuid

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger("wp10_overlay_rebuild")
sys.path.insert(0, os.path.dirname(__file__))

import psycopg  # noqa: E402

from pipeline.orchestrator.writers import ContextSpec  # noqa: E402
import pipeline.orchestrator.writers.ka_vedha_gochara  # noqa: F401,E402 — registers
import pipeline.orchestrator.writers.ka_moorti_nirnaya  # noqa: F401,E402 — registers
from services.ka_vedha_gochara.freshness import (  # noqa: E402
    check_overlay_freshness,
    gate_allows_overlays,
)
from services.ka_vedha_gochara.writer import KaVedhaGocharaWriter  # noqa: E402
from services.ka_moorti_nirnaya.writer import KaMoortiNirnayaWriter  # noqa: E402


def _report(reports: dict) -> dict:
    return {
        name: {
            "state": r.state,
            "total": r.total,
            "missing": r.missing,
            "mismatched": r.mismatched,
            "current_fingerprint": r.current,
        }
        for name, r in reports.items()
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", required=True)
    parser.add_argument("--chart-id", required=True)
    args = parser.parse_args()

    if os.environ.get("PRODUCTION_TRANCHE_2_AUTHORIZED") != "true":
        print("REFUSED: PRODUCTION_TRANCHE_2_AUTHORIZED is not 'true'. "
              "Link 1 is a tranche-2 production write.", file=sys.stderr)
        return 3

    conn = psycopg.connect(args.dsn, prepare_threshold=None)
    conn.autocommit = False
    # MR-39 + S7-LOCK session-scoped SETs (precedent: run_ph_pratikara_prod.py)
    with conn.cursor() as cur:
        cur.execute("SET idle_in_transaction_session_timeout = 1800000")
        cur.execute("SET lock_timeout = '300s'")
    conn.commit()

    build_id = f"wp10-link1-{uuid.uuid4()}"
    logger.info("build_id=%s chart_id=%s", build_id, args.chart_id)

    # Pre-state (read-only): the gate is expected RED (stale) before the rebuild.
    pre = check_overlay_freshness(conn, args.chart_id)
    conn.rollback()
    logger.info("pre-state: %s", json.dumps({k: v["state"] for k, v in _report(pre).items()}))

    results = {}
    try:
        for writer in (KaVedhaGocharaWriter(), KaMoortiNirnayaWriter()):
            ctx = ContextSpec(
                asset_id=writer.asset_id,
                build_id=build_id,
                db_conn=conn,
                config={"chart_id": args.chart_id},
            )
            res = writer.run(ctx)
            results[writer.asset_id] = {
                "rows_inserted": res.rows_inserted,
                "notes": res.notes,
            }
            logger.info("%s: rows_inserted=%s notes=%s",
                        writer.asset_id, res.rows_inserted, res.notes)
        conn.commit()
    except Exception as exc:
        conn.rollback()
        import traceback
        traceback.print_exc()
        logger.error("Link 1 rebuild FAILED for %s: %s", args.chart_id, exc)
        conn.close()
        return 1

    # Post-state: the §12.9 gate must be GREEN (fresh) on the rebuilt rows.
    post = check_overlay_freshness(conn, args.chart_id)
    conn.rollback()
    conn.close()

    ok = gate_allows_overlays(post)
    report = {
        "build_id": build_id,
        "chart_id": args.chart_id,
        "pre": _report(pre),
        "writers": results,
        "post": _report(post),
        "gate_allows_overlays": ok,
    }
    print(json.dumps(report, indent=2, default=str))
    if not ok:
        print("ERROR: post-rebuild freshness gate is not fresh — do NOT proceed "
              "to Link 2 for this chart", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
