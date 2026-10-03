"""
dispatch_v5_small_test_job.py — Pravāha C37: steward-run dispatch of a SMALL
TEST build of asset ka_gochara_v5, modelled exactly on
dispatch_a25_v41_candidate_job.py (same frozen-manifest staging pattern).

SHIPS IN THE PR BUT RUNS ONLY ON STEWARD GO — and only when BOTH
--i-am-steward AND --after-settled-1 are passed (the protected window's
settled-1 precondition). Without both flags the script refuses (exit 2)
before touching anything.

This script only STAGES, in ONE database transaction (no other session ever
observes is_active=true under READ COMMITTED):
  1. an idempotent asset_registry row for ka_gochara_v5
     (ON CONFLICT (asset_id) DO NOTHING) with is_active = FALSE — the same
     row migration 1243 inserts — validated field by field with
     _validate_registry_row (depends_on = '{}' and a live check that NO
     existing asset lists it in depends_on, so no DAG build ever schedules
     it);
  2. is_active flipped TRUE and back to FALSE inside the ONE transaction
     that also stages the run (UPDATE true; … staging …; UPDATE false;
     COMMIT). _load_candidate (dispatch_frozen_rebuild.py:80) requires an
     active+has_writer row, which the same transaction sees. A try/finally
     rollback is the belt for any failure before the commit;
  3. asset_throughput forced 'dormant' for the PINNED chart (per_chart
     scope), so the orchestrator treats the run as a genuine build;
  4. a build_runs row (scope='asset_set', scope_target=the asset,
     action='rebuild', triggered_by='gochara-v5-small-test') carrying
     plan_manifest and plan_manifest_digest: build_manifest
     ('nirmana-run-manifest/v1') PLUS a small-test slice marker (see
     build_slice_marker) merged into the manifest BEFORE the sha256 digest
     is computed;
  5. its build_run_assets row.

The slice marker tells the (separately governed) writer that this run is a
SMALL TEST: test_slice=true, classes (a list, or 'all'), horizon_start,
horizon_end. Stream A defines how the writer reads it — the marker
construction is deliberately ONE small function (build_slice_marker) so it
can be adjusted in one place.

The chart is the pinned canonical chart 482012f1-710e-4a25-994a-93821f5871aa
ONLY — there is no chart argument; any other chart is refused by
construction. The DSN comes from DATABASE_URL only: never on argv, never
printed.

--dry-run runs the SAME staging transaction but ROLLS BACK instead of
committing and prints the staged plan (run row + manifest) as JSON — nothing
is written.

Execution happens separately, after steward go:

  gcloud run jobs execute brahma-build-pipeline-job --args=--run-id,<run_id>

Teardown is a SEPARATE script (C38, teardown_v5_small_test_job.py) — this
script never deletes anything.

Usage:
  cd <repo-root>/platform
  python3 scripts/dispatch_v5_small_test_job.py --i-am-steward --after-settled-1 \
      [--classes all|class1,class2] --horizon-start YYYY-MM-DD --horizon-end YYYY-MM-DD [--dry-run]
  python3 scripts/dispatch_v5_small_test_job.py --help
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys
import uuid

from dispatch_frozen_rebuild import (
    _canonical_json,
    _load_candidate,
    _load_writer_digest,
    build_manifest,
)

ASSET_ID = "ka_gochara_v5"
CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
TRIGGERED_BY = "gochara-v5-small-test"

_env_file = os.path.join(os.path.dirname(__file__), "..", ".env.local")
if os.path.exists(_env_file):
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

# The same asset_registry row migration 1243 lands (28-column seed order),
# idempotent: ON CONFLICT (asset_id) DO NOTHING. is_active = FALSE — inert to
# all planners; the transient flip below is the only activation.
REGISTRY_INSERT = """
INSERT INTO asset_registry (
    asset_id, layer, sort_order, sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql, target_floor,
    expected_volume_formula, expected_volume_inputs, volume_explanation,
    depends_on, scope, is_active, estimated_seconds,
    asset_type, layer_name, layer_index, provides_apis, health_probe, catalog_status,
    asset_kind, has_writer, has_substeps, writer_timeout_seconds
) VALUES (
    'ka_gochara_v5',
    'kala',
    142,
    'Gocara-Pratijñā 5.0',
    'Gochara ''5.0'' Writer Skeleton (Pravāha A5.3, INERT)',
    'PRAVĀHA A5.3 INERT skeleton: registered WriterBase writer ka_gochara_v5 '
    '(@register, asset_id pinned, light shape) with a hard chart-scope '
    'refusal (only chart 482012f1-710e-4a25-994a-93821f5871aa admitted) and '
    'every execution path raising NotImplementedError pending steward pins '
    '3-7 (ruling M20261001T014547-357e pins 1-2). Never commits/rolls '
    'back/closes ctx.db_conn, opens no connection, writes no '
    'asset_throughput — no DB touch at all. Registration + inertness ONLY; '
    'the geometry/solver is a separate governed step.',
    'postgres_table', 'kala_gochara_windows',
    'SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation=''5.0''',
    'SELECT pg_total_relation_size(''kala_gochara_windows'')',
    0,
    NULL, NULL,
    'Placeholder surface for the pending ''5.0'' generation — the skeleton '
    'writes NOTHING (every path raises NotImplementedError), so the count '
    'stays 0 until steward pins 3-7 land and the geometry/solver is '
    'implemented under a later governed step.',
    '{}'::text[],
    'per_chart',
    false,
    NULL,
    'data', 'Kāla', 'L3',
    NULL, NULL, 'CURRENT',
    'data',
    true, false,
    600
) ON CONFLICT (asset_id) DO NOTHING
"""

# The shape the ka_gochara_v5 registry row MUST have before staging (the 1243
# row: has_substeps = false, the 600s timeout — NOT the A2.5 candidate's).
EXPECTED_REGISTRY_ROW = {
    "scope": "per_chart",
    "is_active": False,
    "has_writer": True,
    "has_substeps": False,
    "writer_timeout_seconds": 600,
    "depends_on": [],
}


def _validate_registry_row(cur) -> None:
    cur.execute(
        """SELECT scope, is_active, has_writer, has_substeps,
                  writer_timeout_seconds, depends_on
           FROM asset_registry WHERE asset_id = %s""",
        (ASSET_ID,),
    )
    row = cur.fetchone()
    if row is None:
        raise RuntimeError(f"asset_registry insert for {ASSET_ID} did not land")
    for field, expected in EXPECTED_REGISTRY_ROW.items():
        actual = row[field]
        if field == "depends_on":
            actual = list(actual or [])
        if actual != expected:
            raise RuntimeError(
                f"{ASSET_ID}.{field} is {actual!r}, expected {expected!r} — "
                "a pre-existing non-conforming registry row would change how "
                "this build is scheduled or budgeted; fix the row before "
                "dispatching")


def build_slice_marker(*, classes: str, horizon_start: str, horizon_end: str) -> dict:
    """The small-test slice marker merged into plan_manifest. ONE small
    function by design: Stream A defines how the writer reads it, so it can
    be adjusted here without touching the staging flow. classes is 'all' or
    a comma-separated list; the horizons are ISO dates."""
    for label, value in (("horizon_start", horizon_start), ("horizon_end", horizon_end)):
        try:
            datetime.date.fromisoformat(value)
        except ValueError:
            raise RuntimeError(f"{label} {value!r} is not an ISO date (YYYY-MM-DD)")
    if horizon_end <= horizon_start:
        raise RuntimeError(
            f"horizon_end {horizon_end!r} must be after horizon_start {horizon_start!r}")
    parsed: str | list[str]
    if classes == "all":
        parsed = "all"
    else:
        parsed = [c.strip() for c in classes.split(",") if c.strip()]
        if not parsed:
            raise RuntimeError("--classes must be 'all' or a non-empty comma-separated list")
    return {
        "test_slice": True,
        "classes": parsed,
        "horizon_start": horizon_start,
        "horizon_end": horizon_end,
    }


def build_small_test_manifest(*, candidate, slice_marker: dict) -> tuple[dict, str]:
    """The frozen asset_set manifest PLUS the slice marker, digested once."""
    manifest, _ = build_manifest(
        chart_id=CHART_ID,
        candidate=candidate,
        expected_code_digest=_load_writer_digest(ASSET_ID),
    )
    manifest["slice_marker"] = slice_marker
    digest = hashlib.sha256(_canonical_json(manifest).encode("utf-8")).hexdigest()
    return manifest, digest


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="dispatch_v5_small_test_job.py",
        description="Stage a SMALL TEST build_run of ka_gochara_v5 (steward only).")
    p.add_argument("--i-am-steward", action="store_true",
                   help="required: you are the steward, acting on native authority")
    p.add_argument("--after-settled-1", action="store_true",
                   help="required: the protected window's settled-1 precondition has passed")
    p.add_argument("--classes", default="all",
                   help="'all' (default) or a comma-separated list of event classes")
    p.add_argument("--horizon-start", required=True, help="ISO date YYYY-MM-DD")
    p.add_argument("--horizon-end", required=True, help="ISO date YYYY-MM-DD")
    p.add_argument("--dry-run", action="store_true",
                   help="run the same staging transaction, ROLL BACK, print the staged plan")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    if not (args.i_am_steward and args.after_settled_1):
        print("REFUSAL: this dispatch runs only on steward go AFTER settled-1 — "
              "pass BOTH --i-am-steward and --after-settled-1", file=sys.stderr)
        sys.exit(2)
    slice_marker = build_slice_marker(
        classes=args.classes, horizon_start=args.horizon_start, horizon_end=args.horizon_end)

    import psycopg
    import psycopg.rows

    database_url = os.environ["DATABASE_URL"]
    conn = psycopg.connect(database_url, row_factory=psycopg.rows.dict_row)
    conn.autocommit = False
    cur = conn.cursor()

    # NOTHING may depend on this asset, or an existing DAG build could
    # schedule it. Fail before staging anything.
    cur.execute(
        "SELECT asset_id FROM asset_registry WHERE %s = ANY(depends_on)",
        (ASSET_ID,),
    )
    dependents = [r["asset_id"] for r in cur.fetchall()]
    if dependents:
        conn.close()
        raise RuntimeError(
            f"dispatch refused: asset_registry rows {dependents} list "
            f"{ASSET_ID} in depends_on — the asset must stay dependency-free "
            "so no existing DAG build ever schedules it")

    try:
        cur.execute(REGISTRY_INSERT)
        _validate_registry_row(cur)
    except Exception:
        conn.rollback()
        conn.close()
        raise

    run_id = None
    try:
        # ONE transaction for the whole staging: the is_active flip TRUE →
        # staging → flip FALSE → single COMMIT (or, with --dry-run, one
        # ROLLBACK — the transaction never lands).
        cur.execute(
            "UPDATE asset_registry SET is_active = true WHERE asset_id = %s",
            (ASSET_ID,),
        )
        candidate = _load_candidate(cur, ASSET_ID)
        manifest, manifest_digest = build_small_test_manifest(
            candidate=candidate, slice_marker=slice_marker)

        # Force dormant (per_chart scope) so the orchestrator treats this as a
        # genuine build, not a no-op over an already-lit asset.
        cur.execute(
            """INSERT INTO asset_throughput (chart_id, asset_id, state)
               VALUES (%s, %s, 'dormant')
               ON CONFLICT (chart_id, asset_id) WHERE chart_id IS NOT NULL
               DO UPDATE SET state = 'dormant', rows_written = 0, last_error = NULL""",
            (CHART_ID, ASSET_ID),
        )

        run_id = str(uuid.uuid4())
        cur.execute(
            """INSERT INTO build_runs
                 (id, chart_id, scope, scope_target, action, state, plan,
                  plan_manifest, plan_manifest_digest, triggered_by)
               VALUES (%s, %s, 'asset_set', %s, 'rebuild', 'planned', %s::jsonb,
                       %s::jsonb, %s, %s)""",
            (run_id, CHART_ID, ASSET_ID, json.dumps([ASSET_ID]),
             json.dumps(manifest), manifest_digest, TRIGGERED_BY),
        )
        cur.execute(
            """INSERT INTO build_run_assets (run_id, asset_id, position, state)
               VALUES (%s, %s, 0, 'queued')""",
            (run_id, ASSET_ID),
        )
        # Restore inertness in the SAME transaction.
        cur.execute(
            "UPDATE asset_registry SET is_active = false WHERE asset_id = %s",
            (ASSET_ID,),
        )
        if args.dry_run:
            conn.rollback()
        else:
            conn.commit()
    except Exception:
        conn.rollback()
        conn.close()
        raise
    conn.close()

    plan = {
        "run_id": run_id,
        "chart_id": CHART_ID,
        "asset_id": ASSET_ID,
        "triggered_by": TRIGGERED_BY,
        "plan_manifest_digest": manifest_digest,
        "plan_manifest": manifest,
    }
    if args.dry_run:
        print(f"[dry-run] staged plan for a SMALL TEST build of {ASSET_ID} on chart "
              f"{CHART_ID} — ROLLED BACK, nothing written", file=sys.stderr)
        print(json.dumps(plan, indent=2, sort_keys=True), flush=True)
        return
    print(f"[dispatch] staged v5 SMALL TEST build_run {run_id} for asset "
          f"{ASSET_ID} on chart {CHART_ID} (manifest digest {manifest_digest}); "
          f"asset_registry.is_active restored to false. Execute on steward go "
          f"via `gcloud run jobs execute brahma-build-pipeline-job "
          f"--args=--run-id,{run_id}`",
          file=sys.stderr)
    print(run_id, flush=True)


if __name__ == "__main__":
    main()
