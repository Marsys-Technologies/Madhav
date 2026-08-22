"""
dispatch_utkarsha_w02_ka_assets.py — GOCHARA-UTKARṢA W0.2 baseline builds.

Dispatches the six W0.2 ka_* (plus bg_gochara_arcs check) baseline builds
for BOTH canonical charts:
  - 482012f1-710e-4a25-994a-93821f5871aa (native, Abhisek Mohanty)
  - 1c826d5a-41cb-4450-b4dc-59d440e5f75a (Abhinandan Mohanty)

TARGET ASSETS (per chart):
  ka_vedha_gochara, ka_moorti_nirnaya, ka_kota_chakra,
  ka_tithi_pravesha, ka_gochara_v2_materialize

NOTE: bg_gochara_arcs is scope='global' — this script CHECKS its state.
If NOT lit, it prints a warning. Fix: run the global build first:
  cd platform/python-sidecar
  python3 -m pipeline.orchestrator.main --global-build
Then re-run this script.

PRECONDITIONS:
  1. cloud-sql-proxy running on 127.0.0.1:5433 (DATABASE_URL in .env.local).
  2. SAMPŪRTI L-2 cross-campaign lease expired (after 06:30 UTC 2026-08-10).
  3. W0.2 DB9 fixes merged (PR #1151, 162c387a6) — ka_vedha_gochara,
     ka_kota_chakra, sarvatobhadra fixes in production sidecar.
  4. W0.3 migration 556 applied (generation-inclusive index + protected_generations).
  5. I6a migration 557 applied (utkarsha_builder role live).
  6. I1 constraint: ka_gochara_sweep is EXCLUDED from this build (never rebuild
     the protected v1 corpus).

Usage:
  cd <repo-root>/platform
  python3 scripts/dispatch_utkarsha_w02_ka_assets.py

Prints TWO run_ids (one per chart) to stdout. Then run:
  cd python-sidecar
  python3 -m pipeline.orchestrator.main --run-id <NATIVE_RUN_ID>
  python3 -m pipeline.orchestrator.main --run-id <ABHINANDAN_RUN_ID>
"""
from __future__ import annotations

import json
import os
import sys
import uuid

CHARTS = [
    ("482012f1-710e-4a25-994a-93821f5871aa", "native"),
    ("1c826d5a-41cb-4450-b4dc-59d440e5f75a", "abhinandan"),
]
TARGET_ASSETS = [
    "ka_vedha_gochara",
    "ka_moorti_nirnaya",
    "ka_kota_chakra",
    "ka_tithi_pravesha",
    "ka_gochara_v2_materialize",
]
TRIGGERED_BY = "utkarsha-w02-baseline-builds"

_env_file = os.path.join(os.path.dirname(__file__), "..", ".env.local")
if os.path.exists(_env_file):
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


def main() -> None:
    import psycopg
    import psycopg.rows

    database_url = os.environ["DATABASE_URL"]
    conn = psycopg.connect(database_url, row_factory=psycopg.rows.dict_row)
    conn.autocommit = False
    cur = conn.cursor()

    # ── 1. Check bg_gochara_arcs global state ────────────────────────────────
    cur.execute(
        """SELECT state, last_error, last_built_at
           FROM asset_throughput
           WHERE asset_id = 'bg_gochara_arcs' AND chart_id IS NULL""",
    )
    arcs_row = cur.fetchone()
    if arcs_row is None:
        print("[W0.2 WARN] bg_gochara_arcs: no asset_throughput row (never built).", file=sys.stderr)
        print("[W0.2 WARN] Run global build FIRST:", file=sys.stderr)
        print("[W0.2 WARN]   cd platform/python-sidecar && python3 -m pipeline.orchestrator.main --global-build", file=sys.stderr)
        print("[W0.2 WARN] Then re-run this script.", file=sys.stderr)
        conn.close()
        sys.exit(1)
    elif arcs_row["state"] != "lit":
        print(f"[W0.2 WARN] bg_gochara_arcs state={arcs_row['state']} (not lit).", file=sys.stderr)
        print(f"[W0.2 WARN] last_error={arcs_row['last_error']}", file=sys.stderr)
        print("[W0.2 WARN] Run global build FIRST:", file=sys.stderr)
        print("[W0.2 WARN]   cd platform/python-sidecar && python3 -m pipeline.orchestrator.main --global-build", file=sys.stderr)
        print("[W0.2 WARN] Then re-run this script.", file=sys.stderr)
        conn.close()
        sys.exit(1)
    else:
        print(
            f"[W0.2] bg_gochara_arcs: state=lit, built_at={arcs_row['last_built_at']} ✓",
            file=sys.stderr,
        )

    # ── 2. Verify target assets exist in registry ────────────────────────────
    cur.execute(
        "SELECT asset_id, scope, has_writer FROM asset_registry WHERE asset_id = ANY(%s)",
        (TARGET_ASSETS,),
    )
    rows = cur.fetchall()
    found = {r["asset_id"] for r in rows}
    missing = set(TARGET_ASSETS) - found
    if missing:
        raise RuntimeError(f"asset_registry missing rows for: {sorted(missing)}")
    no_writer = [r["asset_id"] for r in rows if not r["has_writer"]]
    if no_writer:
        raise RuntimeError(f"asset_registry rows with has_writer=false: {sorted(no_writer)}")
    print(f"[W0.2] asset_registry: all {len(TARGET_ASSETS)} target assets confirmed ✓", file=sys.stderr)

    # ── 3. Create build_runs for each chart ──────────────────────────────────
    run_ids = {}
    for chart_id, label in CHARTS:
        # Reset all target assets to dormant so orchestrator treats as genuine rebuild.
        # I1: ka_gochara_sweep is explicitly excluded from this loop.
        for asset_id in TARGET_ASSETS:
            cur.execute(
                """INSERT INTO asset_throughput (chart_id, asset_id, state)
                   VALUES (%s, %s, 'dormant')
                   ON CONFLICT (chart_id, asset_id) WHERE chart_id IS NOT NULL
                   DO UPDATE SET state = 'dormant', last_error = NULL""",
                (chart_id, asset_id),
            )

        run_id = str(uuid.uuid4())
        cur.execute(
            """INSERT INTO build_runs
                 (id, chart_id, scope, scope_target, action, plan, state, triggered_by)
               VALUES (%s, %s, 'asset_set', NULL, 'rebuild', %s, 'planned', %s)""",
            (run_id, chart_id, json.dumps(TARGET_ASSETS), TRIGGERED_BY),
        )
        for position, asset_id in enumerate(TARGET_ASSETS):
            cur.execute(
                """INSERT INTO build_run_assets (run_id, asset_id, position, state)
                   VALUES (%s, %s, %s, 'queued')""",
                (run_id, asset_id, position),
            )
        run_ids[label] = (chart_id, run_id)
        print(f"[W0.2] created build_run for {label} ({chart_id[:8]}…): {run_id}", file=sys.stderr)

    conn.commit()
    conn.close()

    print(f"\nNATIVE_RUN_ID={run_ids['native'][1]}")
    print(f"ABHINANDAN_RUN_ID={run_ids['abhinandan'][1]}")
    print(
        "\nNext steps:",
        "  cd platform/python-sidecar",
        f"  python3 -m pipeline.orchestrator.main --run-id {run_ids['native'][1]}",
        f"  python3 -m pipeline.orchestrator.main --run-id {run_ids['abhinandan'][1]}",
        sep="\n",
    )


if __name__ == "__main__":
    main()
