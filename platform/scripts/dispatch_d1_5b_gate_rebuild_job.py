"""
dispatch_d1_5b_gate_rebuild_job.py — D-1.5b's mandated FULL L1->L5 rebuild
for Gate B (BRIEF_D1_5B.md §G: "this wave adds new chalit/AV fact categories
that feed MSR + L3, so §8.2 trigger (a) applies... FULL L1->L5").

Unlike dispatch_d1_5b_precascade_job.py (which only rebuilds assets already
in a non-'lit' state), this script resets EVERY chart-scoped asset for
Abhisek's chart (482012f1) back to 'dormant' -- L1 through L5 (ga_*, bo_*,
ka_*, mi_*, ph_*; brahmagyan/bg_* is chart-independent reference data and is
left untouched) -- so the full closure rebuilds fresh against cycle-1+cycle-2's
new writer code (B-1 chalit/cusps, B-2 bhava-bala/AV, B-5 shadbala-ratio/D2-hora,
B-3's new bo_sudarshana asset). Abhinandan (1c826d5a) is NOT rebuilt per the brief.

Runs via the Cloud Run job (brahma-build-pipeline-job) with a direct in-GCP
Cloud SQL connection -- the local laptop proxy path proved unreliable for
long-running builds this wave (see STATE_D-1.5b.md precascade_rebuild).

Prints ONLY the run_id (UUID) to stdout on success, for shell capture.

Usage (Cloud SQL Auth Proxy on 5433 -- only needed for THIS quick insert):
  cd <repo-root>/platform
  python -m scripts.dispatch_d1_5b_gate_rebuild_job
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from collections import deque

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
TRIGGERED_BY = "d1-5b-gate-b-full-rebuild"

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


def _full_chart_scoped_plan(cur) -> list[str]:
    """Every non-brahmagyan asset_registry row is a candidate for this chart
    (asset_throughput rows already present for it, PLUS any new asset -- e.g.
    B-3's bo_sudarshana -- that has no row yet), topo-sorted via depends_on
    (Kahn's algorithm). Assets outside this chart-scoped set (e.g. gated
    transit-sidecar assets not yet buildable) are excluded by only including
    what's already reachable in asset_throughput OR newly registered with a
    L1-only or already-satisfiable dependency footprint."""
    cur.execute(
        "SELECT asset_id FROM asset_throughput WHERE chart_id = %s",
        (CHART_ID,),
    )
    already_tracked = {r["asset_id"] for r in cur.fetchall()}

    cur.execute(
        "SELECT asset_id, layer, COALESCE(depends_on, '{}') AS deps FROM asset_registry WHERE layer != 'brahmagyan'"
    )
    all_rows = cur.fetchall()
    all_deps = {r["asset_id"]: list(r["deps"] or []) for r in all_rows}
    all_ids = {r["asset_id"] for r in all_rows}

    # Target set = every already-tracked asset for this chart, PLUS any new
    # registry asset whose full dependency closure is already tracked (i.e.
    # buildable now) -- this picks up bo_sudarshana without dragging in
    # gated/not-yet-buildable assets like the transit-sidecar-blocked ones.
    targets = set(already_tracked) & all_ids
    changed = True
    while changed:
        changed = False
        for asset_id in all_ids - targets:
            deps = all_deps.get(asset_id, [])
            l1_plus_deps = [d for d in deps if d in all_ids]
            if l1_plus_deps and all(d in targets or d in already_tracked for d in l1_plus_deps):
                # only pull in a new (not-yet-tracked) asset if ALL its
                # in-scope deps are already tracked for this chart
                if asset_id not in already_tracked:
                    targets.add(asset_id)
                    changed = True

    if not targets:
        return []

    in_degree = {a: 0 for a in targets}
    edges: dict[str, list[str]] = {a: [] for a in targets}
    for a in targets:
        for dep in all_deps.get(a, []):
            if dep in targets:
                edges[dep].append(a)
                in_degree[a] += 1

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

    assets = _full_chart_scoped_plan(cur)
    if not assets:
        print("NOTHING_TO_BUILD", flush=True)
        return

    # Force EVERY target asset -> dormant, regardless of current state
    # ('lit' included) -- this is a FULL rebuild, not a stale-only cascade.
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
    print(f"[dispatch] created FULL rebuild build_run {run_id} with {len(assets)} assets: {assets}", file=sys.stderr)
    print(run_id, flush=True)


if __name__ == "__main__":
    main()
