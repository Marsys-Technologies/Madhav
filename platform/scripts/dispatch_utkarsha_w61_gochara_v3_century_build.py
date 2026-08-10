"""
dispatch_utkarsha_w61_gochara_v3_century_build.py — GOCHARA-UTKARṢA W6.1 production builds.

Provisions full-century production builds of ka_gochara_v3_century_materialize
for BOTH canonical charts:
  - 482012f1-710e-4a25-994a-93821f5871aa (native, Abhisek Mohanty)
  - 1c826d5a-41cb-4450-b4dc-59d440e5f75a (Abhinandan Mohanty)

The W5.4-repointed writer dual-writes:
  (a) kala_gochara_windows_v2 — staging corpus (era_slice_key='g3_%')
  (b) kala_gochara_windows   — production rows (generation='3.0')

GATE CRITERIA (all must be satisfied before running this script):
  W5.4 MERGED ✓ — writer repoint (ka_gochara_v3_century_materialize dual-write)
  W4.5 VERIFIED ✓ — gochara_v3_calibration table populated with fitted weights
  migration 561 ✓ — gochara_v3_calibration table
  migration 562 ✓ — DAG integration (depends_on, count_sql)
  I6(b) PASS ✓ — protection triggers intact, v1 corpus checksums match
  I1 INVARIANT: ka_gochara_sweep NEVER rebuilt — this script enforces it

PRECONDITIONS:
  1. cloud-sql-proxy running on 127.0.0.1:5433 (DATABASE_URL in platform/.env.local).
  2. All Wave 5 merges in main AND deployed (Deploy to Cloud Run CI completed).
  3. gochara_v3_calibration has fitted weights (from W4.5 run_weight_fitting).
  4. I6(b) rail PASS confirmed (run I6(b) check before this script).

Usage:
  cd <repo-root>/platform
  python3 scripts/dispatch_utkarsha_w61_gochara_v3_century_build.py

Prints TWO run_ids (one per chart) to stdout. Then run:
  cd python-sidecar
  python3 -m pipeline.orchestrator.main --run-id <NATIVE_RUN_ID>
  python3 -m pipeline.orchestrator.main --run-id <ABHINANDAN_RUN_ID>

SLO: target ≤20 min per chart full-century build. If missed, record wall-clock
and raise with ADJUDICATOR (optimize-vs-accept, never a silent miss).
"""
from __future__ import annotations

import json
import os
import sys
import time
import uuid

CHARTS = [
    ("482012f1-710e-4a25-994a-93821f5871aa", "native"),
    ("1c826d5a-41cb-4450-b4dc-59d440e5f75a", "abhinandan"),
]
TARGET_ASSET = "ka_gochara_v3_century_materialize"
TRIGGERED_BY = "utkarsha-w61-production-builds"
EXPECTED_DEPENDS = [
    "ka_moorti_nirnaya",
    "ka_vedha_gochara",
    "ka_kota_chakra",
    "ka_tithi_pravesha",
]

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

    # ── 1. Verify migrations applied ─────────────────────────────────────────
    cur.execute(
        """SELECT EXISTS (
               SELECT 1 FROM information_schema.tables
               WHERE table_name = 'gochara_v3_calibration'
           )"""
    )
    if not cur.fetchone()["exists"]:
        print("[W6.1 ERROR] gochara_v3_calibration table missing (migration 561 not applied).", file=sys.stderr)
        conn.close()
        sys.exit(1)
    print("[W6.1] migration 561 (gochara_v3_calibration): applied ✓", file=sys.stderr)

    cur.execute(
        "SELECT asset_id, has_writer FROM asset_registry WHERE asset_id = %s",
        (TARGET_ASSET,),
    )
    row = cur.fetchone()
    if row is None:
        print(f"[W6.1 ERROR] {TARGET_ASSET} missing from asset_registry (migration 562 not applied).", file=sys.stderr)
        conn.close()
        sys.exit(1)
    if not row["has_writer"]:
        print(f"[W6.1 ERROR] {TARGET_ASSET} has has_writer=false in asset_registry.", file=sys.stderr)
        conn.close()
        sys.exit(1)
    print(f"[W6.1] asset_registry: {TARGET_ASSET} confirmed (has_writer=true) ✓", file=sys.stderr)

    # ── 2. Verify fitted weights exist (W4.5 post-fit rebuild) ───────────────
    cur.execute("SELECT count(*) AS n FROM gochara_v3_calibration")
    cal_count = cur.fetchone()["n"]
    if cal_count == 0:
        print("[W6.1 WARN] gochara_v3_calibration is EMPTY — W4.5 post-fit rebuild may not have run.", file=sys.stderr)
        print("[W6.1 WARN] W6.1 will use I4 honest-fallback weights (0.0 for all mechanisms).", file=sys.stderr)
        print("[W6.1 WARN] This is structurally valid but produces an unweighted v3 corpus.", file=sys.stderr)
        print("[W6.1 WARN] Recommended: run W4.5 post-fit rebuild first.", file=sys.stderr)
        # Not fatal — the writer uses I4 honest 0.0 fallback
    else:
        cur.execute(
            "SELECT toggle_key, weight_value, fitted_at FROM gochara_v3_calibration ORDER BY fitted_at DESC LIMIT 5"
        )
        samples = cur.fetchall()
        print(f"[W6.1] gochara_v3_calibration: {cal_count} fitted weights found ✓", file=sys.stderr)
        for s in samples:
            print(f"  {s['toggle_key']}: weight={s['weight_value']:.4f} (fitted_at={s['fitted_at']})", file=sys.stderr)

    # ── 3. I1 guard: confirm ka_gochara_sweep NOT in target ──────────────────
    assert TARGET_ASSET != "ka_gochara_sweep", "I1 VIOLATION: ka_gochara_sweep must never be in W6.1 target"
    print("[W6.1] I1 guard: ka_gochara_sweep excluded ✓", file=sys.stderr)

    # ── 4. Verify depends-on assets are lit on both charts ───────────────────
    for chart_id, label in CHARTS:
        cur.execute(
            """SELECT asset_id, state FROM asset_throughput
               WHERE chart_id = %s AND asset_id = ANY(%s)""",
            (chart_id, EXPECTED_DEPENDS),
        )
        rows_found = {r["asset_id"]: r["state"] for r in cur.fetchall()}
        not_lit = [dep for dep in EXPECTED_DEPENDS if rows_found.get(dep) != "lit"]
        if not_lit:
            print(f"[W6.1 WARN] {label}: depends-on assets not lit: {not_lit}", file=sys.stderr)
            print(f"[W6.1 WARN] W6.1 writer may fail or skip rows if deps missing.", file=sys.stderr)
        else:
            print(f"[W6.1] {label}: all 4 depends-on assets lit ✓", file=sys.stderr)

    # ── 5. Create build_runs for each chart ──────────────────────────────────
    run_ids: dict[str, tuple[str, str]] = {}
    for chart_id, label in CHARTS:
        # Reset target asset to dormant
        cur.execute(
            """INSERT INTO asset_throughput (chart_id, asset_id, state)
               VALUES (%s, %s, 'dormant')
               ON CONFLICT (chart_id, asset_id) WHERE chart_id IS NOT NULL
               DO UPDATE SET state = 'dormant', last_error = NULL""",
            (chart_id, TARGET_ASSET),
        )

        run_id = str(uuid.uuid4())
        cur.execute(
            """INSERT INTO build_runs
                 (id, chart_id, scope, scope_target, action, plan, state, triggered_by)
               VALUES (%s, %s, 'asset_set', NULL, 'rebuild', %s, 'planned', %s)""",
            (run_id, chart_id, json.dumps([TARGET_ASSET]), TRIGGERED_BY),
        )
        cur.execute(
            """INSERT INTO build_run_assets (run_id, asset_id, position, state)
               VALUES (%s, %s, 0, 'queued')""",
            (run_id, TARGET_ASSET),
        )
        run_ids[label] = (chart_id, run_id)
        print(f"[W6.1] created build_run for {label} ({chart_id[:8]}…): {run_id}", file=sys.stderr)

    conn.commit()
    conn.close()

    print(f"\nNATIVE_RUN_ID={run_ids['native'][1]}")
    print(f"ABHINANDAN_RUN_ID={run_ids['abhinandan'][1]}")
    print(
        "\nNext steps (run in platform/python-sidecar, one at a time, record wall-clock):",
        "  cd platform/python-sidecar",
        f"  time python3 -m pipeline.orchestrator.main --run-id {run_ids['native'][1]}",
        f"  time python3 -m pipeline.orchestrator.main --run-id {run_ids['abhinandan'][1]}",
        "\nSLO: target ≤20 min per chart. Record wall-clock in LEDGER.",
        sep="\n",
    )


if __name__ == "__main__":
    main()
