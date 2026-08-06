#!/usr/bin/env python3
"""
run_ka_gochara_v2_materialize.py — drive the ka_gochara_v2_materialize writer
against a live database for ONE chart, outside the orchestrator (a manual/
measurement run, same discipline as scripts/run_w2g_bind_validations.py).

ṢAḌ-DARŚANA W2G (item 19), lane G REWORK. Mirrors
`pipeline/orchestrator/asset_runner.py`'s real per-substep transaction
discipline (SAVEPOINT before each `run_substep`, RELEASE + commit after each
success, ROLLBACK TO SAVEPOINT on failure) since this script — not the
orchestrator — is the transaction owner for this direct-invocation path. The
writer itself NEVER commits/rolls back/closes the connection (§N.2); this
script is exactly the "someone else" the FROZEN contract assumes will.

Writes ONLY to `kala_gochara_windows_v2` (the writer's own table) and
`kala_gochara_v2_build_state` (delta-aware-invalidation bookkeeping, migration
541, reused unchanged). Never touches `kala_gochara_windows` (v1, protected)
and never sets `app.allow_protected_sweep_rewrite` — this script issues no SQL
of its own beyond the SAVEPOINT/commit machinery; every data statement comes
from the writer, which is independently tested never to reference either
(see `pipeline/orchestrator/writers/tests/test_ka_gochara_v2_materialize.py`).

Usage:
    DATABASE_URL=postgresql://... python3 scripts/run_ka_gochara_v2_materialize.py \\
        --chart-id 482012f1-710e-4a25-994a-93821f5871aa [--now-date 2026-08-06] [--dry-run]

Exit codes:
    0 — every planned substep ran without raising (individual substeps may
        still report zero rows -- an honest empty is not a failure)
    2 — at least one substep raised and could not complete
    3 — the run itself could not proceed (no DATABASE_URL, no driver)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chart-id", required=True)
    parser.add_argument("--now-date", default=None, help="ISO date anchoring the ±3y progressive horizon (default: today)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("ERROR: DATABASE_URL is required", file=sys.stderr)
        return 3

    try:
        import psycopg  # noqa: F401
    except ImportError as exc:  # pragma: no cover
        print(f"ERROR: psycopg unavailable: {exc}", file=sys.stderr)
        return 3

    from pipeline.orchestrator.db import connect
    from pipeline.orchestrator.writers import ContextSpec
    from pipeline.orchestrator.writers.ka_gochara_v2_materialize import GocharaV2MaterializeWriter

    conn = connect()
    writer = GocharaV2MaterializeWriter()
    config = {"chart_id": args.chart_id}
    if args.now_date:
        config["now_date"] = args.now_date
    ctx = ContextSpec(
        asset_id=writer.asset_id,
        build_id=f"manual-run-{int(time.time())}",
        db_conn=conn,
        config=config,
        dry_run=args.dry_run,
    )

    t0 = time.time()
    steps = writer.plan_substeps(ctx)
    results = []
    exit_code = 0

    for step in steps:
        with conn.cursor() as cur:
            cur.execute("SAVEPOINT writer_exec")
        try:
            result = writer.run_substep(ctx, step)
        except Exception as exc:  # noqa: BLE001 -- mirrors asset_runner.py's per-substep isolation
            with conn.cursor() as cur:
                cur.execute("ROLLBACK TO SAVEPOINT writer_exec")
            print(f"[{step.key}] FAILED: {exc}", file=sys.stderr)
            results.append({"event_class": step.key, "error": str(exc)})
            exit_code = 2
            continue
        with conn.cursor() as cur:
            cur.execute("RELEASE SAVEPOINT writer_exec")
        if not args.dry_run:
            conn.commit()
        print(f"[{step.key}] {result.notes}", file=sys.stderr)
        # Candidates-evaluated is parsed PROGRAMMATICALLY from the writer's
        # own notes text (never hand-typed/hand-summed) -- this is the exact
        # discipline PARĪKṢAKA's review of PR #1081 found missing: that PR's
        # "TOTAL: 38 candidates evaluated" line was a hand-computed figure
        # that didn't match its own per-class breakdown (which summed to 30).
        # A regex extraction + `sum()` here cannot silently drift from the
        # per-class figures the way manual arithmetic did.
        m = re.search(r"(\d+) candidates evaluated", result.notes)
        candidates_evaluated = int(m.group(1)) if m else None
        results.append({
            "event_class": step.key,
            "candidates_evaluated": candidates_evaluated,
            "rows_inserted": result.rows_inserted,
            "duration_seconds": result.duration_seconds,
            "notes": result.notes,
        })

    total_inserted = sum(r.get("rows_inserted", 0) for r in results)
    total_candidates = sum(r["candidates_evaluated"] for r in results if r["candidates_evaluated"] is not None)
    report = {
        "chart_id": args.chart_id,
        "asset_id": writer.asset_id,
        "dry_run": args.dry_run,
        "substeps_planned": len(steps),
        "total_candidates_evaluated": total_candidates,
        "total_rows_inserted": total_inserted,
        "wall_clock_seconds": time.time() - t0,
        "results": results,
    }
    print(json.dumps(report, indent=2, default=str))
    conn.close()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
