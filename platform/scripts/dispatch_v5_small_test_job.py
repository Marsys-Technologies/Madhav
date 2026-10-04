"""
dispatch_v5_small_test_job.py — Pravāha C37: steward-run dispatch of a SMALL
TEST build of asset ka_gochara_v5, modelled on dispatch_a25_v41_candidate_job.py
(same frozen-manifest staging pattern).

SHIPS IN THE PR BUT RUNS ONLY ON STEWARD GO — and only when BOTH
--i-am-steward AND --after-settled-1 are passed (the protected window's
settled-1 precondition). Without both flags the script refuses (exit 2)
before touching anything.

PRECONDITION: migration 1304 (PR 3101) has been applied — it is the ONLY source
of the ka_gochara_v5 registry row's small-test shape (has_substeps true,
writer_timeout_seconds 7200, depends_on [ga_positions, ga_dashas], the
ka_gochara_eval_window counter). This script does NOT insert or alter that row;
it VALIDATES it field by field and refuses on any difference or if the row is
absent (A2 review: the old INSERT carried the pre-1304 shape and could never
fire against a real row).

This script only STAGES, in ONE database transaction (no other session ever
observes is_active=true under READ COMMITTED):
  1. the registry row is read and validated against EXPECTED_REGISTRY_ROW (the
     1304 values), plus a live check that NO existing asset lists ka_gochara_v5
     in depends_on, so no DAG build ever schedules it as a dependency;
  2. is_active flipped TRUE and back to FALSE inside the ONE transaction that
     also stages the run (UPDATE true; … staging …; UPDATE false; COMMIT).
     _load_candidate (dispatch_frozen_rebuild.py:80) requires an active+has_writer
     row, which the same transaction sees. A try/finally rollback is the belt for
     any failure before the commit;
  3. asset_throughput forced 'dormant' for the PINNED chart (per_chart scope), so
     the orchestrator treats the run as a genuine build;
  4. a build_runs row (scope='asset_set', scope_target=the asset, action='rebuild',
     triggered_by='gochara-v5-small-test') carrying plan_manifest and
     plan_manifest_digest: build_manifest ('nirmana-run-manifest/v1') PLUS the
     slice marker merged into the manifest BEFORE the sha256 digest is computed.
     The manifest's asset depends_on is the registry's depends_on (the runner
     requires the two to be equal);
  5. its build_run_assets row.

THE SLICE MARKER is the writer's contract, not a copy of it: plan_manifest[
"gochara_v5_test_slice"] = {"schema": "gochara_v5_test_slice/1", "run":
"all_classes_1y" | "one_class_full", "horizon": [<start>, <end>], "classes":
[...]} — exactly those four fields. Before ANY database connection the built
marker is passed through the WRITER's own validator
(ka_gochara_v5._validate_test_slice, imported from the sidecar), so a marker the
writer would refuse never reaches a staged run:
  * horizons are tz-aware ISO timestamps (a naive timestamp is refused; they are
    stored normalised to UTC). one_class_full defaults to the writer's full
    DEFAULT_HORIZON; all_classes_1y needs --horizon-start/--horizon-end (≤ 366 days,
    inside DEFAULT_HORIZON);
  * classes come from the writer's SCORED_CLASSES (26): --classes all (the default
    for all_classes_1y) or a comma list; one_class_full takes exactly one class.

The chart is the pinned canonical chart 482012f1-710e-4a25-994a-93821f5871aa
ONLY — there is no chart argument; any other chart is refused by construction.
The DSN comes from DATABASE_URL only: never on argv, never printed.

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
      --run all_classes_1y --horizon-start 2025-04-01T00:00:00+00:00 \
      --horizon-end 2026-04-01T00:00:00+00:00 [--classes all] [--dry-run]
  python3 scripts/dispatch_v5_small_test_job.py --i-am-steward --after-settled-1 \
      --run one_class_full --classes <one scored class> [--dry-run]
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

# The shape the ka_gochara_v5 registry row MUST have before staging — the values migration 1304
# (PR 3101) lands, compared field by field. depends_on is compared in 1304's order.
EXPECTED_COUNT_SQL = ("SELECT COUNT(*) FROM ka_gochara_eval_window "
                      "WHERE chart_id=$1 AND generation='5.0'")
EXPECTED_REGISTRY_ROW = {
    "scope": "per_chart",
    "is_active": False,
    "has_writer": True,
    "has_substeps": True,
    "writer_timeout_seconds": 7200,
    "depends_on": ["ga_positions", "ga_dashas"],
    "target_table": "ka_gochara_eval_window",
    "count_sql": EXPECTED_COUNT_SQL,
    "target_floor": 0,
    "estimated_seconds": None,
}


def _validate_registry_row(cur) -> None:
    cur.execute(
        """SELECT scope, is_active, has_writer, has_substeps, writer_timeout_seconds,
                  depends_on, target_table, count_sql, target_floor, estimated_seconds
           FROM asset_registry WHERE asset_id = %s""",
        (ASSET_ID,),
    )
    row = cur.fetchone()
    if row is None:
        raise RuntimeError(
            f"asset_registry has no {ASSET_ID} row — migration 1243 (row) and 1304 (small-test "
            "shape) must be applied before this dispatch; this script never inserts it")
    for field, expected in EXPECTED_REGISTRY_ROW.items():
        actual = row[field]
        if field == "depends_on":
            actual = list(actual or [])
        if actual != expected:
            raise RuntimeError(
                f"{ASSET_ID}.{field} is {actual!r}, expected {expected!r} — the registry row "
                "is not in the migration-1304 small-test shape; a non-conforming row would "
                "change how this build is scheduled or budgeted (apply 1304, do not edit by hand)")


SLICE_MARKER_SCHEMA = "gochara_v5_test_slice/1"
SLICE_RUNS = ("all_classes_1y", "one_class_full")


def _writer():
    """The sidecar writer module (its slice contract is the single source of truth)."""
    sidecar = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "python-sidecar"))
    if sidecar not in sys.path:
        sys.path.insert(0, sidecar)
    try:
        import pipeline.orchestrator.writers.ka_gochara_v5 as writer
    except Exception as exc:  # an environment without the sidecar deps cannot validate: refuse, never skip
        raise RuntimeError(
            f"cannot import the ka_gochara_v5 writer to validate the slice marker ({exc!r}); "
            "run this from an environment with the sidecar dependencies") from exc
    return writer


def _utc_iso(label: str, raw: str) -> str:
    try:
        value = datetime.datetime.fromisoformat(raw)
    except ValueError:
        raise RuntimeError(f"{label} {raw!r} is not an ISO 8601 timestamp")
    if value.tzinfo is None:
        raise RuntimeError(
            f"{label} {raw!r} has no timezone — pass a tz-aware timestamp such as "
            "2025-04-01T00:00:00+00:00; an unstated zone is never guessed")
    return value.astimezone(datetime.timezone.utc).isoformat()


def build_slice_marker(*, run: str, classes: str | None = None,
                       horizon_start: str | None = None, horizon_end: str | None = None) -> dict:
    """The slice marker merged into plan_manifest under 'gochara_v5_test_slice', validated by the
    WRITER's own _validate_test_slice before it is returned (a TestSliceRefusal propagates by
    name). classes: None / 'all' = every scored class (all_classes_1y), else a comma list. Horizons
    are tz-aware ISO timestamps, stored in UTC; one_class_full defaults to the full DEFAULT_HORIZON."""
    writer = _writer()
    if run not in SLICE_RUNS or tuple(writer.TEST_SLICE_RUNS) != SLICE_RUNS:
        raise RuntimeError(f"--run must be one of {SLICE_RUNS} (writer: {tuple(writer.TEST_SLICE_RUNS)}), got {run!r}")
    if classes is None:
        if run == "one_class_full":
            raise RuntimeError("--classes must name exactly one scored class for run 'one_class_full'")
        names = list(writer.SCORED_CLASSES)
    elif classes.strip() == "all":
        names = list(writer.SCORED_CLASSES)
    else:
        names = [c.strip() for c in classes.split(",") if c.strip()]
        if not names:
            raise RuntimeError("--classes must be 'all' or a non-empty comma-separated list")
    if horizon_start is None and horizon_end is None and run == "one_class_full":
        start, end = (x.astimezone(datetime.timezone.utc).isoformat() for x in writer.DEFAULT_HORIZON)
    elif horizon_start is None or horizon_end is None:
        raise RuntimeError("--horizon-start and --horizon-end are both required "
                           "(only one_class_full may omit both, meaning the full DEFAULT_HORIZON)")
    else:
        start, end = _utc_iso("horizon_start", horizon_start), _utc_iso("horizon_end", horizon_end)
    marker = {"schema": SLICE_MARKER_SCHEMA, "run": run, "horizon": [start, end], "classes": names}
    writer._validate_test_slice(marker)
    return marker


def build_small_test_manifest(*, candidate, slice_marker: dict) -> tuple[dict, str]:
    """The frozen asset_set manifest PLUS the slice marker, digested once."""
    manifest, _ = build_manifest(
        chart_id=CHART_ID,
        candidate=candidate,
        expected_code_digest=_load_writer_digest(ASSET_ID),
    )
    manifest["gochara_v5_test_slice"] = slice_marker
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
    p.add_argument("--run", required=True, choices=SLICE_RUNS,
                   help="the small-test run identity: all_classes_1y or one_class_full")
    p.add_argument("--classes", default=None,
                   help="'all' (default for all_classes_1y) or a comma-separated list of scored "
                        "classes; one_class_full takes exactly one")
    p.add_argument("--horizon-start", default=None,
                   help="tz-aware ISO timestamp, e.g. 2025-04-01T00:00:00+00:00 "
                        "(required for all_classes_1y; one_class_full defaults to the full horizon)")
    p.add_argument("--horizon-end", default=None, help="tz-aware ISO timestamp (see --horizon-start)")
    p.add_argument("--dry-run", action="store_true",
                   help="run the same staging transaction, ROLL BACK, print the staged plan")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    if not (args.i_am_steward and args.after_settled_1):
        print("REFUSAL: this dispatch runs only on steward go AFTER settled-1 — "
              "pass BOTH --i-am-steward and --after-settled-1", file=sys.stderr)
        sys.exit(2)
    try:
        slice_marker = build_slice_marker(
            run=args.run, classes=args.classes,
            horizon_start=args.horizon_start, horizon_end=args.horizon_end)
    except Exception as exc:  # RuntimeError or the writer's TestSliceRefusal: nothing touched yet
        print(f"REFUSAL: {exc}", file=sys.stderr)
        sys.exit(2)

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
            f"{ASSET_ID} in depends_on — nothing may depend on this asset "
            "so no existing DAG build ever schedules it")

    try:
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
