"""
dispatch_a25_v41_candidate_job.py — Pravāha A2.5: dispatch the '4.1' gochara
candidate writer (ka_gochara_v4_41_candidate) as a governed build_run, on the
frozen-manifest pattern of dispatch_frozen_rebuild.py.

SHIPS IN THE PR BUT RUNS ONLY ON STEWARD GO. This script only STAGES:
  1. an idempotent asset_registry row for the new asset
     (ON CONFLICT (asset_id) DO NOTHING) with is_active = FALSE — matching
     the seed (scripts/seed/asset_registry_seed.ts) so the asset is INERT to
     all planners: runPreparation selects WHERE is_active = true
     (src/lib/build/runPreparation.ts:183) and recalibrationEnqueue selects
     is_active = true AND has_writer = true
     (src/lib/build/recalibrationEnqueue.ts:141). depends_on = '{}' and a
     live check that NO existing asset lists it in depends_on, so no existing
     DAG build ever schedules it;
  2. the asset_registry row's is_active flipped TRUE and back to FALSE inside
     the ONE database transaction that also stages the run (UPDATE true; …
     staging …; UPDATE false; COMMIT) — no other session ever observes
     is_active=true (READ COMMITTED), so no concurrent full build can pick
     the asset up in the staging window. _load_candidate
     (dispatch_frozen_rebuild.py:80) requires an active+has_writer row, which
     the same transaction sees. The runner never re-checks is_active at
     execution: runner.py restores all scheduling inputs from the frozen
     manifest and _verify_registry_still_matches_manifest compares only
     scope/depends_on/natural_key_partition/has_cowriters. A try/finally
     rollback is the belt for any failure before the commit. If this script
     is killed hard mid-transaction the transaction simply never commits;
     restore manually only if some other tooling changed the row:
       UPDATE asset_registry SET is_active = false
         WHERE asset_id = 'ka_gochara_v4_41_candidate';
  3. asset_throughput forced 'dormant' for the native's chart (per_chart
     scope), so the orchestrator treats the run as a genuine build;
  4. a build_runs row (scope='asset_set', scope_target=the asset,
     action='rebuild') naming ONLY this asset, carrying plan_manifest and
     plan_manifest_digest built by dispatch_frozen_rebuild.build_manifest
     ('nirmana-run-manifest/v1', sha256 of the canonical JSON — the same
     algorithm as src/app/api/cockpit/runs/route.ts) with the writer's
     expected_code_digest from src/generated/nirmana-writer-digests.json —
     runner.py's validate_frozen_run_manifest requires both columns;
  5. its build_run_assets row.

Execution happens separately, after steward go:

  gcloud run jobs execute brahma-build-pipeline-job --args=--run-id,<run_id>

Prints ONLY the run_id (UUID) to stdout on success, for shell capture.

TEARDOWN (--teardown): ONE transaction, chart/run-scoped, fail-closed —
  1. REFUSES when any of these holds (loudly, nothing deleted):
     * a kala_gochara_publication row for the PINNED chart at generation
       '4.1' has status 'published' (a published generation is immutable —
       plan §4.7/N-7);
     * kala_gochara_authority names '4.1' as the pinned chart's
       authoritative_generation (a SERVING generation is never torn down);
     * a build_runs row for this asset on the pinned chart is
       planned/running/paused (active execution — stop it first);
  2. then deletes, in one commit:
       DELETE FROM build_run_assets WHERE run_id IN
         (SELECT id FROM build_runs WHERE triggered_by = 'pravaha-a25-v41-candidate'
            AND chart_id = '<pinned>');
       DELETE FROM build_runs WHERE triggered_by = 'pravaha-a25-v41-candidate'
         AND chart_id = '<pinned>';
       DELETE FROM asset_throughput WHERE asset_id = 'ka_gochara_v4_41_candidate'
         AND chart_id = '<pinned>';
       -- candidate rows for the PINNED CHART ONLY, generation '4.1' only —
       -- never another chart's '4.1', never 'v1'/'3.0':
       DELETE FROM kala_gochara_windows   WHERE chart_id = '<pinned>' AND generation = '4.1';
       DELETE FROM kala_gochara_contacts  WHERE chart_id = '<pinned>' AND generation = '4.1';
       DELETE FROM kala_gochara_coverage  WHERE chart_id = '<pinned>' AND generation = '4.1';
       DELETE FROM kala_gochara_publication WHERE chart_id = '<pinned>' AND generation = '4.1';
  3. then, in the SAME transaction, the asset_registry row is LEFT IN PLACE
     (migration 1243 inserts it permanently — deleting it would fail the
     orchestrator's writer-gap preflight, runner.py:159–205, on EVERY build
     run) and RESTORED to its inert state:
       UPDATE asset_registry SET is_active = false
         WHERE asset_id = 'ka_gochara_v4_41_candidate';
     and verified field by field with _validate_registry_row (the row must
     exist and match EXPECTED_REGISTRY_ROW after teardown).

Usage:
  cd <repo-root>/platform
  python3 scripts/dispatch_a25_v41_candidate_job.py          # stages + prints run_id
  python3 scripts/dispatch_a25_v41_candidate_job.py --teardown  # refuse-or-teardown (above; keeps the registry row)
  python3 scripts/dispatch_a25_v41_candidate_job.py --help   # this text
"""
from __future__ import annotations

import json
import os
import sys
import uuid

from dispatch_frozen_rebuild import (
    _load_candidate,
    _load_writer_digest,
    build_manifest,
)

ASSET_ID = "ka_gochara_v4_41_candidate"
CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
TRIGGERED_BY = "pravaha-a25-v41-candidate"

_env_file = os.path.join(os.path.dirname(__file__), "..", ".env.local")
if os.path.exists(_env_file):
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

# The asset_registry row (steward condition 2): chart-scoped count_sql,
# depends_on = '{}' and nothing depends on it (verified live below), so no
# existing DAG build ever schedules it. is_active = FALSE — inert to all
# planners; the transient flip below is the only activation. Idempotent:
# ON CONFLICT DO NOTHING.
REGISTRY_INSERT = """
INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql,
    target_floor, scope, is_active, has_writer, has_substeps,
    writer_timeout_seconds,
    layer_name, layer_index, catalog_status, asset_kind,
    depends_on
) VALUES (
    'ka_gochara_v4_41_candidate',
    'kala',
    141,
    'Gocara-Pratijñā 4.1',
    'Gochara ''4.1'' Candidate (Pravāha A2.5)',
    'PRAVĀHA campaign A2.5: the ''4.1'' gochara CANDIDATE chain '
    '(step06 enumerate → candidate build → class context → windows '
    'projection, scripts/kala_gochara_cutover/) run inside the governed '
    'build pipeline, replacing the deleted bespoke Cloud Run job. '
    'Generation fixed ''4.1'' (candidate only — never serving/published, '
    'never flipped by this asset); horizon fixed '
    '[1998-01-01, 2026-04-18). is_active = false: inert to all planners; '
    'activated only transiently by the steward dispatch. depends_on = '
    '''{}'' and nothing depends on it: no existing DAG build ever '
    'schedules it; it runs ONLY via a steward-dispatched asset_set '
    'build_run.',
    'postgres_table', 'kala_gochara_windows',
    'SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation=''4.1''',
    'SELECT pg_total_relation_size(''kala_gochara_windows'')',
    0, 'per_chart', false, true, true,
    7200,
    'Kāla', 'L3', 'CURRENT', 'data',
    '{}'::text[]
) ON CONFLICT (asset_id) DO NOTHING
"""

# ASTRA A2.5 A10: the shape a registry row for this asset MUST have before
# staging. ON CONFLICT DO NOTHING preserves a pre-existing (e.g. seeded) row,
# so the insert alone proves nothing — validate the landed row field by field.
# A seeded default writer_timeout_seconds=600 would silently cap this
# two-hour job at ten minutes (the runner reads the registry timeout).
EXPECTED_REGISTRY_ROW = {
    "scope": "per_chart",
    "is_active": False,
    "has_writer": True,
    "has_substeps": True,
    "writer_timeout_seconds": 7200,
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


# A4: candidate-row teardown, chart/run-scoped, ONE transaction, fail-closed.
# The DELETE list is executed only after every refusal check passes. The
# asset_registry row is NOT deleted — migration 1243 inserts it permanently;
# teardown only restores its inert state (is_active = false) and verifies it
# with _validate_registry_row in the same transaction.
TEARDOWN_DELETES = (
    # build bookkeeping for THIS asset on THIS chart staged by THIS dispatch
    """DELETE FROM build_run_assets WHERE run_id IN
         (SELECT id FROM build_runs WHERE triggered_by = %s
            AND chart_id = %s)""",
    "DELETE FROM build_runs WHERE triggered_by = %s AND chart_id = %s",
    "DELETE FROM asset_throughput WHERE asset_id = %s AND chart_id = %s",
    # candidate rows for the PINNED CHART ONLY, generation '4.1' only —
    # never another chart's '4.1', never 'v1'/'3.0'
    "DELETE FROM kala_gochara_windows   WHERE chart_id = %s AND generation = '4.1'",
    "DELETE FROM kala_gochara_contacts  WHERE chart_id = %s AND generation = '4.1'",
    "DELETE FROM kala_gochara_coverage  WHERE chart_id = %s AND generation = '4.1'",
    "DELETE FROM kala_gochara_publication WHERE chart_id = %s AND generation = '4.1'",
)


def teardown() -> None:
    import psycopg
    import psycopg.rows

    database_url = os.environ["DATABASE_URL"]
    conn = psycopg.connect(database_url, row_factory=psycopg.rows.dict_row)
    conn.autocommit = False
    cur = conn.cursor()
    try:
        # Refusal 1: a PUBLISHED '4.1' manifest for the pinned chart is
        # immutable (plan §4.7/N-7) — never torn down.
        cur.execute(
            """SELECT manifest_id, status FROM kala_gochara_publication
               WHERE chart_id = %s AND generation = '4.1'
                 AND status = 'published'""",
            (CHART_ID,),
        )
        published = cur.fetchone()
        if published:
            raise RuntimeError(
                f"teardown refused: kala_gochara_publication has a PUBLISHED "
                f"'4.1' manifest {published['manifest_id']} for chart "
                f"{CHART_ID} — a published generation is immutable")

        # Refusal 2: a SERVING generation is never torn down.
        cur.execute(
            """SELECT authoritative_generation FROM kala_gochara_authority
               WHERE chart_id = %s""",
            (CHART_ID,),
        )
        authority = cur.fetchone()
        if authority and authority["authoritative_generation"] == "4.1":
            raise RuntimeError(
                f"teardown refused: kala_gochara_authority names '4.1' as the "
                f"authoritative_generation for chart {CHART_ID} — a serving "
                "generation is never torn down")

        # Refusal 3: active execution for this asset on this chart — stop it
        # first; tearing down underneath a running build corrupts the run.
        cur.execute(
            """SELECT id, state FROM build_runs
               WHERE chart_id = %s AND scope = 'asset_set'
                 AND scope_target = %s
                 AND state IN ('planned', 'running', 'paused')""",
            (CHART_ID, ASSET_ID),
        )
        active = cur.fetchall()
        if active:
            raise RuntimeError(
                f"teardown refused: active build_runs {[(str(r['id']), r['state']) for r in active]} "
                f"for asset {ASSET_ID} on chart {CHART_ID} — stop active "
                "execution first")

        for sql in TEARDOWN_DELETES:
            if "build_run_assets" in sql or "FROM build_runs" in sql:
                cur.execute(sql, (TRIGGERED_BY, CHART_ID))
            elif "asset_throughput" in sql:
                cur.execute(sql, (ASSET_ID, CHART_ID))
            else:
                cur.execute(sql, (CHART_ID,))
        # The asset_registry row is permanent (migration 1243) and must NOT
        # be deleted — the orchestrator's writer-gap preflight
        # (runner.py:159–205, enforce) fails every build run if it is
        # missing. Restore its inert state and verify the landed row field
        # by field in the same transaction.
        cur.execute(
            "UPDATE asset_registry SET is_active = false WHERE asset_id = %s",
            (ASSET_ID,),
        )
        _validate_registry_row(cur)
        conn.commit()
    except Exception:
        conn.rollback()
        conn.close()
        raise
    conn.close()
    print(f"[teardown] removed staged run bookkeeping and ALL '4.1' "
          f"candidate rows for chart {CHART_ID}; asset_registry row kept and "
          f"restored to inert (is_active=false) — one transaction",
          file=sys.stderr)


def main() -> None:
    import psycopg
    import psycopg.rows

    database_url = os.environ["DATABASE_URL"]
    conn = psycopg.connect(database_url, row_factory=psycopg.rows.dict_row)
    conn.autocommit = False
    cur = conn.cursor()

    # Steward condition 2, second half: NOTHING may depend on this asset, or
    # an existing DAG build could schedule it. Fail before staging anything.
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
        # A10: the insert is ON CONFLICT DO NOTHING — validate the LANDED
        # row (pre-existing or new) field by field before staging anything.
        _validate_registry_row(cur)
    except Exception:
        conn.rollback()
        conn.close()
        raise

    run_id = None
    try:
        # ONE transaction for the whole staging (steward refinement
        # M20260930T203925-f792): the is_active flip TRUE → staging → flip
        # FALSE → single COMMIT, so no other session ever observes
        # is_active=true (READ COMMITTED) and no concurrent full build can
        # pick the asset up in the staging window. _load_candidate requires
        # is_active = true AND has_writer = true
        # (dispatch_frozen_rebuild.py:80) — the same transaction sees it.
        cur.execute(
            "UPDATE asset_registry SET is_active = true WHERE asset_id = %s",
            (ASSET_ID,),
        )
        candidate = _load_candidate(cur, ASSET_ID)
        manifest, manifest_digest = build_manifest(
            chart_id=CHART_ID,
            candidate=candidate,
            expected_code_digest=_load_writer_digest(ASSET_ID),
        )

        # Force dormant (per_chart scope) so the orchestrator treats this as a
        # genuine build, not a no-op over an already-lit asset (D-1.5b/D-1.6
        # precedent).
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
        # Restore inertness in the SAME transaction, then the one commit.
        cur.execute(
            "UPDATE asset_registry SET is_active = false WHERE asset_id = %s",
            (ASSET_ID,),
        )
        conn.commit()
    except Exception:
        # Belt for any failure before the commit: nothing staged, nothing
        # flipped — the transaction never lands.
        conn.rollback()
        conn.close()
        raise
    conn.close()

    print(f"[dispatch] staged A2.5 '4.1' candidate build_run {run_id} for "
          f"asset {ASSET_ID} on chart {CHART_ID} (manifest digest "
          f"{manifest_digest}); asset_registry.is_active restored to false. "
          f"Execute on steward go via `gcloud run jobs execute "
          f"brahma-build-pipeline-job --args=--run-id,{run_id}`",
          file=sys.stderr)
    print(run_id, flush=True)


if __name__ == "__main__":
    if any(a in ("-h", "--help") for a in sys.argv[1:]):
        print(__doc__)
        sys.exit(0)
    if "--teardown" in sys.argv[1:]:
        teardown()
    else:
        main()
