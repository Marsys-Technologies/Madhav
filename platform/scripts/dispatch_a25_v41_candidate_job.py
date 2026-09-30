"""
dispatch_a25_v41_candidate_job.py — Pravāha A2.5: dispatch the '4.1' gochara
candidate writer (ka_gochara_v4_41_candidate) as a governed build_run.

SHIPS IN THE PR BUT RUNS ONLY ON STEWARD GO. This script only STAGES:
  1. an idempotent asset_registry row for the new asset
     (ON CONFLICT (asset_id) DO NOTHING) — depends_on = '{}' and a live
     check that NO existing asset lists it in depends_on, so no existing DAG
     build ever schedules it;
  2. asset_throughput forced 'dormant' for the native's chart (per_chart
     scope), so the orchestrator treats the run as a genuine build;
  3. a build_runs row (scope='asset_set', action='rebuild') naming ONLY this
     asset, plus its build_run_assets row.

Execution happens separately, after steward go:

  gcloud run jobs execute brahma-build-pipeline-job --args=--run-id,<run_id>

Prints ONLY the run_id (UUID) to stdout on success, for shell capture.

TEARDOWN (exact):
  DELETE FROM build_run_assets WHERE run_id IN
    (SELECT id FROM build_runs WHERE triggered_by = 'pravaha-a25-v41-candidate');
  DELETE FROM build_runs WHERE triggered_by = 'pravaha-a25-v41-candidate';
  DELETE FROM asset_throughput WHERE asset_id = 'ka_gochara_v4_41_candidate';
  DELETE FROM asset_registry   WHERE asset_id = 'ka_gochara_v4_41_candidate';
  -- candidate rows themselves (generation '4.1' only — never 'v1'/'3.0'):
  DELETE FROM kala_gochara_windows   WHERE generation = '4.1';
  DELETE FROM kala_gochara_contacts  WHERE generation = '4.1';
  DELETE FROM kala_gochara_coverage  WHERE generation = '4.1';
  DELETE FROM kala_gochara_publication WHERE generation = '4.1';

Usage:
  cd <repo-root>/platform
  python3 scripts/dispatch_a25_v41_candidate_job.py          # stages + prints run_id
  python3 scripts/dispatch_a25_v41_candidate_job.py --help   # this text
"""
from __future__ import annotations

import json
import os
import sys
import uuid

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
# existing DAG build ever schedules it. Idempotent: ON CONFLICT DO NOTHING.
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
    '[1998-01-01, 2026-04-18). depends_on = ''{}'' and nothing depends on '
    'it: no existing DAG build ever schedules it; it runs ONLY via a '
    'steward-dispatched asset_set build_run.',
    'postgres_table', 'kala_gochara_windows',
    'SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation=''4.1''',
    'SELECT pg_total_relation_size(''kala_gochara_windows'')',
    0, 'per_chart', true, true, true,
    7200,
    'Kāla', 'L3', 'CURRENT', 'data',
    '{}'::text[]
) ON CONFLICT (asset_id) DO NOTHING
"""


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

    cur.execute(REGISTRY_INSERT)
    cur.execute(
        "SELECT depends_on FROM asset_registry WHERE asset_id = %s",
        (ASSET_ID,),
    )
    row = cur.fetchone()
    if row is None:
        conn.close()
        raise RuntimeError(f"asset_registry insert for {ASSET_ID} did not land")
    if row["depends_on"]:
        conn.close()
        raise RuntimeError(
            f"{ASSET_ID}.depends_on is {row['depends_on']}, expected '{{}}' — "
            "a pre-existing row with dependencies would let DAG builds "
            "schedule it; investigate before dispatching")

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
             (id, chart_id, scope, scope_target, action, plan, state, triggered_by)
           VALUES (%s, %s, 'asset_set', NULL, 'rebuild', %s, 'planned', %s)""",
        (run_id, CHART_ID, json.dumps([ASSET_ID]), TRIGGERED_BY),
    )
    cur.execute(
        """INSERT INTO build_run_assets (run_id, asset_id, position, state)
           VALUES (%s, %s, 0, 'queued')""",
        (run_id, ASSET_ID),
    )
    conn.commit()
    conn.close()
    print(f"[dispatch] staged A2.5 '4.1' candidate build_run {run_id} for "
          f"asset {ASSET_ID} on chart {CHART_ID}; execute on steward go via "
          f"`gcloud run jobs execute brahma-build-pipeline-job "
          f"--args=--run-id,{run_id}`", file=sys.stderr)
    print(run_id, flush=True)


if __name__ == "__main__":
    if any(a in ("-h", "--help") for a in sys.argv[1:]):
        print(__doc__)
        sys.exit(0)
    main()
