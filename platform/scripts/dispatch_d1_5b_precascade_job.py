"""
dispatch_d1_5b_precascade_job.py — create a build_runs row for the remaining
non-lit assets, so the Cloud Run job (brahma-build-pipeline-job) can execute it
INSIDE GCP with a stable direct Cloud SQL connection.

Root cause of the repeated local-rebuild failures (D-1.5b, 2026-07-15): the
laptop cloud-sql-proxy path is unreliable — the proxy intermittently drops, and
bo_samskara's ~2-min-per-ayanamsha Vertex AI embedding loop holds the connection
idle long enough that a proxy drop mid-embed kills the whole run, restarting
embedding from scratch. The product code is already fully resilient (keepalives,
idle-txn timeout disabled, batch-level embed tolerance) and completes fine in
production via the Cloud Run job. This script prepares the run row; the caller
then dispatches the job with `gcloud run jobs execute ... --args=^:^--run-id:<id>`.

Prints ONLY the run_id (UUID) to stdout on success, for shell capture.

Usage (Cloud SQL Auth Proxy on 5433 — only needed for THIS quick insert, not the
build itself which runs in GCP):
  cd <repo-root>/platform
  python -m scripts.dispatch_d1_5b_precascade_job
"""
from __future__ import annotations

import json
import os
import sys
import uuid

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
TRIGGERED_BY = "d1-5b-precascade-cloudrun-job"

_env_file = os.path.join(os.path.dirname(__file__), "..", ".env.local")
if os.path.exists(_env_file):
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

_sidecar = os.path.join(os.path.dirname(__file__), "..", "python-sidecar")
if _sidecar not in sys.path:
    sys.path.insert(0, _sidecar)


def _topo_sorted_non_lit(cur) -> list[str]:
    """Non-'lit' writer-backed assets for CHART_ID, topo-sorted via
    asset_registry.depends_on (Kahn's algorithm restricted to the target set)."""
    cur.execute(
        "SELECT asset_id FROM asset_throughput WHERE chart_id = %s AND state != 'lit'",
        (CHART_ID,),
    )
    targets = {r["asset_id"] for r in cur.fetchall()}
    if not targets:
        return []
    cur.execute("SELECT asset_id, COALESCE(depends_on, '{}') AS deps FROM asset_registry")
    all_deps = {r["asset_id"]: list(r["deps"] or []) for r in cur.fetchall()}

    in_degree = {a: 0 for a in targets}
    edges: dict[str, list[str]] = {a: [] for a in targets}
    for a in targets:
        for dep in all_deps.get(a, []):
            if dep in targets:
                edges[dep].append(a)
                in_degree[a] += 1

    from collections import deque
    queue = deque(sorted(a for a in targets if in_degree[a] == 0))
    ordered: list[str] = []
    while queue:
        node = queue.popleft()
        ordered.append(node)
        for nxt in sorted(edges[node]):
            in_degree[nxt] -= 1
            if in_degree[nxt] == 0:
                queue.append(nxt)
    if len(ordered) != len(targets):
        raise RuntimeError(f"cycle/unresolved among target assets: {targets - set(ordered)}")
    return ordered


def main() -> None:
    import psycopg
    import psycopg.rows
    from pipeline.orchestrator.db import db_url

    conn = psycopg.connect(db_url(), row_factory=psycopg.rows.dict_row)
    conn.autocommit = False
    cur = conn.cursor()

    assets = _topo_sorted_non_lit(cur)
    if not assets:
        print("ALL_LIT", flush=True)
        return

    # Reset any error-state target to dormant so the runner re-executes it.
    for asset_id in assets:
        cur.execute(
            """INSERT INTO asset_throughput (chart_id, asset_id, state)
               VALUES (%s, %s, 'dormant')
               ON CONFLICT (chart_id, asset_id) WHERE chart_id IS NOT NULL
               DO UPDATE SET state = 'dormant', rows_written = 0, last_error = NULL""",
            (CHART_ID, asset_id),
        )

    run_id = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO build_runs
             (id, chart_id, scope, scope_target, action, plan, state, triggered_by)
           VALUES (%s, %s, 'asset_set', NULL, 'build', %s, 'planned', %s)""",
        (run_id, CHART_ID, json.dumps(assets), TRIGGERED_BY),
    )
    for position, asset_id in enumerate(assets):
        cur.execute(
            """INSERT INTO build_run_assets (run_id, asset_id, position, state)
               VALUES (%s, %s, %s, 'queued')""",
            (run_id, asset_id, position),
        )
    conn.commit()
    conn.close()
    # stderr: human detail; stdout: run_id only (for shell capture)
    print(f"[dispatch] created build_run {run_id} with {len(assets)} assets: {assets}", file=sys.stderr)
    print(run_id, flush=True)


if __name__ == "__main__":
    main()
