#!/usr/bin/env python3
"""
fresh_chart_smoke_bootstrap.py — the fresh-chart CI smoke test (native-authorized,
item 2c of the ka_bhavishya_lekha/ga_structural vocabulary-drift close-out wave).

Purpose: build ONE synthetic ("fixture") chart through the FULL asset plan (every
active ga_*/bo_*/ka_*/ph_*/mi_* asset in asset_registry, topologically ordered) on a
schema that has JUST had the current branch's migrations applied — so that any
mismatch between a writer's emitted vocabulary and a live CHECK constraint fails
LOUDLY, in CI, on the PR/branch that introduced it, instead of being discovered
later as a parked finding (the exact failure mode this test exists to retire).

This script assumes the target database already has:
  - the full production schema (all tables/constraints) restored from a
    schema-only pg_dump, PLUS data for the ~85 global reference tables
    (bg_*, brahma_*, reference_*, classical_*, ephemeris_daily, panchanga_daily,
    asset_registry, asset_coefficients, ...) — see the accompanying workflow
    (.github/workflows/fresh_chart_smoke.yml) for the exact dump/restore recipe.
  - the CURRENT branch's migrations applied on top (via platform/scripts/migrate.ts).
It does NOT create any of that itself — it only creates the fixture chart row and
drives the orchestrator's own execute_run() over that chart's full asset plan.

Usage:
    DATABASE_URL=postgresql://... python3 fresh_chart_smoke_bootstrap.py

Exit codes:
    0 — every active asset reached 'lit'/'service_ok' for the fixture chart.
    1 — one or more assets failed; a CHECK-constraint violation among the
        failures is called out explicitly (that's this test's primary purpose).
"""
from __future__ import annotations

import json
import logging
import os
import sys
import uuid

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

_sidecar = os.path.join(os.path.dirname(__file__), "..", "..", "python-sidecar")
if _sidecar not in sys.path:
    sys.path.insert(0, os.path.abspath(_sidecar))

TRIGGERED_BY = "ci-fresh-chart-smoke"

# A synthetic native — deliberately NOT the real native's birth data (CLAUDE.md
# §B / B.10: no literal native birth-chart values in code outside L1; this is a
# fixture chart, role='fixture', not a native record). Chosen to exercise a
# distinct lagna/nakshatra from the canonical chart so vocabulary bugs gated on
# specific sign/nakshatra branches aren't accidentally missed.
FIXTURE_NATIVE = {
    "name": "CI Fresh-Chart Smoke Fixture",
    "birth_date": "1990-06-15",
    "birth_time": "14:30:00",
    "birth_place": "Chennai, Tamil Nadu, India",
    "birth_lat": 13.0827,
    "birth_lng": 80.2707,
    "timezone_id": "Asia/Kolkata",
}


def toposort(nodes: set[str], deps: dict[str, list[str]]) -> list[str]:
    order: list[str] = []
    visited: set[str] = set()
    temp: set[str] = set()

    def visit(n: str) -> None:
        if n in visited:
            return
        if n in temp:
            raise RuntimeError(f"cycle detected at {n}")
        temp.add(n)
        for d in deps.get(n, []):
            if d in nodes:
                visit(d)
        temp.discard(n)
        visited.add(n)
        order.append(n)

    for n in sorted(nodes):
        visit(n)
    return order


def main() -> None:
    import psycopg
    import psycopg.rows

    from pipeline.orchestrator.db import db_url
    from pipeline.orchestrator.writers import discover_all
    discover_all()
    from pipeline.orchestrator.runner import execute_run

    conn = psycopg.connect(db_url(), row_factory=psycopg.rows.dict_row)
    conn.autocommit = False
    cur = conn.cursor()

    # ── Create the fixture chart ────────────────────────────────────────────
    chart_id = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO charts
             (id, chart_id, name, birth_date, birth_time, birth_place,
              birth_lat, birth_lng, timezone_id, role, native_id)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'fixture', 'ci-smoke')""",
        (
            chart_id, chart_id, FIXTURE_NATIVE["name"], FIXTURE_NATIVE["birth_date"],
            FIXTURE_NATIVE["birth_time"], FIXTURE_NATIVE["birth_place"],
            FIXTURE_NATIVE["birth_lat"], FIXTURE_NATIVE["birth_lng"],
            FIXTURE_NATIVE["timezone_id"],
        ),
    )
    conn.commit()
    logger.info("[fixture] created chart_id=%s (role=fixture, native_id=ci-smoke)", chart_id)

    # ── Compute the full active-asset topological plan ──────────────────────
    cur.execute(
        "SELECT asset_id, COALESCE(depends_on, '{}') AS depends_on "
        "FROM asset_registry WHERE is_active = true"
    )
    registry = cur.fetchall()
    all_assets = {r["asset_id"] for r in registry}
    deps = {r["asset_id"]: list(r["depends_on"] or []) for r in registry}
    plan = toposort(all_assets, deps)
    logger.info("[plan] %d active assets in dependency order", len(plan))

    run_id = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO build_runs
             (id, chart_id, scope, scope_target, action, plan, state, triggered_by)
           VALUES (%s, %s, 'asset_set', NULL, 'build', %s, 'planned', %s)""",
        (run_id, chart_id, json.dumps(plan), TRIGGERED_BY),
    )
    for i, asset_id in enumerate(plan):
        cur.execute(
            """INSERT INTO build_run_assets (run_id, asset_id, position, state)
               VALUES (%s, %s, %s, 'queued')""",
            (run_id, asset_id, i),
        )
    conn.commit()
    logger.info("[run] created build_run %s — invoking execute_run()", run_id)
    conn.close()

    execute_run(run_id)
    logger.info("[run] execute_run returned — verifying throughput")

    conn2 = psycopg.connect(db_url(), row_factory=psycopg.rows.dict_row)
    cur2 = conn2.cursor()
    cur2.execute(
        """SELECT asset_id, state, rows_written, last_error
           FROM asset_throughput WHERE chart_id = %s
           ORDER BY array_position(%s::text[], asset_id)""",
        (chart_id, plan),
    )
    rows = cur2.fetchall()
    failed = [r for r in rows if r["state"] not in ("lit", "service_ok")]
    conn2.close()

    for r in rows:
        marker = "OK" if r not in failed else "FAIL"
        logger.info("[post][%s] %s: state=%s rows_written=%s last_error=%s",
                    marker, r["asset_id"], r["state"], r["rows_written"], r["last_error"])

    if failed:
        check_violations = [
            f for f in failed
            if f["last_error"] and (
                "check constraint" in f["last_error"].lower()
                or "CheckViolation" in f["last_error"]
                or "violates check" in f["last_error"].lower()
            )
        ]
        if check_violations:
            logger.error(
                "[SCHEMA-DRIFT] %d asset(s) failed on a live CHECK-constraint violation — "
                "this is exactly the defect class this smoke test exists to catch: %s",
                len(check_violations), [f["asset_id"] for f in check_violations],
            )
        logger.error("[run] %d/%d assets did NOT reach a built state: %s",
                      len(failed), len(rows), [f["asset_id"] for f in failed])
        sys.exit(1)

    logger.info("[run] ALL %d active assets built successfully for fixture chart %s",
                len(rows), chart_id)


if __name__ == "__main__":
    main()
